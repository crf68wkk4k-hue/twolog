
(function () {
  "use strict";

  /* ------------------------------------------------------------------ utils */
  /* v22: 앱 버전 — 업데이트할 때 sw.js 의 VERSION(twolog-vNN)과 함께 올려 주세요.
     My 탭 맨 윗줄 오른쪽에 「버전 vNN」으로 보입니다. */
  var APP_VERSION = "v32";
  var KEY = "couple-app-v1";
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var pad = function (n) { return String(n).padStart(2, "0"); };
  var iso = function (d) { return d.getFullYear() + "-" + pad(d.getMonth() + 1) + "-" + pad(d.getDate()); };
  var parse = function (s) { var p = String(s).split("-").map(Number); return new Date(p[0], p[1] - 1, p[2]); };
  var addDays = function (s, n) { var d = parse(s); d.setDate(d.getDate() + n); return iso(d); };
  var diffDays = function (a, b) { return Math.round((parse(b) - parse(a)) / 86400000); };
  var today = iso(new Date());
  var won = function (n) { return Math.round(n).toLocaleString("ko-KR"); };
  var uid = function () { return Math.random().toString(36).slice(2, 9); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var WD = ["일", "월", "화", "수", "목", "금", "토"];
  function byDateAsc(a, b) { if (a.date === b.date) return 0; return a.date < b.date ? -1 : 1; }
  function byDateDesc(a, b) { if (a.date === b.date) return 0; return a.date < b.date ? 1 : -1; }
  function byTimeAsc(a, b) {
    var x = a.time || "99:99", y = b.time || "99:99";
    if (x === y) return 0;
    return x < y ? -1 : 1;
  }
  function josa(name, withBatchim, without) {
    var s = String(name || "");
    if (!s) return without;
    var c = s.charCodeAt(s.length - 1);
    if (c < 0xac00 || c > 0xd7a3) return without;
    return (c - 0xac00) % 28 ? withBatchim : without;
  }

  /* ------------------------------------------------------------------ icons */
  var svg = function (d, w) {
    return '<svg width="' + (w || 20) + '" height="' + (w || 20) + '" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">' + d + "</svg>";
  };
  var IC = {
    home: svg('<path d="M4 10.6 12 4l8 6.6V19a1.4 1.4 0 0 1-1.4 1.4h-3.7v-5.6H9.1v5.6H5.4A1.4 1.4 0 0 1 4 19z"/>', 21),
    cal: svg('<rect x="3.6" y="5.4" width="16.8" height="15"/><path d="M8.2 3.4v3.4M15.8 3.4v3.4M3.6 10.2h16.8"/>', 21),
    diary: svg('<rect x="4.2" y="3" width="15.6" height="18"/><path d="M8.4 3v18"/><path d="M12 8.2h4.2M12 12h4.2"/>', 21),
    photo: svg('<rect x="3.4" y="4.6" width="17.2" height="14.8"/><circle cx="8.9" cy="9.7" r="1.5"/><path d="M4.2 17.2l4.4-4.3a1.7 1.7 0 0 1 2.4 0l3.1 3 1.6-1.5a1.7 1.7 0 0 1 2.3 0l2 1.9"/>', 21),
    plus: svg('<path d="M12 5.5v13M5.5 12h13"/>', 18),
    x: svg('<path d="M6.5 6.5l11 11M17.5 6.5l-11 11"/>', 16),
    pencil: svg('<path d="M4.5 19.5h3.6l9.7-9.7-3.6-3.6-9.7 9.7z"/><path d="M15.1 4.7l2.3-2.3 3.6 3.6-2.3 2.3"/>', 15),
    left: svg('<path d="M14.5 6l-6 6 6 6"/>', 18),
    right: svg('<path d="M9.5 6l6 6-6 6"/>', 18),
    check: svg('<path d="M5 12.6l4.2 4.2L19 7"/>', 13),
    palette: svg('<path d="M12 3.4a8.6 8.6 0 1 0 0 17.2c1.1 0 1.9-.8 1.9-1.8 0-.9-.6-1.4-.6-2.1 0-.8.7-1.4 1.5-1.4h1.4a4.3 4.3 0 0 0 4.3-4.3c0-4.2-3.7-7.6-8.5-7.6z"/><circle cx="8.3" cy="9.8" r="1" fill="currentColor" stroke="none"/><circle cx="12" cy="7.8" r="1" fill="currentColor" stroke="none"/><circle cx="15.7" cy="9.7" r="1" fill="currentColor" stroke="none"/>', 17),
    gear: svg('<path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h11M19 17h1"/><circle cx="15" cy="7" r="1.9"/><circle cx="9" cy="12" r="1.9"/><circle cx="17.5" cy="17" r="1.9"/>', 21),
    person: svg('<circle cx="12" cy="8.3" r="3.5"/><path d="M5.2 20c0-3.4 3.1-5.7 6.8-5.7s6.8 2.3 6.8 5.7"/>', 21),
    search: svg('<circle cx="10.8" cy="10.8" r="6.2"/><path d="M15.4 15.4l4.1 4.1"/>', 20),
    grid: svg('<rect x="3.6" y="3.6" width="7" height="7"/><rect x="13.4" y="3.6" width="7" height="7"/><rect x="3.6" y="13.4" width="7" height="7"/><rect x="13.4" y="13.4" width="7" height="7"/>', 18),
    /* v28: 노트 알약 탭 옆 — 「목록 +」 아이콘 */
    listPlus: svg('<path d="M4.6 6.4h9.2M4.6 11h6.4M4.6 15.6h4.4"/><path d="M17.6 12.4v6.2M14.5 15.5h6.2"/>', 20)
  };
  var STAR = '<svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2.8l2.86 5.94 6.54.9-4.77 4.55 1.18 6.5L12 17.6l-5.81 3.09 1.18-6.5L2.6 9.64l6.54-.9z"/></svg>';

  function stars(rating) {
    var pct = Math.max(0, Math.min(5, rating)) / 5 * 100;
    return '<span class="stars"><span class="bg">' + STAR.repeat(5) + '</span><span class="fg" style="width:' + pct + '%">' + STAR.repeat(5) + "</span></span>";
  }

  /* ------------------------------------------------------------------ seed */
  function seed() {
    var t = today;
    return {
      couple: { me: "소영", you: "준영", since: addDays(t, -365), fmt: "D", phrase: "함께한 지", colors: { me: "#9E636B", you: "#3D5C82" }, sched: { me: "#9E636B", you: "#3D5C82", both: "#625A7F" } },
      link: { code: "371502", connected: true, partnerCode: "" },
      auth: { out: false },
      events: [
        { id: uid(), date: t, time: "19:00", title: "성수 데이트", type: "date", memo: "파스타 · 와인 한 잔", who: "both" },
        { id: uid(), date: t, time: "12:30", title: "치과 예약", type: "etc", memo: "오후 1시까지", who: "me" },
        { id: uid(), date: t, time: "20:30", title: "청모모임!", type: "etc", memo: "성수", who: "me" },
        { id: uid(), date: addDays(t, 3), time: "", title: "휴가가는 날", type: "trip", memo: "", who: "both" },
        { id: uid(), date: addDays(t, 8), time: "18:00", title: "준영 회식", type: "etc", memo: "", who: "you" },
        { id: uid(), date: t, time: "", title: "만난 지 1주년", type: "anni", memo: "", who: "both" },
        { id: uid(), date: addDays(t, 6), time: "15:00", title: "영화 보는 날", type: "date", memo: "용산 CGV", who: "both" },
        { id: uid(), date: addDays(t, 11), time: "", title: "준영 생일", type: "anni", memo: "", who: "you" },
        { id: uid(), date: addDays(t, -3), time: "13:00", title: "북한산 산행", type: "trip", memo: "우이신설역 10시", who: "both" },
        { id: uid(), date: addDays(t, 24), time: "", title: "제주 여행 예약", type: "trip", memo: "숙소 결제", who: "both" }
      ],
      todos: [
        { id: uid(), text: "주말 장보기", done: true, who: "함께" },
        { id: uid(), text: "12월 여행 항공권 예약", done: false, who: "함께" },
        { id: uid(), text: "침구 세탁", done: false, who: "나" },
        { id: uid(), text: "준영 자전거 수리 맡기기", done: false, who: "준영" },
        { id: uid(), text: "냉장고 정리", done: true, who: "나" },
        { id: uid(), text: "커플 사진 인화", done: false, who: "함께" }
      ],
      bucket: [
        { id: uid(), title: "제주도 3박 4일", cat: "여행", done: false, status: "doing" },
        { id: uid(), title: "오사카 먹방 여행", cat: "여행", done: false },
        { id: uid(), title: "한강 자전거 한 바퀴", cat: "취미", done: true },
        { id: uid(), title: "미슐랭 라멘 리스트 정복", cat: "맛집", done: false, status: "doing" },
        { id: uid(), title: "도자기 원데이 클래스", cat: "취미", done: true }
      ],
      logs: [
        { id: uid(), kind: "movie", title: "화양연화", rating: 4.5, date: addDays(t, -7), review: "다시 봐도 여운이 오래 남는 색감.", done: true },
        { id: uid(), kind: "food", title: "성수 파스타", rating: 4, date: addDays(t, -3), review: "트러플 크림은 꼭. 웨이팅 30분.", done: true },
        { id: uid(), kind: "movie", title: "그대들은 어떻게 살 것인가", rating: 5, date: addDays(t, -20), review: "같이 보고 한참 얘기했다.", done: true }
      ],
      expenses: [
        { id: uid(), date: addDays(t, -3), amount: 38000, cat: "식비", memo: "성수 파스타", payer: "준영" },
        { id: uid(), date: addDays(t, -7), amount: 54000, cat: "데이트", memo: "영화 + 팝콘", payer: "나" },
        { id: uid(), date: addDays(t, -7), amount: 12400, cat: "교통", memo: "택시", payer: "준영" },
        { id: uid(), date: addDays(t, -10), amount: 89000, cat: "생활", memo: "침구 세트", payer: "나" },
        { id: uid(), date: addDays(t, -12), amount: 26500, cat: "식비", memo: "장보기", payer: "함께" },
        { id: uid(), date: addDays(t, -5), amount: 120000, cat: "기타", memo: "콘서트 예매", payer: "함께" }
      ],
      photos: [
        { id: uid(), date: addDays(t, -6), album: "성수, 늦가을", title: "골목 산책", place: "서울 성수동", memo: "해 질 무렵 골목이 제일 예뻤다.", art: 10, capBg: "#FAEDE8" },
        { id: uid(), date: addDays(t, -6), album: "성수, 늦가을", title: "첫 커피", place: "성수 카페", memo: "아메리카노 두 잔, 창가 자리.", art: 0, capBg: "#FBF6EE" },
        { id: uid(), date: addDays(t, -6), album: "성수, 늦가을", title: "창가 자리", place: "성수 카페", memo: "", art: 1, capBg: "#FFFFFF" },
        { id: uid(), date: addDays(t, -6), album: "성수, 늦가을", title: "저녁 산책", place: "서울숲", memo: "", art: 7, capBg: "#EDF1EC" },
        { id: uid(), date: addDays(t, -6), album: "성수, 늦가을", title: "LP 한 장", place: "성수 레코드", memo: "고른 LP는 아직도 안 틀어봤다.", art: 4, capBg: "#F8EBEE" },
        { id: uid(), date: addDays(t, -6), album: "성수, 늦가을", title: "늦은 저녁", place: "성수", memo: "", art: 5, capBg: "#ECF2F7" },
        { id: uid(), date: addDays(t, -28), album: "북한산", title: "정상에서", place: "북한산", memo: "생각보다 힘들었다.", art: 2, capBg: "#EDF1EC" },
        { id: uid(), date: addDays(t, -28), album: "북한산", title: "단풍", place: "북한산", memo: "", art: 3, capBg: "#FAEDE8" },
        { id: uid(), date: addDays(t, -28), album: "북한산", title: "김밥 타임", place: "북한산", memo: "정상에서 먹은 김밥이 제일 맛있었다.", art: 11, capBg: "#FBF3DE" },
        { id: uid(), date: addDays(t, -105), album: "여름, 강릉", title: "바다", place: "강릉 안목", memo: "", art: 6, capBg: "#ECF2F7" },
        { id: uid(), date: addDays(t, -105), album: "여름, 강릉", title: "커피거리", place: "강릉", memo: "", art: 9, capBg: "#FFFFFF" },
        { id: uid(), date: addDays(t, -105), album: "여름, 강릉", title: "노을", place: "강릉", memo: "이 시간에 맞춰 다시 오기로.", art: 8, capBg: "#F8EBEE" }
      ],
      lists: [
        { id: uid(), title: "여행 준비물", emoji: "🧳", kind: "check", items: [
          { id: uid(), text: "여권 · 신분증", done: true },
          { id: uid(), text: "충전기 · 보조배터리", done: false },
          { id: uid(), text: "상비약", done: false }
        ] },
        { id: uid(), title: "주말 데이트", emoji: "🎈", kind: "memo", items: [
          { id: uid(), text: "토요일 오후 — 성수 카페 골목\n저녁은 파스타, 예약은 금요일에." }
        ] }
      ],
      ui: { seg: "todo", expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today }
    };
  }

  /* ------------------------------------------------------------------ store */
  /* S(공유 상태)는 sync.js 가 불러옵니다. 이 파일은 그리기와 상호작용만 담당해요. */
  var S = null;
  var Store = null;
  var PHOTO_URLS = {};          // photo id -> 렌더링용 URL (IndexedDB blob 또는 원격 URL)
  var BOOTED = false;
  var pendingFiles = [];        // 사진 추가 시트에서 고른 파일
  var pendingUrls = [];         // 시트 미리보기 objectURL (닫을 때 정리)
  var loginMode = "in";         // remote 모드 로그인 화면: in | up

  function normalizeState(s) {
  S = s;
  /* 이전 초기값(상대 이름 "민준")을 저장해 둔 기기는 한 번만 "준영"으로 바꿉니다.
     이후에 설정에서 직접 고친 이름은 mig 표시 덕분에 건드리지 않아요. */
  if (!S.mig || typeof S.mig !== "object") S.mig = {};
  if (!S.mig.palette) {
    var OLDCOL = { "#F7C6D4": "#9E636B", "#BCE0F7": "#3D5C82", "#D6C5F7": "#625A7F" };
    ["me", "you", "both"].forEach(function (w) {
      var sc = String(((S.couple.sched || {})[w]) || "").toUpperCase();
      var ac = String(((S.couple.colors || {})[w]) || "").toUpperCase();
      if (OLDCOL[sc]) S.couple.sched[w] = OLDCOL[sc];
      if (OLDCOL[ac]) S.couple.colors[w] = OLDCOL[ac];
    });
    S.mig.palette = 1;
  }
  if (!S.mig.you) {
    if (S.couple && S.couple.you === "민준") S.couple.you = "준영";
    S.mig.you = 1;
  }
  if (!S.ui) S.ui = { seg: "todo", expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today };
  if (!S.theme || typeof S.theme !== "object") S.theme = { name: null, log: null };
  if (!("name" in S.theme)) S.theme.name = null;
  if (!("log" in S.theme)) S.theme.log = null;
  if (S.theme.mode !== "dark") S.theme.mode = "light";
  if (!S.theme.pages || typeof S.theme.pages !== "object") S.theme.pages = {};
  if (!S.note || typeof S.note !== "object") S.note = {};
  /* v18: My 탭 4자리 화면 잠금 (이 기기에만 저장) */
  ["todo", "bucket", "log"].forEach(function (k) {
    if (!S.note[k] || typeof S.note[k] !== "object") S.note[k] = {};
    if (typeof S.note[k].e !== "string") S.note[k].e = NOTE_DEF[k].e;
    if (typeof S.note[k].n !== "string" || !S.note[k].n) S.note[k].n = NOTE_DEF[k].n;
  });
  if (S.couple.fmt !== "Y") S.couple.fmt = "D";
  if (typeof S.couple.phrase !== "string" || !S.couple.phrase.trim()) S.couple.phrase = defaultPhrase();
  if (!S.mig.phrase) {
    if (S.couple.phrase === "함께한 지") S.couple.phrase = defaultPhrase();
    S.mig.phrase = 1;
  }
  if (!S.couple.colors || typeof S.couple.colors !== "object") S.couple.colors = {};
  if (!S.couple.birthdays || typeof S.couple.birthdays !== "object") S.couple.birthdays = {};
  if (typeof S.couple.birthdays.me !== "string") S.couple.birthdays.me = S.couple.me === "소영" ? "6월 26일" : "";
  if (typeof S.couple.birthdays.you !== "string") S.couple.birthdays.you = "";
  if (!S.theme || typeof S.theme !== "object") S.theme = { name: null, log: null };
  /* v14: 「다가오는 일정」과 「{월}월의 우리」 제목 색을 하나(homeTitleBg)로 묶었어요.
     v13 에서 따로 저장해 둔 색은 한 번만 옮겨 오고 비웁니다. */
  if (!("homeTitleBg" in S.theme)) S.theme.homeTitleBg = S.theme.schedBg || S.theme.ourBg || null;
  if (!S.mig.homeBg) {
    if (S.theme.schedBg || S.theme.ourBg) S.theme.schedBg = S.theme.ourBg = null;
    S.mig.homeBg = 1;
  }
  if (!S.couple.pics || typeof S.couple.pics !== "object") S.couple.pics = {};
  if (!("me" in S.couple.colors)) S.couple.colors.me = "#9E636B";
  if (!("you" in S.couple.colors)) S.couple.colors.you = "#3D5C82";
  if (!S.couple.sched || typeof S.couple.sched !== "object") S.couple.sched = {};
  ["me", "you", "both"].forEach(function (k) {
    if (!S.couple.sched[k]) S.couple.sched[k] = SCHED_DEFAULT[k];
  });
  if (!S.link || typeof S.link !== "object") S.link = { code: "371502", connected: true, partnerCode: "" };
  if (!/^\d{6}$/.test(String(S.link.code || ""))) S.link.code = "371502";
  if (!("connected" in S.link)) S.link.connected = true;
  if (!S.auth || typeof S.auth !== "object") S.auth = { out: false };
  if (!Array.isArray(S.lists)) S.lists = [];
  if (!S.theme || typeof S.theme !== "object") S.theme = { mode: "light", name: null, log: null };
  if (!S.notif || typeof S.notif !== "object") S.notif = {};
  ["anni", "today", "dday"].forEach(function (k) {
    if (typeof S.notif[k] !== "boolean") S.notif[k] = k !== "dday";
  });
  /* 노트: 텝 안의 리스트(그룹). 예전 항목은 첫 번째 리스트로 옮겨 하나도 사라지지 않게 */
  if (!S.groups || typeof S.groups !== "object") S.groups = {};
  ["todo", "bucket", "log"].forEach(function (k) {
    if (!Array.isArray(S.groups[k])) S.groups[k] = [];
    S.groups[k] = S.groups[k].filter(function (g) { return g && typeof g === "object"; });
    S.groups[k].forEach(function (g) {
      if (!g.id) g.id = uid();
      if (typeof g.title !== "string") g.title = "";
      if ("topic" in g) delete g.topic;   /* v17: 카드 윗줄「주제」가 없어져 예전에 적어 둔 값도 지워요 */
      if (typeof g.caption !== "string") g.caption = "";
      if (g.who !== "you") g.who = "me";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || "")) || isNaN(parse(g.date).getTime())) g.date = today;
    });
    if (!S.groups[k].length) {
      S.groups[k].push({ id: uid(), title: (NOTE_DEF[k] || {}).n || "할 일", caption: "" });
    }
    var gids = S.groups[k].map(function (g) { return g.id; });
    var arr = S[{ todo: "todos", bucket: "bucket", log: "logs" }[k]] || [];
    arr.forEach(function (it) {
      if (!it || typeof it !== "object") return;
      if (!it.gid || gids.indexOf(it.gid) < 0) it.gid = gids[0];
    });
  });
  S.events.forEach(function (e) {
    if (e.who !== "me" && e.who !== "you" && e.who !== "both") e.who = "both";
    /* 예전 한 칸짜리 일정은 종료일 = 시작일 */
    var st = String(e.date || "").slice(0, 10);
    if (!e.date || !/^\d{4}-\d{2}-\d{2}$/.test(st)) e.date = today;
    if (!e.endDate || !/^\d{4}-\d{2}-\d{2}$/.test(String(e.endDate)) || String(e.endDate) < String(e.date)) e.endDate = e.date;
    /* v31: 일정에 고른 색은 대문자 #RRGGBB 만 인정 — 아니면 담당자 색을 씁니다 */
    var ecolNow = String(e.color == null ? "" : e.color).toUpperCase();
    e.color = /^#[0-9A-F]{6}$/.test(ecolNow) ? ecolNow : "";
  });
  if (!Array.isArray(S.photos)) S.photos = [];
  S.photos.forEach(function (p) {
    if (!p || typeof p !== "object") return;
    if (typeof p.capBg === "string" && /^#[0-9a-fA-F]{6}$/.test(p.capBg)) p.capBg = p.capBg.toUpperCase();
    else p.capBg = null;
  });
  S.lists.forEach(function (l) {
    if (!l || typeof l !== "object") return;
    if (!l.id) l.id = uid();
    if (l.kind !== "memo") l.kind = "check";
    if (!l.emoji) l.emoji = "📌";
    if (!Array.isArray(l.items)) l.items = [];
  });
  S.lists = S.lists.filter(function (l) { return l && typeof l === "object"; });
  return S;
  }

  /* 저장: 화면에서 곧바로 호출할 수 있도록 동기 함수로 두고, 실제 쓰기는 sync.js 가 처리합니다. */
  function save() {
    if (!S || !Store) return;
    try { Store.persist(S); } catch (e) {}
  }

  /* ==========================================================================
     v26: 폰에 남아 있던 예전 로컬 기록(localStorage·IndexedDB)을 새 커플 공간으로
     이어 오기. 실제 업로드는 sync.js 의 Store.migrate 가 합니다.
     ========================================================================== */
  function localSummaryLine(info) {
    if (!info) return "";
    var parts = [];
    if (info.events) parts.push("일정 " + info.events + "개");
    if (info.notes) parts.push("노트 " + info.notes + "개");
    if (info.photos) parts.push("사진 " + info.photos + "장");
    if (!parts.length && info.customized) parts.push("커플 정보·설정");
    return parts.join(" · ");
  }
  function migrateToast(res) {
    if (!res || !res.ok) return "";
    var line = res.moved ? localSummaryLine({ events: res.moved.events, notes: res.moved.notes, photos: res.moved.photos }) : "";
    if (!line && res.moved && res.moved.meta) return "폰에 있던 커플 정보를 이어 왔어요";
    if (!line) return "";
    return "폰에 있던 예전 기록을 이어 왔어요 · " + line;
  }
  function localReadyInfo() {
    if (!Store || Store.mode !== "remote" || !Store.local) return null;
    var info = null;
    try { info = Store.local.summary(); } catch (e) { info = null; }
    return info && info.has ? info : null;
  }
  /* 이전 결과의 상태를 화면에 반영 (사진 주소는 다시 받아 옵니다) */
  function applyMigrated(res) {
    if (!res || !res.ok || !res.state) return false;
    var keepUi = S ? S.ui : null;
    S = normalizeState(res.state);
    if (keepUi) S.ui = keepUi;
    S.auth.out = false;
    var u = Store && Store.backend && Store.backend.user;
    if (u && u.email) S.auth.email = u.email;
    applyTheme(); renderAll(); loadPhotoUrls();
    var msg = migrateToast(res);
    if (msg) toast(msg);
    return true;
  }
  /* 앱 시작 직후: 로그인된 기기에 예전 기록이 남아 있으면 자동 1회 이전 */
  function joinLocalHistory() {
    if (!Store || Store.mode !== "remote" || !Store.migrate || !S) return Promise.resolve(false);
    return Store.migrate.run({}).then(function (res) {
      if (res && res.ok && res.state) { applyMigrated(res); return true; }
      if (current === "set") renderSet();
      return false;
    }).catch(function () { return false; });
  }
  /* 로그인·커플 연결 직후: 이전을 마친 상태(doc)를 받아 화면을 그립니다 */
  function withLocalHistory(doc, done) {
    if (!Store || Store.mode !== "remote" || !Store.migrate) { done(doc, null); return; }
    Store.migrate.run({}).then(function (res) {
      done(res && res.state ? res.state : doc, res);
    }, function () { done(doc, null); });
  }

  /* ==========================================================================
     v27: v26 에서 카드 정보(gid·groups) 없이 올라간 노트를 이 폰의 원본으로 1회 복구
     — 메모 2개·버킷 3개처럼 나눠 둔 카드와 그 안의 항목이 원래 자리로 돌아옵니다.
     ========================================================================== */
  function repairNoteGroups() {
    if (!Store || Store.mode !== "remote" || !Store.repairGroups || !S) return Promise.resolve(false);
    return Store.repairGroups().then(function (res) {
      if (!res || !res.ok || !res.state) return false;
      var keepUi = S ? S.ui : null;
      S = normalizeState(res.state);
      if (keepUi) S.ui = keepUi;
      S.auth.out = false;
      var u = Store && Store.backend && Store.backend.user;
      if (u && u.email) S.auth.email = u.email;
      applyTheme(); renderAll(); loadPhotoUrls();
      var g = res.groups || {};
      var parts = [];
      if (g.todo) parts.push("메모 " + g.todo + "개");
      if (g.bucket) parts.push("버킷 " + g.bucket + "개");
      if (g.log) parts.push("영화·먹방 " + g.log + "개");
      toast("노트 카드를 되살렸어요" + (parts.length ? " · " + parts.join(" · ") : ""));
      if (current === "set") renderSet();
      return true;
    }).catch(function () { return false; });
  }

  /* ------------------------------------------------------------------ color theme */
  /* 팔레트 버튼에서 고르는 차분한 10색 (일정 색과 같은 톤) */
  var PALETTE = [
    { n: "로즈브라운", c: "#9E636B" }, { n: "테라코타", c: "#BD6C48" }, { n: "머스터드", c: "#A68C53" },
    { n: "올리브", c: "#5B7048" }, { n: "세이지", c: "#537B67" }, { n: "네이비", c: "#3D5C82" },
    { n: "플럼", c: "#625A7F" }, { n: "코코아", c: "#745A4A" }, { n: "샌드", c: "#9B816C" }, { n: "차콜", c: "#4A4A4C" }
  ];
  /* 홈 섹션 제목 줄(캡션)·기본 버튼에 칠하는 12색 — 소영님이 고른 팔레트(IMG_4508), 4열 3줄 */
  var MUTED = [
    { n: "블러시", c: "#F2CFC9" }, { n: "로즈", c: "#DEA2A6" }, { n: "코랄", c: "#DD785B" }, { n: "오렌지", c: "#EA994D" },
    { n: "레몬", c: "#EFD353" }, { n: "라임", c: "#C4C66A" }, { n: "세이지", c: "#B8CAA5" }, { n: "민트", c: "#B4D8D4" },
    { n: "청록", c: "#80A4AA" }, { n: "라벤더", c: "#D2CBE3" }, { n: "모브", c: "#A299B8" }, { n: "샌드", c: "#C4B28E" }
  ];
  var SOFT = [
    { n: "핑크", c: "#F7C6D4" }, { n: "스카이", c: "#BCE0F7" }, { n: "라벤더", c: "#D6C5F7" }, { n: "민트", c: "#C8E9D5" },
    { n: "버터", c: "#F8E6A8" }, { n: "피치", c: "#FAD4C0" }, { n: "라임", c: "#DDEBC0" }, { n: "로즈", c: "#EFD3DC" }
  ];
  var SCHED_DEFAULT = { me: "#9E636B", you: "#3D5C82", both: "#625A7F" };
  /* 일정·프로필 색 팔레트 (12색) */
  var OWNER_COLORS = ["#9E636B", "#BD6C48", "#A68C53", "#5B7048", "#537B67",
    "#3D5C82", "#625A7F", "#745A4A", "#9B816C", "#4A4A4C"];
  /* v19: 밝기 계산을 한 곳으로 — 제목 줄 글씨(inkOn)와 버튼 글씨(btnInk)가 같은 값을 씁니다 */
  function lumOf(hex) {
    var h = String(hex || "").replace("#", "");
    if (h.length === 3) h = h.charAt(0) + h.charAt(0) + h.charAt(1) + h.charAt(1) + h.charAt(2) + h.charAt(2);
    if (!/^[0-9a-fA-F]{6}$/.test(h)) return null;
    var n = parseInt(h, 16);
    var lin = function (c) { return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    return 0.2126 * lin(((n >> 16) & 255) / 255) + 0.7152 * lin(((n >> 8) & 255) / 255) + 0.0722 * lin((n & 255) / 255);
  }
  function inkOn(hex) {
    var L = lumOf(hex);
    if (L === null) return "#111111";
    return L > 0.5 ? "#111111" : "#FFFFFF";
  }
  /* v19: 확인·기본 버튼(완료·저장하기·추가하기 …) 글씨는 테라코타·파스텔·뮤트 12색 어느 쪽이든
     검정으로 또렷하게. 배경이 검정에 가까운 아주 어두운 색(L ≤ 0.09)일 때만 흰 글씨로 둡니다. */
  function btnInk(hex) {
    var L = lumOf(hex);
    if (L === null) return "#111111";
    return L <= 0.09 ? "#FFFFFF" : "#111111";
  }
  function setOwnerColor(who, hex) {
    var v = String(hex || "").toUpperCase();
    if (!/^#[0-9A-F]{6}$/.test(v)) return;
    S.couple.colors = S.couple.colors || {};
    S.couple.sched = S.couple.sched || {};
    S.couple.colors[who] = v;
    S.couple.sched[who] = v;
    save(); applyTheme(); renderAll();
    if (personSheetWho) openPersonSheet(personSheetWho);
  }
  /* v27: 프로필 시트의 컬러 — 이름·네모 칸 없이 「컬러」 라벨 + 동그란 12색(뮤트)만 */
  function prColorRow(who) {
    var cur = String(sched(who) || "").toUpperCase();
    var h = '<div class="pr-sws">';
    MUTED.forEach(function (p) {
      h += '<button type="button" class="sw rsw' + (cur === p.c ? " sel" : "") + '" data-act="pickOwner" data-who="' + who +
        '" data-color="' + p.c + '" style="background:' + p.c + '" aria-label="' + p.n + " " + p.c + '"></button>';
    });
    return h + "</div>";
  }
  function colorPickRow(who) {
    var cur = String(sched(who) || "").toUpperCase();
    var h = '<div class="own-block"><div class="own-hd"><span class="own-nm">' + esc(schedName(who)) + "</span>" +
      '<span class="own-chip" style="background:' + cur + '"></span>' +
      '<label class="own-pick"><input type="color" class="js-own" data-who="' + who + '" value="' + (cur || "#D96B52") + '"><span>컬러</span></label></div>';
    h += '<div class="own-sws">';
    OWNER_COLORS.forEach(function (c) {
      h += '<button type="button" class="sw osw' + (cur === c ? " sel" : "") + '" data-act="pickOwner" data-who="' + who +
        '" data-color="' + c + '" style="background:' + c + '" aria-label="' + esc(schedName(who)) + " " + c + '"></button>';
    });
    h += "</div></div>";
    return h;
  }
  function sched(w) {
    var c = (S.couple.sched || {})[w];
    return c || SCHED_DEFAULT[w] || SCHED_DEFAULT.both;
  }
  function schedName(w) {
    if (w === "me") return S.couple.me;
    if (w === "you") return S.couple.you;
    return "공동";
  }

  function rgba(hex, a) {
    var h = String(hex || "").replace("#", "");
    if (h.length === 3) h = h.charAt(0) + h.charAt(0) + h.charAt(1) + h.charAt(1) + h.charAt(2) + h.charAt(2);
    if (!/^[0-9a-fA-F]{6}$/.test(h)) return "rgba(28,28,30," + a + ")";
    var n = parseInt(h, 16);
    return "rgba(" + ((n >> 16) & 255) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")";
  }
  function modeIcon() {
    var dark = (S.theme || {}).mode === "dark";
    return '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7">' +
      '<rect x="3.6" y="3.6" width="16.8" height="16.8"/><path d="M12 3.6v16.8"/>' +
      '<rect x="3.6" y="3.6" width="8.4" height="16.8" fill="currentColor" stroke="none" style="opacity:' + (dark ? 0 : 1) + '"/>' +
      '<rect x="12" y="3.6" width="8.4" height="16.8" fill="currentColor" stroke="none" style="opacity:' + (dark ? 1 : 0) + '"/></svg>';
  }
  function modeLabel() { return (S.theme || {}).mode === "dark" ? "라이트 모드로 바꾸기" : "다크 모드로 바꾸기"; }

  /* 홈 D-day 위에 그대로 보이는 기념일 문구 (자유 입력) */
  function defaultPhrase() {
    var c = S.couple || {};
    return String(c.me || "소영") + josa(c.me || "소영", "과", "와") + " " +
      String(c.you || "준영") + josa(c.you || "준영", "이", "가") + " 함께한 지";
  }
  function ddayPhrase() {
    var v = (S.couple || {}).phrase;
    return typeof v === "string" && v.trim() ? v : defaultPhrase();
  }

  /* 페이지 캡션(제목 줄) 바탕색 — 글씨는 항상 #111111 */
  var PAGES = [
    { k: "home", n: "홈" }, { k: "cal", n: "캘린더" }, { k: "diary", n: "노트" },
    { k: "photo", n: "사진첩" }, { k: "set", n: "설정" }
  ];
  var CAP_BG = ["#FAEDE8", "#EDF1EC", "#ECF2F7", "#F8EBEE", "#FBF3DE", "#F4F4F4"];
  /* 앱 전체 글꼴 — index.html 에서 Google Fonts 로 불러옵니다 */
  var FONTS = [
    { k: "base", n: "기본 고딕", s: "'Pretendard', -apple-system, BlinkMacSystemFont, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif" },
    { k: "noto", n: "노토 산스", s: "'Noto Sans KR', 'Pretendard', sans-serif" },
    { k: "nanum", n: "나눔고딕", s: "'Nanum Gothic', 'Pretendard', sans-serif" },
    { k: "dodum", n: "고운돋움", s: "'Gowun Dodum', 'Pretendard', sans-serif" },
    { k: "batang", n: "고운바탕", s: "'Gowun Batang', 'Nanum Myeongjo', serif" },
    { k: "myeongjo", n: "마루부리 명조", s: "'Noto Serif KR', 'Nanum Myeongjo', serif" },
    { k: "plex", n: "IBM 플렉스", s: "'IBM Plex Sans KR', 'Pretendard', sans-serif" },
    { k: "pen", n: "나눔손글씨 펜", s: "'Nanum Pen Script', 'Gowun Dodum', cursive" },
    { k: "jua", n: "배민 주아체", s: "'BM Jua', 'Pretendard', sans-serif" },
    { k: "dohyeon", n: "배민 도현체", s: "'BM Dohyeon', 'Pretendard', sans-serif" },
    { k: "hanna", n: "배민 한나체 Pro", s: "'BM Hanna Pro', 'Pretendard', sans-serif" },
    { k: "yeonsung", n: "배민 연성체", s: "'BM Yeonsung', 'Pretendard', sans-serif" },
    { k: "euljiro", n: "배민 을지로체", s: "'BM Euljiro', 'Pretendard', sans-serif" }
  ];
  function fontOf(k) {
    for (var i = 0; i < FONTS.length; i++) if (FONTS[i].k === k) return FONTS[i];
    return FONTS[0];
  }
  /* 노트 기본 탭 이름 — 설정에서 바꿀 수 있어요 */
  var NOTE_DEF = { todo: { e: "📝", n: "메모" }, bucket: { e: "🎯", n: "버킷리스트" }, log: { e: "🎬", n: "영화·먹방" } };
  function pageCap(page) {
    var t = S.theme || {};
    /* 모든 페이지에 한 번에 쓰는 캡션 색(theme.cap)이 먼저, 예전 페이지별 설정은 그다음 */
    if (typeof t.cap === "string" && /^#[0-9a-fA-F]{6}$/.test(t.cap)) return t.cap.toUpperCase();
    var v = (t.pages || {})[page];
    return typeof v === "string" && /^#[0-9a-fA-F]{6}$/.test(v) ? v : "";
  }
  function capCls(page) { return pageCap(page) ? " cap-tint" : ""; }
  function capStyle(page) {
    var c = pageCap(page);
    return c ? ' style="--cap:' + c + '"' : "";
  }

  function applyTheme() {
    var root = document.documentElement, t = S.theme || {};
    var dark = (t.mode === "dark");
    root.setAttribute("data-mode", dark ? "dark" : "light");
    var cc = S.couple.colors || {};
    root.style.setProperty("--me", cc.me || "#D96B52");
    root.style.setProperty("--you", cc.you || "#5F6F65");
    root.style.setProperty("--font", fontOf((S.theme || {}).font).s);
    var mt = document.querySelector('meta[name="theme-color"]');
    if (mt) mt.setAttribute("content", dark ? "#111111" : "#FFFFFF");
    if (t.name) {
      root.style.setProperty("--nm", t.name);
      root.style.setProperty("--nm-soft", rgba(t.name, .10));
      root.style.setProperty("--nm-line", rgba(t.name, .26));
      root.style.setProperty("--nm-dot", t.name);
    } else {
      ["--nm", "--nm-soft", "--nm-line", "--nm-dot"].forEach(function (k) { root.style.removeProperty(k); });
    }
    if (t.log) {
      root.style.setProperty("--log", t.log);
      root.style.setProperty("--log-soft", rgba(t.log, .07));
      root.style.setProperty("--log-line", rgba(t.log, .24));
      root.style.setProperty("--log-sw", t.log);
    } else {
      ["--log", "--log-soft", "--log-line", "--log-sw"].forEach(function (k) { root.style.removeProperty(k); });
    }
    /* v16: 홈 제목 색을 골랐다면 저장·완료 같은 기본 버튼도 같은 색으로
       v19: 글씨는 늘 검정으로 또렷하게(btnInk) */
    var htb = String(t.homeTitleBg || "").toUpperCase();
    if (/^#[0-9A-F]{6}$/.test(htb)) {
      root.style.setProperty("--btn-bg", htb);
      root.style.setProperty("--btn-ink", btnInk(htb));
    } else {
      ["--btn-bg", "--btn-ink"].forEach(function (k) { root.style.removeProperty(k); });
    }
  }
  function setMode(m) {
    S.theme = S.theme || { name: null, log: null };
    S.theme.mode = m === "dark" ? "dark" : "light";
    save(); applyTheme();
    var btn = document.querySelector('[data-act="toggleMode"]');
    if (btn) { btn.innerHTML = modeIcon(); btn.setAttribute("aria-label", modeLabel()); btn.setAttribute("title", modeLabel()); }
    var cell = (typeof current !== "undefined" && current) ? current : "home";
    if (cell === "home") renderHome();
    if (cell === "cal") renderCal();
    if (cell === "diary") renderDiary();
    if (cell === "photo") renderPhoto();
    if (cell === "set") renderSet();
    syncThemeSheet();
  }

  /* 예전 이름(schedBg·ourBg)은 홈 제목 색 하나로 모읍니다 */
  var THEME_ALIAS = { schedBg: "homeTitleBg", ourBg: "homeTitleBg" };
  function setThemeColor(target, color) {
    target = THEME_ALIAS[target] || target;
    var ok = target === "name" || target === "log" || target === "homeTitleBg";
    if (!ok) return;
    S.theme = S.theme || { name: null, log: null };
    S.theme[target] = color ? String(color).toUpperCase() : null;
    save(); applyTheme(); renderAll(); syncThemeSheet();
  }
  function setPageCap(page, color) {
    if (!page) return;
    var v = String(color || "").trim();
    if (v && !/^#[0-9a-fA-F]{6}$/.test(v)) return;
    S.theme.pages = S.theme.pages || {};
    if (v) S.theme.pages[page] = v.toUpperCase(); else delete S.theme.pages[page];
    save();
    var val = v ? v.toUpperCase() : "";
    /* 화면 전체를 다시 그리지 않고 지금 보이는 페이지 띠만 바로 바꿔요 (색 고르는 중에 창이 닫히지 않도록) */
    document.querySelectorAll('[data-pg="' + page + '"]').forEach(function (el) {
      el.classList.toggle("cap-tint", !!val);
      if (val) el.style.setProperty("--cap", val); else el.style.removeProperty("--cap");
    });
    var row = document.querySelector('.cap-row[data-caprow="' + page + '"]');
    if (row) row.querySelectorAll(".sw").forEach(function (b) {
      b.classList.toggle("sel", (b.getAttribute("data-color") || "") === val);
    });
    document.querySelectorAll('input.js-page[data-page="' + page + '"]').forEach(function (inp) {
      if (val && inp.value.toUpperCase() !== val) inp.value = val;
    });
  }

  /* ------------------------------------------------------------------ types */
  var TYPE = {
    trip: { label: "여행", color: "#8C7B6B" },
    date: { label: "데이트", color: "#D96B52" },
    etc: { label: "개인일정", color: "#8A8A8F" },
    anni: { label: "기념일", color: "#5F6F65" }
  };
  var TYPE_ORDER = ["trip", "date", "etc"];
  /* 가계부(지출)는 이번 버전에서 화면에서 빼 두었습니다.
     데이터(expenses)와 카테고리 색은 다음 단계에서 화면만 다시 붙이면 되도록 남겨 둡니다. */
  var CAT = [
    { name: "식비", color: "#D96B52" },
    { name: "데이트", color: "#5F6F65" },
    { name: "교통", color: "#B9A48C" },
    { name: "생활", color: "#8E8E93" },
    { name: "기타", color: "#DCDCD8" }
  ];
  var catColor = function (n) { for (var i = 0; i < CAT.length; i++) if (CAT[i].name === n) return CAT[i].color; return "#DCDCD8"; };

  /* ------------------------------------------------------------------ photo captions */
  var CAP_DEFAULT = "#F4F4F2";
  var CAP_PALETTE = [
    { n: "화이트", c: "#FFFFFF" }, { n: "아이보리", c: "#FBF6EE" }, { n: "라이트 그레이", c: "#F4F4F2" },
    { n: "세이지", c: "#EDF1EC" }, { n: "코랄", c: "#FAEDE8" }, { n: "블러시", c: "#F8EBEE" },
    { n: "스카이", c: "#ECF2F7" }, { n: "버터", c: "#FBF3DE" }
  ];
  function capBg(p) { return (p && p.capBg) ? p.capBg : CAP_DEFAULT; }

  /* ------------------------------------------------------------------ photos art */
  function art(i, big) {
    var pal = [
      { bg: "#EFE7DF", a: "#FFFFFF", b: "#D96B52", c: "#D9CFC4" },
      { bg: "#F4EFE9", a: "#FFFFFF", b: "#D96B52", c: "#E2D6C9" },
      { bg: "#EDF1EC", a: "#C7D0C9", b: "#5F6F65", c: "#DCE3DB" },
      { bg: "#F7EFEA", a: "#E4C9BE", b: "#D96B52", c: "#5F6F65" },
      { bg: "#F1EEEA", a: "#1C1C1E", b: "#D96B52", c: "#DCD7CF" },
      { bg: "#F3EFE8", a: "#FFFFFF", b: "#5F6F65", c: "#D96B52" },
      { bg: "#EDF1F0", a: "#FFFFFF", b: "#5F6F65", c: "#C7D0C9" },
      { bg: "#EEECE9", a: "#1C1C1E", b: "#F8F8F7", c: "#D96B52" },
      { bg: "#F7EFE7", a: "#FFFFFF", b: "#D96B52", c: "#CBB7A6" },
      { bg: "#EFF1F0", a: "#FFFFFF", b: "#5F6F65", c: "#C7D0C9" },
      { bg: "#F5F0E9", a: "#FFFFFF", b: "#D96B52", c: "#D6C8B8" },
      { bg: "#F2EFEB", a: "#FFFFFF", b: "#D96B52", c: "#CFC7BC" }
    ];
    var p = pal[i % 12];
    var k = i % 12;
    var g = "";
    if (k === 0) {
      g = '<circle cx="35" cy="58" r="14" fill="' + p.a + '"/><circle cx="35" cy="58" r="7" fill="' + p.c + '" opacity=".5"/>' +
          '<circle cx="64" cy="62" r="11" fill="' + p.a + '"/><circle cx="64" cy="62" r="5" fill="' + p.c + '" opacity=".5"/>' +
          '<path d="M33 36c3 4-3 6 0 10M46 33c3 4-3 6 0 10" stroke="' + p.b + '" stroke-width="1.6" stroke-linecap="round" fill="none"/>' +
          '<rect x="22" y="74" width="56" height="2" rx="0" fill="' + p.c + '"/>';
    } else if (k === 1) {
      g = '<rect x="26" y="20" width="48" height="56" rx="0" fill="' + p.a + '" stroke="' + p.c + '" stroke-width="1.4"/>' +
          '<circle cx="50" cy="40" r="10" fill="' + p.b + '" opacity=".85"/>' +
          '<path d="M26 62h48" stroke="' + p.c + '" stroke-width="1.3"/><path d="M26 68h48" stroke="' + p.c + '" stroke-width="2.6"/>';
    } else if (k === 2) {
      g = '<path d="M8 76 34 38l16 22 10-13 24 29z" fill="' + p.b + '" opacity=".85"/>' +
          '<path d="M8 82 30 56l14 16 12-9 24 19z" fill="' + p.a + '" opacity=".85"/>' +
          '<circle cx="74" cy="26" r="7" fill="' + p.b + '" opacity=".5"/>';
    } else if (k === 3) {
      g = '<path d="M50 78V46M38 78V52M62 78V54" stroke="' + p.c + '" stroke-width="1.6" stroke-linecap="round"/>' +
          '<circle cx="50" cy="40" r="9" fill="' + p.b + '" opacity=".9"/><circle cx="36" cy="46" r="7" fill="' + p.a + '" stroke="' + p.b + '" stroke-width="1.3"/>' +
          '<circle cx="64" cy="48" r="6.5" fill="' + p.a + '" stroke="' + p.b + '" stroke-width="1.3"/>';
    } else if (k === 4) {
      g = '<circle cx="50" cy="52" r="26" fill="' + p.a + '"/><circle cx="50" cy="52" r="7" fill="' + p.bg + '" stroke="' + p.c + '" stroke-width="1.2"/>' +
          '<circle cx="50" cy="52" r="17" fill="none" stroke="' + p.c + '" stroke-width=".9" opacity=".8"/>' +
          '<circle cx="73" cy="31" r="4" fill="' + p.b + '"/>';
    } else if (k === 5) {
      g = '<circle cx="50" cy="56" r="24" fill="' + p.a + '" stroke="' + p.c + '" stroke-width="1.2"/>' +
          '<circle cx="50" cy="56" r="14" fill="' + p.b + '" opacity=".18"/>' +
          '<circle cx="44" cy="50" r="5" fill="' + p.b + '" opacity=".8"/><circle cx="56" cy="60" r="6" fill="' + p.c + '"/>' +
          '<path d="M20 28h18" stroke="' + p.c + '" stroke-width="2" stroke-linecap="round"/>';
    } else if (k === 6) {
      g = '<path d="M0 62h100v38H0z" fill="' + p.a + '"/>' +
          '<path d="M0 62c10 4 20-4 30 0s20-4 30 0 20-4 40 0" stroke="' + p.b + '" stroke-width="1.6" fill="none"/>' +
          '<path d="M0 72c10 4 20-4 30 0s20-4 30 0 20-4 40 0" stroke="' + p.b + '" stroke-width="1.2" fill="none" opacity=".6"/>' +
          '<circle cx="70" cy="30" r="9" fill="' + p.b + '" opacity=".4"/>';
    } else if (k === 7) {
      g = '<rect x="20" y="24" width="60" height="52" rx="0" fill="' + p.a + '"/>' +
          '<rect x="27" y="31" width="46" height="38" fill="' + p.b + '" opacity=".9"/>' +
          '<rect x="22" y="20" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/><rect x="40" y="20" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/>' +
          '<rect x="58" y="20" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/><rect x="74" y="20" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/>' +
          '<rect x="22" y="72" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/><rect x="40" y="72" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/>' +
          '<rect x="58" y="72" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/><rect x="74" y="72" width="5" height="8" rx="0" fill="' + p.bg + '" opacity=".9"/>';
    } else if (k === 8) {
      g = '<circle cx="50" cy="58" r="19" fill="' + p.b + '" opacity=".75"/>' +
          '<rect x="0" y="58" width="100" height="42" fill="' + p.a + '"/>' +
          '<path d="M0 58h100" stroke="' + p.c + '" stroke-width="1.4"/>' +
          '<path d="M18 70h16M18 76h26M18 82h10" stroke="' + p.c + '" stroke-width="1.2" stroke-linecap="round" opacity=".8"/>';
    } else if (k === 9) {
      g = '<rect x="24" y="22" width="52" height="56" rx="0" fill="' + p.a + '" stroke="' + p.c + '" stroke-width="1.2"/>' +
          '<path d="M34 34v10M44 30v14M54 36v8M64 32v12" stroke="' + p.c + '" stroke-width="1.4" stroke-linecap="round" opacity=".85"/>' +
          '<circle cx="50" cy="70" r="4" fill="' + p.b + '" opacity=".65"/>';
    } else if (k === 10) {
      g = '<path d="M16 94c12-20 24-28 34-34s22-14 32-30" stroke="' + p.c + '" stroke-width="1.7" fill="none" stroke-linecap="round"/>' +
          '<path d="M32 94c8-14 18-22 28-28s20-12 30-26" stroke="' + p.c + '" stroke-width="1.2" fill="none" stroke-linecap="round" opacity=".5"/>' +
          '<circle cx="66" cy="34" r="11" fill="' + p.b + '" opacity=".68"/>';
    } else {
      g = '<rect x="24" y="50" width="34" height="24" rx="0" fill="' + p.a + '" stroke="' + p.c + '" stroke-width="1.2"/>' +
          '<path d="M24 57h34" stroke="' + p.c + '" stroke-width="1"/>' +
          '<circle cx="66" cy="62" r="9" fill="' + p.a + '" stroke="' + p.b + '" stroke-width="1.3"/>' +
          '<path d="M18 80h64" stroke="' + p.c + '" stroke-width="1.4" opacity=".7"/>';
    }
    return '<svg viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice" aria-hidden="true"><rect width="100" height="100" fill="' + p.bg + '"/>' + g + "</svg>";
  }

  /* ------------------------------------------------------------------ home */
  function ddayLabel(days) {
    if ((S.couple.fmt || "D") !== "Y") return { text: "D+" + days, compact: false };
    var since = parse(S.couple.since), now = parse(today);
    var ann = function (y) { return new Date(y, since.getMonth(), since.getDate()); };
    var years = now.getFullYear() - since.getFullYear();
    if (ann(since.getFullYear() + years) > now) years -= 1;
    if (years < 1) return { text: days + "일째", compact: false };
    var rem = Math.round((now - ann(since.getFullYear() + years)) / 86400000);
    return { text: years + "년 " + rem + "일째", compact: true };
  }

  function nextAnniversary() {
    var since = S.couple.since;
    var d = parse(since);
    var years = new Date().getFullYear() - d.getFullYear();
    for (var n = Math.max(1, years); n < 80; n++) {
      var nd = new Date(d.getFullYear() + n, d.getMonth(), d.getDate());
      var days = diffDays(today, iso(nd));
      if (days >= 0) return { n: n, date: iso(nd), days: days };
    }
    return null;
  }

  function bktStatus(b) {
    if (b.done) return { t: "완료", k: "done" };
    return b.status === "doing" ? { t: "진행 중", k: "doing" } : { t: "미완료", k: "todo" };
  }

  /* 섹션 제목 줄(캡션) 바탕색 — 목록·카드가 아니라 제목 줄에만 칠하고, 글씨는 색에 맞춰 진하게 */
  function secTintStyle(bg) {
    if (!bg) return "";
    return ' style="--sec-bg:' + bg + ";--sec-ink:" + inkOn(bg) + '"';
  }

  function renderHome() {
    var c = S.couple;
    /* v14: 두 섹션의 제목 줄 색은 하나로 묶여 있어요 */
    var titleBg = String(((S.theme || {}).homeTitleBg) || "").toUpperCase();
    var dday = Math.max(0, diffDays(c.since, today));
    var dl = ddayLabel(dday);
    var ann = nextAnniversary();
    var todayEvents = S.events.filter(function (e) { return evCovers(e, today); }).sort(byTimeAsc);
    var upcoming = S.events.filter(function (e) { return evStart(e) > today; }).sort(byDateAsc).slice(0, 3);

    var html = "";
    var nmOn = S.theme && S.theme.name;
    /* v20: 「투로그」 앞의 두 네모 로고는 지웠어요 — 이름만 깔끔하게 */
    html += '<div class="brand' + capCls("home") + '"' + capStyle("home") + ' data-pg="home"><b>투로그</b><span class="bw">(twolog)</span>' +
      '<button class="icon-btn pal first" data-act="toggleMode" aria-label="' + modeLabel() + '" title="' + modeLabel() + '">' + modeIcon() + "</button>" +
      '<button class="icon-btn pal" data-act="openTheme" aria-label="컬러" title="컬러">' + IC.palette + "</button></div>";

    /* ---- 1. D-day ---- */
    /* 프사는 양 옆에 크게, 가운데에 「우리는」 문구·D+N·기념일 배지 */
    html += '<div class="dday" data-act="editDday">' +
      '<button class="icon-btn dday-edit" data-act="editDday" aria-label="기념일 수정">' + IC.pencil + "</button>" +
      '<div class="dday-side">' + avSpan("me", "hero") + "</div>" +
      '<div class="dday-mid">' +
      '<div class="eyebrow">' + esc(ddayPhrase()) + "</div>" +
      '<div class="dday-num' + (dl.compact ? " compact" : "") + '">' + dl.text + "</div>" +
      (ann ? '<div class="chip-row"><span class="chip coral">' + ann.n + "주년 " + (ann.days === 0 ? "오늘" : "D-" + ann.days) + "</span></div>" : "") +
      "</div>" +
      '<div class="dday-side">' + avSpan("you", "hero") + "</div>" +
      "</div>";

    /* ---- 2. 다가오는 일정 ---- */
    var slist = [];
    todayEvents.slice(0, 2).forEach(function (e) {
      slist.push({
        e: e,
        when: mdText(evStart(e)) + (evRange(e) ? " ~ " + mdText(evEnd(e)) : "") + (evWhenK(e) ? " " + evWhenK(e) : "") + " · " + (TYPE[e.type] || TYPE.etc).label,
        left: "오늘"
      });
    });
    upcoming.slice(0, 3).forEach(function (e) {
      slist.push({
        e: e,
        when: mdText(evStart(e)) + (evRange(e) ? " ~ " + mdText(evEnd(e)) : "") + (evWhenK(e) ? " " + evWhenK(e) : "") + " · " + (TYPE[e.type] || TYPE.etc).label,
        left: "D-" + diffDays(today, evStart(e))
      });
    });
    slist = slist.slice(0, 4);

    html += '<div class="home-sec" data-sec="sched">';
    html += '<div class="sec sec-tint"' + secTintStyle(titleBg) + '><h2>📅 다가오는 일정</h2><span class="more">' + (todayEvents.length + upcoming.length) + "개</span></div>";
    html += '<div class="pad"><div class="list">';
    if (slist.length) {
      slist.forEach(function (s) {
        var edge = evColor(s.e);
        /* 프사 대신 일정 색 띠(왼쪽)만으로 누구 일정인지 보여 줍니다 */
        html += '<div class="row sched" data-who="' + evWho(s.e) + '">' +
          '<span class="bar" style="background:' + edge + '"></span>' +
          '<div class="sbody">' +
          '<div class="srow1"><div class="t" title="' + esc(s.e.title) + '">' + esc(s.e.title) + "</div></div>" +
          '<div class="smeta"><span class="sd">' + esc(s.when) + '</span><span class="sl">' + esc(s.left) + "</span></div>" +
          "</div></div>";
      });
    } else { html += '<div class="empty">예정된 일정이 없어요.</div>'; }
    html += "</div></div></div>";

    /* v23: 「{월}월의 우리」 대시보드는 지웠어요 — 홈은 D-day 다음에 다가오는 일정만 */
    html += '<div style="height:18px"></div>';

    $("#s-home").innerHTML = html;
  }

  /* ------------------------------------------------------------------ calendar */
  var HOLIDAY = {
    "2026-01-01": "신정",
    "2026-02-16": "설날 연휴", "2026-02-17": "설날", "2026-02-18": "설날 연휴",
    "2026-03-01": "삼일절", "2026-03-02": "대체공휴일",
    "2026-05-05": "어린이날", "2026-05-24": "부처님오신날", "2026-05-25": "대체공휴일",
    "2026-06-03": "지방선거", "2026-06-06": "현충일",
    "2026-08-15": "광복절", "2026-08-17": "대체공휴일",
    "2026-09-24": "추석 연휴", "2026-09-25": "추석", "2026-09-26": "추석 연휴",
    "2026-10-03": "개천절", "2026-10-05": "대체공휴일", "2026-10-09": "한글날",
    "2026-12-25": "성탄절"
  };
  function holName(ds) { return HOLIDAY[ds] || ""; }

  function ymd(y, m, d) { return y + "-" + pad(m + 1) + "-" + pad(d); }

  function evWho(e) {
    var w = e.who;
    return w === "me" || w === "you" ? w : "both";
  }
  function avSquare(person) {
    return avSpan(person);
  }
  function whoRow(e) {
    var w = evWho(e);
    if (w === "both") {
      /* 함께하는 일정은 (소영 프사)🤎(준영 프사) 로 */
      return '<div class="who-row both">' + avSquare("me") +
        '<span class="heart" aria-hidden="true">🤎</span>' + avSquare("you") + "</div>";
    }
    return '<div class="who-row">' + avSquare(w) +
      '<span class="wname">' + esc(w === "me" ? S.couple.me : S.couple.you) + "</span></div>";
  }


  function evStart(e) { return String((e && e.date) || "").slice(0, 10); }
  function evEnd(e) {
    var st = evStart(e);
    var en = String((e && e.endDate) || "").slice(0, 10);
    return en && en > st ? en : st;
  }
  function evCovers(e, ds) { return !!ds && ds >= evStart(e) && ds <= evEnd(e); }
  var DOW_KR = ["일", "월", "화", "수", "목", "금", "토"];
  /* v28: 일정 시트 — 날짜 아래에 「화요일」처럼 요일을 풀어서 */
  var DOW_FULL = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"];
  /* v21: 일정에 고른 색이 있으면 그 색, 없으면 담당자 색 (달력 막대·띠·목록에 함께) */
  function evColor(e) {
    var c = String((e && e.color) || "").toUpperCase();
    return /^#[0-9A-F]{6}$/.test(c) ? c : sched(evWho(e));
  }
  /* v21: 일정 시간 — 시작만 있으면 «19:00», 둘 다 있으면 «19:00~21:00» */
  function evWhen(e) {
    var t = String((e && e.time) || "").slice(0, 5);
    var t2 = String((e && e.endTime) || "").slice(0, 5);
    if (t && t2) return t + "~" + t2;
    return t || "";
  }
  /* v21: 시간은 한국어 12시간제로 — «오전 09:45» «오후 09:00» */
  function timeK(hhmm) {
    var s2 = String(hhmm || "").slice(0, 5);
    if (!/^\d{2}:\d{2}$/.test(s2)) return "";
    var h = Number(s2.slice(0, 2)), mi = s2.slice(3, 5);
    var am = h < 12, h12 = h % 12;
    if (h12 === 0) h12 = 12;
    return (am ? "오전 " : "오후 ") + (h12 < 10 ? "0" : "") + h12 + ":" + mi;
  }
  /* 홈·PDF 처럼 글자로 보여 줄 때 쓰는 시간 표기 */
  function evWhenK(e) {
    var a = timeK(e && e.time), b = timeK(e && e.endTime);
    if (a && b) return a + "~" + b.replace(/^오[전후] /, "");
    return a || b || "";
  }
  /* v21: «26.11.17(화)» — 일정 시트의 큰 날짜 */
  function evDateBig(ds) {
    var d = parse(ds);
    if (!d || isNaN(d.getTime())) return "";
    /* v28: 요일은 아래 줄(evDowFull)로 따로 — 여기는 날짜만 */
    return String(d.getFullYear()).slice(2) + "." + pad(d.getMonth() + 1) + "." + pad(d.getDate());
  }
  function evDowFull(ds) {
    var d = parse(ds);
    if (!d || isNaN(d.getTime())) return "";
    return DOW_FULL[d.getDay()];
  }
  function evRange(e) {
    var st = evStart(e), en = evEnd(e);
    if (st === en) return "";
    var f = function (x) { return Number(x.slice(5, 7)) + "." + Number(x.slice(8, 10)); };
    return f(st) + " ~ " + f(en);
  }
  function mdText(ds) {
    var s = String(ds || "");
    return s.length >= 10 ? Number(s.slice(5, 7)) + "." + Number(s.slice(8, 10)) : s;
  }
  /* 생일 — "6월 26일" 과 "1992-06-26" 둘 다 읽어요 */
  function parseBirthday(v) {
    var s = String(v || "").trim();
    var m = s.match(/^(\d{4})-(\d{1,2})-(\d{1,2})$/);
    if (m) return bdOk(+m[1], +m[2], +m[3]);
    m = s.match(/(\d{1,2})\s*월\s*(\d{1,2})\s*일/);
    if (m) return bdOk(0, +m[1], +m[2]);
    return null;
  }
  function bdOk(y, mo, da) {
    if (!(mo >= 1 && mo <= 12) || !(da >= 1 && da <= 31)) return null;
    return { y: y || 0, m: mo, d: da };
  }
  /* 화면에 보여 줄 "M월 D일" */
  function bdayText(v) {
    var p = parseBirthday(v);
    return p ? p.m + "월 " + p.d + "일" : "";
  }
  /* 달력(input[type=date])에 넣을 값 — 연도를 모르면 소영은 1992, 상대는 올해로 채워요 */
  function bdayInput(who) {
    var p = parseBirthday((S.couple.birthdays || {})[who]);
    if (!p) return "";
    var y = p.y || (who === "me" ? 1992 : new Date().getFullYear());
    var d = new Date(y, p.m - 1, p.d);
    if (d.getMonth() !== p.m - 1 || d.getDate() !== p.d) d = new Date(y, p.m, 0); /* 2월 30일처럼 없는 날은 그 달 마지막 날 */
    return iso(d);
  }
  /* 다음 생일까지 남은 날 — 월·일로만 계산해요 */
  function nextBirthday(v) {
    var p = parseBirthday(v);
    if (!p) return null;
    var now = parse(today), y = now.getFullYear();
    var d = new Date(y, p.m - 1, p.d);
    if (d.getTime() < new Date(y, now.getMonth(), now.getDate()).getTime()) d = new Date(y + 1, p.m - 1, p.d);
    return { date: iso(d), days: diffDays(today, iso(d)) };
  }
  function mileRow(name, date, left, soon) {
    return '<div class="mile-row"><span class="mile-n">' + esc(name) + '</span><span class="mile-d">' + esc(date) + '</span>' +
      '<span class="mile-x' + (soon ? " soon" : "") + '">' + esc(left) + "</span></div>";
  }

  /* v19: 캘린더 일정 검색 — 제목으로 찾고, 결과를 누르면 그 달·날짜로 이동해요 */
  function calSearchResults(q) {
    var raw = String(q || "").trim();
    var key = raw.toLowerCase();
    var list = (S.events || []).slice();
    if (key) {
      list = list.filter(function (e) { return String(e.title || "").toLowerCase().indexOf(key) >= 0; });
    }
    list.sort(function (a, b) { var as = evStart(a), bs = evStart(b); return as < bs ? -1 : as > bs ? 1 : 0; });
    /* v21: 검색어가 비어 있으면 아무것도 그리지 않아요 — 시트에는 검색창만 깔끔하게 */
    if (!key) return "";
    if (!list.length) return '<div class="sres-empty">「' + esc(raw) + "」와 맞는 일정이 없어요.</div>";
    return list.slice(0, 60).map(function (e) {
      var t = TYPE[e.type] || TYPE.etc;
      var rng = evRange(e);
      return '<button type="button" class="sres" data-act="goEvent" data-date="' + evStart(e) + '">' +
        '<span class="sbar" style="background:' + evColor(e) + '"></span>' +
        '<span class="sbody"><span class="st">' + esc(e.title) + "</span>" +
        '<span class="sd">' + esc(rng || evStart(e).replace(/-/g, ".")) + " · " + esc(t.label) + "</span></span>" +
        '<span class="sgo" aria-hidden="true">›</span></button>';
    }).join("");
  }

  /* v21: 검색 시트는 «검색만» — 처음에는 입력칸 하나만 보이고,
     글자를 치는 순간 아래에 맞는 일정이 자동으로 나옵니다 (안내는 플레이스홀더로만). */
  function formCalSearch(q) {
    var key = String(q || "").trim();
    return sheetHead("일정 검색") +
      '<div class="f" style="margin-top:14px">' +
      '<input class="field" id="calSearchIn" value="' + esc(key) + '" placeholder="일정 이름으로 검색" autocomplete="off" enterkeyhint="search" aria-label="일정 검색어">' +
      "</div>" +
      '<div class="sres-wrap" id="calSearchOut">' + calSearchResults(key) + "</div>" +
      '<div style="height:12px"></div><button class="btn-line" data-close="1">닫기</button>';
  }

  /* v21: 달 이동 — 화살표 버튼과 손가락 스와이프가 같은 함수를 씁니다 */
  function calMove(step) {
    var cur = S.ui.calMonth || today.slice(0, 7);
    var y = Number(cur.slice(0, 4)), m = Number(cur.slice(5, 7)) - 1 + (step > 0 ? 1 : -1);
    var nd = new Date(y, m, 1);
    S.ui.calMonth = nd.getFullYear() + "-" + pad(nd.getMonth() + 1);
    save(); renderCal();
  }

  function renderCal() {
    var cur = S.ui.calMonth || today.slice(0, 7);
    var y = Number(cur.slice(0, 4)), m = Number(cur.slice(5, 7)) - 1;
    var first = new Date(y, m, 1), startDow = first.getDay(), daysIn = new Date(y, m + 1, 0).getDate();
    var sel = S.ui.selDate || today;
    var monthStart = cur + "-01", monthEnd = ymd(y, m, daysIn);

    var html = "";
    /* v20: 「🗓️ 캘린더」 제목 줄을 지우고, 그 자리에 그 달(11월)을 제목과 같은 크기로 왼쪽에 —
       같은 줄 맨 오른쪽 끝에 돋보기. 달 이동은 「11월」 옆의 작은 화살표로 해요 */
    var thisYear = Number(today.slice(0, 4));
    var monthTxt = (m + 1) + "월";
    html += '<div class="cal-top">' +
      '<div class="cal-title" title="' + y + "년 " + (m + 1) + '월" aria-label="' + y + "년 " + (m + 1) + '월">' +
      '<span class="cal-month">' + monthTxt + "</span>" +
      (y !== thisYear ? '<span class="cal-year">' + y + "</span>" : "") +
      '<span class="cal-nav">' +
      '<button type="button" class="cal-arrow" data-act="calPrev" aria-label="이전 달">' + IC.left + "</button>" +
      '<button type="button" class="cal-arrow" data-act="calNext" aria-label="다음 달">' + IC.right + "</button>" +
      "</span></div>" +
      '<button type="button" class="cal-search" data-act="calSearch" aria-label="일정 검색" title="일정 검색">' + IC.search + "</button>" +
      "</div>";

    html += '<div class="cal">';

    html += '<div class="cal-week"><span>일</span><span>월</span><span>화</span><span>수</span><span>목</span><span>금</span><span>토</span></div>';

    /* 날짜 칸을 7일씩 주 단위로 나눕니다 */
    var cells = [];
    for (var i0 = 0; i0 < startDow; i0++) cells.push("");
    for (var d = 1; d <= daysIn; d++) cells.push(ymd(y, m, d));
    while (cells.length % 7) cells.push("");

    var monthEvents = S.events.filter(function (e) {
      return evEnd(e) >= monthStart && evStart(e) <= monthEnd;
    });

    /* v23: 일정 막대를 16px + 사이 3px(19px)로 띄우고, 한 주에 세 줄까지 펼칩니다.
       네 줄을 넘는 일정만 날짜 칸의「외 N」으로 알려 줘요. */
    /* v24: 세 줄이 서로 붙지 않고 날짜 숫자·다음 주와도 부딪히지 않게 간격을 넉넉히.
       TOP_H = 날짜 숫자 아래에서 첫 줄까지, LANE_H = 한 줄 높이(막대 16 + 사이 6),
       ROW_PAD = 마지막 줄 아래 여백입니다.
       v27: 한 칸에 일정이 여러 개면 막대 사이 빈틈 없이 딱 붙여 쌓습니다(LANE_H = 막대 16). */
    /* v28: 한 날에 보이는 일정 막대는 두 줄까지 — 세 개부터는 날짜 칸에 「+1」처럼 알려 줘요 */
    var LANE_H = 16, TOP_H = 32, ROW_MIN = 68, ROW_PAD = 12, MAX_LANE = 2;
    html += '<div class="cal-grid">';
    for (var w = 0; w < cells.length / 7; w++) {
      var wk = cells.slice(w * 7, w * 7 + 7);

      /* 이 주에 걸치는 일정 → 시작/끝 칸과 줄(lane) 계산 */
      var bars = [];
      monthEvents.forEach(function (e) {
        var s = evStart(e), en = evEnd(e);
        var sCol = -1, eCol = -1;
        for (var ci = 0; ci < 7; ci++) {
          var ds = wk[ci];
          if (!ds || ds < s || ds > en) continue;
          if (sCol < 0) sCol = ci;
          eCol = ci;
        }
        if (sCol < 0) return;
        bars.push({ e: e, sCol: sCol, eCol: eCol, openL: s < wk[sCol], openR: en > wk[eCol] });
      });
      bars.sort(function (a, b) { return a.sCol - b.sCol || (b.eCol - b.sCol) - (a.eCol - a.sCol); });
      var lanes = [];
      bars.forEach(function (b) {
        var li = 0;
        while (lanes[li] && lanes[li].some(function (x) { return !(b.eCol < x.sCol || b.sCol > x.eCol); })) li++;
        (lanes[li] = lanes[li] || []).push(b);
        b.lane = li;
      });
      /* 한 주에 보이는 막대는 두 줄까지 — 넘치는 일정은 날짜 칸에 '+N' 으로 알려 줍니다 */
      var shown = bars.filter(function (b) { return b.lane < MAX_LANE; });
      var ovf = {};
      bars.forEach(function (b) {
        if (b.lane < MAX_LANE) return;
        var ovDs = wk[b.sCol] || "";
        if (ovDs) ovf[ovDs] = (ovf[ovDs] || 0) + 1;
      });
      var ovfCount = Object.keys(ovf).length ? ovf : null;
      /* v24: 공휴일 이름이 있는 주는 그 이름 아래에서 일정 줄이 시작하게 조금 내립니다 */
      var holRow = wk.some(function (dsH) { return !!dsH && !!holName(dsH); });
      var topBase = TOP_H + (holRow ? 13 : 0);
      var rowsH = Math.max(ROW_MIN, topBase + Math.min(lanes.length, MAX_LANE) * LANE_H + (ovfCount ? 22 : ROW_PAD));
      /* v21: 마지막 주에 일정이 없으면 그 빈 줄만큼 높이를 줄여 — 달력과 아래 일정이 훨씬 가깝게 */
      var lastRow = (w === cells.length / 7 - 1);
      if (lastRow && !shown.length && !ovfCount) rowsH = topBase + 10;

      html += '<div class="cal-row" style="height:' + rowsH + 'px"><div class="cal-daygrid">';
      for (var ci2 = 0; ci2 < 7; ci2++) {
        var ds2 = wk[ci2];
        if (!ds2) { html += '<div class="day blank"></div>'; continue; }
        var dow2 = new Date(Number(ds2.slice(0, 4)), Number(ds2.slice(5, 7)) - 1, Number(ds2.slice(8, 10))).getDay();
        var cls = "day";
        if (dow2 === 0) cls += " sun";
        if (dow2 === 6) cls += " sat";
        if (ds2 === today) cls += " today";
        if (ds2 === sel) cls += " sel";
        if (holName(ds2)) cls += " hol";
        var hol2 = holName(ds2);
        html += '<button class="' + cls + '" data-act="pickDay" data-date="' + ds2 + '"><span class="dnum">' +
          Number(ds2.slice(8, 10)) + "</span>" +
          (hol2 ? '<span class="dhol">' + esc(hol2) + "</span>" : "") +
          (ovfCount && ovfCount[ds2] ? '<span class="dovf">+' + ovfCount[ds2] + "</span>" : "") + "</button>";
      }
      html += "</div>";
      if (shown.length) {
        html += '<div class="cal-bars">';
        shown.forEach(function (b) {
          var left = b.sCol / 7 * 100, width = (b.eCol - b.sCol + 1) / 7 * 100;
          var top = topBase + b.lane * LANE_H;
          var edge = evColor(b.e);
          /* 여러 칸에 걸친 일정은 막대 전체 폭의 가운데에 제목을 놓습니다 */
          var mid = b.eCol > b.sCol ? " mid" : "";
          /* v23: 이웃한 칸의 막대끼리 붙어 보이지 않게 좌우로 1.5px씩 비웁니다 */
          /* v32: 달력 칸 일정 막대 글씨는 배경 밝기와 상관없이 늘 흰색(#FFFFFF)으로 통일 */
          html += '<span class="ebar' + (b.openL ? " openl" : "") + (b.openR ? " openr" : "") + mid +
            '" style="left:calc(' + left + "% + 1.5px); width:calc(" + width + "% - 3px); top:" + top + "px; background:" + edge +
            "; color:#FFFFFF" + '">' + esc(b.e.title) + "</span>";
        });
        html += "</div>";
      }
      html += "</div>";
    }
    html += "</div></div>";

    /* v15: 달력 아래 생일 줄은 지웠어요 — 생일은 홈 D-day 시트에서 고쳐요 */

    /* 선택한 날: 기간이 걸치는 일정 모두 */
    var selEvents = S.events.filter(function (e) { return evCovers(e, sel); })
      .sort(function (a, b) {
        return evStart(a) < evStart(b) ? -1 : evStart(a) > evStart(b) ? 1 : (a.title < b.title ? -1 : 1);
      });
    var sd = parse(sel);
    /* v21: 날짜를 누르면 그날의 «일정만» 깔끔하게 — v18에 넣었던 메모 카드·기록·사진 묶음은 지웠어요.
       (기록은 노트/사진첩 탭에서, 사진은 사진첩에서 봐요) */
    /* v20: 날짜 줄에는 「2026년 11월 17일」만 — 요일·공휴일 배지·개수는 지웠어요 */
    html += '<div class="daypanel"><div class="daypanel-hd"><div class="d">' + sd.getFullYear() + "년 " + (sd.getMonth() + 1) + "월 " + sd.getDate() + "일</div></div>";
    html += '<div class="daylist daytl">';
    if (selEvents.length) {
      selEvents.forEach(function (e) {
        /* (프사) 이름 일정 — 한 줄로 나란히 (오른쪽은 삭제 × 하나만) */
        /* v28: 줄을 누르면 그 일정의 수정 시트가 열려요 (오른쪽 × 만 삭제) */
        html += '<div class="ev ev-tap" role="button" tabindex="0" data-act="editEvent" data-id="' + e.id +
          '" aria-label="' + esc(e.title) + ' 일정 수정"><span class="bar" style="background:' + evColor(e) + '"></span>' +
          whoRow(e) +
          '<div class="t" title="' + esc(e.title) + '">' + esc(e.title) + "</div>" +
          /* v21: 오른쪽의 작은 날짜·종일 표시는 지웠어요 — 색띠·이름·제목만 깔끔하게 */
          '<button class="x" data-act="delEvent" data-id="' + e.id + '" aria-label="삭제">' + IC.x + "</button></div>";
      });
    } else {
      html += '<div class="empty">이 날은 아직 일정이 없어요.</div>';
    }
    html += "</div>";
    html += '<div style="padding:14px 0 0"><button class="ghost add-big" data-act="addEvent">' + IC.plus + " 일정 추가</button></div>";
    html += "</div>";

    html += '<div style="height:24px"></div>';

    $("#s-cal").innerHTML = html;
  }

  /* ------------------------------------------------------------------ note */
  var NOTE_BASE = ["todo", "bucket", "log"];

  function noteTab(k) {
    var v = (S.note || {})[k] || {};
    var d = NOTE_DEF[k];
    /* v18: 이모지를 비우고 이름만 쓸 수도 있어요(예: 「함께」). 빈 문자열은 그대로 존중합니다 */
    return {
      e: typeof v.e === "string" ? v.e : d.e,
      n: typeof v.n === "string" && v.n ? v.n : d.n
    };
  }
  function noteLabel(k) { var t = noteTab(k); return t.e ? t.e + " " + t.n : t.n; }

  /* v18: 이모지 + 이름을 한 칸에서 받아 — 앞의 이모지만 떼어 저장해요 */
  function splitEmojiName(s) {
    var t = String(s == null ? "" : s).trim();
    if (!t) return { e: "", n: "" };
    var m = t.match(/^([\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{200D}\u{20E3}]+)\s*([\s\S]*)$/u);
    if (!m) return { e: "", n: t };
    var rest = String(m[2] || "").trim();
    if (!rest) return { e: "", n: t };
    return { e: String(m[1] || "").trim(), n: rest };
  }
  function listLabel(l) {
    if (!l) return "";
    return l.emoji ? String(l.emoji) + " " + String(l.title || "") : String(l.title || "");
  }

  function findList(id) {
    for (var i = 0; i < S.lists.length; i++) if (S.lists[i].id === id) return S.lists[i];
    return null;
  }
  function curList() {
    var seg = S.ui.seg || "";
    return seg.indexOf("list:") === 0 ? findList(seg.slice(5)) : null;
  }
  function segBtn(seg, val, label) {
    return '<button class="seg-btn' + (seg === val ? " active" : "") + '" data-act="seg" data-seg="' + esc(val) + '">' + esc(label) + "</button>";
  }

  function renderDiary() {
    var seg = S.ui.seg || "todo";
    var known = NOTE_BASE.some(function (b) { return b === seg; });
    var custom = seg.indexOf("list:") === 0 && !!findList(seg.slice(5));
    if (!known && !custom) seg = "todo";
    S.ui.seg = seg;

    var html = "";
    /* v29: 맨 윗줄 오른쪽의 네모 설정 버튼을 지우고, 그 자리에 새 카테고리 탭 추가 + (동그란) 를 둡니다.
       탭 이름 바꾸기(노트 설정)는 「📖 노트」 제목을 꾹 눌러 엽니다. */
    html += '<header class="hdr' + capCls("diary") + '"' + capStyle("diary") + ' data-pg="diary"><div>' +
      '<h1 class="note-h1" title="꾹 누르면 탭 이름을 바꿀 수 있어요"><span class="eh">📖</span> 노트</h1></div>' +
      '<div class="hdr-acts"><button type="button" class="round-btn note-add" data-act="newList" aria-label="새 카테고리 탭 추가" title="새 카테고리 탭 추가">' + IC.listPlus + "</button></div></header>";
    html += '<div class="segs">';
    NOTE_BASE.forEach(function (k) { html += segBtn(seg, k, noteLabel(k)); });
    html += "</div>";
    /* v29: + 는 맨 윗줄 오른쪽으로 옮겼고, 이 줄에는 내가 만든 카테고리 칩만 둡니다 */
    if (S.lists.length) {
      html += '<div class="lstbar"><div class="lst-scroll">';
      S.lists.forEach(function (l) {
        var on = seg === "list:" + l.id;
        html += '<button class="lchip' + (on ? " active" : "") + '" data-act="seg" data-seg="list:' + l.id + '" aria-label="' + esc(listLabel(l)) + '">' +
          (l.emoji ? '<span class="le">' + esc(l.emoji) + "</span>" : "") + "<span>" + esc(l.title) + "</span></button>";
      });
      html += "</div></div>";
    }
    var body;
    if (seg === "todo") body = viewTodo();
    else if (seg === "bucket") body = viewBucket();
    else if (seg === "log") body = viewLog();
    else body = viewList(curList());

    html += '<div class="dbody" id="dbody">' + body + "</div>";
    html += '<div style="height:20px"></div>';
    $("#s-diary").innerHTML = html;

    var act2 = $("#s-diary .lchip.active") || $("#s-diary .seg-btn.active");
    if (act2 && act2.scrollIntoView) {
      try { act2.scrollIntoView({ block: "nearest", inline: "center" }); } catch (e) {}
    }
    /* 카드 상세가 열려 있으면 그 안의 To-do 목록도 같이 맞춰 줍니다 */
    if (openCard) refreshCardSheet();
  }

  /* v29: 노트 맨 윗줄의 네모 설정 버튼이 없어져, 「📖 노트」 제목을 600ms 꾹 누르면
     탭 이름 바꾸기(노트 설정) 시트가 열립니다. 화면에는 아무 버튼도 늘지 않아요. */
  var ntHold = null;
  function ntHoldCancel() {
    if (ntHold && ntHold.timer) clearTimeout(ntHold.timer);
    ntHold = null;
  }
  document.addEventListener("pointerdown", function (ev) {
    var t = ev.target;
    if (!t || !t.closest || !t.closest("#s-diary .hdr .note-h1")) return;
    ntHoldCancel();
    var st = { x: ev.clientX, y: ev.clientY, fired: false };
    st.timer = setTimeout(function () {
      st.fired = true;
      try { if (navigator.vibrate) navigator.vibrate(10); } catch (e) {}
    }, 600);
    ntHold = st;
  }, true);
  window.addEventListener("pointermove", function (ev) {
    if (!ntHold) return;
    if (Math.abs(ev.clientX - ntHold.x) > 8 || Math.abs(ev.clientY - ntHold.y) > 8) ntHoldCancel();
  }, true);
  window.addEventListener("pointerup", function () {
    var st = ntHold;
    ntHoldCancel();
    if (st && st.fired) setTimeout(function () { openNoteSettings(); }, 0);
  }, true);
  window.addEventListener("pointercancel", ntHoldCancel, true);

  /* 노트 공통: 맨 아래 + 추가 줄 */
  function addRow(act, attrs, label) {
    return '<button type="button" class="addrow" data-act="' + act + '"' + (attrs || "") + ">" +
      '<span class="ap">' + IC.plus + "</span>" +
      '<span class="al">' + esc(label) + "</span></button>";
  }

  /* 완료된 항목은 아래로 내리고, 원하면 숨길 수 있게 */
  function byDone(a, b) { return (a.done ? 1 : 0) - (b.done ? 1 : 0); }

  /* v19: 체크/해제로 항목이 위아래로 자리를 옮길 때 살짝 부드럽게 (FLIP) */
  function rowTops(sel) {
    var o = {};
    Array.prototype.forEach.call(document.querySelectorAll(sel + " .trow"), function (r) {
      var b = r.querySelector("[data-id]");
      if (b) o[b.getAttribute("data-id")] = r.getBoundingClientRect().top;
    });
    return o;
  }
  function rowMoveAnim(sel, before) {
    if (!before) return;
    if (window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    Array.prototype.forEach.call(document.querySelectorAll(sel + " .trow"), function (r) {
      var b = r.querySelector("[data-id]");
      if (!b || !r.animate) return;
      var old = before[b.getAttribute("data-id")];
      if (old == null) return;
      var dy = old - r.getBoundingClientRect().top;
      if (Math.abs(dy) < 2) return;
      r.animate([{ transform: "translateY(" + dy + "px)" }, { transform: "translateY(0)" }],
        { duration: 190, easing: "cubic-bezier(.2,.8,.3,1)" });
    });
  }

  function doneToggle(doneCount) {
    if (!doneCount) return "";
    var hide = !!(S.ui && S.ui.hideDone);
    return '<div class="donebar"><button type="button" class="dtgl" data-act="toggleDone" aria-pressed="' + (hide ? "true" : "false") + '">' +
      (hide ? "완료 " + doneCount + "개 보기" : "완료 " + doneCount + "개 숨기기") + "</button></div>";
  }

  /* ---------- 노트: 탭 안의 리스트(그룹) ---------- */
  var CIR_OFF = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="12" cy="12" r="9"/></svg>';
  var CIR_ON = '<svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="M7.4 12.3l3 3 5.8-6.2" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  var GROUP_ARR = { todo: "todos", bucket: "bucket", log: "logs" };
  var GROUP_DEF = { todo: "메모", bucket: "버킷리스트", log: "영화·먹방" };
  function itemsOf(k) { return S[GROUP_ARR[k]] || []; }
  function groupsOf(k) { return (S.groups && S.groups[k]) || []; }
  function groupOf(k, gid) {
    var gs = groupsOf(k);
    for (var i = 0; i < gs.length; i++) if (gs[i].id === gid) return gs[i];
    return null;
  }

  /* ○ / ✓ 동그라미 + 내용 + (삭제) 한 줄 */
  function listItemRow(it, body, toggler, editor, deleter) {
    return '<div class="trow' + (it.done ? " done" : "") + '">' +
      '<button type="button" class="circ" ' + toggler + ' aria-label="완료 표시">' + (it.done ? CIR_ON : CIR_OFF) + "</button>" +
      '<div class="body" ' + editor + ">" + body + "</div>" +
      (deleter ? '<button type="button" class="x" ' + deleter + ' aria-label="삭제">' + IC.x + "</button>" : "") +
      "</div>";
  }

  /* 탭 안의 리스트는 2열 카드로 — 프사·이름 / 제목 / 메모 / 항목 미리보기 / 날짜 */
  var CIR_S_OFF = '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="9"/></svg>';
  var CIR_S_ON = '<svg width="13" height="13" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="10" fill="currentColor"/><path d="M7.4 12.3l3 3 5.8-6.2" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>';

  function cardItem(k, it) {
    var label = k === "todo" ? it.text : it.title;
    if (k === "log") {
      return '<div class="cti log"><span class="lt">' + (it.kind === "movie" ? "영화" : "먹방") + "</span>" +
        '<span class="cx">' + esc(label) + "</span></div>";
    }
    /* v19: 미리보기는 «보기만» — 카드를 누르면 언제나 그 리스트의 전체 목록으로 들어가요.
       (예전에는 항목을 누르면 카드 안에서 바로 체크돼서 리스트로 들어가지 않는 것처럼 보였어요) */
    return '<div class="cti' + (it.done ? " on" : "") + '">' +
      '<span class="cb">' + (it.done ? CIR_S_ON : CIR_S_OFF) + "</span>" +
      '<span class="cx">' + esc(label) + "</span></div>";
  }

  function noteCard(k, g) {
    var items = itemsOf(k).filter(function (x) { return x.gid === g.id; }).sort(byDone);
    /* v17: 「주제」 줄을 없애고 카드는 제목부터 — 제목 아래로 To-do 미리보기 */
    var gTitle = g.title || GROUP_DEF[k];
    var tBg = String(g.titleBg || "").toUpperCase();
    var h = '<div class="ncard" role="button" tabindex="0" data-act="openGroup" data-tab="' + k + '" data-gid="' + g.id +
      '" aria-label="' + esc(gTitle) + ' 목록 열기">';
    /* v21: 카드 위쪽은 색이 꽉 차는 제목 띠 — 고른 색이 없으면 은은한 기본 회색 띠 */
    var ink = tBg ? inkOn(tBg) : "";
    h += '<div class="nc-hd' + (tBg ? " tint" : "") + '"' + (tBg ? ' style="background:' + tBg + '"' : "") + ">" +
      '<div class="nc-t"' + (tBg ? ' style="color:' + ink + '"' : "") + ">" + esc(gTitle) + "</div></div>";
    if (items.length) {
      h += '<div class="nc-items">' + items.slice(0, 4).map(function (x) { return cardItem(k, x); }).join("") + "</div>";
    } else {
      h += '<div class="nc-empty">아직 비어 있어요</div>';
    }
    h += "</div>";
    return h;
  }

  /* v21: 카드 상세 시트의 제목 색 컬러판 — 제목 입력칸 바로 위,
     앱의 다른 색 고르기와 같은 12색 뮤트 팔레트 + 「기본」(색 없음)
     v22: 팔레트는 작은 동그라미 한 줄, 「기본」은 제목 옆에 (일정 시트와 같게) */
  function cardColorPanel(k, g) {
    var cur = String(g.titleBg || "").toUpperCase();
    var h = '<div class="cp ccp"><div class="cp-hd"><span>제목 색</span>' +
      '<button type="button" class="cp-reset' + (cur ? "" : " on") +
      '" data-act="pickCardColor" data-tab="' + k + '" data-gid="' + g.id + '" data-color="">기본</button></div>' +
      '<div class="sw-grid sw-row" data-sw="cardTitleBg">';
    MUTED.forEach(function (p) {
      h += '<button type="button" class="sw' + (cur === p.c ? " sel" : "") + '" data-act="pickCardColor" data-tab="' + k +
        '" data-gid="' + g.id + '" data-color="' + p.c + '" style="background:' + p.c + '" aria-label="' + p.n + " " + p.c + '"></button>';
    });
    h += "</div></div>";
    return h;
  }

  /* 리스트 카드 상세 시트 — v17: 제목만 맨 위, 그 아래 To-do (주제·한 줄 메모·누구는 삭제) */
  function cardSheetHtml(k, g) {
    var items = itemsOf(k).filter(function (x) { return x.gid === g.id; }).sort(byDone);
    var h = '<div class="sheet-hd card-hd"><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>";
    /* 제목을 시트 맨 위로 — 카드에서 가장 크게 보이는 값이라 먼저 고쳐요.
       v19: 입력칸 아래 부가설명 줄은 지웠어요 (제목 → To-do 로 바로).
       v21: 제목 입력칸 바로 위에 제목 바탕색 컬러판을 두었어요. */
    h += cardColorPanel(k, g);
    h += '<form class="form card-meta" id="sheetForm">' +
      '<div class="f"><label>제목</label><input class="field" name="title" value="' + esc(g.title || GROUP_DEF[k]) + '" required autocomplete="off"></div>' +
      "</form>";
    h += '<div class="todo-label" style="margin-top:20px">To-do</div>';
    h += '<form class="todo-add" id="listAddForm" data-tab="' + k + '" data-gid="' + g.id + '">' +
      '<span class="circ" aria-hidden="true">' + CIR_OFF + "</span>" +
      '<input class="todo-in" name="text" placeholder="내용을 추가해보세요" autocomplete="off" enterkeyhint="done" aria-label="내용">' +
      '<button class="todo-add-btn" type="submit">Add</button></form>';
    h += '<div class="todo-items card-items" data-tab="' + k + '" data-gid="' + g.id + '">';
    if (!items.length) h += '<div class="empty">위 칸에 적고 Add 를 눌러 보세요.</div>';
    items.forEach(function (it) { h += diaryRow(k, it); });
    h += "</div>";
    /* 저장·삭제 버튼은 아래에 그대로 — 저장 버튼은 위의 제목·주제 폼(#sheetForm)을 제출해요 */
    h += '<div class="card-acts">' +
      '<button class="btn-primary" type="submit" form="sheetForm">저장하기</button>' +
      '<button type="button" class="btn-del" data-act="delCard" data-tab="' + k + '" data-gid="' + g.id + '">카드 삭제</button></div>';
    return h;
  }

  function openGroupSheet(k, gid) {
    var g = groupOf(k, gid);
    if (!g) return;
    openSheet(cardSheetHtml(k, g), function (fd) {
      var cur = groupOf(k, gid);
      if (!cur) return;
      var t = String(fd.get("title") || "").trim();
      if (!t) { toast("제목을 적어 주세요"); return; }
      cur.title = t;
      /* v16: 한 줄 메모·누구 칸은 없어졌어요 — 예전에 적어 둔 값은 건드리지 않고 그대로 둡니다 */
      openCard = null;
      save(); closeSheet(); renderDiary(); toast("저장했어요");
    });
    /* openSheet 가 열린 카드 표시를 비우므로 시트를 띄운 뒤에 기억해요 */
    openCard = { tab: k, gid: gid };
  }

  /* v31: 지금 열린 시트가 노트 카드 상세(openGroupSheet)이고, 누른 것이 그 안의 항목일 때.
     이때 항목 × 는 «시트는 그대로 두고 목록만» 새로 그립니다. */
  function inCardSheet(el) {
    if (!openCard) return false;
    if (!sheet || !sheetWrap || !sheetWrap.classList.contains("open")) return false;
    return !!(el && el.closest && el.closest("#sheet .card-items"));
  }

  /* 시트를 닫지 않고 항목을 토글·추가·삭제할 때 카드 시트만 다시 그림 */
  function refreshCardSheet() {
    if (!openCard || !sheet || !sheetWrap || !sheetWrap.classList.contains("open")) return;
    var g = groupOf(openCard.tab, openCard.gid);
    if (!g) return;
    var st = sheet.scrollTop;
    /* 항목을 체크해도 방금 적던 제목이 날아가지 않도록 값을 잠깐 들고 있어요 */
    var keepT = sheet.querySelector('#sheetForm input[name="title"]');
    var typedT = keepT ? keepT.value : null;
    /* v19: 체크한 항목이 아래로 내려가는 움직임을 부드럽게 */
    var rtBefore = rowTops("#sheet .card-items");
    sheet.innerHTML = '<div class="grab"></div>' + cardSheetHtml(openCard.tab, g);
    var t2 = sheet.querySelector('#sheetForm input[name="title"]');
    if (t2 && typedT !== null) t2.value = typedT;
    sheet.scrollTop = st;
    rowMoveAnim("#sheet .card-items", rtBefore);
  }

  function viewCards(k) {
    var h = '<div class="ngrid">';
    groupsOf(k).forEach(function (g) { h += noteCard(k, g); });
    h += '<button type="button" class="ncard new" data-act="addGroup" data-tab="' + k + '">' +
      '<span class="ap">' + IC.plus + '</span><span>새 리스트</span></button>';
    h += "</div>";
    h += '<div style="height:18px"></div>';
    return h;
  }
  function firstGroupId(k) {
    var gs = groupsOf(k);
    return gs.length ? gs[0].id : null;
  }
  function updateProgressBar(el, arr, word) {
    var dn = arr.filter(function (x) { return x.done; }).length;
    var n = el.querySelector(".n");
    if (n) n.textContent = dn + " / " + arr.length + " " + word;
    var b = el.querySelector(".bar i");
    if (b) b.style.width = (arr.length ? Math.round(dn / arr.length * 100) : 0) + "%";
  }

  /* 탭별 항목 한 줄 (토글·수정·삭제 동작까지) */
  function diaryRow(k, it) {
    if (k === "todo") {
      return listItemRow(it, '<div class="t tw">' + esc(it.text) + "</div>" +
        (it.memo ? '<div class="sub">' + esc(it.memo) + "</div>" : ""),
        'data-act="toggleTodo" data-id="' + it.id + '"', 'data-act="editTodo" data-id="' + it.id + '"',
        'data-act="delTodo" data-id="' + it.id + '"');
    }
    if (k === "bucket") {
      /* v19: 항목 아래 카테고리 태그(기타 등)는 없앴어요 — 글씨를 눌러도 완료 체크만 토글되고
         `버킷 수정` 시트는 열리지 않아요. 삭제는 오른쪽 ×, 순서는 꾹 눌러 이동. */
      return listItemRow(it, '<div class="t tw">' + esc(it.title) + "</div>" +
        (it.memo ? '<div class="sub"><span class="subtx">' + esc(it.memo) + "</span></div>" : ""),
        'data-act="toggleBucket" data-id="' + it.id + '"', 'data-act="toggleBucket" data-id="' + it.id + '"',
        'data-act="delBucket" data-id="' + it.id + '"');
    }
    return listItemRow(it, '<div class="lrow"><span class="tag ' + it.kind + '">' + (it.kind === "movie" ? "영화" : "먹방") +
      '</span><span class="t">' + esc(it.title) + "</span></div>" +
      (it.review ? '<div class="sub">' + esc(it.review) + "</div>" : "") +
      '<div class="meta">' + stars(it.rating) + "<span>" + Number(it.rating).toFixed(1) +
      '</span><span>·</span><span>' + String(it.date || today).replace(/-/g, ".") + "</span>" +
      (it.place ? "<span>·</span><span>" + esc(it.place) + "</span>" : "") + "</div>",
      'data-act="toggleLog" data-id="' + it.id + '"', 'data-act="editLog" data-id="' + it.id + '"',
      'data-act="delLog" data-id="' + it.id + '"');
  }

  function viewList(l) {
    if (!l) return '<div class="list" style="margin:0 20px"><div class="empty">리스트를 찾을 수 없어요.</div></div>';
    var h = '<div class="note-hd"><div class="nh-l"><span class="t">' + esc(listLabel(l)) + "</span>" +
      '<span class="k">' + (l.kind === "memo" ? "메모" : "체크") + "</span></div></div>";

    var done = l.items.filter(function (i) { return i.done; }).length;
    var pct = l.items.length ? Math.round(done / l.items.length * 100) : 0;
    h += '<div class="progress" data-list="' + l.id + '"><span class="n">' + done + " / " + l.items.length + ' 완료</span><span class="bar"><i style="width:' + pct + '%"></i></span></div>';
    h += doneToggle(done);

    var hide = !!(S.ui && S.ui.hideDone);
    var items = l.items.slice().sort(byDone);
    if (hide) items = items.filter(function (i) { return !i.done; });

    /* 제목 칸 없이 바로 To-do — ○ + 입력 + Add 로 한 줄씩 바로 더해요 */
    h += '<div class="todo-block" data-list="' + l.id + '">';
    h += '<div class="todo-label">To-do</div>';
    h += '<form class="todo-add" id="listAddForm" data-list="' + l.id + '">' +
      '<span class="circ" aria-hidden="true">' + CIR_OFF + "</span>" +
      '<input class="todo-in" name="text" placeholder="내용을 추가해보세요." autocomplete="off" enterkeyhint="done" aria-label="할 일 내용">' +
      '<button class="todo-add-btn" type="submit">Add</button></form>';
    h += '<div class="todo-items" data-list="' + l.id + '">';
    if (!items.length) h += '<div class="empty">' + (l.items.length ? "완료한 항목을 숨겼어요." : "위 칸에 할 일을 적고 Add 를 눌러 보세요.") + "</div>";
    items.forEach(function (it) {
      h += listItemRow(it, '<div class="t tw">' + esc(it.text) + "</div>" +
        (it.memo ? '<div class="sub">' + esc(it.memo) + "</div>" : ""),
        'data-act="toggleListItem" data-list="' + l.id + '" data-id="' + it.id + '"',
        'data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '"',
        'data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '"');
    });
    h += "</div></div>";
    h += '<div style="height:6px"></div>';
    return h;
  }

  function viewTodo() { return viewCards("todo"); }

  function viewBucket() { return viewCards("bucket"); }

  function viewLog() { return viewCards("log"); }

  /* ------------------------------------------------------------------ photos */
  function photoSrc(p) {
    if (!p) return "";
    if (PHOTO_URLS[p.id]) return PHOTO_URLS[p.id];
    return p.src || p.url || "";
  }
  function photoImg(p, big) {
    var src = photoSrc(p);
    if (src) return '<img src="' + esc(src) + '" alt="' + esc(p.title || p.album || "사진") + '"' + (big ? "" : ' loading="lazy" decoding="async"') + ">";
    return art(p.art, big);
  }
  function capHtml(p, cls) {
    if (!p.title && !p.capBg) return "";
    return '<span class="' + cls + '" data-capid="' + p.id + '" style="background:' + capBg(p) + '">' + esc(p.title || "") + "</span>";
  }

  /* 사진첩 v17: 날짜별(최신순) 묶음 + 살짝 기운 폴라로이드 프레임 — IMG_4511 레이아웃 */
  var POLA_TILT = ["-3deg", "2deg", "-1.5deg", "3deg"];
  var PHOTOS_PER_DAY = 3;   /* v18: 하루에 보이는 폴라로이드는 3개까지 */
  function photoDayLabel(day) {
    var d = parse(day);
    if (day === today) return '<span class="d acc">오늘</span>';
    if (day === addDays(today, -1)) return '<span class="d acc">어제</span>';
    return '<span class="d">' + (d.getMonth() + 1) + "월 " + d.getDate() + "일</span>" +
      '<span class="w">· ' + WD[d.getDay()] + '요일</span>';
  }

  /* v23: 사진첩 달력 보기 — 한 달만 보이고 화살표·좌우 밀기로 달을 넘깁니다.
     날짜 칸은 그날 대표 사진으로 가득 차고, 왼쪽 위 날짜 · 오른쪽 아래 장수가 붙어요. */
  function photoMonthYM() {
    var ym = String((S.ui && S.ui.photoMonth) || "");
    return /^\d{4}-\d{2}$/.test(ym) ? ym : today.slice(0, 7);
  }
  function shiftYm(ym, step) {
    var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7)) - 1 + step;
    var d = new Date(y, m, 1);
    return d.getFullYear() + "-" + pad(d.getMonth() + 1);
  }
  function photoCalHtml() {
    var ym = photoMonthYM();
    var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7));
    var daysIn = new Date(y, m, 0).getDate();
    var startDow = new Date(y, m - 1, 1).getDay();
    var byDay = {};
    S.photos.forEach(function (p) {
      var d = String(p.date || "").slice(0, 10);
      if (d.slice(0, 7) !== ym) return;
      (byDay[d] = byDay[d] || []).push(p);
    });
    var cells = [];
    for (var i = 0; i < startDow; i++) cells.push(0);
    for (var d = 1; d <= daysIn; d++) cells.push(d);
    while (cells.length % 7) cells.push(0);

    var h = '<div class="pcal"><div class="pcal-hd">' +
      '<div class="pcal-ym" aria-label="' + y + "년 " + m + '월">' + y + "년 " + m + '월</div>' +
      '<div class="pcal-nav">' +
      '<button type="button" class="cal-arrow" data-act="pcalPrev" aria-label="이전 달">' + IC.left + "</button>" +
      '<button type="button" class="cal-arrow" data-act="pcalNext" aria-label="다음 달">' + IC.right + "</button>" +
      "</div></div>" +
      '<div class="pcal-week"><span>일</span><span>월</span><span>화</span><span>수</span><span>목</span><span>금</span><span>토</span></div>' +
      '<div class="pcal-grid" data-pcal="1" data-rows="' + (cells.length / 7) + '">';

    cells.forEach(function (dayNo) {
      if (!dayNo) { h += '<div class="pcell blank"></div>'; return; }
      var ds = ym + "-" + pad(dayNo);
      var list = (byDay[ds] || []).slice().sort(byDateDesc);
      if (!list.length) {
        h += '<div class="pcell' + (ds === today ? " today" : "") + '"><span class="pn">' + dayNo + "</span></div>";
        return;
      }
      h += '<button type="button" class="pcell has' + (ds === today ? " today" : "") + '" data-act="pcalDay" data-date="' + ds +
        '" aria-label="' + m + "월 " + dayNo + "일 사진 " + list.length + '장 열기">' +
        photoImg(list[0]) + '<span class="pn">' + dayNo + "</span>" +
        (list.length > 1 ? '<span class="pc">' + list.length + "</span>" : "") + "</button>";
    });
    h += "</div>";
    if (!Object.keys(byDay).length) h += '<div class="pcal-empty">이 달에 담은 사진이 없어요.</div>';
    h += '<div style="height:24px"></div></div>';
    return h;
  }

  /* v24: 사진 달력 칸 높이 — 화면의 세로 여유를 재서 5주·6주 달력이 탭바 바로 위까지 차도록 잡아요.
     폭보다 세로로 길게(폭의 최대 2배) 키우되, 그 이상은 사진이 길쭉해져서 멈춥니다. */
  function fitPhotoCal() {
    var scr = $("#s-photo");
    if (!scr) return;
    var grid = scr.querySelector(".pcal-grid");
    if (!grid || grid.children.length < 7) return;
    var host = $("#screens");
    var rows = Math.round(grid.children.length / 7);
    var gBox = grid.getBoundingClientRect();
    var hostBox = host ? host.getBoundingClientRect() : null;
    var top = gBox.top - (hostBox ? hostBox.top : 0) + (host ? host.scrollTop : 0);
    var room = (host ? host.clientHeight : window.innerHeight) - top - 12;
    var gap = parseFloat(getComputedStyle(grid).rowGap) || 4;
    var colW = grid.children[0] ? grid.children[0].getBoundingClientRect().width : 0;
    var byRoom = (room - gap * (rows - 1)) / rows;
    var h = Math.round(Math.min(Math.max(byRoom, 76), Math.max(82, colW * 2)));
    /* 사진이 하나도 없는 달은 칸을 조금만 키워 「이 달에 담은 사진이 없어요」가 화면 안에 보이게 */
    if (scr.querySelector(".pcal-empty")) h = Math.min(h, 76);
    grid.style.setProperty("--pcell-h", h + "px");
  }
  window.addEventListener("resize", function () {
    if (current === "photo") fitPhotoCal();
  });

  function renderPhoto() {
    /* v21: 사진첩은 제목·「N장의 순간」 없이 오른쪽 + 버튼만 — 상단 여백도 군더더기 없이 */
    /* v23: + 옆에 달력 아이콘 — 누르면 그 달 사진을 달력으로 (다시 누르면 목록으로) */
    var pcOn = !!(S.ui && S.ui.photoCal);
    var h = '<header class="hdr hdr-min' + capCls("photo") + '"' + capStyle("photo") + ' data-pg="photo">' +
      '<div class="hdr-empty"></div>' +
      '<div class="hdr-acts">' +
      '<button class="round-btn" data-act="togglePhotoCal" aria-label="' + (pcOn ? "사진 목록으로" : "사진 달력 보기") +
      '" title="' + (pcOn ? "사진 목록으로" : "사진 달력 보기") + '">' + (pcOn ? IC.grid : IC.cal) + "</button>" +
      '<button class="round-btn" data-act="addPhoto" aria-label="사진 추가" title="사진 추가">' + IC.plus + "</button></div></header>";
    if (pcOn) {
      h += photoCalHtml();
      $("#s-photo").innerHTML = h;
      fitPhotoCal();
      return;
    }
    /* 앨범 대신 날짜로 묶어요 — 하루에 담은 순간이 한 줄에 모입니다 */
    var groups = [];
    var map = {};
    S.photos.slice().sort(byDateDesc).forEach(function (p) {
      var k = String(p.date || "").slice(0, 10);
      if (!map[k]) { map[k] = { date: k, items: [] }; groups.push(map[k]); }
      map[k].items.push(p);
    });
    groups.forEach(function (g) {
      /* 그날 사진이 모두 한 앨범이면 오른쪽에 앨범 이름을 함께 적어요 */
      var albums = [];
      g.items.forEach(function (p) { var a = String(p.album || "").trim(); if (a && albums.indexOf(a) < 0) albums.push(a); });
      var meta = g.items.length + "장" + (albums.length === 1 ? " · " + esc(albums[0]) : "");
      /* v18: 하루는 폴라로이드 3개까지 — 넘치면 세 번째에 +N, 눌러서 그날 사진을 모두 봐요 */
      var shown = g.items.slice(0, PHOTOS_PER_DAY);
      var rest = g.items.length - shown.length;
      h += '<div class="pday"><div class="pday-hd">' + photoDayLabel(g.date) +
        '<span class="c">' + meta + "</span></div>" +
        '<div class="polas">' +
        shown.map(function (p, i) {
          var more = (rest > 0 && i === shown.length - 1) ? '<span class="pola-more">+' + rest + "</span>" : "";
          return '<button class="pola" style="--tilt:' + POLA_TILT[i % POLA_TILT.length] + '" data-act="openPhoto" data-id="' + p.id +
            '" aria-label="' + esc(p.title || p.album || "사진") + ' 열기">' +
            '<span class="pola-pic">' + photoImg(p) + more + "</span>" +
            '<span class="pola-chin' + (p.capBg ? " tinted" : "") + '"' + (p.capBg ? ' style="background:' + esc(p.capBg) + '"' : "") + ">" +
            esc(p.title || "") + "</span></button>";
        }).join("") + "</div></div>";
    });
    if (!S.photos.length) {
      h += '<div class="album"><div class="list" style="margin:0"><div class="empty">아직 사진이 없어요.<br>오른쪽 위 <b>+</b> 로 이 순간을 담아 보세요.</div></div></div>';
    }
    h += '<div style="height:24px"></div>';
    $("#s-photo").innerHTML = h;
  }

  /* ------------------------------------------------------------------ sheet */
  var sheetWrap = $("#sheetWrap"), sheet = $("#sheet"), sheetSubmit = null;
  var sheetCenter = false;   /* v21: 일정 검색처럼 떠 있는 모달로 띄울 때 */
  var vvBound = false;
  /* v22: 아이폰 키보드가 올라오면 «보이는 화면»이 짧아져요. 그 높이에 맞춰
     검색 모달의 최대 높이를 다시 잡아 줍니다 — 검색칸과 결과가 키보드 위에 남아요. */
  function fitCenterSheet() {
    if (!sheet || !sheetWrap.classList.contains("sheet-center")) return;
    var vv = window.visualViewport;
    var vh = (vv && vv.height) || window.innerHeight || 844;
    var top = 64;
    try { top = parseFloat(getComputedStyle(sheetWrap).paddingTop) || 64; } catch (e) {}
    sheet.style.maxHeight = Math.max(200, Math.round(vh - top - 14)) + "px";
  }
  function bindViewportFit() {
    if (vvBound || !window.visualViewport) return;
    vvBound = true;
    window.visualViewport.addEventListener("resize", fitCenterSheet);
    window.visualViewport.addEventListener("scroll", fitCenterSheet);
    window.addEventListener("resize", fitCenterSheet);
  }
  function openSheet(html, onSubmit) {
    personSheetWho = null;
    openCard = null;
    sheetWrap.classList.toggle("sheet-center", !!sheetCenter);
    sheetCenter = false;
    sheet.innerHTML = '<div class="grab"></div>' + html;
    sheetSubmit = onSubmit || null;
    sheetWrap.classList.add("open");
    sheetWrap.setAttribute("aria-hidden", "false");
    sheet.style.maxHeight = "";
    sheet.scrollTop = 0;
    if (sheetWrap.classList.contains("sheet-center")) { bindViewportFit(); fitCenterSheet(); }
  }
  function closeSheet() {
    personSheetWho = null;
    openCard = null;
    sheetWrap.classList.remove("sheet-center");
    sheet.style.maxHeight = "";
    sheetWrap.classList.remove("open");
    sheetWrap.setAttribute("aria-hidden", "true");
    sheetSubmit = null;
    pendingUrls.forEach(function (u) { try { URL.revokeObjectURL(u); } catch (e) {} });
    pendingUrls = [];
    pendingFiles = [];
    /* 시트에서 고친 내용(카드 안 To-do 등)이 뒤 화면에도 바로 보이도록 노트를 다시 그림 */
    var dEl = document.getElementById("s-diary");
    if (dEl && dEl.classList.contains("active")) renderDiary();
  }

  function toast(msg) {
    var t = $("#toast");
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(t._tid);
    t._tid = setTimeout(function () { t.classList.remove("show"); }, 1600);
  }

  /* ------------------------------------------------------------------ forms */
  function sheetHead(title) {
    return '<div class="sheet-hd"><h2>' + title + '</h2><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>";
  }

  var LIST_EMOJI = ["📌", "🧳", "🛒", "🍽️", "🎁", "✅"];

  function formNewList(l) {
    var curEmo = l ? (l.emoji || "📌") : "📌";
    var emo = LIST_EMOJI.map(function (e) {
      return '<button type="button" class="emk' + (e === curEmo ? " sel" : "") + '" data-act="lpick" data-emoji="' + e + '" aria-label="' + e + '">' + e + "</button>";
    }).join("");
    var kindMemo = !!l && l.kind === "memo";
    return sheetHead(l ? "리스트 수정" : "새 리스트") +
      '<p class="sheet-sub">' + (l ? "이름·항목 형식·이모지를 바로 바꿀 수 있어요." : "노트 안에 내가 쓰고 싶은 리스트를 하나 더 만들어요.") + "</p>" +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>리스트 이름</label><input class="field" name="title" value="' + (l ? esc(l.title) : "") + '" placeholder="예) 여행 준비물, 주말 데이트" required autocomplete="off"></div>' +
      '<div class="f"><label>형식</label><div class="seg seg-sm" data-group="lkind">' +
      '<button type="button" class="seg-btn' + (kindMemo ? "" : " active") + '" data-act="lkind" data-kind="check">체크리스트</button>' +
      '<button type="button" class="seg-btn' + (kindMemo ? " active" : "") + '" data-act="lkind" data-kind="memo">메모</button></div>' +
      '<input type="hidden" name="kind" value="' + (kindMemo ? "memo" : "check") + '"></div>' +
      '<div class="f"><label>이모지</label><div class="emk-row">' + emo + "</div>" +
      '<input type="hidden" name="emoji" value="' + esc(curEmo) + '"></div>' +
      '<button class="btn-primary" type="submit">' + (l ? "저장하기" : "만들기") + "</button></form>";
  }

  function formNoteSettings() {
    var h = sheetHead("노트 설정");
    h += '<p class="sheet-sub">탭 이름과 내 리스트를 여기서 정리해요. 이모지와 이름을 한 칸에 함께 적으면 돼요.</p>';
    h += '<form class="form" id="noteForm" style="margin-top:12px">';
    h += '<div class="set-lbl">탭 이름</div>';
    NOTE_BASE.forEach(function (k) {
      var t = noteTab(k);
      /* v18: 이모지 칸을 따로 두지 않고 한 칸에 — 「📝 메모」처럼 이모지와 이름을 함께 적어요 */
      h += '<div class="nt-row">' +
        '<input class="field nt-nm" name="t_' + k + '" value="' + esc(t.e ? t.e + " " + t.n : t.n) + '" placeholder="예) 📝 메모" aria-label="탭 이름" autocomplete="off">' +
        "</div>";
    });
    h += '<div class="set-lbl" style="margin-top:20px">내 리스트</div>';
    if (!S.lists.length) h += '<div class="set-hint" style="margin-top:0">아직 만든 리스트가 없어요. 아래에서 새로 만들 수 있어요.</div>';
    S.lists.forEach(function (l) {
      h += '<div class="nt-row">' +
        '<input class="field nt-nm" name="l_' + l.id + '" value="' + esc(listLabel(l)) + '" placeholder="예) 🧳 여행 준비물" aria-label="리스트 이름" autocomplete="off">' +
        '<button type="button" class="nt-del" data-act="delListFromNote" data-id="' + l.id + '">삭제</button></div>';
    });
    h += '<div class="nt-new"><div class="set-lbl">새 리스트</div>' +
      '<div class="nt-row">' +
      '<input class="field nt-nm" name="new_n" placeholder="예) 📌 여행 준비물" aria-label="새 리스트 이름" autocomplete="off">' +
      '<select class="field nt-kind" name="new_kind" aria-label="새 리스트 형식"><option value="check">체크</option><option value="memo">메모</option></select>' +
      "</div></div>";
    h += '<div style="height:14px"></div><button class="btn-primary" type="submit">저장하기</button></form>';
    h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
    return h;
  }

  function openNoteSettings() { openSheet(formNoteSettings()); }

  function formListItem(l, it) {
    var isEdit = !!it;
    var memo = !!l && l.kind === "memo";
    return sheetHead(isEdit ? "항목 수정" : "항목 추가") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>' + (memo ? "메모" : "항목") + "</label>" +
      (memo
        ? '<textarea class="field" name="text" rows="3" required placeholder="예) 기념일 선물 아이디어">' + (it ? esc(it.text) : "") + "</textarea>"
        : '<input class="field" name="text" value="' + (it ? esc(it.text) : "") + '" placeholder="예) 우산 챙기기" required autocomplete="off">') +
      "</div>" +
      '<div class="f"><label>상세 메모</label><textarea class="field" name="memo" rows="3" placeholder="선택 · 더 자세히 적어 두세요">' + (it ? esc(it.memo || "") : "") + "</textarea></div>" +
      (isEdit ? '<button type="button" class="btn-del" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '">삭제</button>' : "") +
      '<button class="btn-primary" type="submit">' + (isEdit ? "저장하기" : "추가하기") + "</button></form>";
  }

  function askConfirm(msg, label, onYes, title) {
    openSheet(sheetHead(title || "리스트 삭제") + '<p class="sheet-sub">' + msg + "</p>" +
      '<form class="form" id="sheetForm"><button class="btn-primary" type="submit">' + label + "</button></form>" +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">취소</button>',
      function () { closeSheet(); if (onYes) onYes(); });
  }

  /* v28: 일정 추가·수정 시트 — 컬러 → 제목 → 큰 «26.11.17 / 화요일 ~ 26.11.17 / 화요일» → 누구와.
     시간 설정은 없앴고, 저장은 헤더 오른쪽 검정 ✓ 로 해요. */
  var IC_CHK = '<svg width="21" height="21" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.4l4.4 4.4L19 6.8"/></svg>';

  /* v28: 시작·종료 날짜 칸 — 날짜 아래에 요일(화요일) */
  function evSideHtml(side, label, ds) {
    return '<div class="ev-side">' +
      '<label class="ev-datewrap">' +
      '<span class="ev-dbig" data-dbig="' + side + '">' + evDateBig(ds) + "</span>" +
      '<span class="ev-dow" data-dow="' + side + '">' + evDowFull(ds) + "</span>" +
      '<input type="date" class="ev-date-in js-evdate" data-side="' + side + '" name="' + side + '" value="' + ds + '" required aria-label="' + label + '">' +
      "</label>" +
      "</div>";
  }

  /* v28: 일정 시트 — 새 일정(ev 없음)과 수정(ev 있음)에 함께 씁니다.
     수정할 때는 컬러·제목·시작일·종료일·누구와가 채워진 채로 열려요. */
  function formEvent(dateStr, ev) {
    var edit = !!ev;
    var ds = edit ? evStart(ev) : (dateStr || today);
    var de = edit ? evEnd(ev) : ds;
    var ecol = edit ? String(ev.color || "").toUpperCase() : "";
    var ewho = edit ? (ev.who || "both") : "both";
    var wopts = [["both", "함께"], ["me", S.couple.me], ["you", S.couple.you]].map(function (w) {
      return '<button type="button" class="wopt' + (ewho === w[0] ? " active" : "") + '" data-act="who" data-who="' + w[0] + '">' +
        (w[0] === "both" ? avSpan("me") + avSpan("you") : avSpan(w[0])) + esc(w[1]) + "</button>";
    }).join("");
    var sw = "";
    MUTED.forEach(function (p) {
      sw += '<button type="button" class="sw' + (ecol === p.c ? " sel" : "") + '" data-act="pickEvColor" data-color="' + p.c +
        '" style="background:' + p.c + '" aria-label="' + p.n + " " + p.c + '"></button>';
    });
    var saveWord = edit ? "저장" : "추가";
    return '<div class="sheet-hd ev-hd">' +
      '<button type="button" class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button>" +
      "<h2>일정 " + saveWord + "</h2>" +
      '<button type="submit" form="sheetForm" id="evSave" class="icon-btn ev-chk" aria-label="일정 ' + saveWord + '" title="일정 ' + saveWord + '">' + IC_CHK + "</button>" +
      "</div>" +
      '<form class="form eform" id="sheetForm">' +
      '<input type="hidden" name="color" value="' + ecol + '">' +
      '<input type="hidden" name="evId" value="' + (edit ? esc(ev.id) : "") + '">' +
      '<div class="f"><label>제목</label><input class="field ev-title" name="title" value="' + (edit ? esc(ev.title) : "") + '" placeholder="예) 성수 데이트" required autocomplete="off"></div>' +
      '<div class="cp ccp ev-cp"><div class="cp-hd"><span>컬러</span>' +
      '<button type="button" class="cp-reset' + (ecol ? "" : " on") + '" data-act="pickEvColor" data-color="">기본</button></div>' +
      '<div class="sw-row" data-sw="evColor">' + sw + "</div></div>" +
      '<div class="ev-when">' + evSideHtml("start", "시작 날짜", ds) + '<span class="ev-tilde">~</span>' +
      evSideHtml("end", "종료 날짜", de) + "</div>" +
      '<div class="wsel" data-group="who" aria-label="누구와">' + wopts + "</div>" +
      '<input type="hidden" name="who" value="' + ewho + '">' +
      /* 아래 버튼도 그대로 — 헤더의 검은 ✓ 와 같은 일을 합니다 */
      '<button class="btn-primary" type="submit">' + (edit ? "저장하기" : "추가하기") + "</button>" +
      "</form>";
  }

  function whoOpts(cur) {
    var list = ["함께", "나", S.couple.you];
    var seen = {};
    return list.filter(function (w) {
      var k = String(w);
      if (!k || seen[k]) return false;
      seen[k] = 1; return true;
    }).map(function (w) {
      return '<option value="' + esc(w) + '"' + (w === cur ? " selected" : "") + ">" + esc(w) + "</option>";
    }).join("");
  }

  function formTodo(t) {
    return sheetHead(t ? noteTab("todo").n + " 수정" : noteTab("todo").n + " 추가") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>' + esc(noteTab("todo").n) + '</label><input class="field" name="text" value="' + (t ? esc(t.text) : "") + '" placeholder="예) 주말 장보기" required autocomplete="off"></div>' +
      '<div class="f"><label>상세 메모</label><textarea class="field" name="memo" rows="3" placeholder="선택 · 필요한 내용을 더 적어 두세요">' + (t ? esc(t.memo || "") : "") + "</textarea></div>" +
      (t ? '<button type="button" class="btn-del" data-act="delTodo" data-id="' + t.id + '">' + esc(noteTab("todo").n) + " 삭제</button>" : "") +
      '<button class="btn-primary" type="submit">' + (t ? "저장하기" : "추가하기") + "</button></form>";
  }

  function formBucket(b) {
    var cats = ["여행", "맛집", "취미", "기타"];
    var opts = cats.map(function (c) {
      return '<option value="' + c + '"' + (b && b.cat === c ? " selected" : "") + ">" + c + "</option>";
    }).join("");
    return sheetHead(b ? "버킷 수정" : "버킷 추가") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>하고 싶은 것</label><input class="field" name="title" value="' + (b ? esc(b.title) : "") + '" placeholder="예) 제주도 3박 4일" required autocomplete="off"></div>' +
      '<div class="f"><label>카테고리</label><select class="field" name="cat">' + opts + "</select></div>" +
      '<div class="f"><label>상세 메모</label><textarea class="field" name="memo" rows="3" placeholder="선택 · 언제, 누구와, 어떻게 할지">' + (b ? esc(b.memo || "") : "") + "</textarea></div>" +
      (b ? '<div class="f"><label>상태</label><select class="field" name="done"><option value="">예정</option><option value="1"' + (b.done ? " selected" : "") + ">달성</option></select></div>" : "") +
      (b ? '<button type="button" class="btn-del" data-act="delBucket" data-id="' + b.id + '">버킷 삭제</button>' : "") +
      '<button class="btn-primary" type="submit">' + (b ? "저장하기" : "추가하기") + "</button></form>";
  }

  function formLog(l) {
    var r = l ? Math.max(0, Math.min(5, Number(l.rating) || 0)) : 4;
    var kindFood = !!l && l.kind === "food";
    var stars5 = "";
    for (var i = 1; i <= 5; i++) stars5 += '<button type="button" class="rate-star' + (i <= r ? " on" : "") + '" data-act="rate" data-val="' + i + '" aria-label="' + i + '점">' + STAR + "</button>";
    return sheetHead(l ? "기록 수정" : "기록 추가") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>종류</label><div class="seg seg-sm" data-group="kind">' +
      '<button type="button" class="seg-btn' + (kindFood ? "" : " active") + '" data-act="kind" data-kind="movie">영화</button>' +
      '<button type="button" class="seg-btn' + (kindFood ? " active" : "") + '" data-act="kind" data-kind="food">먹방</button></div>' +
      '<input type="hidden" name="kind" value="' + (kindFood ? "food" : "movie") + '"></div>' +
      '<div class="f"><label>제목</label><input class="field" name="title" value="' + (l ? esc(l.title) : "") + '" placeholder="예) 화양연화 / 성수 파스타" required autocomplete="off"></div>' +
      '<div class="f"><label>별점</label><div class="rate">' + stars5 + '<span class="val">' + r.toFixed(1) + "</span></div>" +
      '<input type="hidden" name="rating" value="' + r + '"></div>' +
      '<div class="two"><div class="f"><label>날짜</label><input class="field" type="date" name="date" value="' + (l ? l.date : today) + '" required></div>' +
      '<div class="f"><label>장소</label><input class="field" name="place" value="' + (l ? esc(l.place || "") : "") + '" placeholder="선택" autocomplete="off"></div></div>' +
      '<div class="f"><label>한 줄 평</label><input class="field" name="review" value="' + (l ? esc(l.review || "") : "") + '" placeholder="한 줄로 남겨 주세요" autocomplete="off"></div>' +
      (l ? '<button type="button" class="btn-del" data-act="delLog" data-id="' + l.id + '">기록 삭제</button>' : "") +
      '<button class="btn-primary" type="submit">' + (l ? "저장하기" : "추가하기") + "</button></form>";
  }

  function formDday() {
    var c = S.couple;
    var bd = c.birthdays || {};
    var h = sheetHead("기념일 & 생일");

    /* 1. 문구는 맨 위에서 — 라벨은 「우리는」 */
    h += '<form class="form" id="sheetForm">' +
      '<div class="f"><label>우리는</label><input class="field" name="phrase" value="' + esc(ddayPhrase()) + '" placeholder="소영과 준영이 함께한 지" autocomplete="off"></div>' +
      '<p class="sheet-sub" style="margin-top:-4px">홈 D-day 위에 이 문구가 그대로 보여요.</p>' +
      '<div class="f"><label>처음 만난 날</label><input class="field" type="date" name="since" value="' + c.since + '" required></div>' +
      '<div class="f"><label>D-day 표기</label><div class="seg seg-sm" data-group="fmt">' +
      '<button type="button" class="seg-btn' + (c.fmt === "Y" ? "" : " active") + '" data-act="fmt" data-fmt="D">일수로 · D+365일</button>' +
      '<button type="button" class="seg-btn' + (c.fmt === "Y" ? " active" : "") + '" data-act="fmt" data-fmt="Y">연·일로 · 1년 4일째</button>' +
      '</div><input type="hidden" name="fmt" value="' + (c.fmt === "Y" ? "Y" : "D") + '"></div>' +
      '<p style="font-size:11.5px;color:var(--ink-3);line-height:1.6;margin-top:-2px">이 날을 기준으로 D-day와 기념일을 계산해요.</p>';

    /* 2. 기념일 & 생일 — 주년은 그대로, 두 사람 생일은 달력에서 바로 고쳐요 */
    h += '<div class="mile-hd">기념일 &amp; 생일</div><div class="mile">';
    var since = parse(c.since);
    for (var n = 1; n <= 3; n++) {
      var ad = new Date(since.getFullYear() + n, since.getMonth(), since.getDate());
      var ads = iso(ad), add = diffDays(today, ads);
      h += mileRow(n + "주년", ads.replace(/-/g, "."), add === 0 ? "오늘" : add > 0 ? "D-" + add : -add + "일 지남", add >= 0 && add <= 30);
    }
    ["me", "you"].forEach(function (w) {
      var nm = w === "me" ? c.me : c.you;
      var nb = nextBirthday(bd[w]);
      h += '<div class="mile-bd">' +
        '<div class="mile-row bd-top">' +
        '<span class="mile-n">' + esc(nm) + ' 생일</span>' +
        '<span class="mile-d" data-bdtxt="' + w + '">' + esc(bdayText(bd[w]) || "날짜 입력") + "</span>" +
        '<span class="mile-x' + (nb && nb.days <= 30 ? " soon" : "") + '" data-bdleft="' + w + '">' +
        (nb ? (nb.days === 0 ? "오늘" : "D-" + nb.days) : "—") + "</span></div>" +
        '<input class="field bd-in js-bday" type="date" name="bd' + (w === "me" ? "Me" : "You") +
        '" data-who="' + w + '" value="' + bdayInput(w) + '" aria-label="' + esc(nm) + ' 생일 달력">' +
        "</div>";
    });
    h += "</div>";
    h += '<p class="cp-note" style="margin-top:10px">고른 생일은 바로 위에 「6월 26일」처럼 남아요. 연도는 표시에만 쓰이고 D-day는 월·일로 계산해요.</p>';
    h += '<button class="btn-primary" type="submit">저장하기</button></form>';
    return h;
  }

  function newInviteCode() { return String(Math.floor(100000 + Math.random() * 900000)); }

  /* 커플 연결 시트 — 초대 코드는 여기서만 보입니다 */
  function formLink() {
    var li = S.link || {};
    var code = myInviteCode();
    var h = sheetHead("커플 연결");
    if (li.connected) {
      h += '<div class="link-on"><span class="set-av' + (avPic("you") ? " pic" : "") + '" style="background:' + avColor("you") + '">' + avInner("you") + "</span>" +
        '<div><div class="link-nm">' + esc(S.couple.you) + "</div><div class=\"link-sub\">커플 연결됨 · 함께 기록 중</div></div></div>";
      h += '<div class="set-card" style="margin:18px 0 0"><div class="set-lbl">내 초대 코드</div>' +
        '<div class="set-code-row"><div class="set-code">' + codeFmt(code) + "</div>" +
        '<button class="set-btn" data-act="copyCode">복사</button></div>' +
        '<div class="set-hint">다른 기기에서 이 코드를 입력하면 이어서 함께 쓸 수 있어요.</div></div>';
      h += '<div style="height:18px"></div><button class="btn-line" data-act="unlink">연결 해제</button>';
      h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
      return h;
    }
    h += '<p class="sheet-sub">내 초대 코드를 상대에게 알려 주거나, 상대 코드를 입력하면 연결돼요.</p>';
    h += '<div class="set-card" style="margin:14px 0 0"><div class="set-lbl">내 초대 코드</div>' +
      '<div class="set-code-row"><div class="set-code">' + codeFmt(code) + "</div>" +
      '<button class="set-btn" data-act="copyCode">복사</button></div>' +
      '<button class="link-mini" data-act="newCode">코드 새로 만들기</button>' +
      '<div class="set-hint">이 6자리를 상대에게 알려 주세요.</div></div>';
    h += '<div class="link-or"><span>또는</span></div>';
    h += '<form class="form" id="linkForm" style="margin-top:0">' +
      '<div class="f"><label>상대 초대 코드</label>' +
      '<div class="link-in-row"><input class="field" name="code" inputmode="numeric" maxlength="6" placeholder="6자리 숫자" autocomplete="off">' +
      '<button class="set-btn on" type="submit">연결하기</button></div></div></form>';
    h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
    return h;
  }



  function swRow(target, cur, pal) {
    var list = pal || PALETTE;
    var curU = String(cur || "").toUpperCase();
    var h = '<div class="sw-grid sw-row" data-sw="' + target + '">';
    list.forEach(function (p) {
      h += '<button class="sw' + (curU === p.c ? " sel" : "") + '" data-act="pickColor" data-target="' + target +
        '" data-color="' + p.c + '" style="background:' + p.c + '" aria-label="' + p.n + ' ' + p.c + '"></button>';
    });
    return h + "</div>";
  }

  /* v19: 팔레트 알맹이만(제목 줄·헥스 코드 없이) — 컬러 시트에서 씁니다 */
  function cpGrid(target, cur, pal, fallback) {
    var curU = cur ? String(cur).toUpperCase() : "";
    return swRow(target, curU, pal) +
      '<div class="cp-foot"><label class="cp-pick"><input type="color" class="js-color" data-target="' + target + '" value="' +
      (curU || fallback) + '"><span>컬러</span></label>' +
      '<button class="cp-reset' + (cur ? "" : " on") + '" data-act="pickColor" data-target="' + target + '" data-color="">기본</button></div>';
  }

  function cpBlock(title, target, cur, pal, fallback) {
    return '<div class="cp"><div class="cp-hd"><span>' + title + '</span><span class="cp-val" data-val="' + target + '">' +
      (cur ? String(cur).toUpperCase() : "기본") + "</span></div>" + cpGrid(target, cur, pal, fallback) + "</div>";
  }

  function formTheme() {
    var t = S.theme || {};
    var dark = t.mode === "dark";
    /* v19: 위 안내 문구·팔레트 제목 라벨(다가오는 일정 · N월의 우리)·헥스 코드를 지웠어요.
       화면(라이트/다크) → 컬러(12색 팔레트 · 컬러/기본) → 설명 → 완료 순서이고,
       두 섹션 제목 「화면」·「컬러」는 같은 .cp-hd 캡션으로 크기·굵기를 똑같이 맞춥니다. */
    return sheetHead("컬러") +
      '<div class="cp"><div class="cp-hd"><span>화면</span><span class="cp-val">' + (dark ? "다크" : "라이트") + '</span></div>' +
      '<div class="seg seg-sm" data-group="mode">' +
      '<button type="button" class="seg-btn' + (dark ? "" : " active") + '" data-act="mode" data-mode="light">라이트</button>' +
      '<button type="button" class="seg-btn' + (dark ? " active" : "") + '" data-act="mode" data-mode="dark">다크</button>' +
      "</div></div>" +
      '<div class="cp" role="group" aria-label="홈 제목 줄·버튼 색">' +
      '<div class="cp-hd"><span>컬러</span></div>' +
      cpGrid("homeTitleBg", t.homeTitleBg, MUTED, "#F2CFC9") + "</div>" +
      '<p class="cp-note">고른 색은 홈 제목 줄(문구) 바탕과 저장·완료 같은 기본 버튼에 함께 칠해지고, 제목 줄 글씨는 색에 맞춰, 버튼 글씨는 검정으로 또렷하게 보여요. 바로 적용되고 앱을 다시 열어도 그대로 남아 있어요. ‘기본’으로 두면 원래대로 돌아가요.</p>' +
      '<button class="btn-primary" data-close="1">완료</button>';
  }

  /* 새 리스트 시트 — v17: 제목만 (주제·한 줄 메모·누구 칸 삭제) */
  function formGroup(k, g) {
    var isNew = !g;
    return sheetHead(isNew ? "새 리스트" : "리스트 수정") +
      '<p class="sheet-sub">탭 안에 리스트를 나눠 담을 수 있어요. 제목을 적어 주세요.</p>' +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>제목</label><input class="field" name="title" value="' + esc(g ? g.title : "") +
      '" placeholder="예) 장보기" autocomplete="off"></div>' +
      '<button class="btn-primary" type="submit">저장</button></form>' +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
  }

  /* 기념일 시트 안 생일 달력을 고르는 순간 「6월 26일 · D-223」을 바로 갱신 */
  function updateBdayRow(inp) {
    var w = inp.getAttribute("data-who") === "you" ? "you" : "me";
    var val = String(inp.value || "");
    var nb = nextBirthday(val);
    var left = sheet.querySelector('[data-bdleft="' + w + '"]');
    if (left) {
      left.textContent = nb ? (nb.days === 0 ? "오늘" : "D-" + nb.days) : "—";
      left.classList.toggle("soon", !!nb && nb.days <= 30);
    }
    var txt = sheet.querySelector('[data-bdtxt="' + w + '"]');
    if (txt) txt.textContent = bdayText(val) || "날짜 입력";
  }

  function syncThemeSheet() {
    if (!sheet) return;
    var modeGroup = sheet.querySelector('[data-group="mode"]');
    if (modeGroup) {
      var dk = (S.theme || {}).mode === "dark";
      modeGroup.querySelectorAll(".seg-btn").forEach(function (b) {
        b.classList.toggle("active", (b.getAttribute("data-mode") === "dark") === dk);
      });
      var mv = modeGroup.parentNode.querySelector('.cp-val');
      if (mv) mv.textContent = dk ? "다크" : "라이트";
    }
    ["name", "log", "homeTitleBg"].forEach(function (t) {
      var cur = String((S.theme || {})[t] || "").toUpperCase();
      var val = sheet.querySelector('.cp-val[data-val="' + t + '"]');
      if (val) val.textContent = cur || "기본";
      var row = sheet.querySelector('.sw-grid[data-sw="' + t + '"]');
      if (row) row.querySelectorAll(".sw").forEach(function (b) {
        b.classList.toggle("sel", String(b.getAttribute("data-color") || "").toUpperCase() === cur);
      });
      var rb = sheet.querySelector('.cp-reset[data-target="' + t + '"]');
      if (rb) rb.classList.toggle("on", !cur);
      var inp = sheet.querySelector('.js-color[data-target="' + t + '"]');
      if (inp && cur && String(inp.value).toUpperCase() !== cur) inp.value = cur;
    });
  }

  /* ------------------------------------------------------------------ photo detail */
  /* v18: 폴라로이드를 누르면 그날 사진이 크게 — 좌우로 넘겨 보고, 캡션·정보·삭제도 여기서 */
  var photoView = null;    /* { ids: [...그날 사진 id], i: 지금 보고 있는 순서 } */

  function photoDayIds(p) {
    var day = String((p && p.date) || "").slice(0, 10);
    return S.photos.slice().sort(byDateDesc)
      .filter(function (x) { return String(x.date || "").slice(0, 10) === day; })
      .map(function (x) { return x.id; });
  }

  function photoViewBody() {
    var ids = (photoView && photoView.ids) || [];
    var i = photoView ? photoView.i : 0;
    var p = S.photos.filter(function (x) { return x.id === ids[i]; })[0];
    if (!p) {
      return '<div class="sheet-hd"><h2>사진</h2><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>" +
        '<p class="sheet-sub">사진을 찾을 수 없어요.</p>';
    }
    var d = parse(p.date);
    var cur = p.capBg || "";
    var sw = '<div class="sw-grid" data-sw="cap">';
    CAP_PALETTE.forEach(function (c) {
      sw += '<button class="sw' + (cur === c.c ? " sel" : "") + '" data-act="pickCap" data-id="' + p.id +
        '" data-color="' + c.c + '" style="background:' + c.c + '" aria-label="' + c.n + ' ' + c.c + '"></button>';
    });
    sw += "</div>";
    var many = ids.length > 1;
    var html = '<div class="sheet-hd"><h2>' + esc(p.title || p.album || "사진") + '</h2><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>" +
      '<div class="pview" data-pv="1">' + photoImg(p, true) +
      '<button class="pv-nav prev" type="button" data-act="photoStep" data-step="-1" aria-label="이전 사진"' + (i <= 0 ? " disabled" : "") + ">" + IC.left + "</button>" +
      '<button class="pv-nav next" type="button" data-act="photoStep" data-step="1" aria-label="다음 사진"' + (i >= ids.length - 1 ? " disabled" : "") + ">" + IC.right + "</button>" +
      "</div>" +
      '<div class="pv-cap">' + capHtml(p, "pd-cap") + "</div>" +
      (many ? '<div class="pv-count">' + (i + 1) + " / " + ids.length + " · 옆으로 넘겨 보기</div>" : "") +
      '<div style="margin-top:14px">' +
      '<div style="font-size:13.5px;font-weight:600;letter-spacing:-.02em">' + esc(p.album) + "</div>" +
      '<div style="font-size:11.5px;color:var(--ink-3);margin-top:3px">' + d.getFullYear() + "." + pad(d.getMonth() + 1) + "." + pad(d.getDate()) + (p.place ? " · " + esc(p.place) : "") + "</div></div>" +
      (p.memo ? '<p style="margin-top:14px;font-size:12.5px;color:var(--ink-2);line-height:1.65">' + esc(p.memo) + "</p>" : "") +
      '<div class="photo-tools"><button class="set-btn" data-act="photoEdit" data-id="' + p.id + '">정보 수정</button>' +
      '<button class="set-btn warn" data-act="photoDelete" data-id="' + p.id + '">삭제</button></div>' +
      '<div class="cp"><div class="cp-hd"><span>캡션 바탕색</span><span class="cp-val" data-capval="' + p.id + '">' +
      (p.capBg ? p.capBg.toUpperCase() : "기본") + "</span></div>" + sw +
      '<div class="cp-foot"><label class="cp-pick"><input type="color" class="js-cap" data-id="' + p.id + '" value="' + capBg(p) + '"><span>컬러</span></label>' +
      '<button class="cp-reset' + (p.capBg ? "" : " on") + '" data-act="pickCap" data-id="' + p.id + '" data-color="">기본</button></div>' +
      '<p class="cp-note">글씨는 어느 색을 골라도 검정으로 유지돼요. 고른 색은 앱을 다시 열어도 그대로 남아 있어요.</p></div>' +
      '<div style="height:6px"></div>';
    return html;
  }

  function photoShow(id) {
    var p = S.photos.filter(function (x) { return x.id === id; })[0];
    if (!p) return false;
    var ids = photoDayIds(p);
    var i = ids.indexOf(p.id);
    photoView = { ids: ids, i: i < 0 ? 0 : i };
    return true;
  }

  function photoStep(step) {
    if (!photoView) return;
    var n = photoView.i + step;
    if (n < 0 || n >= photoView.ids.length) return;
    photoView.i = n;
    var st = sheet.scrollTop;
    sheet.innerHTML = '<div class="grab"></div>' + photoViewBody();
    sheet.scrollTop = st;
  }

  function openPhoto(id) {
    if (!photoShow(id)) return;
    openSheet(photoViewBody(), null);
  }

  function setCapColor(id, color) {
    var p = S.photos.filter(function (x) { return x.id === id; })[0];
    if (!p) return;
    var v = String(color || "").trim();
    if (v && !/^#[0-9a-fA-F]{6}$/.test(v)) return;
    p.capBg = v ? v.toUpperCase() : null;
    save();
    var bg = capBg(p);
    document.querySelectorAll('.pd-cap[data-capid="' + id + '"], .ph .cap[data-capid="' + id + '"]').forEach(function (el) {
      el.style.background = bg;
    });
    var val = document.querySelector('.cp-val[data-capval="' + id + '"]');
    if (val) val.textContent = p.capBg ? p.capBg.toUpperCase() : "기본";
    var row = document.querySelector('.sw-grid[data-sw="cap"]');
    if (row) row.querySelectorAll(".sw").forEach(function (b) {
      b.classList.toggle("sel", (b.getAttribute("data-color") || "") === (p.capBg || ""));
    });
    var rb = document.querySelector('.cp-reset[data-act="pickCap"]');
    if (rb) rb.classList.toggle("on", !p.capBg);
    var inp = document.querySelector('.js-cap[data-id="' + id + '"]');
    if (inp && inp.value.toUpperCase() !== bg) inp.value = bg;
    if (current === "photo" && !document.querySelector('.ph .cap[data-capid="' + id + '"]')) renderPhoto();
  }

  /* ------------------------------------------------------------------ photo upload */
  function defaultAlbum() {
    var d = parse(today);
    return (d.getMonth() + 1) + "월의 순간";
  }
  function fmtBytes(n) {
    if (!n) return "";
    return n >= 1024 * 1024 ? (n / 1024 / 1024).toFixed(1) + "MB" : Math.max(1, Math.round(n / 1024)) + "KB";
  }
  function lastAlbum() {
    var sorted = S.photos.slice().sort(byDateDesc);
    return sorted.length ? sorted[0].album : "";
  }
  function albumDatalist() {
    var names = [];
    S.photos.forEach(function (p) { if (p.album && names.indexOf(p.album) < 0) names.push(p.album); });
    return names.map(function (n) { return '<option value="' + esc(n) + '"></option>'; }).join("");
  }
  function fileTitle(name) {
    var base = String(name || "").replace(/\.[a-z0-9]+$/i, "").trim();
    if (!base) return "";
    if (/^(img|image|photo|dsc|dscn|kakao|screenshot|스크린샷|unnamed)[\s_-]*\d*$/i.test(base)) return "";
    if (/^\d+$/.test(base)) return "";
    return base.slice(0, 30);
  }

  function formAddPhoto(files) {
    pendingFiles = files || [];
    var total = 0;
    pendingFiles.forEach(function (f) { total += f.size || 0; });
    var rows = pendingFiles.map(function (f) {
      var url = "";
      try { url = URL.createObjectURL(f); pendingUrls.push(url); } catch (e) {}
      return '<div class="up-item">' + (url ? '<img class="up-thumb" src="' + url + '" alt="">' : '<div class="up-thumb"></div>') +
        '<div class="up-name">' + esc(f.name || "사진") + "</div>" +
        '<div class="up-size">' + fmtBytes(f.size) + "</div></div>";
    }).join("");
    return sheetHead("사진 추가") +
      '<p class="sheet-sub">' + pendingFiles.length + "장 · " + fmtBytes(total) + " · 긴 변 1800px 로 줄여서 보관해요.</p>" +
      '<form class="form" id="sheetForm" data-form="photo">' +
      '<div class="f"><label>앨범</label><input class="field" name="album" list="albumList" value="' + esc(lastAlbum() || defaultAlbum()) + '" placeholder="예) 성수, 늦가을" required autocomplete="off">' +
      '<datalist id="albumList">' + albumDatalist() + "</datalist></div>" +
      '<div class="f"><label>날짜</label><input class="field" type="date" name="date" value="' + today + '" required></div>' +
      '<div class="f"><label>캡션</label><input class="field" name="title" placeholder="비워 두면 한 장씩 나중에 적을 수 있어요" autocomplete="off"></div>' +
      '<div class="up-list">' + rows + "</div>" +
      '<div class="up-bar" id="upBar"><i></i></div>' +
      '<button class="btn-primary" type="submit">' + pendingFiles.length + "장 담기</button></form>" +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">취소</button>';
  }

  function addPhotoFiles(files, meta) {
    var total = files.length, done = 0, failed = 0;
    var bar = document.querySelector("#upBar i");
    var btn = sheet.querySelector(".btn-primary");
    if (btn) { btn.disabled = true; btn.textContent = "담는 중…"; }
    var setBar = function () { if (bar) bar.style.width = Math.round((done + failed) / total * 100) + "%"; };
    var chain = Promise.resolve();
    files.forEach(function (f) {
      chain = chain.then(function () {
        return Store.photos.add(f, { album: meta.album, date: meta.date, title: meta.title }).then(function (res) {
          var rec = res.photo;
          rec.title = String(rec.title || meta.title || fileTitle(f.name) || "").trim();
          if (res.url) PHOTO_URLS[rec.id] = res.url;
          S.photos.unshift(rec);
          done++;
          setBar();
          save();
        }).catch(function (e) {
          failed++;
          setBar();
          console.warn("[투로그] photo add failed", e);
        });
      });
    });
    return chain.then(function () {
      closeSheet();
      if (current === "photo") renderPhoto();
      if (failed === 0) toast(done + "장을 담았어요");
      else if (done === 0) toast("사진을 담지 못했어요. 다른 사진으로 해 보세요");
      else toast(done + "장 담았어요 · " + failed + "장은 실패");
    });
  }

  function formEditPhoto(p) {
    return sheetHead("사진 정보") +
      '<form class="form" id="sheetForm" data-form="photoEdit">' +
      '<div class="f"><label>캡션</label><input class="field" name="title" value="' + esc(p.title || "") + '" placeholder="예) 골목 산책" autocomplete="off">' +
      '<div class="cap-preview" style="background:' + capBg(p) + '">' + esc(p.title || "캡션 미리보기") + "</div></div>" +
      '<div class="f"><label>앨범</label><input class="field" name="album" list="albumList" value="' + esc(p.album || "") + '" required autocomplete="off">' +
      '<datalist id="albumList">' + albumDatalist() + "</datalist></div>" +
      '<div class="two"><div class="f"><label>날짜</label><input class="field" type="date" name="date" value="' + p.date + '"></div>' +
      '<div class="f"><label>장소</label><input class="field" name="place" value="' + esc(p.place || "") + '" placeholder="선택" autocomplete="off"></div></div>' +
      '<div class="f"><label>메모</label><textarea class="field" name="memo" rows="3">' + esc(p.memo || "") + "</textarea></div>" +
      '<button class="btn-primary" type="submit">저장하기</button></form>' +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
  }

  /* ------------------------------------------------------------------ settings */
  function initials(n) { return esc(String(n || "?").slice(0, 1)); }

  /* --------------------------------------------------- 프로필 사진 (동그란 아바타)
     작은 JPEG dataURL 로 만들어 상태(couple.pics)에 함께 저장합니다. */
  /* v26: 두 사람이 연결된 뒤에는 **자기 사진만** 바꿀 수 있습니다.
     (상대 사진은 상대 폰에서 바꾸면 settings 를 통해 이 폰에도 나타나요) */
  function canEditAvatar(who) {
    if (!Store || Store.mode !== "remote") return true;      // 이 기기 혼자 쓰는 모드
    var n = 1;
    try { n = Store.couple.memberCount(); } catch (e) { n = 1; }
    if (!(n >= 2)) return true;                               // 아직 연결 전 — 두 사람 다 꾸밀 수 있음
    return who !== "you";
  }
  function setAvatarPic(who, url) {
    S.couple.pics = S.couple.pics || {};
    if (url) S.couple.pics[who] = url;
    else delete S.couple.pics[who];
    if (Store && Store.mode === "remote" && Store.avatar) {
      Store.avatar.set(who, url || "").catch(function () {});
    }
    save();
    renderAll();
    if (personSheetWho) openPersonSheet(personSheetWho);
  }
  function avPic(who) {
    var p = (S.couple.pics || {})[who];
    return typeof p === "string" && p.indexOf("data:image/") === 0 ? p : "";
  }
  function avInner(who) {
    var pic = avPic(who);
    /* 사진이 없으면 글자 없이 색만 있는 빈 동그라미로 보여 줍니다 */
    if (pic) return '<img class="av-img" src="' + pic + '" alt="">';
    return "";
  }
  function avSpan(who, extra) {
    var nm = who === "me" ? S.couple.me : S.couple.you;
    return '<span class="av ' + who + (avPic(who) ? " pic" : "") + (extra ? " " + extra : "") +
      '" aria-label="' + esc(nm) + '">' + avInner(who) + "</span>";
  }
  /* 고른 사진을 가운데 기준으로 정사각형 256px JPEG 로 줄입니다
     (v27: 프로필 사진은 동그라미 가이드 크롭 화면(openAvatarCrop)을 거쳐 저장합니다) */
  function squareAvatar(file) {
    return new Promise(function (resolve, reject) {
      if (!file) return reject(new Error("no file"));
      var reader = new FileReader();
      reader.onerror = function () { reject(new Error("read")); };
      reader.onload = function () {
        var img = new Image();
        img.onerror = function () { reject(new Error("decode")); };
        img.onload = function () {
          try {
            var SIDE = 256;
            var iw = img.naturalWidth || img.width || 0;
            var ih = img.naturalHeight || img.height || 0;
            if (!iw || !ih) { reject(new Error("empty image")); return; }
            var cv = document.createElement("canvas");
            cv.width = SIDE; cv.height = SIDE;
            var ctx = cv.getContext("2d");
            var m = Math.min(iw, ih);
            var sx = Math.floor((iw - m) / 2), sy = Math.floor((ih - m) / 2);
            ctx.imageSmoothingEnabled = true;
            ctx.imageSmoothingQuality = "high";
            ctx.drawImage(img, sx, sy, m, m, 0, 0, SIDE, SIDE);
            var url = cv.toDataURL("image/jpeg", 0.82);
            if (url.length > 180000) url = cv.toDataURL("image/jpeg", 0.62);
            if (url.length > 180000) url = cv.toDataURL("image/jpeg", 0.45);
            resolve(url);
          } catch (e) { reject(e); }
        };
        img.src = String(reader.result || "");
      };
      reader.readAsDataURL(file);
    });
  }
  var personSheetWho = null;
  /* ==========================================================================
     v27: 프로필 사진 — 카카오톡 프사처럼 동그라미 가이드 안에서 옮기고 키워 자르기
     · 어두운 화면 가운데 밝은 동그라미 안에서 손가락(마우스)으로 옮기고
       두 손가락(또는 아래 슬라이더)으로 확대·축소
     · 「적용」을 누르면 동그라미에 맞춘 정사각 256×256 JPEG 로 잘라 저장·동기화
     ========================================================================== */
  var AV_SIDE = 256;
  var avCrop = null;

  function avCropEl() { return document.getElementById("avCrop"); }
  function closeAvatarCrop() {
    var el = avCropEl();
    if (el && el.parentNode) el.parentNode.removeChild(el);
    avCrop = null;
  }
  function avClamp() {
    if (!avCrop) return;
    var st = avCrop;
    var halfW = st.iw * st.base * st.zoom / 2;
    var halfH = st.ih * st.base * st.zoom / 2;
    var mx = Math.max(0, halfW - st.box / 2);
    var my = Math.max(0, halfH - st.box / 2);
    st.tx = Math.min(mx, Math.max(-mx, st.tx));
    st.ty = Math.min(my, Math.max(-my, st.ty));
  }
  function avDraw() {
    if (!avCrop) return;
    avClamp();
    var st = avCrop;
    var img = document.getElementById("avcImg");
    if (img) {
      img.style.width = (st.iw * st.base) + "px";
      img.style.height = (st.ih * st.base) + "px";
      img.style.transform = "translate(calc(-50% + " + st.tx + "px), calc(-50% + " + st.ty + "px)) scale(" + st.zoom + ")";
    }
    var z = document.getElementById("avcZoom");
    if (z && Math.abs(Number(z.value) - st.zoom) > 0.002) z.value = String(st.zoom);
  }
  function showAvatarCrop(img, iw, ih, who) {
    closeAvatarCrop();
    var vw = window.innerWidth || 390, vh = window.innerHeight || 700;
    var box = Math.round(Math.min(300, Math.min(vw, vh) * 0.62));
    box = Math.max(190, box);
    avCrop = { who: who, img: img, iw: iw, ih: ih, box: box, base: box / Math.min(iw, ih), zoom: 1, tx: 0, ty: 0 };
    var wrap = document.createElement("div");
    wrap.className = "avcrop";
    wrap.id = "avCrop";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-label", "프로필 사진 맞추기");
    wrap.innerHTML =
      '<div class="avcrop-hd">동그라미 안에 맞춰 주세요</div>' +
      '<div class="avcrop-stage" id="avcStage" style="width:' + box + 'px;height:' + box + 'px">' +
      '<img class="avc-img" id="avcImg" alt="" src="' + img.src + '"></div>' +
      '<div class="avcrop-zoom"><span aria-hidden="true">−</span>' +
      '<input id="avcZoom" type="range" min="1" max="3" step="0.01" value="1" aria-label="확대·축소">' +
      '<span aria-hidden="true">+</span></div>' +
      '<div class="avcrop-btns"><button type="button" class="avcrop-btn" id="avcCancel">취소</button>' +
      '<button type="button" class="avcrop-btn on" id="avcApply">적용</button></div>';
    (document.getElementById("phone") || document.body).appendChild(wrap);
    avDraw();

    var stage = document.getElementById("avcStage");
    var pts = {}, last = null;
    function list() { return Object.keys(pts).map(function (k) { return pts[k]; }); }
    function reset() { last = null; }
    stage.addEventListener("pointerdown", function (e) {
      pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      try { stage.setPointerCapture(e.pointerId); } catch (err) {}
      reset();
      if (e.preventDefault) e.preventDefault();
    });
    stage.addEventListener("pointermove", function (e) {
      if (!avCrop || !pts[e.pointerId]) return;
      pts[e.pointerId] = { x: e.clientX, y: e.clientY };
      var ps = list();
      if (ps.length === 1) {
        if (!last || last.n !== 1) { last = { n: 1, x: e.clientX, y: e.clientY }; return; }
        avCrop.tx += e.clientX - last.x;
        avCrop.ty += e.clientY - last.y;
        last = { n: 1, x: e.clientX, y: e.clientY };
        avDraw();
      } else if (ps.length >= 2) {
        var a = ps[0], b = ps[1];
        var dist = Math.sqrt(Math.pow(a.x - b.x, 2) + Math.pow(a.y - b.y, 2)) || 1;
        var mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        if (!last || last.n !== 2) { last = { n: 2, dist: dist, x: mx, y: my }; return; }
        avCrop.zoom = Math.min(3, Math.max(1, avCrop.zoom * (dist / last.dist)));
        avCrop.tx += mx - last.x;
        avCrop.ty += my - last.y;
        last = { n: 2, dist: dist, x: mx, y: my };
        avDraw();
      }
      if (e.preventDefault) e.preventDefault();
    });
    function done(e) { delete pts[e.pointerId]; reset(); }
    stage.addEventListener("pointerup", done);
    stage.addEventListener("pointercancel", done);
    stage.addEventListener("pointerleave", done);
    wrap.addEventListener("wheel", function (e) {
      if (!avCrop) return;
      if (e.preventDefault) e.preventDefault();
      avCrop.zoom = Math.min(3, Math.max(1, avCrop.zoom - e.deltaY * 0.0015));
      avDraw();
    }, { passive: false });
    var zoomIn = document.getElementById("avcZoom");
    if (zoomIn) zoomIn.addEventListener("input", function () {
      if (!avCrop) return;
      avCrop.zoom = Math.min(3, Math.max(1, Number(zoomIn.value) || 1));
      avDraw();
    });
    document.getElementById("avcCancel").addEventListener("click", function () { closeAvatarCrop(); });
    document.getElementById("avcApply").addEventListener("click", function () {
      if (!avCrop) return;
      var applyWho = avCrop.who;
      var url = "";
      try { url = avatarCropUrl(); } catch (e) { url = ""; }
      if (!url) { toast("사진을 자르지 못했어요. 다른 사진으로 해볼까요?"); return; }
      closeAvatarCrop();
      setAvatarPic(applyWho, url);
      toast(applyWho === "me" ? "내 프로필 사진을 바꿨어요" : "프로필 사진을 바꿨어요");
    });
  }
  /* 동그라미 가이드에 보이는 부분을 정사각 256px JPEG 로 */
  function avatarCropUrl() {
    var st = avCrop;
    if (!st || !st.img) return "";
    var per = 1 / (st.base * st.zoom);        // 화면 1px = 원본 몇 px
    var half = (st.box / 2) * per;
    var size = Math.max(1, Math.min(half * 2, Math.min(st.iw, st.ih)));
    var cx = st.iw / 2 - st.tx * per;
    var cy = st.ih / 2 - st.ty * per;
    var sx = Math.min(Math.max(0, cx - size / 2), Math.max(0, st.iw - size));
    var sy = Math.min(Math.max(0, cy - size / 2), Math.max(0, st.ih - size));
    var cv = document.createElement("canvas");
    cv.width = AV_SIDE; cv.height = AV_SIDE;
    var ctx = cv.getContext("2d");
    ctx.fillStyle = "#FFFFFF";
    ctx.fillRect(0, 0, AV_SIDE, AV_SIDE);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(st.img, sx, sy, size, size, 0, 0, AV_SIDE, AV_SIDE);
    var url = cv.toDataURL("image/jpeg", 0.82);
    if (url.length > 180000) url = cv.toDataURL("image/jpeg", 0.62);
    if (url.length > 180000) url = cv.toDataURL("image/jpeg", 0.45);
    return url;
  }
  function openAvatarCrop(file, who) {
    if (!file) return;
    var reader = new FileReader();
    reader.onerror = function () { toast("사진을 불러오지 못했어요"); };
    reader.onload = function () {
      var img = new Image();
      img.onerror = function () { toast("사진을 불러오지 못했어요. 다른 사진으로 해볼까요?"); };
      img.onload = function () {
        var iw = img.naturalWidth || img.width || 0;
        var ih = img.naturalHeight || img.height || 0;
        if (!iw || !ih) { toast("사진을 불러오지 못했어요"); return; }
        showAvatarCrop(img, iw, ih, who);
      };
      img.src = String(reader.result || "");
    };
    reader.readAsDataURL(file);
  }
  /* 노트 카드 상세 시트가 열려 있을 때 어느 카드인지 */
  var openCard = null;

  function formPerson(who) {
    var isMe = who === "me";
    var nm = isMe ? S.couple.me : S.couple.you;
    var pic = avPic(who);
    var linked = !!(S.link && S.link.connected);
    var canPic = canEditAvatar(who);
    var h = sheetHead(isMe ? "내 프로필" : esc(nm) + " 설정");
    /* v27: 프로필 사진(＋ 배지 · 누르면 사진첩) 바로 옆에 「닉네임」 한 칸 —
       글씨 버튼(사진첩 선택·사진 지우기)은 없애고, 지우기는 사진 위 작은 × 로만. */
    h += '<form class="form" id="personForm" data-who="' + who + '" style="margin-top:2px">' +
      '<div class="pr-top">' +
      '<div class="pr-avbtn' + (canPic ? "" : " locked") + '"' +
      (canPic ? ' data-act="pickPic" data-who="' + who + '" role="button" tabindex="0"' : "") +
      ' aria-label="' + esc(nm) + ' 프로필 사진 바꾸기">' +
      '<span class="pr-av' + (pic ? " pic" : "") + '" style="background:' + avColor(who) + '">' + avInner(who) + "</span>" +
      (canPic ? '<span class="pr-plus" aria-hidden="true">+</span>' : "") +
      (canPic && pic ? '<button type="button" class="pr-del" data-act="clearPic" data-who="' + who + '" aria-label="프로필 사진 지우기">×</button>' : "") +
      "</div>" +
      '<div class="pr-nm"><label class="pr-lbl" for="personName">닉네임</label>' +
      '<input class="field" id="personName" name="name" value="' + esc(nm) + '" placeholder="닉네임" required autocomplete="off"></div>' +
      "</div>" +
      (canPic ? "" : '<div class="set-hint" style="margin-top:10px;padding:0">프로필 사진은 ' + esc(nm) + " 본인 폰에서 바꿀 수 있어요.</div>") +
      '<button class="btn-primary" type="submit" style="margin-top:18px">저장</button></form>';
    h += '<div class="pr-color"><span class="set-lbl">컬러</span>' + prColorRow(who) + "</div>";
    if (!isMe) {
      /* 상대 카드: 연결 끊기 · 재연결 */
      h += '<div class="pr-link">' +
        '<div class="pr-link-hd">' + (linked ? "커플 연결됨" : "아직 연결되지 않았어요") + "</div>" +
        (linked
          ? '<button type="button" class="set-btn ghost" data-act="linkSheet" style="width:100%">재연결 · 초대코드 다시 넣기</button>' +
            '<button type="button" class="set-btn warn" data-act="unlink" style="width:100%;margin-top:8px">연결 끊기</button>'
          : '<button type="button" class="set-btn" data-act="linkSheet" style="width:100%">연결하기 · 초대코드 넣기</button>') +
        "</div>";
    }
    h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
    return h;
  }
  function openPersonSheet(who) {
    openSheet(formPerson(who));
    personSheetWho = who;
  }

  function avatarPickRow(who) {
    var nm = who === "me" ? S.couple.me : S.couple.you;
    var has = !!avPic(who);
    var canPic = canEditAvatar(who);
    return '<div class="av-line">' +
      '<button type="button" class="set-av pick' + (has ? " pic" : "") + '" data-act="pickPic" data-who="' + who +
      '" style="background:' + avColor(who) + '" aria-label="' + esc(nm) + ' 프로필 사진 선택">' + avInner(who) + "</button>" +
      '<span class="av-nm">' + esc(nm) + "</span>" +
      (canPic
        ? '<span class="av-acts"><button type="button" class="set-btn" data-act="pickPic" data-who="' + who + '">' +
          (has ? "사진 바꾸기" : "사진 선택") + "</button>" +
          (has ? '<button type="button" class="set-btn ghost" data-act="clearPic" data-who="' + who + '">기본으로</button>' : "") + "</span>"
        : '<span class="av-acts"><span class="set-hint" style="margin:0">본인 폰에서 바꿔요</span></span>') +
      "</div>";
  }
  function avColor(who) {
    var c = (S.couple.colors || {})[who];
    return c || (who === "me" ? "#D96B52" : "#5F6F65");
  }
  function codeFmt(code) {
    var s = String(code || "").replace(/\D/g, "");
    return s.length === 6 ? s.slice(0, 3) + " " + s.slice(3) : s;
  }
  function copyText(txt, msg) {
    var ok = function () { toast(msg || "복사했어요"); };
    var no = function () { toast("복사하지 못했어요. 코드를 길게 눌러 복사해 주세요"); };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(ok).catch(no);
        return;
      }
    } catch (e) {}
    try {
      var ta = document.createElement("textarea");
      ta.value = txt; ta.setAttribute("readonly", "");
      ta.style.position = "fixed"; ta.style.top = "-1000px"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select(); ta.setSelectionRange(0, txt.length);
      var done = document.execCommand("copy");
      document.body.removeChild(ta);
      done ? ok() : no();
    } catch (e) { no(); }
  }
  function avatarPick(who, name) {
    var cur = avColor(who);
    var h = '<div class="av-line"><span class="set-av sm' + (avPic(who) ? " pic" : "") + '" style="background:' + cur + '">' + avInner(who) + "</span>" +
      '<span class="av-nm">' + esc(name) + "</span></div>";
    h += '<div class="sw-grid" data-av="' + who + '" style="margin-top:10px">';
    SOFT.forEach(function (p) {
      h += '<button class="sw' + (p.c === cur ? " sel" : "") + '" data-act="pickAvatar" data-who="' + who +
        '" data-color="' + p.c + '" style="background:' + p.c + '" aria-label="' + p.n + " " + p.c + '"></button>';
    });
    return h + "</div>";
  }
  function schedPick(who) {
    var cur = sched(who);
    var h = '<div class="av-line"><span class="av-nm">' + esc(schedName(who)) + "</span>" +
      '<span class="av-chip" style="background:' + cur + '"></span></div>';
    h += '<div class="sw-grid" data-sched="' + who + '" style="margin-top:10px">';
    SOFT.forEach(function (p) {
      h += '<button class="sw' + (p.c === cur ? " sel" : "") + '" data-act="pickSched" data-who="' + who +
        '" data-color="' + p.c + '" style="background:' + p.c + '" aria-label="' + p.n + " " + p.c + '"></button>';
    });
    return h + "</div>";
  }

  function myInviteCode() {
    if (Store && Store.mode === "remote") return Store.couple.myCode() || (S.link || {}).code || "";
    return (S.link || {}).code || "";
  }
  function syncStateLabel() {
    if (!Store) return "불러오는 중";
    if (Store.mode !== "remote") return "이 기기에 저장 중";
    var st = (Store.status || {}).state;
    if (st === "offline") return "오프라인 · 다시 연결하는 중";
    return "두 대 실시간 동기화 중";
  }

  /* ---- My (설정) 화면 ---- */

  /* 페이지 캡션 색: 다섯 페이지에 한 번에 쓰는 하나의 색 */
  function capPickAll() {
    var cur = String((S.theme || {}).cap || "").toUpperCase();
    var h = '<div class="cap-all"><div class="cap-sws">';
    h += '<button type="button" class="sw none' + (!cur ? " sel" : "") + '" data-act="pickCapAll" data-color="" aria-label="캡션 색 기본"></button>';
    CAP_BG.forEach(function (c) {
      h += '<button type="button" class="sw' + (cur === c.toUpperCase() ? " sel" : "") + '" data-act="pickCapAll" data-color="' + c +
        '" style="background:' + c + '" aria-label="캡션 ' + c + '"></button>';
    });
    h += '</div><input type="color" class="cap-pick js-capall" value="' + (cur || "#FFFFFF") + '" aria-label="캡션 컬러"></div>';
    return h;
  }

  function setCapAll(color) {
    var v = String(color || "").trim();
    if (v && !/^#[0-9a-fA-F]{6}$/.test(v)) return;
    S.theme = S.theme || {};
    if (v) S.theme.cap = v.toUpperCase(); else delete S.theme.cap;
    S.theme.pages = {};                    /* 예전 페이지별 설정은 한 색으로 합칩니다 */
    save();
    var val = v ? v.toUpperCase() : "";
    document.querySelectorAll("[data-pg]").forEach(function (el) {
      el.classList.toggle("cap-tint", !!val);
      if (val) el.style.setProperty("--cap", val); else el.style.removeProperty("--cap");
    });
    document.querySelectorAll(".cap-all .sw").forEach(function (b) {
      b.classList.toggle("sel", String(b.getAttribute("data-color") || "").toUpperCase() === val);
    });
    var inp = document.querySelector(".js-capall");
    if (inp && val) inp.value = val;
  }

  function fontRows() {
    var cur = fontOf((S.theme || {}).font).k;
    return FONTS.map(function (f) {
      return '<button type="button" class="font-row' + (f.k === cur ? " on" : "") + '" data-act="pickFont" data-font="' + f.k + '">' +
        '<span class="fn" style="font-family:' + f.s + '">' + esc(f.n) + "</span>" +
        '<span class="fx" style="font-family:' + f.s + '">우리의 기록 Aa</span>' +
        '<span class="fk">' + (f.k === cur ? "✓" : "") + "</span></button>";
    }).join("");
  }

  var NOTIFS = [
    { k: "anni", n: "기념일 알림", d: "생일과 기념일 하루 전에 알려드려요" },
    { k: "today", n: "오늘의 일정 알림", d: "그날 아침, 오늘 일정을 모아 알려드려요" },
    { k: "dday", n: "D-Day 리마인드", d: "매달 같은 날, 함께한 날을 세어 알려드려요" }
  ];
  function notifOn(k) {
    var n = S.notif || {};
    return typeof n[k] === "boolean" ? n[k] : k !== "dday";
  }
  function notifRows() {
    return NOTIFS.map(function (n) {
      var on = notifOn(n.k);
      return '<button type="button" class="row tap notif" data-act="toggleNotif" data-key="' + n.k + '" aria-pressed="' + (on ? "true" : "false") + '">' +
        '<div class="body"><div class="t">' + esc(n.n) + "</div><div class=\"m\">" + esc(n.d) + "</div></div>" +
        '<span class="tgl' + (on ? " on" : "") + '"><i></i></span></button>';
    }).join("");
  }
  function notifSummary() {
    var on = NOTIFS.filter(function (n) { return notifOn(n.k); });
    return on.length ? on.length + "개 켜짐 · " + on.map(function (n) { return n.n.replace(" 알림", ""); }).join(" · ") : "모두 꺼짐";
  }

  /* My 탭의 메뉴 줄 (누르면 안으로 들어가기) */
  function menuRow(act, icon, title, sub) {
    return '<button type="button" class="menu-row" data-act="' + act + '">' +
      '<span class="mi" aria-hidden="true">' + icon + "</span>" +
      '<span class="mb"><span class="mt">' + esc(title) + '</span><span class="ms">' + esc(sub) + "</span></span>" +
      '<span class="mc" aria-hidden="true">›</span></button>';
  }
  function themeSummary() {
    var t = S.theme || {};
    var parts = [t.mode === "dark" ? "다크" : "라이트", fontOf(t.font).n];
    if (t.cap) parts.push("캡션 색");
    if (t.homeTitleBg) parts.push("홈 제목 색");
    return parts.join(" · ");
  }

  /* 테마 관리 — 화면·캡션 색·일정 색·홈 제목 색·폰트를 한 곳에서 */
  function themeManagerHtml() {
    var t = S.theme || {}, dark = t.mode === "dark";
    var h = sheetHead("테마 관리");
    h += '<div class="cp"><div class="cp-hd"><span>화면</span><span class="cp-val">' + (dark ? "다크" : "라이트") + '</span></div>' +
      '<div class="seg seg-sm" data-group="mode">' +
      '<button type="button" class="seg-btn' + (dark ? "" : " active") + '" data-act="mode" data-mode="light">라이트</button>' +
      '<button type="button" class="seg-btn' + (dark ? " active" : "") + '" data-act="mode" data-mode="dark">다크</button>' +
      "</div></div>";
    h += '<div class="cp"><div class="cp-hd"><span>페이지 캡션 색</span><span class="cp-val">' +
      (String(t.cap || "").toUpperCase() || "기본") + "</span></div>" + capPickAll() +
      '<p class="cp-note" style="margin-top:10px">홈·노트·사진첩·My 제목 줄에 한 번에 적용돼요. 글씨는 늘 검정으로 또렷하게 보여요.</p></div>';
    h += '<div class="cp"><div class="cp-hd"><span>일정 색</span><span class="cp-val">소영 · 준영 · 공동</span></div>' +
      colorPickRow("me") + colorPickRow("you") + colorPickRow("both") + "</div>";
    /* v23: 「{월}월의 우리」 섹션이 홈에서 사라져 색 이름도 「다가오는 일정」 하나로 */
    h += '<div class="cp"><div class="cp-hd"><span>홈 제목 색</span><span class="cp-val">뮤트 톤</span></div>' +
      cpBlock("다가오는 일정", "homeTitleBg", t.homeTitleBg, MUTED, "#F2CFC9") +
      '<p class="cp-note" style="margin-top:10px">제목 줄과 저장·완료 버튼에 같은 색이 칠해져요. 일정 목록은 흰 바탕으로 남아요.</p></div>';
    h += '<div class="cp"><div class="cp-hd"><span>폰트</span><span class="cp-val">' + esc(fontOf(t.font).n) + '</span></div>' +
      '<div class="font-list">' + fontRows() + "</div></div>";
    h += '<div style="height:16px"></div><button class="btn-primary" data-close="1">완료</button>';
    return h;
  }

  function notifSheetHtml() {
    return sheetHead("알림 설정") +
      '<p class="sheet-sub">필요한 알림만 골라서 켜 두세요.</p>' +
      '<div class="list" style="margin:0">' + notifRows() + "</div>" +
      '<p class="cp-note">알림 설정은 이 기기에 저장돼요. 브라우저 알림을 허용해 두면 그대로 이어서 써요.</p>' +
      '<button class="btn-primary" data-close="1">완료</button>';
  }

  function askNotifyPermission(cb) {
    try {
      if (typeof Notification === "undefined") { cb(false); return; }
      if (Notification.permission === "granted") { cb(true); return; }
      if (Notification.permission === "denied") { cb(false); return; }
      var res = Notification.requestPermission(function (r) { cb(r === "granted"); });
      if (res && typeof res.then === "function") res.then(function (r) { cb(r === "granted"); });
    } catch (e) { cb(false); }
  }

  /* v27: 노트 카드 묶음 복구 결과 — My 탭 「폰에 있던 기록」 카드 안에 한 줄 */
  function repairedHint() {
    var rep = null;
    try { rep = Store && Store.groupsRepaired ? Store.groupsRepaired() : null; } catch (e) { rep = null; }
    if (!rep) return "";
    var c = rep.groups || {};
    var bits = [];
    if (c.todo) bits.push("메모 " + c.todo + "개");
    if (c.bucket) bits.push("버킷 " + c.bucket + "개");
    if (c.log) bits.push("영화·먹방 " + c.log + "개");
    return '<div class="set-hint" style="margin-top:8px">노트 카드를 되살렸어요' +
      (bits.length ? " · " + bits.join(" · ") : "") + "</div>";
  }

  function renderSet() {
    var c = S.couple, t = S.theme || {}, li = S.link || {}, dark = t.mode === "dark";
    var remote = !!(Store && Store.mode === "remote");
    var acct = (S.auth || {});
    var h = '<header class="hdr' + capCls("set") + '"' + capStyle("set") + ' data-pg="set"><div><h1>My</h1></div>' +
      '<span class="app-ver" title="투로그 버전">버전 ' + APP_VERSION + "</span></header>";

    /* ---- 1. 계정 및 커플 연결 ---- */
    h += '<div class="sec"><h2>계정 및 커플 연결</h2><span class="more">' + (li.connected ? "연결됨" : "미연결") + "</span></div>";
    h += '<div class="list">';
    /* 내 줄 — 프로필 사진은 언제나 내가 바꿀 수 있어요 */
    h += '<div class="row tap" data-act="personSheet" data-who="me"><button type="button" class="set-av pick' + (avPic("me") ? " pic" : "") + '" data-act="pickPic" data-who="me" style="background:' + avColor("me") + '" aria-label="' + esc(c.me) + ' 프로필 사진 선택">' + avInner("me") + "</button>" +
      '<div class="body" style="flex:1 1 auto;min-width:0"><div class="t set-who-nm">' + esc(c.me) + "</div>" +
      '<div style="font-size:11px;color:var(--ink-3);margin-top:2px">' + (remote && acct.email ? esc(acct.email) : "내 계정 · 로그인됨") + "</div></div>" +
      '<span class="chip plain">나</span></div>';
    /* 상대 줄 — v26: 두 사람이 연결된 뒤에는 상대 사진을 바꿀 수 없고, 상대 폰에서 바꿔요 */
    var youPicOn = canEditAvatar("you");
    h += '<div class="row tap" data-act="personSheet" data-who="you">' +
      (youPicOn
        ? '<button type="button" class="set-av pick' + (avPic("you") ? " pic" : "") + '" data-act="pickPic" data-who="you" style="background:' + avColor("you") + '" aria-label="' + esc(c.you) + ' 프로필 사진 선택">' + avInner("you") + "</button>"
        : '<span class="set-av' + (avPic("you") ? " pic" : "") + '" style="background:' + avColor("you") + '" aria-label="' + esc(c.you) + ' 프로필 사진">' + avInner("you") + "</span>") +
      '<div class="body" style="flex:1 1 auto;min-width:0"><div class="t set-who-nm">' + esc(c.you) + "</div>" +
      '<div style="font-size:11px;color:var(--ink-3);margin-top:2px">' + (li.connected ? (youPicOn ? "커플 연결됨 · 함께 기록 중" : "프로필 사진은 " + esc(c.you) + " 폰에서 바꿔요") : "초대 코드로 연결할 수 있어요") + "</div></div>" +
      '<button class="chip ' + (li.connected ? "coral" : "plain") + '" data-act="linkSheet" aria-label="커플 연결 설정">' + (li.connected ? "연결됨" : "미연결") + "</button></div>";
    h += "</div>";

    h += '<div class="set-card"><div class="set-lbl">동기화</div>' +
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px">' +
      '<div style="font-size:12.5px;font-weight:600;letter-spacing:-.01em">' + syncStateLabel() + "</div>" +
      '<span class="chip ' + (remote ? "sage" : "plain") + '">' + (remote ? "자동" : "로컬") + "</span></div>" +
      (remote
        ? '<div class="set-hint">한쪽에서 고치면 다른 쪽에 몇 초 안에 나타나요. 사진은 비공개 Storage 에 보관되고 서명된 주소로만 보여요.</div>' +
          '<button class="set-btn" data-act="syncNow" style="width:100%;margin-top:10px">지금 동기화</button>'
        : '<div class="set-hint">지금은 이 기기(인터넷 없어도 OK)에만 저장해요. Supabase 주소를 넣으면 두 사람이 실시간으로 함께 쓸 수 있어요. (README 참고)</div>') +
      "</div>";

    h += '<div style="margin:14px 20px 0"><button class="set-btn warn" data-act="logout" style="width:100%;height:46px">로그아웃</button></div>';
    /* ---- v26: 폰에 남아 있던 예전 로컬 기록 ---- */
    var locInfo = localReadyInfo();
    if (locInfo) {
      var mdone = null;
      try { mdone = Store.migrate && Store.migrate.done ? Store.migrate.done() : null; } catch (e) { mdone = null; }
      h += '<div class="set-card"><div class="set-lbl">폰에 있던 기록</div>' +
        '<div style="display:flex;align-items:center;justify-content:space-between;gap:10px;margin-top:10px">' +
        '<div style="font-size:12.5px;font-weight:600;letter-spacing:-.01em">' + esc(localSummaryLine(locInfo)) + "</div>" +
        '<span class="chip ' + (mdone ? "sage" : "plain") + '">' + (mdone ? "이어 옴" : "대기") + "</span></div>" +
        '<div class="set-hint">' + (mdone
          ? "이 기기의 예전 기록은 새 커플 공간으로 옮겨 두었어요. 원본은 이 폰에 그대로 남아 있고, 다시 가져와도 같은 기록은 겹치지 않아요."
          : "이 기기에만 저장해 둔 예전 기록이에요. 커플 공간이 비어 있으면 로그인할 때 자동으로 이어 오고, 그 밖에는 아래 버튼으로 더할 수 있어요.") + "</div>" +
        repairedHint() +
        '<button class="set-btn" data-act="importLocal" style="width:100%;margin-top:10px">폰에 있던 예전 기록 가져오기</button></div>';
    }

    /* ---- 2. 잠금 · 보관 (v18) ---- */
    h += '<div class="my-gap"></div>';
    h += '<div class="sec"><h2>잠금 · 보관</h2></div>' +
      '<div class="list">' +
      menuRow("lockSheet", "🔒", "화면 잠금", lockOn() ? "켜짐 · 4자리 비밀번호" : "꺼짐") +
      menuRow("exportSheet", "📄", "기록 PDF 내보내기", "이번 달 · 올해 · 전체") + "</div>";

    /* ---- 3. 꾸미기 ---- */
    h += '<div class="my-gap"></div>';
    h += '<div class="sec"><h2>꾸미기</h2></div>';
    h += '<div class="list">' + menuRow("openThemeManager", "🎨", "테마 관리", themeSummary()) + "</div>";

    /* ---- 3. 알림 설정 ---- */
    h += '<div class="my-gap"></div>';
    h += '<div class="sec"><h2>알림 설정</h2></div>';
    h += '<div class="list">' + menuRow("openNotifSheet", "🔔", "알림 설정", notifSummary()) + "</div>";
    h += '<div class="set-hint" style="margin:10px 20px 0">알림 설정은 이 기기에 저장돼요. 브라우저 알림을 허용해 두면 다음 업데이트에서 그대로 이어서 쓸 수 있어요.</div>';

    h += '<div style="height:26px"></div>';
    h += '<p class="cp-note" style="text-align:center;padding:0 24px">' + installHint() + "</p>";
    h += '<div style="height:26px"></div>';
    $("#s-set").innerHTML = h;
  }

  /* ==========================================================================
     v18: My 탭 — 4자리 화면 잠금
     ========================================================================== */
  var lockBuf = "";
  var LOCK_KEY = "twolog:v1:lock";   /* 잠금은 이 기기에만 — 상대 기기로 PIN 이 넘어가지 않게 */
  function lockCfg() {
    try {
      var raw = localStorage.getItem(LOCK_KEY);
      var c = raw ? JSON.parse(raw) : null;
      if (c && typeof c === "object") return { on: !!c.on, pin: String(c.pin || "") };
    } catch (e) {}
    return { on: false, pin: "" };
  }
  function lockSave(cfg) {
    try { localStorage.setItem(LOCK_KEY, JSON.stringify({ on: !!cfg.on, pin: String(cfg.pin || "") })); } catch (e) {}
  }
  function lockOn() { var c = lockCfg(); return !!c.on && /^\d{4}$/.test(c.pin); }

  function showLock() {
    var el = $("#lockScreen");
    if (!el) return;
    lockBuf = "";
    el.hidden = false;
    el.setAttribute("aria-hidden", "false");
    renderLockScreen("");
  }
  function hideLock() {
    var el = $("#lockScreen");
    if (!el) return;
    el.hidden = true;
    el.setAttribute("aria-hidden", "true");
  }
  function renderLockScreen(msg) {
    var el = $("#lockScreen");
    if (!el) return;
    var dots = "";
    for (var i = 0; i < 4; i++) dots += '<span class="lk-dot' + (i < lockBuf.length ? " on" : "") + '"></span>';
    var keys = "";
    for (var n = 1; n <= 9; n++) keys += '<button type="button" class="lk-key" data-act="lockKey" data-k="' + n + '">' + n + "</button>";
    keys += '<button type="button" class="lk-key ghost" data-act="lockKey" data-k="clear">전체 삭제</button>' +
      '<button type="button" class="lk-key" data-act="lockKey" data-k="0">0</button>' +
      '<button type="button" class="lk-key ghost" data-act="lockKey" data-k="del">지우기</button>';
    var who = (S && S.couple && S.couple.me) ? S.couple.me + "님, " : "";
    el.innerHTML = '<div class="lk-body"><div class="mark"><i></i><i></i></div>' +
      '<div class="lk-title">투로그</div>' +
      '<p class="lk-sub">' + esc(who) + "4자리 비밀번호를 입력해 주세요</p>" +
      '<div class="lk-dots' + (msg === "wrong" ? " lk-shake" : "") + '">' + dots + "</div>" +
      '<div class="lk-msg">' + (msg === "wrong" ? "비밀번호가 달라요. 다시 입력해 주세요." : "") + "</div>" +
      '<div class="lk-pad">' + keys + "</div></div>";
  }
  function lockKey(k) {
    if (k === "del") lockBuf = lockBuf.slice(0, -1);
    else if (k === "clear") lockBuf = "";
    else if (/^\d$/.test(k) && lockBuf.length < 4) lockBuf += k;
    renderLockScreen("");
    if (lockBuf.length !== 4) return;
    if (lockBuf === lockCfg().pin) {
      lockBuf = "";
      hideLock();
      toast("다시 오셨네요");
    } else {
      lockBuf = "";
      renderLockScreen("wrong");
      try { if (navigator.vibrate) navigator.vibrate([12, 60, 12]); } catch (e) {}
    }
  }

  function formLock() {
    var on = lockOn();
    var h = sheetHead("화면 잠금");
    h += '<p class="sheet-sub">' + (on
      ? "지금 화면 잠금이 켜져 있어요. 앱을 열 때 4자리 숫자를 먼저 확인해요."
      : "앱을 열 때 4자리 숫자를 먼저 확인해요. 이 기기에서만 쓰는 간단한 잠금이에요.") + "</p>";
    h += '<form class="form" id="lockForm" style="margin-top:12px">';
    if (on) h += '<div class="f"><label>지금 비밀번호</label><input class="field" type="password" name="cur" inputmode="numeric" maxlength="4" autocomplete="off" placeholder="4자리"></div>';
    h += '<div class="f"><label>' + (on ? "새 비밀번호" : "4자리 비밀번호") + '</label><input class="field" type="password" name="pin" inputmode="numeric" maxlength="4" autocomplete="off" placeholder="4자리 숫자" required></div>' +
      '<div class="f"><label>한 번 더</label><input class="field" type="password" name="pin2" inputmode="numeric" maxlength="4" autocomplete="off" placeholder="같은 숫자" required></div>' +
      '<button class="btn-primary" type="submit">' + (on ? "비밀번호 바꾸기" : "잠금 켜기") + "</button></form>";
    if (on) {
      h += '<div style="height:10px"></div><button class="btn-line" data-act="lockOff">잠금 끄기</button>';
      h += '<button class="btn-line" data-act="lockForgot" style="margin-top:8px;color:var(--ink-3)">비밀번호를 잊었어요</button>';
    }
    h += '<p class="cp-note" style="margin-top:14px">비밀번호는 이 기기에만 저장돼요. 두 사람이 같이 쓰는 앱이라면 서로 아는 숫자로 정해 두는 게 좋아요.</p>';
    h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
    return h;
  }

  /* ==========================================================================
     v18: My 탭 — 기간을 골라 기록 PDF 내보내기 (인쇄 창 → PDF로 저장)
     ========================================================================== */
  function formExport() {
    var y = today.slice(0, 4), m = today.slice(5, 7);
    return sheetHead("기록 PDF 내보내기") +
      '<p class="sheet-sub">기간을 고르면 투로그 기록장 모양으로 정리해 인쇄 창을 열어요. 인쇄 창에서 ‘PDF로 저장’을 고르면 돼요.</p>' +
      '<div class="ex-list">' +
      '<button class="ex-btn" data-act="exportRun" data-scope="month"><b>이번 달</b><span>' + Number(m) + "월 · 일정과 사진" + "</span></button>" +
      '<button class="ex-btn" data-act="exportRun" data-scope="year"><b>올해</b><span>' + y + "년 · 1월부터 지금까지</span></button>" +
      '<button class="ex-btn" data-act="exportRun" data-scope="all"><b>전체 기록</b><span>함께한 날부터 지금까지</span></button>' +
      "</div>" +
      '<p class="cp-note" style="margin-top:14px">사진은 화면에 보이는 그대로 담겨요. 인쇄 창에서 ‘PDF로 저장’을 고르면 파일로 남길 수 있어요.</p>' +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
  }

  function inScope(dateStr, scope) {
    var d = String(dateStr || "").slice(0, 10);
    if (!d) return false;
    if (scope === "month") return d.slice(0, 7) === today.slice(0, 7);
    if (scope === "year") return d.slice(0, 4) === today.slice(0, 4);
    return true;
  }

  function buildPrint(scope) {
    var c = S.couple || {};
    var y = today.slice(0, 4), m = Number(today.slice(5, 7));
    var title = scope === "month" ? m + "월의 기록" : scope === "year" ? y + "년의 기록" : "우리의 기록";
    var dday = Math.max(0, diffDays(c.since, today));
    var evs = S.events.filter(function (e) { return inScope(evStart(e), scope); })
      .sort(function (a, b) { return a.date < b.date ? -1 : a.date > b.date ? 1 : byTimeAsc(a, b); });
    var phs = S.photos.filter(function (p) { return inScope(p.date, scope); }).slice().sort(byDateAsc);
    var logs = (S.logs || []).filter(function (x) { return inScope(x.date, scope); });
    var todos = S.todos || [];
    var buckets = S.bucket || [];

    var h = '<div class="pr-page"><div class="pr-head"><div class="pr-brand"><i></i><i></i><b>투로그</b></div>' +
      '<h1>' + esc(title) + "</h1>" +
      '<p class="pr-sub">' + esc(c.me || "") + " · " + esc(c.you || "") + " · " +
      (c.since ? c.since.replace(/-/g, ".") + "부터 " + dday + "일째" : "") + "</p>" +
      '<p class="pr-date">' + today.replace(/-/g, ".") + " 기준</p></div>";

    h += '<section class="pr-sec"><h2>일정</h2>';
    if (evs.length) {
      var lastD = "";
      evs.forEach(function (e) {
        if (e.date !== lastD) {
          if (lastD) h += "</div>";
          var ed = parse(e.date);
          h += '<div class="pr-day"><div class="pr-dh">' + (ed.getMonth() + 1) + "월 " + ed.getDate() + "일 " + WD[ed.getDay()] + "요일</div>";
          lastD = e.date;
        }
        var who = e.who === "me" ? c.me : e.who === "you" ? c.you : "함께";
        h += '<div class="pr-ev"><span class="pr-t">' + esc(e.title) + "</span><span class=\"pr-m\">" + esc(who) +
          (evWhenK(e) ? " · " + esc(evWhenK(e)) : "") + (evRange(e) ? " · " + esc(evRange(e)) : "") + "</span></div>";
      });
      h += "</div>";
    } else h += '<p class="pr-empty">이 기간에 적어 둔 일정이 없어요.</p>';
    h += "</section>";

    h += '<section class="pr-sec"><h2>사진</h2>';
    if (phs.length) {
      h += '<div class="pr-photos">';
      phs.forEach(function (p) {
        h += '<figure class="pr-ph">' + photoImg(p) +
          '<figcaption>' + esc(p.title || p.album || "") + "<em>" + String(p.date || "").replace(/-/g, ".") + "</em></figcaption></figure>";
      });
      h += "</div>";
    } else h += '<p class="pr-empty">이 기간에 담아 둔 사진이 없어요.</p>';
    h += "</section>";

    h += '<section class="pr-sec"><h2>기록</h2>';
    var dn = todos.filter(function (t) { return t.done; }).length;
    h += '<div class="pr-stats"><span>메모 ' + dn + " / " + todos.length + " 완료</span><span>버킷리스트 " +
      buckets.filter(function (b) { return b.done; }).length + " / " + buckets.length + " 이룸</span><span>영화·먹방 " + logs.length + "개</span></div>";
    if (buckets.length) {
      h += '<div class="pr-day"><div class="pr-dh">버킷리스트</div>';
      buckets.forEach(function (b) {
        h += '<div class="pr-ev"><span class="pr-t">' + (b.done ? "✓ " : "· ") + esc(b.title) + '</span><span class="pr-m">' + esc(b.cat || "") + "</span></div>";
      });
      h += "</div>";
    }
    if (logs.length) {
      h += '<div class="pr-day"><div class="pr-dh">영화 · 먹방</div>';
      logs.forEach(function (x) {
        h += '<div class="pr-ev"><span class="pr-t">' + esc(x.title) + '</span><span class="pr-m">' +
          (x.kind === "movie" ? "영화" : "먹방") + " · " + Number(x.rating || 0).toFixed(1) + "점" +
          (x.review ? " · " + esc(x.review) : "") + "</span></div>";
      });
      h += "</div>";
    }
    h += '</section><div class="pr-foot">투로그 · 둘이 함께 쌓는 기록</div></div>';

    var old = document.getElementById("printRoot");
    if (old && old.parentNode) old.parentNode.removeChild(old);
    var root = document.createElement("div");
    root.id = "printRoot";
    root.innerHTML = h;
    document.body.appendChild(root);
    return root;
  }

  function exportRun(scope) {
    var sc = scope === "month" || scope === "year" ? scope : "all";
    closeSheet();
    buildPrint(sc);
    toast("인쇄 창에서 ‘PDF로 저장’을 골라 주세요");
    setTimeout(function () { try { window.print(); } catch (e) {} }, 450);
  }

  function installHint() {    try {
      if (window.matchMedia("(display-mode: standalone)").matches || navigator.standalone) {
        return "홈 화면 앱으로 열려 있어요 · 투로그";
      }
    } catch (e) {}
    var ios = /iPhone|iPad|iPod/.test(navigator.userAgent || "");
    return ios
      ? "아이폰에서는 Safari 의 공유 → ‘홈 화면에 추가’ 로 앱처럼 열 수 있어요."
      : "브라우저 메뉴의 ‘앱 설치’(또는 홈 화면에 추가)로 앱처럼 열 수 있어요.";
  }

  function renderLogin() {
    var c = S.couple || { me: "소영", you: "준영" };
    var remote = !!(Store && Store.mode === "remote");

    /* remote: 진짜 계정 로그인 */
    if (remote) {
      var up = loginMode === "up";
      var f = '<div class="login"><div class="mark"><i></i><i></i></div>' +
        '<h1 class="login-t">' + (up ? "처음 오셨네요" : "다시, 우리") + "</h1>" +
        '<p class="login-s">' + (up
          ? "이메일과 비밀번호를 정하면, 상대와 같은 기록을 함께 볼 수 있어요."
          : "두 사람이 같은 기록을 봐요.<br>가입한 이메일로 들어와 주세요.") + "</p>" +
        '<form class="form" id="loginForm" style="margin-top:22px">' +
        '<div class="f"><label>이메일</label><input class="field" type="email" name="email" inputmode="email" autocomplete="username" autocapitalize="off" required></div>' +
        '<div class="f"><label>비밀번호</label><input class="field" type="password" name="password" autocomplete="' + (up ? "new-password" : "current-password") + '" minlength="6" required></div>' +
        '<button class="btn-primary" type="submit">' + (up ? "계정 만들기" : "로그인") + "</button></form>" +
        '<button class="btn-line" data-act="loginSwitch" style="margin-top:8px">' + (up ? "이미 계정이 있어요 · 로그인" : "처음이에요 · 계정 만들기") + "</button>" +
        '<p class="login-foot">기록은 두 사람만 볼 수 있게 잠겨 있어요. 로그아웃해도 쌓아 둔 기록은 지워지지 않아요.</p></div>';
      $("#s-login").innerHTML = f;
      return;
    }

    var h = '<div class="login"><div class="mark"><i></i><i></i></div>' +
      '<h1 class="login-t">다시, 우리</h1>' +
      '<p class="login-s">' + esc(c.me) + josa(c.me, "과", "와") + " " + esc(c.you) + josa(c.you, "이", "가") + " 함께한 기록이 그대로 기다리고 있어요.<br>다시 시작하면 바로 이어져요.</p>" +
      '<div class="login-card"><span class="set-av' + (avPic("me") ? " pic" : "") + '" style="background:' + avColor("me") + '">' + avInner("me") + "</span>" +
      '<div><div class="nm">' + esc(c.me) + "</div><div class=\"st\">로그아웃된 계정 · 기록은 안전하게 보관 중</div></div></div>" +
      '<button class="btn-primary" data-act="login">다시 시작하기</button>' +
      '<button class="btn-line" data-act="loginOther">다른 계정으로 시작</button>' +
      '<p class="login-foot">로그아웃 상태예요. ‘다시 시작하기’를 누르면 바로 원래 화면으로 돌아가요. 기록은 이 기기에 그대로 남아 있어요.</p>' +
      "</div>";
    $("#s-login").innerHTML = h;
  }

  /* ------------------------------------------------------------------ routing */
  var current = "home";
  var SCREENS = ["home", "cal", "diary", "photo", "set", "login"];
  function showScreen(name) {
    SCREENS.forEach(function (k) {
      var el = $("#s-" + k);
      if (el) el.classList.toggle("active", k === name);
    });
  }
  function renderAll() {
    if (S.auth && S.auth.out) {
      renderLogin();
      showScreen("login");
      var tb0 = $("#tabbar");
      if (tb0) { tb0.innerHTML = ""; tb0.style.display = "none"; }
      return;
    }
    var tb = $("#tabbar");
    if (tb) tb.style.display = "";
    if (current === "home") renderHome();
    if (current === "cal") renderCal();
    if (current === "diary") renderDiary();
    if (current === "photo") renderPhoto();
    if (current === "set") renderSet();
    var tabs = [
      ["home", "홈", IC.home],
      ["cal", "캘린더", IC.cal],
      ["diary", "노트", IC.diary],
      ["photo", "사진첩", IC.photo],
      ["set", "My", IC.person]
    ];
    $("#tabbar").innerHTML = tabs.map(function (t) {
      return '<button class="tab' + (current === t[0] ? " active" : "") + '" data-act="nav" data-screen="' + t[0] + '">' +
        '<span class="ic">' + t[2] + "</span><span>" + t[1] + "</span></button>";
    }).join("");
  }

  /* v28: 캘린더는 열 때마다 «오늘이 속한 달»·«오늘 날짜»로 시작합니다.
     달 안에서 화살표·스와이프로 넘긴 달은 그 달에 머무는 동안만 유지되고,
     다른 탭에 갔다 돌아오거나 앱을 다시 켜면 다시 이번 달이 나와요. */
  function syncCalToday() {
    if (!S || !S.ui) return;
    S.ui.calMonth = today.slice(0, 7);
    S.ui.selDate = today;
  }

  function go(name, opts) {
    if (S.auth && S.auth.out) return;
    /* v28: 탭에서 캘린더로 들어올 때는 늘 이번 달로.
       일정 검색 결과처럼 «그 달로 가야 하는» 이동은 opts.keepCal 로 그 달을 지킵니다. */
    if (name === "cal" && current !== "cal" && !(opts && opts.keepCal)) syncCalToday();
    current = name;
    showScreen(name);
    $("#screens").scrollTop = 0;
    renderAll();
  }

  /* ------------------------------------------------------------------ actions */
  document.addEventListener("click", function (ev) {
    var closeEl = ev.target.closest("[data-close]");
    if (closeEl) { closeSheet(); return; }

    var el = ev.target.closest("[data-act]");
    if (!el) return;
    var act = el.getAttribute("data-act");

    if (act === "nav") { go(el.getAttribute("data-screen")); return; }

    /* v18: 화면 잠금 · 기록 PDF */
    if (act === "lockSheet") { openSheet(formLock()); return; }
    if (act === "lockKey") { lockKey(el.getAttribute("data-k")); return; }
    if (act === "lockOff") {
      var cIn = sheet.querySelector('#lockForm input[name="cur"]');
      var cVal = cIn ? String(cIn.value || "") : "";
      if (!/^\d{4}$/.test(cVal)) { toast("지금 비밀번호 4자리를 적어 주세요"); return; }
      if (cVal !== lockCfg().pin) { toast("비밀번호가 달라요"); return; }
      lockSave({ on: false, pin: "" });
      closeSheet(); renderSet(); hideLock(); toast("화면 잠금을 껐어요");
      return;
    }
    if (act === "lockForgot") {
      askConfirm("비밀번호를 잊었다면 이 기기에서 잠금을 끌 수 있어요. 기록은 그대로 남고, 끄면 앱을 열 때 더 이상 묻지 않아요.", "잠금 끄기", function () {
        lockSave({ on: false, pin: "" });
        closeSheet(); renderSet(); hideLock(); toast("화면 잠금을 껐어요");
      }, "잠금 끄기");
      return;
    }
    if (act === "exportSheet") { openSheet(formExport()); return; }
    if (act === "exportRun") { exportRun(el.getAttribute("data-scope")); return; }

    if (act === "navSeg") {
      var ns = el.getAttribute("data-seg");
      if (ns) { S.ui.seg = ns; save(); }
      go(el.getAttribute("data-screen") || "diary");
      return;
    }

    if (act === "editDday") {
      openSheet(formDday(), function (fd) {
        S.couple.phrase = String(fd.get("phrase") || "").trim() || defaultPhrase();
        if (fd.get("since")) S.couple.since = fd.get("since");
        S.couple.fmt = fd.get("fmt") === "Y" ? "Y" : "D";
        /* 생일은 시트 안 달력(input[type=date])에서 바로 — 빈 값이면 비우기 */
        if (fd.has("bdMe") || fd.has("bdYou")) {
          S.couple.birthdays = S.couple.birthdays || {};
          S.couple.birthdays.me = String(fd.get("bdMe") || "").trim();
          S.couple.birthdays.you = String(fd.get("bdYou") || "").trim();
        }
        save(); closeSheet(); renderAll(); toast("기념일을 저장했어요");
      });
      return;
    }

    if (act === "fmt") {
      var fmtVal = el.getAttribute("data-fmt") === "Y" ? "Y" : "D";
      var fgrp = el.closest('[data-group="fmt"]');
      fgrp.querySelectorAll(".seg-btn").forEach(function (b) { b.classList.toggle("active", b === el); });
      var fin = fgrp.parentNode.querySelector('input[name="fmt"]');
      if (fin) fin.value = fmtVal;
      return;
    }

    if (act === "calPrev" || act === "calNext") { calMove(act === "calNext" ? 1 : -1); return; }

    if (act === "pickDay") { S.ui.selDate = el.getAttribute("data-date"); save(); renderCal(); return; }

    /* v19: 일정 검색 → 결과를 누르면 그 달·날짜로 */
    if (act === "calSearch") {
      sheetCenter = true;   /* v21: 아래가 아니라 화면 가운데에 떠요 */
      openSheet(formCalSearch(""));
      /* 바로 칠 수 있게 검색칸에 커서를 둡니다 */
      var si = document.getElementById("calSearchIn");
      if (si) { try { si.focus({ preventScroll: true }); } catch (e) { si.focus(); } }
      return;
    }
    if (act === "goEvent") {
      var gd = String(el.getAttribute("data-date") || "");
      if (!/^\d{4}-\d{2}-\d{2}$/.test(gd)) return;
      S.ui.calMonth = gd.slice(0, 7);
      S.ui.selDate = gd;
      save(); closeSheet(); go("cal", { keepCal: true });
      toast(Number(gd.slice(5, 7)) + "월 " + Number(gd.slice(8, 10)) + "일로 이동했어요");
      return;
    }

    if (act === "addEvent") {
      openSheet(formEvent(el.getAttribute("data-date") || S.ui.selDate || today), function (fd) {
        var st = String(fd.get("start") || today).slice(0, 10);
        var en = String(fd.get("end") || st).slice(0, 10);
        if (en < st) en = st;
        var ecol = String(fd.get("color") || "").toUpperCase();
        S.events.push({
          id: uid(), date: st, endDate: en,
          /* v28: 시간 설정 칸을 없앴어요 — 새 일정은 시간 없이 담깁니다 */
          time: "",
          title: String(fd.get("title") || "").trim(),
          /* v21: 종류 고르는 칸은 없어졌어요 — 새 일정은 「기타」로 담기고, 색은 고른 컬러(없으면 담당자 색) */
          type: "etc", memo: "",
          color: /^#[0-9A-F]{6}$/.test(ecol) ? ecol : "",
          who: fd.get("who") || "both"
        });
        S.ui.calMonth = st.slice(0, 7);
        S.ui.selDate = st;
        save(); closeSheet(); renderAll(); toast("일정을 추가했어요");
      });
      return;
    }

    /* v28: 달력 아래 상세 일정을 누르면 그 일정을 고칠 수 있는 시트가 열려요 */
    if (act === "editEvent") {
      var evId = el.getAttribute("data-id");
      var editEv = S.events.filter(function (x) { return x.id === evId; })[0];
      if (!editEv) return;
      openSheet(formEvent(null, editEv), function (fd) {
        var curEv = S.events.filter(function (x) { return x.id === evId; })[0];
        if (!curEv) return;
        var st2 = String(fd.get("start") || curEv.date || today).slice(0, 10);
        var en2 = String(fd.get("end") || st2).slice(0, 10);
        if (en2 < st2) en2 = st2;
        var ecol2 = String(fd.get("color") || "").toUpperCase();
        var title2 = String(fd.get("title") || "").trim();
        if (!title2) { toast("제목을 적어 주세요"); return; }
        curEv.date = st2;
        curEv.endDate = en2;
        curEv.title = title2;
        curEv.color = /^#[0-9A-F]{6}$/.test(ecol2) ? ecol2 : "";
        curEv.who = fd.get("who") || "both";
        S.ui.calMonth = st2.slice(0, 7);
        S.ui.selDate = st2;
        save(); closeSheet(); renderAll(); toast("일정을 저장했어요");
      });
      return;
    }

    if (act === "delEvent") {
      var id = el.getAttribute("data-id");
      S.events = S.events.filter(function (e) { return e.id !== id; });
      save(); renderAll(); toast("일정을 삭제했어요"); return;
    }

    if (act === "seg") {
      S.ui.seg = el.getAttribute("data-seg"); save(); renderDiary(); return;
    }

    if (act === "noteSettings") { openNoteSettings(); return; }

    if (act === "delListFromNote") {
      var nDelId = el.getAttribute("data-id");
      var nDel = findList(nDelId);
      askConfirm("‘" + esc(nDel ? nDel.title : "이") + "’ 리스트를 지울까요? 안에 적어 둔 항목도 함께 사라져요.", "지우기", function () {
        S.lists = S.lists.filter(function (x) { return x.id !== nDelId; });
        if (S.ui.seg === "list:" + nDelId) S.ui.seg = "todo";
        save(); renderDiary(); openNoteSettings(); toast("리스트를 지웠어요");
      });
      return;
    }

    if (act === "newList") {
      openSheet(formNewList(), function (fd) {
        var title = String(fd.get("title") || "").trim();
        if (!title) { toast("이름을 먼저 적어 주세요"); return; }
        var l = { id: uid(), title: title, emoji: fd.get("emoji") || "📌", kind: fd.get("kind") === "memo" ? "memo" : "check", items: [] };
        S.lists.push(l);
        S.ui.seg = "list:" + l.id;
        save(); closeSheet(); renderDiary(); toast("리스트를 만들었어요");
      });
      return;
    }

    if (act === "who") {
      var wv = el.getAttribute("data-who");
      var wgrp = el.closest('[data-group="who"]');
      wgrp.querySelectorAll(".wopt").forEach(function (b) { b.classList.toggle("active", b === el); });
      var win = wgrp.parentNode.querySelector('input[name="who"]');
      if (win) win.value = wv;
      return;
    }

    if (act === "lkind") {
      var lk = el.getAttribute("data-kind");
      var lgrp = el.closest('[data-group="lkind"]');
      lgrp.querySelectorAll(".seg-btn").forEach(function (b) { b.classList.toggle("active", b === el); });
      var lin = lgrp.parentNode.querySelector('input[name="kind"]');
      if (lin) lin.value = lk;
      return;
    }

    if (act === "lpick") {
      var erow = el.parentNode;
      erow.querySelectorAll(".emk").forEach(function (b) { b.classList.toggle("sel", b === el); });
      var ei = erow.parentNode.querySelector('input[name="emoji"]');
      if (ei) ei.value = el.getAttribute("data-emoji");
      return;
    }

    if (act === "delList") {
      var did = el.getAttribute("data-id");
      var rec = findList(did);
      askConfirm("‘" + esc(rec ? rec.title : "이") + "’ 리스트를 지울까요? 안에 적어 둔 항목도 함께 사라져요.", "지우기", function () {
        S.lists = S.lists.filter(function (x) { return x.id !== did; });
        if (S.ui.seg === "list:" + did) S.ui.seg = "todo";
        save(); renderDiary(); toast("리스트를 지웠어요");
      });
      return;
    }

    if (act === "toggleListItem") {
      var tl = findList(el.getAttribute("data-list"));
      var ti = el.getAttribute("data-id");
      var ltBefore = rowTops("#s-diary .dbody");
      if (tl) tl.items.forEach(function (it) { if (it.id === ti) it.done = !it.done; });
      save(); renderDiary(); rowMoveAnim("#s-diary .dbody", ltBefore); return;
    }

    if (act === "delListItem") {
      var dl = findList(el.getAttribute("data-list"));
      var di = el.getAttribute("data-id");
      if (dl) dl.items = dl.items.filter(function (it) { return it.id !== di; });
      save(); closeSheet(); renderDiary(); return;
    }

    if (act === "editListItem") {
      var elL = findList(el.getAttribute("data-list")), elId = el.getAttribute("data-id");
      var elIt = elL ? elL.items.filter(function (x) { return x.id === elId; })[0] : null;
      if (!elL || !elIt) return;
      openSheet(formListItem(elL, elIt), function (fd) {
        var L2 = findList(elL.id);
        var I2 = L2 ? L2.items.filter(function (x) { return x.id === elId; })[0] : null;
        if (!I2) return;
        var txt = String(fd.get("text") || "").trim();
        if (!txt) { toast("내용을 적어 주세요"); return; }
        I2.text = txt;
        I2.memo = String(fd.get("memo") || "").trim();
        save(); closeSheet(); renderDiary(); toast("저장했어요");
      });
      return;
    }

    if (act === "openGroup") {
      openGroupSheet(el.getAttribute("data-tab") || "todo", el.getAttribute("data-gid"));
      return;
    }

    if (act === "delCard") {
      var dcK = el.getAttribute("data-tab") || "todo";
      var dcGid = el.getAttribute("data-gid");
      var dcg = groupOf(dcK, dcGid);
      if (!dcg) return;
      askConfirm("‘" + esc(dcg.title || GROUP_DEF[dcK]) + "’ 카드를 지울까요? 안에 적은 항목도 함께 사라져요.", "지우기", function () {
        S.groups[dcK] = (S.groups[dcK] || []).filter(function (g) { return g.id !== dcGid; });
        var dckey = GROUP_ARR[dcK];
        S[dckey] = (S[dckey] || []).filter(function (x) { return x.gid !== dcGid; });
        openCard = null;
        save(); closeSheet(); renderDiary(); toast("카드를 지웠어요");
      });
      return;
    }

    if (act === "addGroup") {
      var agK = el.getAttribute("data-tab") || "todo";
      openSheet(formGroup(agK, null), function (fd) {
        var gTitle = String(fd.get("title") || "").trim();
        if (!gTitle) { toast("리스트 이름을 적어 주세요"); return; }
        S.groups = S.groups || {};
        S.groups[agK] = S.groups[agK] || [];
        S.groups[agK].push({ id: uid(), title: gTitle, who: "me", date: today });
        save(); closeSheet(); renderAll(); toast("리스트를 만들었어요");
      });
      return;
    }

    if (act === "editGroup") {
      var egK = el.getAttribute("data-tab") || "todo";
      var egId = el.getAttribute("data-gid");
      var eg = groupOf(egK, egId);
      if (!eg) return;
      openSheet(formGroup(egK, eg), function (fd) {
        var g2 = groupOf(egK, egId);
        if (!g2) return;
        var gTitle2 = String(fd.get("title") || "").trim();
        if (!gTitle2) { toast("리스트 이름을 적어 주세요"); return; }
        g2.title = gTitle2;
        save(); closeSheet(); renderAll(); toast("저장했어요");
      });
      return;
    }

    if (act === "delGroup") {
      var dgK = el.getAttribute("data-tab") || "todo";
      var dgId = el.getAttribute("data-gid");
      var dgN = itemsOf(dgK).filter(function (x) { return x.gid === dgId; }).length;
      if (dgN) { toast("안의 항목을 먼저 지워 주세요"); return; }
      S.groups[dgK] = (S.groups[dgK] || []).filter(function (g) { return g.id !== dgId; });
      save(); renderAll(); toast("리스트를 지웠어요");
      return;
    }

    if (act === "addListItem") {
      var alL = findList(el.getAttribute("data-list"));
      if (!alL) return;
      openSheet(formListItem(alL, null), function (fd) {
        var L0 = findList(alL.id);
        if (!L0) return;
        var txt0 = String(fd.get("text") || "").trim();
        if (!txt0) { toast("항목을 적어 주세요"); return; }
        L0.items.push({ id: uid(), text: txt0, memo: String(fd.get("memo") || "").trim(), done: false });
        save(); closeSheet(); renderDiary(); toast("추가했어요");
      });
      return;
    }

    if (act === "editList") {
      var eLid = el.getAttribute("data-id");
      var eL = findList(eLid);
      if (!eL) return;
      openSheet(formNewList(eL), function (fd) {
        var L3 = findList(eLid);
        if (!L3) return;
        var title = String(fd.get("title") || "").trim();
        if (!title) { toast("리스트 이름을 적어 주세요"); return; }
        L3.title = title;
        L3.emoji = fd.get("emoji") || "📌";
        L3.kind = fd.get("kind") === "memo" ? "memo" : "check";
        save(); closeSheet(); renderDiary(); toast("리스트를 저장했어요");
      });
      return;
    }

    if (act === "editTodo") {
      var etId = el.getAttribute("data-id");
      var et = S.todos.filter(function (x) { return x.id === etId; })[0];
      if (!et) return;
      openSheet(formTodo(et), function (fd) {
        var t2 = S.todos.filter(function (x) { return x.id === etId; })[0];
        if (!t2) return;
        var txt = String(fd.get("text") || "").trim();
        if (!txt) { toast(noteTab("todo").n + "를 적어 주세요"); return; }
        t2.text = txt;
        t2.memo = String(fd.get("memo") || "").trim();
        save(); closeSheet(); renderDiary(); toast("저장했어요");
      });
      return;
    }

    if (act === "delTodo") {
      var dtId = el.getAttribute("data-id");
      S.todos = S.todos.filter(function (x) { return x.id !== dtId; });
      save();
      /* v31: 카드 시트 안에서 지울 때는 시트를 닫지 않고 목록만 새로 그려요 */
      if (inCardSheet(el)) { renderDiary(); toast("지웠어요"); return; }
      closeSheet(); renderDiary(); toast("지웠어요"); return;
    }

    if (act === "editBucket") {
      var ebId = el.getAttribute("data-id");
      var eb = S.bucket.filter(function (x) { return x.id === ebId; })[0];
      if (!eb) return;
      openSheet(formBucket(eb), function (fd) {
        var b2 = S.bucket.filter(function (x) { return x.id === ebId; })[0];
        if (!b2) return;
        var title = String(fd.get("title") || "").trim();
        if (!title) { toast("내용을 적어 주세요"); return; }
        b2.title = title;
        b2.cat = fd.get("cat") || "기타";
        b2.memo = String(fd.get("memo") || "").trim();
        b2.done = !!fd.get("done");
        if (b2.done) delete b2.status;
        save(); closeSheet(); renderDiary(); toast("버킷을 저장했어요");
      });
      return;
    }

    if (act === "delBucket") {
      var dbId = el.getAttribute("data-id");
      S.bucket = S.bucket.filter(function (x) { return x.id !== dbId; });
      save();
      /* v31: 카드 시트 안에서는 시트를 닫지 않고 목록만 새로 그려요 */
      if (inCardSheet(el)) { renderDiary(); toast("버킷을 삭제했어요"); return; }
      closeSheet(); renderDiary(); toast("버킷을 삭제했어요"); return;
    }

    if (act === "editLog") {
      var egId = el.getAttribute("data-id");
      var eg = S.logs.filter(function (x) { return x.id === egId; })[0];
      if (!eg) return;
      openSheet(formLog(eg), function (fd) {
        var g2 = S.logs.filter(function (x) { return x.id === egId; })[0];
        if (!g2) return;
        var title = String(fd.get("title") || "").trim();
        if (!title) { toast("제목을 적어 주세요"); return; }
        g2.kind = fd.get("kind") === "food" ? "food" : "movie";
        g2.title = title;
        g2.rating = Number(fd.get("rating") || 4);
        g2.date = fd.get("date") || g2.date;
        g2.place = fd.get("place") || "";
        g2.review = fd.get("review") || "";
        save(); closeSheet(); renderDiary(); toast("기록을 저장했어요");
      });
      return;
    }

    if (act === "toggleDone") {
      S.ui.hideDone = !(S.ui && S.ui.hideDone);
      save(); renderDiary(); return;
    }

    if (act === "toggleTodo") {
      var tid = el.getAttribute("data-id");
      S.todos.forEach(function (t) { if (t.id === tid) t.done = !t.done; });
      save(); renderDiary(); return;
    }

    if (act === "toggleLog") {
      var lgid = el.getAttribute("data-id");
      S.logs.forEach(function (x) { if (x.id === lgid) x.done = !x.done; });
      save(); renderDiary(); return;
    }

    if (act === "addTodo") {
      openSheet(formTodo(), function (fd) {
        var at = String(fd.get("text") || "").trim();
        if (!at) { toast("내용을 적어 주세요"); return; }
        S.todos.push({ id: uid(), text: at, memo: String(fd.get("memo") || "").trim(), done: false, who: "함께", gid: firstGroupId("todo") });
        save(); closeSheet(); renderDiary(); toast("추가했어요");
      });
      return;
    }

    if (act === "toggleBucket") {
      var bid = el.getAttribute("data-id");
      S.bucket.forEach(function (b) { if (b.id === bid) b.done = !b.done; });
      save(); renderDiary(); return;
    }

    if (act === "addBucket") {
      openSheet(formBucket(), function (fd) {
        var bt = String(fd.get("title") || "").trim();
        if (!bt) { toast("내용을 적어 주세요"); return; }
        S.bucket.push({ id: uid(), title: bt, cat: fd.get("cat") || "기타", memo: String(fd.get("memo") || "").trim(), done: false, gid: firstGroupId("bucket") });
        save(); closeSheet(); renderDiary(); toast("버킷리스트에 담았어요");
      });
      return;
    }

    if (act === "addLog") {
      openSheet(formLog(), function (fd) {
        S.logs.push({
          id: uid(), kind: fd.get("kind"), title: fd.get("title"),
          rating: Number(fd.get("rating") || 4), date: fd.get("date"),
          review: fd.get("review") || "", place: fd.get("place") || "", done: true,
          gid: firstGroupId("log")
        });
        save(); closeSheet(); renderDiary(); toast("기록을 저장했어요");
      });
      return;
    }

    if (act === "delLog") {
      var lid = el.getAttribute("data-id");
      S.logs = S.logs.filter(function (l) { return l.id !== lid; });
      save();
      /* v31: 카드 시트 안에서는 시트를 닫지 않고 목록만 새로 그려요 */
      if (inCardSheet(el)) { renderDiary(); toast("기록을 삭제했어요"); return; }
      closeSheet(); renderDiary(); toast("기록을 삭제했어요"); return;
    }

    if (act === "openTheme") { openSheet(formTheme(), null); return; }

    if (act === "openThemeManager") { openSheet(themeManagerHtml(), null); return; }

    if (act === "openNotifSheet") { openSheet(notifSheetHtml(), null); return; }

    if (act === "toggleMode") { setMode(S.theme && S.theme.mode === "dark" ? "light" : "dark"); return; }

    if (act === "mode") { setMode(el.getAttribute("data-mode")); return; }

    if (act === "pickColor") {
      setThemeColor(el.getAttribute("data-target"), el.getAttribute("data-color") || "");
      return;
    }

    /* v21: 일정 추가 시트의 컬러 — 시트를 다시 그리지 않고 고른 칸만 표시를 옮겨요 */
    if (act === "pickEvColor") {
      var ecol = String(el.getAttribute("data-color") || "").toUpperCase();
      var ehid = document.querySelector('#sheet input[name="color"]');
      if (ehid) ehid.value = ecol;
      var egrid = el.closest('[data-sw="evColor"]');
      if (egrid) egrid.querySelectorAll(".sw").forEach(function (b) { b.classList.toggle("sel", b === el); });
      var ereset = document.querySelector('#sheet .cp-reset[data-act="pickEvColor"]');
      if (ereset) ereset.classList.toggle("on", !ecol);
      return;
    }

    /* v21: 노트 카드 시트에서 제목 바탕색을 고를 때 — 그 카드에만 바로 저장 */
    if (act === "pickCardColor") {
      var ccg = groupOf(el.getAttribute("data-tab") || "", el.getAttribute("data-gid") || "");
      if (!ccg) return;
      var ccv = String(el.getAttribute("data-color") || "");
      ccg.titleBg = /^#[0-9a-fA-F]{6}$/.test(ccv) ? ccv.toUpperCase() : "";
      save();
      /* 시트 안 컬러판 표시와 뒤의 카드 그리드를 함께 맞춰요 (적던 제목은 refreshCardSheet 가 지킵니다) */
      renderDiary();
      return;
    }

    if (act === "login") { S.auth.out = false; save(); closeSheet(); go("home"); toast("다시 오신 걸 환영해요"); return; }
    if (act === "loginOther") { toast("계정은 설정에서 바꿀 수 있어요"); return; }

    if (act === "logout") {
      openSheet(sheetHead("로그아웃") +
        '<p class="sheet-sub">로그아웃하면 이 기기에서는 기록이 보이지 않아요. 쌓아 둔 기록은 지워지지 않고 그대로 남아 있어요.</p>' +
        '<form class="form" id="sheetForm"><button class="btn-primary" type="submit">로그아웃</button></form>' +
        '<div style="height:10px"></div><button class="btn-line" data-close="1">취소</button>',
        function () {
          var remote = Store && Store.mode === "remote";
          S.auth.out = true;
          S.auth.email = "";
          loginMode = "in";          /* v25: 로그아웃 다음에는 가입 화면이 아니라 로그인 화면 */
          closeSheet();
          renderAll();
          toast("로그아웃했어요");
          if (remote) Store.auth.signOut().catch(function () {});
        });
      return;
    }

    if (act === "importLocal") {
      var linf = localReadyInfo();
      if (!linf) { toast("이 기기에 예전 기록이 없어요"); return; }
      openSheet(sheetHead("폰에 있던 기록 가져오기") +
        '<p class="sheet-sub">' + esc(localSummaryLine(linf)) + "을 지금 커플 공간에 더해요. 이미 있는 기록은 건드리지 않고, 같은 내용은 겹치지 않게 건너뛰어요.</p>" +
        '<form class="form" id="importForm"><button class="btn-primary" type="submit">가져오기</button></form>' +
        '<div style="height:10px"></div><button class="btn-line" data-close="1">취소</button>');
      return;
    }

    if (act === "copyCode") { copyText(myInviteCode(), "초대 코드를 복사했어요"); return; }

    if (act === "linkSheet") { openSheet(formLink()); return; }

    if (act === "newCode") {
      S.link = S.link || {};
      /* v25: remote 모드의 초대 코드는 서버(couples.invite_code)가 원본 —
         기기에만 적어 두면 화면이 그대로라 서버 값을 바꿉니다. */
      if (Store && Store.mode === "remote") {
        var freshCode = newInviteCode();
        var codeBtn = el;
        if (codeBtn) { codeBtn.disabled = true; codeBtn.textContent = "만드는 중"; }
        Store.couple.setCode(freshCode).then(function (res) {
          if (codeBtn) { codeBtn.disabled = false; codeBtn.textContent = "코드 새로 만들기"; }
          if (!res || res.error) { toast("코드를 새로 만들지 못했어요"); return; }
          S.link.code = freshCode;
          openSheet(formLink());
          toast("초대 코드를 새로 만들었어요");
        }).catch(function () {
          if (codeBtn) { codeBtn.disabled = false; codeBtn.textContent = "코드 새로 만들기"; }
          toast("코드를 새로 만들지 못했어요");
        });
        return;
      }
      S.link.code = newInviteCode();
      save();
      openSheet(formLink());
      toast("초대 코드를 새로 만들었어요");
      return;
    }

    if (act === "unlink") {
      if (Store && Store.mode === "remote") {
        toast("연결을 해제하는 중…");
        Store.couple.leave().then(function (res) {
          if (res && res.error) { toast("해제하지 못했어요"); return; }
          S.link.connected = false;
          save(); closeSheet(); renderAll(); toast("커플 연결을 해제했어요");
        }).catch(function () { toast("해제하지 못했어요"); });
        return;
      }
      S.link.connected = false;
      S.link.partnerCode = "";
      save(); closeSheet(); renderAll(); toast("커플 연결을 해제했어요"); return;
    }

    if (act === "pickOwner") {
      setOwnerColor(el.getAttribute("data-who") || "me", el.getAttribute("data-color") || "");
      toast("색을 바꿨어요");
      return;
    }

    if (act === "pickSched") {
      var sWho = el.getAttribute("data-who");
      var sCol = el.getAttribute("data-color") || "";
      S.couple.sched = S.couple.sched || {};
      S.couple.sched[sWho] = sCol || SCHED_DEFAULT[sWho];
      save(); renderAll(); toast("일정 색을 바꿨어요"); return;
    }

    if (act === "pickCap") {
      var pg = el.getAttribute("data-page") || "";
      var pgCol = el.getAttribute("data-color") || "";
      setPageCap(pg, pgCol);
      toast(pgCol ? "캡션 색을 바꿨어요" : "기본 캡션으로 돌렸어요");
      return;
    }

    if (act === "pickCapAll") {
      var allCol = el.getAttribute("data-color") || "";
      setCapAll(allCol);
      toast(allCol ? "페이지 캡션 색을 바꿨어요" : "캡션 색을 기본으로 돌렸어요");
      return;
    }

    if (act === "pickFont") {
      S.theme = S.theme || {};
      S.theme.font = fontOf(el.getAttribute("data-font") || "base").k;
      save(); applyTheme();
      if (current === "set") renderSet();
      return;
    }

    if (act === "toggleNotif") {
      var nk = el.getAttribute("data-key") || "";
      if (!nk) return;
      var non = !notifOn(nk);
      S.notif = S.notif || {};
      S.notif[nk] = non;
      save();
      el.setAttribute("aria-pressed", non ? "true" : "false");
      var tg = el.querySelector(".tgl");
      if (tg) tg.classList.toggle("on", non);
      if (current === "set") renderSet();
      if (non) {
        askNotifyPermission(function (granted) {
          toast(granted ? "알림을 켰어요" : "알림을 켰어요 · 브라우저 알림은 꺼져 있어요");
        });
      } else {
        toast("알림을 껐어요");
      }
      return;
    }

    if (act === "pickAvatar") {
      var aWho = el.getAttribute("data-who");
      var aCol = el.getAttribute("data-color") || "";
      S.couple.colors = S.couple.colors || {};
      S.couple.colors[aWho] = aCol || null;
      save(); applyTheme(); renderAll(); toast("프로필 색을 바꿨어요"); return;
    }

    if (act === "personSheet") {
      openPersonSheet(el.getAttribute("data-who") === "you" ? "you" : "me");
      return;
    }

    if (act === "pickPic") {
      var pWho = el.getAttribute("data-who") === "you" ? "you" : "me";
      if (!canEditAvatar(pWho)) { toast("프로필 사진은 " + (pWho === "you" ? S.couple.you : "본인") + " 폰에서 바꿀 수 있어요"); return; }
      var ai = $("#avatarInput");
      if (!ai) return;
      ai.value = "";
      ai.setAttribute("data-who", pWho);
      ai.click();
      return;
    }

    if (act === "clearPic") {
      var cWho = el.getAttribute("data-who") === "you" ? "you" : "me";
      if (!canEditAvatar(cWho)) { toast("프로필 사진은 " + (cWho === "you" ? S.couple.you : "본인") + " 폰에서 바꿀 수 있어요"); return; }
      setAvatarPic(cWho, "");
      toast("프로필 사진을 지웠어요"); return;
    }

    if (act === "openPhoto") { openPhoto(el.getAttribute("data-id")); return; }

    /* v23: 사진첩 달력 보기 — 켜고 끄기, 달 넘기기, 날짜 칸 열기 */
    if (act === "togglePhotoCal") {
      S.ui = S.ui || {};
      S.ui.photoCal = !S.ui.photoCal;
      if (S.ui.photoCal) S.ui.photoMonth = today.slice(0, 7);
      save(); renderPhoto(); return;
    }
    if (act === "pcalPrev" || act === "pcalNext") {
      S.ui = S.ui || {};
      S.ui.photoMonth = shiftYm(photoMonthYM(), act === "pcalPrev" ? -1 : 1);
      save(); renderPhoto(); return;
    }
    if (act === "pcalDay") {
      var pcds = el.getAttribute("data-date");
      var pcp = S.photos.filter(function (x) { return String(x.date || "").slice(0, 10) === pcds; }).sort(byDateDesc)[0];
      if (pcp) openPhoto(pcp.id);
      return;
    }

    if (act === "photoStep") { photoStep(Number(el.getAttribute("data-step")) || 1); return; }

    if (act === "addPhoto") {
      var pi = $("#photoInput");
      if (pi) { pi.value = ""; pi.click(); }
      return;
    }

    if (act === "photoEdit") {
      var pe = S.photos.filter(function (x) { return x.id === el.getAttribute("data-id"); })[0];
      if (!pe) return;
      var pvKeep = !!photoView;
      openSheet(formEditPhoto(pe), function (fd) {
        var p2 = S.photos.filter(function (x) { return x.id === pe.id; })[0];
        if (!p2) return;
        p2.title = String(fd.get("title") || "").trim();
        p2.album = String(fd.get("album") || "").trim() || defaultAlbum();
        p2.date = fd.get("date") || p2.date;
        p2.place = String(fd.get("place") || "").trim();
        p2.memo = String(fd.get("memo") || "").trim();
        save(); closeSheet(); renderAll(); toast("사진 정보를 저장했어요");
        /* v18: 사진을 보던 중이었다면 수정 뒤에도 그 자리에서 계속 넘겨 볼 수 있게 */
        if (pvKeep && photoShow(p2.id)) { openSheet(photoViewBody(), null); }
      });
      return;
    }

    if (act === "photoDelete") {
      var pdId = el.getAttribute("data-id");
      var pdView = photoView ? { ids: photoView.ids.slice(), i: photoView.i } : null;
      askConfirm("이 사진을 지울까요? 사진과 캡션이 함께 사라져요.", "지우기", function () {
        var gone = S.photos.filter(function (x) { return x.id === pdId; })[0];
        S.photos = S.photos.filter(function (x) { return x.id !== pdId; });
        delete PHOTO_URLS[pdId];
        if (gone) { try { Store.photos.remove(gone).catch(function () {}); } catch (e) {} }
        save(); renderAll(); toast("사진을 지웠어요");
        /* v18: 지운 사진이 마지막이 아니면 그날 다음 사진을 이어서 보여 줘요 */
        var left = pdView ? pdView.ids.filter(function (x) { return x !== pdId; }) : [];
        if (left.length) {
          var ni = Math.min(pdView.i, left.length - 1);
          photoView = { ids: left, i: ni };
          openSheet(photoViewBody(), null);
        } else {
          photoView = null;
          closeSheet();
        }
      }, "사진 삭제");
      return;
    }

    if (act === "syncNow") {
      toast("동기화하는 중…");
      Store.flush().then(function () {
        return Store.reload();
      }).then(function (doc) {
        if (doc) { var k = S.ui; S = normalizeState(doc); S.ui = k; applyTheme(); renderAll(); }
        toast(Store.status.state === "offline" ? "연결을 기다리는 중이에요" : "동기화했어요");
      }).catch(function () { toast("지금은 연결할 수 없어요"); });
      return;
    }

    if (act === "loginSwitch") {
      loginMode = loginMode === "up" ? "in" : "up";
      renderLogin();
      return;
    }

    if (act === "pickCap") {
      setCapColor(el.getAttribute("data-id"), el.getAttribute("data-color") || "");
      return;
    }

    if (act === "rate") {
      var val = Number(el.getAttribute("data-val"));
      var row = el.closest(".rate");
      var input = row.parentNode.querySelector('input[name="rating"]');
      if (input) input.value = String(val);
      row.querySelectorAll(".rate-star").forEach(function (b, i) { b.classList.toggle("on", i < val); });
      var lbl = row.querySelector(".val");
      if (lbl) lbl.textContent = val.toFixed(1);
      return;
    }

    if (act === "kind") {
      var kind = el.getAttribute("data-kind");
      var grp = el.closest('[data-group="kind"]');
      grp.querySelectorAll(".seg-btn").forEach(function (b) { b.classList.toggle("active", b === el); });
      var inp = grp.parentNode.querySelector('input[name="kind"]');
      if (inp) inp.value = kind;
      return;
    }
  });

  /* ==========================================================================
     v18: 꾹 눌러 순서 바꾸기 — 노트의 리스트 카드와 To-do 한 줄
     · 320ms 동안 가만히 누르고 있으면 카드가 들려요
     · 그 뒤에는 손가락/마우스를 움직여 원하는 자리에 놓으면 순서가 저장됩니다
     · 스크롤하려고 바로 움직이면(8px 이상) 드래그를 포기하고 평소처럼 스크롤돼요
     ========================================================================== */
  var RZ_LONG = 460;
  var rzState = null;
  var rzMoved = false;

  function rzTarget(t) {
    if (!t || !t.closest) return null;
    var card = t.closest("#s-diary .ngrid .ncard");
    if (card && !card.classList.contains("new")) return { el: card, kind: "card", box: card.parentNode };
    var row = t.closest(".todo-items .trow");
    if (row) return { el: row, kind: "row", box: row.parentNode };
    return null;
  }

  function rzSiblings(st) {
    var sel = st.kind === "card" ? ".ncard:not(.new)" : ".trow";
    return Array.prototype.slice.call(st.box.children).filter(function (n) {
      return n !== st.el && n !== st.ph && n.matches && n.matches(sel);
    });
  }

  function rzBegin(st) {
    if (!st || st.active || !st.el.parentNode) return;
    st.active = true;
    st.moved = false;
    var r = st.el.getBoundingClientRect();
    /* v19: 원래 자리에는 점선 빈 자리를 두고, 잡힌 카드/행은 fixed 로 떠서 손가락을 따라갑니다 */
    var ph = document.createElement("div");
    ph.className = "rz-ph" + (st.kind === "card" ? " rz-ph-card" : " rz-ph-row");
    ph.style.width = r.width + "px";
    ph.style.height = r.height + "px";
    st.el.parentNode.insertBefore(ph, st.el);
    st.ph = ph;
    st.el.classList.add("lift");
    st.el.style.boxSizing = "border-box";
    st.el.style.width = r.width + "px";
    st.el.style.height = r.height + "px";
    st.el.style.left = r.left + "px";
    st.el.style.top = r.top + "px";
    st.el.style.margin = "0";
    st.el.style.transform = "translate3d(0,0,0) scale(1.03)";
    if (st.box.classList) st.box.classList.add("rz-on");
    try { if (navigator.vibrate) navigator.vibrate(12); } catch (e) {}
  }

  function rzMove(ev) {
    var st = rzState;
    if (!st || !st.active) return;
    var x = ev.clientX, y = ev.clientY;
    /* v19: 손가락이 실제로 움직였는지 기억 — 안 움직였으면 «누른 것» 으로 보고 클릭을 살립니다 */
    if (!st.moved && (Math.abs(x - st.x) > 4 || Math.abs(y - st.y) > 4)) st.moved = true;
    /* 잡힌 카드/행은 손가락을 그대로 따라가요 */
    st.el.style.transform = "translate3d(" + (x - st.x) + "px," + (y - st.y) + "px,0) scale(1.03)";
    if (!st.moved) return;
    var sibs = rzSiblings(st);
    if (!sibs.length) return;
    var best = null, bestD = Infinity;
    sibs.forEach(function (n) {
      var r = n.getBoundingClientRect();
      var d = Math.sqrt(Math.pow(x - (r.left + r.width / 2), 2) + Math.pow(y - (r.top + r.height / 2), 2));
      if (d < bestD) { bestD = d; best = n; }
    });
    if (!best) return;
    var r2 = best.getBoundingClientRect();
    var after;
    if (st.kind === "card") {
      /* 같은 줄이면 좌우로, 다른 줄이면 위아래로 자리를 정해요 */
      after = (Math.abs(y - (r2.top + r2.height / 2)) < r2.height / 2)
        ? (x > r2.left + r2.width / 2)
        : (y > r2.top + r2.height / 2);
    } else {
      after = y > r2.top + r2.height / 2;
    }
    /* 빈 자리(placeholder)가 실시간으로 밀려나며 어디로 들어가는지 보여요 */
    if (after) {
      if (best.nextSibling !== st.ph) best.parentNode.insertBefore(st.ph, best.nextSibling);
    } else if (best !== st.ph.nextSibling) {
      best.parentNode.insertBefore(st.ph, best);
    }
  }

  function rzRows(st) {
    var box = st.box;
    var listId = box.getAttribute("data-list");
    var gid = box.getAttribute("data-gid");
    var tab = box.getAttribute("data-tab");
    var arr;
    if (listId) {
      var l = findList(listId);
      if (!l) return;
      arr = l.items;
    } else {
      arr = itemsOf(tab);
    }
    var ids = Array.prototype.slice.call(box.querySelectorAll(".trow")).map(function (n) {
      var b = n.querySelector("[data-id]");
      return b ? b.getAttribute("data-id") : null;
    });
    var byId = {};
    arr.forEach(function (it) { byId[it.id] = it; });
    var slots = [];
    arr.forEach(function (it, i) { if (!gid || it.gid === gid) slots.push(i); });
    var seq = ids.map(function (id) { return byId[id]; }).filter(Boolean);
    if (!seq.length || seq.length !== slots.length) return;
    slots.forEach(function (pos, n) { arr[pos] = seq[n]; });
    save();
    if (box.closest("#sheet")) refreshCardSheet();
    else renderDiary();
  }

  function rzCommit(st) {
    if (st.kind === "card") {
      var tab = st.el.getAttribute("data-tab");
      var gs = groupsOf(tab);
      var order = Array.prototype.slice.call(st.box.querySelectorAll(".ncard[data-gid]")).map(function (n) { return n.getAttribute("data-gid"); });
      var byId = {};
      gs.forEach(function (g) { byId[g.id] = g; });
      var next = [];
      order.forEach(function (id) { if (byId[id]) { next.push(byId[id]); delete byId[id]; } });
      gs.forEach(function (g) { if (byId[g.id]) next.push(g); });
      S.groups[tab] = next;
      save();
      renderDiary();
    } else {
      rzRows(st);
    }
    toast("순서를 바꿨어요");
  }

  function rzEnd() {
    var st = rzState;
    if (!st) return;
    clearTimeout(st.timer);
    if (st.active) {
      var movedNow = st.moved;
      /* 잡았던 카드/행을 (옮겨 둔) 자리로 되돌리고 임시 스타일을 지워요 */
      if (st.ph && st.ph.parentNode) st.ph.parentNode.insertBefore(st.el, st.ph);
      st.el.classList.remove("lift");
      ["boxSizing", "width", "height", "left", "top", "margin", "transform", "position", "pointerEvents"].forEach(function (k) {
        st.el.style[k] = "";
      });
      if (st.ph && st.ph.parentNode) st.ph.parentNode.removeChild(st.ph);
      if (st.box.classList) st.box.classList.remove("rz-on");
      /* v19: 꾹 눌렀어도 손가락을 움직이지 않았으면 그냥 누른 것 — 순서를 바꾸지 않고,
         다음 click 도 막지 않아 그 리스트의 전체 목록이 열립니다. */
      if (movedNow) {
        rzMoved = true;
        setTimeout(function () { rzMoved = false; }, 500);
        rzCommit(st);
      }
    }
    rzState = null;
  }

  document.addEventListener("pointerdown", function (ev) {
    if (ev.pointerType === "mouse" && ev.button !== 0) return;
    /* 새로 누르는 손가락/마우스는 언제나 새 동작 — 드래그 직후의 click 만 한 번 막아요 */
    rzMoved = false;
    var hit = rzTarget(ev.target);
    if (!hit) return;
    var st = { el: hit.el, kind: hit.kind, box: hit.box, x: ev.clientX, y: ev.clientY, active: false, timer: null };
    st.timer = setTimeout(function () { rzBegin(st); }, RZ_LONG);
    rzState = st;
  }, true);

  window.addEventListener("pointermove", function (ev) {
    var st = rzState;
    if (!st) return;
    if (!st.active) {
      if (Math.abs(ev.clientX - st.x) > 8 || Math.abs(ev.clientY - st.y) > 8) {
        clearTimeout(st.timer);
        rzState = null;
      }
      return;
    }
    if (ev.cancelable) ev.preventDefault();
    rzMove(ev);
  }, { passive: false });

  window.addEventListener("pointerup", rzEnd);
  window.addEventListener("pointercancel", rzEnd);
  window.addEventListener("blur", rzEnd);

  /* 드래그하는 동안에는 화면이 따라 스크롤되지 않게, 길게 눌러 뜨는 메뉴·글자 선택도 막아요 */
  document.addEventListener("touchmove", function (ev) {
    if (rzState && rzState.active && ev.cancelable) ev.preventDefault();
  }, { passive: false });
  document.addEventListener("contextmenu", function (ev) {
    if (rzState && rzState.active) ev.preventDefault();
  });
  document.addEventListener("click", function (ev) {
    if (rzMoved) { ev.stopPropagation(); ev.preventDefault(); rzMoved = false; }
    /* v21: 달력을 밀어서 달을 넘긴 직후의 click 은 날짜 선택으로 이어지지 않게 */
    if (calSwiped) { ev.stopPropagation(); ev.preventDefault(); calSwiped = false; }
  }, true);

  /* v19: 키보드로도 카드 열기 (Enter / Space) — div[role=button] 은 스스로 click 을 만들지 않아요 */
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter" && ev.key !== " " && ev.key !== "Spacebar") return;
    var el = ev.target.closest && ev.target.closest("#s-diary .ncard[data-act='openGroup']");
    if (!el) return;
    ev.preventDefault();
    el.click();
  });

  /* 사진 크게 보기: 손가락으로 좌우 넘기기 */
  var pvSwipe = null;
  document.addEventListener("touchstart", function (ev) {
    if (!photoView) return;
    var v = ev.target.closest && ev.target.closest(".pview");
    if (!v || !ev.touches || !ev.touches.length) return;
    pvSwipe = { x: ev.touches[0].clientX, y: ev.touches[0].clientY };
  }, { passive: true });
  document.addEventListener("touchend", function (ev) {
    if (!pvSwipe || !ev.changedTouches || !ev.changedTouches.length) { pvSwipe = null; return; }
    var t = ev.changedTouches[0];
    var dx = t.clientX - pvSwipe.x, dy = t.clientY - pvSwipe.y;
    pvSwipe = null;
    if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.4) photoStep(dx < 0 ? 1 : -1);
  }, { passive: true });

  /* v23: 사진첩 달력에서도 손가락으로 좌우로 밀면 이전/다음 달 */
  var pcalSwipe = null, pcalSwiped = false;
  document.addEventListener("touchstart", function (ev) {
    pcalSwipe = null;
    if (current !== "photo" || photoView || !(S.ui && S.ui.photoCal)) return;
    var g = ev.target.closest && ev.target.closest("#s-photo .pcal-grid");
    if (!g || !ev.touches || !ev.touches.length) return;
    pcalSwipe = { x: ev.touches[0].clientX, y: ev.touches[0].clientY };
  }, { passive: true });
  document.addEventListener("touchend", function (ev) {
    if (!pcalSwipe || !ev.changedTouches || !ev.changedTouches.length) { pcalSwipe = null; return; }
    var t = ev.changedTouches[0];
    var dx = t.clientX - pcalSwipe.x, dy = t.clientY - pcalSwipe.y;
    pcalSwipe = null;
    if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy) * 1.3) return;
    pcalSwiped = true;
    setTimeout(function () { pcalSwiped = false; }, 400);
    S.ui.photoMonth = shiftYm(photoMonthYM(), dx < 0 ? 1 : -1);
    save(); renderPhoto();
  }, { passive: true });
  /* 밀어서 달을 넘긴 직후의 click 은 날짜 열기로 이어지지 않게 */
  document.addEventListener("click", function (ev) {
    if (pcalSwiped) { ev.stopPropagation(); ev.preventDefault(); pcalSwiped = false; }
  }, true);

  /* v21: 달력에서 손가락으로 좌우로 밀면 이전/다음 달 — 사진 크게 보기의 넘기기와 같은 방식.
     왼쪽으로 밀면 다음 달, 오른쪽으로 밀면 이전 달. 탭(날짜 선택)과 세로 스크롤은 그대로 둡니다. */
  var calSwipe = null, calSwiped = false;
  document.addEventListener("touchstart", function (ev) {
    calSwipe = null;
    if (current !== "cal" || photoView) return;
    var g = ev.target.closest && ev.target.closest("#s-cal .cal");
    if (!g || !ev.touches || !ev.touches.length) return;
    calSwipe = { x: ev.touches[0].clientX, y: ev.touches[0].clientY };
  }, { passive: true });
  document.addEventListener("touchend", function (ev) {
    if (!calSwipe || !ev.changedTouches || !ev.changedTouches.length) { calSwipe = null; return; }
    var t = ev.changedTouches[0];
    var dx = t.clientX - calSwipe.x, dy = t.clientY - calSwipe.y;
    calSwipe = null;
    /* 가로로 45px 넘게, 세로 움직임보다 확실히 크게 밀었을 때만 — 그냥 누른 날짜는 그대로 선택돼요 */
    if (Math.abs(dx) < 45 || Math.abs(dx) < Math.abs(dy) * 1.3) return;
    calSwiped = true;
    setTimeout(function () { calSwiped = false; }, 400);
    calMove(dx < 0 ? 1 : -1);
  }, { passive: true });

  document.addEventListener("submit", function (ev) {
    if (ev.target.id === "personForm") {
      ev.preventDefault();
      var pfWho = ev.target.getAttribute("data-who") === "you" ? "you" : "me";
      var pfName = String(new FormData(ev.target).get("name") || "").trim();
      if (!pfName) { toast("이름을 적어 주세요"); return; }
      var beforeDef = defaultPhrase();
      if (pfWho === "me") S.couple.me = pfName; else S.couple.you = pfName;
      /* 문구를 기본값 그대로 두고 있었다면 새 이름에 맞춰 같이 바꿔 줍니다 */
      if (S.couple.phrase === beforeDef) S.couple.phrase = defaultPhrase();
      save(); closeSheet(); renderAll(); toast("저장했어요");
      return;
    }

    if (ev.target.id === "lockForm") {
      ev.preventDefault();
      var lf = new FormData(ev.target);
      var wasOn = lockOn();
      var curPin = String(lf.get("cur") || "");
      var nPin = String(lf.get("pin") || "").trim();
      var nPin2 = String(lf.get("pin2") || "").trim();
      if (wasOn && curPin !== lockCfg().pin) { toast("지금 비밀번호가 달라요"); return; }
      if (!/^\d{4}$/.test(nPin)) { toast("숫자 4자리로 정해 주세요"); return; }
      if (nPin !== nPin2) { toast("두 번 적은 숫자가 달라요"); return; }
      lockSave({ on: true, pin: nPin });
      closeSheet(); renderSet();
      toast(wasOn ? "비밀번호를 바꿨어요" : "화면 잠금을 켰어요");
      return;
    }

    if (ev.target.id === "noteForm") {
      ev.preventDefault();
      var nf = new FormData(ev.target);
      /* v18: 한 칸에 적은 「이모지 + 이름」을 앞의 이모지와 나머지로 나눠 저장해요 */
      NOTE_BASE.forEach(function (k) {
        var split = splitEmojiName(nf.get("t_" + k));
        S.note[k] = {
          e: split.n ? split.e : "",
          n: split.n || NOTE_DEF[k].n
        };
      });
      S.lists.forEach(function (l) {
        var ls = splitEmojiName(nf.get("l_" + l.id));
        l.emoji = ls.n ? ls.e : "";
        l.title = ls.n || l.title;
      });
      var newSplit = splitEmojiName(nf.get("new_n"));
      if (newSplit.n) {
        var newList = {
          id: uid(), title: newSplit.n,
          emoji: newSplit.e,
          kind: nf.get("new_kind") === "memo" ? "memo" : "check", items: []
        };
        S.lists.push(newList);
        S.ui.seg = "list:" + newList.id;
      }
      save(); closeSheet(); renderDiary();
      toast("노트 설정을 저장했어요");
      return;
    }

    if (ev.target.id === "linkForm") {
      ev.preventDefault();
      var rawCode = String(new FormData(ev.target).get("code") || "").replace(/\D/g, "");
      if (rawCode.length !== 6) { toast("6자리 코드를 입력해 주세요"); return; }
      if (rawCode === myInviteCode()) { toast("내 코드예요. 상대 코드를 입력해 주세요"); return; }

      if (Store && Store.mode === "remote") {
        var lbtn = ev.target.querySelector("button");
        if (lbtn) { lbtn.disabled = true; lbtn.textContent = "연결 중"; }
        Store.couple.join(rawCode).then(function (res) {
          if (lbtn) { lbtn.disabled = false; lbtn.textContent = "연결하기"; }
          if (!res || res.error) { toast("연결하지 못했어요. 코드를 확인해 주세요"); return; }
          return Store.reload().then(function (doc) {
            return new Promise(function (resolve) {
              withLocalHistory(doc, function (next, mres) {
                if (next) {
                  var keepUi = S.ui;
                  S = normalizeState(next);
                  S.ui = keepUi;
                  applyTheme(); renderAll(); loadPhotoUrls();
                }
                closeSheet();
                toast(migrateToast(mres) || "커플 연결을 완료했어요");
                repairNoteGroups();
                resolve();
              });
            });
          });
        }).catch(function () {
          if (lbtn) { lbtn.disabled = false; lbtn.textContent = "연결하기"; }
          toast("연결하지 못했어요");
        });
        return;
      }

      S.link.connected = true;
      S.link.partnerCode = rawCode;
      save(); closeSheet(); renderAll(); toast("커플 연결을 완료했어요");
      return;
    }

    if (ev.target.id === "loginForm") {
      ev.preventDefault();
      var lfd = new FormData(ev.target);
      var email = String(lfd.get("email") || "").trim();
      var pw = String(lfd.get("password") || "");
      if (!email || pw.length < 6) { toast("이메일과 6자 이상의 비밀번호를 넣어 주세요"); return; }
      var btn = ev.target.querySelector(".btn-primary");
      var label = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; btn.textContent = "잠시만요…"; }
      var call = loginMode === "up" ? Store.auth.signUp(email, pw) : Store.auth.signIn(email, pw);
      call.then(function (res) {
        if (btn) { btn.disabled = false; btn.textContent = label; }
        if (res && res.error) { toast("들어가지 못했어요: " + res.error); return; }
        if (res && res.needsConfirm) { toast("메일로 온 확인 링크를 누른 뒤 로그인해 주세요"); return; }
        return Store.load().then(function (doc) {
          /* v26: 이 폰에 예전 로컬 기록이 남아 있으면 먼저 이어 옵니다 */
          return new Promise(function (resolve) {
            withLocalHistory(doc, function (next, mres) { resolve({ doc: next, mres: mres }); });
          });
        }).then(function (got) {
          S = normalizeState(got.doc || emptyState());
          S.auth.out = false;
          S.auth.email = email;
          applyTheme(); go("home"); renderAll();
          loadPhotoUrls();
          toast(migrateToast(got.mres) || "들어왔어요");
          /* v27: 카드 정보 없이 올라간 예전 노트가 있으면 바로 되살립니다 */
          repairNoteGroups();
        });
      }).catch(function (e) { toast("들어가지 못했어요"); if (btn) { btn.disabled = false; btn.textContent = label; } });
      return;
    }

    if (ev.target.id === "importForm") {
      ev.preventDefault();
      var ibtn = ev.target.querySelector(".btn-primary");
      if (ibtn) { ibtn.disabled = true; ibtn.textContent = "가져오는 중…"; }
      Store.migrate.run({ force: true }).then(function (res) {
        if (ibtn) { ibtn.disabled = false; ibtn.textContent = "가져오기"; }
        closeSheet();
        if (!res || !res.ok) {
          toast(res && res.reason === "no_local" ? "이 기기에 예전 기록이 없어요"
            : res && res.reason === "no_couple" ? "로그인이 필요해요"
            : "가져오지 못했어요. 잠시 뒤 다시 해 주세요");
          return;
        }
        applyMigrated(res);
        /* v27: 예전에 gid 없이 올라간 항목도 이 폰의 카드 자리로 맞춥니다 */
        repairNoteGroups();
      }).catch(function () { closeSheet(); toast("가져오지 못했어요"); });
      return;
    }

    if (ev.target.id === "setForm") {
      ev.preventDefault();
      var sfd = new FormData(ev.target);
      var me2 = String(sfd.get("me") || "").trim(), you2 = String(sfd.get("you") || "").trim();
      if (!me2 || !you2) { toast("두 이름을 모두 적어 주세요"); return; }
      S.couple.me = me2;
      S.couple.you = you2;
      if (sfd.get("since")) S.couple.since = sfd.get("since");
      S.couple.phrase = String(sfd.get("phrase") || "").trim() || "함께한 지";
      S.couple.fmt = sfd.get("fmt") === "Y" ? "Y" : "D";
      save(); applyTheme(); renderAll(); toast("저장했어요");
      return;
    }
    if (ev.target.id === "listAddForm") {
      /* 노트 리스트: ○ + 입력 + Add 로 바로 더하기 */
      ev.preventDefault();
      var lf = ev.target;
      var lid = lf.getAttribute("data-list");
      if (lid) {
        /* 사용자 리스트(리스트 탭) 안에서 바로 더하기 */
        var lobj = findList(lid);
        if (!lobj) return;
        var cin = lf.querySelector('input[name="text"]');
        var ctx = String((cin && cin.value) || "").trim();
        if (!ctx) { if (cin) cin.focus(); return; }
        var cit = { id: uid(), text: ctx, memo: "", done: false };
        lobj.items.push(cit);
        save();
        var cbox = document.querySelector('#s-diary .todo-items[data-list="' + lid + '"]');
        if (cbox) {
          var cem = cbox.querySelector(".empty");
          if (cem) cem.remove();
          cbox.insertAdjacentHTML("beforeend", listItemRow(cit, '<div class="t tw">' + esc(cit.text) + "</div>",
            'data-act="toggleListItem" data-list="' + lid + '" data-id="' + cit.id + '"',
            'data-act="editListItem" data-list="' + lid + '" data-id="' + cit.id + '"',
            'data-act="delListItem" data-list="' + lid + '" data-id="' + cit.id + '"'));
        }
        if (cin) { cin.value = ""; cin.focus(); }
        var cpr = document.querySelector('#s-diary .progress[data-list="' + lid + '"]');
        if (cpr) updateProgressBar(cpr, lobj.items, "완료");
        return;
      }
      var lk = lf.getAttribute("data-tab") || "todo";
      var lgid = lf.getAttribute("data-gid") || firstGroupId(lk);
      var lin = lf.querySelector('input[name="text"]');
      var ltxt = String((lin && lin.value) || "").trim();
      if (!ltxt) { if (lin) lin.focus(); return; }
      var lit = { id: uid(), done: false, gid: lgid };
      if (lk === "todo") { lit.text = ltxt; lit.memo = ""; lit.who = "함께"; }
      else if (lk === "bucket") { lit.title = ltxt; lit.cat = "기타"; lit.memo = ""; }
      else { lit.kind = "movie"; lit.title = ltxt; lit.rating = 4; lit.date = today; lit.review = ""; lit.place = ""; lit.done = true; }
      itemsOf(lk).push(lit);
      save();
      /* 카드 상세 시트에서 바로 더한 경우 — 시트 안 목록에 붙이고 입력칸을 비워요 */
      if (openCard && openCard.tab === lk && openCard.gid === lgid) {
        var sbox = document.querySelector('#sheet .card-items');
        if (sbox) {
          var sel2 = sbox.querySelector(".empty");
          if (sel2) sel2.remove();
          sbox.insertAdjacentHTML("beforeend", diaryRow(lk, lit));
        }
        if (lin) { lin.value = ""; lin.focus(); }
        return;
      }
      var lbox = document.querySelector('#s-diary .todo-items[data-tab="' + lk + '"][data-gid="' + lgid + '"]');
      if (lbox) {
        var lel = lbox.querySelector(".empty");
        if (lel) lel.remove();
        lbox.insertAdjacentHTML("beforeend", diaryRow(lk, lit));
      }
      if (lin) { lin.value = ""; lin.focus(); }
      var lpr = document.querySelector('#s-diary .progress[data-tab="' + lk + '"]');
      if (lpr) updateProgressBar(lpr, itemsOf(lk), lk === "bucket" ? "달성" : "완료");
      return;
    }
    if (ev.target.id !== "sheetForm" || !sheetSubmit) return;
    ev.preventDefault();
    var fd = new FormData(ev.target);
    try { sheetSubmit(fd); } catch (e) { toast("저장하지 못했어요"); }
  });

  document.addEventListener("input", function (ev) {
    var t = ev.target;
    /* v19: 일정 검색 — 글자를 칠 때마다 결과를 바로 */
    if (t && t.id === "calSearchIn") {
      var sOut = document.getElementById("calSearchOut");
      if (sOut) sOut.innerHTML = calSearchResults(t.value);
      return;
    }
    /* v21: 일정 시트 — 날짜를 고르면 큰 날짜 글씨가 그 자리에서 바뀌고, 시간을 고르면 버튼에 시간이 남아요 */
    if (t && t.classList && t.classList.contains("js-evdate")) {
      var edside = t.getAttribute("data-side");
      var big = document.querySelector('#sheet .ev-dbig[data-dbig="' + edside + '"]');
      if (big) big.textContent = evDateBig(t.value);
      /* v28: 날짜 아래 요일(화요일)도 함께 바뀝니다 */
      var dowEl = document.querySelector('#sheet .ev-dow[data-dow="' + edside + '"]');
      if (dowEl) dowEl.textContent = evDowFull(t.value);
      /* 시작일을 종료일보다 뒤로 고르면 종료일도 같이 따라가요 */
      if (edside === "start") {
        var ein = document.querySelector('#sheet .js-evdate[data-side="end"]');
        if (ein && ein.value && ein.value < t.value) {
          ein.value = t.value;
          var ebig = document.querySelector('#sheet .ev-dbig[data-dbig="end"]');
          if (ebig) ebig.textContent = evDateBig(t.value);
          var edow = document.querySelector('#sheet .ev-dow[data-dow="end"]');
          if (edow) edow.textContent = evDowFull(t.value);
        }
      }
      return;
    }
    if (t && t.classList && t.classList.contains("js-color")) setThemeColor(t.getAttribute("data-target"), t.value);
    if (t && t.classList && t.classList.contains("js-cap")) setCapColor(t.getAttribute("data-id"), t.value);
    if (t && t.classList && t.classList.contains("js-page")) setPageCap(t.getAttribute("data-page"), t.value);
    if (t && t.classList && t.classList.contains("js-capall")) setCapAll(t.value);
    if (t && t.classList && t.classList.contains("js-own")) setOwnerColor(t.getAttribute("data-who") || "me", t.value);
    if (t && t.classList && t.classList.contains("js-bday")) updateBdayRow(t);
  });

  /* 파일 선택 → 프로필 사진 (동그란 아바타) */
  document.addEventListener("change", function (ev) {
    /* v21: 일정 시간을 고르고 나면 그 칸은 접고, 고른 시간만 버튼에 남겨요 (다시 누르면 또 고름) */
    if (ev.target && ev.target.classList && ev.target.classList.contains("js-evtime") && ev.target.value) {
      ev.target.hidden = true;
    }
    if (!ev.target || ev.target.id !== "avatarInput") return;
    var file = (ev.target.files || [])[0];
    if (!file) return;
    var w = ev.target.getAttribute("data-who") === "you" ? "you" : "me";
    if (!canEditAvatar(w)) { toast("프로필 사진은 " + (w === "you" ? S.couple.you : "본인") + " 폰에서 바꿀 수 있어요"); return; }
    /* v27: 바로 저장하지 않고 동그라미 가이드 화면에서 위치·확대를 맞춘 뒤 적용 */
    ev.target.value = "";
    openAvatarCrop(file, w);
  });

  /* 파일 선택 → 사진 추가 시트 */
  document.addEventListener("change", function (ev) {
    if (!ev.target || ev.target.id !== "photoInput") return;
    var files = Array.prototype.slice.call(ev.target.files || []);
    if (!files.length) return;
    openSheet(formAddPhoto(files), function (fd) {
      var album = String(fd.get("album") || "").trim() || defaultAlbum();
      var date = fd.get("date") || today;
      var title = String(fd.get("title") || "").trim();
      addPhotoFiles(files.slice(), { album: album, date: date, title: title });
    });
  });

  document.addEventListener("keydown", function (ev) {
    if (ev.key === "Escape") {
      /* v27: 사진 맞추기 화면이 열려 있으면 그것부터 닫습니다 */
      if (avCropEl()) { closeAvatarCrop(); return; }
      closeSheet();
    }
  });

  /* ------------------------------------------------------------------ boot */
  function emptyState() {
    return {
      couple: {
        me: "소영", you: "준영", since: today, fmt: "D", phrase: "함께한 지",
        colors: { me: "#9E636B", you: "#3D5C82" },
        sched: { me: "#9E636B", you: "#3D5C82", both: "#625A7F" }
      },
      link: { code: String(Math.floor(100000 + Math.random() * 900000)), connected: false, partnerCode: "" },
      auth: { out: false, email: "" },
      theme: { name: null, log: null, mode: "light" },
      events: [], todos: [], bucket: [], logs: [], expenses: [], photos: [], lists: [],
      ui: { seg: "todo", expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today }
    };
  }

  /* 저장된 사진(IndexedDB/Storage)의 주소를 받아 화면에 반영 */
  function loadPhotoUrls() {
    if (!Store || !S || !S.photos.length) return Promise.resolve();
    return Store.photos.urls(S.photos).then(function (map) {
      Object.keys(map || {}).forEach(function (id) { PHOTO_URLS[id] = map[id]; });
      if (BOOTED && current === "photo") renderPhoto();
    }).catch(function () {});
  }

  function start(store, state, opts) {
    Store = store;
    var base = state === "demo" ? seed() : (state || emptyState());
    S = normalizeState(base);
    /* v28: 앱을 새로 켜면 캘린더는 지난번에 보던 달이 아니라 오늘의 달로 열립니다 */
    syncCalToday();
    if (opts && opts.signedOut) { S.auth.out = true; S.auth.email = ""; }
    applyTheme();
    renderAll();
    BOOTED = true;
    loadPhotoUrls();
    /* v18: 잠금이 켜져 있으면 앱을 열 때 4자리 화면을 먼저 */
    if (lockOn()) showLock();
  }

  /* 상대 기기에서 바뀐 내용 반영 — v27: 조용히 다시 그립니다(토스트 없음) */
  function applyRemote(doc) {
    if (!doc) return;
    var ui = S ? S.ui : null;
    var unchanged = false;
    try { unchanged = JSON.stringify(stripUi(doc)) === JSON.stringify(stripUi(S)); } catch (e) {}
    S = normalizeState(doc);
    if (ui) S.ui = ui;
    if (unchanged) return;
    applyTheme();
    renderAll();
    loadPhotoUrls();
    /* v27: 「상대와 맞췄어요」 토스트는 띄우지 않습니다 — 바뀐 내용만 조용히 반영 */
  }
  function stripUi(doc) {
    if (!doc) return null;
    var copy = {};
    Object.keys(doc).forEach(function (k) { if (k !== "ui") copy[k] = doc[k]; });
    return copy;
  }

  function refreshToday() {
    var was = today;
    var t2 = iso(new Date());
    if (t2 === today) return;
    today = t2;
    /* v28: 앱을 켜 둔 채 날짜가 바뀌어 달이 넘어갔으면 캘린더도 새 달로 맞춰요.
       (다른 달을 보던 중이면 그 달은 그대로 둡니다) */
    if (was.slice(0, 7) !== t2.slice(0, 7) && S && S.ui && S.ui.calMonth === was.slice(0, 7)) syncCalToday();
    if (BOOTED) renderAll();
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") refreshToday();
  });

  window.TwoLogUI = {
    start: start,
    applyRemote: applyRemote,
    joinLocalHistory: joinLocalHistory,
    repairNoteGroups: repairNoteGroups,
    localReadyInfo: localReadyInfo,
    rerender: function () { if (BOOTED) { applyTheme(); renderAll(); } },
    toast: function (m) { toast(m); },
    go: go,
    loadPhotoUrls: loadPhotoUrls,
    get state() { return S; },
    get store() { return Store; }
  };
  window.__app = window.TwoLogUI;
})();

