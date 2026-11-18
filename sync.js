/* ============================================================================
   투로그 TwoLog — sync.js
   ----------------------------------------------------------------------------
   화면(app.js)은 이 파일이 주는 상태만 그리고, 저장·동기화는 여기서 다 합니다.

     · 지금 바로 (기본값)  : local 모드 — 이 기기의 localStorage + IndexedDB.
                              인터넷 없이도 그대로 동작합니다.
     · 두 대 실시간 동기화 : 아래 CONFIG 두 칸에 Supabase URL / anon key 를 넣으면
                              remote 모드로 바뀝니다. (Auth + Postgres + Storage + Realtime)

   데이터 모델 (supabase-schema.sql 참고)
     couples   : 우리 커플 한 줄 (이름·만난 날·문구·초대 코드·members)
     events    : 캘린더 일정
     notes     : 할일 / 버킷 / 영화·먹방 / 커스텀 리스트  (payload jsonb)
     photos    : 사진 메타데이터 (+ Storage 파일 경로)
     settings  : 공유 설정 (테마 색 등)

   이 기기에서만 쓰는 값(보고 있던 탭, 달력 위치)은 절대 올리지 않고
   localStorage 에 따로 둡니다. 그래서 두 사람이 서로의 화면 위치를 건드리지 않아요.
   ========================================================================= */
