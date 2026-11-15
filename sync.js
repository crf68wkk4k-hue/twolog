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
    /* ↓↓↓ 여기 두 줄만 채우면 실시간 동기화가 켜집니다 (README 참고) ↓↓↓ */
    supabaseUrl: "",
    supabaseAnonKey: "",
    /* ↑↑↑ 비워 두면 local 모드로 동작합니다 ↑↑↑ */

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

  function isRemote() { return !!(CONFIG.supabaseUrl && CONFIG.supabaseAnonKey); }
  function nowIso() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
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
        createImageBitmap(file, { imageOrientation: "from-image" }).then(resolve, function () {
          fallback();
        });
      } else fallback();

      function fallback() {
        var url = URL.createObjectURL(file);
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
    return idbRun("readonly", function (store) { return store.get(id); }).then(function (blob) {
      if (blob) memPhotos[id] = blob;
      return blob || null;
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
        type: e.type || "date", memo: e.memo || "", who: flip(e.who)
      });
    });
    var push = function (kind, obj, sort, payload) {
      rows.notes.push({ id: String(obj.id), couple_id: coupleId, kind: kind, sort: sort, payload: payload, deleted: false });
    };
    (doc.todos || []).forEach(function (t, i) {
      push("todo", t, i, { text: t.text || "", done: !!t.done, who: flip(whoToken(t.who)) });
    });
    (doc.bucket || []).forEach(function (b, i) {
      push("bucket", b, i, { title: b.title || "", cat: b.cat || "기타", done: !!b.done, status: b.status || "" });
    });
    (doc.logs || []).forEach(function (l, i) {
      push("log", l, i, { kind: l.kind === "food" ? "food" : "movie", title: l.title || "", rating: Number(l.rating) || 0, date: l.date || nowIso(), review: l.review || "", place: l.place || "" });
    });
    (doc.lists || []).forEach(function (l, i) {
      push("list", l, i, { title: l.title || "", emoji: l.emoji || "📌", kind: l.kind === "memo" ? "memo" : "check", items: (l.items || []).map(function (it) { return { id: it.id, text: it.text || "", done: !!it.done }; }) });
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
        sched: { me: meSched, you: youSched, both: bothSched }
      },
      link: { code: String(coupleRow.invite_code || ""), connected: (coupleRow.members || []).length > 1, partnerCode: "" },
      auth: { out: false, email: "" },
      events: [], todos: [], bucket: [], logs: [], expenses: [], photos: [], lists: [],
      theme: { name: null, log: null, mode: "light" }
    };

    (eventRows || []).forEach(function (r) {
      doc.events.push({ id: r.id, date: r.date, time: r.time || "", title: r.title || "", type: r.type || "date", memo: r.memo || "", who: flip(r.who) });
    });
    (noteRows || []).filter(function (r) { return !r.deleted; }).sort(function (a, b) { return (a.sort || 0) - (b.sort || 0); })
      .forEach(function (r) {
        var p = r.payload || {};
        if (r.kind === "todo") doc.todos.push({ id: r.id, text: p.text || "", done: !!p.done, who: noteWhoLabel(p.who, flip, doc.couple) });
        else if (r.kind === "bucket") doc.bucket.push({ id: r.id, title: p.title || "", cat: p.cat || "기타", done: !!p.done, status: p.status || undefined });
        else if (r.kind === "log") doc.logs.push({ id: r.id, kind: p.kind === "food" ? "food" : "movie", title: p.title || "", rating: Number(p.rating) || 0, date: p.date || nowIso(), review: p.review || "", place: p.place || "" });
        else if (r.kind === "list") doc.lists.push({ id: r.id, title: p.title || "", emoji: p.emoji || "📌", kind: p.kind === "memo" ? "memo" : "check", items: (p.items || []).map(function (it) { return { id: it.id || randId(), text: it.text || "", done: !!it.done }; }) });
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

  SupabaseBackend.prototype.load = function () {
    var self = this;
    return this.whoAmI().then(function (user) {
      if (!user) return null;                     // 로그인 화면으로
      return self.ensureCouple();
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
    var cc = doc.couple.colors || {};
    var sc = doc.couple.sched || {};
    var couplePatch = {
      me: this.swap ? doc.couple.you : doc.couple.me,
      you: this.swap ? doc.couple.me : doc.couple.you,
      since: doc.couple.since,
      phrase: doc.couple.phrase || "함께한 지", fmt: doc.couple.fmt === "Y" ? "Y" : "D",
      colors: this.swap ? { me: cc.you, you: cc.me } : cc,
      sched: this.swap ? { me: sc.you, you: sc.me, both: sc.both } : sc
    };
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
    var remote = isRemote();
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
            try { localStorage.removeItem(K_STATE); localStorage.removeItem(K_LEVEL); } catch (e) {}
            return true;
          });
        }
      },

      /* 커플 연결 */
      couple: {
        myCode: function () { return backend.couple ? String(backend.couple.invite_code || "") : ""; },
        join: function (code) { return backend.joinCouple(code); },
        leave: function () { return backend.leaveCouple(); },
        memberCount: function () { return backend.couple && backend.couple.members ? backend.couple.members.length : 1; }
      },

      /* 이 기기 식별(충돌 방지용) */
      deviceId: (function () {
        try {
          var id = localStorage.getItem(K_DEVICE);
          if (!id) { id = randId() + Date.now().toString(36); localStorage.setItem(K_DEVICE, id); }
          return id;
        } catch (e) { return randId(); }
      })()
    };

    /* 저장 누락 방지: 앱이 가려지거나 닫힐 때 바로 씁니다. */
    try {
      global.addEventListener("pagehide", function () { store.flush(); });
      document.addEventListener("visibilitychange", function () { if (document.visibilityState === "hidden") store.flush(); });
      global.addEventListener("online", function () {
        status.state = remote ? "online" : "local";
        store.flush();
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
