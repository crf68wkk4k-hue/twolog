
(function () {
  "use strict";

  /* ------------------------------------------------------------------ utils */
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
    gear: svg('<path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h11M19 17h1"/><circle cx="15" cy="7" r="1.9"/><circle cx="9" cy="12" r="1.9"/><circle cx="17.5" cy="17" r="1.9"/>', 21)
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
      couple: { me: "소영", you: "준영", since: addDays(t, -365), fmt: "D", phrase: "함께한 지", colors: { me: "#F7C6D4", you: "#BCE0F7" }, sched: { me: "#F7C6D4", you: "#BCE0F7", both: "#D6C5F7" } },
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
        { id: uid(), kind: "movie", title: "화양연화", rating: 4.5, date: addDays(t, -7), review: "다시 봐도 여운이 오래 남는 색감." },
        { id: uid(), kind: "food", title: "성수 파스타", rating: 4, date: addDays(t, -3), review: "트러플 크림은 꼭. 웨이팅 30분." },
        { id: uid(), kind: "movie", title: "그대들은 어떻게 살 것인가", rating: 5, date: addDays(t, -20), review: "같이 보고 한참 얘기했다." }
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
  ["todo", "bucket", "log"].forEach(function (k) {
    if (!S.note[k] || typeof S.note[k] !== "object") S.note[k] = {};
    if (typeof S.note[k].e !== "string" || !S.note[k].e) S.note[k].e = NOTE_DEF[k].e;
    if (typeof S.note[k].n !== "string" || !S.note[k].n) S.note[k].n = NOTE_DEF[k].n;
  });
  if (S.couple.fmt !== "Y") S.couple.fmt = "D";
  if (typeof S.couple.phrase !== "string" || !S.couple.phrase.trim()) S.couple.phrase = defaultPhrase();
  if (!S.mig.phrase) {
    if (S.couple.phrase === "함께한 지") S.couple.phrase = defaultPhrase();
    S.mig.phrase = 1;
  }
  if (!S.couple.colors || typeof S.couple.colors !== "object") S.couple.colors = {};
  if (!S.couple.pics || typeof S.couple.pics !== "object") S.couple.pics = {};
  if (!("me" in S.couple.colors)) S.couple.colors.me = "#F7C6D4";
  if (!("you" in S.couple.colors)) S.couple.colors.you = "#BCE0F7";
  if (!S.couple.sched || typeof S.couple.sched !== "object") S.couple.sched = {};
  ["me", "you", "both"].forEach(function (k) {
    if (!S.couple.sched[k]) S.couple.sched[k] = SCHED_DEFAULT[k];
  });
  if (!S.link || typeof S.link !== "object") S.link = { code: "371502", connected: true, partnerCode: "" };
  if (!/^\d{6}$/.test(String(S.link.code || ""))) S.link.code = "371502";
  if (!("connected" in S.link)) S.link.connected = true;
  if (!S.auth || typeof S.auth !== "object") S.auth = { out: false };
  if (!Array.isArray(S.lists)) S.lists = [];
  S.events.forEach(function (e) {
    if (e.who !== "me" && e.who !== "you" && e.who !== "both") e.who = "both";
    /* 예전 한 칸짜리 일정은 종료일 = 시작일 */
    var st = String(e.date || "").slice(0, 10);
    if (!e.date || !/^\d{4}-\d{2}-\d{2}$/.test(st)) e.date = today;
    if (!e.endDate || !/^\d{4}-\d{2}-\d{2}$/.test(String(e.endDate)) || String(e.endDate) < String(e.date)) e.endDate = e.date;
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

  /* ------------------------------------------------------------------ color theme */
  var PALETTE = [
    { n: "코랄", c: "#D96B52" }, { n: "세이지", c: "#5F6F65" }, { n: "잉크", c: "#1C1C1E" }, { n: "코코아", c: "#8C7B6B" },
    { n: "네이비", c: "#3F5C74" }, { n: "플럼", c: "#7A5A72" }, { n: "머스터드", c: "#B08341" }, { n: "로즈", c: "#C4737F" }
  ];
  var SOFT = [
    { n: "핑크", c: "#F7C6D4" }, { n: "스카이", c: "#BCE0F7" }, { n: "라벤더", c: "#D6C5F7" }, { n: "민트", c: "#C8E9D5" },
    { n: "버터", c: "#F8E6A8" }, { n: "피치", c: "#FAD4C0" }, { n: "라임", c: "#DDEBC0" }, { n: "로즈", c: "#EFD3DC" }
  ];
  var SCHED_DEFAULT = { me: "#F7C6D4", you: "#BCE0F7", both: "#D6C5F7" };
  /* 일정·프로필 색 팔레트 (12색) */
  var OWNER_COLORS = ["#E8849B", "#D96B52", "#E9A87C", "#C9A227", "#8A9A5B", "#5F6F65",
    "#6FBF9B", "#5B9BC9", "#3F5C74", "#8E7CC3", "#8C7B6B", "#3A3A3E"];
  function inkOn(hex) {
    var h = String(hex || "").replace("#", "");
    if (h.length === 3) h = h.charAt(0) + h.charAt(0) + h.charAt(1) + h.charAt(1) + h.charAt(2) + h.charAt(2);
    if (!/^[0-9a-fA-F]{6}$/.test(h)) return "#111111";
    var n = parseInt(h, 16);
    var lin = function (c) { return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); };
    var L = 0.2126 * lin(((n >> 16) & 255) / 255) + 0.7152 * lin(((n >> 8) & 255) / 255) + 0.0722 * lin((n & 255) / 255);
    return L > 0.5 ? "#111111" : "#FFFFFF";
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
  function colorPickRow(who) {
    var cur = String(sched(who) || "").toUpperCase();
    var h = '<div class="own-block"><div class="own-hd"><span class="own-nm">' + esc(schedName(who)) + "</span>" +
      '<span class="own-chip" style="background:' + cur + '"></span>' +
      '<label class="own-pick"><input type="color" class="js-own" data-who="' + who + '" value="' + (cur || "#D96B52") + '"><span>직접 고르기</span></label></div>';
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
  /* 노트 기본 탭 이름 — 설정에서 바꿀 수 있어요 */
  var NOTE_DEF = { todo: { e: "📝", n: "메모" }, bucket: { e: "🎯", n: "버킷리스트" }, log: { e: "🎬", n: "영화·먹방" } };
  function pageCap(page) {
    var v = ((S.theme || {}).pages || {})[page];
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

  function setThemeColor(target, color) {
    if (target !== "name" && target !== "log") return;
    S.theme = S.theme || { name: null, log: null };
    S.theme[target] = color ? String(color).toLowerCase() : null;
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

  var BI = {
    todo: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3.6 5.2h3.2v3.2H3.6zM9.8 6.8h10.6M3.6 15.2h3.2v3.2H3.6zM9.8 16.8h10.6"/></svg>',
    cal: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3.6" y="5.4" width="16.8" height="15"/><path d="M8.2 3.4v3.4M15.8 3.4v3.4M3.6 10.2h16.8"/></svg>',
    photo: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3.4" y="4.6" width="17.2" height="14.8"/><path d="M4.2 17.2l4.4-4.3 2.6 2.4 3-2.7 5.6 5"/></svg>',
    heart: '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9"><path d="M12 20.3 5 13.2a4.6 4.6 0 0 1 6.5-6.5l.5.5.5-.5a4.6 4.6 0 0 1 6.5 6.5z"/></svg>'
  };

  function bktStatus(b) {
    if (b.done) return { t: "완료", k: "done" };
    return b.status === "doing" ? { t: "진행 중", k: "doing" } : { t: "미완료", k: "todo" };
  }

  function renderHome() {
    var c = S.couple;
    var dday = Math.max(0, diffDays(c.since, today));
    var dl = ddayLabel(dday);
    var ann = nextAnniversary();
    var todayEvents = S.events.filter(function (e) { return evCovers(e, today); }).sort(byTimeAsc);
    var upcoming = S.events.filter(function (e) { return evStart(e) > today; }).sort(byDateAsc).slice(0, 3);
    var ym = today.slice(0, 7);
    var monthNo = Number(ym.slice(5, 7));
    var logs = S.logs.slice().sort(byDateDesc).slice(0, 2);

    /* ---- figures for {month}월의 우리 ---- */
    var todoTotal = S.todos.length, todoDone = S.todos.filter(function (t) { return t.done; }).length;
    S.lists.forEach(function (l) {
      if (l.kind !== "check") return;
      todoTotal += l.items.length;
      todoDone += l.items.filter(function (i) { return i.done; }).length;
    });
    var todoLeft = Math.max(0, todoTotal - todoDone);
    var todoPct = todoTotal ? Math.round(todoDone / todoTotal * 1000) / 10 : 0;

    var monthEvents = S.events.filter(function (e) { return e.date.slice(0, 7) === ym; });
    var typeCount = {};
    monthEvents.forEach(function (e) { typeCount[e.type] = (typeCount[e.type] || 0) + 1; });
    var typeKeys = Object.keys(TYPE).filter(function (k) { return typeCount[k]; })
      .sort(function (a, b) { return typeCount[b] - typeCount[a]; });
    var typeLine = typeKeys.slice(0, 2).map(function (k) { return TYPE[k].label + " " + typeCount[k]; }).join(" · ");
    if (typeKeys.length > 2) typeLine += " · 외 " + (typeKeys.length - 2);
    var monthPhotos = S.photos.filter(function (p) { return p.date.slice(0, 7) === ym; }).length;
    var monthLogs = S.logs.filter(function (l) { return String(l.date || "").slice(0, 7) === ym; }).length;
    var pastEvents = monthEvents.filter(function (e) { return e.date < today; }).length;
    var memories = monthLogs + pastEvents;

    var bktTop = S.bucket.slice().sort(function (a, b) {
      var rank = function (x) { return x.done ? 2 : x.status === "doing" ? 0 : 1; };
      return rank(a) - rank(b);
    }).slice(0, 3);

    var html = "";
    var nmOn = S.theme && S.theme.name;
    html += '<div class="brand' + capCls("home") + '"' + capStyle("home") + ' data-pg="home"><span class="mark"><i></i><i></i></span><b>투로그</b><span class="bw">(twolog)</span>' +
      '<span class="who' + (nmOn ? " tinted" : "") + '">' + esc(c.me) + " · " + esc(c.you) + "</span>" +
      '<button class="icon-btn pal" data-act="toggleMode" aria-label="' + modeLabel() + '" title="' + modeLabel() + '">' + modeIcon() + "</button>" +
      '<button class="icon-btn pal" data-act="openTheme" aria-label="컬러 설정">' + IC.palette + "</button></div>";

    /* ---- 1. D-day ---- */
    /* 위 라벨: 「소영과 준영이 함께한 지」 — 날짜 없이 두 이름과 문구만 */
    html += '<div class="dday" data-act="editDday"><div class="dday-top"><span class="eyebrow">' +
      esc(ddayPhrase()) + "</span>" +
      '<button class="icon-btn" data-act="editDday" aria-label="기념일 수정">' + IC.pencil + "</button></div>" +
      '<div class="dday-num' + (dl.compact ? " compact" : "") + '">' + dl.text + "</div>" +
      (ann ? '<div class="chip-row"><span class="chip coral">' + ann.n + "주년 " + (ann.days === 0 ? "오늘" : "D-" + ann.days) + "</span></div>" : "") +
      "</div>";

    /* ---- 3. {month}월의 우리 dashboard ---- */
    html += '<div class="sec"><h2>🗓️ ' + monthNo + '월의 우리</h2><span class="more">' + ym.replace("-", ".") + "</span></div>";
    html += '<div class="pad">';
    html += '<div class="bento">';

    html += '<div class="bcard"><div class="bcard-hd"><span class="bi">' + BI.todo + '</span><span class="lb">TO-DO</span></div>' +
      '<div class="bm">' + todoDone + " / " + todoTotal + "</div>" +
      '<div class="bs">' + esc(noteTab("todo").n) + " 완료</div>" +
      '<div class="bbar"><i style="width:' + todoPct + '%"></i></div></div>';

    html += '<div class="bcard"><div class="bcard-hd"><span class="bi">' + BI.cal + '</span><span class="lb">SCHEDULE</span></div>' +
      '<div class="bm">' + monthEvents.length + "<em>개</em></div>" +
      '<div class="bs">이번 달 일정</div>' +
      (typeLine ? '<div class="bx">' + esc(typeLine) + "</div>" : "") + "</div>";

    html += '<div class="bcard"><div class="bcard-hd"><span class="bi">' + BI.photo + '</span><span class="lb">PHOTO</span></div>' +
      '<div class="bm">' + monthPhotos + "<em>장</em></div>" +
      '<div class="bs">이번 달 사진</div></div>';

    html += '<div class="bcard"><div class="bcard-hd"><span class="bi">' + BI.heart + '</span><span class="lb">MEMORY</span></div>' +
      '<div class="bm">' + memories + "<em>개</em></div>" +
      '<div class="bs">함께한 추억</div></div>';

    html += "</div>";

    html += '<div class="mblocks">';

    html += '<div class="mblock"><h3>🎯 이번 달 버킷리스트</h3>';
    if (bktTop.length) {
      bktTop.forEach(function (b) {
        var st = bktStatus(b);
        html += '<div class="bitem"><span class="t">' + esc(b.title) + '</span><span class="btag ' + st.k + '">' + st.t + "</span></div>";
      });
    } else {
      html += '<div class="empty" style="padding:14px 0 0;text-align:left">아직 담은 버킷이 없어요.</div>';
    }
    html += "</div>";

    html += '<div class="mblock"><div class="mbhd"><h3 class="tint-h">' + esc(noteLabel("log")) + "</h3>" +
      '<button class="sw-btn" data-act="openTheme" aria-label="최근 기록 색 선택"></button></div>';
    if (logs.length) {
      logs.forEach(function (l) {
        html += '<div class="lrow"><div class="lbody">' +
          '<div class="lt"><span class="tag ' + l.kind + '">' + (l.kind === "movie" ? "영화" : "먹방") + "</span>" + esc(l.title) + "</div>" +
          '<div class="lm">' + l.date.replace(/-/g, ".") + (l.review ? " · " + esc(l.review) : "") + "</div></div>" +
          '<div class="lstar">' + stars(l.rating) + "</div></div>";
      });
    } else { html += '<div class="empty" style="padding:14px 0 0;text-align:left">아직 기록이 없어요.</div>'; }
    html += '<div class="wrap20" style="padding:12px 0 0"><button class="ghost" data-act="navSeg" data-screen="diary" data-seg="log">' + esc(noteLabel("log")) + " 전체 보기</button></div></div>";

    html += "</div></div>";

    /* ---- 4. upcoming ---- */
    var sched = [];
    todayEvents.slice(0, 2).forEach(function (e) {
      sched.push({ e: e, left: "오늘", meta: (TYPE[e.type] || TYPE.etc).label + (evRange(e) ? " · " + evRange(e) : "") });
    });
    upcoming.slice(0, 3).forEach(function (e) {
      var d = parse(evStart(e));
      sched.push({ e: e, left: (d.getMonth() + 1) + "/" + d.getDate(), meta: (TYPE[e.type] || TYPE.etc).label + (evRange(e) ? " · " + evRange(e) : "") + " · D-" + diffDays(today, evStart(e)) });
    });
    sched = sched.slice(0, 4);

    html += '<div class="sec"><h2>📅 다가오는 일정</h2><span class="more">' + (todayEvents.length + upcoming.length) + "개</span></div>";
    html += '<div class="pad"><div class="list">';
    if (sched.length) {
      sched.forEach(function (s) {
        html += '<div class="row"><span class="sched-d">' + s.left + "</span>" +
          '<div class="body"><div class="t">' + esc(s.e.title) + "</div>" +
          '<div class="m"><span class="dot-type t-' + s.e.type + '"></span>' + s.meta + "</div></div></div>";
      });
    } else { html += '<div class="empty">예정된 일정이 없어요.</div>'; }
    html += "</div></div>";

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
      return '<div class="who-row">' + avSquare("me") + avSquare("you") +
        '<span class="wname">' + esc(S.couple.me) + " " + esc(S.couple.you) + "</span></div>";
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
  function evRange(e) {
    var st = evStart(e), en = evEnd(e);
    if (st === en) return "";
    var f = function (x) { return Number(x.slice(5, 7)) + "." + Number(x.slice(8, 10)); };
    return f(st) + " ~ " + f(en);
  }

  function renderCal() {
    var cur = S.ui.calMonth || today.slice(0, 7);
    var y = Number(cur.slice(0, 4)), m = Number(cur.slice(5, 7)) - 1;
    var first = new Date(y, m, 1), startDow = first.getDay(), daysIn = new Date(y, m + 1, 0).getDate();
    var sel = S.ui.selDate || today;
    var monthStart = cur + "-01", monthEnd = ymd(y, m, daysIn);

    var html = "";
    html += '<header class="hdr' + capCls("cal") + '"' + capStyle("cal") + ' data-pg="cal"><div><h1><span class="eh">🗓️</span> 캘린더</h1></div>' +
      '<button class="round-btn" data-act="addEvent" aria-label="일정 추가">' + IC.plus + "</button></header>";

    html += '<div class="cal"><div class="cal-head"><div class="cal-month">' + y + "년 " + (m + 1) + "월</div>" +
      '<div class="cal-nav"><button data-act="calPrev" aria-label="이전 달">' + IC.left + "</button>" +
      '<button data-act="calNext" aria-label="다음 달">' + IC.right + "</button></div></div>";

    html += '<div class="cal-week"><span>일</span><span>월</span><span>화</span><span>수</span><span>목</span><span>금</span><span>토</span></div>';

    /* 날짜 칸을 7일씩 주 단위로 나눕니다 */
    var cells = [];
    for (var i0 = 0; i0 < startDow; i0++) cells.push("");
    for (var d = 1; d <= daysIn; d++) cells.push(ymd(y, m, d));
    while (cells.length % 7) cells.push("");

    var monthEvents = S.events.filter(function (e) {
      return evEnd(e) >= monthStart && evStart(e) <= monthEnd;
    });

    var LANE_H = 17, TOP_H = 26, ROW_MIN = 62;
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
      var rowsH = Math.max(ROW_MIN, TOP_H + lanes.length * LANE_H + 8);

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
        html += '<button class="' + cls + '" data-act="pickDay" data-date="' + ds2 + '"><span class="dnum">' +
          Number(ds2.slice(8, 10)) + "</span></button>";
      }
      html += "</div>";
      if (bars.length) {
        html += '<div class="cal-bars">';
        bars.forEach(function (b) {
          var left = b.sCol / 7 * 100, width = (b.eCol - b.sCol + 1) / 7 * 100;
          var top = TOP_H + b.lane * LANE_H;
          var edge = sched(evWho(b.e));
          html += '<span class="ebar' + (b.openL ? " openl" : "") + (b.openR ? " openr" : "") +
            '" style="left:' + left + "%; width:" + width + "%; top:" + top + "px; background:" + edge +
            "; color:" + inkOn(edge) + '">' + esc(b.e.title) + "</span>";
        });
        html += "</div>";
      }
      html += "</div>";
    }
    html += "</div></div>";

    /* 선택한 날: 기간이 걸치는 일정 모두 */
    var selEvents = S.events.filter(function (e) { return evCovers(e, sel); })
      .sort(function (a, b) {
        return evStart(a) < evStart(b) ? -1 : evStart(a) > evStart(b) ? 1 : (a.title < b.title ? -1 : 1);
      });
    var sd = parse(sel);
    var selHol = holName(sel);
    html += '<div class="daypanel"><div class="daypanel-hd"><div class="d">' + (sd.getMonth() + 1) + "월 " + sd.getDate() + "일<em>" + WD[sd.getDay()] + "요일</em>" +
      (selHol ? '<span class="hol-badge">' + esc(selHol) + "</span>" : "") + "</div>" +
      '<span class="more" style="font-size:11.5px;color:var(--ink-3)">' + selEvents.length + "개</span></div>";
    html += '<div class="daylist">';
    if (selEvents.length) {
      selEvents.forEach(function (e) {
        var rng = evRange(e);
        var t = TYPE[e.type] || TYPE.etc;
        html += '<div class="ev"><span class="bar" style="background:' + sched(evWho(e)) + '"></span>' +
          '<div class="body">' + whoRow(e) + '<div class="t">' + esc(e.title) + "</div>" +
          '<div class="m">' + (rng ? "<span>" + rng + "</span><span>·</span>" : "") + "<span>" + t.label + "</span></div></div>" +
          '<button class="x" data-act="delEvent" data-id="' + e.id + '" aria-label="삭제">' + IC.x + "</button></div>";
      });
    } else {
      html += '<div class="empty">이 날은 아직 비어 있어요.</div>';
    }
    html += "</div>";
    html += '<div class="wrap20" style="padding:12px 0 0"><button class="ghost" data-act="addEvent">' + IC.plus + " 일정 추가</button></div>";
    html += "</div>";
    html += '<div style="height:24px"></div>';

    $("#s-cal").innerHTML = html;
  }

  /* ------------------------------------------------------------------ note */
  var NOTE_BASE = ["todo", "bucket", "log"];

  function noteTab(k) {
    var v = (S.note || {})[k] || {};
    var d = NOTE_DEF[k];
    return {
      e: typeof v.e === "string" && v.e ? v.e : d.e,
      n: typeof v.n === "string" && v.n ? v.n : d.n
    };
  }
  function noteLabel(k) { var t = noteTab(k); return t.e + " " + t.n; }

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
    html += '<header class="hdr' + capCls("diary") + '"' + capStyle("diary") + ' data-pg="diary"><div><h1><span class="eh">📖</span> 노트</h1><p class="sub">함께 쌓는 우리 기록</p></div>' +
      '<div class="hdr-acts"><button class="round-btn" data-act="noteSettings" aria-label="노트 설정">' + IC.gear + "</button></div></header>";
    html += '<div class="seg">';
    NOTE_BASE.forEach(function (k) { html += segBtn(seg, k, noteLabel(k)); });
    html += "</div>";
    if (S.lists.length) {
      html += '<div class="lstbar"><div class="lst-scroll">';
      S.lists.forEach(function (l) {
        var on = seg === "list:" + l.id;
        html += '<button class="lchip' + (on ? " active" : "") + '" data-act="seg" data-seg="list:' + l.id + '" aria-label="' + esc(l.title) + '">' +
          '<span class="le">' + esc(l.emoji || "📌") + "</span><span>" + esc(l.title) + "</span></button>";
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

    var act = $("#s-diary .lchip.active") || $("#s-diary .seg-btn.active");
    if (act && act.scrollIntoView) {
      try { act.scrollIntoView({ block: "nearest", inline: "center" }); } catch (e) {}
    }
  }

  function viewList(l) {
    if (!l) return '<div class="list" style="margin:0 20px"><div class="empty">리스트를 찾을 수 없어요.</div></div>';
    var h = '<div class="note-hd"><div class="nh-l"><span class="t">' + esc((l.emoji || "📌") + " " + l.title) + "</span>" +
      '<span class="k">' + (l.kind === "memo" ? "메모" : "체크") + "</span></div></div>";

    if (l.kind === "memo") {
      h += '<div class="list" style="margin:0 20px">';
      if (!l.items.length) h += '<div class="empty">메모를 남겨 보세요.</div>';
      l.items.forEach(function (it) {
        h += '<div class="memo-row"><div class="body" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '"><div class="note-memo">' + esc(it.text) + "</div></div>" +
          '<button class="edit-ic" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="수정">' + IC.pencil + "</button>" +
          '<button class="x" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="삭제">' + IC.x + "</button></div>";
      });
      h += "</div>";
    } else {
      var done = l.items.filter(function (i) { return i.done; }).length;
      var pct = l.items.length ? Math.round(done / l.items.length * 100) : 0;
      h += '<div class="progress"><span class="n">' + done + " / " + l.items.length + ' 완료</span><span class="bar"><i style="width:' + pct + '%"></i></span></div>';
      h += '<div class="list" style="margin:0 20px">';
      if (!l.items.length) h += '<div class="empty">아래에 첫 항목을 적어 보세요.</div>';
      l.items.forEach(function (it) {
        h += '<div class="row todo' + (it.done ? " done" : "") + '">' +
          '<button class="check" data-act="toggleListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="완료 표시">' + IC.check + "</button>" +
          '<div class="body" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '"><div class="t">' + esc(it.text) + "</div></div>" +
          '<button class="edit-ic" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="수정">' + IC.pencil + "</button>" +
          '<button class="x" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="삭제">' + IC.x + "</button></div>";
      });
      h += "</div>";
    }

    h += '<form class="qadd" id="qaddForm" data-kind="list:' + l.id + '">' +
      (l.kind === "memo"
        ? '<textarea class="field qfield" name="text" id="qaddInput" rows="2" placeholder="메모를 적고 추가를 눌러 주세요"></textarea>'
        : '<input class="field qfield" name="text" id="qaddInput" placeholder="항목을 적고 추가를 눌러 주세요" autocomplete="off">') +
      '<button class="qbtn" type="submit" aria-label="추가">' + IC.plus + "추가</button></form>";
    return h;
  }

  function viewTodo() {
    var done = S.todos.filter(function (t) { return t.done; }).length;
    var pct = S.todos.length ? Math.round(done / S.todos.length * 100) : 0;
    var h = '<div class="progress"><span class="n">' + done + " / " + S.todos.length + ' 완료</span><span class="bar"><i style="width:' + pct + '%"></i></span></div>';
    h += '<div class="list" style="margin:0 20px">';
    if (!S.todos.length) h += '<div class="empty">' + esc(noteTab("todo").n) + "를 추가해 보세요.</div>";
    S.todos.forEach(function (t) {
      var whoCls = t.who === "나" ? "me" : t.who === S.couple.you ? "you" : "";
      h += '<div class="row todo' + (t.done ? " done" : "") + '">' +
        '<button class="check" data-act="toggleTodo" data-id="' + t.id + '" aria-label="완료 표시">' + IC.check + "</button>" +
        '<div class="body" data-act="editTodo" data-id="' + t.id + '"><div class="t">' + esc(t.text) + "</div></div>" +
        '<span class="who ' + whoCls + '">' + esc(t.who) + "</span>" +
        '<button class="edit-ic" data-act="editTodo" data-id="' + t.id + '" aria-label="수정">' + IC.pencil + "</button></div>";
    });
    h += "</div>";
    h += '<form class="qadd" id="qaddForm" data-kind="todo">' +
      '<input class="field qfield" name="text" id="qaddInput" placeholder="' + esc(noteTab("todo").n) + '를 적고 추가" autocomplete="off">' +
      '<select class="field qsel" name="sub" aria-label="담당">' + whoOpts("함께") + "</select>" +
      '<button class="qbtn" type="submit" aria-label="추가">' + IC.plus + "추가</button></form>";
    return h;
  }

  function viewBucket() {
    var done = S.bucket.filter(function (b) { return b.done; }).length;
    var h = '<div class="progress"><span class="n">' + done + " / " + S.bucket.length + ' 달성</span><span class="bar"><i style="width:' +
      (S.bucket.length ? Math.round(done / S.bucket.length * 100) : 0) + '%"></i></span></div>';
    h += '<div class="list" style="margin:0 20px">';
    if (!S.bucket.length) h += '<div class="empty">버킷리스트를 추가해 보세요.</div>';
    S.bucket.forEach(function (b) {
      h += '<div class="bkt' + (b.done ? " done" : "") + '"><div class="body" data-act="editBucket" data-id="' + b.id + '"><div class="t">' + esc(b.title) + "</div>" +
        '<div class="cat">' + esc(b.cat) + "</div></div>" +
        '<button class="toggle' + (b.done ? " on" : "") + '" data-act="toggleBucket" data-id="' + b.id + '">' + (b.done ? "완료" : "예정") + "</button>" +
        '<button class="edit-ic" data-act="editBucket" data-id="' + b.id + '" aria-label="수정">' + IC.pencil + "</button></div>";
    });
    h += "</div>";
    h += '<form class="qadd" id="qaddForm" data-kind="bucket">' +
      '<input class="field qfield" name="text" id="qaddInput" placeholder="하고 싶은 것을 적고 추가" autocomplete="off">' +
      '<select class="field qsel" name="sub" aria-label="카테고리"><option>여행</option><option>맛집</option><option>취미</option><option>기타</option></select>' +
      '<button class="qbtn" type="submit" aria-label="추가">' + IC.plus + "추가</button></form>";
    return h;
  }

  function viewLog() {
    var items = S.logs.slice().sort(byDateDesc);
    var h = '<div class="list" style="margin:0 20px">';
    if (!items.length) h += '<div class="empty">영화나 맛집 기록을 남겨 보세요.</div>';
    items.forEach(function (l) {
      h += '<div class="log"><div class="body" data-act="editLog" data-id="' + l.id + '"><div class="top"><span class="tag ' + l.kind + '">' + (l.kind === "movie" ? "영화" : "먹방") + "</span>" +
        '<span class="t">' + esc(l.title) + "</span></div>" +
        '<div class="rev">' + esc(l.review || "") + "</div>" +
        '<div class="meta">' + stars(l.rating) + "<span>" + Number(l.rating).toFixed(1) + "</span><span>·</span><span>" + l.date.replace(/-/g, ".") + "</span></div></div>" +
        '<button class="edit-ic" data-act="editLog" data-id="' + l.id + '" aria-label="수정">' + IC.pencil + "</button>" +
        '<button class="x" data-act="delLog" data-id="' + l.id + '" aria-label="삭제" style="width:24px;height:24px;display:flex;align-items:center;justify-content:center;color:#CFCFCA">' + IC.x + "</button></div>";
    });
    h += "</div>";
    h += '<form class="qadd" id="qaddForm" data-kind="log">' +
      '<input class="field qfield" name="text" id="qaddInput" placeholder="영화·맛집 이름을 적고 추가" autocomplete="off">' +
      '<select class="field qsel" name="sub" aria-label="종류"><option value="movie">영화</option><option value="food">먹방</option></select>' +
      '<button class="qbtn" type="submit" aria-label="추가">' + IC.plus + "추가</button></form>";
    return h;
  }

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

  function renderPhoto() {
    var h = '<header class="hdr' + capCls("photo") + '"' + capStyle("photo") + ' data-pg="photo"><div><h1><span class="eh">🖼️</span> 사진첩</h1><p class="sub">' + S.photos.length + "장의 순간</p></div>" +
      '<div class="hdr-acts"><button class="round-btn" data-act="addPhoto" aria-label="사진 추가" title="사진 추가">' + IC.plus + "</button></div></header>";
    var groups = [];
    var map = {};
    S.photos.slice().sort(byDateDesc).forEach(function (p) {
      var k = p.album;
      if (!map[k]) { map[k] = { name: k, date: p.date, items: [] }; groups.push(map[k]); }
      map[k].items.push(p);
    });
    groups.forEach(function (g) {
      var d = parse(g.date);
      h += '<div class="album"><div class="album-hd"><span class="n">' + esc(g.name) + "</span>" +
        '<span class="c">' + (d.getFullYear()) + "." + pad(d.getMonth() + 1) + " · " + g.items.length + "장</span></div>" +
        '<div class="grid3">' +
        g.items.map(function (p) {
          return '<button class="ph" data-act="openPhoto" data-id="' + p.id + '" aria-label="' + esc(p.title || "사진") + '">' + photoImg(p) + capHtml(p, "cap") + "</button>";
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
  function openSheet(html, onSubmit) {
    personSheetWho = null;
    sheet.innerHTML = '<div class="grab"></div>' + html;
    sheetSubmit = onSubmit || null;
    sheetWrap.classList.add("open");
    sheetWrap.setAttribute("aria-hidden", "false");
    sheet.scrollTop = 0;
  }
  function closeSheet() {
    personSheetWho = null;
    sheetWrap.classList.remove("open");
    sheetWrap.setAttribute("aria-hidden", "true");
    sheetSubmit = null;
    pendingUrls.forEach(function (u) { try { URL.revokeObjectURL(u); } catch (e) {} });
    pendingUrls = [];
    pendingFiles = [];
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
    h += '<p class="sheet-sub">탭 이름과 내 리스트를 여기서 정리해요.</p>';
    h += '<form class="form" id="noteForm" style="margin-top:12px">';
    h += '<div class="set-lbl">탭 이름</div>';
    NOTE_BASE.forEach(function (k) {
      var t = noteTab(k);
      h += '<div class="nt-row">' +
        '<input class="field nt-emo" name="t_' + k + '_e" value="' + esc(t.e) + '" maxlength="4" aria-label="' + esc(t.n) + ' 이모지" autocomplete="off">' +
        '<input class="field nt-nm" name="t_' + k + '_n" value="' + esc(t.n) + '" aria-label="탭 이름" autocomplete="off">' +
        "</div>";
    });
    h += '<div class="set-lbl" style="margin-top:20px">내 리스트</div>';
    if (!S.lists.length) h += '<div class="set-hint" style="margin-top:0">아직 만든 리스트가 없어요. 아래에서 새로 만들 수 있어요.</div>';
    S.lists.forEach(function (l) {
      h += '<div class="nt-row">' +
        '<input class="field nt-emo" name="l_' + l.id + '_e" value="' + esc(l.emoji || "📌") + '" maxlength="4" aria-label="' + esc(l.title) + ' 이모지" autocomplete="off">' +
        '<input class="field nt-nm" name="l_' + l.id + '_n" value="' + esc(l.title) + '" aria-label="리스트 이름" autocomplete="off">' +
        '<button type="button" class="nt-del" data-act="delListFromNote" data-id="' + l.id + '">삭제</button></div>';
    });
    h += '<div class="nt-new"><div class="set-lbl">새 리스트</div>' +
      '<div class="nt-row">' +
      '<input class="field nt-emo" name="new_e" value="📌" maxlength="4" aria-label="새 리스트 이모지" autocomplete="off">' +
      '<input class="field nt-nm" name="new_n" placeholder="예) 여행 준비물" aria-label="새 리스트 이름" autocomplete="off">' +
      '<select class="field nt-kind" name="new_kind" aria-label="새 리스트 형식"><option value="check">체크</option><option value="memo">메모</option></select>' +
      "</div></div>";
    h += '<div style="height:14px"></div><button class="btn-primary" type="submit">저장하기</button></form>';
    h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
    return h;
  }

  function openNoteSettings() { openSheet(formNoteSettings()); }

  function formListItem(l, it) {
    var memo = !!l && l.kind === "memo";
    return sheetHead(memo ? "메모 수정" : "항목 수정") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>' + (memo ? "메모" : "항목") + "</label>" +
      (memo
        ? '<textarea class="field" name="text" rows="4" style="height:auto;padding:11px 12px;line-height:1.6;resize:none">' + esc(it.text) + "</textarea>"
        : '<input class="field" name="text" value="' + esc(it.text) + '" required autocomplete="off">') + "</div>" +
      '<button type="button" class="btn-del" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '">삭제</button>' +
      '<button class="btn-primary" type="submit">저장하기</button></form>';
  }

  function askConfirm(msg, label, onYes, title) {
    openSheet(sheetHead(title || "리스트 삭제") + '<p class="sheet-sub">' + msg + "</p>" +
      '<form class="form" id="sheetForm"><button class="btn-primary" type="submit">' + label + "</button></form>" +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">취소</button>',
      function () { closeSheet(); if (onYes) onYes(); });
  }

  function formEvent(dateStr) {
    var opts = TYPE_ORDER.map(function (k) {
      return '<option value="' + k + '">' + TYPE[k].label + "</option>";
    }).join("");
    var wopts = '<button type="button" class="wopt active" data-act="who" data-who="both">' + avSpan("me") + avSpan("you") + "함께</button>" +
      '<button type="button" class="wopt" data-act="who" data-who="me">' + avSpan("me") + esc(S.couple.me) + "</button>" +
      '<button type="button" class="wopt" data-act="who" data-who="you">' + avSpan("you") + esc(S.couple.you) + "</button>";
    return sheetHead("일정 추가") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>제목</label><input class="field" name="title" placeholder="예) 성수 데이트" required autocomplete="off"></div>' +
      '<div class="two"><div class="f"><label>시작일</label><input class="field" type="date" name="start" value="' + (dateStr || today) + '" required></div>' +
      '<div class="f"><label>종료일</label><input class="field" type="date" name="end" value="' + (dateStr || today) + '" required></div></div>' +
      '<p class="sheet-sub" style="margin-top:-2px">여러 날이면 종료일까지 달력에 색으로 이어져요.</p>' +
      '<div class="f"><label>종류</label><select class="field" name="type">' + opts + "</select></div>" +
      '<div class="f"><label>담당</label><div class="wsel" data-group="who">' + wopts + "</div>" +
      '<input type="hidden" name="who" value="both"></div>' +
      '<button class="btn-primary" type="submit">추가하기</button>' +
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
      '<div class="f"><label>담당</label><select class="field" name="who">' + whoOpts(t ? t.who : "함께") + "</select></div>" +
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
      '<div class="f"><label>상태</label><select class="field" name="done"><option value="">예정</option><option value="1"' + (b && b.done ? " selected" : "") + ">달성</option></select></div>" +
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
    return sheetHead("기념일 설정") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>기념일 문구</label><input class="field" name="phrase" value="' + esc(ddayPhrase()) + '" placeholder="소영과 준영이 함께한 지" autocomplete="off"></div>' +
      '<p class="sheet-sub" style="margin-top:-2px">홈 D-day 위에 이 문구가 그대로 보여요. 자유롭게 적어 주세요.</p>' +
      '<div class="f" style="margin-top:2px"><label>처음 만난 날</label><input class="field" type="date" name="since" value="' + c.since + '" required></div>' +
      '<div class="f"><label>D-day 표기</label><div class="seg seg-sm" data-group="fmt">' +
      '<button type="button" class="seg-btn' + (c.fmt === "Y" ? "" : " active") + '" data-act="fmt" data-fmt="D">일수로 · D+365일</button>' +
      '<button type="button" class="seg-btn' + (c.fmt === "Y" ? " active" : "") + '" data-act="fmt" data-fmt="Y">연·일로 · 1년 4일째</button>' +
      '</div><input type="hidden" name="fmt" value="' + (c.fmt === "Y" ? "Y" : "D") + '"></div>' +
      '<p style="font-size:11.5px;color:var(--ink-3);line-height:1.6;margin-top:-2px">이 날을 기준으로 D-day와 기념일을 계산해요.</p>' +
      '<button class="btn-primary" type="submit">저장하기</button></form>';
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

  function capPickRows() {
    return PAGES.map(function (p) {
      var cur = pageCap(p.k);
      var h = '<div class="cap-row" data-caprow="' + p.k + '"><span class="cap-nm">' + p.n + '</span><div class="cap-sws">';
      h += '<button type="button" class="sw none' + (!cur ? " sel" : "") + '" data-act="pickCap" data-page="' + p.k +
        '" data-color="" aria-label="' + p.n + ' 기본"></button>';
      CAP_BG.forEach(function (c) {
        h += '<button type="button" class="sw' + (cur && cur.toUpperCase() === c ? " sel" : "") + '" data-act="pickCap" data-page="' + p.k +
          '" data-color="' + c + '" style="background:' + c + '" aria-label="' + p.n + " " + c + '"></button>';
      });
      h += '</div><input type="color" class="cap-pick js-page" data-page="' + p.k + '" value="' + (cur || "#FFFFFF") +
        '" aria-label="' + p.n + ' 캡션 색 직접 고르기"></div>';
      return h;
    }).join("");
  }

  function swRow(target, cur) {
    var h = '<div class="sw-grid" data-sw="' + target + '">';
    PALETTE.forEach(function (p) {
      h += '<button class="sw' + (cur === p.c ? " sel" : "") + '" data-act="pickColor" data-target="' + target +
        '" data-color="' + p.c + '" style="background:' + p.c + '" aria-label="' + p.n + ' ' + p.c + '"></button>';
    });
    return h + "</div>";
  }

  function cpBlock(title, target, cur) {
    return '<div class="cp"><div class="cp-hd"><span>' + title + '</span><span class="cp-val" data-val="' + target + '">' +
      (cur ? cur.toUpperCase() : "기본") + "</span></div>" + swRow(target, cur) +
      '<div class="cp-foot"><label class="cp-pick"><input type="color" class="js-color" data-target="' + target + '" value="' +
      (cur || "#D96B52") + '"><span>직접 고르기</span></label>' +
      '<button class="cp-reset' + (cur ? "" : " on") + '" data-act="pickColor" data-target="' + target + '" data-color="">기본</button></div></div>';
  }

  function formTheme() {
    var t = S.theme || {};
    var dark = t.mode === "dark";
    return sheetHead("설정") +
      '<p class="sheet-sub">화면 밝기와 이름·최근 기록 색을 골라 주세요.</p>' +
      '<div class="cp"><div class="cp-hd"><span>화면</span><span class="cp-val">' + (dark ? "다크" : "라이트") + '</span></div>' +
      '<div class="seg seg-sm" data-group="mode">' +
      '<button type="button" class="seg-btn' + (dark ? "" : " active") + '" data-act="mode" data-mode="light">라이트</button>' +
      '<button type="button" class="seg-btn' + (dark ? " active" : "") + '" data-act="mode" data-mode="dark">다크</button>' +
      "</div></div>" +
      cpBlock("이름", "name", t.name) +
      cpBlock("최근 기록", "log", t.log) +
      '<p class="cp-note">고른 색은 바로 적용되고, 앱을 다시 열어도 그대로 남아 있어요. ‘기본’으로 두면 원래 색으로 돌아가요.</p>' +
      '<button class="btn-primary" data-close="1">완료</button>';
  }

  function syncThemeSheet() {
    if (!sheet) return;
    var modeGroup = sheet.querySelector('[data-group="mode"]');
    if (modeGroup) {
      var dk = (S.theme || {}).mode === "dark";
      modeGroup.querySelectorAll(".seg-btn").forEach(function (b) {
        b.classList.toggle("active", (b.getAttribute("data-mode") === "dark") === dk);
      });
      var mv = sheet.querySelector('.cp .cp-val');
      if (mv) mv.textContent = dk ? "다크" : "라이트";
    }
    ["name", "log"].forEach(function (t) {
      var cur = (S.theme || {})[t] || "";
      var val = sheet.querySelector('.cp-val[data-val="' + t + '"]');
      if (val) val.textContent = cur ? cur.toUpperCase() : "기본";
      var row = sheet.querySelector('.sw-grid[data-sw="' + t + '"]');
      if (row) row.querySelectorAll(".sw").forEach(function (b) {
        b.classList.toggle("sel", (b.getAttribute("data-color") || "") === cur);
      });
      var rb = sheet.querySelector('.cp-reset[data-target="' + t + '"]');
      if (rb) rb.classList.toggle("on", !cur);
      var inp = sheet.querySelector('.js-color[data-target="' + t + '"]');
      if (inp && cur && inp.value !== cur) inp.value = cur;
    });
  }

  /* ------------------------------------------------------------------ photo detail */
  function openPhoto(id) {
    var p = S.photos.filter(function (x) { return x.id === id; })[0];
    if (!p) return;
    var d = parse(p.date);
    var cur = p.capBg || "";
    var sw = '<div class="sw-grid" data-sw="cap">';
    CAP_PALETTE.forEach(function (c) {
      sw += '<button class="sw' + (cur === c.c ? " sel" : "") + '" data-act="pickCap" data-id="' + p.id +
        '" data-color="' + c.c + '" style="background:' + c.c + '" aria-label="' + c.n + ' ' + c.c + '"></button>';
    });
    sw += "</div>";
    var html = '<div class="sheet-hd"><h2>' + esc(p.title || p.album || "사진") + '</h2><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>" +
      '<div class="pdetail">' + photoImg(p, true) +
      capHtml(p, "pd-cap") + "</div>" +
      '<div style="margin-top:14px">' +
      '<div style="font-size:13.5px;font-weight:600;letter-spacing:-.02em">' + esc(p.album) + "</div>" +
      '<div style="font-size:11.5px;color:var(--ink-3);margin-top:3px">' + d.getFullYear() + "." + pad(d.getMonth() + 1) + "." + pad(d.getDate()) + (p.place ? " · " + esc(p.place) : "") + "</div></div>" +
      (p.memo ? '<p style="margin-top:14px;font-size:12.5px;color:var(--ink-2);line-height:1.65">' + esc(p.memo) + "</p>" : "") +
      '<div class="photo-tools"><button class="set-btn" data-act="photoEdit" data-id="' + p.id + '">정보 수정</button>' +
      '<button class="set-btn warn" data-act="photoDelete" data-id="' + p.id + '">삭제</button></div>' +
      '<div class="cp"><div class="cp-hd"><span>캡션 바탕색</span><span class="cp-val" data-capval="' + p.id + '">' +
      (p.capBg ? p.capBg.toUpperCase() : "기본") + "</span></div>" + sw +
      '<div class="cp-foot"><label class="cp-pick"><input type="color" class="js-cap" data-id="' + p.id + '" value="' + capBg(p) + '"><span>직접 고르기</span></label>' +
      '<button class="cp-reset' + (p.capBg ? "" : " on") + '" data-act="pickCap" data-id="' + p.id + '" data-color="">기본</button></div>' +
      '<p class="cp-note">글씨는 어느 색을 골라도 검정으로 유지돼요. 고른 색은 앱을 다시 열어도 그대로 남아 있어요.</p></div>' +
      '<div style="height:6px"></div>';
    openSheet(html, null);
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
  /* 고른 사진을 가운데 기준으로 정사각형 256px JPEG 로 줄입니다 */
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

  function formPerson(who) {
    var nm = who === "me" ? S.couple.me : S.couple.you;
    var pic = avPic(who);
    var h = sheetHead(nm + " 프로필");
    h += '<div class="pr-top">' +
      '<span class="pr-av' + (pic ? " pic" : "") + '" style="background:' + avColor(who) + '">' + avInner(who) + "</span>" +
      '<div class="pr-acts">' +
      '<button type="button" class="set-btn" data-act="pickPic" data-who="' + who + '">사진첩에서 선택</button>' +
      (pic ? '<button type="button" class="set-btn ghost" data-act="clearPic" data-who="' + who + '">사진 지우기</button>' : "") +
      "</div></div>";
    h += '<div class="pr-color"><span class="set-lbl">색</span>' + colorPickRow(who) + "</div>";
    h += '<form class="form" id="personForm" data-who="' + who + '" style="margin-top:16px">' +
      '<div class="f"><label>이름</label><input class="field" name="name" value="' + esc(nm) + '" placeholder="이름" required autocomplete="off"></div>' +
      '<button class="btn-primary" type="submit">저장</button></form>';
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
    return '<div class="av-line">' +
      '<button type="button" class="set-av pick' + (has ? " pic" : "") + '" data-act="pickPic" data-who="' + who +
      '" style="background:' + avColor(who) + '" aria-label="' + esc(nm) + ' 프로필 사진 선택">' + avInner(who) + "</button>" +
      '<span class="av-nm">' + esc(nm) + "</span>" +
      '<span class="av-acts"><button type="button" class="set-btn" data-act="pickPic" data-who="' + who + '">' +
      (has ? "사진 바꾸기" : "사진 선택") + "</button>" +
      (has ? '<button type="button" class="set-btn ghost" data-act="clearPic" data-who="' + who + '">기본으로</button>' : "") +
      "</span></div>";
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

  function renderSet() {
    var c = S.couple, t = S.theme || {}, li = S.link || {}, dark = t.mode === "dark";
    var remote = !!(Store && Store.mode === "remote");
    var acct = (S.auth || {});
    var h = '<header class="hdr' + capCls("set") + '"' + capStyle("set") + ' data-pg="set"><div><h1><span class="eh">⚙️</span> 설정</h1><p class="sub">계정·연결·화면을 내 방식으로</p></div></header>';

    /* ---- 계정 및 커플 연결 ---- */
    h += '<div class="sec"><h2>👤 계정 및 커플 연결</h2><span class="more">' + (li.connected ? "연결됨" : "미연결") + "</span></div>";
    h += '<div class="list">';
    h += '<div class="row tap" data-act="personSheet" data-who="me"><button type="button" class="set-av pick' + (avPic("me") ? " pic" : "") + '" data-act="pickPic" data-who="me" style="background:' + avColor("me") + '" aria-label="' + esc(c.me) + ' 프로필 사진 선택">' + avInner("me") + "</button>" +
      '<div class="body" style="flex:1 1 auto;min-width:0"><div class="t" style="font-size:13.5px;font-weight:600;letter-spacing:-.02em">' + esc(c.me) + "</div>" +
      '<div style="font-size:11px;color:var(--ink-3);margin-top:2px">' + (remote && acct.email ? esc(acct.email) : "내 계정 · 로그인됨") + "</div></div>" +
      '<span class="chip plain">나</span></div>';
    h += '<div class="row tap" data-act="personSheet" data-who="you"><button type="button" class="set-av pick' + (avPic("you") ? " pic" : "") + '" data-act="pickPic" data-who="you" style="background:' + avColor("you") + '" aria-label="' + esc(c.you) + ' 프로필 사진 선택">' + avInner("you") + "</button>" +
      '<div class="body" style="flex:1 1 auto;min-width:0"><div class="t" style="font-size:13.5px;font-weight:600;letter-spacing:-.02em">' + esc(c.you) + "</div>" +
      '<div style="font-size:11px;color:var(--ink-3);margin-top:2px">' + (li.connected ? "커플 연결됨 · 함께 기록 중" : "초대 코드로 연결할 수 있어요") + "</div></div>" +
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

    /* ---- 화면 및 꾸미기 ---- */
    h += '<div class="sec"><h2>🎛️ 화면 및 꾸미기</h2></div>';
    h += '<div class="list">';
    h += '<div class="set-block"><span class="set-lbl">화면</span><div class="seg seg-sm" data-group="mode">' +
      '<button type="button" class="seg-btn' + (dark ? "" : " active") + '" data-act="mode" data-mode="light">라이트</button>' +
      '<button type="button" class="seg-btn' + (dark ? " active" : "") + '" data-act="mode" data-mode="dark">다크</button></div></div>';
    h += '<div class="set-block"><span class="set-lbl">페이지 캡션 색</span>' + capPickRows() +
      '<div class="set-hint">페이지마다 제목 줄의 바탕색을 고를 수 있어요. 글씨는 라이트·다크 모두 검정으로 또렷하게 보여요.</div></div>';
    h += '<div class="set-block"><span class="set-lbl">일정 색 · 캘린더</span>' +
      colorPickRow("me") + colorPickRow("you") + colorPickRow("both") + "</div>";
    h += '<div class="set-block"><div class="set-hint" style="margin-top:0">이름과 프로필 사진은 위 계정 줄을 눌러 바꿔요. 처음 만난 날 · 문구 · 표기 방식은 홈 D-day 카드를 눌러 바꿀 수 있어요.</div></div>';
    h += "</div>";

    h += '<div style="height:26px"></div>';
    h += '<p class="cp-note" style="text-align:center;padding:0 24px">' + installHint() + "</p>";
    h += '<div style="height:26px"></div>';
    $("#s-set").innerHTML = h;
  }

  function installHint() {
    try {
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
      ["set", "설정", IC.gear]
    ];
    $("#tabbar").innerHTML = tabs.map(function (t) {
      return '<button class="tab' + (current === t[0] ? " active" : "") + '" data-act="nav" data-screen="' + t[0] + '">' +
        '<span class="ic">' + t[2] + "</span><span>" + t[1] + "</span></button>";
    }).join("");
  }

  function go(name) {
    if (S.auth && S.auth.out) return;
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

    if (act === "calPrev" || act === "calNext") {
      var cur = S.ui.calMonth || today.slice(0, 7);
      var y = Number(cur.slice(0, 4)), m = Number(cur.slice(5, 7)) - 1 + (act === "calNext" ? 1 : -1);
      var nd = new Date(y, m, 1);
      S.ui.calMonth = nd.getFullYear() + "-" + pad(nd.getMonth() + 1);
      save(); renderCal(); return;
    }

    if (act === "pickDay") { S.ui.selDate = el.getAttribute("data-date"); save(); renderCal(); return; }

    if (act === "addEvent") {
      openSheet(formEvent(S.ui.selDate || today), function (fd) {
        var st = String(fd.get("start") || today).slice(0, 10);
        var en = String(fd.get("end") || st).slice(0, 10);
        if (en < st) en = st;
        S.events.push({
          id: uid(), date: st, endDate: en, time: "",
          title: String(fd.get("title") || "").trim(), type: fd.get("type") || "date", memo: "",
          who: fd.get("who") || "both"
        });
        S.ui.calMonth = st.slice(0, 7);
        S.ui.selDate = st;
        save(); closeSheet(); renderAll(); toast("일정을 추가했어요");
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
      if (tl) tl.items.forEach(function (it) { if (it.id === ti) it.done = !it.done; });
      save(); renderDiary(); return;
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
        save(); closeSheet(); renderDiary(); toast("저장했어요");
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
        t2.who = String(fd.get("who") || "함께");
        save(); closeSheet(); renderDiary(); toast("저장했어요");
      });
      return;
    }

    if (act === "delTodo") {
      var dtId = el.getAttribute("data-id");
      S.todos = S.todos.filter(function (x) { return x.id !== dtId; });
      save(); closeSheet(); renderDiary(); toast("지웠어요"); return;
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
        b2.done = !!fd.get("done");
        if (b2.done) delete b2.status;
        save(); closeSheet(); renderDiary(); toast("버킷을 저장했어요");
      });
      return;
    }

    if (act === "delBucket") {
      var dbId = el.getAttribute("data-id");
      S.bucket = S.bucket.filter(function (x) { return x.id !== dbId; });
      save(); closeSheet(); renderDiary(); toast("버킷을 삭제했어요"); return;
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

    if (act === "toggleTodo") {
      var tid = el.getAttribute("data-id");
      S.todos.forEach(function (t) { if (t.id === tid) t.done = !t.done; });
      save(); renderDiary(); return;
    }

    if (act === "addTodo") {
      openSheet(formTodo(), function (fd) {
        S.todos.push({ id: uid(), text: fd.get("text"), done: false, who: fd.get("who") || "함께" });
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
        S.bucket.push({ id: uid(), title: fd.get("title"), cat: fd.get("cat") || "기타", done: false });
        save(); closeSheet(); renderDiary(); toast("버킷리스트에 담았어요");
      });
      return;
    }

    if (act === "addLog") {
      openSheet(formLog(), function (fd) {
        S.logs.push({
          id: uid(), kind: fd.get("kind"), title: fd.get("title"),
          rating: Number(fd.get("rating") || 4), date: fd.get("date"),
          review: fd.get("review") || "", place: fd.get("place") || ""
        });
        save(); closeSheet(); renderDiary(); toast("기록을 저장했어요");
      });
      return;
    }

    if (act === "delLog") {
      var lid = el.getAttribute("data-id");
      S.logs = S.logs.filter(function (l) { return l.id !== lid; });
      save(); closeSheet(); renderDiary(); toast("기록을 삭제했어요"); return;
    }

    if (act === "openTheme") { openSheet(formTheme(), null); return; }

    if (act === "toggleMode") { setMode(S.theme && S.theme.mode === "dark" ? "light" : "dark"); return; }

    if (act === "mode") { setMode(el.getAttribute("data-mode")); return; }

    if (act === "pickColor") {
      setThemeColor(el.getAttribute("data-target"), el.getAttribute("data-color") || "");
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
          closeSheet();
          renderAll();
          toast("로그아웃했어요");
          if (remote) Store.auth.signOut().catch(function () {});
        });
      return;
    }

    if (act === "copyCode") { copyText(myInviteCode(), "초대 코드를 복사했어요"); return; }

    if (act === "linkSheet") { openSheet(formLink()); return; }

    if (act === "newCode") {
      S.link = S.link || {};
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
      var ai = $("#avatarInput");
      if (!ai) return;
      ai.value = "";
      ai.setAttribute("data-who", pWho);
      ai.click();
      return;
    }

    if (act === "clearPic") {
      var cWho = el.getAttribute("data-who") === "you" ? "you" : "me";
      if (S.couple.pics) delete S.couple.pics[cWho];
      save(); renderAll();
      if (personSheetWho) openPersonSheet(personSheetWho);
      toast("프로필 사진을 지웠어요"); return;
    }

    if (act === "openPhoto") { openPhoto(el.getAttribute("data-id")); return; }

    if (act === "addPhoto") {
      var pi = $("#photoInput");
      if (pi) { pi.value = ""; pi.click(); }
      return;
    }

    if (act === "photoEdit") {
      var pe = S.photos.filter(function (x) { return x.id === el.getAttribute("data-id"); })[0];
      if (!pe) return;
      openSheet(formEditPhoto(pe), function (fd) {
        var p2 = S.photos.filter(function (x) { return x.id === pe.id; })[0];
        if (!p2) return;
        p2.title = String(fd.get("title") || "").trim();
        p2.album = String(fd.get("album") || "").trim() || defaultAlbum();
        p2.date = fd.get("date") || p2.date;
        p2.place = String(fd.get("place") || "").trim();
        p2.memo = String(fd.get("memo") || "").trim();
        save(); closeSheet(); renderAll(); toast("사진 정보를 저장했어요");
      });
      return;
    }

    if (act === "photoDelete") {
      var pdId = el.getAttribute("data-id");
      askConfirm("이 사진을 지울까요? 사진과 캡션이 함께 사라져요.", "지우기", function () {
        var gone = S.photos.filter(function (x) { return x.id === pdId; })[0];
        S.photos = S.photos.filter(function (x) { return x.id !== pdId; });
        delete PHOTO_URLS[pdId];
        if (gone) { try { Store.photos.remove(gone).catch(function () {}); } catch (e) {} }
        save(); closeSheet(); renderAll(); toast("사진을 지웠어요");
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

  document.addEventListener("submit", function (ev) {
    if (ev.target.id === "qaddForm") {
      ev.preventDefault();
      var form = ev.target;
      var inp = form.querySelector('[name="text"]');
      var text = inp ? String(inp.value || "").trim() : "";
      if (!text) { if (inp) inp.focus(); return; }
      var kind = form.getAttribute("data-kind") || "";
      var selEl = form.querySelector('[name="sub"]');
      var sub = selEl ? String(selEl.value || "") : "";
      if (kind.indexOf("list:") === 0) {
        var l0 = findList(kind.slice(5));
        if (!l0) return;
        l0.items.push({ id: uid(), text: text, done: false });
      } else if (kind === "todo") {
        S.todos.push({ id: uid(), text: text, done: false, who: sub || "함께" });
      } else if (kind === "bucket") {
        S.bucket.push({ id: uid(), title: text, cat: sub || "기타", done: false });
      } else if (kind === "log") {
        S.logs.push({ id: uid(), kind: sub === "food" ? "food" : "movie", title: text, rating: 4, date: today, review: "", place: "" });
      } else { return; }
      save(); renderDiary();
      var nx = $("#qaddInput");
      if (nx) { nx.value = ""; nx.focus(); }
      return;
    }

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

    if (ev.target.id === "noteForm") {
      ev.preventDefault();
      var nf = new FormData(ev.target);
      NOTE_BASE.forEach(function (k) {
        S.note[k] = {
          e: String(nf.get("t_" + k + "_e") || "").trim() || NOTE_DEF[k].e,
          n: String(nf.get("t_" + k + "_n") || "").trim() || NOTE_DEF[k].n
        };
      });
      S.lists.forEach(function (l) {
        l.emoji = String(nf.get("l_" + l.id + "_e") || "").trim() || "📌";
        l.title = String(nf.get("l_" + l.id + "_n") || "").trim() || l.title;
      });
      var newName = String(nf.get("new_n") || "").trim();
      if (newName) {
        var newList = {
          id: uid(), title: newName,
          emoji: String(nf.get("new_e") || "").trim() || "📌",
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
            if (doc) { var keepUi = S.ui; S = normalizeState(doc); S.ui = keepUi; applyTheme(); renderAll(); }
            closeSheet();
            toast("커플 연결을 완료했어요");
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
          S = normalizeState(doc || emptyState());
          S.auth.out = false;
          S.auth.email = email;
          applyTheme(); go("home"); renderAll();
          toast("들어왔어요");
          loadPhotoUrls();
        });
      }).catch(function (e) { toast("들어가지 못했어요"); if (btn) { btn.disabled = false; btn.textContent = label; } });
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
    if (ev.target.id !== "sheetForm" || !sheetSubmit) return;
    ev.preventDefault();
    var fd = new FormData(ev.target);
    try { sheetSubmit(fd); } catch (e) { toast("저장하지 못했어요"); }
  });

  document.addEventListener("input", function (ev) {
    var t = ev.target;
    if (t && t.classList && t.classList.contains("js-color")) setThemeColor(t.getAttribute("data-target"), t.value);
    if (t && t.classList && t.classList.contains("js-cap")) setCapColor(t.getAttribute("data-id"), t.value);
    if (t && t.classList && t.classList.contains("js-page")) setPageCap(t.getAttribute("data-page"), t.value);
    if (t && t.classList && t.classList.contains("js-own")) setOwnerColor(t.getAttribute("data-who") || "me", t.value);
  });

  /* 파일 선택 → 프로필 사진 (동그란 아바타) */
  document.addEventListener("change", function (ev) {
    if (!ev.target || ev.target.id !== "avatarInput") return;
    var file = (ev.target.files || [])[0];
    if (!file) return;
    var w = ev.target.getAttribute("data-who") === "you" ? "you" : "me";
    squareAvatar(file).then(function (url) {
      S.couple.pics = S.couple.pics || {};
      S.couple.pics[w] = url;
      save(); renderAll();
      if (personSheetWho) openPersonSheet(personSheetWho);
      toast("프로필 사진을 바꿨어요");
    }).catch(function () { toast("사진을 불러오지 못했어요. 다른 사진으로 해볼까요?"); });
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
    if (ev.key === "Escape") closeSheet();
  });

  /* ------------------------------------------------------------------ boot */
  function emptyState() {
    return {
      couple: {
        me: "소영", you: "준영", since: today, fmt: "D", phrase: "함께한 지",
        colors: { me: "#F7C6D4", you: "#BCE0F7" },
        sched: { me: "#F7C6D4", you: "#BCE0F7", both: "#D6C5F7" }
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
    if (opts && opts.signedOut) { S.auth.out = true; S.auth.email = ""; }
    applyTheme();
    renderAll();
    BOOTED = true;
    loadPhotoUrls();
  }

  /* 상대 기기에서 바뀐 내용 반영 */
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
    toast("상대와 맞췄어요");
  }
  function stripUi(doc) {
    if (!doc) return null;
    var copy = {};
    Object.keys(doc).forEach(function (k) { if (k !== "ui") copy[k] = doc[k]; });
    return copy;
  }

  function refreshToday() {
    var t2 = iso(new Date());
    if (t2 !== today) { today = t2; if (BOOTED) renderAll(); }
  }
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "visible") refreshToday();
  });

  window.TwoLogUI = {
    start: start,
    applyRemote: applyRemote,
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
    navigator.serviceWorker.register("sw.js").catch(function (e) {
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
    }).catch(function (e) {
      console.error("[투로그] 시작하지 못했어요", e);
      window.TwoLogUI.start(store, demo ? "demo" : null, {});
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