(function (global) {
  "use strict";

  /* ------------------------------------------------------------------ config */
  var CONFIG = {
    /* v25: 소영·준영의 Supabase 프로젝트 (README 5장).
       anon(publishable) 키는 앱에 들어가도 되는 공개 키 — 데이터는 RLS 가 지킵니다. */
    supabaseUrl: "https://qvhupdivtfzhzymovtyy.supabase.co",
    supabaseAnonKey: "sb_publishable_X4eO7AgGT5DnrxPdR5A3MA__hCxIqhD",
    /* 두 값을 비우면 local 모드(이 기기에만 저장)로 돌아갑니다. */

    supabaseModule: "https://esm.sh/@supabase/supabase-js@2.45.4", // 버전 고정
    photoBucket: "photos",
    photoMaxDim: 1800,      // 업로드 전 긴 변 최대 px
    photoQuality: 0.82,     // JPEG 품질
    key: "twolog:v1"
  };

  var K_STATE = CONFIG.key + ":state";
  var K_UI = CONFIG.key + ":ui";
  var K_DEVICE = CONFIG.key + ":device";
  var K_LEVEL = CONFIG.key + ":level"; // 마지막으로 올린 상태의 지문(불필요한 push 방지)
  var K_LEGACY = "couple-app-v1";
  /* v26: 이 기기의 로컬 기록을 그 커플(coupleId)로 옮겼다는 표시.
     한 번 옮긴 뒤에는 자동으로 다시 옮기지 않아 기록이 겹치지 않습니다.
     localStorage["twolog.migrated.<coupleId>"] = {at, events, notes, photos} */
  var K_MIGRATED = "twolog.migrated.";
  /* v27: v26 에서 gid·groups 없이 올라간 노트 카드 묶음을 폰의 원본으로 되살렸다는 표시.
     localStorage["twolog.groupsRepaired.<coupleId>"] = {at, groups:{todo,bucket,log}, notes} */
  var K_GROUPS_REPAIRED = "twolog.groupsRepaired.";
  var K_GROUPS = "groups";           // settings 테이블의 노트 카드 묶음 행
  var NOTE_ARR = { todo: "todos", bucket: "bucket", log: "logs" };

  function isRemote() { return !!(CONFIG.supabaseUrl && CONFIG.supabaseAnonKey); }

  /* 모드 강제(테스트·확인용) — 기본값은 위 CONFIG 그대로.
       · 주소에 ?sync=local / ?sync=remote 를 붙이거나
       · 첫 스크립트보다 먼저 window.__TWOLOG_MODE = "local" | "remote" 를 정해 두면
     그 모드로 열립니다. (로컬 모드 테스트가 실제 서버에 붙지 않게 하는 통로) */
  function forcedMode() {
    try {
      var g = global.__TWOLOG_MODE;
      if (g === "local" || g === "remote") return g;
    } catch (e) {}
    try {
      var v = new URLSearchParams(global.location.search).get("sync");
      if (v === "local" || v === "remote") return v;
    } catch (e) {}
    return null;
  }
  function nowIso() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function arr(v) { return Array.isArray(v) ? v : []; }
  function freshId() { return randId() + randId(); }
  function randId() { return Math.random().toString(36).slice(2, 10); }
  function randomCode() { return String(Math.floor(100000 + Math.random() * 900000)); }
  function log() { try { console.info.apply(console, ["[투로그]"].concat([].slice.call(arguments))); } catch (e) {} }
  function warn() { try { console.warn.apply(console, ["[투로그]"].concat([].slice.call(arguments))); } catch (e) {} }

  /* =====================================================================
     사진: 기기에서 리사이즈·압축 (업로드 용량을 1/10 로)
     ===================================================================== */
  function loadBitmap(file) {
    return new Promise(function (resolve, reject) {
      if (typeof createImageBitmap === "function") {
        try {
          createImageBitmap(file, { imageOrientation: "from-image" }).then(resolve, function () { fallback(); });
        } catch (e) { fallback(); }
      } else fallback();

      /* v26: 사진 덩어리가 아닌 값이 와도 promise 가 영원히 매달리지 않게 — 실패는 reject 로 */
      function fallback() {
        var url;
        try { url = URL.createObjectURL(file); } catch (e) { reject(new Error("image_decode_failed")); return; }
        var img = new Image();
        img.onload = function () { resolve(img); };
        img.onerror = function () { URL.revokeObjectURL(url); reject(new Error("image_decode_failed")); };
        img.src = url;
      }
    });
  }

  function compressImage(file, maxDim, quality) {
    return loadBitmap(file).then(function (src) {
      var w = src.width || src.naturalWidth || 0;
      var h = src.height || src.naturalHeight || 0;
      if (!w || !h) throw new Error("image_empty");
      var scale = Math.min(1, (maxDim || 1800) / Math.max(w, h));
      var cw = Math.max(1, Math.round(w * scale));
      var ch = Math.max(1, Math.round(h * scale));
      var canvas = document.createElement("canvas");
      canvas.width = cw;
      canvas.height = ch;
      var ctx = canvas.getContext("2d");
      ctx.fillStyle = "#FFFFFF";           // 투명 PNG 도 흰 바탕으로
      ctx.fillRect(0, 0, cw, ch);
      ctx.drawImage(src, 0, 0, cw, ch);
      if (src.close) { try { src.close(); } catch (e) {} }
      return new Promise(function (resolve, reject) {
        canvas.toBlob(function (blob) {
          blob ? resolve({ blob: blob, width: cw, height: ch }) : reject(new Error("compress_failed"));
        }, "image/jpeg", quality || 0.82);
      });
    });
  }

  /* =====================================================================
     로컬 사진 저장소 (IndexedDB) — localStorage 5MB 한계를 피합니다
     ===================================================================== */
  var idbHandle = null;
  var idbBroken = false;
  var memPhotos = Object.create(null); // IndexedDB 를 못 쓰는 환경(사생활 보호 모드) 대비
  var objectUrls = Object.create(null);

  function openIdb() {
    if (idbHandle) return Promise.resolve(idbHandle);
    if (idbBroken || typeof indexedDB === "undefined") return Promise.resolve(null);
    return new Promise(function (resolve) {
      var req;
      try { req = indexedDB.open("twolog", 1); } catch (e) { idbBroken = true; return resolve(null); }
      req.onupgradeneeded = function () {
        var db = req.result;
        if (!db.objectStoreNames.contains("photos")) db.createObjectStore("photos");
      };
      req.onsuccess = function () { idbHandle = req.result; resolve(idbHandle); };
      req.onerror = function () { idbBroken = true; resolve(null); };
      req.onblocked = function () { idbBroken = true; resolve(null); };
    });
  }

  function idbRun(mode, fn) {
    return openIdb().then(function (db) {
      if (!db) return null;
      return new Promise(function (resolve, reject) {
        var tx, store;
        try {
          tx = db.transaction("photos", mode);
          store = tx.objectStore("photos");
        } catch (e) { return resolve(null); }
        var out;
        try { out = fn(store); } catch (e) { return resolve(null); }
        tx.oncomplete = function () { resolve(out && out.result !== undefined ? out.result : out); };
        tx.onerror = function () { resolve(null); };
        tx.onabort = function () { resolve(null); };
      });
    });
  }

  function idbPut(id, blob) {
    memPhotos[id] = blob;
    return idbRun("readwrite", function (store) { store.put(blob, id); return null; });
  }
  function idbGet(id) {
    if (memPhotos[id]) return Promise.resolve(memPhotos[id]);
    return idbRun("readonly", function (store) { return store.get(id); }).then(function (v) {
      /* 없는 키를 읽으면 결과가 undefined 라 요청 객체가 돌아올 수 있어요 — 사진 덩어리만 인정 */
      var blob = typeof Blob !== "undefined" && v instanceof Blob ? v : null;
      if (blob) memPhotos[id] = blob;
      return blob;
    });
  }
  function idbDel(id) {
    delete memPhotos[id];
    return idbRun("readwrite", function (store) { store.delete(id); return null; });
  }

  function objectUrl(id, blob) {
    if (objectUrls[id]) return objectUrls[id];
    if (!blob) return "";
    try { objectUrls[id] = URL.createObjectURL(blob); } catch (e) { return ""; }
    return objectUrls[id];
  }
  function dropObjectUrl(id) {
    if (objectUrls[id]) { try { URL.revokeObjectURL(objectUrls[id]); } catch (e) {} delete objectUrls[id]; }
  }

  /* =====================================================================
     v26: 이 기기에 남아 있던 로컬 기록(localStorage) 읽기
     ---------------------------------------------------------------------
     로컬 모드가 쓰던 자리는 그대로 localStorage["twolog:v1:state"] 이고
     (없으면 예전 프로토타입 키 "couple-app-v1"), 사진 원본은 IndexedDB 입니다.
     이전(migration)은 이 값을 **읽기만** 하고 지우지 않습니다.
     ===================================================================== */
  function readLocalDoc() {
    var doc = null;
    try {
      var raw = localStorage.getItem(K_STATE);
      if (raw) doc = JSON.parse(raw);
      if (!doc) {
        var legacy = localStorage.getItem(K_LEGACY);
        if (legacy) doc = JSON.parse(legacy);
      }
    } catch (e) { warn("local state read failed", e); }
    return doc && typeof doc === "object" ? doc : null;
  }

  /* 로컬 기록 요약 — 무엇이 몇 개 있는지, 기본값과 다른 설정이 있는지. */
  function localSummary(doc) {
    var out = { has: false, events: 0, notes: 0, photos: 0, records: 0, customized: false };
    if (!doc || typeof doc !== "object") return out;
    out.events = arr(doc.events).length;
    out.notes = arr(doc.todos).length + arr(doc.bucket).length + arr(doc.logs).length + arr(doc.lists).length;
    out.photos = arr(doc.photos).length;
    out.records = out.events + out.notes + out.photos;
    var c = doc.couple && typeof doc.couple === "object" ? doc.couple : {};
    var t = doc.theme && typeof doc.theme === "object" ? doc.theme : {};
    var col = c.colors || {}, sc = c.sched || {};
    out.customized = !!(
      (c.me && c.me !== "소영") || (c.you && c.you !== "준영") ||
      (c.since && c.since !== nowIso()) ||
      (c.phrase && c.phrase !== "함께한 지") ||
      (c.fmt && c.fmt !== "D") ||
      (col.me && col.me !== "#9E636B") || (col.you && col.you !== "#3D5C82") ||
      (sc.me && sc.me !== "#9E636B") || (sc.you && sc.you !== "#3D5C82") || (sc.both && sc.both !== "#625A7F") ||
      t.name || t.log || t.mode === "dark" || t.homeTitleBg ||
      (t.pages && Object.keys(t.pages).length)
    );
    out.has = out.records > 0 || out.customized;
    return out;
  }

  function dataUrlToBlob(url) {
    return fetch(url).then(function (r) { return r.blob(); }).catch(function () {
      try {
        var parts = String(url).split(",");
        var mime = (parts[0].match(/data:([^;]+)/) || [])[1] || "image/jpeg";
        var bin = atob(parts[1] || "");
        var buf = new Uint8Array(bin.length);
        for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
        return new Blob([buf], { type: mime });
      } catch (e) { return null; }
    });
  }

  /* 로컬 사진의 원본 — IndexedDB(idb:) 덩어리이거나, 예전에 data URL 로 들어 있던 것 */
  function localPhotoBlob(p) {
    if (!p || typeof p !== "object") return Promise.resolve(null);
    var path = String(p.path || "");
    if (path.indexOf("idb:") === 0) return idbGet(path.slice(4));
    var cand = [p.src, p.data, p.url, path];
    for (var i = 0; i < cand.length; i++) {
      if (typeof cand[i] === "string" && cand[i].indexOf("data:") === 0) return dataUrlToBlob(cand[i]);
    }
    return Promise.resolve(null);
  }

  /* 로컬 couple 설정 → couples 행 (상대 기기라면 '나/상대'를 뒤집어 저장) */
  function couplePatchOf(couple, swap) {
    var c = couple || {};
    var cc = c.colors || {}, sc = c.sched || {};
    return {
      me: swap ? c.you : c.me,
      you: swap ? c.me : c.you,
      since: c.since,
      phrase: c.phrase || "함께한 지", fmt: c.fmt === "Y" ? "Y" : "D",
      colors: swap ? { me: cc.you, you: cc.me } : cc,
      sched: swap ? { me: sc.you, you: sc.me, both: sc.both } : sc
    };
  }

  /* 아직 아무도 손대지 않은 커플 행(이름이 '나/상대' 그대로)인지 */
  function coupleIsPlain(row) {
    if (!row) return true;
    var me = String(row.me || ""), you = String(row.you || "");
    return (me === "" || me === "나" || me === "상대") && (you === "" || you === "상대" || you === "나");
  }

  /* 겹치지 않게 같은 내용은 건너뛰기 위한 지문 */
  function sigEvent(r) { return [r.date, r.time || "", r.title || "", r.type || "", r.who || "", r.memo || ""].join("|"); }
  /* v27: 노트 지문은 «무엇을 적었는지»만 봅니다.
     payload 에 gid·memo·done 이 더해지기 전(v26)에 올라간 행과 같은 내용을
     다시 가져오기 했을 때 중복으로 들어가지 않게 하려는 것. */
  function noteLabel(kind, p) {
    var v = kind === "todo" ? (p || {}).text : (p || {}).title;
    return String(v == null ? "" : v);
  }
  function sigNote(r) { return String(r.kind || "") + "|" + noteLabel(r.kind, r.payload); }
  function sigPhoto(r) { return [r.date, r.album || "", r.title || "", r.memo || ""].join("|"); }

  /* v26: 프로필 사진(아바타)은 settings 테이블에 **사람별 한 줄**로 올립니다.
     key = "avatar:0" (couples.members[0] = 만든 사람) / "avatar:1" (members[1]).
     두 사람이 같은 순간에 각자 사진을 바꿔도 서로 덮어쓰지 않게 행을 따로 둡니다. */
  var K_AVATAR = "avatar:";
  function avatarSlotOf(who, swap) {
    var meSlot = swap ? 1 : 0;
    return who === "me" ? meSlot : 1 - meSlot;
  }
  function avatarKeyOf(who, swap) { return K_AVATAR + avatarSlotOf(who, swap); }
  function avatarWhoOf(key, swap) {
    var slot = Number(String(key || "").slice(K_AVATAR.length));
    if (isNaN(slot)) return null;
    return slot === (swap ? 1 : 0) ? "me" : "you";
  }
  function avatarSrc(v) {
    if (!v) return "";
    var s = typeof v === "string" ? v : v.src;
    return typeof s === "string" && s.indexOf("data:image/") === 0 ? s : "";
  }

  /* =====================================================================
     상태 → 테이블 행 / 테이블 행 → 상태
     ===================================================================== */
  function stateToRows(doc, coupleId, swap) {
    var flip = function (who) {
      if (who !== "me" && who !== "you") return "both";
      if (!swap) return who;
      return who === "me" ? "you" : "me";
    };
    var whoToken = function (w) {
      if (!w || w === "함께" || w === "both") return "both";
      if (w === "나" || w === "me") return "me";
      return "you";          // 상대 이름 또는 그 밖의 값
    };
    var rows = { events: [], notes: [], photos: [] };
    (doc.events || []).forEach(function (e) {
      rows.events.push({
        id: String(e.id), couple_id: coupleId,
        title: e.title || "", date: e.date || nowIso(), time: e.time || "",
        /* 여러 날 일정의 종료일은 memo 칸에 담아 둡니다 (스키마 변경 없이 동기화) */
        type: e.type || "date", memo: e.endDate && e.endDate > e.date ? e.endDate : "", who: flip(e.who)
      });
    });
    var push = function (kind, obj, sort, payload) {
      rows.notes.push({ id: String(obj.id), couple_id: coupleId, kind: kind, sort: sort, payload: payload, deleted: false });
    };
    /* v27: 항목 하나를 notes 행의 payload 로 — gid(카드 묶음)·memo(상세 메모)·done 까지 담습니다.
       (v26 까지는 이 셋이 빠져서 카드가 한 개로 합쳐지고 상세 메모가 사라졌어요) */
    (doc.todos || []).forEach(function (t, i) {
      push("todo", t, i, notePayload("todo", t, flip, whoToken));
    });
    (doc.bucket || []).forEach(function (b, i) {
      push("bucket", b, i, notePayload("bucket", b, flip, whoToken));
    });
    (doc.logs || []).forEach(function (l, i) {
      push("log", l, i, notePayload("log", l, flip, whoToken));
    });
    (doc.lists || []).forEach(function (l, i) {
      push("list", l, i, notePayload("list", l, flip, whoToken));
    });
    (doc.photos || []).forEach(function (p, i) {
      rows.photos.push({
        id: String(p.id), couple_id: coupleId, date: p.date || nowIso(), album: p.album || "",
        title: p.title || "", place: p.place || "", memo: p.memo || "",
        art: typeof p.art === "number" ? p.art : null,
        cap_bg: p.capBg || null, storage_path: p.path || null, sort: i
      });
    });
    return rows;
  }

  /* v27: 노트 한 항목 → payload (stateToRows·repairGroups 가 함께 씁니다) */
  function notePayload(kind, obj, flip, whoToken) {
    var o = obj || {};
    var p;
    if (kind === "todo") {
      p = { text: o.text || "", memo: o.memo || "", done: !!o.done, who: flip(whoToken(o.who)) };
    } else if (kind === "bucket") {
      p = { title: o.title || "", cat: o.cat || "기타", memo: o.memo || "", done: !!o.done, status: o.status || "" };
    } else if (kind === "log") {
      p = { kind: o.kind === "food" ? "food" : "movie", title: o.title || "", rating: Number(o.rating) || 0,
        date: o.date || nowIso(), review: o.review || "", place: o.place || "", done: o.done !== false };
    } else {
      p = { title: o.title || "", emoji: o.emoji || "📌", kind: o.kind === "memo" ? "memo" : "check",
        items: arr(o.items).map(function (it) { return { id: it.id, text: it.text || "", memo: it.memo || "", done: !!it.done }; }) };
    }
    if (o.gid) p.gid = String(o.gid);        // 어느 카드(리스트)에 들어 있는지
    return p;
  }

  /* v27: 노트 카드 묶음({todo,bucket,log} 의 {id,title,titleBg,caption,who,date,...})을
     그대로(모든 필드) 복사합니다. settings 의 key="groups" 행에 이 값을 담아요. */
  function normalizeGroups(value) {
    var src = value && typeof value === "object" ? value : {};
    var out = { todo: [], bucket: [], log: [] };
    ["todo", "bucket", "log"].forEach(function (k) {
      out[k] = arr(src[k]).filter(function (g) { return g && typeof g === "object"; }).map(function (g) {
        var c;
        try { c = JSON.parse(JSON.stringify(g)); } catch (e) { c = {}; }
        if (!c.id) c.id = freshId();
        c.id = String(c.id);
        return c;
      });
    });
    return out;
  }
  function groupCount(groups) {
    var g = normalizeGroups(groups);
    return { todo: g.todo.length, bucket: g.bucket.length, log: g.log.length };
  }
  function groupsEmpty(value) {
    if (!value || typeof value !== "object") return true;
    return !(arr(value.todo).length + arr(value.bucket).length + arr(value.log).length);
  }

  function noteWhoLabel(who, flip, couple) {
    var t = flip(who);
    if (t === "me") return "나";
    if (t === "you") return couple.you;
    return "함께";
  }

  function rowsToState(coupleRow, eventRows, noteRows, photoRows, settingRows, swap) {
    var colors = coupleRow.colors || {};
    var sched = coupleRow.sched || {};
    var meColor = colors.me || "#F7C6D4";
    var youColor = colors.you || "#BCE0F7";
    var meSched = sched.me || "#F7C6D4";
    var youSched = sched.you || "#BCE0F7";
    var bothSched = sched.both || "#D6C5F7";
    var meName = coupleRow.me || "소영";
    var youName = coupleRow.you || "준영";
    if (swap) {
      var tn = meName; meName = youName; youName = tn;
      var tc = meColor; meColor = youColor; youColor = tc;
      var ts = meSched; meSched = youSched; youSched = ts;
    }
    var flip = function (who) {
      if (who !== "me" && who !== "you") return "both";
      if (!swap) return who;
      return who === "me" ? "you" : "me";
    };
    var doc = {
      couple: {
        me: meName,
        you: youName,
        since: coupleRow.since || nowIso(),
        fmt: coupleRow.fmt === "Y" ? "Y" : "D",
        phrase: coupleRow.phrase || "함께한 지",
        colors: { me: meColor, you: youColor },
        sched: { me: meSched, you: youSched, both: bothSched },
        pics: {}
      },
      link: { code: String(coupleRow.invite_code || ""), connected: (coupleRow.members || []).length > 1, partnerCode: "" },
      auth: { out: false, email: "" },
      events: [], todos: [], bucket: [], logs: [], expenses: [], photos: [], lists: [],
      theme: { name: null, log: null, mode: "light" }
    };

    (eventRows || []).forEach(function (r) {
      var rMemo = String(r.memo || "");
      var rEnd = /^\d{4}-\d{2}-\d{2}$/.test(rMemo) && rMemo > String(r.date || "") ? rMemo : String(r.date || "");
      doc.events.push({ id: r.id, date: r.date, endDate: rEnd, time: r.time || "", title: r.title || "", type: r.type || "date", memo: "", who: flip(r.who) });
    });
    /* v27: gid(카드 묶음)·memo(상세 메모)·done 도 함께 복원합니다 */
    (noteRows || []).filter(function (r) { return !r.deleted; }).sort(function (a, b) { return (a.sort || 0) - (b.sort || 0); })
      .forEach(function (r) {
        var p = r.payload || {};
        var gid = p.gid ? String(p.gid) : undefined;
        if (r.kind === "todo") {
          var todo = { id: r.id, text: p.text || "", memo: p.memo || "", done: !!p.done, who: noteWhoLabel(p.who, flip, doc.couple) };
          if (gid) todo.gid = gid;
          doc.todos.push(todo);
        } else if (r.kind === "bucket") {
          var buck = { id: r.id, title: p.title || "", cat: p.cat || "기타", memo: p.memo || "", done: !!p.done, status: p.status || undefined };
          if (gid) buck.gid = gid;
          doc.bucket.push(buck);
        } else if (r.kind === "log") {
          var log = { id: r.id, kind: p.kind === "food" ? "food" : "movie", title: p.title || "", rating: Number(p.rating) || 0,
            date: p.date || nowIso(), review: p.review || "", place: p.place || "", done: p.done !== false };
          if (gid) log.gid = gid;
          doc.logs.push(log);
        } else if (r.kind === "list") {
          var list = { id: r.id, title: p.title || "", emoji: p.emoji || "📌", kind: p.kind === "memo" ? "memo" : "check",
            items: arr(p.items).map(function (it) { return { id: it.id || randId(), text: it.text || "", memo: it.memo || "", done: !!it.done }; }) };
          if (gid) list.gid = gid;
          doc.lists.push(list);
        }
      });
    (photoRows || []).sort(function (a, b) { return (a.sort || 0) - (b.sort || 0); }).forEach(function (r) {
      doc.photos.push({
        id: r.id, date: r.date, album: r.album || "", title: r.title || "", place: r.place || "",
        memo: r.memo || "", art: typeof r.art === "number" ? r.art : 0,
        capBg: r.cap_bg || null, path: r.storage_path || null
      });
    });
    (settingRows || []).forEach(function (r) {
      if (r.key === "theme" && r.value) doc.theme = Object.assign({ name: null, log: null, mode: "light" }, r.value);
      else if (r.key === K_GROUPS && r.value) {
        /* v27: 노트 카드 묶음 — 두 기기가 같은 카드 id·제목·색을 봅니다 */
        var gs = normalizeGroups(r.value);
        if (gs.todo.length || gs.bucket.length || gs.log.length) doc.groups = gs;
      }
      else if (String(r.key || "").indexOf(K_AVATAR) === 0) {
        /* v26: 프로필 사진 — 사람별 행을 이 기기의 '나/상대'로 바꿔 담습니다 */
        var aw = avatarWhoOf(r.key, swap);
        var src = avatarSrc(r.value);
        if (aw && src) doc.couple.pics[aw] = src;
      }
    });
    return doc;
  }

  /* =====================================================================
     local 백엔드
     ===================================================================== */
  function LocalBackend() {}

  LocalBackend.prototype.load = function () {
    var state = null;
    try {
      var raw = localStorage.getItem(K_STATE);
      if (raw) state = JSON.parse(raw);
      if (!state) {
        var legacy = localStorage.getItem(K_LEGACY);  // 예전 프로토타입 데이터 1회 이전
        if (legacy) { state = JSON.parse(legacy); localStorage.setItem(K_STATE, legacy); }
      }
    } catch (e) { warn("state read failed", e); }
    return Promise.resolve(state);
  };

  LocalBackend.prototype.save = function (doc) {
    try {
      localStorage.setItem(K_STATE, JSON.stringify(doc));
      return Promise.resolve(true);
    } catch (e) {
      warn("state write failed", e);
      return Promise.reject(e);
    }
  };

  LocalBackend.prototype.addPhoto = function (file, meta) {
    return compressImage(file, CONFIG.photoMaxDim, CONFIG.photoQuality).then(function (res) {
      var id = randId() + randId();
      return idbPut(id, res.blob).then(function () {
        return {
          photo: {
            id: id, date: meta.date, album: meta.album, title: meta.title || "",
            place: "", memo: "", art: 0, capBg: null, path: "idb:" + id,
            w: res.width, h: res.height
          },
          url: objectUrl(id, res.blob)
        };
      });
    });
  };

  LocalBackend.prototype.photoUrls = function (photos) {
    return Promise.all((photos || []).map(function (p) {
      if (!p.path || String(p.path).indexOf("idb:") !== 0) return Promise.resolve(null);
      var id = String(p.path).slice(4);
      if (objectUrls[id]) return Promise.resolve([id, objectUrls[id]]);
      return idbGet(id).then(function (blob) {
        return blob ? [id, objectUrl(id, blob)] : null;
      });
    })).then(function (pairs) {
      var map = {};
      pairs.forEach(function (pair) { if (pair) map[pair[0]] = pair[1]; });
      return map;
    });
  };

  LocalBackend.prototype.deletePhoto = function (photo) {
    if (photo && photo.path && String(photo.path).indexOf("idb:") === 0) {
      var id = String(photo.path).slice(4);
      dropObjectUrl(id);
      return idbDel(id);
    }
    return Promise.resolve();
  };

  /* auth / couple 는 local 모드에서 '이 기기 안의 설정'으로만 동작합니다. */
  LocalBackend.prototype.session = function () { return Promise.resolve({ signedIn: false, email: "" }); };
  LocalBackend.prototype.signIn = function () { return Promise.resolve({ error: "local_mode" }); };
  LocalBackend.prototype.signUp = function () { return Promise.resolve({ error: "local_mode" }); };
  LocalBackend.prototype.signOut = function () { return Promise.resolve(); };
  LocalBackend.prototype.joinCouple = function () { return Promise.resolve({ error: "local_mode" }); };
  LocalBackend.prototype.leaveCouple = function () { return Promise.resolve({ error: "local_mode" }); };
  LocalBackend.prototype.setInviteCode = function () { return Promise.resolve({ error: "local_mode" }); };
  /* v26: 로컬 모드의 프로필 사진은 상태(couple.pics)와 함께 기기에만 저장됩니다. */
  LocalBackend.prototype.setAvatar = function () { return Promise.resolve({ ok: true, local: true }); };
  /* v26: 로컬 모드에서는 옮길 곳(원격)이 없으니 그대로 안내만 */
  LocalBackend.prototype.migrateLocal = function () { return Promise.resolve({ ok: false, reason: "local_mode" }); };
  LocalBackend.prototype.migratedFlag = function () { return null; };
  /* v27: 로컬 모드는 groups·gid 가 이미 한 파일에 함께 저장되므로 복구할 것이 없습니다. */
  LocalBackend.prototype.repairGroups = function () { return Promise.resolve({ ok: false, reason: "local_mode" }); };
  LocalBackend.prototype.groupsRepairedFlag = function () { return null; };
  LocalBackend.prototype.subscribe = function () { return function () {}; };

  /* =====================================================================
     supabase 백엔드
     ===================================================================== */
  function SupabaseBackend() {
    this.client = null;
    this.user = null;
    this.couple = null;
    this.prev = null;          // 마지막으로 올린/받은 행 스냅샷 (변경분만 push)
    this.saving = null;        // 저장 직렬화
    this.queued = null;
    this.remoteHandler = null;
    this.unsubscribe = null;
    this.reloadTimer = null;
    this.signed = {};          // photo id -> signed url
  }

  SupabaseBackend.prototype.connect = function () {
    var self = this;
    if (this.client) return Promise.resolve(this.client);
    return import(CONFIG.supabaseModule).then(function (mod) {
      var createClient = mod.createClient || (mod.default && mod.default.createClient);
      if (!createClient) throw new Error("supabase_module_missing");
      self.client = createClient(CONFIG.supabaseUrl, CONFIG.supabaseAnonKey, {
        auth: { persistSession: true, autoRefreshToken: true, detectSessionInUrl: true }
      });
      return self.client;
    });
  };

  SupabaseBackend.prototype.whoAmI = function () {
    var self = this;
    return this.connect().then(function (client) {
      return client.auth.getSession().then(function (res) {
        self.user = res && res.data && res.data.session ? res.data.session.user : null;
        return self.user;
      });
    });
  };

  SupabaseBackend.prototype.session = function () {
    return this.whoAmI().then(function (user) {
      return { signedIn: !!user, email: user ? user.email || "" : "" };
    }).catch(function () { return { signedIn: false, email: "" }; });
  };

  SupabaseBackend.prototype.signIn = function (email, password) {
    var self = this;
    return this.connect().then(function (client) {
      return client.auth.signInWithPassword({ email: email, password: password });
    }).then(function (res) {
      if (res.error) return { error: res.error.message };
      self.user = res.data.user;
      return { ok: true };
    }).catch(function (e) { return { error: String(e && e.message || e) }; });
  };

  SupabaseBackend.prototype.signUp = function (email, password) {
    var self = this;
    return this.connect().then(function (client) {
      return client.auth.signUp({ email: email, password: password });
    }).then(function (res) {
      if (res.error) return { error: res.error.message };
      // 이메일 확인이 켜져 있으면 session 이 비어 있습니다.
      if (!res.data.session) return { needsConfirm: true };
      self.user = res.data.user;
      return { ok: true };
    }).catch(function (e) { return { error: String(e && e.message || e) }; });
  };

  SupabaseBackend.prototype.signOut = function () {
    var self = this;
    return this.connect().then(function (client) { return client.auth.signOut(); }).then(function () {
      self.user = null; self.couple = null; self.prev = null; self.signed = {};
      return true;
    });
  };

  SupabaseBackend.prototype.ensureCouple = function () {
    var self = this;
    if (this.couple) return Promise.resolve(this.couple);
    if (!this.user) return Promise.reject(new Error("no_session"));
    var client = this.client;
    return client.from("couples").select("*").contains("members", [this.user.id]).then(function (res) {
      if (res.error) throw res.error;
      var rows = res.data || [];
      if (rows.length) {
        /* 커플 연결 뒤에는 두 사람이 들어 있는 커플을 먼저 고릅니다. */
        var shared = rows.filter(function (r) { return (r.members || []).length > 1; });
        self.adopt((shared[0] || rows[0]));
        return self.couple;
      }
      var today = nowIso();
      return client.from("couples").insert({
        invite_code: randomCode(),
        members: [self.user.id],
        me: "나", you: "상대", since: today, phrase: "함께한 지", fmt: "D",
        colors: { me: "#F7C6D4", you: "#BCE0F7" },
        sched: { me: "#F7C6D4", you: "#BCE0F7", both: "#D6C5F7" }
      }).select().single().then(function (ins) {
        if (ins.error) throw ins.error;
        self.adopt(ins.data);
        return self.couple;
      });
    });
  };

  /* 두 번째 멤버(상대 기기)라면 이름·색·담당의 '나/상대'를 뒤집어 보여줍니다. */
  SupabaseBackend.prototype.adopt = function (row) {
    this.couple = row;
    this.swap = !!(row && row.members && this.user && row.members.indexOf(this.user.id) === 1);
  };

  /* v27: couples 행을 서버에서 다시 읽어 옵니다 (상대가 고친 이름·만난 날·색 반영) */
  SupabaseBackend.prototype.refreshCouple = function () {
    var self = this;
    if (!this.client || !this.couple || !this.user) return Promise.resolve(this.couple);
    return this.client.from("couples").select("*").eq("id", this.couple.id).then(function (res) {
      if (res && !res.error && Array.isArray(res.data) && res.data.length) self.adopt(res.data[0]);
      return self.couple;
    }).catch(function () { return self.couple; });
  };

  SupabaseBackend.prototype.load = function () {
    var self = this;
    return this.whoAmI().then(function (user) {
      if (!user) return null;                     // 로그인 화면으로
      return self.ensureCouple();
    }).then(function (couple) {
      if (!couple) return null;
      /* v27: 상대가 커플 정보(이름·만난 날·문구·색)를 바꿨으면 다시 읽어 옵니다.
         예전에는 메모리에 있던 값만 써서 couples 변경이 화면에 안 닿았어요. */
      return self.refreshCouple().then(function () { return self.couple || couple; });
    }).then(function (couple) {
      if (!couple) return null;
      var client = self.client, cid = couple.id;
      return Promise.all([
        client.from("events").select("*").eq("couple_id", cid),
        client.from("notes").select("*").eq("couple_id", cid),
        client.from("photos").select("*").eq("couple_id", cid),
        client.from("settings").select("*").eq("couple_id", cid)
      ]).then(function (parts) {
        parts.forEach(function (r) { if (r.error) warn("load table failed", r.error); });
        var doc = rowsToState(couple, parts[0].data || [], parts[1].data || [], parts[2].data || [], parts[3].data || [], !!self.swap);
        self.prev = {
          couple: JSON.parse(JSON.stringify(couple)),
          events: index(parts[0].data || []),
          notes: index(parts[1].data || []),
          photos: index(parts[2].data || []),
          settings: index(parts[3].data || [])
        };
        return doc;
      });
    });
  };

  function index(rows) {
    var map = {};
    (rows || []).forEach(function (r) { map[r.id || r.key] = r; });
    return map;
  }
  function sameRow(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

  SupabaseBackend.prototype.save = function (doc) {
    var self = this;
    if (!this.couple) return Promise.resolve(false);
    // 같은 순간 여러 번 저장되지 않도록 직렬화 + 마지막 상태만 반영
    if (this.saving) { this.queued = doc; return this.saving.then(function () { return self.save(self.queued || doc); }); }
    this.saving = this.push(doc).catch(function (e) {
      warn("push failed", e);
      try { localStorage.setItem(K_LEVEL, JSON.stringify({ pending: true, at: Date.now() })); } catch (err) {}
      return false;
    }).then(function (res) {
      self.saving = null;
      var next = self.queued; self.queued = null;
      if (next && next !== doc) return self.save(next);
      return res;
    });
    return this.saving;
  };

  SupabaseBackend.prototype.push = function (doc) {
    var self = this;
    var client = this.client;
    var cid = this.couple.id;
    var rows = stateToRows(doc, cid, !!this.swap);
    if (!this.prev) this.prev = { couple: null, events: {}, notes: {}, photos: {}, settings: {} };

    var jobs = [];

    /* couples (이름·만난 날·문구·D-day 표기·색) — 저장은 항상 '만든 사람' 기준 */
    var couplePatch = couplePatchOf(doc.couple, !!this.swap);
    var prevCouple = this.prev.couple || {};
    var coupleChanged = Object.keys(couplePatch).some(function (k) { return JSON.stringify(couplePatch[k]) !== JSON.stringify(prevCouple[k]); });
    if (coupleChanged) {
      jobs.push(client.from("couples").update(couplePatch).eq("id", cid).then(function (r) {
        if (r.error) throw r.error;
      }));
    }

    /* events */
    jobs.push(this.upsertTable("events", rows.events, this.prev.events));
    /* notes */
    jobs.push(this.upsertTable("notes", rows.notes, this.prev.notes));
    /* photos (Storage 파일은 addPhoto 에서 이미 올라감) */
    jobs.push(this.upsertTable("photos", rows.photos.map(function (p) {
      return { id: p.id, couple_id: p.couple_id, date: p.date, album: p.album, title: p.title, place: p.place, memo: p.memo, art: p.art, cap_bg: p.cap_bg, storage_path: p.storage_path, sort: p.sort };
    }), this.prev.photos));

    /* settings: 테마 */
    var themeRow = { couple_id: cid, key: "theme", value: doc.theme || {} };
    if (!this.prev.settings.theme || !sameRow(this.prev.settings.theme.value, themeRow.value)) {
      jobs.push(client.from("settings").upsert(themeRow, { onConflict: "couple_id,key" }).then(function (r) {
        if (r.error) throw r.error;
        self.prev.settings.theme = themeRow;
      }));
    }

    /* settings: v27 노트 카드 묶음(groups) — 카드 id·제목·제목색·순서를 두 기기가 함께 씁니다 */
    var groupsValue = normalizeGroups(doc.groups);
    var prevGroups = this.prev.settings[K_GROUPS];
    var groupsChanged = !prevGroups || !prevGroups.value || !sameRow(prevGroups.value, groupsValue);
    if (groupsChanged && (groupsValue.todo.length || groupsValue.bucket.length || groupsValue.log.length)) {
      var groupsRow = { couple_id: cid, key: K_GROUPS, value: groupsValue };
      jobs.push(client.from("settings").upsert(groupsRow, { onConflict: "couple_id,key" }).then(function (r) {
        if (r.error) throw r.error;
        self.prev.settings[K_GROUPS] = groupsRow;
      }));
    }

    return Promise.all(jobs).then(function () {
      self.prev = {
        couple: Object.assign({}, prevCouple, couplePatch),
        events: index(rows.events), notes: index(rows.notes),
        photos: index(rows.photos), settings: self.prev.settings
      };
      try { localStorage.setItem(K_LEVEL, JSON.stringify({ pending: false, at: Date.now() })); } catch (e) {}
      return true;
    });
  };

  SupabaseBackend.prototype.upsertTable = function (table, rows, prevMap) {
    var self = this, client = this.client, jobs = [];
    var prev = prevMap || {};
    var keep = {};
    rows.forEach(function (row) {
      keep[row.id] = true;
      var old = prev[row.id];
      if (!old || !sameRow(pickData(old), row)) {
        jobs.push(client.from(table).upsert(row).then(function (r) {
          if (r.error) throw r.error;
          if (table === "photos") self.markSigned(row.storage_path);
        }));
      }
    });
    Object.keys(prev).forEach(function (id) {
      if (keep[id]) return;
      jobs.push(client.from(table).delete().eq("id", id).then(function (r) {
        if (r.error) throw r.error;
      }));
    });
    return Promise.all(jobs);
  };

  function pickData(row) {
    var out = {};
    Object.keys(row).forEach(function (k) {
      if (k === "updated_at" || k === "created_at" || k === "updated_by") return;
      out[k] = row[k];
    });
    return out;
  }

  SupabaseBackend.prototype.markSigned = function (path) {
    if (!path) return;
    this.signed[path] = true;
  };

  /* 사진: Storage 업로드 (비공개 버킷 + 서명 URL) */
  SupabaseBackend.prototype.addPhoto = function (file, meta) {
    var self = this;
    return compressImage(file, CONFIG.photoMaxDim, CONFIG.photoQuality).then(function (res) {
      var id = randId() + randId();
      var path = self.couple.id + "/" + id + ".jpg";
      return self.client.storage.from(CONFIG.photoBucket)
        .upload(path, res.blob, { contentType: "image/jpeg", upsert: true })
        .then(function (up) {
          if (up.error) throw up.error;
          return self.client.storage.from(CONFIG.photoBucket).createSignedUrl(path, 60 * 60 * 24 * 6).then(function (s) {
            return {
              photo: {
                id: id, date: meta.date, album: meta.album, title: meta.title || "",
                place: "", memo: "", art: 0, capBg: null, path: path
              },
              url: s && !s.error ? s.data.signedUrl : "",
              blob: res.blob, width: res.width, height: res.height
            };
          });
        });
    });
  };

  SupabaseBackend.prototype.photoUrls = function (photos) {
    var self = this;
    var need = (photos || []).filter(function (p) { return p.path && String(p.path).indexOf("idb:") !== 0; });
    if (!need.length) return Promise.resolve({});
    var paths = need.map(function (p) { return p.path; });
    return this.client.storage.from(CONFIG.photoBucket).createSignedUrls(paths, 60 * 60 * 24 * 6).then(function (res) {
      var map = {};
      if (res.error) { warn("signed url failed", res.error); return map; }
      (res.data || []).forEach(function (item) {
        if (!item.path || !item.signedUrl) return;
        var hit = need.filter(function (p) { return p.path === item.path; })[0];
        if (hit) map[hit.id] = item.signedUrl;
      });
      return map;
    }).catch(function () { return {}; });
  };

  SupabaseBackend.prototype.deletePhoto = function (photo) {
    if (!photo || !photo.path || String(photo.path).indexOf("idb:") === 0) return Promise.resolve();
    return this.client.storage.from(CONFIG.photoBucket).remove([photo.path]).catch(function () {});
  };

  SupabaseBackend.prototype.joinCouple = function (code) {
    var self = this;
    return this.whoAmI().then(function () {
      return self.connect();
    }).then(function (client) {
      return client.rpc("join_couple_by_code", { code: String(code) });
    }).then(function (res) {
      if (res.error) return { error: res.error.message };
      var row = Array.isArray(res.data) ? res.data[0] : res.data;
      if (row) self.adopt(row); else self.couple = null;
      return self.load().then(function (doc) { return { ok: true, state: doc }; });
    });
  };

  SupabaseBackend.prototype.leaveCouple = function () {
    var self = this;
    return this.connect().then(function (client) {
      return client.rpc("leave_couple");
    }).then(function (res) {
      if (res.error) return { error: res.error.message };
      self.couple = null; self.prev = null;
      return { ok: true };
    });
  };

  /* v25: 초대 코드 새로 만들기 — 서버(couples.invite_code)를 바꿔야 두 기기가 같은 코드를 봅니다. */
  SupabaseBackend.prototype.setInviteCode = function (code) {
    var self = this;
    if (!this.couple) return Promise.resolve({ error: "no_couple" });
    var nextCode = String(code || "");
    if (!/^[0-9]{6}$/.test(nextCode)) return Promise.resolve({ error: "bad_code" });
    return this.connect().then(function (client) {
      return client.from("couples").update({ invite_code: nextCode }).eq("id", self.couple.id);
    }).then(function (r) {
      if (r && r.error) return { error: r.error.message || "update_failed" };
      self.couple.invite_code = nextCode;
      if (self.prev && self.prev.couple) self.prev.couple.invite_code = nextCode;
      return { ok: true, code: nextCode };
    }).catch(function (e) { return { error: String(e && e.message || e) }; });
  };

  /* v26: 프로필 사진 한 장을 서버(settings)에 올립니다.
       who : 'me' | 'you' (이 기기 화면 기준)
       dataUrl : 256px JPEG data URL, 지우기면 "" */
  SupabaseBackend.prototype.setAvatar = function (who, dataUrl) {
    var self = this;
    if (!this.couple || !this.user) return Promise.resolve({ error: "no_couple" });
    var key = avatarKeyOf(who === "you" ? "you" : "me", !!this.swap);
    var row = { couple_id: this.couple.id, key: key, value: { src: avatarSrc(dataUrl), at: Date.now() } };
    return this.connect().then(function (client) {
      return client.from("settings").upsert(row, { onConflict: "couple_id,key" });
    }).then(function (r) {
      if (r && r.error) return { error: r.error.message || "update_failed" };
      if (self.prev && self.prev.settings) self.prev.settings[key] = row;
      return { ok: true, who: who, has: !!row.value.src };
    }).catch(function (e) { return { error: String(e && e.message || e) }; });
  };

  /* =====================================================================
     v26: 폰에 남아 있던 로컬 기록 → 이 커플 공간으로 이전
     ---------------------------------------------------------------------
     · 자동(기본): 이 기기에서 이 커플로 옮긴 적이 없고(플래그 없음),
                  로컬에 사용자가 만든 기록·설정이 있고, 원격 events/notes/photos 가
                  비어 있을 때만 — 로그인/앱 시작/커플 연결 직후에 한 번.
     · force    : My 탭 「폰에 있던 예전 기록 가져오기」 — 원격에 이미 기록이 있어도
                  겹치는 내용(같은 날·같은 제목 등)은 건너뛰고 새 기록만 더합니다.
     성공하면 localStorage 의 로컬 상태는 그대로 두고 플래그만 남깁니다.
     ===================================================================== */
  SupabaseBackend.prototype.migrateLocal = function (opts) {
    var self = this;
    var force = !!(opts && opts.force);
    if (!this.couple || !this.user) return Promise.resolve({ ok: false, reason: "no_couple" });
    var cid = this.couple.id;
    var local = readLocalDoc();
    var info = localSummary(local);
    if (!local || !info.has) return Promise.resolve({ ok: false, reason: "no_local", summary: info });

    var flagKey = K_MIGRATED + cid;
    if (!force) {
      var already = false;
      try { already = !!localStorage.getItem(flagKey); } catch (e) {}
      if (already) return Promise.resolve({ ok: false, skipped: "already", summary: info });
    }

    var client = this.client;
    var swap = !!this.swap;
    return Promise.all([
      client.from("events").select("*").eq("couple_id", cid),
      client.from("notes").select("*").eq("couple_id", cid),
      client.from("photos").select("*").eq("couple_id", cid),
      client.from("settings").select("*").eq("couple_id", cid)
    ]).then(function (parts) {
      parts.forEach(function (r) { if (r && r.error) throw r.error; });
      var evRows = parts[0].data || [];
      var noteRows = parts[1].data || [];
      var photoRows = parts[2].data || [];
      var setRows = parts[3].data || [];

      var liveNotes = noteRows.filter(function (r) { return !r.deleted; });
      var remoteHas = evRows.length + liveNotes.length + photoRows.length > 0;
      if (remoteHas && !force) {
        return { ok: false, skipped: "remote_not_empty", summary: info, remoteHas: true };
      }

      /* ---- 1. 일정 · 노트 ---- */
      var rows = stateToRows(local, cid, swap);
      var evSigs = {};
      evRows.forEach(function (r) { evSigs[sigEvent(r)] = 1; });
      var evIds = {};
      evRows.forEach(function (r) { evIds[r.id] = 1; });
      var evOut = [];
      rows.events.forEach(function (r) {
        if (evSigs[sigEvent(r)]) return;                     // 이미 있는 같은 일정은 건너뜀
        if (evIds[r.id]) r.id = freshId();                   // id 가 겹치면 새 id 로
        evIds[r.id] = 1;
        evSigs[sigEvent(r)] = 1;
        evOut.push(r);
      });

      var noteSigs = {};
      var noteIds = {};
      var noteMax = -1;
      noteRows.forEach(function (r) {
        noteSigs[sigNote(r)] = 1;
        noteIds[r.id] = 1;
        var sv = Number(r.sort);
        if (!isNaN(sv) && sv > noteMax) noteMax = sv;
      });
      var noteOut = [];
      rows.notes.forEach(function (r) {
        if (noteSigs[sigNote(r)]) return;                     // 같은 내용의 메모·할일은 건너뜀
        if (noteIds[r.id]) r.id = freshId();
        noteIds[r.id] = 1;
        noteSigs[sigNote(r)] = 1;
        r.sort = ++noteMax;
        noteOut.push(r);
      });

      /* ---- 2. 사진: 원본(IndexedDB / data URL)을 Storage 에 올리고 행을 만듭니다 ---- */
      var photoSigs = {};
      var photoIds = {};
      var photoMax = -1;
      photoRows.forEach(function (r) {
        photoSigs[sigPhoto(r)] = 1;
        photoIds[r.id] = 1;
        var sv = Number(r.sort);
        if (!isNaN(sv) && sv > photoMax) photoMax = sv;
      });
      var localPhotos = arr(local.photos).filter(function (p) {
        return p && typeof p === "object" && !photoSigs[sigPhoto(p)];
      });

      return localPhotos.reduce(function (chain, p) {
        return chain.then(function (acc) {
          var pid = freshId();
          var path = cid + "/" + pid + ".jpg";
          return localPhotoBlob(p).then(function (blob) {
            if (!blob) return null;
            return compressImage(blob, CONFIG.photoMaxDim, CONFIG.photoQuality).catch(function () {
              return { blob: blob };
            }).then(function (res) {
              return client.storage.from(CONFIG.photoBucket)
                .upload(path, res.blob, { contentType: "image/jpeg", upsert: true });
            }).then(function (up) {
              if (up && up.error) throw up.error;
              return path;
            });
          }).then(function (storedPath) {
            acc.rows.push({
              id: pid, couple_id: cid, date: p.date || nowIso(), album: p.album || "",
              title: p.title || "", place: p.place || "", memo: p.memo || "",
              art: typeof p.art === "number" ? p.art : null,
              cap_bg: p.capBg || null, storage_path: storedPath || null, sort: ++photoMax
            });
            if (!storedPath) acc.withoutFile++;
            return acc;
          }, function () {
            /* 파일을 못 올려도 사진의 날짜·제목은 남깁니다 */
            acc.rows.push({
              id: pid, couple_id: cid, date: p.date || nowIso(), album: p.album || "",
              title: p.title || "", place: p.place || "", memo: p.memo || "",
              art: typeof p.art === "number" ? p.art : null,
              cap_bg: p.capBg || null, storage_path: null, sort: ++photoMax
            });
            acc.withoutFile++;
            return acc;
          });
        });
      }, Promise.resolve({ rows: [], withoutFile: 0 })).then(function (photoAcc) {
        var photoOut = photoAcc.rows;

        /* ---- 3. 커플 정보(이름·만난 날·문구·D-day·색) — 아직 기본값일 때만 ---- */
        var jobs = [];
        var metaMoved = false;
        if (coupleIsPlain(self.couple)) {
          var patch = couplePatchOf(local.couple, swap);
          var clean = {};
          Object.keys(patch).forEach(function (k) {
            if (patch[k] !== undefined && patch[k] !== null && patch[k] !== "") clean[k] = patch[k];
          });
          if (Object.keys(clean).length) {
            metaMoved = true;
            jobs.push(client.from("couples").update(clean).eq("id", cid).then(function (r) {
              if (r && r.error) throw r.error;
              self.couple = Object.assign({}, self.couple, clean);
            }));
          }
        }

        /* ---- 4. 테마(settings) — 원격에 테마가 없을 때만 ---- */
        var themeRow = setRows.filter(function (r) { return r.key === "theme"; })[0];
        var themeEmpty = !themeRow || !themeRow.value || !Object.keys(themeRow.value).length;
        if (themeEmpty && local.theme && Object.keys(local.theme).length) {
          jobs.push(client.from("settings").upsert({ couple_id: cid, key: "theme", value: local.theme }, { onConflict: "couple_id,key" }).then(function (r) {
            if (r && r.error) throw r.error;
          }));
        }

        /* ---- 4-1. v27 노트 카드 묶음(settings groups) — 원격에 아직 없을 때만 ---- */
        var groupsRow = setRows.filter(function (r) { return r.key === K_GROUPS; })[0];
        var localGroups = normalizeGroups(local.groups);
        var localGroupTotal = localGroups.todo.length + localGroups.bucket.length + localGroups.log.length;
        if (groupsEmpty(groupsRow && groupsRow.value) && localGroupTotal) {
          jobs.push(client.from("settings").upsert({ couple_id: cid, key: K_GROUPS, value: localGroups }, { onConflict: "couple_id,key" }).then(function (r) {
            if (r && r.error) throw r.error;
          }));
        }

        /* ---- 4-2. 프로필 사진 — 이 폰에 있던 사진을 각자 몫으로 올립니다 ---- */
        var pics = (local.couple && local.couple.pics) || {};
        var avatarKeys = ["me", "you"].filter(function (w) {
          var src = avatarSrc(pics[w]);
          if (!src) return false;
          var key = avatarKeyOf(w, swap);
          var there = setRows.filter(function (r) { return r.key === key; })[0];
          return !(there && avatarSrc(there.value));      // 원격에 이미 그 사람 사진이 있으면 그대로
        });
        avatarKeys.forEach(function (w) {
          var key = avatarKeyOf(w, swap);
          jobs.push(client.from("settings").upsert({ couple_id: cid, key: key, value: { src: avatarSrc(pics[w]), at: Date.now() } }, { onConflict: "couple_id,key" }).then(function (r) {
            if (r && r.error) throw r.error;
          }));
        });
        if (avatarKeys.length) metaMoved = true;

        /* ---- 5. 행 쓰기 (바뀐 것만, 200개씩) ---- */
        if (evOut.length) jobs.push(writeChunks(client, "events", evOut));
        if (noteOut.length) jobs.push(writeChunks(client, "notes", noteOut));
        if (photoOut.length) jobs.push(writeChunks(client, "photos", photoOut));

        return Promise.all(jobs).then(function () {
          var moved = { events: evOut.length, notes: noteOut.length, photos: photoOut.length, meta: metaMoved, photosWithoutFile: photoAcc.withoutFile };
          return self.load().then(function (doc) {
            try {
              localStorage.setItem(flagKey, JSON.stringify({
                at: Date.now(), events: moved.events, notes: moved.notes, photos: moved.photos, meta: moved.meta
              }));
            } catch (e) {}
            return { ok: true, moved: moved, counts: moved.events + moved.notes + moved.photos, state: doc };
          });
        });
      });
    }).catch(function (e) {
      warn("migrate failed", e);
      return { ok: false, reason: "failed", error: String(e && e.message || e) };
    });
  };

  /* 이 기기에서 그 커플로 이미 옮겼는지 */
  SupabaseBackend.prototype.migratedFlag = function () {
    if (!this.couple) return null;
    try {
      var raw = localStorage.getItem(K_MIGRATED + this.couple.id);
      if (!raw) return null;
      var v = JSON.parse(raw);
      return v && typeof v === "object" ? v : { at: 0 };
    } catch (e) { return null; }
  };

  function writeChunks(client, table, rows) {
    var chunks = [];
    for (var i = 0; i < rows.length; i += 200) chunks.push(rows.slice(i, i + 200));
    return Promise.all(chunks.map(function (part) {
      return client.from(table).upsert(part).then(function (r) {
        if (r && r.error) throw r.error;
      });
    }));
  }

  /* =====================================================================
     v27: v26 에서 gid·groups 없이 올라간 노트 카드 묶음 자동 복구
     ---------------------------------------------------------------------
     v26 까지 sync.js 는 notes 의 payload 에 gid 를, settings 에 groups 를
     올리지 않았습니다. 그래서 이미 v26 으로 한 번 이전을 마친 폰
     (twolog.migrated.<coupleId> 있음)은 원격 notes 에 카드 정보가 없고
     화면에는 모든 항목이 기본 카드 한 개로 합쳐져 보입니다.

     이 폰(localStorage["twolog:v1:state"])에는 원본 groups 와 항목별 gid 가
     그대로 남아 있으므로, 로그인/앱 시작 때 한 번(플래그 twolog.groupsRepaired.<>):
       · 로컬 groups 를 settings key="groups" 행으로 올리고
       · 원격 notes 중 같은 항목(같은 id → 같은 kind+내용)의 payload 에
         원래 gid(와 빠진 상세 메모·완료 여부)를 채워 넣고
       · 원격에 없는 로컬 항목은 새로 넣습니다. (화면은 바로 다시 그립니다)
     한 번 복구한 뒤에는 플래그 때문에 다시 돌지 않습니다.
     ===================================================================== */
  SupabaseBackend.prototype.groupsRepairedFlag = function () {
    if (!this.couple) return null;
    try {
      var raw = localStorage.getItem(K_GROUPS_REPAIRED + this.couple.id);
      if (!raw) return null;
      var v = JSON.parse(raw);
      return v && typeof v === "object" ? v : { at: 0 };
    } catch (e) { return null; }
  };

  SupabaseBackend.prototype.repairGroups = function (opts) {
    var self = this;
    var force = !!(opts && opts.force);
    if (!this.couple || !this.user) return Promise.resolve({ ok: false, reason: "no_couple" });
    var cid = this.couple.id;
    var local = readLocalDoc();
    if (!local) return Promise.resolve({ ok: false, reason: "no_local" });

    var localGroups = normalizeGroups(local.groups);
    var localGroupTotal = localGroups.todo.length + localGroups.bucket.length + localGroups.log.length;
    var localNotes = arr(local.todos).length + arr(local.bucket).length + arr(local.logs).length;
    if (!localGroupTotal || !localNotes) return Promise.resolve({ ok: false, reason: "no_groups" });

    var flagKey = K_GROUPS_REPAIRED + cid;
    if (!force) {
      var already = false;
      try { already = !!localStorage.getItem(flagKey); } catch (e) {}
      if (already) return Promise.resolve({ ok: false, skipped: "already" });
    }

    var client = this.client;
    var swap = !!this.swap;
    var flip = function (who) {
      if (who !== "me" && who !== "you") return "both";
      if (!swap) return who;
      return who === "me" ? "you" : "me";
    };
    var whoToken = function (w) {
      if (!w || w === "함께" || w === "both") return "both";
      if (w === "나" || w === "me") return "me";
      return "you";
    };

    return Promise.all([
      client.from("notes").select("*").eq("couple_id", cid),
      client.from("settings").select("*").eq("couple_id", cid)
    ]).then(function (parts) {
      parts.forEach(function (r) { if (r && r.error) throw r.error; });
      var noteRows = parts[0].data || [];
      var setRows = parts[1].data || [];
      var groupsRow = setRows.filter(function (r) { return r.key === K_GROUPS; })[0];
      var groupsMissing = groupsEmpty(groupsRow && groupsRow.value);

      var live = noteRows.filter(function (r) { return !r.deleted; });
      var missingGid = live.filter(function (r) {
        return NOTE_ARR[r.kind] && !((r.payload || {}).gid);
      }).length;

      /* 이미 카드 묶음도 있고 모든 항목에 gid 가 있으면 할 일이 없음 */
      if (!force && !groupsMissing && !missingGid) return { ok: false, skipped: "nothing" };

      /* ---- 1. 원격 항목 ↔ 로컬 항목 맞추기 ---- */
      var used = {};                      // 로컬 항목 id
      var patches = [];                   // payload 를 보탤 원격 행
      live.forEach(function (r) {
        var arrKey = NOTE_ARR[r.kind];
        if (!arrKey) return;
        var items = arr(local[arrKey]);
        var p = r.payload || {};
        var it = items.filter(function (x) { return x && String(x.id) === String(r.id); })[0];
        if (!it) {
          var label = noteLabel(r.kind, p);
          it = items.filter(function (x) { return x && noteLabel(r.kind, x) === label; })[0];
        }
        if (!it) return;
        used[it.id] = true;
        var patch = {};
        if (!p.gid && it.gid) patch.gid = String(it.gid);
        if ((r.kind === "todo" || r.kind === "bucket") && p.memo === undefined && it.memo) patch.memo = String(it.memo);
        if (r.kind === "log" && p.done === undefined && typeof it.done === "boolean") patch.done = it.done;
        if (Object.keys(patch).length) {
          patches.push({
            id: r.id, couple_id: r.couple_id || cid, kind: r.kind, sort: r.sort || 0, deleted: !!r.deleted,
            payload: Object.assign({}, p, patch)
          });
        }
      });

      /* ---- 2. 원격에 아예 없는 로컬 항목은 새 행으로 ---- */
      var added = [];
      var sortMax = -1;
      live.forEach(function (r) { var v = Number(r.sort); if (!isNaN(v) && v > sortMax) sortMax = v; });
      Object.keys(NOTE_ARR).forEach(function (kind) {
        arr(local[NOTE_ARR[kind]]).forEach(function (it) {
          if (!it || typeof it !== "object") return;
          if (used[it.id]) return;
          added.push({
            id: String(it.id || freshId()), couple_id: cid, kind: kind, sort: ++sortMax,
            deleted: false, payload: notePayload(kind, it, flip, whoToken)
          });
        });
      });

      /* ---- 2-2. 커스텀 리스트(kind=list) — 항목 상세 메모도 채우고, 빠진 리스트는 더합니다 ---- */
      var localLists = arr(local.lists);
      var usedLists = {};
      live.filter(function (r) { return r.kind === "list"; }).forEach(function (r) {
        var p = r.payload || {};
        var l = localLists.filter(function (x) { return x && String(x.id) === String(r.id); })[0];
        if (!l) l = localLists.filter(function (x) { return x && String(x.title || "") === String(p.title || ""); })[0];
        if (!l) return;
        usedLists[l.id] = true;
        var srcItems = arr(p.items);
        var touched = false;
        var items = srcItems.map(function (it) {
          var mine = arr(l.items).filter(function (x) { return x && String(x.id) === String(it.id); })[0] ||
            arr(l.items).filter(function (x) { return x && String(x.text || "") === String(it.text || ""); })[0];
          if (!mine) return it;
          if (it.memo === undefined && mine.memo) { touched = true; return Object.assign({}, it, { memo: String(mine.memo) }); }
          return it;
        });
        if (!touched) return;
        patches.push({
          id: r.id, couple_id: r.couple_id || cid, kind: "list", sort: r.sort || 0, deleted: !!r.deleted,
          payload: Object.assign({}, p, { items: items })
        });
      });
      localLists.forEach(function (l) {
        if (!l || typeof l !== "object" || usedLists[l.id]) return;
        added.push({
          id: String(l.id || freshId()), couple_id: cid, kind: "list", sort: ++sortMax,
          deleted: false, payload: notePayload("list", l, flip, whoToken)
        });
      });

      var jobs = [];
      if (groupsMissing && localGroupTotal) {
        jobs.push(client.from("settings").upsert({ couple_id: cid, key: K_GROUPS, value: localGroups }, { onConflict: "couple_id,key" }).then(function (r) {
          if (r && r.error) throw r.error;
        }));
      }
      if (patches.length) jobs.push(writeChunks(client, "notes", patches));
      if (added.length) jobs.push(writeChunks(client, "notes", added));

      var wroteGroups = groupsMissing && !!localGroupTotal;
      if (!jobs.length) return { ok: false, skipped: "nothing" };

      return Promise.all(jobs).then(function () {
        return self.load().then(function (doc) {
          var counts = groupCount(localGroups);
          try {
            localStorage.setItem(flagKey, JSON.stringify({
              at: Date.now(), groups: counts, fixed: patches.length, added: added.length, groupsRow: wroteGroups
            }));
          } catch (e) {}
          return { ok: true, groups: counts, fixed: patches.length, added: added.length, groupsRow: wroteGroups, state: doc };
        });
      });
    }).catch(function (e) {
      warn("groups repair failed", e);
      return { ok: false, reason: "failed", error: String(e && e.message || e) };
    });
  };

  /* Realtime: 상대가 바꾸면 다시 읽어서 화면에 반영 */
  SupabaseBackend.prototype.subscribe = function (onRemote) {
    var self = this;
    if (!this.client || !this.couple) return function () {};
    var cid = this.couple.id;
    var channel = this.client.channel("twolog:" + cid);
    ["events", "notes", "photos", "settings"].forEach(function (table) {
      channel.on("postgres_changes", { event: "*", schema: "public", table: table, filter: "couple_id=eq." + cid }, function () { self.scheduleReload(onRemote); });
    });
    channel.on("postgres_changes", { event: "UPDATE", schema: "public", table: "couples", filter: "id=eq." + cid }, function () { self.scheduleReload(onRemote); });
    channel.subscribe(function (status) { log("realtime", status); });
    this.unsubscribe = function () { try { self.client.removeChannel(channel); } catch (e) {} };
    return this.unsubscribe;
  };

  SupabaseBackend.prototype.scheduleReload = function (onRemote) {
    var self = this;
    clearTimeout(this.reloadTimer);
    this.reloadTimer = setTimeout(function () {
      self.load().then(function (doc) {
        if (doc && onRemote) onRemote(doc);
      }).catch(function (e) { warn("reload failed", e); });
    }, 450);
  };

  /* =====================================================================
     store 파사드
     ===================================================================== */
  function createStore() {
    var forced = forcedMode();
    var remote = forced ? forced === "remote" : isRemote();
    var backend = remote ? new SupabaseBackend() : new LocalBackend();
    var listener = null;
    var subscribed = false;
    var saveTimer = null;
    var lastDoc = null;
    var status = { state: remote ? "connecting" : "local", at: 0, pending: 0 };

    /* 상대 기기 변경 구독 — 로그인 전에 시작해도, 로그인 뒤 자동으로 붙습니다. */
    function ensureSubscribed() {
      if (!remote || subscribed || !backend.couple || !backend.subscribe) return;
      subscribed = true;
      backend.subscribe(function (doc) {
        var ui = lastDoc ? lastDoc.ui : null;
        if (ui) doc.ui = Object.assign(doc.ui || {}, ui);
        lastDoc = doc;
        status.at = Date.now();
        status.state = "online";
        if (listener) listener(doc);
      });
    }

    /* v27: 앱이 다시 앞으로 나올 때 서버의 최신 상태를 당겨 옵니다.
       (홈 화면 앱·모바일 Safari 는 쉬는 동안 Realtime 연결이 끊길 수 있어요) */
    var pullTimer = null;
    function pullNow() {
      if (!remote || !backend.couple || !backend.load) return Promise.resolve(null);
      /* 아직 서버로 보내지 않은 변경이 있으면 그 저장이 끝난 뒤에 맞춥니다 */
      if (saveTimer || backend.saving) return Promise.resolve(null);
      return backend.load().then(function (doc) {
        if (!doc) return null;
        var ui = lastDoc ? lastDoc.ui : null;
        if (ui) doc.ui = Object.assign(doc.ui || {}, ui);
        var changed = true;
        try { changed = !lastDoc || JSON.stringify(doc) !== JSON.stringify(lastDoc); } catch (e) { changed = true; }
        lastDoc = doc;
        status.at = Date.now();
        status.state = "online";
        if (changed && listener) listener(doc);
        return doc;
      }).catch(function () { status.state = "offline"; return null; });
    }
    function schedulePull(delay) {
      if (!remote) return;
      clearTimeout(pullTimer);
      pullTimer = setTimeout(function () { pullTimer = null; pullNow(); }, delay == null ? 300 : delay);
    }

    var store = {
      mode: remote ? "remote" : "local",
      backend: backend,
      get coupleId() { return backend.couple ? backend.couple.id : null; },
      status: status,

      /* 앱 시작: 공유 상태 + 이 기기의 화면 상태(ui)를 합쳐서 돌려줍니다. */
      load: function () {
        return backend.load().then(function (doc) {
          var ui = null;
          try { var raw = localStorage.getItem(K_UI); if (raw) ui = JSON.parse(raw); } catch (e) {}
          if (doc && ui) doc.ui = Object.assign(doc.ui || {}, ui);
          status.state = remote ? "online" : "local";
          status.at = Date.now();
          if (doc) { lastDoc = doc; ensureSubscribed(); }
          return doc;
        }).catch(function (e) {
          warn("load failed", e);
          status.state = "offline";
          var cached = null;
          try { var raw = localStorage.getItem(K_STATE); if (raw) cached = JSON.parse(raw); } catch (err) {}
          var ui = null;
          try { var r2 = localStorage.getItem(K_UI); if (r2) ui = JSON.parse(r2); } catch (err2) {}
          if (cached && ui) cached.ui = Object.assign(cached.ui || {}, ui);
          return cached;
        });
      },

      /* 저장: 화면에서는 즉시, 디스크/서버에는 조금 모았다가(150ms) 씁니다. */
      persist: function (doc) {
        if (!doc) return;
        lastDoc = doc;
        var ui = doc.ui;
        var shared = JSON.parse(JSON.stringify(doc));
        delete shared.ui;
        try { if (ui) localStorage.setItem(K_UI, JSON.stringify(ui)); } catch (e) {}
        clearTimeout(saveTimer);
        saveTimer = setTimeout(function () { store.flush(); }, 150);
      },

      flush: function () {
        clearTimeout(saveTimer);
        saveTimer = null;
        var doc = lastDoc;
        if (!doc) return Promise.resolve(false);
        var shared = JSON.parse(JSON.stringify(doc));
        delete shared.ui;
        return backend.save(shared).then(function (ok) {
          status.at = Date.now();
          return ok;
        }).catch(function (e) {
          status.state = "offline";
          warn("save failed", e);
          return false;
        });
      },

      /* 상대 기기 변경 수신 */
      onRemote: function (cb) {
        listener = cb;
        ensureSubscribed();
        return Promise.resolve(function () {
          listener = null;
        });
      },

      reload: function () {
        return backend.load().then(function (doc) {
          if (doc) { lastDoc = doc; }
          return doc;
        }).catch(function (e) { warn("reload failed", e); return null; });
      },

      /* 사진 */
      photos: {
        add: function (file, meta) {
          return backend.addPhoto(file, meta);
        },
        urls: function (photos) {
          return backend.photoUrls(photos);
        },
        remove: function (photo) {
          return backend.deletePhoto(photo);
        }
      },

      /* 계정 */
      auth: {
        session: function () { return backend.session(); },
        signIn: function (email, pw) { return backend.signIn(email, pw); },
        signUp: function (email, pw) { return backend.signUp(email, pw); },
        signOut: function () {
          return backend.signOut().then(function () {
            /* v26: 로그아웃해도 이 기기에 남아 있던 로컬 기록(twolog:v1:state)은 지우지 않습니다.
               다음에 로그인할 때 그 기록을 다시 이어 올 수 있어야 하니까요. */
            try { localStorage.removeItem(K_LEVEL); } catch (e) {}
            return true;
          });
        }
      },

      /* 커플 연결 */
      couple: {
        myCode: function () { return backend.couple ? String(backend.couple.invite_code || "") : ""; },
        setCode: function (code) { return backend.setInviteCode(code); },
        join: function (code) { return backend.joinCouple(code); },
        leave: function () { return backend.leaveCouple(); },
        memberCount: function () { return backend.couple && backend.couple.members ? backend.couple.members.length : 1; },
        /* v26: 이 기기 사용자가 members[0] 인지 [1] 인지 (0/1) */
        mySlot: function () { return backend.swap ? 1 : 0; }
      },

      /* v26: 프로필 사진 — 사람별로 서버(settings)에 올립니다 */
      avatar: {
        set: function (who, dataUrl) {
          if (!remote) return Promise.resolve({ ok: true, local: true });
          return backend.setAvatar ? backend.setAvatar(who, dataUrl) : Promise.resolve({ ok: true });
        }
      },

      /* v26: 이 기기에 남아 있던 로컬 기록 — 요약과 이전 */
      local: {
        summary: function () { return localSummary(readLocalDoc()); },
        doc: function () { return readLocalDoc(); }
      },
      migrate: {
        /* opts.force === true 면 원격에 기록이 있어도 겹치지 않는 것만 더합니다.
           성공하면 store 가 들고 있는 마지막 상태도 옮긴 뒤의 것으로 바꿉니다
           (그러지 않으면 앱을 닫을 때 옛 빈 상태가 서버로 다시 밀려 기록을 지울 수 있어요). */
        run: function (opts) {
          if (!remote) return Promise.resolve({ ok: false, reason: "local_mode" });
          return backend.migrateLocal(opts || {}).then(function (res) {
            if (res && res.ok && res.state) {
              var ui = lastDoc ? lastDoc.ui : null;
              if (ui) res.state.ui = Object.assign(res.state.ui || {}, ui);
              lastDoc = res.state;
            }
            return res;
          });
        },
        done: function () { return remote && backend.migratedFlag ? backend.migratedFlag() : null; }
      },

      /* v27: v26 에서 카드 정보 없이 올라간 노트 카드 묶음 — 이 폰의 원본으로 1회 복구 */
      repairGroups: function (opts) {
        if (!remote) return Promise.resolve({ ok: false, reason: "local_mode" });
        if (!backend.repairGroups) return Promise.resolve({ ok: false, reason: "unsupported" });
        return backend.repairGroups(opts || {}).then(function (res) {
          if (res && res.ok && res.state) {
            var ui = lastDoc ? lastDoc.ui : null;
            if (ui) res.state.ui = Object.assign(res.state.ui || {}, ui);
            lastDoc = res.state;
          }
          return res;
        });
      },
      groupsRepaired: function () {
        return remote && backend.groupsRepairedFlag ? backend.groupsRepairedFlag() : null;
      },

      /* v27: 지금 서버 상태를 바로 당겨오기 (테스트·수동 확인용) */
      pull: pullNow,

      /* 이 기기 식별(충돌 방지용) */
      deviceId: (function () {
        try {
          var id = localStorage.getItem(K_DEVICE);
          if (!id) { id = randId() + Date.now().toString(36); localStorage.setItem(K_DEVICE, id); }
          return id;
        } catch (e) { return randId(); }
      })()
    };

    /* 저장 누락 방지: 앱이 가려지거나 닫힐 때 바로 쓰고,
       다시 앞으로 나오면(v27) 서버의 최신 상태를 조용히 당겨 옵니다. */
    try {
      global.addEventListener("pagehide", function () { store.flush(); });
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "hidden") store.flush();
        else schedulePull(250);
      });
      global.addEventListener("focus", function () { schedulePull(250); });
      global.addEventListener("pageshow", function () { schedulePull(250); });
      global.addEventListener("online", function () {
        status.state = remote ? "online" : "local";
        store.flush().then(function () { schedulePull(600); });
      });
    } catch (e) {}

    return store;
  }

  global.TwoLog = {
    CONFIG: CONFIG,
    isRemote: isRemote,
    createStore: createStore,
    compressImage: compressImage,
    util: { nowIso: nowIso, randId: randId }
  };
})(window);