/* ============================================================================
   부팅: sync.js 에서 상태를 받아 app.js 에 건네줍니다.
     · ?demo=1  → 프로토타입 v4 의 예시 데이터로 보기 (화면 확인용)
     · 저장된 기록이 없으면 빈 상태로 시작 (이름·만난 날은 설정에서)
     · remote 모드에서 세션이 없으면 로그인 화면
   ========================================================================= */
(function () {
  "use strict";

  function clock() {
    var el = document.getElementById("clock");
    if (!el) return;
    var d = new Date();
    el.textContent = d.getHours() + ":" + String(d.getMinutes()).padStart(2, "0");
  }

  function wantsDemo() {
    try { return /[?&]demo=1\b/.test(location.search); } catch (e) { return false; }
  }

  function registerWorker() {
    if (!("serviceWorker" in navigator)) return;
    if (location.protocol !== "https:" && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") return;
    /* v17: 새 버전 서비스워커가 넘겨받으면 한 번만 새로고침 —
       홈 화면 앱이 옛 캐시(v15 등)에 머물러 화면이 안 바뀌는 문제를 막아요. */
    var hadController = !!navigator.serviceWorker.controller;
    var reloaded = false;
    navigator.serviceWorker.addEventListener("controllerchange", function () {
      if (!hadController) { hadController = true; return; }   /* 첫 설치 때는 그대로 */
      if (reloaded) return;
      reloaded = true;
      location.reload();
    });
    /* v22: sw.js 자쳴는 브라우저 HTTP 캐시를 거치지 않게(updateViaCache:"none") —
       홈 화면 앱이 예전 서비스워커에 머물러 화면이 안 바뀌는 일을 줄입니다. */
    navigator.serviceWorker.register("sw.js", { updateViaCache: "none" }).then(function (reg) {
      /* 앱을 열거나 다시 앞으로 꺼낼 때마다 새 sw.js 가 있는지 확인 */
      function check() {
        if (document.visibilityState !== "visible") return;
        reg.update().catch(function () {});
      }
      check();
      document.addEventListener("visibilitychange", function () {
        if (document.visibilityState === "visible") check();
      });
      window.addEventListener("online", check);
      window.addEventListener("pageshow", check);
    }).catch(function (e) {
      console.warn("[투로그] service worker 등록 실패", e);
    });
  }

  function boot() {
    clock();
    setInterval(clock, 30000);
    registerWorker();

    if (!window.TwoLog) {
      console.error("[투로그] sync.js 를 불러오지 못했어요");
      return;
    }

    var store = window.TwoLog.createStore();
    window.TwoLogStore = store;
    var demo = wantsDemo();

    store.load().then(function (state) {
      return store.auth.session().then(function (session) {
        return { state: state, session: session };
      }).catch(function () { return { state: state, session: { signedIn: false } }; });
    }).then(function (res) {
      if (demo) {
      /* 예시 화면: 진짜 기록을 건드리지 않도록 저장을 잠급니다 */
      store.persist = function () {};
      store.flush = function () { return Promise.resolve(false); };
    }
    var signedOut = store.mode === "remote" && !(res.session && res.session.signedIn);
      var state = demo ? "demo" : res.state;
      if (signedOut && !demo) {
        window.TwoLogUI.start(store, state || null, { signedOut: true });
      } else {
        window.TwoLogUI.start(store, state, {});
      }
      if (res.session && res.session.email && window.TwoLogUI.state) {
        window.TwoLogUI.state.auth.email = res.session.email;
      }
      if (!demo && store.mode === "remote") {
        store.onRemote(function (doc) { window.TwoLogUI.applyRemote(doc); });
      }
      window.TwoLogUI.loadPhotoUrls();
      /* v26: 로그인된 기기에 예전 로컬 기록이 남아 있으면 한 번 자동으로 이어 옵니다
         v27: 이어 오기를 마친 뒤, v26 에서 카드 정보 없이 올라간 노트 카드를 한 번 되살립니다 */
      if (!demo && !signedOut) {
        window.TwoLogUI.joinLocalHistory().then(function () { window.TwoLogUI.repairNoteGroups(); });
      }
    }).catch(function (e) {
      console.error("[투로그] 시작하지 못했어요", e);
      window.TwoLogUI.start(store, demo ? "demo" : null, {});
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
