
(function () {
  "use strict";

  /* ------------------------------------------------------------------ utils */
  /* v22: 앱 버전 — 업데이트할 때 sw.js 의 VERSION(twolog-vNN)과 함께 올려 주세요.
     My 탭 맨 윗줄 오른쪽에 「버전 vNN」으로 보입니다. */
  var APP_VERSION = "v47";
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
    /* v37: 사진첩 달력은 달을 위아래로 넘겨요 — 위로 밀면 다음 달, 아래로 밀면 지난 달 */
    up: svg('<path d="M6 14.5l6-6 6 6"/>', 18),
    down: svg('<path d="M6 9.5l6 6 6-6"/>', 18),
    check: svg('<path d="M5 12.6l4.2 4.2L19 7"/>', 13),
    palette: svg('<path d="M12 3.4a8.6 8.6 0 1 0 0 17.2c1.1 0 1.9-.8 1.9-1.8 0-.9-.6-1.4-.6-2.1 0-.8.7-1.4 1.5-1.4h1.4a4.3 4.3 0 0 0 4.3-4.3c0-4.2-3.7-7.6-8.5-7.6z"/><circle cx="8.3" cy="9.8" r="1" fill="currentColor" stroke="none"/><circle cx="12" cy="7.8" r="1" fill="currentColor" stroke="none"/><circle cx="15.7" cy="9.7" r="1" fill="currentColor" stroke="none"/>', 17),
    gear: svg('<path d="M4 7h9M17 7h3M4 12h3M11 12h9M4 17h11M19 17h1"/><circle cx="15" cy="7" r="1.9"/><circle cx="9" cy="12" r="1.9"/><circle cx="17.5" cy="17" r="1.9"/>', 21),
    person: svg('<circle cx="12" cy="8.3" r="3.5"/><path d="M5.2 20c0-3.4 3.1-5.7 6.8-5.7s6.8 2.3 6.8 5.7"/>', 21),
    search: svg('<circle cx="10.8" cy="10.8" r="6.2"/><path d="M15.4 15.4l4.1 4.1"/>', 20),
    grid: svg('<rect x="3.6" y="3.6" width="7" height="7"/><rect x="13.4" y="3.6" width="7" height="7"/><rect x="3.6" y="13.4" width="7" height="7"/><rect x="13.4" y="13.4" width="7" height="7"/>', 18),
    /* v28: 노트 알약 탭 옆 — 「목록 +」 아이콘 */
    listPlus: svg('<path d="M4.6 6.4h9.2M4.6 11h6.4M4.6 15.6h4.4"/><path d="M17.6 12.4v6.2M14.5 15.5h6.2"/>', 20),
    /* v34: + 시트의 카테고리 순서를 끌어 옮기는 3줄 손잡이 (≡) */
    grip: svg('<path d="M5 8h14M5 12h14M5 16h14"/>', 20),
    /* v40: 사진 크게 보기의 댓글·더 보기 */
    chat: svg('<path d="M4.2 5.6h15.6v10.2H9.6l-4 3.4v-3.4H4.2z"/>', 19),
    more: svg('<circle cx="6" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none"/><circle cx="18" cy="12" r="1.4" fill="currentColor" stroke="none"/>', 19),
    /* v44: 글씨 정렬 — 왼쪽·가운데·오른쪽 */
    alignL: svg('<path d="M4 7h16M4 12h10M4 17h13"/>', 18),
    alignC: svg('<path d="M4 7h16M7 12h10M5.5 17h13"/>', 18),
    alignR: svg('<path d="M4 7h16M10 12h10M7 17h13"/>', 18),
    /* v44: 모눈 다이어리 — 되돌리기 · 다시 실행 · 형광펜 · 지우개 */
    undo: svg('<path d="M8.8 5.6 4.4 10l4.4 4.4"/><path d="M4.4 10h9.6a5.1 5.1 0 0 1 0 10.2h-2.4"/>', 19),
    redo: svg('<path d="M15.2 5.6 19.6 10l-4.4 4.4"/><path d="M19.6 10h-9.6a5.1 5.1 0 0 0 0 10.2h2.4"/>', 19),
    marker: svg('<path d="M5 19.5h14"/><path d="M6.8 15.6 13.7 8.7a1.9 1.9 0 0 1 2.7 0l1.5 1.5a1.9 1.9 0 0 1 0 2.7l-6.9 6.9-3.6.9.9-3.6z"/>', 19),
    eraser: svg('<path d="M4.5 15.6 12 8.1a2 2 0 0 1 2.8 0l3.6 3.6a2 2 0 0 1 0 2.8l-3.7 3.7H8.7z"/><path d="M4.5 19.6h15"/>', 19),
    /* v45: 지출·정산 시트 — 고친 항목 지우기 */
    trash: svg('<path d="M4.6 7h14.8M9.4 7V5.3h5.2V7"/><path d="M6.8 7l.9 12.3a1.5 1.5 0 0 0 1.5 1.4h5.6a1.5 1.5 0 0 0 1.5-1.4L17.2 7"/>', 19)
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
  /* v33: 예전 기본 이모지(📝·🎯·🎬)가 저장돼 있던 기기는 한 번만 지워 이름만 남겨요.
     내가 일부러 다른 이모지를 넣어 둔 탭은 건드리지 않습니다. */
  if (!S.mig.noteEmo) {
    var OLD_NOTE_EMO = { todo: "📝", bucket: "🎯", log: "🎬" };
    ["todo", "bucket", "log"].forEach(function (k) {
      if (S.note[k] && S.note[k].e === OLD_NOTE_EMO[k]) S.note[k].e = "";
    });
    S.mig.noteEmo = 1;
  }
  /* v34: 노트 카테고리(탭) 순서 — 기본 탭 3개와 내가 만든 카테고리를 한 줄에 섞어 놓을 수 있어요.
     예) ["todo", "list:ab12", "bucket", "log"] / 없던 값은 아래 noteOrderList() 가 정리합니다. */
  if (!Array.isArray(S.noteOrder)) S.noteOrder = [];
  /* v39: 기본 카테고리(메모·버킷리스트·영화·먹방)가 고른 속지 — 값이 없으면 지금 모양(카드) 그대로예요.
     예) S.noteKinds = { bucket: "expense" } → 버킷리스트 탭이 지출·정산 속지로 그려집니다. */
  if (!S.noteKinds || typeof S.noteKinds !== "object") S.noteKinds = {};
  /* v45: 기본 카테고리가 지출·정산 속지일 때의 달 예산 — { todo|bucket|log: { "2026-11": 1500000 } } */
  if (!S.noteBudgets || typeof S.noteBudgets !== "object") S.noteBudgets = {};
  ["todo", "bucket", "log"].forEach(function (k) {
    if (!S.noteBudgets[k] || typeof S.noteBudgets[k] !== "object") S.noteBudgets[k] = {};
  });
  ["todo", "bucket", "log"].forEach(function (k) {
    if (["check", "memo", "review", "expense"].indexOf(S.noteKinds[k]) < 0) delete S.noteKinds[k];
    /* v40: 기본 카테고리의 「투두리스트」는 이제 「카드」와 같은 화면이라 값을 걷어요 */
    if (S.noteKinds[k] === "check") delete S.noteKinds[k];
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
    /* v40: 사진 댓글·대댓글 — 모양이 깨진 값은 조용히 걷어 내요 */
    if (!Array.isArray(p.comments)) p.comments = [];
    p.comments = p.comments.filter(function (c) { return c && typeof c === "object" && String(c.text || "").trim(); });
    p.comments.forEach(function (c) {
      if (c.who !== "you") c.who = "me";
      if (!Array.isArray(c.replies)) c.replies = [];
      c.replies = c.replies.filter(function (r) { return r && typeof r === "object" && String(r.text || "").trim(); });
      c.replies.forEach(function (r) { if (r.who !== "you") r.who = "me"; });
    });
  });
  S.lists.forEach(function (l) {
    if (!l || typeof l !== "object") return;
    if (!l.id) l.id = uid();
    /* v38: 속지 레이아웃 4종 — 모르는 값(예전 데이터)은 투두리스트로 */
    if (["check", "memo", "review", "expense"].indexOf(l.kind) < 0) l.kind = "check";
    if (typeof l.emoji !== "string") l.emoji = "";   /* v33: 이모지 없이 쓰는 카테고리 */
    if (!Array.isArray(l.items)) l.items = [];
    /* v45: 지출·정산 달 예산 { "2026-11": 1500000 } — 모양이 깨진 값은 걷어 내요 */
    if (l.budgets != null && typeof l.budgets !== "object") delete l.budgets;
    if (l.budgets) {
      Object.keys(l.budgets).forEach(function (k) {
        var v = Math.round(Number(l.budgets[k]) || 0);
        if (/^\d{4}-\d{2}$/.test(k) && v > 0) l.budgets[k] = v; else delete l.budgets[k];
      });
    }
  });
  S.lists = S.lists.filter(function (l) { return l && typeof l === "object"; });
  /* v40: 「투두리스트」 속지는 2열 카드 묶음 화면이 됐어요 — 내 카테고리도 카드 묶음을 갖고,
     v38·v39 에서 카드 없이 한 줄씩 적어 둔 항목은 카테고리 이름의 첫 카드 안으로 옮겨 담습니다. */
  var listKeysLive = {};
  S.lists.forEach(function (l) {
    listKeysLive["list:" + l.id] = 1;
    if (l.kind === "check") ensureListCards(l);
  });
  Object.keys(S.groups).forEach(function (k) {
    if (k.indexOf("list:") === 0 && !listKeysLive[k]) delete S.groups[k];   /* 지운 카테고리의 카드 정리 */
  });
  /* v39: 기본 카테고리에도 속지(투두·메모·리뷰·지출)를 고를 수 있어, 항목의 «제목/본문» 자리를
     탭마다 다른 이름(text·title / memo·review)으로 쓰던 것을 한 가지로 읽고 쓸 수 있게 맞춥니다. */
  (S.todos || []).forEach(function (t) { if (t && typeof t.memo !== "string") t.memo = ""; });
  (S.bucket || []).forEach(function (b) { if (b && typeof b.memo !== "string") b.memo = ""; });
  (S.logs || []).forEach(function (l) { if (l && typeof l.review !== "string") l.review = ""; });
  return S;
  }

  /* 저장: 화면에서 곧바로 호출할 수 있도록 동기 함수로 두고, 실제 쓰기는 sync.js 가 처리합니다. */
  function save() {
    if (!S || !Store) return;
    /* v35: 모드·색·폰트는 이 폰에만 남는 값이라 저장할 때마다 기기 테마에도 함께 적어 둡니다 */
    captureLocalTheme();
    try { Store.persist(S); } catch (e) {}
  }

  /* ==========================================================================
     v36: 노트 중복 항목 정리
     --------------------------------------------------------------------------
     같은 카드(gid) 안에 같은 내용이 두 번 들어 있으면 하나로 합칩니다.
       · 할 일(todo)  : text.trim()
       · 버킷(bucket) : title.trim()
       · 영화·먹방(log) : kind + "|" + title.trim() + "|" + date
       · 커스텀 리스트 : 그 리스트 안 항목 text.trim()
     합칠 때는 한쪽이라도 체크(done)했으면 체크를 남기고,
     상세 메모·감상·곳 같은 부가 내용이 있는 쪽을 살립니다.
     (예전 동기화 겁침으로 같은 줄이 두 번 들어가면, 위쪽을 체크해도 아래에
     같은 줄이 남아 「체크했는데 또 떠 있다」고 보이던 문제를 정리합니다)
     ========================================================================== */
  var SIGNED_OUT = false;
  function noteFlat(v) { return String(v == null ? "" : v).replace(/\s+/g, " ").trim(); }
  /* 부가 내용이 몇 개 있는지 — 많은 쪽을 남깁니다 */
  function noteRich(it) {
    var n = 0;
    ["memo", "review", "place", "status", "caption"].forEach(function (k) {
      if (it && typeof it[k] === "string" && noteFlat(it[k])) n += 1;
    });
    if (it && Number(it.rating) > 0) n += 1;
    return n;
  }
  /* a 를 남기고 b 의 내용을 보탭니다 (체크·부가 내용이 사라지지 않게) */
  function mergeNoteItem(a, b) {
    if (!a || !b) return a;
    if (b.done === true) a.done = true;
    ["memo", "review", "place", "status", "caption"].forEach(function (k) {
      if (!noteFlat(a[k]) && noteFlat(b[k])) a[k] = b[k];
    });
    if (!Number(a.rating) && Number(b.rating)) a.rating = b.rating;
    if ((!a.cat || a.cat === "기타") && b.cat) a.cat = b.cat;
    return a;
  }
  function noteDedupeKey(kind, it) {
    if (!it || typeof it !== "object") return "";
    if (kind === "todo") return noteFlat(it.text);
    if (kind === "bucket") return noteFlat(it.title);
    if (kind === "log") {
      return (it.kind === "food" ? "food" : "movie") + "|" + noteFlat(it.title) + "|" +
        String(it.date == null ? "" : it.date).slice(0, 10);
    }
    return noteFlat(it.text);
  }
  /* 배열 하나에서 같은 카드·같은 내용의 항목을 합칩니다. {items, removed} */
  function dedupeItems(kind, list) {
    var out = [], seen = {}, removed = 0;
    (list || []).forEach(function (it) {
      if (!it || typeof it !== "object") return;
      var key = noteDedupeKey(kind, it);
      if (!key) { out.push(it); return; }
      var mapKey = String(it.gid || "") + "\u0000" + key;
      var at = seen[mapKey];
      if (at === undefined) { seen[mapKey] = out.length; out.push(it); return; }
      var keep = out[at];
      if (noteRich(it) > noteRich(keep)) {      // 부가 내용이 더 많은 쪽을 남깁니다
        mergeNoteItem(it, keep);
        out[at] = it;
      } else {
        mergeNoteItem(keep, it);
      }
      removed += 1;
    });
    return { items: out, removed: removed };
  }
  /* 상태 안의 노트 항목 전체 — 지운 개수를 돌려줍니다 */
  function dedupeNotes(st) {
    var S2 = st || S;
    if (!S2) return 0;
    var removed = 0;
    [["todo", "todos"], ["bucket", "bucket"], ["log", "logs"]].forEach(function (p) {
      /* v45: 지출·정산 속지의 항목은 같은 이름(같은 카테고리)이어도 하나로 합치지 않아요 */
      if (noteBaseKind(p[0]) === "expense") return;
      var res = dedupeItems(p[0], S2[p[1]]);
      if (res.removed) { S2[p[1]] = res.items; removed += res.removed; }
    });
    /* 커스텀 리스트(내 카테고리) 안의 항목 */
    (S2.lists || []).forEach(function (l) {
      if (!l || !Array.isArray(l.items)) return;
      /* v45: 가계부는 «식비» «입금» 처럼 이름이 같은 줄이 여러 개예요 — 합치면 안 돼요 */
      if (listKindOf(l) === "expense") return;
      var res = dedupeItems("list", l.items);
      if (res.removed) { l.items = res.items; removed += res.removed; }
    });
    return removed;
  }
  function demoBoot() {
    try { return /[?&]demo=1\b/.test(location.search); } catch (e) { return false; }
  }
  /* 중복을 실제로 지웠을 때만 저장 — 서버(notes)에서도 중복 행이 지워집니다.
     ?demo=1 예시 화면과 로그아웃 화면에서는 저장하지 않습니다.
     (서버를 못 읽어 폰에 있던 예전 상태로 열린 때는 저장하지 않아
      엇갈린 상태가 서버로 밀리지 않게 합니다) */
  function dedupeNotesAndSave() {
    var removed = dedupeNotes(S);
    if (!removed) return 0;
    if (demoBoot() || SIGNED_OUT || !Store) return removed;
    if (Store.mode === "remote" && Store.status && Store.status.state !== "online") return removed;
    save();
    return removed;
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
    applyLocalTheme();
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
      applyLocalTheme();
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
  /* v33: 기본 탭은 이모지 없이 이름만 — 「메모」·「버킷리스트」·「영화·먹방」 */
  var NOTE_DEF = { todo: { e: "", n: "메모" }, bucket: { e: "", n: "버킷리스트" }, log: { e: "", n: "영화·먹방" } };
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
    /* v42: 테마 포인트 색 — 홈에서 고른 색(없으면 테마 이름 색)을 노트 탭·다이어리 저장 같은
       강조 자리에 함께 써서 앱 전체가 한 테마로 이어지게 해요 */
    var pt = /^#[0-9A-F]{6}$/.test(htb) ? htb : (function () {
      var nmc = String(t.name || "").toUpperCase();
      return /^#[0-9A-F]{6}$/.test(nmc) ? nmc : "";
    })();
    if (pt) {
      root.style.setProperty("--point", pt);
      root.style.setProperty("--point-ink", btnInk(pt));
    } else {
      ["--point", "--point-ink"].forEach(function (k) { root.style.removeProperty(k); });
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

  /* ==========================================================================
     v35: 화면 모드·컬러·폰트는 「이 폰」에만 저장해요.
     --------------------------------------------------------------------------
     라이트/다크 · 페이지 캡션 색 · 홈 제목 색 · 일정 색(소영·준영·공동) · 폰트는
     커플 공간(서버)으로 올리지 않고 이 기기의 localStorage 키 하나에만 둡니다.
     그래서 내가 다크로 바꾸거나 색을 바꿔도 상대 폰 화면은 그대로예요.
     일정·노트·사진·디데이·닉네임·프로필 사진은 예전처럼 함께 동기화됩니다.
     ========================================================================== */
  var K_LOCAL_THEME = "twolog:v1:localTheme";
  var LT = null;                    /* 이 기기의 테마 {mode, cap, pages, homeTitleBg, font, sched, colors} */
  var LT_HEX = /^#[0-9A-F]{6}$/;

  function ltHex(v) {
    var s = String(v == null ? "" : v).toUpperCase();
    return LT_HEX.test(s) ? s : "";
  }
  /* 지금 화면(S)의 모드·색·폰트를 이 기기 테마 모양으로 뽑습니다 */
  function themeFromState() {
    var t = (S && S.theme) || {};
    var sc = (S && S.couple && S.couple.sched) || {};
    var cc = (S && S.couple && S.couple.colors) || {};
    var pages = {};
    Object.keys(t.pages || {}).forEach(function (k) {
      var c = ltHex((t.pages || {})[k]);
      if (c) pages[k] = c;
    });
    return {
      v: 1,
      mode: t.mode === "dark" ? "dark" : "light",
      cap: ltHex(t.cap),
      pages: pages,
      homeTitleBg: ltHex(t.homeTitleBg),
      font: fontOf(t.font).k,
      sched: { me: ltHex(sc.me), you: ltHex(sc.you), both: ltHex(sc.both) },
      colors: { me: ltHex(cc.me), you: ltHex(cc.you) }
    };
  }
  function localThemeRead() {
    try {
      var raw = localStorage.getItem(K_LOCAL_THEME);
      var o = raw ? JSON.parse(raw) : null;
      return o && typeof o === "object" ? o : null;
    } catch (e) { return null; }
  }
  function localThemeWrite(t) {
    try { localStorage.setItem(K_LOCAL_THEME, JSON.stringify(t || {})); } catch (e) {}
  }
  /* 앱을 열거나 상대 기록을 받을 때: 저장해 둔 이 폰의 테마를 S 위에 다시 얹습니다.
     저장된 값이 없으면(예전 버전에서 올라온 기기) 지금 값으로 한 번만 이어받아 저장해요. */
  function applyLocalTheme(noSeed) {
    if (!S) return;
    LT = localThemeRead();
    if (!LT) {
      /* 아직 저장된 기기 테마가 없는 기기: 로그인 화면(빈 상태)에서는 기본값을
         굳혀 두지 않고, 진짜 기록을 받았을 때 한 번만 이어받습니다. */
      if (noSeed) return;
      LT = themeFromState(); localThemeWrite(LT); return;
    }
    S.theme = S.theme || {};
    S.theme.mode = LT.mode === "dark" ? "dark" : "light";
    S.theme.cap = ltHex(LT.cap);
    var pages = {};
    Object.keys(LT.pages || {}).forEach(function (k) {
      var c = ltHex((LT.pages || {})[k]);
      if (c) pages[k] = c;
    });
    S.theme.pages = pages;
    S.theme.homeTitleBg = ltHex(LT.homeTitleBg) || null;
    S.theme.font = fontOf(LT.font).k;
    S.couple = S.couple || {};
    S.couple.sched = S.couple.sched || {};
    ["me", "you", "both"].forEach(function (w) {
      S.couple.sched[w] = ltHex((LT.sched || {})[w]) || SCHED_DEFAULT[w];
    });
    S.couple.colors = S.couple.colors || {};
    ["me", "you"].forEach(function (w) {
      var c = ltHex((LT.colors || {})[w]);
      if (c) S.couple.colors[w] = c; else delete S.couple.colors[w];
    });
  }
  /* 모드·색·폰트를 바꿀 때마다 이 폰의 테마도 함께 적어 둡니다 (save 가 불러 줍니다) */
  function captureLocalTheme() {
    if (!S) return;
    LT = themeFromState();
    localThemeWrite(LT);
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
  /* v43: 「1992년 6월 26일」처럼 연·월·일을 다 보여 주는 글 (프로필 생일 칸 아래) */
  function bdayFullText(v) {
    var p = parseBirthday(v);
    if (!p) return "";
    return (p.y ? p.y + "년 " : "") + p.m + "월 " + p.d + "일";
  }
  /* =====================================================================
     v45: 프로필 생일은 «한 번에» — 날짜 입력칸 하나
     ---------------------------------------------------------------------
     v44 의 «년 / 월 / 일» 세 고르기는 한 번에 고르기 불편하다는 요청으로 걷어냈어요.
     다시 예전처럼 input[type=date] 한 칸(name=bday)으로 받고, 고르면 바로 아래
     안내 줄에 「1992년 6월 26일 · D-…」처럼 보여 줍니다.
     값은 예전 그대로 YYYY-MM-DD 로 저장하고(sync.js K_BDAY), 비우면 지워져요.
     ===================================================================== */
  function prBdayValue(who) {
    var v = String((S.couple.birthdays || {})[who] || "").trim();
    var p = parseBirthday(v);
    /* 연도 없는 예전 값(«6월 26일»)은 날짜칸에 넣을 수 없어 비워 두고 아래 줄에 보여 줘요 */
    if (p && p.y) return p.y + "-" + pad(p.m) + "-" + pad(p.d);
    return /^\d{4}-\d{2}-\d{2}$/.test(v) ? v : "";
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
          /* v32: 달력 칸 일정 막대 글씨는 배경 밝기와 상관없이 늘 흰색(#FFFFFF)으로 통일
             v44: 여러 주에 걸친 일정은 제목을 첫 주에만 — 이어지는 주의 막대는 빈 막대로
             (예전엔 아래 주 줄까지 내려가면 제목이 또 쓰여졌어요) */
          html += '<span class="ebar' + (b.openL ? " openl" : "") + (b.openR ? " openr" : "") + mid +
            '" style="left:calc(' + left + "% + 1.5px); width:calc(" + width + "% - 3px); top:" + top + "px; background:" + edge +
            "; color:#FFFFFF" + (b.openL ? ' aria-label="' + esc(b.e.title) + ' 일정 이어짐"' : "") +
            '">' + (b.openL ? "" : esc(b.e.title)) + "</span>";
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

  /* v34: 노트 카테고리(탭) 순서 — 기본 탭과 내가 만든 카테고리를 한 목록으로 다뤄요.
     저장된 S.noteOrder 를 그대로 쓰되, 없어진 리스트는 빼고 새로 만든 리스트는 맨 뒤에 붙입니다. */
  function noteAllKeys() {
    var keys = NOTE_BASE.slice();
    (S.lists || []).forEach(function (l) { keys.push("list:" + l.id); });
    return keys;
  }
  function noteOrderList() {
    var valid = noteAllKeys();
    var src = Array.isArray(S.noteOrder) ? S.noteOrder : [];
    var out = [];
    src.forEach(function (k) {
      k = String(k || "");
      if (valid.indexOf(k) >= 0 && out.indexOf(k) < 0) out.push(k);
    });
    valid.forEach(function (k) { if (out.indexOf(k) < 0) out.push(k); });
    S.noteOrder = out;
    return out.slice();
  }

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
    /* v29: 맨 윗줄 오른쪽의 네모 설정 버튼을 지우고, 그 자리에 새 카테고리 탭 추가 + 를 둡니다.
       v37: 동그란 점선 테두리를 걷어내고 ＋ 하나만 — 터치 영역은 44px 그대로.
       탭 이름 바꾸기(노트 설정)는 「📖 노트」 제목을 꾹 눌러 엽니다. */
    html += '<header class="hdr' + capCls("diary") + '"' + capStyle("diary") + ' data-pg="diary"><div>' +
      '<h1 class="note-h1" title="꾹 누르면 탭 이름을 바꿀 수 있어요">노트</h1></div>' +
      '<div class="hdr-acts"><button type="button" class="note-add" data-act="newList" aria-label="새 카테고리 탭 추가" title="새 카테고리 탭 추가">' + IC.plus + "</button></div></header>";
    html += '<div class="segs note-segs">';
    /* v34: 기본 탭과 내가 만든 카테고리를 저장된 순서 그대로 한 줄에 — ≡ 로 옮긴 순서가 여기 그대로 보입니다 */
    noteOrderList().forEach(function (k) {
      if (k.indexOf("list:") === 0) {
        var l = findList(k.slice(5));
        if (!l) return;
        html += '<button class="lchip' + (seg === k ? " active" : "") + '" data-act="seg" data-seg="' + esc(k) + '" aria-label="' + esc(listLabel(l)) + '">' +
          (l.emoji ? '<span class="le">' + esc(l.emoji) + "</span>" : "") + "<span>" + esc(l.title) + "</span></button>";
      } else {
        html += segBtn(seg, k, noteLabel(k));
      }
    });
    html += "</div>";
    var body;
    /* v39: 기본 카테고리에 속지를 골랐으면 그 속지로 그립니다(고르지 않았으면 지금까지처럼 카드) */
    if (NOTE_BASE.indexOf(seg) >= 0 && noteBaseKind(seg)) body = viewBasePage(seg);
    else if (seg === "todo") body = viewTodo();
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
  /* v40: 「투두리스트」 속지가 2열 카드 묶음이 되면서, 카드 묶음(S.groups)이 내가 만든 카테고리
     (list:<id>)에도 생겼어요. 그 카테고리의 항목은 원래처럼 그 리스트의 items 안에 그대로 있어요. */
  var LIST_SEG = "list:";
  function isListSeg(k) { return String(k == null ? "" : k).indexOf(LIST_SEG) === 0; }
  function listOfSeg(k) { return isListSeg(k) ? findList(String(k).slice(LIST_SEG.length)) : null; }
  function itemsOf(k) {
    if (GROUP_ARR[k]) return S[GROUP_ARR[k]] || [];
    var l = listOfSeg(k);
    return l && Array.isArray(l.items) ? l.items : [];
  }
  function groupsOf(k) { return (S.groups && S.groups[k]) || []; }
  /* 카드 제목이 비었을 때 보여 줄 이름 — 기본 카테고리는 그 탭 이름, 내 카테고리는 카테고리 이름 */
  function groupTitleOf(k, g) {
    if (g && g.title) return String(g.title);
    if (GROUP_DEF[k]) return GROUP_DEF[k];
    var l = listOfSeg(k);
    return l ? String(l.title || "리스트") : "리스트";
  }
  /* v40: 카드가 없이 항목만 있는 예전 리스트(v38·v39)를 카드 묶음으로 이어 줌 —
     카드가 하나도 없으면 카테고리 이름의 첫 카드를 만들고, gid 가 없는 항목을 그 안에 넣어요. */
  function ensureListCards(l) {
    if (!l) return 0;
    var k = LIST_SEG + l.id;
    if (!S.groups || typeof S.groups !== "object") S.groups = {};
    if (!Array.isArray(S.groups[k])) S.groups[k] = [];
    S.groups[k] = S.groups[k].filter(function (g) { return g && typeof g === "object"; });
    var gs = S.groups[k];
    gs.forEach(function (g) {
      if (!g.id) g.id = uid();
      if (typeof g.title !== "string") g.title = "";
      if (g.who !== "you") g.who = "me";
      if (!/^\d{4}-\d{2}-\d{2}$/.test(String(g.date || "")) || isNaN(parse(g.date).getTime())) g.date = today;
    });
    if (!Array.isArray(l.items)) l.items = [];
    var moved = 0;
    if (l.items.length) {
      if (!gs.length) gs.push({ id: uid(), title: String(l.title || "리스트"), who: "me", date: today });
      var ids = gs.map(function (g) { return g.id; });
      l.items.forEach(function (it) {
        if (!it || typeof it !== "object") return;
        if (!it.gid || ids.indexOf(it.gid) < 0) { it.gid = gs[0].id; moved += 1; }
      });
    }
    return moved;
  }
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
    var label = k === "log" ? it.title : itTitle(it);
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
    var gTitle = groupTitleOf(k, g);
    var tBg = String(g.titleBg || "").toUpperCase();
    var h = '<div class="ncard" role="button" tabindex="0" data-act="openGroup" data-tab="' + k + '" data-gid="' + g.id +
      '" aria-label="' + esc(gTitle) + ' 목록 열기">';
    /* v21: 카드 위쪽은 색이 꽉 차는 제목 띠 — 고른 색이 없으면 은은한 기본 회색 띠
       v38: 띠 색과 상관없이 제목은 늘 검정 글씨 */
    h += '<div class="nc-hd' + (tBg ? " tint" : "") + '"' + (tBg ? ' style="background:' + tBg + '"' : "") + ">" +
      '<div class="nc-t">' + esc(gTitle) + "</div></div>";
    if (items.length) {
      /* v42: 미리보기는 5개까지 — 넘치면 카드 아래에 「+N개 더」 */
      var restN = items.length - 5;
      h += '<div class="nc-items">' + items.slice(0, 5).map(function (x) { return cardItem(k, x); }).join("") +
        (restN > 0 ? '<div class="nc-more">+' + restN + "개 더</div>" : "") + "</div>";
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

  /* 리스트 카드 상세 시트 — v17: 제목만 맨 위, 그 아래 To-do (주제·한 줄 메모·누구는 삭제)
     v41: 「+ 새 리스트」는 이 시트를 그대로 열어 제목·제목 색·To-do 를 한 번에 적고 저장해요.
     (새 카드일 때는 「카드 삭제」 없이 「저장하기」만 — 그냥 닫으면 빈 카드가 남지 않아요) */
  function cardSheetHtml(k, g, isNew) {
    var items = isNew ? (newCard ? newCard.items.slice() : [])
      : itemsOf(k).filter(function (x) { return x.gid === g.id; }).sort(byDone);
    var h = '<div class="sheet-hd card-hd"><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>";
    /* 제목을 시트 맨 위로 — 카드에서 가장 크게 보이는 값이라 먼저 고쳐요.
       v19: 입력칸 아래 부가설명 줄은 지웠어요 (제목 → To-do 로 바로).
       v21: 제목 입력칸 바로 위에 제목 바탕색 컬러판을 두었어요. */
    /* v40: 「제목」을 맨 위로, 「제목 색」은 한 칸 띄워 그 아래로 — 제목 글씨도 크게 */
    /* v41: 제목·제목 색·To-do·저장하기를 한 폼 안에 — 「+ 새 리스트」로 열어도
       바로 이 카드 시트에서 다 적고 저장해요. */
    h += '<form id="sheetForm">';
    h += '<div class="form card-meta">' +
      '<div class="f"><label>제목</label><input class="field card-title-in" name="title" value="' + (isNew ? "" : esc(groupTitleOf(k, g))) + '" placeholder="예) 장보기" autocomplete="off"></div>' +
      "</div>";
    h += '<div class="card-color-gap"></div>';
    h += cardColorPanel(k, g);
    h += '<div class="todo-label" style="margin-top:20px">To-do</div>';
    h += '<div class="todo-add" id="listAddForm" data-tab="' + k + '" data-gid="' + g.id + '">' +
      '<span class="circ" aria-hidden="true">' + CIR_OFF + "</span>" +
      '<input class="todo-in" name="text" placeholder="내용을 추가해보세요" autocomplete="off" enterkeyhint="done" aria-label="내용">' +
      '<button class="todo-add-btn" type="button">Add</button></div>';
    h += '<div class="todo-items card-items" data-tab="' + k + '" data-gid="' + g.id + '">';
    if (!items.length) h += '<div class="empty">위 칸에 적고 Add 를 눌러 보세요.</div>';
    items.forEach(function (it) { h += diaryRow(k, it); });
    h += "</div>";
    h += '<div class="card-acts">' +
      '<button class="btn-primary" type="submit">저장하기</button>' +
      (isNew ? "" : '<button type="button" class="btn-del" data-act="delCard" data-tab="' + k + '" data-gid="' + g.id + '">카드 삭제</button>') +
      "</div>";
    h += "</form>";
    return h;
  }

  /* v41: 「+ 새 리스트」 — 중간 제목 시트 없이 바로 카드 시트를 열고,
     저장할 때 그제야 카드(리스트)를 만듭니다. 그냥 닫으면 아무것도 남지 않아요. */
  var newCard = null;
  function openNewCardSheet(k) {
    newCard = { k: k, gid: "nc-" + uid(), titleBg: "", items: [] };
    openSheet(cardSheetHtml(k, { id: newCard.gid, title: "", titleBg: "" }, true),
      function (fd) { saveNewCard(fd); });
    openCard = { tab: k, gid: newCard.gid };
  }
  function saveNewCard(fd) {
    if (!newCard) { closeSheet(); return; }
    var k = newCard.k;
    var t = String(fd.get("title") || "").trim();
    if (!t) t = newCard.items.length ? "새 리스트" : "";
    if (!t) { toast("제목을 적어 주세요"); return; }
    var g = { id: newCard.gid, title: t, who: "me", date: today };
    if (newCard.titleBg) g.titleBg = newCard.titleBg;
    S.groups = S.groups || {};
    S.groups[k] = S.groups[k] || [];
    S.groups[k].push(g);
    var list = newCard.items.slice();
    newCard = null;
    list.forEach(function (it) { itemsOf(k).push(it); });
    openCard = null;
    save(); closeSheet(); renderDiary(); toast("카드를 만들었어요");
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

  /* v41: 저장 전인 새 카드 안의 항목 빼기 */
  function dropDraftItem(id) {
    if (!newCard || !id) return false;
    var idx = -1;
    newCard.items.forEach(function (x, i) { if (x.id === id) idx = i; });
    if (idx < 0) return false;
    newCard.items.splice(idx, 1);
    var box = document.querySelector("#sheet .card-items");
    if (box) {
      var row = box.querySelector('[data-id="' + id + '"]');
      var tr = row && row.closest ? row.closest(".trow") : null;
      if (tr && tr.parentNode) tr.parentNode.removeChild(tr);
      if (!newCard.items.length) box.innerHTML = '<div class="empty">위 칸에 적고 Add 를 눌러 보세요.</div>';
    }
    return true;
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

  /* v40: 2열 카드 묶음 + 「+ 새 리스트」 — 기본 카테고리(todo·bucket·log)와
     투두리스트 속지를 고른 내 카테고리(list:<id>)가 같은 화면을 씁니다. */
  function viewCards(k) {
    if (isListSeg(k)) ensureListCards(listOfSeg(k));
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
    /* v40: 내 카테고리 투두리스트 카드 안 항목 — 그 카테고리의 항목을 그대로 토글·삭제 */
    if (isListSeg(k)) {
      return listItemRow(it, '<div class="t tw">' + esc(itTitle(it)) + "</div>" +
        (itBody(it) ? '<div class="sub">' + esc(itBody(it)) + "</div>" : ""),
        'data-act="toggleListItem" data-list="' + k + '" data-id="' + it.id + '"',
        'data-act="editListItem" data-list="' + k + '" data-id="' + it.id + '"',
        'data-act="delListItem" data-list="' + k + '" data-id="' + it.id + '"');
    }
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

  /* ==========================================================================
     v38: 노트 속지 레이아웃 4종
     --------------------------------------------------------------------------
     카테고리를 만들 때 속지를 고르면 그 카테고리 화면이 속지에 맞춰 그려집니다.
       · check   투두리스트   — 체크 동그라미 + Add + 완료는 아래로 (예전 그대로)
       · memo    모눈 메모   — 모눈종이 바탕에 제목·본문을 자유롭게 쓰는 메모 카드
       · review  별점 리뷰   — 별점(1~5)·장소·날짜·한줄평
       · expense 지출·정산   — 항목 + 금액, 위에 합계 자동
     예전에 만들어 둔 「memo」 리스트는 그대로 모눈 메모로 이어집니다.
     ========================================================================== */
  var LIST_KIND_DEF = {
    check:   { n: "투두리스트", d: "리스트를 카드로 묶어서" },
    memo:    { n: "모눈 메모", d: "모눈 바탕에 자유롭게" },
    review:  { n: "별점 리뷰", d: "별점·장소·한줄평" },
    expense: { n: "지출·정산", d: "금액을 적으면 합계까지" }
  };
  var LIST_KINDS = ["check", "memo", "review", "expense"];
  function listKindOf(l) {
    var k = l && l.kind;
    return LIST_KIND_DEF[k] ? k : "check";
  }

  /* ==========================================================================
     v39: 카테고리마다 속지 고르기 — 기본 카테고리(메모·버킷리스트·영화·먹방)도
     --------------------------------------------------------------------------
     v38 은 «내가 만든 카테고리»만 속지를 골랐어요. v39 부터는 + 시트의 카테고리 줄을
     누르면 그 카테고리의 속지를 그 자리에서 바꿀 수 있고, 기본 카테고리도 같은 네 속지로
     그려집니다(고르지 않으면 지금 모양 그대로 = 카드).
       · S.noteKinds = { todo|bucket|log: "check"|"memo"|"review"|"expense" }
       · 기본 카테고리를 속지로 보면 그 탭의 항목(S.todos·S.bucket·S.logs)이 한 장에 펼쳐져요.
         항목은 그대로라 「카드」로 되돌리면 원래 카드가 다시 보입니다.
     ========================================================================== */
  var BASE_SEG = "base:";                 /* 기본 카테고리 속지 화면의 가상 리스트 id */
  function noteBaseKind(k) { return (S.noteKinds || {})[k] || ""; }
  function baseContainer(k) {
    return { id: BASE_SEG + k, base: k, kind: noteBaseKind(k) || "check", items: itemsOf(k) };
  }
  function isBaseContainer(c) { return !!(c && c.base); }
  /* 화면의 data-list 값 → 진짜 리스트(내 카테고리) 또는 기본 카테고리의 속지 화면
     v40: 투두리스트 카드 안에서는 data-list="list:<id>" 도 써요 */
  function containerOf(id) {
    id = String(id == null ? "" : id);
    if (id.indexOf(BASE_SEG) === 0 && NOTE_BASE.indexOf(id.slice(BASE_SEG.length)) >= 0) {
      return baseContainer(id.slice(BASE_SEG.length));
    }
    if (isListSeg(id)) return findList(id.slice(LIST_SEG.length));
    return findList(id);
  }
  /* 속지 화면이 항목의 «제목·본문»을 읽고 쓰는 자리 — 기본 카테고리는 탭마다 이름이 달라요
     (메모 text / 버킷·영화·먹방 title, 메모·버킷 memo / 영화·먹방 review) */
  function itTitle(it) {
    if (!it) return "";
    if (it.text != null && it.text !== "") return String(it.text);
    return String(it.title == null ? "" : it.title);
  }
  function itBody(it) {
    if (!it) return "";
    if (it.memo != null && it.memo !== "") return String(it.memo);
    return String(it.review == null ? "" : it.review);
  }
  function setItTitle(it, v) {
    if (!it) return;
    if (it.text === undefined) it.title = v; else it.text = v;
  }
  function setItBody(it, v) {
    if (!it) return;
    if (it.memo === undefined) it.review = v; else it.memo = v;
  }
  /* 기본 카테고리 속지 화면에서 항목 더하기 — 탭에 맞는 이름으로 넣고, 소속 카드는 첫 번째 카드 */
  function basePush(k, f) {
    var it = { id: uid(), done: false };
    if (k === "todo") { it.text = f.text || ""; it.memo = f.memo || ""; }
    else if (k === "bucket") { it.title = f.text || ""; it.memo = f.memo || ""; it.cat = "기타"; }
    else {
      it.title = f.text || ""; it.review = f.memo || "";
      it.kind = "movie"; it.rating = f.rating != null ? f.rating : 0; it.place = f.place || ""; it.done = true;
    }
    if (f.rating != null) it.rating = f.rating;
    if (f.place != null) it.place = f.place;
    if (f.amount != null) it.amount = f.amount;
    /* v45: 지출·정산 속지에서 적은 입금/지출·카테고리·누가 */
    if (f.txType) it.txType = f.txType === "deposit" ? "deposit" : "expense";
    if (f.cat != null) it.cat = String(f.cat);
    if (f.who) it.who = f.who;
    it.date = f.date ? String(f.date).slice(0, 10) : today;
    it.gid = firstGroupId(k) || "";
    itemsOf(k).push(it);
    return it;
  }
  /* 기본 카테고리 속지 화면의 머리 — 카테고리 이름만
     v41: 이름 옆 속지 배지 없앰 · v42: 오른쪽 「투두리스트」 되돌리기 버튼도 없앰
     (속지 변경·해제는 노트 「+」 설정 시트에서만 해요) */
  function basePageHead(k, kind) {
    return '<div class="note-hd"><div class="nh-l"><span class="t">' + esc(noteLabel(k)) + "</span></div></div>";
  }
  /* 금액 — 「12,000」·「12000원」·「-3,000」 모두 숫자로 */
  function parseAmount(v) {
    var s = String(v == null ? "" : v).replace(/[^\d-]/g, "");
    var n = Number(s);
    return isFinite(n) ? Math.round(n) : 0;
  }
  function wonTxt(n) {
    var v = Math.round(Number(n) || 0);
    return (v < 0 ? "-" : "") + won(Math.abs(v)) + "원";
  }
  function itemDateTxt(d) {
    return String(d || "").slice(0, 10).replace(/-/g, ".");
  }

  function viewList(l) {
    if (!l) return '<div class="list" style="margin:0 20px"><div class="empty">리스트를 찾을 수 없어요.</div></div>';
    /* v41: 카테고리 이름 옆에 붙던 속지 배지(모눈 메모·투두리스트…)는 없앴어요 */
    var h = '<div class="note-hd"><div class="nh-l"><span class="t">' + esc(listLabel(l)) + "</span></div></div>";
    return h + viewListBody(l);
  }
  /* v39: 속지 본문만 — 기본 카테고리 속지 화면도 같은 본문을 씁니다 */
  function viewListBody(l) {
    if (!l) return "";
    var kind = listKindOf(l);
    /* v40: 투두리스트 속지는 2열 카드 묶음 + 「+ 새 리스트」 (기본 카테고리도 같은 화면) */
    if (kind === "check") return viewCards(isBaseContainer(l) ? l.base : LIST_SEG + l.id);
    if (kind === "memo") return viewListMemo(l);
    if (kind === "review") return viewListReview(l);
    if (kind === "expense") return viewListExpense(l);
    return "";
  }
  /* v39: 기본 카테고리를 속지로 보기(메모·버킷리스트·영화·먹방 탭에서 고른 경우) */
  function viewBasePage(k) {
    var kind = noteBaseKind(k) || "check";
    return basePageHead(k, kind) + viewListBody(baseContainer(k));
  }

  /* 속지 공통: 맨 위 빠른 추가 한 줄 (이름 + [금액] + Add) */
  function quickAddForm(l, kind, ph) {
    return '<form class="todo-add qadd-list" id="listQuickForm" data-list="' + l.id + '" data-kind="' + kind + '">' +
      '<input class="todo-in" name="text" placeholder="' + esc(ph) + '" autocomplete="off" enterkeyhint="done" aria-label="내용">' +
      (kind === "expense" ? '<input class="todo-in ex-in" name="amount" inputmode="numeric" placeholder="금액" autocomplete="off" aria-label="금액">' : "") +
      '<button class="todo-add-btn" type="submit">Add</button></form>';
  }

  /* 1) 투두리스트 — 예전과 똑같이 ○ + 입력 + Add, 완료는 아래로 */
  /* v40: 예전「투두리스트」한 줄 체크 화면(viewListCheck)은 없앴어요 —
     이제 투두리스트 속지는 viewCards() 의 2열 카드 묶음 + 「+ 새 리스트」로 그립니다. */

  /* 2) 모눈 메모 — 모눈종이 바탕의 제목·본문 카드. 눌러서 본문을 써요 (v40) */
  /* v40: 모눈 메모 카드의 날짜 머리 — 「2026.11.21 토요일」 */
  function memoDayLabel(ds) {
    var d = parse(String(ds || today).slice(0, 10));
    if (!d || isNaN(d.getTime())) return itemDateTxt(ds);
    return d.getFullYear() + "." + pad(d.getMonth() + 1) + "." + pad(d.getDate()) + " " + DOW_FULL[d.getDay()];
  }

  /* 2) 모눈 메모 (v41) — 모눈종이 바탕 위에 다이어리 카드가 세로로 쌓여요.
     카드를 누르면 그 다이어리가, 맨 아래 「+ 새 다이어리」를 누르면 새 다이어리가
     화면을 꽉 채우는 모눈종이 다이어리로 열립니다. */
  function viewListMemo(l) {
    var h = '<div class="todo-block d41-list" data-list="' + l.id + '">';
    h += '<div class="memo-list nmemo-list d41-cards" data-list="' + l.id + '">';
    if (!l.items.length) {
      h += '<button type="button" class="d41-empty" data-act="openDiary" data-list="' + l.id + '">' +
        '<span class="de-t">아직 다이어리가 없어요</span><span class="de-s">+ 새 다이어리</span></button>';
    }
    l.items.forEach(function (it) {
      var body = itBody(it);
      var imgs = diaryImgsOf(it);
      h += '<article class="memo-card nmemo-card d41-card" data-act="openDiary" data-list="' + l.id + '" data-id="' + it.id + '" role="button" tabindex="0">' +
        '<div class="mc-d nmemo-date">' + esc(memoDayLabel(it.date)) + "</div>" +
        (itTitle(it) ? '<div class="mc-t nmemo-t">' + esc(itTitle(it)) + "</div>" : "") +
        (body ? '<div class="mc-b nmemo-b">' + esc(body) + "</div>" : "") +
        (imgs.length ? '<div class="d41-thumbs">' + imgs.slice(0, 3).map(function (im) {
          return '<img class="d41-th" src="' + esc(im.src) + '" alt="다이어리 사진" loading="lazy" decoding="async">';
        }).join("") + (imgs.length > 3 ? '<span class="d41-thn">+' + (imgs.length - 3) + "</span>" : "") + "</div>" : "") +
        (it.pen && it.pen.length ? '<div class="d41-penz">손그림</div>' : "") +
        '<button type="button" class="x nmemo-x" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="삭제">' + IC.x + "</button></article>";
    });
    h += "</div>";
    h += '<button type="button" class="d41-new" data-act="openDiary" data-list="' + l.id + '">' +
      '<span class="ap">' + IC.plus + '</span><span>새 다이어리</span></button>';
    h += "</div>";
    return h;
  }

  /* ==========================================================================
     v41: 모눈종이 풀스크린 다이어리
     --------------------------------------------------------------------------
     카드를 누르면 화면 전체가 모눈종이 다이어리로 열려요.
       위   ‹ 뒤로 · 제목(가운데) · 저장
       그 아래 11.21 SAT 큰 날짜 (눌러서 날짜 바꾸기)
       가운데 모눈 캔버스 (본문 · 사진 · 손그림)
       맨 아래 T(글씨) · 🖼(사진) · ✏(펜) 도구
     저장한 값은 예전 메모 항목 그대로에 담겨요:
       text = 제목, memo = 본문, date = 날짜,
       imgs = [{id, src, size}]  사진 여러 장(720px 로 줄여 보관), size 1·2·3 = 작게·보통·크게
       sty  = {size: 1|2|3, color, align}   글씨 크기·색·정렬
       pen  = [{c, w, p: [x,y,...]}]        손그림 — 폭 기준 0~1 좌표라 폰 폭이 달라도 그대로
     예전(v40) 메모의 사진 한 장(it.img)은 첫 사진으로 이어받아요.
     ========================================================================== */
  var DOW_ENG = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"];
  var D41_SIZES = [0, 14, 16.5, 19];
  var D41_COLORS = ["", "#6E6E73", "#B4564E", "#3D6E8A", "#5E7A52"];
  /* v45: 글씨 색 «전체 컬러판» — 색 동그라미를 누르면 이 판이 펼쳐져요 */
  /* v47: 프리셋 9색 — 날씨의 요정 팔레트(코랄·핑크·보라·파랑·초록·노랑·주황·갈색) + 검정.
     (v46 까지의 차분한 9색을 대신해요) */
  var D41_TCOLORS = ["#111111", "#F46B62", "#DC4A98", "#9268C9", "#4E8EC1", "#4FA78E", "#F7CE46", "#F69B42", "#8D6F61"];
  var diary = null;

  function d41Stamp(ds) {
    var d = parse(String(ds || today).slice(0, 10));
    if (!d || isNaN(d.getTime())) return "";
    return (d.getMonth() + 1) + "." + pad(d.getDate()) + " " + DOW_ENG[d.getDay()];
  }
  /* --------------------------------------------------------------------------
     v42: 모눈종이 캔버스 다이어리 (그림판처럼)
       · 종이(모눈)는 위 상단 바 바로 아래부터 깔리고, 내용이 내려가면 함께 길어져요
       · 글  texts: [{id, x, y, text, size, color, align}]   x·y = 종이 «폭» 기준 비율(0~1)
       · 사진 imgs: [{id, src, x, y, w}]                     w = 종이 폭에서 차지하는 비율
       · 펜  pen:  [{c, w, p: [x,y,...]}]                    폭 기준 좌표 (v41 그대로)
       좌표를 폭 기준으로 두니 폰 폭이 달라도 같은 자리에 놓입니다.
     -------------------------------------------------------------------------- */
  var D41_MINW = 0.16;          /* 사진 최소 폭 (종이 폭 대비) */
  var D41_TXMIN = 12, D41_TXMAX = 40;
  var d41CropState = null;
  /* v43: 두 손가락으로 사진을 벌리거나 오므려 크기 바꾸기 */
  var d41Pointers = {};         /* pointerId → {x, y, id} */
  var d41TapKey = "", d41TapAt = 0;   /* 글 상자를 두 번 톡 누르면 입력(키보드) */
  var d41Pinch = null;          /* {id, im, d0, w0, x0, y0, mx, my} */

  function d41Num(v, d) { var n = Number(v); return isFinite(n) ? n : d; }
  function d41Clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
  function d41WPx() {
    var p = document.getElementById("d41Paper");
    return Math.max(1, p ? p.clientWidth : 360);
  }

  /* 저장된 글 상자 — v41 의 한 덩어리 본문(memo)은 첫 글 상자로 이어받아요 */
  function diaryTextsOf(it) {
    var out = [];
    if (it && Array.isArray(it.texts)) {
      it.texts.forEach(function (t) {
        if (!t) return;
        out.push({
          id: String(t.id || uid()),
          x: d41Clamp(d41Num(t.x, 0.05), 0, 0.92),
          y: Math.max(0, d41Num(t.y, 0.18)),
          text: String(t.text == null ? "" : t.text),
          size: d41Clamp(d41Num(t.size, 16.5), D41_TXMIN, D41_TXMAX),
          color: typeof t.color === "string" ? t.color : "",
          bold: t.bold ? 1 : 0, strike: t.strike ? 1 : 0, underline: t.underline ? 1 : 0,
          align: t.align === "center" ? "center" : t.align === "right" ? "right" : "left"
        });
      });
    }
    if (!out.length && it && String(itBody(it) || "").trim()) {
      var st = diaryStyOf(it);
      out.push({
        id: uid(), x: 0.05, y: 0.2, text: String(itBody(it)),
        size: d41Clamp(D41_SIZES[st.size] || 16.5, D41_TXMIN, D41_TXMAX),
        color: st.color || "", align: st.align === "center" ? "center" : "left"
      });
    }
    return out;
  }
  /* 저장된 사진 — v41 처럼 «크기(작게·보통·크게)» 만 있던 사진은 그 크기로 아래에 차곡차곡 */
  function diaryImgsOf(it) {
    var out = [];
    if (it && Array.isArray(it.imgs)) {
      it.imgs.forEach(function (im, i) {
        if (!im || !im.src) return;
        var sz = Number(im.size);
        var w0 = im.w != null ? d41Clamp(d41Num(im.w, 0.74), D41_MINW, 1)
          : (sz === 1 ? 0.46 : sz === 3 ? 1 : 0.74);
        out.push({
          id: String(im.id || uid()),
          src: String(im.src),
          x: im.x != null ? d41Clamp(d41Num(im.x, 0.05), 0, 1 - D41_MINW) : 0.05,
          y: im.y != null ? Math.max(0, d41Num(im.y, 0.62 + i * 0.45)) : 0.62 + i * 0.45,
          w: w0
        });
      });
    }
    if (!out.length && it && it.img) out.push({ id: "legacy", src: String(it.img), x: 0.05, y: 0.62, w: 0.74 });
    return out;
  }
  function diaryStyOf(it) {
    var s = (it && it.sty) || {};
    var sz = Number(s.size);
    return {
      size: sz === 1 || sz === 3 ? sz : 2,
      color: typeof s.color === "string" ? s.color : "",
      align: s.align === "center" ? "center" : "left"
    };
  }
  function diaryPenOf(it) {
    if (!it || !Array.isArray(it.pen)) return [];
    return it.pen.filter(function (s) { return s && Array.isArray(s.p) && s.p.length >= 4; })
      .map(function (s) {
        /* v44: 그림 한 획마다 id — 고르기·끌어 옮기기에 씁니다 */
        return { id: String(s.id || uid()), hl: s.hl ? 1 : 0,
                 c: String(s.c || "#111111"), w: Number(s.w) || 3.5,
                 p: s.p.map(function (v) { return Number(v) || 0; }) };
      });
  }

  function d41TxHtml(t) {
    var sel = diary && diary.sel === "tx:" + t.id;
    var W = d41WPx();
    var ta = t.align === "center" ? "center" : t.align === "right" ? "right" : "left";
    var deco = [t.strike ? "line-through" : "", t.underline ? "underline" : ""].filter(Boolean).join(" ");
    /* v44: 보기(스크롤) 모드에서는 글 상자를 고칠 수 없게 — 종이를 톡 누르면 고치기로 바뀌어요 */
    return '<div class="d41-tx' + (sel ? " sel" : "") + '" data-tx="' + esc(t.id) + '"' +
      ' style="left:' + (t.x * 100).toFixed(2) + "%; top:" + Math.round(t.y * W) + "px; font-size:" + t.size + "px;" +
      (t.color ? "color:" + t.color + ";" : "") +
      (t.bold ? "font-weight:700;" : "") +
      (deco ? "text-decoration:" + deco + ";" : "") +
      "text-align:" + ta + '">' +
      '<div class="d41-txt" contenteditable="' + (diary && diary.editing === false ? "false" : "true") + '" spellcheck="false" data-txedit="' + esc(t.id) + '"' +
      ' data-ph="글을 써 보세요" aria-label="다이어리 글">' + esc(t.text) + "</div>" +
      '<button type="button" class="d41-txx" data-act="d41TxDel" data-tx="' + esc(t.id) + '" aria-label="글 삭제">' + IC.x + "</button></div>";
  }
  function d41ImgHtml(im) {
    var sel = diary && diary.sel === "img:" + im.id;
    var W = d41WPx();
    return '<div class="d41-imgb' + (sel ? " sel" : "") + '" data-img="' + esc(im.id) + '"' +
      ' style="left:' + (im.x * 100).toFixed(2) + "%; top:" + Math.round(im.y * W) + "px; width:" + (im.w * 100).toFixed(2) + '%">' +
      '<img src="' + esc(im.src) + '" alt="다이어리 사진" draggable="false">' +
      '<button type="button" class="d41-imgx" data-act="d41ImgDel" data-img="' + esc(im.id) + '" aria-label="사진 삭제">' + IC.x + "</button>" +
      '<span class="d41-rz" data-rz="' + esc(im.id) + '" aria-hidden="true"></span></div>';
  }
  /* v44: 아이폰 메모장처럼 — 이미 쓴 다이어리는 처음에 «보기(스크롤)»로 열리고,
     종이를 톡 누르면 «고치기»로 바뀌어요 (새 다이어리는 바로 고치기). */
  function d41SetEditing(on) {
    if (!diary) return;
    diary.editing = !!on;
    var tools = document.querySelector(".d41-tools");
    if (tools) {
      tools.hidden = !diary.editing;
      /* v47: 보기 화면에서 종이를 톡 눌러 고치기로 바뀔 때 도구 줄이 부드럽게 내려와요 */
      if (diary.editing) {
        tools.classList.remove("tools-in");
        void tools.offsetWidth;
        tools.classList.add("tools-in");
      }
    }
    /* v47: 보기(스크롤) 모드에서는 글 상자 위에서도 화면을 밀어 넘기고 글자를 고를 수 있어요 */
    var paperEl = document.getElementById("d41Paper");
    if (paperEl) paperEl.classList.toggle("view", !diary.editing);
    if (!diary.editing) {
      var panel = document.getElementById("d41Panel");
      if (panel) panel.hidden = true;
      d41BlurAll();
      diary.sel = null;
    }
    d41RenderNodes();
  }
  function d41NodesHtml() {
    if (!diary) return "";
    var h = "";
    diary.imgs.forEach(function (im) { h += d41ImgHtml(im); });
    diary.texts.forEach(function (t) { h += d41TxHtml(t); });
    return h;
  }
  function d41RenderNodes() {
    var box = document.getElementById("d41Nodes");
    if (!box || !diary) return;
    box.innerHTML = d41NodesHtml();
    d41Grow();
    d41Sync();
  }

  /* 화면의 글 상자 글씨를 그대로 모델에 담아요 — 조합 중이던 마지막 글자까지 (저장 직전에 꼭) */
  function d41CommitTexts() {
    if (!diary) return;
    var boxes = document.querySelectorAll("#d41Nodes .d41-tx");
    Array.prototype.forEach.call(boxes, function (box) {
      var id = box.getAttribute("data-tx");
      var ed = box.querySelector(".d41-txt");
      var o = (diary.texts || []).filter(function (x) { return x.id === id; })[0];
      if (o && ed) o.text = String(ed.innerText || "").replace(/\u00a0/g, " ");
    });
  }

  /* 손그림 — 종이 폭을 1로 본 좌표(0~1)를 그대로 폰 폭에 맞춰 그립니다 */
  function d41Paint() {
    var svgEl = document.getElementById("d41Pen");
    var paper = document.getElementById("d41Paper");
    if (!svgEl || !paper || !diary) return;
    var W = Math.max(1, Math.round(paper.clientWidth));
    var H = Math.max(1, Math.round(paper.offsetHeight || paper.scrollHeight || 1));
    svgEl.setAttribute("viewBox", "0 0 " + W + " " + H);
    var out = "";
    diary.pen.forEach(function (s) {
      if (!s.p || s.p.length < 4) return;
      var d = "";
      for (var i = 0; i < s.p.length; i += 2) {
        d += (i ? "L" : "M") + (s.p[i] * W).toFixed(1) + " " + (s.p[i + 1] * W).toFixed(1);
      }
      /* v44: 형광펜(stroke hl)은 반투명하게 */
      out += '<path d="' + d + '" fill="none" stroke="' + esc(s.c) + '" stroke-width="' + s.w +
        '" stroke-linecap="round" stroke-linejoin="round"' + (s.hl ? ' stroke-opacity="0.35"' : "") + "/>";
    });
    /* v44: 고른 그림에는 점선 테두리와 × 지우기 단추 */
    var selPen = d41SelPen();
    var oldX = document.getElementById("d41PenX");
    if (oldX && oldX.parentNode) oldX.parentNode.removeChild(oldX);
    if (selPen) {
      var minX = 1e9, minY = 1e9, maxX = -1e9, maxY = -1e9;
      for (var i = 0; i < selPen.p.length; i += 2) {
        minX = Math.min(minX, selPen.p[i] * W); maxX = Math.max(maxX, selPen.p[i] * W);
        minY = Math.min(minY, selPen.p[i + 1] * W); maxY = Math.max(maxY, selPen.p[i + 1] * W);
      }
      var pad = 8;
      out += '<rect x="' + (minX - pad).toFixed(1) + '" y="' + (minY - pad).toFixed(1) +
        '" width="' + Math.max(10, maxX - minX + pad * 2).toFixed(1) +
        '" height="' + Math.max(10, maxY - minY + pad * 2).toFixed(1) +
        '" fill="none" stroke="var(--ink-3)" stroke-dasharray="4 4" stroke-width="1"/>';
      var xbtn = document.createElement("button");
      xbtn.type = "button";
      xbtn.id = "d41PenX";
      xbtn.className = "d41-imgx d41-penx";
      xbtn.setAttribute("aria-label", "그림 지우기");
      xbtn.style.left = Math.max(0, minX - pad - 10) + "px";
      xbtn.style.top = Math.max(0, minY - pad - 10) + "px";
      xbtn.innerHTML = IC.x;
      xbtn.addEventListener("pointerdown", function (ev) {
        ev.preventDefault();
        ev.stopPropagation();
        d41DelPen(selPen.id);
      });
      paper.appendChild(xbtn);
    }
    svgEl.innerHTML = out;
  }
  /* 내용이 아래로 내려가면 종이(모눈)도 같이 길어져요 — 최소한 화면 한 장은 채웁니다 */
  function d41Grow() {
    var paper = document.getElementById("d41Paper");
    var canvas = document.getElementById("d41Canvas");
    if (!paper || !diary) return;
    var W = Math.max(1, paper.clientWidth);
    var bottom = 0;
    Array.prototype.forEach.call(paper.querySelectorAll(".d41-tx, .d41-imgb"), function (el) {
      bottom = Math.max(bottom, el.offsetTop + el.offsetHeight);
    });
    diary.pen.forEach(function (s) {
      for (var i = 1; i < s.p.length; i += 2) bottom = Math.max(bottom, s.p[i] * W);
    });
    var base = Math.max(380, (canvas ? canvas.clientHeight : 0) - 2);
    paper.style.minHeight = Math.max(base, Math.ceil(bottom) + 130) + "px";
    d41Paint();
  }

  function d41Sync() {
    if (!diary) return;
    var im = document.getElementById("d41ImgsIn");
    if (im) im.value = JSON.stringify(diary.imgs.map(function (x) {
      return { id: x.id, src: x.src, x: x.x, y: x.y, w: x.w };
    }));
    var tx = document.getElementById("d41TextsIn");
    if (tx) tx.value = JSON.stringify(diary.texts.map(function (t) {
      return { id: t.id, x: t.x, y: t.y, text: t.text, size: t.size, color: t.color,
        bold: t.bold ? 1 : 0, strike: t.strike ? 1 : 0, underline: t.underline ? 1 : 0, align: t.align };
    }));
    var pe = document.getElementById("d41PenIn");
    if (pe) pe.value = JSON.stringify(diary.pen);
  }

  /* =====================================================================
     v44: 모눈 다이어리 되돌리기·다시 실행 — 글·사진·그림 상태를 스냅샷으로 기록해요
     ===================================================================== */
  var d41Hist = { stack: [], idx: -1 };
  function d41HistPush() {
    if (!diary) return;
    var s = JSON.stringify({ texts: diary.texts, imgs: diary.imgs, pen: diary.pen });
    if (d41Hist.stack[d41Hist.idx] === s) return;
    d41Hist.stack = d41Hist.stack.slice(0, d41Hist.idx + 1);
    d41Hist.stack.push(s);
    if (d41Hist.stack.length > 80) d41Hist.stack.shift();
    d41Hist.idx = d41Hist.stack.length - 1;
    d41HistRefresh();
  }
  function d41HistGo(step) {
    if (!diary) return;
    var next = d41Hist.idx + step;
    if (next < 0 || next >= d41Hist.stack.length) return;
    d41Hist.idx = next;
    var s = JSON.parse(d41Hist.stack[d41Hist.idx]);
    diary.texts = s.texts || [];
    diary.imgs = s.imgs || [];
    diary.pen = s.pen || [];
    diary.sel = null;
    d41RenderNodes();
    d41Paint();
    d41Sync();
    d41Grow();
    d41PanelRefresh();
    d41HistRefresh();
  }
  function d41HistRefresh() {
    var u = document.getElementById("d41UndoBtn"), r = document.getElementById("d41RedoBtn");
    if (u) u.disabled = d41Hist.idx <= 0;
    if (r) r.disabled = d41Hist.idx >= d41Hist.stack.length - 1;
  }

  function d41SelText() {
    if (!diary || !diary.sel || diary.sel.indexOf("tx:") !== 0) return null;
    var id = diary.sel.slice(3);
    return (diary.texts || []).filter(function (t) { return t.id === id; })[0] || null;
  }
  function d41SelImg() {
    if (!diary || !diary.sel || diary.sel.indexOf("img:") !== 0) return null;
    var id = diary.sel.slice(4);
    return (diary.imgs || []).filter(function (t) { return t.id === id; })[0] || null;
  }
  /* 고른 글 상자를 화면에서만 표시 (다시 그리지 않아 끌던 손가락이 끊기지 않아요) */
  function d41Select(sel) {
    if (!diary) return;
    diary.sel = sel;
    Array.prototype.forEach.call(document.querySelectorAll("#d41Nodes .d41-tx, #d41Nodes .d41-imgb"), function (el) {
      var k = el.classList.contains("d41-tx") ? "tx:" + el.getAttribute("data-tx") : "img:" + el.getAttribute("data-img");
      el.classList.toggle("sel", k === sel);
    });
    /* v43: 다른 곳을 고르면 방금 만든 빈 글 상자를 남기지 않아요 */
    d41PruneEmpty(sel && sel.indexOf("tx:") === 0 ? sel.slice(3) : "");
    var p = document.getElementById("d41Panel");
    if (!p) return;
    if (sel && sel.indexOf("img:") === 0) { p.hidden = false; p.innerHTML = d41ImgPanel(); d41Grow(); }
    else if (sel && sel.indexOf("tx:") === 0) { p.hidden = false; p.innerHTML = d41TextPanel(); d41Grow(); }
  }

  /* ---------------- v43: 빈 글 상자 정리 · 포커스 · 즉시 삭제 ---------------- */
  var d41Ime = false;                     /* 한글 조합 중에는 빈 상자를 지우지 않아요 */
  function d41EmptyText(t) { return !String(t && t.text != null ? t.text : "").replace(/\u00a0/g, " ").trim(); }
  function d41FocusedTx() {
    var a = document.activeElement;
    var box = a && a.closest ? a.closest(".d41-tx") : null;
    return box ? String(box.getAttribute("data-tx") || "") : "";
  }
  function d41BlurAll() {
    var a = document.activeElement;
    if (a && a.blur && a.classList && a.classList.contains("d41-txt")) { try { a.blur(); } catch (e) {} }
  }
  /* 아무 글자도 안 쓴 글 상자를 지워요 — exceptId 상자와 한글 조합 중인 상자는 남깁니다.
     화면은 통째로 다시 그리지 않고 그 상자만 걷어내서, 끌고 있던 다른 상자는 끊기지 않아요. */
  function d41PruneEmpty(exceptId) {
    if (!diary || d41Ime) return 0;
    var keep = String(exceptId || ""), gone = [];
    diary.texts = (diary.texts || []).filter(function (t) {
      if (t.id === keep || !d41EmptyText(t)) return true;
      gone.push(t.id);
      return false;
    });
    if (!gone.length) return 0;
    gone.forEach(function (id) {
      var el = document.querySelector('#d41Nodes .d41-tx[data-tx="' + id + '"]');
      if (el && el.parentNode) el.parentNode.removeChild(el);
      if (diary.sel === "tx:" + id) diary.sel = null;
    });
    d41Grow();
    d41Sync();
    return gone.length;
  }
  /* 글 상자에 입력(키보드) — 누른 자리에 커서를 놓아요 */
  function d41FocusText(id, x, y) {
    var ed = document.querySelector('#d41Nodes .d41-tx[data-tx="' + id + '"] .d41-txt');
    if (!ed) return;
    try { ed.focus(); } catch (e) {}
    try {
      var rng = null;
      if (x != null && document.caretRangeFromPoint) {
        var r = document.caretRangeFromPoint(x, y);
        if (r && ed.contains(r.startContainer)) rng = r;
      }
      if (!rng) {
        rng = document.createRange();
        rng.selectNodeContents(ed);
        rng.collapse(false);
      }
      var sl = window.getSelection && window.getSelection();
      if (sl) { sl.removeAllRanges(); sl.addRange(rng); }
    } catch (e) {}
  }
  function d41DelText(id) {
    if (!diary || !id) return;
    var before = (diary.texts || []).length;
    diary.texts = (diary.texts || []).filter(function (x) { return x.id !== id; });
    if (diary.texts.length === before) return;
    if (diary.sel === "tx:" + id) diary.sel = null;
    var el = document.querySelector('#d41Nodes .d41-tx[data-tx="' + id + '"]');
    if (el && el.parentNode) el.parentNode.removeChild(el);
    d41Grow();
    d41Sync();
    d41PanelRefresh();
    d41HistPush();
    d41AutoSave();
    toast("글 상자를 지웠어요");
  }
  function d41DelImg(id) {
    if (!diary || !id) return;
    var before = (diary.imgs || []).length;
    diary.imgs = (diary.imgs || []).filter(function (x) { return x.id !== id; });
    if (diary.imgs.length === before) return;
    if (diary.sel === "img:" + id) diary.sel = null;
    var el = document.querySelector('#d41Nodes .d41-imgb[data-img="' + id + '"]');
    if (el && el.parentNode) el.parentNode.removeChild(el);
    d41Grow();
    d41Sync();
    d41PanelRefresh();
    d41HistPush();
    d41AutoSave();
    toast("사진을 지웠어요");
  }

  function d41SetSize(px) {
    if (!diary) return;
    px = d41Clamp(Math.round(d41Num(px, 16.5)), D41_TXMIN, D41_TXMAX);
    var cur = d41SelText();
    if (cur) { cur.size = px; d41RenderNodes(); }
    else diary.tsize = px;
    d41Sync();
    d41HistPush();
  }
  /* v44: − + 크기 조절 — 1px 씩, 12~40 사이 */
  function d41SizeStep(d) {
    if (!diary) return;
    var cur = d41SelText();
    if (cur) { cur.size = d41Clamp(Math.round(cur.size) + d, D41_TXMIN, D41_TXMAX); d41RenderNodes(); }
    else diary.tsize = d41Clamp(Math.round(diary.tsize || 16.5) + d, D41_TXMIN, D41_TXMAX);
    d41PanelRefresh();
    d41Sync();
    d41HistPush();
  }
  function d41SetColor(c) {
    if (!diary) return;
    var cur = d41SelText();
    if (cur) { cur.color = c; d41RenderNodes(); } else diary.tcolor = c;
    diary.cpick = false;
    d41SpShut();            /* v46: 프리셋을 고르면 스펙트럼 판도 따라 닫혀요 */
    d41PanelRefresh();
    d41Sync();
    d41HistPush();
    d41AutoSave();
  }
  /* v44: 글 상자 모양 — 굵게·취소선·밑줄 · 정렬은 왼쪽→가운데→오른쪽으로 돌아가요 */
  function d41SetTFlag(flag) {
    if (!diary) return;
    var cur = d41SelText();
    if (cur) { cur[flag] = cur[flag] ? 0 : 1; d41RenderNodes(); }
    else {
      var key = "t" + flag;
      diary[key] = !diary[key];
    }
    d41PanelRefresh();
    d41Sync();
    d41HistPush();
  }
  function d41CycleAlign() {
    if (!diary) return;
    var order = ["left", "center", "right"];
    var cur = d41SelText();
    var now = cur ? cur.align : (diary.talign || "left");
    var next = order[(order.indexOf(now) + 1) % 3];
    if (cur) { cur.align = next; d41RenderNodes(); } else diary.talign = next;
    d41PanelRefresh();
    d41Sync();
    d41HistPush();
  }
  function d41ApplyStyle() { d41Sync(); d41PanelRefresh(); }

  function d41ToolsHtml() {
    var mode = diary ? diary.mode : "text";
    /* v46: ↶ ↷ 는 도구 줄 «맨 왼쪽», 펜·T·사진은 «오른쪽»으로 (예전엔 반대였어요) */
    /* v44: 이미 쓴 다이어리는 처음에 보기(스크롤)로 열려요 — 도구 바는 고칠 때 나타나요 */
    return '<div class="d41-tools"' + (diary && diary.editing === false ? " hidden" : "") + '>' +
      '<button type="button" class="d41-ub" id="d41UndoBtn" data-act="d41Undo" aria-label="되돌리기" title="되돌리기" disabled>' + IC.undo + "</button>" +
      '<button type="button" class="d41-ub" id="d41RedoBtn" data-act="d41Redo" aria-label="다시 실행" title="다시 실행" disabled>' + IC.redo + "</button>" +
      '<span class="d41-tools-gap"></span>' +
      '<button type="button" class="d41-tool' + (mode === "pen" ? " on" : "") + '" data-act="d41Pen" aria-label="펜 그리기">' + IC.pencil + "</button>" +
      '<button type="button" class="d41-tool d41-tool-t' + (mode === "text" ? " on" : "") + '" data-act="d41Text" aria-label="글씨">T</button>' +
      '<button type="button" class="d41-tool" data-act="d41Img" aria-label="사진 넣기">' + IC.photo + "</button>" +
      "</div>";
  }
  /* v44: T 도구 — 누르면 새 글 상자를 만들어요 (배경을 누르면 이제 글쓰기가 끝나요).
     이미 글 상자를 고른 채면 지금 글을 마무리하고 그 아래에 새 상자를 만들어요. */
  function d41TextTool() {
    if (!diary) return;
    if (diary.mode !== "text") { d41PanelOpen("text"); return; }
    d41CommitTexts();
    d41BlurAll();
    d41PruneEmpty("");
    var W = d41WPx();
    var bottom = 0;
    Array.prototype.forEach.call(document.querySelectorAll("#d41Nodes .d41-tx, #d41Nodes .d41-imgb"), function (el) {
      bottom = Math.max(bottom, el.offsetTop + el.offsetHeight);
    });
    (diary.pen || []).forEach(function (s) {
      for (var i = 1; i < s.p.length; i += 2) bottom = Math.max(bottom, s.p[i] * W);
    });
    var canvas = document.getElementById("d41Canvas");
    var y = Math.max(0.2, (canvas ? canvas.scrollTop / W : 0) + (bottom ? bottom / W + 0.3 : 0.2));
    d41AddTextAt(0.06, y);
  }
  /* T 패널 — 「작게·보통·크게」 옆에 가로 슬라이더(12~40px)로 세밀하게 */
  /* v44: 글씨 도구 — 가늘고 긴 두 줄: 정렬·B·S·U·색 동그라미 / − 크기 +
     (예전의 작게·보통·크게·슬라이더·색 점·정렬 줄은 정리했어요) */
  /* v45: 글씨 도구도 «한 줄» — [정렬 B S U − 크기 + 색 동그라미]
     · 단추를 조금 크게, 색 동그라미는 작게(22px)
     · 색 동그라미를 누르면 «전체 컬러판» 이 아래에 펼쳐져요
     · 「글 수정 / 키보드 내리기」 줄과 안내 글씨는 없앴어요 (상자를 한 번 더 톡 누르면 입력) */
  function d41TextPanel() {
    var cur = d41SelText();
    var size = cur ? cur.size : (diary.tsize || 16.5);
    var color = cur ? cur.color : (diary.tcolor || "");
    var align = cur ? cur.align : (diary.talign || "left");
    var bold = cur ? !!cur.bold : !!diary.tbold;
    var strike = cur ? !!cur.strike : !!diary.tstrike;
    var under = cur ? !!cur.underline : !!diary.tunderline;
    var aico = align === "center" ? IC.alignC : align === "right" ? IC.alignR : IC.alignL;
    var h = '<div class="d41-prow d41-trow">' +
      '<button type="button" class="d41-tb d41-tb-lg" data-act="d41Align" aria-label="정렬 바꾸기">' + aico + "</button>" +
      '<button type="button" class="d41-tb d41-tb-lg d41-tb-b' + (bold ? " on" : "") + '" data-act="d41Bold" aria-label="굵게">B</button>' +
      '<button type="button" class="d41-tb d41-tb-lg d41-tb-s' + (strike ? " on" : "") + '" data-act="d41Strike" aria-label="취소선">S</button>' +
      '<button type="button" class="d41-tb d41-tb-lg d41-tb-u' + (under ? " on" : "") + '" data-act="d41Underline" aria-label="밑줄">U</button>' +
      '<span class="d41-tsep"></span>' +
      '<button type="button" class="d41-tb d41-tb-sm" data-act="d41SizeStep" data-d="-1" aria-label="글씨 작게">−</button>' +
      '<span class="d41-pv">' + Math.round(size) + "</span>" +
      '<button type="button" class="d41-tb d41-tb-sm" data-act="d41SizeStep" data-d="1" aria-label="글씨 크게">+</button>' +
      '<span class="d41-trow-gap"></span>' +
      '<button type="button" class="d41-tc d41-tc-sm' + (diary.sp === "text" ? " on" : "") + '" data-act="d41ColorPick" aria-label="글씨 색 고르기" ' +
        'style="background:' + (color || "#111111") + '"></button>' +
      "</div>";
    return h;
  }
  function d41ImgPanel() {
    var im = d41SelImg();
    var h = '<div class="d41-prow"><span class="d41-pl">사진</span><div class="d41-pbtns">' +
      '<button type="button" class="d41-pb" data-act="d41ImgCrop" data-img="' + esc(im ? im.id : "") + '">자르기</button>' +
      '<button type="button" class="d41-pb" data-act="d41ImgDel" data-img="' + esc(im ? im.id : "") + '">삭제</button>' +
      "</div></div>";
    h += '<div class="d41-phint">사진을 끌어 옮기고, 오른쪽 아래 모서리를 끌어 크기를 바꿔요.</div>';
    return h;
  }
  /* v45: 펜을 누르면 «한 줄짜리 그림 도구 판» — 글씨 라벨 없이 펜촉 그림만.
     가는 펜 · 일반 펜 · 형광펜 · 지우개 · 색 동그라미 · 전체 지우기 (굵기 글씨·슬라이더는 없앰) */
  function d41PenTipSvg(color, thick) {
    /* 가는 펜은 몸통도 가늘게, 일반 펜은 굵게 — 한눈에 구분되도록 */
    var nib = thick ? "M12 1.4 16.4 8.8H7.6z" : "M12 1.6 13.9 8.8H10.1z";
    var body = thick ? '<rect x="7.6" y="8.8" width="8.8" height="13.4" rx="1.8"/><path d="M7.6 12.8h8.8M7.6 17.4h8.8"/>'
                     : '<rect x="9.2" y="8.8" width="5.6" height="13.4" rx="1.5"/><path d="M9.2 12.8h5.6M9.2 17.4h5.6"/>';
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">' +
      '<path d="' + nib + '" fill="' + color + '" stroke="' + color + '"/>' + body + "</svg>";
  }
  function d41HlTipSvg(color) {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linejoin="round">' +
      '<path d="M8.4 2.6h7.2l2.8 5.2H5.6z" fill="' + color + '" stroke="' + color + '"/>' +
      '<rect x="6.6" y="7.8" width="10.8" height="9.6" rx="1.5"/>' +
      '<path d="M6.6 16.4h10.8l-1 4H7.6z"/></svg>';
  }
  function d41PenPanel() {
    var w = Number(diary.pw) || 3.5;
    var thinOn = diary.pmode === "pen" && Math.abs(w - 2) < 0.6;
    var normOn = diary.pmode === "pen" && !thinOn;
    var h = '<div class="d41-prow d41-prow-dock"><div class="d41-dock">';
    h += '<button type="button" class="d41-dk' + (thinOn ? " on" : "") + '" data-act="d41PenMode" data-mode="pen" data-w="2" aria-label="가는 펜" title="가는 펜">' +
      d41PenTipSvg(diary.pcolor, false) + "</button>";
    h += '<button type="button" class="d41-dk' + (normOn ? " on" : "") + '" data-act="d41PenMode" data-mode="pen" data-w="4.5" aria-label="일반 펜" title="일반 펜">' +
      d41PenTipSvg(diary.pcolor, true) + "</button>";
    h += '<button type="button" class="d41-dk' + (diary.pmode === "hl" ? " on" : "") + '" data-act="d41PenMode" data-mode="hl" aria-label="형광펜" title="형광펜">' +
      d41HlTipSvg(diary.pcolor) + "</button>";
    h += '<button type="button" class="d41-dk' + (diary.pmode === "erase" ? " on" : "") + '" data-act="d41PenMode" data-mode="erase" aria-label="지우개" title="지우개">' +
      IC.eraser + "</button>";
    h += '<span class="d41-dock-gap"></span>';
    h += '<button type="button" class="d41-dk d41-dk-color' + (diary.sp === "pen" ? " on" : "") + '" data-act="d41PenColorPick" aria-label="펜 색" title="펜 색">' +
      '<span class="d41-dkk" style="background:' + diary.pcolor + '"></span></button>';
    h += '<button type="button" class="d41-dk d41-dk-x" data-act="d41Clear" aria-label="전체 지우기" title="전체 지우기">' + IC.x + "</button>";
    h += "</div></div>";
    return h;
  }
  function d41PanelHtml() {
    if (!diary) return "";
    if (diary.mode === "pen") return d41PenPanel();
    if (diary.sel && diary.sel.indexOf("pen:") === 0) return d41PenSelPanel();
    if (d41SelImg()) return d41ImgPanel();
    return d41TextPanel();
  }
  function d41PanelRefresh() {
    var p = document.getElementById("d41Panel");
    if (p && diary) { p.innerHTML = d41PanelHtml(); d41Grow(); }
  }
  /* v44: 배경을 누르면 도구 판을 덮어 — 쓴 내용만 보이게 (도구를 다시 누르면 열려요) */
  function d41PanelHide() {
    var p = document.getElementById("d41Panel");
    if (p) p.hidden = true;
    var tools = document.querySelector(".d41-tools");
    if (tools) Array.prototype.forEach.call(tools.querySelectorAll(".d41-tool.on"), function (el) { el.classList.remove("on"); });
  }

  /* ========================================================================
     v46 — 색상 스펙트럼 판 (아이폰 메모의 «색상 · 스펙트럼» 과 같은 모양)
     · 펜 도크의 색 동그라미, 글씨 도구의 색 동그라미를 누르면 아래에서 올라와요
     · 가로 = 색(hue) · 세로 = 밝기 — 왼쪽은 하얗고 아래로 갈수록 어두워져요
     · 판을 톡 누르거나 손가락으로 끌면 그 자리 색이 바로 칠해지고 위에 #색이 따라와요
     · 아래 프리셋 색 9개 · 오른쪽 위 × 로 닫아요 (바깥을 눌러도 닫혀요)
     ======================================================================== */
  var d41SpDown = false;
  function d41Hex2(n) {
    var q = d41Clamp(Math.round(n), 0, 255).toString(16).toUpperCase();
    return q.length < 2 ? "0" + q : q;
  }
  function d41RgbHex(r, g, b) { return "#" + d41Hex2(r) + d41Hex2(g) + d41Hex2(b); }
  function d41SpRgb(fx, fy) {
    /* v47: 아이폰 «스펙트럼» 과 같은 방향으로 바꿈
       · 세로(y) = 색(hue) — 위 빨강 → 노랑 → 초록 → 하늘 → 파랑 → 자홍 → 아래 빨강
       · 가로(x) = 왼쪽 하양 → 가운데 순색 → 오른쪽 검정 */
    var x = d41Clamp(fx, 0, 1), y = d41Clamp(fy, 0, 1);
    var h = (((y * 360) % 360) + 360) % 360 / 60;
    var s = x <= 0.5 ? x * 2 : 1;
    var v = x <= 0.5 ? 1 : Math.max(0, 1 - (x - 0.5) * 2);
    var c = v * s, xx = c * (1 - Math.abs(h % 2 - 1)), m = v - c, r, g, b;
    if (h < 1) { r = c; g = xx; b = 0; }
    else if (h < 2) { r = xx; g = c; b = 0; }
    else if (h < 3) { r = 0; g = c; b = xx; }
    else if (h < 4) { r = 0; g = xx; b = c; }
    else if (h < 5) { r = xx; g = 0; b = c; }
    else { r = c; g = 0; b = xx; }
    return [Math.round((r + m) * 255), Math.round((g + m) * 255), Math.round((b + m) * 255)];
  }
  function d41SpDraw(cv) {
    var box = cv.getContext("2d");
    if (!box) return;
    var w = cv.width, h = cv.height;
    if (!w || !h) return;
    var img = box.createImageData(w, h), d = img.data, i = 0;
    for (var y = 0; y < h; y++) {
      var fy = h > 1 ? y / (h - 1) : 0;
      for (var x = 0; x < w; x++) {
        var c = d41SpRgb(w > 1 ? x / (w - 1) : 0, fy);
        d[i] = c[0]; d[i + 1] = c[1]; d[i + 2] = c[2]; d[i + 3] = 255;
        i += 4;
      }
    }
    box.putImageData(img, 0, 0);
  }
  /* 지금 색과 가장 가까운 판 위 자리 — 열 때 동그라미를 거기에 놓아요 */
  function d41SpFind(hex) {
    var m = /^#?([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})$/i.exec(String(hex || ""));
    if (!m) return [0.5, 0.02];
    var r = parseInt(m[1], 16), g = parseInt(m[2], 16), b = parseInt(m[3], 16);
    var best = [0.5, 0.02], bd = 1e9;
    for (var fy = 0; fy <= 1.0001; fy += 0.025) {
      for (var fx = 0; fx <= 1.0001; fx += 0.025) {
        var c = d41SpRgb(fx, fy);
        var dd = Math.pow(c[0] - r, 2) + Math.pow(c[1] - g, 2) + Math.pow(c[2] - b, 2);
        if (dd < bd) { bd = dd; best = [fx, fy]; }
      }
    }
    return best;
  }
  function d41SpCur() {
    if (!diary) return "#111111";
    if (diary.sp === "pen") return diary.pcolor || "#111111";
    var cur = d41SelText();
    return (cur ? cur.color : diary.tcolor) || "#111111";
  }
  function d41SpectrumHtml() {
    var color = String(d41SpCur()).toUpperCase();
    var pen = diary && diary.sp === "pen";
    var h = '<div class="d41-sp-bg" data-act="d41SpClose"></div>' +
      '<div class="d41-sp-card" role="dialog" aria-label="색상">' +
      '<div class="d41-sp-hd"><span class="d41-sp-tt">색상</span>' +
      '<button type="button" class="d41-sp-x" data-act="d41SpClose" aria-label="색상 닫기">' + IC.x + "</button></div>" +
      '<div class="d41-sp-box"><canvas class="d41-sp-cv" id="d41SpCv" aria-label="색상 스펙트럼"></canvas>' +
      '<span class="d41-sp-dot" id="d41SpDot" aria-hidden="true"></span></div>' +
      '<div class="d41-sp-ft"><span class="d41-sp-pv" id="d41SpPv" style="background:' + esc(color) + '"></span>' +
      '<span class="d41-sp-hex" id="d41SpHex">' + esc(color) + "</span></div>" +
      '<div class="d41-sp-dots">';
    D41_TCOLORS.forEach(function (c, i) {
      h += '<button type="button" class="d41-sp-dotb' + (color === c ? " on" : "") + '" data-act="' +
        (pen ? "d41PenColor" : "d41Color") + '" data-color="' + esc(c) + '" aria-label="색 ' + (i + 1) + '" style="background:' + c + '"></button>';
    });
    h += "</div></div>";
    return h;
  }
  function d41SpRing(fx, fy) {
    var dot = document.getElementById("d41SpDot");
    if (!dot) return;
    dot.style.left = (d41Clamp(fx, 0, 1) * 100).toFixed(2) + "%";
    dot.style.top = (d41Clamp(fy, 0, 1) * 100).toFixed(2) + "%";
  }
  function d41PaintTx(t) {
    var el = document.querySelector('#d41Nodes .d41-tx[data-tx="' + t.id + '"]');
    if (el) el.style.color = t.color || "";
  }
  function d41SpApply(hex, live) {
    if (!diary) return;
    hex = String(hex || "").toUpperCase();
    if (diary.sp === "pen") diary.pcolor = hex;
    else {
      var cur = d41SelText();
      if (cur) { cur.color = hex; if (live) d41PaintTx(cur); }
      else diary.tcolor = hex;
    }
    var sw = document.querySelector(diary.sp === "pen" ? "#d41Panel .d41-dkk" : "#d41Panel .d41-tc");
    if (sw) sw.style.background = hex;
  }
  function d41SpAt(ev, cv) {
    var b = cv.getBoundingClientRect();
    var fx = d41Clamp((ev.clientX - b.left) / Math.max(1, b.width), 0, 1);
    var fy = d41Clamp((ev.clientY - b.top) / Math.max(1, b.height), 0, 1);
    var c = d41SpRgb(fx, fy);
    var hex = d41RgbHex(c[0], c[1], c[2]);
    if (diary) { diary.spx = fx; diary.spy = fy; }
    d41SpRing(fx, fy);
    var hx = document.getElementById("d41SpHex");
    if (hx) hx.textContent = hex;
    var pv = document.getElementById("d41SpPv");
    if (pv) pv.style.background = hex;
    d41SpApply(hex, true);
  }
  function d41SpWire() {
    var cv = document.getElementById("d41SpCv");
    if (!cv) return;
    var dpr = Math.min(2.5, window.devicePixelRatio || 1);
    var b = cv.getBoundingClientRect();
    cv.width = Math.max(1, Math.round((b.width || 320) * dpr));
    cv.height = Math.max(1, Math.round((b.height || 150) * dpr));
    d41SpDraw(cv);
    var f = d41SpFind(d41SpCur());
    if (diary) { diary.spx = f[0]; diary.spy = f[1]; }
    d41SpRing(f[0], f[1]);
    d41SpDown = false;
    cv.addEventListener("pointerdown", function (ev) {
      d41SpDown = true;
      try { cv.setPointerCapture(ev.pointerId); } catch (e) {}
      if (ev.cancelable) ev.preventDefault();
      ev.stopPropagation();
      d41SpAt(ev, cv);
    });
    cv.addEventListener("pointermove", function (ev) {
      if (!d41SpDown) return;
      if (ev.cancelable) ev.preventDefault();
      d41SpAt(ev, cv);
    });
    var end = function (ev) {
      if (!d41SpDown) return;
      d41SpDown = false;
      if (ev && ev.cancelable) ev.preventDefault();
      if (diary && diary.sp === "text") d41RenderNodes();
      d41Sync();
      d41HistPush();
      d41AutoSave();
    };
    cv.addEventListener("pointerup", end);
    cv.addEventListener("pointercancel", end);
  }
  /* 판만 닫기 (다른 일은 부르는 쪽에서) */
  function d41SpShut() {
    if (diary) diary.sp = null;
    d41SpDown = false;
    var el = document.getElementById("d41Sp");
    if (el) { el.hidden = true; el.innerHTML = ""; }
  }
  function d41SpOpen(kind) {
    if (!diary) return;
    var k = kind === "pen" ? "pen" : "text";
    if (diary.sp === k) { d41SpClose(); return; }
    d41CommitTexts();
    d41BlurAll();
    diary.sp = k;
    var el = document.getElementById("d41Sp");
    if (!el) return;
    el.hidden = false;
    el.innerHTML = d41SpectrumHtml();
    d41PanelRefresh();          /* 색 동그라미에 «켜짐» 표시 */
    d41SpWire();
  }
  function d41SpClose() {
    if (!diary || !diary.sp) return;
    var was = diary.sp;
    d41SpShut();
    if (was === "text") d41RenderNodes();
    d41PanelRefresh();
    d41Sync();
    d41HistPush();
    d41AutoSave();
  }

  function formDiary(cid, it) {
    var l = containerOf(cid);
    if (!l) return "";
    var st = diaryStyOf(it);
    diary = {
      cid: cid, id: it ? it.id : null,
      date: String((it && it.date) || today).slice(0, 10) || today,
      texts: diaryTextsOf(it), imgs: diaryImgsOf(it), pen: diaryPenOf(it),
      mode: "text", sel: null,
      /* v44: 새 다이어리는 바로 고치기, 이미 쓴 다이어리는 보기(스크롤)부터 */
      editing: !(it && ((itTitle(it) || "").trim() || itBody(it).trim() || (it.imgs || []).length || (it.pen || []).length)),
      tsize: d41Clamp(D41_SIZES[st.size] || 16.5, D41_TXMIN, D41_TXMAX),
      tcolor: st.color || "", talign: st.align || "left",
      pmode: "pen", pcolor: "#111111", pw: 3.5, pcpick: false,
      tbold: false, tstrike: false, tunderline: false, cpick: false,
      sp: null, spx: 0.5, spy: 0.02,      /* v46: 스펙트럼 색상 판 (v47: 위=빨강 · 가운데=순색) */
    };
    var h = '<form class="d41" id="sheetForm" autocomplete="off">';
    /* v44: 되돌리기·다시 실행 — 글·사진·그림 상태를 기록해 두었다가 되돌려요 */
    d41Hist = { stack: [], idx: -1 };
    h += '<div class="d41-top">' +
      '<button type="button" class="d41-back" data-close="1" aria-label="뒤로">' + IC.left + "</button>" +
      '<input class="d41-title" name="text" value="' + (it ? esc(itTitle(it)) : "") +
      '" placeholder="새 다이어리" aria-label="다이어리 제목" autocomplete="off">' +
      '<span class="d41-top-sp" aria-hidden="true"></span></div>';
    /* v44: 아이콘바(펜·글씨·사진)를 아래에서 위로 — 상단 바 바로 아래, 도구 판은 그 아래 */
    h += d41ToolsHtml();
    h += '<div class="d41-panel" id="d41Panel" hidden>' + d41PanelHtml() + "</div>";
    /* v46: 색상 스펙트럼 판 — 색 동그라미를 누르면 여기에 올라와요 */
    h += '<div class="d41-sp" id="d41Sp" hidden></div>';
    /* v42: 모눈은 상단 바 바로 아래부터 — 날짜도 종이 위에 얹혀요 */
    h += '<div class="d41-canvas" id="d41Canvas"><div class="d41-paper' + (diary.editing === false ? " view" : "") + '" id="d41Paper">' +
      '<div class="d41-date"><span class="d41-dbig" id="d41DateBig">' + esc(d41Stamp(diary.date)) + "</span>" +
      '<input type="date" class="d41-datein" name="date" value="' + esc(diary.date) + '" aria-label="날짜"></div>' +
      '<div class="d41-nodes" id="d41Nodes">' + d41NodesHtml() + "</div>" +
      '<svg class="d41-pen" id="d41Pen" aria-hidden="true"></svg>' +
      "</div></div>";
    h += '<input type="hidden" name="texts" id="d41TextsIn" value="' + esc(JSON.stringify(diary.texts)) + '">' +
      '<input type="hidden" name="imgs" id="d41ImgsIn" value="' + esc(JSON.stringify(diary.imgs)) + '">' +
      '<input type="hidden" name="pen" id="d41PenIn" value="' + esc(JSON.stringify(diary.pen)) + '">' +
      '<input type="file" id="d41ImgIn" accept="image/*" multiple hidden></form>';
    d41HistPush();
    return h;
  }

  function d41PanelOpen(mode, keepSel) {
    if (!diary) return;
    diary.mode = mode;
    /* v43: 도구를 바꿀 때도 빈 글 상자는 남기지 않아요 (방금 만든 상자는 keepSel 로 지켜요) */
    if (!keepSel) d41PruneEmpty("");
    /* 도구를 고르면 사진 선택은 풀려요 — 펜·글씨 칸이 제대로 열리게 (새 글 상자는 그대로) */
    if (!keepSel && diary.sel) {
      diary.sel = null;
      Array.prototype.forEach.call(document.querySelectorAll("#d41Nodes .sel"), function (el) { el.classList.remove("sel"); });
    }
    var p = document.getElementById("d41Panel");
    if (!p) return;
    p.hidden = false;
    p.innerHTML = d41PanelHtml();
    var paper = document.getElementById("d41Paper");
    if (paper) paper.classList.toggle("pen", mode === "pen");
    var penEl = document.getElementById("d41Pen");
    if (penEl) penEl.classList.toggle("on", mode === "pen");
    var tools = document.querySelector(".d41-tools");
    if (tools) tools.outerHTML = d41ToolsHtml();
    if (mode === "pen") d41Paint();
    d41Grow();
  }

  /* ---------------- 손가락으로 끌기 / 크기 조절 ---------------- */
  /* v47: 아이폰에서 글 상자가 뚝뚝 끊기거나 아예 멈추던 문제 —
     · 상자가 손가락을 붙잡아(setPointerCapture) 스크롤·글자 고르기에 뺏기지 않게
     · 4px만 움직여도 곧바로 따라가기 (예전 6px · 그동안은 꿈쩍도 안 했어요)
     · 자리는 화면에서만(transform) 옮기고 화면 주사율에 맞춰 한 번에 그리기(rAF)
     · 저장·동기화는 손을 뗄 때 딱 한 번 (끄는 동안 화면을 다시 그리지 않아요) */
  function d41Track(ev, onStart, onMove, onEnd, onTap, capEl) {
    var sx = ev.clientX, sy = ev.clientY, moved = false;
    var pid = ev.pointerId, cap = capEl || null;
    /* 끌기 시작한 그 손가락만 따라가요 — 다른 손가락·마우스가 섞이지 않게 */
    function mine(e) { return pid == null || e.pointerId == null || e.pointerId === pid; }
    if (cap && cap.setPointerCapture) {
      try { cap.setPointerCapture(pid); } catch (e) { cap = null; }
    }
    function mv(e) {
      if (!mine(e)) return;
      if (!moved) {
        if (Math.abs(e.clientX - sx) < 4 && Math.abs(e.clientY - sy) < 4) return;
        moved = true;
        onStart && onStart(e);
      }
      if (e.cancelable) e.preventDefault();
      onMove && onMove(e);
    }
    function up(e) {
      if (!mine(e)) return;
      document.removeEventListener("pointermove", mv, true);
      document.removeEventListener("pointerup", up, true);
      document.removeEventListener("pointercancel", up, true);
      window.removeEventListener("pointermove", mv, true);
      window.removeEventListener("pointerup", up, true);
      window.removeEventListener("pointercancel", up, true);
      if (cap && cap.releasePointerCapture) { try { cap.releasePointerCapture(pid); } catch (err) {} }
      if (moved) { try { if (e.cancelable) e.preventDefault(); } catch (err) {} onEnd && onEnd(e); }
      else if (onTap) { try { if (e.cancelable) e.preventDefault(); } catch (err) {} onTap(e); }
    }
    document.addEventListener("pointermove", mv, true);
    document.addEventListener("pointerup", up, true);
    document.addEventListener("pointercancel", up, true);
    window.addEventListener("pointermove", mv, true);
    window.addEventListener("pointerup", up, true);
    window.addEventListener("pointercancel", up, true);
  }
  function d41StartMove(node, kind, id, ev, onTap) {
    var paper = document.getElementById("d41Paper");
    if (!paper) return;
    var W = d41WPx();
    var r = node.getBoundingClientRect();
    var pr = paper.getBoundingClientRect();
    /* 잡은 지점이 상자 안 어디였는지 — 그래야 손가락 아래에서 상자가 튀지 않아요 */
    var offX = ev.clientX - r.left, offY = ev.clientY - r.top;
    var baseL = r.left - pr.left, baseT = r.top - pr.top;   /* 지금 상자의 자리(px) */
    var start = (kind === "img" ? (diary && diary.imgs) || [] : (diary && diary.texts) || [])
      .filter(function (t) { return t.id === id; })[0];
    var nx = start ? start.x : 0.06, ny = start ? start.y : 0;
    var qx = 0, qy = 0;            /* 마지막으로 받은 손가락 자리 */
    var raf = 0;
    function paint() {
      raf = 0;
      if (!diary) return;
      var x = d41Clamp((qx - offX - pr.left) / W, 0, kind === "img" ? 0.96 : 0.9);
      var y = Math.max(0, (qy - offY - pr.top) / W);
      nx = x; ny = y;
      node.style.transform = "translate3d(" + (x * W - baseL).toFixed(1) + "px," +
        (y * W - baseT).toFixed(1) + "px,0)";
    }
    function flush() { if (raf) { cancelAnimationFrame(raf); raf = 0; paint(); } }
    d41Track(ev, function () { node.classList.add("drag"); }, function (e) {
      if (d41Pinch) return;                       /* 두 손가락으로 크기 바꾸는 중 */
      qx = e.clientX; qy = e.clientY;
      if (!raf) raf = requestAnimationFrame(paint);
    }, function () {
      node.classList.remove("drag");
      if (d41Pinch) { if (raf) { cancelAnimationFrame(raf); raf = 0; } node.style.transform = ""; return; }
      flush();                                    /* 마지막 손가락 자리까지 반영 */
      /* 옮긴 자리를 그대로 style 에 넣고 transform 은 지워요 — 다시 그리지 않아 깜빡임이 없어요 */
      node.style.transform = "";
      node.style.left = (nx * 100).toFixed(2) + "%";
      node.style.top = Math.round(ny * W) + "px";
      if (!diary) return;
      var o = (kind === "img" ? diary.imgs : diary.texts).filter(function (t) { return t.id === id; })[0];
      if (o) { o.x = nx; o.y = ny; }
      d41Grow(); d41Sync();
      d41HistPush();
      d41AutoSave();
    }, onTap, node);
  }
  function d41StartResize(id, ev) {
    var node = document.querySelector('#d41Nodes .d41-imgb[data-img="' + id + '"]');
    var im = (diary.imgs || []).filter(function (t) { return t.id === id; })[0];
    if (!node || !im) return;
    ev.preventDefault();
    ev.stopPropagation();
    var W = d41WPx();
    var startW = node.getBoundingClientRect().width;
    var nw = im.w;
    d41Track(ev, function () { node.classList.add("drag"); }, function (e) {
      if (d41Pinch) return;
      var w = d41Clamp((startW + (e.clientX - ev.clientX)) / W, D41_MINW, 1 - im.x);
      nw = w;
      node.style.width = (w * 100).toFixed(2) + "%";
    }, function () {
      node.classList.remove("drag");
      if (d41Pinch) return;
      if (diary) { im.w = nw; }
      d41Grow(); d41Sync();
      d41HistPush();
      d41AutoSave();
    }, null, node);
  }
  /* 빈 종이를 누르면 그 자리에 글 상자 */
  function d41AddTextAt(x, y) {
    if (!diary) return;
    /* v43: 종이를 다시 누를 때, 앞서 만든 빈 상자는 쌓이지 않게 걷어내요 */
    d41CommitTexts();
    d41PruneEmpty("");
    x = d41Clamp(x, 0, 0.72);
    y = Math.max(0, y);
    var t = { id: uid(), x: x, y: y, text: "", size: diary.tsize || 16.5,
      color: diary.tcolor || "", align: diary.talign || "left",
      bold: diary.tbold ? 1 : 0, strike: diary.tstrike ? 1 : 0, underline: diary.tunderline ? 1 : 0 };
    diary.texts.push(t);
    diary.sel = "tx:" + t.id;
    d41TapKey = "tx:" + t.id; d41TapAt = Date.now();
    d41RenderNodes();
    d41PanelOpen("text", true);
    d41Sync();
    d41HistPush();
    /* 한 박자 뒤에 커서를 넣어야 탭의 기본 동작(포커스 풀기)에 지워지지 않아요 */
    var focusIt = function () {
      var ed = document.querySelector('#d41Nodes .d41-tx[data-tx="' + t.id + '"] .d41-txt');
      if (ed) { try { ed.focus(); } catch (e) {} }
    };
    focusIt();
    setTimeout(focusIt, 0);
  }
  function d41BindCanvas() {
    var paper = document.getElementById("d41Paper");
    if (!paper) return;
    d41BindPinch(paper);
    paper.addEventListener("pointerdown", function (ev) {
      if (!diary || diary.mode === "pen") return;
      /* v44: 보기(스크롤) 모드 — 스크롤은 그대로 흘러가고, 톡 누르면 고치기로 바뉼니다 */
      if (!diary.editing) {
        var vStartX = ev.clientX, vStartY = ev.clientY, vMoved = false;
        var vMv = function (e) {
          if (Math.abs(e.clientX - vStartX) > 10 || Math.abs(e.clientY - vStartY) > 10) vMoved = true;
        };
        var vUp = function () {
          document.removeEventListener("pointermove", vMv, true);
          document.removeEventListener("pointerup", vUp, true);
          document.removeEventListener("pointercancel", vUp, true);
          if (!vMoved && diary && document.getElementById("d41Paper")) d41SetEditing(true);
        };
        document.addEventListener("pointermove", vMv, true);
        document.addEventListener("pointerup", vUp, true);
        document.addEventListener("pointercancel", vUp, true);
        return;
      }
      var t = ev.target;
      /* v43: 글·사진 상자의 × — 누르는 순간 바로 지워요.
         (아이폰에서 입력창 포커스가 풀리며 click 이 삼켜져도 지워지도록 pointerdown 에서 처리) */
      var xb = t.closest ? t.closest(".d41-txx, .d41-imgx") : null;
      if (xb) {
        ev.preventDefault();
        ev.stopPropagation();
        if (xb.classList.contains("d41-txx")) d41DelText(String(xb.getAttribute("data-tx") || ""));
        else d41DelImg(String(xb.getAttribute("data-img") || ""));
        return;
      }
      var rz = t.closest ? t.closest(".d41-rz") : null;
      if (rz) { d41StartResize(rz.getAttribute("data-rz"), ev); return; }
      var node = t.closest ? t.closest(".d41-tx, .d41-imgb") : null;
      /* v47: 글·사진 상자 위에서는 상자를 먼저 잡아요 — 상자 밑에 그린 획이 끌려가지 않게 */
      var penHit = node ? null : d41HitPen(ev);
      if (penHit) { d41StartPenMove(penHit, ev); return; }
      if (node) {
        var isTx = node.classList.contains("d41-tx");
        var id = isTx ? node.getAttribute("data-tx") : node.getAttribute("data-img");
        var key = isTx ? "tx:" + id : "img:" + id;
        var now = Date.now();
        /* v43: 처음 누르면 «고르기»만 — 키보드를 내리고 아래 T 툴바가 보이게.
           같은 상자를 짧은 사이에 한 번 더 톡 누르면(끌지 않고) 그때 입력(키보드)을 열어요. */
        var dblTap = isTx && diary.sel === key && d41TapKey === key && (now - d41TapAt) < 520;
        /* v47: 이미 고른 상자는 판을 다시 그리지 않아요 — 끌기 시작에서 화면이 흔들리지 않게 */
        if (diary.sel !== key) d41Select(key);
        if (!node.isConnected) return;
        if (isTx) {
          ev.preventDefault();
          d41TapKey = key; d41TapAt = now;
          /* v47: 키보드 내리기는 «톡» 눌렀을 때만 — 끌 때 내리면 화면이 줄어들어 상자가 튀어요 */
          d41StartMove(node, "tx", id, ev,
            dblTap ? function (e) { d41FocusText(id, e.clientX, e.clientY); }
                   : function () { d41BlurAll(); });
        } else {
          d41StartMove(node, "img", id, ev);
        }
        return;
      }
      if (t === paper || (t.id === "d41Nodes")) {
        ev.preventDefault();
        d41BlurAll();
        var r = paper.getBoundingClientRect();
        /* v44: 글을 쓰고 난 뒤(고른 상자가 있는 동안) 배경을 누르면 글쓰기를 마칩니다 —
           빈 상자는 정리하고, 고르기를 풀고, 지금 상태를 자동 저장해요.
           새 글 상자는 T 도구로 만들어요. (예전엔 배경을 누를 때마다 새 상자가 계속 생겨났어요) */
        var wasSel = !!diary.sel;
        d41PruneEmpty("");
        if (diary.sel) {
          diary.sel = null;
          Array.prototype.forEach.call(document.querySelectorAll("#d41Nodes .sel"), function (el) { el.classList.remove("sel"); });
          d41Paint();
        }
        /* v44: 도구 판(굵기·색 등)도 덮어 — 쓴 내용만 보이게 */
        d41PanelHide();
        if (wasSel) d41AutoSave();
        else d41AddTextAt((ev.clientX - r.left) / r.width, (ev.clientY - r.top) / r.width);
      }
    });
    /* 한글 조합 중에는 빈 상자 정리를 미뤄요 */
    paper.addEventListener("compositionstart", function (ev) {
      if (ev.target && ev.target.classList && ev.target.classList.contains("d41-txt")) d41Ime = true;
    }, true);
    paper.addEventListener("compositionend", function (ev) {
      if (ev.target && ev.target.classList && ev.target.classList.contains("d41-txt")) d41Ime = false;
    }, true);
  }

  /* ---------------- v43: 두 손가락으로 사진 크기 (핀치) ----------------
     선택한 사진 위에서 두 손가락을 벌리면 커지고, 오므리면 작아져요.
     손가락 사이의 가운데 점이 제자리에 있도록 자리(x·y)도 함께 맞춥니다. */
  function d41PinchPts(id) {
    var out = [];
    Object.keys(d41Pointers).forEach(function (k) {
      var p = d41Pointers[k];
      if (!p) return;
      if (!id || p.id === id) out.push(p);
    });
    return out;
  }
  function d41PinchEl(id) { return document.querySelector('#d41Nodes .d41-imgb[data-img="' + id + '"]'); }
  function d41PinchStart(id) {
    if (!diary || !id) return;
    var im = (diary.imgs || []).filter(function (x) { return x.id === id; })[0];
    var el = d41PinchEl(id);
    var ps = d41PinchPts(id);
    if (!im || !el || ps.length < 2) return;
    var d0 = Math.sqrt(Math.pow(ps[0].x - ps[1].x, 2) + Math.pow(ps[0].y - ps[1].y, 2));
    if (d0 < 12) return;                       /* 아주 살짝 벌린 것은 그냥 누른 것으로 */
    var paper = document.getElementById("d41Paper");
    if (!paper) return;
    var pr = paper.getBoundingClientRect();
    var W = Math.max(1, pr.width);
    d41Pinch = { id: id, im: im, d0: d0, w0: im.w, x0: im.x, y0: im.y,
      mx: ((ps[0].x + ps[1].x) / 2 - pr.left) / W, my: ((ps[0].y + ps[1].y) / 2 - pr.top) / W };
    el.classList.add("drag");
    d41Select("img:" + id);
  }
  function d41PinchMove(e) {
    var st = d41Pinch;
    if (!st || !diary) return;
    var ps = d41PinchPts(st.id);
    if (ps.length < 2) return;
    if (e && e.cancelable) e.preventDefault();
    var d = Math.sqrt(Math.pow(ps[0].x - ps[1].x, 2) + Math.pow(ps[0].y - ps[1].y, 2));
    if (!d || !st.d0) return;
    var w = d41Clamp(st.w0 * (d / st.d0), D41_MINW, 1);
    var k = w / (st.w0 || 0.0001);
    var x = d41Clamp(st.mx - (st.mx - st.x0) * k, 0, 1 - w);
    var y = Math.max(0, st.my - (st.my - st.y0) * k);
    st.im.w = w; st.im.x = x; st.im.y = y;
    var el = d41PinchEl(st.id);
    if (el) {
      el.style.left = (x * 100).toFixed(2) + "%";
      el.style.top = Math.round(y * d41WPx()) + "px";
      el.style.width = (w * 100).toFixed(2) + "%";
    }
    d41Grow();
    d41Sync();
  }
  function d41PinchEnd() {
    var st = d41Pinch;
    d41Pinch = null;
    d41Pointers = {};
    if (!st) return;
    var el = d41PinchEl(st.id);
    if (el) el.classList.remove("drag");
    d41Grow();
    d41Sync();
    d41HistPush();
    d41AutoSave();
  }
  function d41BindPinch(paper) {
    paper.addEventListener("pointerdown", function (ev) {
      if (!diary || diary.mode === "pen") { return; }
      var t = ev.target;
      var node = t.closest ? t.closest(".d41-imgb") : null;
      var id = node ? String(node.getAttribute("data-img") || "") : "";
      d41Pointers[ev.pointerId] = { x: ev.clientX, y: ev.clientY, id: id };
      if (d41Pinch) {
        if (!id && d41PinchPts(d41Pinch.id).length >= 2) d41PinchMove(ev);
        return;
      }
      if (id && d41PinchPts(id).length >= 2) { d41PinchStart(id); return; }
      /* 사진 밖에 두 번째 손가락이 닿아도, 먼저 닿은 손가락이 사진 위였으면 그 사진을 */
      var first = "";
      Object.keys(d41Pointers).forEach(function (k) {
        if (!first && d41Pointers[k].id && d41Pointers[k].id !== id) first = d41Pointers[k].id;
      });
      if (first && Object.keys(d41Pointers).length >= 2) d41PinchStart(first);
    }, true);
    paper.addEventListener("pointermove", function (ev) {
      var p = d41Pointers[ev.pointerId];
      if (p) { p.x = ev.clientX; p.y = ev.clientY; }
      if (d41Pinch) d41PinchMove(ev);
    }, true);
    function up(ev) {
      delete d41Pointers[ev.pointerId];
      if (d41Pinch && d41PinchPts(d41Pinch.id).length < 2) d41PinchEnd();
    }
    paper.addEventListener("pointerup", up, true);
    paper.addEventListener("pointercancel", up, true);
  }

  /* ---------------- 사진 자르기 (v43) ----------------
     「자르기」를 누르면 원본 사진 전체를 크게 보여 주고, 그 위에 자르기 테두리가 떠요.
       · 테두리 안쪽을 끌면 옮기고, 모서리·변 손잡이를 끌면 크기가 바뀌어요
       · 「전체」로 되돌리고 「취소」면 원본 그대로 (누르자마자 잘리지 않아요)
       · 「적용」을 눌렀을 때만 canvas.toDataURL 로 실제로 잘라 다이어리에 반영합니다
     ---------------------------------------------------- */
  var D41_CROP_MIN = 0.08;
  var D41_CROP_HANDLES = ["nw", "n", "ne", "e", "se", "s", "sw", "w"];
  function d41CropPaint() {
    var st = d41CropState;
    if (!st) return;
    var f = document.getElementById("d41CropFrame");
    if (!f) return;
    var r = st.rect;
    f.style.left = (r.x * 100).toFixed(2) + "%";
    f.style.top = (r.y * 100).toFixed(2) + "%";
    f.style.width = (r.w * 100).toFixed(2) + "%";
    f.style.height = (r.h * 100).toFixed(2) + "%";
    var o = document.getElementById("d41CropSize");
    if (o && st.nw && st.nh) {
      o.textContent = Math.max(1, Math.round(st.nw * r.w)) + " × " + Math.max(1, Math.round(st.nh * r.h));
    }
  }
  /* 사진이 화면 안에 다 들어오는 크기로 크게 — 세로로 긴 사진도 잘리지 않게 */
  function d41CropFit() {
    var img = document.getElementById("d41CropImg");
    var stage = document.getElementById("d41CropStage");
    var st = d41CropState;
    if (!img || !stage || !st) return;
    var nw = img.naturalWidth || 0, nh = img.naturalHeight || 0;
    if (!nw || !nh) return;
    st.nw = nw; st.nh = nh;
    var ar = nw / nh;
    var maxW = Math.max(160, Math.min(window.innerWidth - 52, 420));
    var maxH = Math.max(150, Math.min(window.innerHeight * 0.5, 540));
    var w = maxW, h = maxW / ar;
    if (h > maxH) { h = maxH; w = maxH * ar; }
    stage.style.width = Math.max(80, Math.round(w)) + "px";
    stage.style.height = Math.max(60, Math.round(h)) + "px";
    d41CropPaint();
  }
  function d41OpenCrop(id) {
    if (!diary) return;
    var im = (diary.imgs || []).filter(function (x) { return x.id === id; })[0];
    if (!im) { toast("자를 사진을 먼저 골라 주세요"); return; }
    var form = document.querySelector("#sheet form.d41") || document.getElementById("sheet");
    if (!form) return;
    var old = document.getElementById("d41CropWrap");
    if (old) old.remove();
    var hs = "";
    D41_CROP_HANDLES.forEach(function (h) {
      hs += '<span class="d41-ch d41-ch-' + h + '" data-h="' + h + '"></span>';
    });
    var wrap = document.createElement("div");
    wrap.className = "d41-cropwrap";
    wrap.id = "d41CropWrap";
    wrap.innerHTML = '<div class="d41-cropcard">' +
      '<div class="d41-crophd"><b>사진 자르기</b>' +
      '<button type="button" class="d41-cropx" data-crop="cancel" aria-label="닫기">' + IC.x + "</button></div>" +
      '<div class="d41-cropstage" id="d41CropStage">' +
        '<img id="d41CropImg" src="' + esc(im.src) + '" alt="자를 사진" draggable="false">' +
        '<div class="d41-cropframe" id="d41CropFrame">' + hs + "</div>" +
      "</div>" +
      '<div class="d41-crophint"><b id="d41CropSize"></b><span>테두리를 끌어 옮기고, 모서리를 끌어 크기를 바꿔요.</span></div>' +
      '<div class="d41-cropacts">' +
        '<button type="button" class="d41-cb ghost" data-crop="reset">전체</button>' +
        '<button type="button" class="d41-cb ghost" data-crop="cancel">취소</button>' +
        '<button type="button" class="d41-cb" data-crop="apply">적용</button></div></div>';
    form.appendChild(wrap);
    d41CropState = { id: id, im: im, rect: { x: 0, y: 0, w: 1, h: 1 }, nw: 0, nh: 0 };
    var imgEl = document.getElementById("d41CropImg");
    if (imgEl) {
      if (imgEl.complete && imgEl.naturalWidth) d41CropFit();
      else imgEl.addEventListener("load", d41CropFit);
    }
    d41CropPaint();

    var stage = document.getElementById("d41CropStage");
    stage.addEventListener("pointerdown", function (ev) {
      var st = d41CropState;
      if (!st) return;
      if (ev.target.closest && ev.target.closest("[data-crop]")) return;
      ev.preventDefault();
      ev.stopPropagation();
      var r = stage.getBoundingClientRect();
      if (!r.width || !r.height) return;
      var s0 = { x: st.rect.x, y: st.rect.y, w: st.rect.w, h: st.rect.h };
      var hEl = ev.target.closest ? ev.target.closest(".d41-ch") : null;
      var handle = hEl ? String(hEl.getAttribute("data-h") || "") : "";
      var inFrame = !!(ev.target.closest && ev.target.closest("#d41CropFrame"));
      var sx = d41Clamp((ev.clientX - r.left) / r.width, 0, 1);
      var sy = d41Clamp((ev.clientY - r.top) / r.height, 0, 1);
      var mode = handle ? "resize" : (inFrame ? "move" : "draw");
      function mv(e) {
        var ax = d41Clamp((e.clientX - r.left) / r.width, 0, 1);
        var ay = d41Clamp((e.clientY - r.top) / r.height, 0, 1);
        var dx = ax - sx, dy = ay - sy;
        var x1 = s0.x, y1 = s0.y, x2 = s0.x + s0.w, y2 = s0.y + s0.h;
        if (mode === "resize") {
          if (handle.indexOf("w") >= 0) x1 = d41Clamp(s0.x + dx, 0, x2 - D41_CROP_MIN);
          if (handle.indexOf("e") >= 0) x2 = d41Clamp(s0.x + s0.w + dx, x1 + D41_CROP_MIN, 1);
          if (handle.indexOf("n") >= 0) y1 = d41Clamp(s0.y + dy, 0, y2 - D41_CROP_MIN);
          if (handle.indexOf("s") >= 0) y2 = d41Clamp(s0.y + s0.h + dy, y1 + D41_CROP_MIN, 1);
        } else if (mode === "move") {
          x1 = d41Clamp(s0.x + dx, 0, 1 - s0.w);
          y1 = d41Clamp(s0.y + dy, 0, 1 - s0.h);
          x2 = x1 + s0.w; y2 = y1 + s0.h;
        } else {
          /* 빈 곳을 끌면 그만큼 새로 그려요 — 그냥 톡 누르면 테두리가 그대로 (작은 조각이 생기지 않아요) */
          x1 = Math.min(sx, ax); y1 = Math.min(sy, ay);
          x2 = Math.max(sx, ax); y2 = Math.max(sy, ay);
          if (x2 - x1 < D41_CROP_MIN) x2 = Math.min(1, x1 + D41_CROP_MIN);
          if (y2 - y1 < D41_CROP_MIN) y2 = Math.min(1, y1 + D41_CROP_MIN);
        }
        d41CropState.rect = { x: Math.min(x1, x2), y: Math.min(y1, y2),
          w: Math.abs(x2 - x1), h: Math.abs(y2 - y1) };
        d41CropPaint();
      }
      function up() {
        document.removeEventListener("pointermove", mv, true);
        document.removeEventListener("pointerup", up, true);
        document.removeEventListener("pointercancel", up, true);
      }
      document.addEventListener("pointermove", mv, true);
      document.addEventListener("pointerup", up, true);
      document.addEventListener("pointercancel", up, true);
    });

    wrap.addEventListener("click", function (ev) {
      var b = ev.target.closest ? ev.target.closest("[data-crop]") : null;
      if (!b || !d41CropState) return;
      var what = b.getAttribute("data-crop");
      if (what === "cancel") { d41CloseCrop(); return; }
      if (what === "reset") { d41CropState.rect = { x: 0, y: 0, w: 1, h: 1 }; d41CropPaint(); return; }
      if (what === "apply") { d41ApplyCrop(); return; }
    });
  }
  function d41CloseCrop() {
    var w = document.getElementById("d41CropWrap");
    if (w) w.remove();
    d41CropState = null;
  }
  function d41ApplyCrop() {
    var st = d41CropState;
    if (!st) return;
    var imgEl = document.getElementById("d41CropImg");
    if ((!st.nw || !st.nh) && imgEl) { st.nw = imgEl.naturalWidth || 0; st.nh = imgEl.naturalHeight || 0; }
    if (!st.nw || !st.nh || !imgEl) { toast("사진을 아직 불러오지 못했어요"); return; }
    var r = st.rect || { x: 0, y: 0, w: 1, h: 1 };
    var x = d41Clamp(r.x, 0, 0.98), y = d41Clamp(r.y, 0, 0.98);
    var w = d41Clamp(r.w, 0.02, 1 - x), h = d41Clamp(r.h, 0.02, 1 - y);
    /* 테두리를 그대로 두었으면(= 자를 부분을 안 정했으면) 사진을 건드리지 않아요 */
    if (x < 0.004 && y < 0.004 && w > 0.992 && h > 0.992) {
      d41CloseCrop();
      toast("자를 부분을 먼저 정해 주세요");
      return;
    }
    var nw = st.nw, nh = st.nh;
    var sx = Math.round(nw * x), sy = Math.round(nh * y);
    var sw = Math.max(8, Math.min(Math.round(nw * w), nw - sx));
    var sh = Math.max(8, Math.min(Math.round(nh * h), nh - sy));
    var scale = Math.min(1, 1200 / Math.max(sw, sh));
    var cv = document.createElement("canvas");
    cv.width = Math.max(8, Math.round(sw * scale));
    cv.height = Math.max(8, Math.round(sh * scale));
    try {
      var cx = cv.getContext("2d");
      cx.drawImage(imgEl, sx, sy, sw, sh, 0, 0, cv.width, cv.height);
      st.im.src = cv.toDataURL("image/jpeg", 0.9);
    } catch (e) { toast("사진을 자르지 못했어요"); return; }
    var keep = "img:" + st.id;
    d41CloseCrop();
    if (!diary) return;
    diary.sel = keep;
    d41RenderNodes();
    d41Select(keep);
    d41HistPush();
    d41AutoSave();
    toast("사진을 잘랐어요");
  }

  function d41BindPen() {
    var svgEl = document.getElementById("d41Pen");
    var paper = document.getElementById("d41Paper");
    if (!svgEl || !paper) return;
    var cur = null, liveEl = null, lastX = 0, lastY = 0;
    function pt(ev) {
      var r = paper.getBoundingClientRect();
      return { x: ev.clientX - r.left, y: ev.clientY - r.top, W: Math.max(1, r.width) };
    }
    function addPoint(p) {
      if (Math.abs(p.x - lastX) < 1.6 && Math.abs(p.y - lastY) < 1.6) return false;
      lastX = p.x; lastY = p.y;
      cur.p.push(Math.round(p.x / p.W * 1000) / 1000, Math.round(p.y / p.W * 1000) / 1000);
      return true;
    }
    function live() {
      if (!liveEl) return;
      var d = "";
      for (var i = 0; i < cur.p.length; i += 2) {
        d += (i ? "L" : "M") + (cur.p[i] * paper.clientWidth).toFixed(1) + " " + (cur.p[i + 1] * paper.clientWidth).toFixed(1);
      }
      liveEl.setAttribute("d", d);
    }
    svgEl.addEventListener("pointerdown", function (ev) {
      if (!diary || diary.mode !== "pen") return;
      var p = pt(ev);
      ev.preventDefault();
      if (diary.pmode === "erase") {
        var hit = -1, W = p.W;
        diary.pen.forEach(function (s, idx) {
          if (hit >= 0) return;
          for (var i = 0; i < s.p.length; i += 2) {
            var dx = s.p[i] * W - p.x, dy = s.p[i + 1] * W - p.y;
            if (dx * dx + dy * dy < 196) { hit = idx; break; }
          }
        });
        if (hit >= 0) { diary.pen.splice(hit, 1); d41Paint(); d41Sync(); d41HistPush(); d41AutoSave(); }
        return;
      }
      cur = { id: uid(), c: diary.pcolor || "#111111", w: Number(diary.pw) || 3.5, p: [] };
      /* v44: 형광펜 — 반투명하게 그려요 */
      if (diary.pmode === "hl") cur.hl = 1;
      lastX = p.x; lastY = p.y;
      cur.p.push(Math.round(p.x / p.W * 1000) / 1000, Math.round(p.y / p.W * 1000) / 1000);
      diary.pen.push(cur);
      liveEl = document.createElementNS("http://www.w3.org/2000/svg", "path");
      liveEl.setAttribute("fill", "none");
      liveEl.setAttribute("stroke", cur.c);
      liveEl.setAttribute("stroke-width", String(cur.w));
      liveEl.setAttribute("stroke-linecap", "round");
      liveEl.setAttribute("stroke-linejoin", "round");
      if (cur.hl) liveEl.setAttribute("stroke-opacity", "0.35");
      svgEl.appendChild(liveEl);
      live();
      try { svgEl.setPointerCapture(ev.pointerId); } catch (e) {}
    });
    svgEl.addEventListener("pointermove", function (ev) {
      if (!cur || !diary || diary.mode !== "pen") return;
      ev.preventDefault();
      if (addPoint(pt(ev))) live();
    });
    function end() {
      if (!cur) return;
      cur = null; liveEl = null;
      d41Grow(); d41Sync();
      d41HistPush();
      d41AutoSave();
    }
    svgEl.addEventListener("pointerup", end);
    svgEl.addEventListener("pointercancel", end);
    svgEl.addEventListener("pointerleave", end);
  }
  /* =====================================================================
     v44: 그림(펜 획)도 글·사진처럼 고르고 끌어 옮기기
     ---------------------------------------------------------------------
     그린 획을 글씨 모드에서 누르면 점선 테두리와 × 가 붙고, 끌면 그대로 옮겨져요.
     ===================================================================== */
  function d41SelPen() {
    if (!diary || !diary.sel || diary.sel.indexOf("pen:") !== 0) return null;
    var id = diary.sel.slice(4);
    return (diary.pen || []).filter(function (s) { return s.id === id; })[0] || null;
  }
  function d41DelPen(id) {
    if (!diary || !id) return;
    var before = (diary.pen || []).length;
    diary.pen = (diary.pen || []).filter(function (s) { return s.id !== id; });
    if (diary.pen.length === before) return;
    if (diary.sel === "pen:" + id) diary.sel = null;
    d41Paint();
    d41Sync();
    d41PanelRefresh();
    d41HistPush();
    d41AutoSave();
    toast("그림을 지웠어요");
  }
  function d41HitPen(ev) {
    if (!diary || diary.mode === "pen") return null;
    var paper = document.getElementById("d41Paper");
    if (!paper) return null;
    var r = paper.getBoundingClientRect();
    var x = ev.clientX - r.left, y = ev.clientY - r.top, W = Math.max(1, r.width);
    var hit = null;
    (diary.pen || []).forEach(function (s) {
      if (hit) return;
      for (var i = 0; i < s.p.length; i += 2) {
        var dx = s.p[i] * W - x, dy = s.p[i + 1] * W - y;
        if (dx * dx + dy * dy < 400) { hit = s.id; break; }
      }
    });
    return hit;
  }
  function d41StartPenMove(id, ev) {
    var s = (diary.pen || []).filter(function (x) { return x.id === id; })[0];
    var paper = document.getElementById("d41Paper");
    if (!s || !paper) return;
    ev.preventDefault();
    ev.stopPropagation();
    d41Select("pen:" + id);
    d41Paint();
    d41PanelRefresh();
    var W = Math.max(1, paper.getBoundingClientRect().width);
    var sx = ev.clientX, sy = ev.clientY;
    var base = s.p.slice(), mx = 0, my = 0;
    d41Track(ev, null, function (e) {
      mx = (e.clientX - sx) / W;
      my = (e.clientY - sy) / W;
      s.p = base.map(function (v, i) { return i % 2 ? v + my : v + mx; });
      d41Paint();
    }, function () {
      if (mx || my) { d41Sync(); d41HistPush(); d41AutoSave(); }
    }, null);
  }
  function d41PenSelPanel() {
    var h = '<div class="d41-prow"><span class="d41-pl">그림</span><div class="d41-pbtns">' +
      '<button type="button" class="d41-pb" data-act="d41PenDel">삭제</button></div></div>';
    h += '<div class="d41-phint">그림을 끌어서 자유롭게 옮겨요.</div>';
    return h;
  }

  function openDiary(cid, id) {
    var l = containerOf(cid);
    if (!l) return;
    var it = id ? (l.items || []).filter(function (x) { return x.id === id; })[0] : null;
    sheetCenter = false;
    openSheet(formDiary(cid, it), function (fd) { saveDiary(fd); }, { full: true, cls: "d41sheet" });
    d41BindPen();
    d41BindCanvas();
    d41Grow();
    d41Paint();
    /* v44: 펜만 있는 다이어리도 종이 크기가 잡힌 뒤에 다시 그려요 —
       폭이 0일 때 그리면 선이 안 보여서(그림이 지워진 것처럼 보여요) 한 박자 뒤에 다시 그립니다 */
    requestAnimationFrame(function () { d41Grow(); d41Paint(); });
    window.addEventListener("resize", d41ResizeOnce);
  }
  function d41ResizeOnce() {
    if (!diary || !document.getElementById("d41Paper")) {
      window.removeEventListener("resize", d41ResizeOnce);
      return;
    }
    d41RenderNodes();
    d41Paint();
  }

  /* v44: 글·사진·그림을 다이어리 항목에 옮겨 담는 공용 함수 (저장 단추와 자동 저장이 함께 씁니다).
     기본 카테고리(메모·버킷·영화·먹방)로 쓴 다이어리는 각 탭이 쓰는 이름 자리(text / title, memo / review)에 넣어요. */
  function d41WriteItem(it, title, date, texts, imgs, pen, base) {
    var body = texts.map(function (t) { return t.text; }).join("\n").trim();
    if (base === "bucket" || base === "log") { it.title = title; if (base === "log") { it.review = body; } else { it.memo = body; } }
    else { it.text = title; it.memo = body; }
    it.date = date;
    if (texts.length) {
      it.texts = texts.map(function (t) {
        return { id: String(t.id || uid()), x: d41Clamp(d41Num(t.x, 0.05), 0, 1),
          y: Math.max(0, d41Num(t.y, 0.2)), text: String(t.text),
          size: d41Clamp(Math.round(d41Num(t.size, 16.5)), D41_TXMIN, D41_TXMAX),
          color: String(t.color || ""),
          bold: t.bold ? 1 : 0, strike: t.strike ? 1 : 0, underline: t.underline ? 1 : 0,
          align: t.align === "center" ? "center" : t.align === "right" ? "right" : "left" };
      });
    } else delete it.texts;
    if (imgs.length) {
      it.imgs = imgs.map(function (x) {
        return { id: String(x.id || uid()), src: String(x.src),
          x: d41Clamp(d41Num(x.x, 0.05), 0, 1), y: Math.max(0, d41Num(x.y, 0.6)),
          w: d41Clamp(d41Num(x.w, 0.74), D41_MINW, 1) };
      });
    } else delete it.imgs;
    delete it.img;                      /* 사진은 imgs 로만 (옛 한 장짜리는 imgs 로 옮겨 담았어요) */
    if (pen.length) it.pen = pen; else delete it.pen;
    /* v41 호환 — 첫 글 상자의 크기·색·정렬을 sty 에도 남겨요 */
    var t0 = texts[0];
    if (t0 && (t0.size <= 15.2 || t0.size >= 18 || t0.color || t0.align === "center")) {
      it.sty = { size: t0.size <= 15.2 ? 1 : (t0.size >= 18 ? 3 : 2),
        color: String(t0.color || ""), align: t0.align === "center" ? "center" : "left" };
    } else delete it.sty;
  }

  /* v44: 편집기를 닫지 않고 지금 상태를 목록에 자동 저장 —
     글쓰기를 마치고(배경을 누르고)·그림을 그리고·옮긴 뒤에 조용히 저장해요 */
  function d41AutoSave() {
    if (!diary) return;
    d41CommitTexts();
    var l = containerOf(diary.cid);
    if (!l) return;
    var titleEl = document.querySelector("#sheet .d41-title");
    var dateEl = document.querySelector("#sheet .d41-datein");
    var title = String((titleEl && titleEl.value) || "").trim();
    var date = String((dateEl && dateEl.value) || diary.date || today).slice(0, 10) || today;
    var texts = (diary.texts || []).filter(function (t) { return String(t.text == null ? "" : t.text).trim(); });
    var imgs = (diary.imgs || []).filter(function (x) { return x && x.src; });
    var pen = diary.pen || [];
    if (!title && !texts.length && !imgs.length && !pen.length) return;  /* 아직 아무것도 없으면 조용히 */
    var it = diary.id ? (l.items || []).filter(function (x) { return x.id === diary.id; })[0] : null;
    if (!it) { it = { id: uid(), done: false }; l.items.push(it); }
    diary.id = it.id;
    d41WriteItem(it, title, date, texts, imgs, pen, l.base);
    save();
    if (typeof renderDiary === "function") { try { renderDiary(); } catch (e) {} }
  }
  /* v44: 제목·날짜를 고치는 동안은 조금 모아서 자동 저장 */
  var d41AutoT = null;
  function d41AutoSaveSoon() {
    if (d41AutoT) clearTimeout(d41AutoT);
    d41AutoT = setTimeout(function () { d41AutoT = null; d41AutoSave(); }, 400);
  }

  function saveDiary(fd) {
    if (!diary) return;
    /* v42: 저장 단추를 누른 순간 화면에 적힌 글을 모두 모델로 옮겨요 —
       입력창에 포커스·조합이 남아 있어도 글이 빠지지 않게 (v41 의 «내용 사라짐» 대비) */
    d41CommitTexts();
    var l = containerOf(diary.cid);
    if (!l) { closeSheet(); return; }
    var title = String(fd.get("text") || "").trim();
    var date = String(fd.get("date") || "").slice(0, 10) || today;
    var texts = (diary.texts || []).filter(function (t) { return String(t.text == null ? "" : t.text).trim(); });
    var body = texts.map(function (t) { return t.text; }).join("\n").trim();
    var imgs = (diary.imgs || []).filter(function (x) { return x && x.src; });
    var pen = diary.pen || [];
    if (!title && !body && !imgs.length && !pen.length) { toast("오늘 있었던 일을 적어 주세요"); return; }
    var it = diary.id ? (l.items || []).filter(function (x) { return x.id === diary.id; })[0] : null;
    if (!it) { it = { id: uid(), done: false }; l.items.push(it); }
    d41WriteItem(it, title, date, texts, imgs, pen, l.base);
    var savedId = it.id;
    save();
    closeSheet();
    renderDiary();
    /* 목록에서 방금 저장한 다이어리가 보이게 */
    var card = document.querySelector('#s-diary .d41-card[data-id="' + savedId + '"]');
    if (card && card.scrollIntoView) { try { card.scrollIntoView({ block: "center" }); } catch (e) {} }
    toast("저장했어요");
  }

  /* 3) 별점 리뷰 — 별을 눌러 바로 점수를 매기고, 눌러서 장소·날짜·한줄평 */
  function viewListReview(l) {
    var h = '<div class="todo-block" data-list="' + l.id + '">';
    h += quickAddForm(l, "review", "어디서 · 무엇을 (예: 성수 카페)");
    h += '<div class="rv-list" data-list="' + l.id + '">';
    if (!l.items.length) h += '<div class="empty">아직 리뷰가 없어요. 위 칸에 이름을 적고 Add 를 눌러 보세요.</div>';
    l.items.forEach(function (it) {
      var r = Math.max(0, Math.min(5, Math.round(Number(it.rating) || 0)));
      var st = "";
      for (var i = 1; i <= 5; i++) {
        st += '<button type="button" class="rvs' + (i <= r ? " on" : "") + '" data-act="rateReview" data-list="' + l.id +
          '" data-id="' + it.id + '" data-r="' + i + '" aria-label="별점 ' + i + '점">' + STAR + "</button>";
      }
      var meta = [];
      if (it.place) meta.push(esc(it.place));
      if (it.date) meta.push(esc(itemDateTxt(it.date)));
      h += '<div class="rv-card" data-list="' + l.id + '" data-id="' + it.id + '">' +
        '<div class="rv-hd"><div class="rv-t" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '" role="button" tabindex="0">' + esc(itTitle(it)) + "</div>" +
        '<button type="button" class="x" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="삭제">' + IC.x + "</button></div>" +
        '<div class="rv-stars" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="별점 ' + r + '점">' + st + "</div>" +
        (meta.length ? '<div class="rv-meta" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '">' + meta.join(" · ") + "</div>" : "") +
        (itBody(it) ? '<div class="rv-note" data-act="editListItem" data-list="' + l.id + '" data-id="' + it.id + '">' + esc(itBody(it)) + "</div>" : "") +
        "</div>";
    });
    h += "</div></div>";
    h += '<div style="height:6px"></div>';
    h += addRow("addListItem", ' data-list="' + l.id + '"', "리뷰 자세히 쓰기");
    return h;
  }

  /* ==========================================================================
     v45 — 지출·정산: 함께 쓰는 돈(공동 자금) 가계부
     --------------------------------------------------------------------------
     · 맨 위 카드 — 고른 달의 «함께 쓰는 돈»(총 입금) · 사용 금액 · 잔액 · 사용률 막대
       그 아래 소영·준영이 각자 넣은 돈 두 칸 (함께 넣은 돈은 한 줄로)
     · 내역 | 달력 — 내역은 날짜 최신순, 달력은 칸마다 그날 입금/지출 합계,
       날짜를 누르면 달력 아래에 그날 내역이 보여요
     · + 입금하기 / - 지출하기 — 시트에서 지출|입금 · 누가 · 금액 · 카테고리(12) · 날짜 · 메모
     · 항목은 { txType: "expense"|"deposit", cat, who, amount, date, memo } 로 담고,
       예전 항목(amount 만 있고 txType 없음)은 «지출» 로 읽어요.
     · 달 예산은 고른 달에만 — 내 카테고리는 그 리스트(budgets), 기본 카테고리는
       S.noteBudgets(탭 이름)에 담아 sync.js 가 note_meta·list 행에 함께 실어요.
     ========================================================================== */
  var EXP_CATS = ["식비", "카페", "생활용품", "데이트", "교통", "주거",
                  "쇼핑", "여행", "건강", "통신", "공과금", "기타"];
  /* 동그란 라인 아이콘 — 24×24, stroke 만 (색은 currentColor) */
  var EXP_IC = {
    "식비": '<path d="M8 3.6v6.1"/><path d="M5.9 3.6v3.1a2.1 2.1 0 0 0 4.2 0V3.6"/><path d="M8 9.7v10.7"/><path d="M16.6 20.4V3.6c-1.9.9-3.1 2.8-3.1 5.3 0 1.9 1 3.1 3.1 3.4"/>',
    "카페": '<path d="M5 7.4h11v6.6a4 4 0 0 1-4 4H9a4 4 0 0 1-4-4z"/><path d="M16 8.8h1.5a2.4 2.4 0 0 1 0 4.8H16"/><path d="M4.4 20.6h12.2"/>',
    "생활용품": '<path d="M9.6 3.6h4.8v2.2H9.6z"/><path d="M10.2 5.8v1.5l-1.4 1.5a2 2 0 0 0-.5 1.3v9.4a1.5 1.5 0 0 0 1.5 1.5h4.4a1.5 1.5 0 0 0 1.5-1.5v-9.4a2 2 0 0 0-.5-1.3l-1.4-1.5V5.8"/><path d="M8.3 12.6h7.4"/>',
    "데이트": '<path d="M12 20.3c-1.6-1-7.4-4.7-7.4-9.3A4.3 4.3 0 0 1 12 7.8a4.3 4.3 0 0 1 7.4 3.2c0 4.6-5.8 8.3-7.4 9.3z"/>',
    "교통": '<rect x="4.6" y="3.6" width="14.8" height="14"/><path d="M4.6 11h14.8"/><path d="M7 17.6v2.9M17 17.6v2.9"/><path d="M7.9 14.1h.1M16 14.1h.1"/>',
    "주거": '<path d="M4 10.6 12 4l8 6.6V19a1.4 1.4 0 0 1-1.4 1.4h-3.7v-5.6H9.1v5.6H5.4A1.4 1.4 0 0 1 4 19z"/>',
    "쇼핑": '<path d="M5.2 8.5h13.6l-1.1 10.4a2 2 0 0 1-2 1.6H8.3a2 2 0 0 1-2-1.6z"/><path d="M8.9 8.5V7a3.1 3.1 0 0 1 6.2 0v1.5"/>',
    "여행": '<rect x="3.6" y="7.2" width="16.8" height="11.6"/><path d="M9 7.2V5.3a1.2 1.2 0 0 1 1.2-1.2h3.6A1.2 1.2 0 0 1 15 5.3v1.9"/><path d="M3.6 12.4h16.8"/>',
    "건강": '<path d="M3.5 12.6h4.1l2.2-5.5 4 10.6 2-5.1h4.7"/>',
    "통신": '<path d="M4 9.1a12 12 0 0 1 16 0"/><path d="M7 12.3a7.6 7.6 0 0 1 10 0"/><path d="M9.8 15.4a3.6 3.6 0 0 1 4.4 0"/><path d="M11.9 18.5h.2"/>',
    "공과금": '<path d="M13.3 3.4 6 13.3h5l-1.2 7.3 7.3-9.9h-5.1z"/>',
    "기타": '<path d="M6 12h.1M12 12h.1M18 12h.1"/>'
  };
  var EXP_IC_IN = '<rect x="3.6" y="6.2" width="16.8" height="11.6"/><circle cx="12" cy="12" r="2.6"/><path d="M6.8 9.2v.1M17.2 14.7v.1"/>';
  function expIconSvg(cat, tx) {
    if (tx === "deposit") return svg(EXP_IC_IN, 19);
    return svg(EXP_IC[cat] || EXP_IC["기타"], 19);
  }
  /* 화면 상태(이 기기에서만) — 카테고리별로 고른 달·보기·날짜 */
  var EXP_MONTH = {}, EXP_VIEW = {}, EXP_DAY = {};
  function expMon(cid) { return EXP_MONTH[cid] || today.slice(0, 7); }
  function expViewOf(cid) { return EXP_VIEW[cid] === "cal" ? "cal" : "list"; }
  function expMonthTxt(ym) { return Number(String(ym).slice(5, 7)) + "월"; }
  function expWon(n) { return "₩" + won(Math.abs(Math.round(Number(n) || 0))); }
  /* 달력 칸용 짧은 금액 — 4.5만 / 67.8만 / 8,900 */
  function expShort(n) {
    var v = Math.abs(Math.round(Number(n) || 0));
    if (v >= 10000) {
      var m = Math.round(v / 1000) / 10;
      return (m % 1 === 0 ? String(m) : m.toFixed(1)) + "만";
    }
    return won(v);
  }
  function expDateTxt(d) { return String(d || "").slice(5, 10).replace("-", "."); }
  function expDateOf(it) {
    var d = String((it && it.date) || "").slice(0, 10);
    return /^\d{4}-\d{2}-\d{2}$/.test(d) ? d : today;
  }
  function expTxOf(it) { return it && it.txType === "deposit" ? "deposit" : "expense"; }
  function expWhoOf(it) {
    var w = it && it.who;
    if (w === "me" || w === "you" || w === "both") return w;
    var me = String((S.couple || {}).me || ""), you = String((S.couple || {}).you || "");
    if (w === "나" || (me && w === me)) return "me";
    if (you && w === you) return "you";
    return "both";
  }
  function expWhoName(it) {
    var w = expWhoOf(it);
    return w === "me" ? String(S.couple.me) : w === "you" ? String(S.couple.you) : "함께";
  }
  function expCatOf(it) {
    if (expTxOf(it) === "deposit") return "입금";
    var c = String((it && it.cat) || "").trim();
    return c || itTitle(it) || "기타";
  }
  /* 예산 — 내 카테고리는 그 리스트의 budgets, 기본 카테고리는 S.noteBudgets[탭] */
  function expBudgetMap(c, create) {
    if (!c) return {};
    if (isBaseContainer(c)) {
      if (create) {
        if (!S.noteBudgets || typeof S.noteBudgets !== "object") S.noteBudgets = {};
        if (!S.noteBudgets[c.base] || typeof S.noteBudgets[c.base] !== "object") S.noteBudgets[c.base] = {};
      }
      return ((S.noteBudgets || {})[c.base]) || {};
    }
    if (create) {
      if (!c.budgets || typeof c.budgets !== "object") c.budgets = {};
      return c.budgets;
    }
    return (c.budgets && typeof c.budgets === "object") ? c.budgets : {};
  }
  function expBudgetOf(c, ym) { return Math.max(0, Math.round(Number(expBudgetMap(c)[ym]) || 0)); }
  function expSetBudget(cid, ym, n) {
    var c = containerOf(cid);
    if (!c) return false;
    var map = expBudgetMap(c, true);
    if (n > 0) map[ym] = Math.round(n); else delete map[ym];
    return true;
  }
  /* 한 달치 — 입금·지출 합계와 사람별 입금 */
  function expMonthList(c, ym) {
    return (c.items || []).filter(function (it) { return expDateOf(it).slice(0, 7) === ym; });
  }
  function expStats(c, ym) {
    var out = { items: [], dep: 0, spent: 0, me: 0, you: 0, both: 0 };
    expMonthList(c, ym).forEach(function (it) {
      out.items.push(it);
      var amt = Math.abs(Math.round(Number(it.amount) || 0));
      if (!amt) return;
      if (expTxOf(it) === "deposit") {
        out.dep += amt;
        var w = expWhoOf(it);
        if (w === "me") out.me += amt;
        else if (w === "you") out.you += amt;
        else out.both += amt;
      } else out.spent += amt;
    });
    out.items.sort(function (a, b) {
      var da = expDateOf(a), db = expDateOf(b);
      if (da === db) return 0;
      return da < db ? 1 : -1;
    });
    return out;
  }
  function expRowTitle(it) {
    return expTxOf(it) === "deposit" ? expWhoName(it) + " 입금" : expCatOf(it);
  }
  function expRowHtml(c, it) {
    var tx = expTxOf(it), amt = Math.abs(Math.round(Number(it.amount) || 0));
    var sub = [];
    var memo = String(it.memo || "").trim();
    if (memo) sub.push(memo);
    sub.push(expDateTxt(expDateOf(it)));
    if (tx !== "deposit") sub.push(expWhoName(it));
    return '<div class="exp-row" data-list="' + c.id + '" data-id="' + it.id + '">' +
      '<span class="exp-ic' + (tx === "deposit" ? " in" : "") + '">' + expIconSvg(expCatOf(it), tx) + "</span>" +
      '<button type="button" class="exp-row-b" data-act="editListItem" data-list="' + c.id + '" data-id="' + it.id + '">' +
        '<span class="exp-row-t">' + esc(expRowTitle(it)) + "</span>" +
        '<span class="exp-row-s">' + esc(sub.join(" · ")) + "</span>" +
      "</button>" +
      '<span class="exp-row-a ' + (tx === "deposit" ? "in" : "out") + '">' + (tx === "deposit" ? "+" : "-") + expWon(amt) + "</span>" +
      '<button type="button" class="x exp-x" data-act="delListItem" data-list="' + c.id + '" data-id="' + it.id + '" aria-label="삭제">' + IC.x + "</button></div>";
  }
  /* 달력 — 칸마다 그날 +입금 / -지출 합계 (0 이면 안 보여요) */
  function expCalHtml(c, ym, stats, selDay) {
    var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7));
    var first = new Date(y, m - 1, 1).getDay();
    var days = new Date(y, m, 0).getDate();
    var byDay = {};
    stats.items.forEach(function (it) {
      var d = expDateOf(it);
      if (d.slice(0, 7) !== ym) return;
      var k = d.slice(8, 10);
      if (!byDay[k]) byDay[k] = { in: 0, out: 0 };
      var amt = Math.abs(Math.round(Number(it.amount) || 0));
      if (expTxOf(it) === "deposit") byDay[k].in += amt; else byDay[k].out += amt;
    });
    var h = '<div class="exp-cal"><div class="exp-week">';
    ["일", "월", "화", "수", "목", "금", "토"].forEach(function (w) { h += "<span>" + w + "</span>"; });
    h += '</div><div class="exp-grid">';
    for (var i = 0; i < first; i++) h += '<span class="exp-blank"></span>';
    for (var d = 1; d <= days; d++) {
      var ds = ym + "-" + pad(d);
      var t = byDay[pad(d)] || null;
      var cls = "exp-cell" + (ds === today ? " today" : "") + (ds === selDay ? " sel" : "");
      h += '<button type="button" class="' + cls + '" data-act="expDay" data-list="' + c.id + '" data-day="' + ds + '">' +
        '<span class="exp-cell-n">' + d + "</span>" +
        (t && t.in ? '<span class="di">+' + expShort(t.in) + "</span>" : "") +
        (t && t.out ? '<span class="do">-' + expShort(t.out) + "</span>" : "") +
        "</button>";
    }
    h += "</div></div>";
    return h;
  }
  function expSelDay(c, ym, stats) {
    var d = EXP_DAY[c.id];
    if (d && d.slice(0, 7) === ym) return d;
    if (ym === today.slice(0, 7)) return today;
    if (stats.items.length) return expDateOf(stats.items[0]);
    return ym + "-01";
  }
  function expDayHtml(c, day) {
    var rows = expMonthList(c, day.slice(0, 7)).filter(function (it) { return expDateOf(it) === day; })
      .sort(function (a, b) { var da = expDateOf(a), db = expDateOf(b); return da === db ? 0 : (da < db ? 1 : -1); });
    var dep = 0, out = 0;
    rows.forEach(function (it) {
      var amt = Math.abs(Math.round(Number(it.amount) || 0));
      if (expTxOf(it) === "deposit") dep += amt; else out += amt;
    });
    var h = '<div class="exp-daylist"><div class="exp-dayhd">' +
      '<b>' + Number(day.slice(5, 7)) + "월 " + Number(day.slice(8, 10)) + "일</b>" +
      '<span class="wd">(' + WD[parse(day).getDay()] + ')</span>' +
      '<span class="exp-daynet">' +
        (dep ? '<em class="di">+' + expWon(dep) + "</em>" : "") +
        (out ? '<em class="do">-' + expWon(out) + "</em>" : "") + "</span></div>";
    if (!rows.length) h += '<div class="exp-empty">이 날은 내역이 없어요</div>';
    rows.forEach(function (it) { h += expRowHtml(c, it); });
    return h + "</div>";
  }
  /* 4) 지출·정산 화면 */
  function viewListExpense(l) {
    var cid = l.id, ym = expMon(cid), view = expViewOf(cid);
    var st = expStats(l, ym);
    var budget = expBudgetOf(l, ym);
    var base = budget > 0 ? budget : st.dep;
    var pct = base > 0 ? Math.round(st.spent / base * 100) : 0;
    var left = st.dep - st.spent;
    var h = '<div class="exp-page" data-list="' + cid + '">';
    /* 달 넘기기 + 내역 | 달력 */
    h += '<div class="exp-hd"><div class="exp-month">' +
      '<button type="button" class="exp-nav" data-act="expPrev" data-list="' + cid + '" aria-label="이전 달">' + IC.left + "</button>" +
      "<b>" + (ym.slice(0, 4) !== today.slice(0, 4) ? '<span class="yr">' + ym.slice(0, 4) + "년</span>" : "") + expMonthTxt(ym) + "</b>" +
      '<button type="button" class="exp-nav" data-act="expNext" data-list="' + cid + '" aria-label="다음 달">' + IC.right + "</button>" +
      '</div><div class="exp-tabs">' +
      '<button type="button" class="exp-tab' + (view === "list" ? " on" : "") + '" data-act="expView" data-list="' + cid + '" data-v="list">내역</button>' +
      '<button type="button" class="exp-tab' + (view === "cal" ? " on" : "") + '" data-act="expView" data-list="' + cid + '" data-v="cal">달력</button>' +
      "</div></div>";
    /* 함께 쓰는 돈 */
    h += '<div class="exp-fund">' +
      '<div class="exp-fund-k">' + expMonthTxt(ym) + " 함께 쓰는 돈</div>" +
      '<div class="exp-fund-total">' + expWon(st.dep) + "</div>" +
      '<div class="exp-fund-row"><span>사용 금액</span><b class="exp-spent">' + expWon(st.spent) + "</b></div>" +
      '<div class="exp-bar"><i class="' + (pct > 100 ? "over" : "") + '" style="width:' + Math.max(0, Math.min(100, pct)) + '%"></i></div>' +
      '<div class="exp-bar-n"><span class="exp-pct">사용 ' + pct + '%</span>' +
        '<span class="exp-left">' + (left >= 0 ? "잔액 " + expWon(left) : expWon(-left) + " 초과") + "</span></div>" +
      '<div class="exp-budget">' +
        (budget > 0
          ? "<span>예산 " + expWon(budget) + " · " + (budget - st.spent >= 0
              ? "남은 " + expWon(budget - st.spent)
              : expWon(st.spent - budget) + " 초과") + "</span>"
          : "<span></span>") +
        '<button type="button" class="exp-budget-btn" data-act="expBudget" data-list="' + cid + '">' +
          (budget > 0 ? "고치기" : "예산 정하기") + "</button></div>" +
      "</div>";
    /* 소영 · 준영 입금 */
    h += '<div class="exp-people">' +
      '<div class="exp-p"><span class="k">' + esc(S.couple.me) + ' 입금</span><span class="v">' + expWon(st.me) + "</span></div>" +
      '<div class="exp-p"><span class="k">' + esc(S.couple.you) + ' 입금</span><span class="v">' + expWon(st.you) + "</span></div>" +
      "</div>" +
      (st.both > 0 ? '<div class="exp-both">함께 넣은 돈 <b>' + expWon(st.both) + "</b></div>" : "");
    /* 내역 / 달력 */
    if (view === "cal") {
      var sel = expSelDay(l, ym, st);
      h += expCalHtml(l, ym, st, sel) + expDayHtml(l, sel);
    } else {
      h += '<div class="exp-list">';
      if (!st.items.length) h += '<div class="exp-empty">' + expMonthTxt(ym) + "에는 아직 내역이 없어요</div>";
      st.items.forEach(function (it) { h += expRowHtml(l, it); });
      h += "</div>";
    }
    /* 아래 두 버튼 */
    h += '<div class="exp-acts">' +
      '<button type="button" class="exp-act in" data-act="expAdd" data-list="' + cid + '" data-tx="deposit"><span class="s">+</span>입금하기</button>' +
      '<button type="button" class="exp-act out" data-act="expAdd" data-list="' + cid + '" data-tx="expense"><span class="s">-</span>지출하기</button>' +
      "</div></div>";
    return h;
  }

  /* 지출·정산 시트 — 지출|입금 · 누가 · 금액 · 카테고리(12 + 직접 입력) · 날짜 · 메모 */
  function formExpItem(l, it, opts) {
    var isEdit = !!it;
    var tx = isEdit ? expTxOf(it) : ((opts && opts.tx) === "deposit" ? "deposit" : "expense");
    var ym = (opts && opts.ym) || expMon(l.id);
    var dflt = today.slice(0, 7) === ym ? today : ym + "-01";
    var cat = isEdit ? (expTxOf(it) === "deposit" ? "입금" : String(it.cat || "").trim()) : "";
    if (tx === "deposit") cat = "입금";
    var who = isEdit ? expWhoOf(it) : (tx === "deposit" ? "me" : "both");
    var amt = isEdit ? Math.abs(Math.round(Number(it.amount) || 0)) : 0;
    var memo = isEdit ? String(it.memo || "") : "";
    if (isEdit && !it.cat && !memo) memo = itTitle(it);
    var date = isEdit ? expDateOf(it) : dflt;
    var cats = EXP_CATS.slice();
    (l.items || []).forEach(function (x) {
      var c = String(x.cat || "").trim();
      if (c && c !== "입금" && cats.indexOf(c) < 0 && cats.length < 18) cats.push(c);
    });
    if (cat && cat !== "입금" && cats.indexOf(cat) < 0) cats.push(cat);

    var whoBtns = [["me", S.couple.me], ["you", S.couple.you], ["both", "함께"]].map(function (w) {
      return '<button type="button" class="exp-who' + (who === w[0] ? " on" : "") + '" data-act="expWho" data-who="' + w[0] + '">' + esc(w[1]) + "</button>";
    }).join("");
    var catTiles = cats.map(function (c) {
      return '<button type="button" class="exp-cat' + (c === cat ? " on" : "") + '" data-act="expCat" data-cat="' + esc(c) + '">' +
        '<span class="ic">' + expIconSvg(c, "expense") + '</span><span class="nm">' + esc(c) + "</span></button>";
    }).join("") +
      '<button type="button" class="exp-cat exp-cat-more" data-act="expCatNew">' +
      '<span class="ic">' + IC.plus + '</span><span class="nm">직접 입력</span></button>';

    var h = '<div class="sheet-hd exp-shd">' +
      '<button type="button" class="icon-btn" data-close="1" aria-label="닫기">' + IC.left + "</button>" +
      '<div class="exp-seg">' +
        '<button type="button" class="' + (tx === "expense" ? "on" : "") + '" data-act="expTx" data-tx="expense">지출</button>' +
        '<button type="button" class="' + (tx === "deposit" ? "on" : "") + '" data-act="expTx" data-tx="deposit">입금</button>' +
      "</div>" +
      (isEdit
        ? '<button type="button" class="icon-btn exp-delbtn" data-act="delListItem" data-list="' + l.id + '" data-id="' + it.id + '" aria-label="삭제">' + IC.trash + "</button>"
        : '<span class="exp-hdsp"></span>') +
      "</div>";
    h += '<form class="exp-form" id="sheetForm" data-tx="' + tx + '">' +
      '<input type="hidden" name="txType" value="' + tx + '">' +
      '<input type="hidden" name="cat" value="' + esc(cat) + '">' +
      '<input type="hidden" name="who" value="' + who + '">' +
      '<div class="exp-fld exp-amt"><label for="expAmt">금액</label><div class="exp-amt-in">' +
        '<span class="w">₩</span><input id="expAmt" name="amount" inputmode="numeric" autocomplete="off" placeholder="0" value="' +
        (amt ? won(amt) : "") + '"></div></div>' +
      '<div class="exp-fld"><label>누가</label><div class="exp-whos">' + whoBtns + "</div></div>" +
      '<div class="exp-cats"' + (tx === "deposit" ? " hidden" : "") + '><div class="exp-cats-lb">카테고리</div>' +
        '<div class="exp-catgrid" id="expCatGrid">' + catTiles + "</div>" +
        '<div class="exp-catnew" id="expCatNew" hidden>' +
          '<input class="field exp-catin" id="expCatIn" placeholder="카테고리 이름 (예: 반려동물)" maxlength="10" autocomplete="off">' +
          '<button type="button" class="exp-catadd" data-act="expCatAdd">확인</button>' +
        "</div></div>" +
      '<div class="exp-fld"><label for="expDate">날짜</label><input class="exp-datein" id="expDate" type="date" name="date" value="' + date + '"></div>' +
      '<div class="exp-fld"><label for="expMemo">메모</label><input class="exp-memoin" id="expMemo" name="memo" value="' + esc(memo) + '" maxlength="40" autocomplete="off" placeholder="' +
        (tx === "deposit" ? "예: 11월 월급" : "예: 장보기") + '"></div>' +
      '<div style="height:14px"></div><button class="btn-primary" type="submit">' + (isEdit ? "저장하기" : "추가하기") + "</button>" +
      "</form>";
    return h;
  }

  /* 시트에서 읽은 값 — 금액이 0 이면 저장하지 않아요 */
  function expFieldsFrom(fd) {
    var tx = String(fd.get("txType") || "expense") === "deposit" ? "deposit" : "expense";
    var amt = Math.abs(Math.round(parseAmount(fd.get("amount"))));
    if (!amt) { toast("금액을 적어 주세요"); return null; }
    var who = String(fd.get("who") || "");
    if (["me", "you", "both"].indexOf(who) < 0) who = "both";
    var cat = String(fd.get("cat") || "").trim().slice(0, 10);
    return {
      txType: tx,
      amount: amt,
      who: who,
      cat: tx === "deposit" ? "입금" : (cat || "기타"),
      date: String(fd.get("date") || "").slice(0, 10) || today,
      memo: String(fd.get("memo") || "").trim()
    };
  }
  function expApply(it, f, c) {
    Object.keys(f).forEach(function (k) { it[k] = f[k]; });
    /* 카드를 보는 화면·다른 자리에서도 읽히도록 «제목» 자리를 비워 두지 않아요 */
    if (isBaseContainer(c)) {
      if (c.base === "todo") { if (!String(it.text || "").trim()) it.text = it.memo || it.cat; }
      else if (!String(it.title || "").trim()) it.title = it.memo || it.cat;
    } else if (!String(it.text || "").trim()) it.text = it.cat;
  }
  function expAfterSave(c, it) {
    var d = expDateOf(it);
    EXP_MONTH[c.id] = d.slice(0, 7);
    EXP_DAY[c.id] = d;
  }
  function openExpSheet(c, it, tx) {
    if (!c) return;
    var ym = expMon(c.id);
    openSheet(formExpItem(c, it, { tx: tx, ym: ym }), function (fd) {
      var L2 = containerOf(c.id);
      if (!L2) return;
      var f = expFieldsFrom(fd);
      if (!f) return;
      var target = null;
      if (it) target = L2.items.filter(function (x) { return x.id === it.id; })[0] || null;
      if (it && !target) return;
      if (!target) {
        if (isBaseContainer(L2)) target = basePush(L2.base, { text: f.memo || f.cat, memo: f.memo, amount: f.amount, date: f.date });
        else { target = { id: uid(), done: false, date: f.date }; L2.items.push(target); }
      }
      expApply(target, f, L2);
      expAfterSave(L2, target);
      save(); closeSheet(); renderDiary(); toast(it ? "저장했어요" : "추가했어요");
    });
  }
  function expShiftMonth(cid, d) {
    if (!cid) return;
    var ym = expMon(cid);
    var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7)) + d;
    if (m < 1) { m = 12; y--; }
    if (m > 12) { m = 1; y++; }
    EXP_MONTH[cid] = y + "-" + pad(m);
    delete EXP_DAY[cid];
    renderDiary();
  }
  function openExpBudget(c) {
    if (!c) return;
    var ym = expMon(c.id), cur = expBudgetOf(c, ym);
    openSheet(sheetHead(expMonthTxt(ym) + " 예산") +
      '<p class="sheet-sub">이번 달에 쓰기로 한 금액이에요. 비워 두면 함께 쓰는 돈 전체를 기준으로 사용률을 보여줘요.</p>' +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>예산 (원)</label><input class="field exp-budget-in" name="budget" inputmode="numeric" autocomplete="off" value="' +
        (cur ? won(cur) : "") + '" placeholder="예) 1,500,000"></div>' +
      '<div style="height:6px"></div><button class="btn-primary" type="submit">저장하기</button></form>' +
      (cur ? '<div style="height:8px"></div><button class="btn-line" data-act="expBudgetOff" data-list="' + c.id + '">예산 지우기</button>' : ""),
      function (fd) {
        expSetBudget(c.id, ym, Math.abs(Math.round(parseAmount(fd.get("budget")))));
        save(); closeSheet(); renderDiary(); toast("예산을 저장했어요");
      });
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
  /* v43: 사진첩이 빨리 뜨도록 — 썸네일은 비동기 디코딩, 화면 밖 날짜는 lazy,
     맨 아래(가장 최근 날짜) 사진은 eager 로 바로 그려요 */
  function photoImg(p, big, eager) {
    var src = photoSrc(p);
    if (src) {
      var attr = big ? ' decoding="async"'
        : (eager ? ' loading="eager" decoding="async" fetchpriority="high"'
                 : ' loading="lazy" decoding="async"');
      return '<img src="' + esc(src) + '" alt="' + esc(p.title || p.album || "사진") + '"' + attr + ">";
    }
    return art(p.art, big);
  }
  function capHtml(p, cls) {
    if (!p.title && !p.capBg) return "";
    return '<span class="' + cls + '" data-capid="' + p.id + '" style="background:' + capBg(p) + '">' + esc(p.title || "") + "</span>";
  }

  /* 사진첩 v17: 날짜별(최신순) 묶음 · v37: 날짜마다 정사각형 사진 3열 (폴라로이드 틀은 걷어냈습니다) */
  var PHOTOS_PER_DAY = 3;   /* v18: 하루에 보이는 사진은 3장까지 */
  /* v39: 날짜 머리글은 「11월 18일」까지만 — 요일은 뺐어요. 태그는 날짜 옆에 가운데 점으로 이어 붙입니다. */
  function photoDayLabel(day) {
    var d = parse(day);
    if (day === today) return '<span class="d acc">오늘</span>';
    if (day === addDays(today, -1)) return '<span class="d acc">어제</span>';
    return '<span class="d">' + (d.getMonth() + 1) + "월 " + d.getDate() + "일</span>";
  }
  /* v41: 날짜 옆 «기록 이름» — 테두리·바탕 없이 날짜와 같은 크기의 글씨로만 (누르면 바로 고치기) */
  function photoDayTagHtml(day) {
    var tag = dateTagOf(day);
    if (tag) {
      return '<span class="pday-dot" aria-hidden="true">·</span>' +
        '<button type="button" class="pday-tag on" data-act="dateTag" data-date="' + day + '" aria-label="날짜 기록 이름 고치기">' +
        esc(tag) + "</button>";
    }
    return '<button type="button" class="pday-tag empty" data-act="dateTag" data-date="' + day + '" aria-label="날짜 기록 이름 추가">+ 기록 이름</button>';
  }

  /* v23: 사진첩 달력 보기 — 한 달만 보이고 화살표·밀어서 달을 넘깁니다.
     날짜 칸은 그날 대표 사진으로 가득 차고, 왼쪽 위 날짜 · 오른쪽 아래 장수가 붙어요.
     v37: 칸은 정사각형, 달은 위아래로 넘깁니다(위로 밀면 다음 달 · 아래로 밀면 지난 달). */
  function photoMonthYM() {
    var ym = String((S.ui && S.ui.photoMonth) || "");
    return /^\d{4}-\d{2}$/.test(ym) ? ym : today.slice(0, 7);
  }
  function shiftYm(ym, step) {
    var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7)) - 1 + step;
    var d = new Date(y, m, 1);
    return d.getFullYear() + "-" + pad(d.getMonth() + 1);
  }
  /* v38: 사진 달력은 한 달씩 끊지 않고 «세로로 이어진 달력» —
     사진이 있는 가장 오래된 달(최대 12개월 전)부터 다음 달까지 쭉 붙여 그리고,
     열면 이번 달이 화면 가운데쯤 오도록 스크롤해요. 위아래로 자연스럽게 넘겨 보세요. */
  function photoCalMonths() {
    var thisYm = today.slice(0, 7);
    var have = (S.photos || []).map(function (p) { return String(p.date || "").slice(0, 7); })
      .filter(function (ym) { return /^\d{4}-\d{2}$/.test(ym); }).sort();
    /* v39: 이번 달 앞뒤로 12개월씩 — 사진이 그보다 더 예전·나중에 있으면 그 달까지 이어 붙여요 */
    var start = shiftYm(thisYm, -12), end = shiftYm(thisYm, 12);
    if (have.length && have[0] < start) start = have[0];
    if (have.length && have[have.length - 1] > end) end = have[have.length - 1];
    var out = [], ym = start;
    while (ym <= end) { out.push(ym); ym = shiftYm(ym, 1); }
    return out;
  }

  function photoMonthBlock(ym, byDay) {
    var y = Number(ym.slice(0, 4)), m = Number(ym.slice(5, 7));
    var daysIn = new Date(y, m, 0).getDate();
    var startDow = new Date(y, m - 1, 1).getDay();
    var cells = [];
    for (var i = 0; i < startDow; i++) cells.push(0);
    for (var d = 1; d <= daysIn; d++) cells.push(d);
    while (cells.length % 7) cells.push(0);
    var h = '<section class="pcal-m" data-ym="' + ym + '">' +
      '<div class="pcal-ym">' + y + "년 " + m + "월</div>" +
      '<div class="pcal-grid" data-pcal="1" data-rows="' + (cells.length / 7) + '">';
    cells.forEach(function (dayNo) {
      if (!dayNo) { h += '<div class="pcell blank"></div>'; return; }
      var ds = ym + "-" + pad(dayNo);
      var list = (byDay[ds] || []).slice().sort(byDateDesc);
      /* v39: 오늘은 숫자 아래에 점 하나 — 사진이 있어도 지우지 않고 위에 얹어 보여 줍니다 */
      var dot = ds === today ? '<span class="pdot" aria-hidden="true"></span>' : "";
      if (!list.length) {
        h += '<div class="pcell' + (ds === today ? " today" : "") + '"><span class="pn">' + dayNo + "</span>" + dot + "</div>";
        return;
      }
      h += '<button type="button" class="pcell has' + (ds === today ? " today" : "") + '" data-act="pcalDay" data-date="' + ds +
        '" aria-label="' + m + "월 " + dayNo + "일" + (ds === today ? " (오늘)" : "") + " 사진 " + list.length + '장 열기">' +
        photoImg(list[0]) + '<span class="pn">' + dayNo + "</span>" +
        (list.length > 1 ? '<span class="pc">' + list.length + "</span>" : "") + dot + "</button>";
    });
    h += "</div></section>";
    return h;
  }

  function photoCalHtml() {
    var byDay = {};
    S.photos.forEach(function (p) {
      var d = String(p.date || "").slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(d)) return;
      (byDay[d] = byDay[d] || []).push(p);
    });
    var months = photoCalMonths();
    var h = '<div class="pcal pcal-stack">';
    /* v39: 요일 줄은 달력 위에 한 줄로 고정(sticky) — 달을 넘겨도 다시 나오지 않아요 */
    h += '<div class="pcal-week pcal-stick" aria-hidden="true"><span>일</span><span>월</span><span>화</span>' +
      "<span>수</span><span>목</span><span>금</span><span>토</span></div>";
    months.forEach(function (ym) { h += photoMonthBlock(ym, byDay); });
    /* v40: 아래 탭바 위로 답답하지 않게 숨통 — 달력 끝에 여백을 둬요 */
    h += '<div style="height:42px"></div></div>';
    return h;
  }

  /* 사진 달력을 열면 이번 달이 화면 가운데쯤 오도록 — 위로는 지난 달, 아래로는 다음 달이 이어져 보입니다 */
  function photoCalCenter() {
    var el = document.querySelector('#s-photo .pcal-m[data-ym="' + today.slice(0, 7) + '"]');
    var box = document.getElementById("screens");
    if (!el || !box) return;
    var r = el.getBoundingClientRect(), b = box.getBoundingClientRect();
    var mid = (box.scrollHeight - b.height) / 2;
    /* v40: 위에 붙어 있는 머리줄(달력 아이콘 줄) 아래로 이번 달이 오도록 — 그 높이만큼 더 내려요 */
    var hdr = document.querySelector("#s-photo .hdr");
    var hh = hdr ? Math.round(hdr.getBoundingClientRect().height) : 48;
    var top = box.scrollTop + (r.top - b.top) - Math.max(hh + 12, Math.round(b.height * 0.2));
    box.scrollTop = Math.max(0, Math.min(top, Math.max(0, mid + 240)));
  }

  /* v37: 사진 달력 칸은 정사각형(aspect-ratio) — 예전처럼 화면 세로 여유를 재서 높이를 잡지 않습니다.
     폭에 맞춰 칸이 스스로 정사각형이 되므로 따로 계산할 것이 없어요. */

  function isDefaultAlbum(s) { return !String(s || "").trim() || /^\d{1,2}월의 순간$/.test(String(s || "").trim()); }
  /* v38: 날짜의 기록 이름 — 그날 사진들의 album 을 «경주여행» 같은 짧은 이름으로 써요(기본 앨범 이름은 기록 이름으로 보지 않음) */
  function dateTagOf(day) {
    var hit = (S.photos || []).filter(function (p) {
      return String(p.date || "").slice(0, 10) === day && !isDefaultAlbum(p.album);
    })[0];
    return hit ? String(hit.album) : "";
  }
  function setDateTag(day, tag) {
    var t = String(tag || "").trim();
    var album = t || defaultAlbum();
    (S.photos || []).forEach(function (p) {
      if (String(p.date || "").slice(0, 10) === day) p.album = album;
    });
    save();
  }
  function formDateTag(day) {
    var d = parse(day);
    return sheetHead("날짜 기록 이름") +
      '<p class="sheet-sub">' + (d.getMonth() + 1) + "월 " + d.getDate() + "일 사진에 붙는 기록 이름이에요. 예) 경주여행 · 성수 데이트</p>" +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>기록 이름</label><input class="field" name="tag" value="' + esc(dateTagOf(day)) +
      '" placeholder="예) 경주여행" autocomplete="off"></div>' +
      '<button class="btn-primary" type="submit">저장하기</button></form>' +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
  }

  /* v38: 사진 검색 — 날짜 태그·캡션·장소·메모에 검색어가 들어간 날을 모아 보여 줍니다 */
  function photoSearchResults(q) {
    var raw = String(q || "").trim();
    var key = raw.toLowerCase();
    if (!key) return "";
    var days = {};
    (S.photos || []).forEach(function (p) {
      var hay = [p.title, p.place, p.memo, p.album].join(" ").toLowerCase();
      if (hay.indexOf(key) < 0) return;
      var d = String(p.date || "").slice(0, 10);
      (days[d] = days[d] || []).push(p);
    });
    /* v39: 검색 결과도 예전 날짜가 위 · 최근 날짜가 아래 (최근 60일까지만) */
    var list = Object.keys(days).sort().reverse().slice(0, 60).reverse();
    if (!list.length) return '<div class="sres-empty">「' + esc(raw) + "」와 맞는 사진이 없어요.</div>";
    return list.map(function (d) {
      var items = days[d];
      var tag = dateTagOf(d);
      var dd = parse(d);
      var cap = items[0].title || items[0].place || "";
      return '<button type="button" class="sres" data-act="goPhotoDay" data-date="' + d + '">' +
        '<span class="sbar" style="background:var(--ink-3)"></span>' +
        '<span class="sbody"><span class="st">' + (dd.getMonth() + 1) + "월 " + dd.getDate() + "일" +
        (tag ? " · " + esc(tag) : "") + "</span>" +
        '<span class="sd">' + items.length + "장" + (cap ? " · " + esc(cap) : "") + "</span></span>" +
        '<span class="sgo" aria-hidden="true">\u203a</span></button>';
    }).join("");
  }
  function formPhotoSearch(q) {
    var key = String(q || "").trim();
    return sheetHead("사진 검색") +
      '<div class="f" style="margin-top:14px">' +
      '<input class="field" id="photoSearchIn" value="' + esc(key) + '" placeholder="기록 이름·장소로 검색 (예: 경주)" autocomplete="off" enterkeyhint="search" aria-label="사진 검색어">' +
      "</div>" +
      '<div class="sres-wrap" id="photoSearchOut">' + photoSearchResults(key) + "</div>" +
      '<div style="height:12px"></div><button class="btn-line" data-close="1">닫기</button>';
  }

  /* ==========================================================================
     v38: 날짜 모아보기 — 한 날의 사진을 3열 정사각형으로
     --------------------------------------------------------------------------
     기본 목록의 날짜·사진 또는 사진 달력의 날짜 칸을 누르면 이 화면이 먼저 열리고,
     사진을 한 장 누르면 전체 화면 크게 보기가 열립니다. 크게 보기를 닫으면 이 화면으로 돌아와요.
     ========================================================================== */
  var photoDayView = null;      /* 'YYYY-MM-DD' — 보고 있는 날짜 모아보기 */
  var photoDayAll = false;      /* v42: 날짜 모아보기에서 9장을 넘겨 «전체 보기»로 펼쳤는지 */
  var PG_DAY_MAX = 9;           /* v42: 날짜 모아보기는 3×3 9장까지, 넘치면 9번째 칸에 +N */
  var pendingPhotoDate = "";    /* v38: 그 날짜에 사진 추가 — 사진 추가 시트의 날짜 기본값 */
  var photoAddMore = false;     /* v38: 사진 추가 시트의 「추가」 — 지금 목록에 이어 담기 */
  var photoToBottom = true;     /* v39: 사진 목록을 그리면 맨 아래(가장 최근 날짜)로 맞출지 */

  function photoDayItems(day) {
    return S.photos.filter(function (p) { return String(p.date || "").slice(0, 10) === day; }).sort(byDateDesc);
  }
  function openDayGallery(day) {
    var ds = String(day || "").slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(ds)) return;
    photoDayView = ds;
    photoDayAll = false;
    renderPhoto();
    $("#screens").scrollTop = 0;
  }
  /* ==========================================================================
     v40: 날짜 모아보기 — 위에 3열 사진, 그 아래 «사진마다 댓글»
     사진을 누르면 사진만 보이는 크게 보기(풀스크린)로 넘어가고,
     댓글·대댓글은 이 화면에서 사진 아래에 바로 달아요.
     ========================================================================== */
  /* v41: 날짜(챕터) 댓글 — 그날 사진 전체에 «하나의 댓글 칸».
     · 사진마다 「1번째 사진 · 제목」 카드와 입력줄을 반복하지 않아요
     · 예전(v40)에 사진마다 달아 둔 댓글도 이 날짜 칸에 모아 보여 줘요
     · 새로 다는 댓글은 그날의 대표(첫 번째) 사진에 담아 photos.memo 동기화를 그대로 써요
     · 대댓글은 그 댓글이 있던 사진에 그대로 붙어요 (상대 폰에서도 같은 날짜 칸에 보임) */
  function dayRepPhoto(day) { return photoDayItems(day)[0] || null; }
  function dayChapterComments(day) {
    var out = [];
    photoDayItems(day).forEach(function (p) {
      ((p && p.comments) || []).forEach(function (c) { out.push({ p: p, c: c }); });
    });
    return out;
  }
  function dayChapterCount(day) {
    return dayChapterComments(day).reduce(function (n, e) { return n + 1 + ((e.c.replies || []).length); }, 0);
  }
  function dayCmtBody(day) {
    var h = '<div class="cmt-list">';
    dayChapterComments(day).forEach(function (e) {
      h += cmtRowHtml(e.c, false, e.c.id, e.p.id);
      (e.c.replies || []).forEach(function (r) { h += cmtRowHtml(r, true, e.c.id, e.p.id); });
    });
    h += "</div>";
    h += cmtFormHtml(dayRepPhoto(day), day);
    return h;
  }
  function dayCmtHtml(day) {
    return '<section class="dcmt dcmt-day" id="dcmtWrap" data-day="' + esc(day) + '">' + dayCmtBody(day) + "</section>";
  }
  /* 댓글·답글·삭제 뒤 그 날짜 칸만 다시 그림 (사진 또는 날짜 문자열을 받아요) */
  function refreshDayCmt(target) {
    var day = typeof target === "string" ? target : String((target && target.date) || "").slice(0, 10);
    var sec = document.querySelector("#s-photo .dcmt.dcmt-day");
    if (!sec || !day) return;
    sec.setAttribute("data-day", day);
    sec.innerHTML = dayCmtBody(day);
  }

  function renderPhotoDay() {
    var day = photoDayView;
    var d = parse(day);
    var items = photoDayItems(day);
    var h = '<header class="hdr hdr-min dgal-hd' + capCls("photo") + '"' + capStyle("photo") + ' data-pg="photo">' +
      '<div class="dgal-l">' +
      '<button class="dgal-back" type="button" data-act="photoDayBack" aria-label="사진첩으로 돌아가기" title="사진첩으로">' + IC.left + "</button>" +
      /* v42: 목록과 똑같이 「11월 21일 · 롯데 리조트」 — 연도·오늘 표기는 헤더에서 빼고 장수 옆으로 */
      '<div class="dgal-tt"><h1>' + (d.getMonth() + 1) + "월 " + d.getDate() + "일</h1>" +
      (dateTagOf(day) ? '<span class="dgal-dot" aria-hidden="true">·</span>' +
        '<button type="button" class="dgal-tag on" data-act="dateTag" data-date="' + day + '">' + esc(dateTagOf(day)) + "</button>" : "") +
      "</div></div>" +
      /* v40: 오른쪽 위 「+」 대신 «수정» 아이콘 — 누르면 이 날짜 사진 편집 시트(날짜·태그·순서·삭제·추가) */
      '<div class="hdr-acts"><button class="round-btn" type="button" data-act="editPhotoDay" data-date="' + day +
      '" aria-label="이 날짜 사진 수정" title="이 날짜 사진 수정">' + IC.pencil + "</button></div></header>";
    h += '<div class="dgal"><div class="dgal-meta">총 ' + items.length + "장" +
      (day === today ? " · 오늘" : (day === addDays(today, -1) ? " · 어제" : "")) + "</div>";
    if (items.length) {
      /* v42: 9장(3×3)까지만 먼저 — 넘치면 9번째 칸 오른쪽 아래에 「+N」 배지
         (배지를 누르면 나머지까지 펼쳐 보고, 사진을 누르면 그날 사진 전체를 크게 보기로 넘겨요) */
      var over = items.length > PG_DAY_MAX;
      var shown = (over && !photoDayAll) ? items.slice(0, PG_DAY_MAX) : items;
      var rest = items.length - PG_DAY_MAX;
      h += '<div class="dgrid" data-day="' + day + '">';
      shown.forEach(function (p, i) {
        /* 9번째 칸 오른쪽 아래 「+N」 — 누르면 나머지 사진까지 펼쳐요 (사진 자체를 누르면 전체 크게 보기) */
        var plus = (over && !photoDayAll && i === shown.length - 1)
          ? '<button class="dg-moren" type="button" data-act="photoDayExpand" data-day="' + esc(day) +
            '" aria-label="나머지 ' + rest + '장 더 보기">+' + rest + "</button>" : "";
        /* v42: 9장만 보이는 동안은 «9번째 사진»을 눌러도 크게 보기가 아니라 그 아래로 나머지를 펼쳐요 */
        var lastCell = (over && !photoDayAll && i === shown.length - 1);
        h += '<div class="dg-wrap">' +
          '<button class="dg-cell" type="button" data-act="' + (lastCell ? "photoDayExpand" : "openPhoto") +
          '" data-id="' + p.id + '" data-day="' + esc(day) +
          '" aria-label="' + (lastCell ? "이 날 사진 " + items.length + "장 모두 보기"
            : esc(p.title || p.album || "사진") + " 크게 보기") + '">' + photoImg(p) + "</button>" +
          /* v43: 사진마다 붙던 «⋯» 수정 메뉴는 없앴어요 — 날짜·기록 이름·순서·빼기·추가는
             오른쪽 위 연필(사진 수정) 시트에서 한 번에 해요. 사진 칸에는 「+N」만. */
          plus + "</div>";
      });
      h += "</div>";
      /* v41: 그 날짜(챕터) 사진 전체에 댓글 한 칸만 — 프사 · 「댓글 달기」 · 「등록」 */
      h += dayCmtHtml(day);
    } else {
      h += '<div class="empty">이 날 담은 사진이 아직 없어요.<br>오른쪽 위 <b>+</b> 로 담아 보세요.</div>';
    }
    h += "</div>";
    $("#s-photo").innerHTML = h;
  }

  function renderPhoto() {
    /* v38: 날짜 모아보기 — 기본 목록·사진 달력에서 날짜를 누르면 그날 사진 전체를
       3열 정사각형 격자로 보여 주고, 사진을 누를 때만 크게 보기가 열립니다. */
    if (photoDayView) { renderPhotoDay(); return; }
    /* v21: 사진첩은 제목·「N장의 순간」 없이 오른쪽 + 버튼만 — 상단 여백도 군더더기 없이 */
    /* v23: + 옆에 달력 아이콘 — 누르면 그 달 사진을 달력으로 (다시 누르면 목록으로) */
    var pcOn = !!(S.ui && S.ui.photoCal);
    /* v40: 달력 보기에서도 머리줄은 화면 위에 붙어 있어요 — 오른쪽 위 달력 아이콘을 한 번 더 누르면
       사진첩 기본 목록으로 돌아갑니다 (아이콘은 늘 달력 모양, 켜져 있으면 진하게). */
    var h = '<header class="hdr hdr-min' + (pcOn ? " hdr-cal" : "") + capCls("photo") + '"' + capStyle("photo") + ' data-pg="photo">' +
      '<div class="hdr-empty"></div>' +
      '<div class="hdr-acts">' +
      '<button class="round-btn photo-search" data-act="photoSearch" aria-label="사진 검색" title="사진 검색">' + IC.search + "</button>" +
      '<button class="round-btn pc-toggle' + (pcOn ? " on" : "") + '" data-act="togglePhotoCal" aria-pressed="' + (pcOn ? "true" : "false") +
      '" aria-label="' + (pcOn ? "사진 목록으로" : "사진 달력 보기") +
      '" title="' + (pcOn ? "사진 목록으로" : "사진 달력 보기") + '">' + IC.cal + "</button>" +
      '<button class="round-btn" data-act="addPhoto" aria-label="사진 추가" title="사진 추가">' + IC.plus + "</button></div></header>";
    if (pcOn) {
      h += photoCalHtml();
      $("#s-photo").innerHTML = h;
      photoCalCenter();
      return;
    }
    /* 앨범 대신 날짜로 묶어요 — 하루에 담은 순간이 한 줄에 모입니다
       v37: 기본 사진첩은 «이번 달» 사진 중 가장 최근 날짜부터 3일치만.
       지난 달 사진은 오른쪽 위 달력 아이콘으로 달력을 열어 위아래로 넘겨 봅니다. */
    var groups = [];
    var map = {};
    S.photos.slice().sort(byDateDesc).forEach(function (p) {
      var k = String(p.date || "").slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(k)) return;
      if (!map[k]) { map[k] = { date: k, items: [] }; groups.push(map[k]); }
      map[k].items.push(p);
    });
    /* v39: 3일 제한 없이 사진이 있는 날을 모두 — 예전 날짜가 위, 가장 최근 날짜가 아래(아래로 쌓임) */
    groups.reverse();
    var daysHtml = "";
    groups.forEach(function (g, gi) {
      var lastGroup = gi === groups.length - 1;      /* 맨 아래 = 가장 최근 날짜 */
      /* v40: 3장을 넘기면 마지막 사진 오른쪽 아래에 작게 「+N」 만 (날짜 줄에는 안 적어요) */
      var rest = g.items.length - PHOTOS_PER_DAY;
      var meta = "";
      /* v18: 하루는 사진 3장까지 — 넘치면 세 번째에 +N, 눌러서 그날 사진을 모두 봐요 */
      var shown = g.items.slice(0, PHOTOS_PER_DAY);
      daysHtml += '<div class="pday' + (lastGroup ? " pday-last" : "") + '"><div class="pday-hd" role="button" tabindex="0" data-act="openPhotoDay" data-date="' + g.date + '">' + photoDayLabel(g.date) +
        photoDayTagHtml(g.date) +
        (meta ? '<span class="c">' + meta + "</span>" : "") + "</div>" +
        '<div class="polas">' +
        shown.map(function (p, i) {
          var more = (rest > 0 && i === shown.length - 1) ? '<span class="pola-more">+' + rest + "</span>" : "";
          /* v37: 흰 틀·기울기 없이 사진만 꽉 채운 정사각형 칸 — 캡션이 있으면 사진 아래 한 줄
             v38: 누르면 바로 크게 보기가 아니라 그날 사진 모아보기가 먼저 열려요 */
          /* v40: 사진 아래 캡션 줄은 없앴어요 — 사진만 (예전 캡션 글씨는 저장돼 있어도 안 보여요) */
          return '<button class="pola" data-act="openPhotoDay" data-date="' + g.date +
            '" aria-label="' + esc(p.album || "사진") + ' — 그날 사진 모아보기">' +
            '<span class="pola-pic">' + photoImg(p, false, lastGroup) + more + "</span></button>";
        }).join("") + "</div></div>";
    });
    if (!groups.length) {
      daysHtml += '<div class="album"><div class="list" style="margin:0"><div class="empty">' +
        "아직 사진이 없어요.<br>오른쪽 위 <b>+</b> 로 이 순간을 담아 보세요." +
        "</div></div></div>";
    }
    /* v37: 사진이 적을 때는 화면 가운데, 많아 화면을 넘기면 위에서부터 자연스럽게 스크롤
       v39: 가장 최근 날짜가 맨 아래라, 들어올 때는 그 자리(맨 아래)로 맞춰 줍니다 */
    var scr0 = document.getElementById("screens");
    var atBottom = !!(scr0 && (scr0.scrollHeight - scr0.scrollTop - scr0.clientHeight) < 48);
    h += '<div class="pbody"><div class="pdays">' + daysHtml + "</div></div>";
    $("#s-photo").innerHTML = h;
    if (photoToBottom || atBottom) photoListToBottom();
    photoToBottom = false;
  }
  /* v39: 사진 목록의 맨 아래(가장 최근 날짜)로 — 목록이 짧으면 스크롤이 없어 그대로예요
     v41: 사진은 화면에 그려진 뒤 높이가 한 번 더 잡혀요. 그래서 바로 · 다음 프레임 ·
     조금 뒤에 한 번 더 맞춰, 달력에서 목록으로 돌아오면 늘 «마지막 업로드 날짜»가 보이게 해요. */
  function photoListToBottom() {
    var scr = document.getElementById("screens");
    if (!scr) return;
    var jump = function () {
      if (photoDayView || (S.ui && S.ui.photoCal)) return;
      if (!document.querySelector("#s-photo .pbody")) return;
      scr.scrollTop = scr.scrollHeight;
    };
    jump();
    requestAnimationFrame(jump);
    setTimeout(jump, 60);
    setTimeout(jump, 240);
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
  function openSheet(html, onSubmit, opts) {
    personSheetWho = null;
    personBack = false;
    openCard = null;
    /* v38: 사진 크게 보기는 화면을 꽉 채우는 풀스크린 시트로 (다른 시트는 예전 그대로) */
    /* v41: 모눈 다이어리는 풀스크린 + 자기 배치(d41sheet) */
    sheet.className = "sheet" + ((opts && opts.cls) ? " " + opts.cls : "");
    sheetWrap.classList.toggle("sheet-full", !!(opts && opts.full));
    sheetWrap.classList.toggle("sheet-center", !!sheetCenter);
    sheetCenter = false;
    sheet.innerHTML = '<div class="grab"></div>' + html;
    /* v39: + 시트의 카테고리 줄이 있으면 줄 배지·「속지 레이아웃」 표시를 지금 상태에 맞춤 */
    if (sheet.querySelector("#noteOrderList")) nkPaint();
    sheetSubmit = onSubmit || null;
    sheetWrap.classList.add("open");
    sheetWrap.setAttribute("aria-hidden", "false");
    sheet.style.maxHeight = "";
    sheet.scrollTop = 0;
    if (sheetWrap.classList.contains("sheet-center")) { bindViewportFit(); fitCenterSheet(); }
  }
  function closeSheet() {
    personSheetWho = null;
    personBack = false;
    openCard = null;
    upMode = "pending";            /* v40: 사진 편집 시트를 닫으면 순서 모드도 새로 담기로 */
    dayEdit = null;
    dayAddMore = false;
    photoView = null;   /* v37: 사진 크게 보기를 닫으면 보던 목록도 끝 — 달럭 밑기·사진 넘기기가 남아 있지 않게 */
    diary = null;       /* v41: 다이어리를 닫으면 편집 상태도 끝 */
    newCard = null;     /* v41: 저장하지 않고 닫은 새 카드는 남기지 않아요 */
    sheet.className = "sheet";
    sheetWrap.classList.remove("sheet-center");
    sheetWrap.classList.remove("sheet-full");
    sheet.style.maxHeight = "";
    sheetWrap.classList.remove("open");
    sheetWrap.setAttribute("aria-hidden", "true");
    sheetSubmit = null;
    pendingUrls.forEach(function (u) { try { URL.revokeObjectURL(u); } catch (e) {} });
    pendingUrls = [];
    pendingFiles = [];
    photoAddMore = false;
    /* 시트에서 고친 내용(카드 안 To-do 등)이 뒤 화면에도 바로 보이도록 노트를 다시 그림 */
    var dEl = document.getElementById("s-diary");
    if (dEl && dEl.classList.contains("active")) renderDiary();
    /* v38: 사진 크게 보기를 닫으면 그 날짜 모아보기로 돌아오고, 지운·고친 사진도 바로 반영 */
    if (current === "photo") renderPhoto();
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

  /* v34: + 시트 한 장에서 «새 카테고리 추가 · 탭 이름 수정 · ≡ 로 순서 바꾸기»를 한 번에 해요.
     (v33 까지 따로 있던 「카테고리 이름」「형식」 라벨·버튼과 「탭 이름 수정」 링크는 없앴습니다) */
  function formNewList(l) {
    var h = sheetHead(l ? "카테고리 수정" : "새 카테고리");
    h += '<p class="sheet-sub">' + (l ? "이름을 바꾸고 순서를 정리한 뒤 저장해요." : "새 카테고리를 더하고, 탭 이름과 순서를 한 번에 정리해요.") + "</p>";
    h += '<form class="form nsheet" id="sheetForm">';
    /* v36: 이름은 네모칸 대신 밑줄만 있는 칸으로. 「추가」를 누르면(또는 엔터) 아래 목록에
       바로 한 줄로 붙어서, 이름을 확인하고 ≡ 로 순서를 옮기는 일을 한 화면에서 이어서 해요.
       (붙인 줄은 아직 저장 전 — 「저장하기」를 누르면 확정되고, 그냥 닫으면 사라집니다) */
    h += '<div class="nord-new-row">' +
      '<input class="nord-new" name="title" value="" placeholder="새 카테고리 이름" aria-label="새 카테고리 이름" autocomplete="off">' +
      '<button type="button" class="nord-add-btn" data-act="nordAdd">추가</button></div>';
    h += '<div class="set-lbl" style="margin-top:18px">노트 카테고리</div>';
    /* v40: 속지 레이아웃은 목록 맨 아래가 아니라 «카테고리 줄을 눌렀을 때 그 줄 바로 아래»에 펼쳐져요 */
    h += '<div class="nord-hint nord-hint-top">줄을 누르면 그 카테고리의 속지가 바로 아래에 펼쳐져요. ≡ 를 끌면 탭 순서가 바뀝니다.</div>';
    h += '<div class="nord" id="noteOrderList">';
    var selKey = l ? "list:" + l.id : "";
    noteOrderList().forEach(function (k) { h += noteOrderRow(k, null, null, k === selKey); });
    h += "</div>";
    h += '<div class="nk-panel" id="nkPanel" hidden></div>';
    h += '<input type="hidden" name="del" id="noteDelIds" value="">';
    h += '<div style="height:14px"></div><button class="btn-primary" type="submit">저장하기</button></form>';
    return h;
  }

  /* v40: 카테고리 줄 아래에 펼쳐지는 속지 2×2 —
     기본 카테고리도 «투두리스트»부터, 내 카테고리·새로 더한 줄은 네 속지만 보여요.
     v41: 기본 카테고리에 있던 「카드」 라벨은 «투두리스트»로 통일 (보이는 모양·항목은 그대로) */
  function nkPanelHtml(kind, isBase, name, key) {
    var list = isBase
      ? [{ k: "", n: "투두리스트", d: "카드로 모아 보기" }].concat(
          LIST_KINDS.filter(function (k) { return k !== "check"; }).map(function (k) {
            return { k: k, n: LIST_KIND_DEF[k].n, d: LIST_KIND_DEF[k].d };
          }))
      : LIST_KINDS.map(function (k) { return { k: k, n: LIST_KIND_DEF[k].n, d: LIST_KIND_DEF[k].d }; });
    var cur = isBase ? (kind || "") : (LIST_KINDS.indexOf(kind) >= 0 ? kind : "check");
    var nm = String(name || "").trim();
    /* v42: 제목은 「속지」만 · 안내는 「이름에 쓸 속지를 골라요.」 (「」 괄호 없이) */
    var h = '<div class="set-lbl" id="nkindLbl">속지</div>';
    h += '<div class="nkind-hint" id="nkindHint">' + esc((nm || "이 카테고리") + "에 쓸 속지를 골라요.") + "</div>";
    h += '<div class="nkind" data-group="nkind" data-key="' + esc(key || "") + '">';
    list.forEach(function (o) {
      h += '<button type="button" class="nk-card' + (o.k === cur ? " active" : "") + '" data-act="nkind" data-kind="' + o.k + '">' +
        '<span class="nk-n">' + esc(o.n) + "</span>" +
        '<span class="nk-d">' + esc(o.d) + "</span>" +
        '<span class="nk-ck">' + IC.check + "</span></button>";
    });
    h += "</div>";
    /* 새 카테고리 이름을 위 칸에 적고 바로 저장할 때 쓸 기본 속지 */
    h += '<input type="hidden" name="nkind" value="' + esc(cur) + '">';
    return h;
  }
  function nkPanelEl() { return document.getElementById("nkPanel"); }
  function nkHiddenKind() {
    var i = document.querySelector('#sheet input[name="nkind"]');
    return i ? String(i.value || "") : "";
  }
  /* 고른 줄 바로 아래로 패널을 옮겨 펼칩니다. 줄이 없으면 접어 두고, 올린 순서는 그대로 둬요. */
  function nkPlacePanel(row) {
    var box = document.querySelector("#sheet #noteOrderList");
    if (!box) return null;
    var p = nkPanelEl();
    if (!p) {
      p = document.createElement("div");
      p.id = "nkPanel";
      p.className = "nk-panel";
      box.parentNode.insertBefore(p, box.nextSibling);
    }
    if (!row) {
      var dk = nkHiddenKind();
      if (LIST_KINDS.indexOf(dk) < 0) dk = "check";
      p.innerHTML = nkPanelHtml(dk, false, "", "");
      p.hidden = true;
      p.classList.remove("open");
      return p;
    }
    var key = row.getAttribute("data-key") || "";
    var isBase = NOTE_BASE.indexOf(key) >= 0;
    var kind = row.getAttribute("data-kind") || "";
    var nmIn = row.querySelector(".nord-nm");
    p.innerHTML = nkPanelHtml(kind, isBase, nmIn ? nmIn.value : "", key);
    if (row.nextElementSibling !== p) box.insertBefore(p, row.nextElementSibling || null);
    p.hidden = false;
    p.classList.add("open");
    return p;
  }

  /* + 시트의 카테고리 한 줄 — 3줄 손잡이 · 이름 칸 · 지금 속지 배지 · (내가 만든 카테고리·새로 더한 줄만) 삭제 */
  function noteOrderRow(k, tempName, tempKind, selected) {
    var isNew = k.indexOf("new:") === 0;
    var isList = k.indexOf("list:") === 0 || isNew;
    var name = "", id = "", kind = "";
    if (isNew) {
      name = String(tempName || "");
      id = k.slice(4);
      kind = LIST_KINDS.indexOf(tempKind) >= 0 ? tempKind : "check";
    } else if (isList) {
      var l = findList(k.slice(5));
      if (!l) return "";
      name = listLabel(l);
      id = l.id;
      kind = listKindOf(l);
    } else {
      name = noteLabel(k);
      kind = noteBaseKind(k);           /* "" = 지금 모양(카드) 그대로 */
    }
    return '<div class="nord-row' + (isNew ? " nord-temp" : "") + (selected ? " active" : "") +
      '" data-key="' + esc(k) + '" data-kind="' + esc(kind) + '">' +
      '<button type="button" class="nord-grip" data-act="nordGrip" aria-label="순서 바꾸기 — 끌거나 위·아래 화살표" title="끌어서 위아래로 옮겨요">' + IC.grip + "</button>" +
      '<input class="field nord-nm" name="n_' + esc(k) + '" value="' + esc(name) + '" aria-label="카테고리 이름" autocomplete="off">' +
      /* v42: 줄 오른쪽 속지 배지(「투두리스트」 등)는 없앴어요 — ≡ 손잡이 + 이름(+ 삭제)만.
         지금 속지는 줄 아래로 펼쳐지는 패널에서 확인·변경해요 */
      (isList ? '<button type="button" class="nt-del nord-del" data-act="nordDel" data-id="' + esc(id) + '" aria-label="삭제">삭제</button>' : "") +
      "</div>";
  }

  /* v39: 속지 이름 — "" 는 기본 카테고리의 지금 모양(투두리스트 = 카드로 모아 보기)
     v41: 예전 「카드」 라벨을 «투두리스트»로 통일 */
  function nkKindName(kind) {
    return LIST_KIND_DEF[kind] ? LIST_KIND_DEF[kind].n : "투두리스트";
  }
  /* v42: 이미 쓴 내용(항목)이 있는 카테고리는 속지를 바꿀 수 없어요.
     바꾸면 지금 글이 그 속지 화면에서 어떻게 보일지 보장할 수 없어서요. 빈 카테고리만 자유롭게. */
  function catHasContent(k) {
    if (!k || String(k).indexOf("new:") === 0) return false;
    return itemsOf(k).length > 0;
  }
  function kindBlockMsg() { return "이미 작성된 내용이 있어 속지를 바꿀 수 없어요"; }
  function kindBlocked(nrow) {
    toast(kindBlockMsg());
    var hint = document.getElementById("nkindHint");
    if (hint) { hint.textContent = kindBlockMsg(); hint.classList.add("warn"); }
    if (nrow && nrow.animate) {
      nrow.animate([{ transform: "translateX(0)" }, { transform: "translateX(-4px)" },
        { transform: "translateX(4px)" }, { transform: "translateX(0)" }], { duration: 220 });
    }
    return false;
  }
  function nkSelectedRow() {
    return document.querySelector("#sheet #noteOrderList .nord-row.active");
  }
  /* + 시트의 표시를 한 번에 맞춤 — 줄 배지 · 속지 패널(고른 줄 바로 아래) · 2×2 카드 체크
     v40: 패널은 고른 줄 아래로만 붙고, 아무 줄도 고르지 않았으면 접혀 있어요. */
  function nkPaint() {
    var box = document.querySelector("#sheet #noteOrderList");
    if (!box) return;
    nkPlacePanel(nkSelectedRow());
  }
  function nkSelectRow(row) {
    var box = document.querySelector("#sheet #noteOrderList");
    if (!box) return;
    Array.prototype.forEach.call(box.querySelectorAll(".nord-row"), function (r) {
      r.classList.toggle("active", !!row && r === row);
    });
    nkPaint();
  }
  /* v47: 방금 더한 줄과 그 «속지» 판이 화면 밖이면 부드럽게 끌어와 보여 줘요 */
  var nkKeepT = 0;
  function nkReveal(row) {
    if (!row) return;
    setTimeout(function () {
      if (!row.isConnected) return;
      var p = nkPanelEl();
      var t = (p && !p.hidden) ? p : row;
      if (!t || !t.scrollIntoView) return;
      try { t.scrollIntoView({ block: "center", behavior: "smooth" }); }
      catch (e) { try { t.scrollIntoView(); } catch (e2) {} }
    }, 130);
  }
  /* 줄을 누르면 그 줄이 선택되고 그 아래에 속지가 펼쳐져요. 같은 줄을 한 번 더 누르면 접힙니다.
     이름칸을 고치러 들어갈 때는 접히지 않고, ≡ 손잡이·삭제 버튼은 그대로 자기 일을 해요. */
  document.addEventListener("pointerdown", function (ev) {
    var t = ev.target;
    if (!t || !t.closest || !t.closest("#sheet")) return;
    var row = t.closest("#sheet #noteOrderList .nord-row");
    if (row) {
      if (t.closest(".nord-grip") || t.closest(".nord-del")) return;
      if (t.closest(".nord-nm")) { if (!row.classList.contains("active")) nkSelectRow(row); return; }
      nkSelectRow(row.classList.contains("active") ? null : row);
      return;
    }
    if (t.closest("#sheet .nord-new") || t.closest("#sheet .nord-add-btn")) {
      if (Date.now() >= nkKeepT) nkSelectRow(null);   /* v47: 방금 더한 줄은 접지 않아요 */
    }
  }, true);
  document.addEventListener("focusin", function (ev) {
    var t = ev.target;
    if (!t || !t.closest || !t.closest("#sheet")) return;
    if (t.closest("#sheet .nord-new")) { if (Date.now() >= nkKeepT) nkSelectRow(null); return; }
    var row = t.closest("#sheet #noteOrderList .nord-row");
    if (row && t.classList && t.classList.contains("nord-nm")) nkSelectRow(row);
  }, true);

  /* v34: + 시트의 ≡ 손잡이 — 터치·마우스로 끌어 순서를 실시간으로 바꿔요.
     v36: 끌고 있는 줄은 손가락을 따라 부드럽게 따라가고(빈 자리는 그대로),
     자리를 비켜 주는 줄들은 FLIP 애니메이션으로 미끄러져 자리를 바꾸며,
     놓으면 제자리로 부드럽게 안착합니다. */
  var nordDrag = null;
  var NORD_EASE = "cubic-bezier(.22,1,.36,1)";

  function nordRowsOf(box) {
    return Array.prototype.slice.call(box.querySelectorAll(".nord-row"));
  }
  function nordGapOf(box) {
    var gap = 6;
    try {
      var cs = window.getComputedStyle(box);
      var g = parseFloat(cs.rowGap || cs.gap || "");
      if (!isNaN(g)) gap = g;
    } catch (e) {}
    return gap;
  }
  /* 자리를 비켜 주는 줄들만 부드럽게 미끄러지게 (FLIP: 먼저 재고 → 옮기고 → 되돌려 놀았다가 → 제자리) */
  function nordFlip(box, keep, mutate, sel) {
    var rows = (sel ? Array.prototype.slice.call(box.querySelectorAll(sel)) : nordRowsOf(box))
      .filter(function (r) { return r !== keep; });
    var before = rows.map(function (r) { return r.getBoundingClientRect().top; });
    mutate();
    rows.forEach(function (r, i) {
      if (!r.isConnected) return;
      var d = before[i] - r.getBoundingClientRect().top;
      r.style.transition = "none";
      r.style.transform = d ? "translateY(" + d + "px)" : "";
      if (!d) { r.style.transition = ""; return; }
      void r.offsetHeight;                       /* 되돌려 놓은 자리를 먼저 그리게 */
      r.style.transition = "transform 180ms " + NORD_EASE;
      r.style.transform = "";
      clearTimeout(r._flipTid);
      r._flipTid = setTimeout(function () { r.style.transition = ""; r.style.transform = ""; }, 230);
    });
  }
  function nordMove(row, dir) {
    if (!row) return false;
    var box = row.parentNode;
    if (!box) return false;
    if (dir < 0 && row.previousElementSibling) {
      nordFlip(box, row, function () { box.insertBefore(row, row.previousElementSibling); });
      if (row.classList.contains("active")) nkPaint();     /* v40: 펼친 패널도 줄을 따라가요 */
      return true;
    }
    if (dir > 0 && row.nextElementSibling) {
      var nx = row.nextElementSibling;
      nordFlip(box, nx, function () { box.insertBefore(nx, row); });
      if (row.classList.contains("active")) nkPaint();
      return true;
    }
    return false;
  }
  function nordEnd() {
    var d = nordDrag;
    if (!d) return;
    nordDrag = null;
    var row = d.row;
    /* 제자리로 매끄럽게 안착 */
    row.style.transition = "transform 200ms " + NORD_EASE;
    row.style.transform = "translateY(0)";
    var settle = function () {
      row.removeEventListener("transitionend", settle);
      row.style.transition = "";
      row.style.transform = "";
      row.style.zIndex = "";
      row.classList.remove("dragging");
    };
    row.addEventListener("transitionend", settle);
    setTimeout(settle, 260);
  }
  document.addEventListener("pointerdown", function (ev) {
    var g = ev.target && ev.target.closest ? ev.target.closest("#sheet .nord-grip") : null;
    if (!g) return;
    var row = g.closest(".nord-row"), box = g.closest(".nord");
    if (!row || !box) return;
    ev.preventDefault();                 /* 끄는 동안 시트가 스크롤되지 않도록 */
    /* v40: 펼쳐진 속지 패널이 끌기 계산을 흔들지 않게 끌기 시작할 때 접어요 */
    if (document.getElementById("nkPanel")) nkSelectRow(null);
    var rb = row.getBoundingClientRect();
    nordDrag = {
      grip: g, row: row, box: box, id: ev.pointerId,
      startY: ev.clientY,
      translate: 0,
      h: rb.height,
      center: rb.top + rb.height / 2,
      step: rb.height + nordGapOf(box),
      order: nordRowsOf(box)
    };
    row.style.transition = "none";
    row.style.zIndex = "5";
    row.classList.add("dragging");
    try { g.setPointerCapture(ev.pointerId); } catch (e) {}
  }, true);
  document.addEventListener("pointermove", function (ev) {
    var d = nordDrag;
    if (!d || ev.pointerId !== d.id) return;
    if (ev.cancelable) ev.preventDefault();
    var row = d.row, box = d.box;
    var boxTop = box.getBoundingClientRect().top;
    /* 손가락이 움직인 만큼 줄 가운데가 갔을 자리 → 몇 번째 순서로 갈지 */
    var desiredTop = (d.center + (ev.clientY - d.startY)) - d.h / 2;
    var want = Math.round((desiredTop - boxTop) / d.step);
    want = Math.max(0, Math.min(d.order.length - 1, want));
    var cur = d.order.indexOf(row);
    if (want !== cur) {
      nordFlip(box, row, function () {
        d.order.splice(cur, 1);
        d.order.splice(want, 0, row);
        box.insertBefore(row, d.order[want + 1] || null);
      });
    }
    /* 줄이 옮겨 간 뒤에도 손가락 아래 같은 자리에 있도록 translate 다시 맞추기 */
    var natural = row.getBoundingClientRect().top - d.translate;
    d.translate = desiredTop - natural;
    row.style.transform = "translateY(" + d.translate + "px)";
  }, true);
  document.addEventListener("pointerup", nordEnd, true);
  document.addEventListener("pointercancel", nordEnd, true);
  /* 손잡이를 고르고 ↑ ↓ 키로도 옮길 수 있게 */
  document.addEventListener("keydown", function (ev) {
    var g = ev.target && ev.target.closest ? ev.target.closest("#sheet .nord-grip") : null;
    if (!g) return;
    var d = ev.key === "ArrowUp" ? -1 : (ev.key === "ArrowDown" ? 1 : 0);
    if (!d) return;
    ev.preventDefault();
    if (nordMove(g.closest(".nord-row"), d)) g.focus();
  }, true);

  /* ==========================================================================
     v40: 사진 추가 시트의 고른 사진 순서 — 맨 앞 ≡ 손잡이를 끌어 위아래로 옮겨요.
     노트 카테고리(nordDrag)와 같은 방식: 손가락을 따라 떠 있고, 자리를 비켜 주는
     줄들은 FLIP 으로 미끄러지며, 놓으면 pendingFiles 배열 순서도 그대로 바뀝니다.
     (키보드 ↑ ↓ 로도 옮길 수 있어요)
     ========================================================================== */
  var upDrag = null;
  function upCellsOf(box) { return Array.prototype.slice.call(box.querySelectorAll(".up-cell")); }
  /* v41: 같은 그리드로 «사진 추가 시트»와 «날짜 사진 편집 시트» 둘 다 순서를 바꿔요 */
  var upMode = "pending";      // pending: 새로 담는 사진들 · day: 그날 이미 올라간 사진 편집
  function upArray() { return (upMode === "day" && dayEdit) ? dayEdit.items : pendingFiles; }
  /* 칸이 가로·세로로 미끄러지는 FLIP (그리드라 위아래뿐 아니라 좌우도 함께) */
  function upFlip(box, keep, mutate) {
    var cells = upCellsOf(box).filter(function (r) { return r !== keep; });
    var before = cells.map(function (r) { var b = r.getBoundingClientRect(); return { x: b.left, y: b.top }; });
    mutate();
    cells.forEach(function (r, i) {
      if (!r.isConnected) return;
      var b = r.getBoundingClientRect();
      var dx = before[i].x - b.left, dy = before[i].y - b.top;
      r.style.transition = "none";
      r.style.transform = (dx || dy) ? "translate(" + dx + "px," + dy + "px)" : "";
      if (!dx && !dy) { r.style.transition = ""; return; }
      void r.offsetHeight;
      r.style.transition = "transform 180ms " + NORD_EASE;
      r.style.transform = "";
      clearTimeout(r._flipTid);
      r._flipTid = setTimeout(function () { r.style.transition = ""; r.style.transform = ""; }, 240);
    });
  }
  /* 화면에 보이는 순서를 지금 목록(pendingFiles · dayEdit.items)에 반영해요 */
  function upCommitOrder() {
    var box = document.querySelector("#sheet #upList");
    if (!box) return;
    var arr = upArray();
    var order = upCellsOf(box).map(function (r) { return Number(r.getAttribute("data-i")); });
    var next = [];
    order.forEach(function (i) { if (arr[i]) next.push(arr[i]); });
    arr.forEach(function (f) { if (next.indexOf(f) < 0) next.push(f); });
    if (upMode === "day" && dayEdit) dayEdit.items = next;
    else pendingFiles = next;
    /* 칸은 그대로 두고 data-i 만 지금 순서로 다시 매겨요 (포커스도 유지) */
    upCellsOf(box).forEach(function (r, i) {
      r.setAttribute("data-i", String(i));
      var x = r.querySelector(".up-x");
      if (x) x.setAttribute("data-i", String(i));
    });
    var cnt = document.querySelector("#sheet #upCount");
    if (cnt) cnt.textContent = String(arr.length);
    if (upMode === "day") return;
    /* v45: 「사진 추가」 아래 장수·용량 요약 줄(#upSum)은 없앴어요 — 담기 단추 글씨만 맞춥니다 */
    var btn = document.querySelector("#sheet #upBtn");
    if (btn) btn.textContent = pendingFiles.length + "장 담기";
  }
  function upEnd() {
    var d = upDrag;
    if (!d) return;
    upDrag = null;
    if (d.moved) {
      d.cell.classList.remove("dragging");
      d.cell.style.zIndex = "";
    }
    upCommitOrder();
  }
  /* 한 칸 옮기기 — 그리드 안에서 ←→ 는 한 칸, ↑↓ 는 한 줄(6칸) */
  function upMoveCell(cell, delta) {
    if (!cell) return false;
    var box = cell.parentNode;
    if (!box) return false;
    var cells = upCellsOf(box);
    var i = cells.indexOf(cell), j = i + delta;
    if (j < 0 || j >= cells.length) return false;
    var ref = cells[j];
    upFlip(box, cell, function () {
      if (delta > 0) box.insertBefore(cell, ref.nextElementSibling);
      else box.insertBefore(cell, ref);
    });
    upCommitOrder();
    return true;
  }
  /* 사진 네모를 끌어다 놓으면 그 자리로 옮겨져요 (누르고 끌기 · 가로세로 모두) */
  document.addEventListener("pointerdown", function (ev) {
    var t = ev.target;
    if (!t || !t.closest) return;
    if (t.closest("#sheet .up-x")) return;
    var c = t.closest("#sheet #upList .up-cell");
    if (!c) return;
    var box = document.getElementById("upList");
    if (!box) return;
    /* 사진을 끄는 동안 브라우저의 «이미지 끌기»가 시작되지 않게 (pointercancel 방지) */
    if (ev.cancelable) ev.preventDefault();
    upDrag = { cell: c, box: box, id: ev.pointerId, sx: ev.clientX, sy: ev.clientY, moved: false };
    try { if (c.setPointerCapture) c.setPointerCapture(ev.pointerId); } catch (e) {}
  }, true);
  document.addEventListener("pointermove", function (ev) {
    var d = upDrag;
    if (!d || ev.pointerId !== d.id) return;
    var dx = ev.clientX - d.sx, dy = ev.clientY - d.sy;
    if (!d.moved) {
      if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
      d.moved = true;
      d.cell.classList.add("dragging");
      d.cell.style.zIndex = "5";
    }
    if (ev.cancelable) ev.preventDefault();
    var box = d.box;
    var cells = upCellsOf(box);
    var first = cells[0];
    if (!first) return;
    var r0 = first.getBoundingClientRect();
    var gr = box.getBoundingClientRect();
    var cw = Math.max(1, r0.width + 6), ch = Math.max(1, r0.height + 6);
    var col = Math.max(0, Math.min(5, Math.floor((ev.clientX - gr.left) / cw)));
    var row = Math.max(0, Math.floor((ev.clientY - gr.top) / ch));
    var want = Math.min(cells.length - 1, row * 6 + col);
    var cur = cells.indexOf(d.cell);
    if (want !== cur) {
      upFlip(box, d.cell, function () {
        var list = upCellsOf(box);
        var ref = list[want];
        if (want > cur) box.insertBefore(d.cell, ref ? ref.nextElementSibling : null);
        else box.insertBefore(d.cell, ref || null);
      });
    }
  }, true);
  document.addEventListener("pointerup", upEnd, true);
  document.addEventListener("pointercancel", upEnd, true);
  /* 칸을 고르고 ← → ↑ ↓ 키로도 옮길 수 있게 */
  document.addEventListener("keydown", function (ev) {
    var c = ev.target && ev.target.closest ? ev.target.closest("#sheet #upList .up-cell") : null;
    if (!c) return;
    var d = ev.key === "ArrowLeft" ? -1 : (ev.key === "ArrowRight" ? 1 :
            (ev.key === "ArrowUp" ? -6 : (ev.key === "ArrowDown" ? 6 : 0)));
    if (!d) return;
    ev.preventDefault();
    if (upMoveCell(c, d)) { try { c.focus(); } catch (e) {} }
  }, true);

  /* v36: 「추가」/엔터 — 입력칸의 이름을 목록 맨 아래 줄로 붙입니다.
     아직 S.lists 에 들어가지 않고(취소하면 사라짐), 「저장하기」에서 리스트로 확정돼요. */
  function nordAddTemp() {
    var inp = document.querySelector("#sheet .nord-new");
    var nm = inp ? String(inp.value || "").trim() : "";
    if (!nm) { toast("카테고리 이름을 적어 주세요"); if (inp) inp.focus(); return false; }
    var box = document.querySelector("#sheet #noteOrderList");
    if (!box) return false;
    var key = "new:" + uid();
    var kindInp0 = document.querySelector('#sheet input[name="nkind"]');
    var kind0 = kindInp0 ? String(kindInp0.value || "") : "check";
    if (LIST_KINDS.indexOf(kind0) < 0) kind0 = "check";
    box.insertAdjacentHTML("beforeend", noteOrderRow(key, nm, kind0));
    inp.value = "";
    /* v47: 이름 칸에 커서를 남겨 두면 아이폰 키보드가 속지 판을 가리고,
       늦게 오는 focusin 이 방금 고른 줄을 접어 버려요 — 커서를 놓고 새 줄로 넘어갑니다. */
    try { if (inp.blur) inp.blur(); } catch (e) {}
    nkKeepT = Date.now() + 900;       /* 곷 붙인 직후에는 새 줄의 속지 판을 접지 않아요 */
    var rows = nordRowsOf(box);
    var last = rows[rows.length - 1];
    /* v39: 방금 붙인 줄을 그대로 선택 — 이름을 확인하고 바로 속지를 고를 수 있게
       v47: 그 줄의 «속지» 판까지 화면 안으로 부드럽게 끌어와 바로 고를 수 있게 */
    if (last) nkSelectRow(last);
    nkReveal(last);
    return true;
  }
  /* 입력칸에서 엔터 → 바로 목록에 추가 (폼이 제출되어 시트가 닫히지 않게) */
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter") return;
    var el = ev.target;
    if (!el || !el.classList || !el.classList.contains("nord-new")) return;
    ev.preventDefault();
    nordAddTemp();
  }, true);

  /* v34: + 시트 저장 — 위 칸의 새 이름은 새 카테고리로, 아래 줄들의 이름·순서는 노트 탭 이름·순서로 반영해요.
     v36: 목록에서 「추가」로 붙인 줄은 먼저 리스트로 만들고, 붙여 둔 그 자리에 그대로 넣습니다. */
  function saveNoteSheet() {
    /* v38: 「속지 레이아웃」에서 고른 속지 — 이 시트에서 새로 만드는 카테고리에 적용하고,
       카테고리 수정으로 열었으면 그 카테고리의 속지도 바꾸어요. */
    var kindInp = document.querySelector('#sheet input[name="nkind"]');
    var nkind = kindInp ? String(kindInp.value || "") : "check";
    if (LIST_KINDS.indexOf(nkind) < 0) nkind = "check";
    var kindTgtInp = document.querySelector('#sheet input[name="nkind_target"]');
    var kindTarget = kindTgtInp ? String(kindTgtInp.value || "") : "";
    var box = document.querySelector("#sheet #noteOrderList");
    var rows = box ? Array.prototype.slice.call(box.querySelectorAll(".nord-row")) : [];
    var added = false, firstNew = "", newMap = {}, blockedKind = false;
    rows.forEach(function (r) {
      var k = r.getAttribute("data-key") || "";
      if (k.indexOf("new:") !== 0) return;
      var inp0 = r.querySelector(".nord-nm");
      var sp0 = splitEmojiName(inp0 ? String(inp0.value || "") : "");
      if (!sp0.n) return;                        /* 이름을 지우면 그냥 버림 */
      var rk0 = r.getAttribute("data-kind") || "";
      var nl0 = { id: uid(), title: sp0.n, emoji: sp0.e, kind: LIST_KINDS.indexOf(rk0) >= 0 ? rk0 : nkind, items: [] };
      S.lists.push(nl0);
      newMap[k] = "list:" + nl0.id;
      if (!firstNew) firstNew = newMap[k];
      added = true;
    });
    var order = [], names = {};
    rows.forEach(function (r) {
      var k = r.getAttribute("data-key") || "";
      if (!k) return;
      if (newMap[k]) { order.push(newMap[k]); return; }
      var inp = r.querySelector(".nord-nm");
      order.push(k);
      names[k] = inp ? String(inp.value || "") : "";
    });
    if (rows.length) {
      /* 기본 탭 이름 — 「이모지 + 이름」을 적으면 앞 이모지와 이름으로 나눠 저장해요 */
      NOTE_BASE.forEach(function (k) {
        if (!(k in names)) return;
        var sp = splitEmojiName(names[k]);
        S.note[k] = { e: sp.n ? sp.e : "", n: sp.n || NOTE_DEF[k].n };
      });
      (S.lists || []).slice().forEach(function (l) {
        var k = "list:" + l.id;
        if (!(k in names)) return;
        var sp = splitEmojiName(names[k]);
        if (sp.n) { l.title = sp.n; l.emoji = sp.e; }
      });
    }
    /* 「삭제」를 누른 카테고리는 저장할 때 지워요 (닫으면 그대로) */
    var delInp = document.querySelector("#sheet #noteDelIds");
    var delIds = delInp && delInp.value ? delInp.value.split(",").filter(Boolean) : [];
    if (delIds.length) {
      S.lists = (S.lists || []).filter(function (l) { return delIds.indexOf(l.id) < 0; });
      if (delIds.some(function (id) { return S.ui.seg === "list:" + id; })) S.ui.seg = "todo";
    }
    /* 새 카테고리 — 목록에 붙여 둔 줄이 있으면 그 줄이 기준, 없으면 위 입력칸(예전 방식 그대로) */
    var newInp = document.querySelector('#sheet input[name="title"]');
    var newName = newInp ? String(newInp.value || "").trim() : "";
    if (newName) {
      var sp1 = splitEmojiName(newName);
      var nl = { id: uid(), title: sp1.n || newName, emoji: sp1.e, kind: nkind, items: [] };
      S.lists.push(nl);
      order.push("list:" + nl.id);
      if (!firstNew) firstNew = "list:" + nl.id;
      added = true;
    }
    /* v39: 줄마다 고른 속지를 그 카테고리에 반영 — 기본 카테고리는 S.noteKinds, 내 카테고리는 l.kind.
       기본 카테고리에서 「카드」를 고르면 값을 지워 지금 모양(카드)으로 돌아갑니다. */
    rows.forEach(function (r) {
      var k2 = r.getAttribute("data-key") || "";
      if (!k2 || k2.indexOf("new:") === 0) return;
      var rk = r.getAttribute("data-kind") || "";
      /* v42: 글이 있는 카테고리의 속지는 저장 때도 바꾸지 않아요 (화면에서 이미 막지만 한 번 더) */
      var l0 = k2.indexOf("list:") === 0 ? findList(k2.slice(5)) : null;
      var nowKind = NOTE_BASE.indexOf(k2) >= 0 ? String(S.noteKinds[k2] || "") : (l0 ? listKindOf(l0) : "");
      if (catHasContent(k2) && rk !== nowKind) { rk = nowKind; blockedKind = true; }
      if (NOTE_BASE.indexOf(k2) >= 0) {
        if (LIST_KINDS.indexOf(rk) >= 0) S.noteKinds[k2] = rk; else delete S.noteKinds[k2];
        return;
      }
      if (k2.indexOf("list:") === 0) {
        var l2 = findList(k2.slice(5));
        if (l2 && LIST_KINDS.indexOf(rk) >= 0) l2.kind = rk;
      }
    });
    /* 카테고리 수정으로 열린 시트 — 고른 속지를 그 카테고리에 반영 */
    if (kindTarget) {
      var kt = findList(kindTarget);
      if (kt && kt.kind !== nkind) kt.kind = nkind;
    }
    if (firstNew) S.ui.seg = firstNew;
    S.noteOrder = order;
    noteOrderList();                       /* 없어진 키 정리 · 새로 생긴 리스트는 맨 뒤에 */
    var cur = S.ui.seg || "todo";
    var okCur = NOTE_BASE.indexOf(cur) >= 0 || (cur.indexOf("list:") === 0 && !!findList(cur.slice(5)));
    if (!okCur) S.ui.seg = "todo";
    save(); closeSheet(); renderDiary();
    toast(blockedKind ? kindBlockMsg() : (added ? "카테고리를 만들었어요" : "노트 설정을 저장했어요"));
  }

  function formNoteSettings() {
    var h = sheetHead("노트 설정");
    h += '<p class="sheet-sub">탭 이름과 내 카테고리를 여기서 정리해요.</p>';
    h += '<form class="form" id="noteForm" style="margin-top:12px">';
    h += '<div class="set-lbl">탭 이름</div>';
    NOTE_BASE.forEach(function (k) {
      var t = noteTab(k);
      /* v18: 이모지 칸을 따로 두지 않고 한 칸에 — 「📝 메모」처럼 이모지와 이름을 함께 적어요 */
      h += '<div class="nt-row">' +
        '<input class="field nt-nm" name="t_' + k + '" value="' + esc(t.e ? t.e + " " + t.n : t.n) + '" placeholder="예) 메모" aria-label="탭 이름" autocomplete="off">' +
        "</div>";
    });
    h += '<div class="set-lbl" style="margin-top:20px">내 카테고리</div>';
    if (!S.lists.length) h += '<div class="set-hint" style="margin-top:0">아직 만든 카테고리가 없어요. 아래에서 새로 만들 수 있어요.</div>';
    S.lists.forEach(function (l) {
      h += '<div class="nt-row">' +
        '<input class="field nt-nm" name="l_' + l.id + '" value="' + esc(listLabel(l)) + '" placeholder="예) 여행 준비물" aria-label="카테고리 이름" autocomplete="off">' +
        '<button type="button" class="nt-del" data-act="delListFromNote" data-id="' + l.id + '">삭제</button></div>';
    });
    h += '<div class="nt-new"><div class="set-lbl">새 카테고리</div>' +
      '<div class="nt-row">' +
      '<input class="field nt-nm" name="new_n" placeholder="예) 여행 준비물" aria-label="새 카테고리 이름" autocomplete="off">' +
      '<select class="field nt-kind" name="new_kind" aria-label="새 카테고리 형식">' +
      '<option value="check">투두리스트</option><option value="memo">모눈 메모</option>' +
      '<option value="review">별점 리뷰</option><option value="expense">지출·정산</option></select>' +
      "</div></div>";
    h += '<div style="height:14px"></div><button class="btn-primary" type="submit">저장하기</button></form>';
    h += '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
    return h;
  }

  function openNoteSettings() { openSheet(formNoteSettings()); }

  /* v38: 속지마다 다른 «항목 쓰기» 시트 */
  function formListItem(l, it, opts) {
    var isEdit = !!it;
    var kind = listKindOf(l);
    var delBtn = isEdit ? '<button type="button" class="btn-del" data-act="delListItem" data-list="' + l.id +
      '" data-id="' + it.id + '">삭제</button>' : "";
    var submit = '<button class="btn-primary" type="submit">' + (isEdit ? "저장하기" : "추가하기") + "</button></form>";

    /* v41: 모눈 메모는 이 시트를 쓰지 않아요 — 모눈종이 풀스크린 다이어리(openDiary)로 열립니다 */
    if (kind === "memo") return sheetHead("메모") + '<p class="sheet-sub">모눈 메모는 모눈종이 다이어리에서 써요.</p>';

    if (kind === "review") {
      var r = it ? Math.max(0, Math.min(5, Math.round(Number(it.rating) || 0))) : 0;
      var st = "";
      for (var i = 1; i <= 5; i++) {
        st += '<button type="button" class="fstar' + (i <= r ? " on" : "") + '" data-act="fstar" data-r="' + i +
          '" aria-label="별점 ' + i + '점">' + STAR + "</button>";
      }
      return sheetHead(isEdit ? "리뷰 수정" : "새 리뷰") +
        '<form class="form" id="sheetForm">' +
        '<div class="f"><label>이름</label><input class="field" name="text" value="' + (it ? esc(itTitle(it)) : "") +
        '" placeholder="예) 성수 카페 · 오늘의 커피" autocomplete="off"></div>' +
        '<div class="f"><label>별점</label><div class="fstars" data-group="fstar" data-v="' + r + '">' + st +
        '</div><input type="hidden" name="rating" value="' + r + '"></div>' +
        '<div class="f"><label>어디서</label><input class="field" name="place" value="' + (it ? esc(it.place || "") : "") +
        '" placeholder="예) 성수 · 연무장길" autocomplete="off"></div>' +
        '<div class="f"><label>날짜</label><input class="field fdate" type="date" name="date" value="' +
        (it && it.date ? String(it.date).slice(0, 10) : today) + '"></div>' +
        '<div class="f"><label>한줄평</label><textarea class="field" name="memo" rows="3" placeholder="더 적어 두고 싶은 말">' +
        (it ? esc(itBody(it)) : "") + "</textarea></div>" + delBtn + submit;
    }

    /* v45: 지출·정산은 전용 시트(지출|입금 · 누가 · 금액 · 카테고리 · 날짜 · 메모)로 */
    if (kind === "expense") return formExpItem(l, it, opts);

    return sheetHead(isEdit ? "항목 수정" : "항목 추가") +
      '<form class="form" id="sheetForm">' +
      '<div class="f"><label>항목</label>' +
      '<input class="field" name="text" value="' + (it ? esc(itTitle(it)) : "") + '" placeholder="예) 우산 챙기기" required autocomplete="off">' +
      "</div>" +
      '<div class="f"><label>상세 메모</label><textarea class="field" name="memo" rows="3" placeholder="선택 · 더 자세히 적어 두세요">' + (it ? esc(itBody(it)) : "") + "</textarea></div>" +
      delBtn + submit;
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
    /* v44: 시트 이름은 «프로필 편집» — 맨 아래 묶음은 «기념일» 로만 */
    var h = sheetHead("프로필 편집");

    /* v43: 두 사람 프로필 편집은 시트 맨 위에서 (아래쪽 버튼은 없앰) */
    h += '<div class="two dday-profs">' +
      ['me', 'you'].map(function (w) {
        var pnm = w === "me" ? c.me : c.you;
        return '<button type="button" class="btn-line dday-prof" data-act="personSheet" data-who="' + w + '" data-back="1">' +
          '<span class="pr-av dday-av' + (avPic(w) ? " pic" : "") + '" style="background:' + avColor(w) + '">' + avInner(w) + "</span>" +
          esc(pnm) + " 프로필 편집</button>";
      }).join("") +
      "</div>" +
      /* 1. 「상단 문구」(왼쪽)와 「처음 만난 날」(오른쪽)을 한 줄에 — 문구는 최대 14자까지 다 보이게 */
      '<form class="form" id="sheetForm" style="margin-top:12px">' +
      '<div class="dday-row">' +
      /* v44: 상단 문구 옆에 «몇 자까지 · 남은 글자» 를 붙여, 쓰는 동안 줄어드는 걸 바로 보여 줘요 */
      '<div class="f dday-ph-f"><label>상단 문구 <span class="dday-cnt" id="ddayPhraseCnt">최대 14자 · ' + Math.max(0, 14 - String(ddayPhrase() || "").length) + '</span></label><input class="field" name="phrase" maxlength="14" value="' + esc(ddayPhrase()) + '" placeholder="소영과 준영이 함께한 지" autocomplete="off"></div>' +
      '<div class="f dday-since-f"><label>우리의 시작</label><input class="field" type="date" name="since" value="' + c.since + '" required></div>' +
      "</div>" +
      '<div class="f"><label>D-day 표기</label><div class="seg seg-sm" data-group="fmt">' +
      '<button type="button" class="seg-btn' + (c.fmt === "Y" ? "" : " active") + '" data-act="fmt" data-fmt="D">일수로 · D+365일</button>' +
      '<button type="button" class="seg-btn' + (c.fmt === "Y" ? " active" : "") + '" data-act="fmt" data-fmt="Y">연·일로 · 1년 4일째</button>' +
      '</div><input type="hidden" name="fmt" value="' + (c.fmt === "Y" ? "Y" : "D") + '"></div>' +
      '<p style="font-size:11.5px;color:var(--ink-3);line-height:1.6;margin-top:-2px">이 날을 기준으로 D-day와 기념일을 계산해요.</p>';

    /* 2. 기념일 & 생일 — 주년은 그대로, 두 사람 생일은 달력에서 바로 고쳐요 */
    h += '<div class="mile-hd">기념일</div><div class="mile">';
    var since = parse(c.since);
    for (var n = 1; n <= 3; n++) {
      var ad = new Date(since.getFullYear() + n, since.getMonth(), since.getDate());
      var ads = iso(ad), add = diffDays(today, ads);
      h += mileRow(n + "주년", ads.replace(/-/g, "."), add === 0 ? "오늘" : add > 0 ? "D-" + add : -add + "일 지남", add >= 0 && add <= 30);
    }
    ["me", "you"].forEach(function (w) {
      var nm = w === "me" ? c.me : c.you;
      var nb = nextBirthday(bd[w]);
      h += '<button type="button" class="mile-row mile-btn" data-act="personSheet" data-who="' + w +
        '" data-back="1" aria-label="' + esc(nm) + ' 프로필 편집">' +
        '<span class="mile-n">' + esc(nm) + ' 생일</span>' +
        '<span class="mile-d" data-bdtxt="' + w + '">' + esc(bdayText(bd[w]) || "생일을 넣어 주세요") + "</span>" +
        '<span class="mile-x' + (nb && nb.days <= 30 ? " soon" : "") + '" data-bdleft="' + w + '">' +
        (nb ? (nb.days === 0 ? "오늘" : "D-" + nb.days) : "—") + "</span>" +
        '<span class="mile-go" aria-hidden="true">›</span></button>';
    });
    h += "</div>";
    h += '<button class="btn-primary" type="submit" style="margin-top:14px">저장하기</button></form>';
    return h;
  }

  /* v42: 기념일 &amp; 생일 시트 — 프로필 편집에서 돌아오면 이 시트로 */
  function openDdaySheet() {
    openSheet(formDday(), function (fd) {
      S.couple.phrase = String(fd.get("phrase") || "").trim() || defaultPhrase();
      if (fd.get("since")) S.couple.since = fd.get("since");
      S.couple.fmt = fd.get("fmt") === "Y" ? "Y" : "D";
      save(); closeSheet(); renderAll(); toast("기념일을 저장했어요");
    });
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
      '<p class="sheet-sub">' + (isListSeg(k) ? "이 카테고리 안에 리스트 카드를 하나 더 만들어요. 제목을 적어 주세요."
        : "탭 안에 리스트를 나눠 담을 수 있어요. 제목을 적어 주세요.") + '</p>' +
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

  /* ==========================================================================
     v40: 사진 크게 보기 — 사진만 화면에 꽉 차게
       · 아래 정보·「캡션 바탕색」·삭제 바는 없앴어요
       · 위 좌우 화살표 대신 «옆으로 밀면 넘어가는» 가로 스냅 스크롤
       · 위 왼쪽 ×로 닫고, 오른쪽에 💬 댓글(개수) · ⋯ 메뉴(정보 수정·삭제)만 조용히
     ========================================================================== */
  function pvPhotos() {
    var ids = (photoView && photoView.ids) || [];
    var out = [];
    ids.forEach(function (id) {
      var p = S.photos.filter(function (x) { return x.id === id; })[0];
      if (p) out.push(p);
    });
    return out;
  }
  /* 사진 한 장의 댓글·대댓글 수 */
  function photoCommentCount(p) {
    var n = 0;
    ((p && p.comments) || []).forEach(function (c) { n += 1 + ((c.replies || []).length); });
    return n;
  }
  function cmtTime(at) {
    var d = parse(String(at || "").slice(0, 10));
    var dt = null;
    try { dt = new Date(at); } catch (e) { dt = null; }
    if (!dt || isNaN(dt.getTime())) return "";
    var h = dt.getHours(), m = dt.getMinutes();
    var ap = h < 12 ? "오전" : "오후";
    var hh = h % 12; if (!hh) hh = 12;
    return ap + " " + hh + ":" + pad(m);
  }
  function cmtName(who) { return who === "you" ? String(S.couple.you || "준영") : String(S.couple.me || "나"); }
  function cmtRowHtml(c, isReply, parentId, pid) {
    var who = c.who === "you" ? "you" : "me";
    var mine = who === "me";
    return '<div class="cmt' + (isReply ? " re" : "") + '" data-cid="' + esc(c.id) + '" data-parent="' + esc(parentId) +
      '" data-pid="' + esc(pid || "") + '">' +
      avSpan(who) +
      '<div class="cmt-b">' +
      '<div class="cmt-h"><b>' + esc(cmtName(who)) + "</b><span>" + esc(cmtTime(c.at)) + "</span></div>" +
      (isReply && c.to ? '<div class="cmt-to">@' + esc(c.to) + "</div>" : "") +
      '<div class="cmt-t">' + esc(c.text || "") + "</div>" +
      '<div class="cmt-acts">' +
      '<button type="button" data-act="cmtReply" data-id="' + esc(parentId) + '" data-who="' + esc(who) + '" data-name="' + esc(cmtName(who)) + '">답글</button>' +
      (mine ? '<button type="button" data-act="cmtDel" data-id="' + esc(c.id) + '" data-parent="' + esc(parentId) + '">삭제</button>' : "") +
      "</div></div></div>";
  }
  function cmtListHtml(p) {
    var cs = (p && p.comments) || [];
    var h = '<div class="cmt-list">';
    if (!cs.length) h += '<div class="cmt-empty">아직 댓글이 없어요. 첫 댓글을 남겨 보세요.</div>';
    cs.forEach(function (c) {
      h += cmtRowHtml(c, false, c.id);
      (c.replies || []).forEach(function (r) { h += cmtRowHtml(r, true, c.id); });
    });
    h += "</div>";
    return h;
  }
  /* v45: 댓글 칸은 «한 줄짜리 입력칸» 대신 스스로 늘어나는 textarea —
     길게 쓰면 가로로 흐르지 않고 화면 폭에 맞춰 아래로 내려가요 (최대 120px, 그 뒤 스크롤).
     Enter 로 등록, Shift+Enter 로 줄바꿈. 등록하면 1줄로 다시 돌아갑니다. */
  var CMT_MAX_H = 120;
  function cmtGrow(el) {
    if (!el || el.tagName !== "TEXTAREA") return;
    el.style.height = "auto";
    var h = Math.min(CMT_MAX_H, Math.max(38, el.scrollHeight));
    el.style.height = h + "px";
    el.style.overflowY = el.scrollHeight > CMT_MAX_H ? "auto" : "hidden";
  }
  function cmtFormHtml(p, day) {
    return '<form class="cmt-form" data-id="' + esc(p ? p.id : "") + '" data-day="' + esc(day || "") + '">' +
      '<input type="hidden" name="re" value="">' +
      '<input type="hidden" name="repid" value="">' +
      avSpan("me") +
      '<textarea class="cmt-in" name="text" rows="1" placeholder="댓글 달기" autocomplete="off" ' +
      'enterkeyhint="send" aria-label="댓글"></textarea>' +
      '<button class="cmt-send" type="submit">등록</button></form>';
  }

  /* v40: 사진만 보이는 풀스크린 크게 보기 — 위아래 어떤 글씨·버튼도 없이 사진만.
     · 옆으로 밀면 같은 날의 이전·다음 사진 (가로 스냅 스크롤)
     · 사진을 한 번 탭하거나 아래로 쓸어내리면 이전 화면(모아보기)으로 닫혀요 */
  function photoViewBody() {
    var ps = pvPhotos();
    var i = photoView ? photoView.i : 0;
    if (i < 0) i = 0;
    if (i > ps.length - 1) i = Math.max(0, ps.length - 1);
    if (photoView) photoView.i = i;
    var p = ps[i];
    if (!p) {
      return '<div class="sheet-hd"><h2>사진</h2><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>" +
        '<p class="sheet-sub">사진을 찾을 수 없어요.</p>';
    }
    return '<div class="pview pv40" data-pv="1">' +
      '<div class="pv40-strip" data-pv="1">' +
      ps.map(function (x) {
        return '<div class="pv40-slide" data-id="' + esc(x.id) + '">' + photoImg(x, true) + "</div>";
      }).join("") +
      "</div></div>";
  }

  /* 옆으로 넘기면 지금 보고 있는 사진만 조용히 따라가요 (화면에는 아무것도 안 보여요) */
  function pvSyncIndex() {
    if (!photoView) return;
    var strip = document.querySelector("#sheet .pv40-strip");
    if (!strip) return;
    var w = strip.clientWidth || 1;
    var idx = Math.round(strip.scrollLeft / w);
    photoView.i = Math.max(0, Math.min(photoView.ids.length - 1, idx));
  }
  document.addEventListener("scroll", function (ev) {
    var el = ev.target;
    if (!el || !el.classList || !el.classList.contains("pv40-strip")) return;
    pvSyncIndex();
  }, true);

  /* 사진을 한 번 탭하거나, 아래로 쓸어내리면 닫기 */
  var pvTap = null;
  document.addEventListener("pointerdown", function (ev) {
    var el = ev.target && ev.target.closest ? ev.target.closest("#sheet .pv40-strip") : null;
    if (!el) { pvTap = null; return; }
    pvTap = { x: ev.clientX, y: ev.clientY, t: Date.now() };
  }, true);
  document.addEventListener("pointermove", function (ev) {
    if (!pvTap) return;
    var dy = ev.clientY - pvTap.y, dx = ev.clientX - pvTap.x;
    if (dy > 90 && Math.abs(dy) > Math.abs(dx) * 1.3) {
      pvTap = null;
      closeSheet();
    }
  }, true);
  document.addEventListener("pointerup", function (ev) {
    var st = pvTap;
    pvTap = null;
    if (!st) return;
    var dx = Math.abs(ev.clientX - st.x), dy = Math.abs(ev.clientY - st.y);
    if (dx < 9 && dy < 9 && Date.now() - st.t < 420) closeSheet();
  }, true);

  function photoShow(id) {
    var p = S.photos.filter(function (x) { return x.id === id; })[0];
    if (!p) return false;
    var ids = photoDayIds(p);
    var i = ids.indexOf(p.id);
    photoView = { ids: ids, i: i < 0 ? 0 : i };
    return true;
  }

  /* v40: 사진 사이는 «옆으로 밀어서» 넘어가요 — 화살표 버튼 대신 스냅 스크롤 */
  function pvScrollTo(idx, smooth) {
    var strip = document.querySelector("#sheet .pv40-strip");
    if (!strip) return;
    var w = strip.clientWidth || 1;
    var left = Math.max(0, Math.min(strip.scrollWidth - w, idx * w));
    try { strip.scrollTo({ left: left, behavior: smooth ? "smooth" : "auto" }); }
    catch (e) { strip.scrollLeft = left; }
  }
  function photoStep(step) {
    if (!photoView) return;
    var n = photoView.i + step;
    if (n < 0 || n >= photoView.ids.length) return;
    photoView.i = n;
    pvScrollTo(n, true);
  }

  function openPhoto(id) {
    if (!photoShow(id)) return;
    openSheet(photoViewBody(), null, { full: true });
    /* 처음 볼 사진이 바로 보이게 스트립을 그 자리로 */
    var i0 = photoView ? photoView.i : 0;
    pvScrollTo(i0, false);
    requestAnimationFrame(function () { pvScrollTo(i0, false); });
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

  /* v38: 사진 추가 시트 — 앨범 칸 없이 «날짜 → 캡션 → 고른 사진 목록».
     목록 위 「추가」로 사진을 더 담고, 줄마다 「삭제」로 빼며, 장 수·용량 요약과 「N장 담기」가 바로 따라갑니다. */
  function upTotal() {
    var t = 0;
    pendingFiles.forEach(function (f) { t += f.size || 0; });
    return t;
  }
  /* v41: 사진은 한 줄에 6개씩 들어가는 정사각 네모 칸으로 — 칸 오른쪽 위 × 로 빼고,
     칸을 끌어다 놓으면(또는 ←→↑↓) 순서가 바뀌어요 */
  function photoUpRowsHtml() {
    if (!pendingFiles.length) return '<div class="up-empty">고른 사진이 없어요. 「추가」로 담아 보세요.</div>';
    return pendingFiles.map(function (f, i) {
      var url = "";
      try { url = URL.createObjectURL(f); pendingUrls.push(url); } catch (e) {}
      return '<div class="up-cell" data-i="' + i + '" tabindex="0" role="button" aria-label="' + esc(f.name || "사진") + '">' +
        (url ? '<img class="up-thumb" src="' + url + '" alt="" draggable="false">' : '<span class="up-thumb"></span>') +
        '<button type="button" class="up-x" data-act="upDel" data-i="' + i + '" aria-label="이 사진 빼기">' + IC.x + "</button></div>";
    }).join("");
  }
  /* 목록·담기 버튼의 장 수를 지금 상태에 맞춰 다시 칩니다 */
  function refreshAddPhoto() {
    var list = document.querySelector("#sheet #upList");
    if (list) list.innerHTML = photoUpRowsHtml();
    var cnt = document.querySelector("#sheet #upCount");
    if (cnt) cnt.textContent = String(pendingFiles.length);
    var btn = document.querySelector("#sheet #upBtn");
    if (btn) btn.textContent = pendingFiles.length + "장 담기";
  }

  function formAddPhoto(files, dateVal) {
    upMode = "pending";            /* v40: 새로 담는 사진 순서 모드 */
    dayEdit = null;
    pendingFiles = files || [];
    var dv = dateVal || pendingPhotoDate || today;
    return sheetHead("사진 추가") +
      '<form class="form" id="sheetForm" data-form="photo">' +
      /* v45: «사진 추가» 아래 요약 줄(장수·용량·줄이는 말)은 지웠어요.
         「기록 이름」 먼저, 「날짜」는 그 아래 줄 — 한 줄에 붙이지 않고 각자 밑줄 한 줄을 씁니다.
         기록 이름은 늘 빈 칸에서 시작(예전에 올린 이름이 따라 올라오지 않게),
         한 시트에서 「+ 추가」로 더 담을 때는 적어 둔 값이 그대로 남아요. */
      '<div class="up-row up-stack">' +
      '<div class="f up-nm-f"><label>기록 이름</label><input class="field" name="album_tag" value=""' +
      ' placeholder="예) 경주여행" autocomplete="off"></div>' +
      '<div class="f up-date-f"><label>날짜</label><input class="field up-date" type="date" name="date" value="' +
      dv + '" required></div></div>' +
      /* v40: 「캡션」 칸은 없앴어요 — 날짜·태그·고른 사진만 남깁니다 */
      '<div class="up-hd"><span class="up-hd-t"><i class="up-hd-lb">사진</i><span class="up-hd-c"><b id="upCount">' +
      pendingFiles.length + "</b>장</span></span>" +
      '<button type="button" class="up-add" data-act="upAdd">' + IC.plus + " 추가</button></div>" +
      '<p class="up-guide">사진을 눌러 끌어 옮기면 순서를 바꿀 수 있어요.</p>' +
      '<div class="up-grid" id="upList">' + photoUpRowsHtml() + "</div>" +
      '<div class="up-bar" id="upBar"><i></i></div>' +
      '<button class="btn-primary" id="upBtn" type="submit">' + pendingFiles.length + "장 담기</button></form>" +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">취소</button>';
  }

  /* ==========================================================================
     v40: 날짜 사진 편집 시트 — 모아보기 오른쪽 위 «수정» 아이콘에서 열려요.
     그날 이미 올라간 사진이 목록에 들어 있어
       · 날짜·태그 수정 · ≡ 로 사진 순서 바꾸기 · 사진 빼기 · + 추가
     를 한 화면에서 하고 저장해요. (캡션 칸은 없앴어요)
     ========================================================================== */
  var dayEdit = null;
  var dayAddMore = false;

  function dayEditRows() {
    if (!dayEdit || !dayEdit.items.length) return '<div class="up-empty">이 날짜에 사진이 없어요. 「추가」로 담아 보세요.</div>';
    return dayEdit.items.map(function (it, i) {
      var p = it.pid ? S.photos.filter(function (x) { return x.id === it.pid; })[0] : null;
      var inner = p ? photoImg(p) : (it.url ? '<img src="' + esc(it.url) + '" alt="" draggable="false">' : "");
      var name = p ? (p.album || "사진") : (it && it.file ? (it.file.name || "사진") : "사진");
      return '<div class="up-cell" data-i="' + i + '"' + (p ? ' data-pid="' + esc(p.id) + '"' : "") +
        ' tabindex="0" role="button" aria-label="' + esc(name) + '">' +
        '<span class="up-thumb">' + inner + "</span>" +
        '<button type="button" class="up-x" data-act="upDel" data-i="' + i + '" aria-label="이 사진 빼기">' + IC.x + "</button></div>";
    }).join("");
  }
  function refreshDayEdit() {
    var list = document.querySelector("#sheet #upList");
    if (list) list.innerHTML = dayEditRows();
    var cnt = document.querySelector("#sheet #upCount");
    if (cnt) cnt.textContent = String(dayEdit ? dayEdit.items.length : 0);
  }
  function formEditPhotoDay(day) {
    var ids = photoDayItems(day).map(function (p) { return p.id; });
    dayEdit = { day: day, items: ids.map(function (id) { return { pid: id }; }), origIds: ids.slice() };
    upMode = "day";
    return sheetHead("사진 수정") +
      '<form class="form" id="sheetForm" data-form="photoDay">' +
      /* v45: 사진 추가와 같은 차례 — 「기록 이름」 먼저, 「날짜」는 아래 줄 (각자 밑줄 한 줄) */
      '<div class="up-row up-stack">' +
      '<div class="f up-nm-f"><label>기록 이름</label><input class="field" name="album_tag" value="' + esc(dateTagOf(day)) +
      '" placeholder="예) 경주여행" autocomplete="off"></div>' +
      '<div class="f up-date-f"><label>날짜</label><input class="field up-date" type="date" name="date" value="' + day + '" required></div></div>' +
      '<div class="up-hd"><span class="up-hd-t"><i class="up-hd-lb">사진</i><span class="up-hd-c"><b id="upCount">' +
      dayEdit.items.length + "</b>장</span></span>" +
      '<button type="button" class="up-add" data-act="upAdd">' + IC.plus + " 추가</button></div>" +
      '<p class="up-guide">사진을 눌러 끌어 옮기면 순서를 바꿀 수 있어요.</p>' +
      '<div class="up-grid" id="upList">' + dayEditRows() + "</div>" +
      '<button class="btn-primary" type="submit">저장하기</button></form>' +
      '<div style="height:10px"></div><button class="btn-line" data-close="1">닫기</button>';
  }
  /* 날짜·태그·순서·삭제·추가를 한 번에 저장 */
  function saveDayEdit(fd) {
    if (!dayEdit) { closeSheet(); return; }
    var day = String(fd.get("date") || dayEdit.day).slice(0, 10);
    if (!/^\d{4}-\d{2}-\d{2}$/.test(day)) day = dayEdit.day;
    var tag = String(fd.get("album_tag") || "").trim();
    var albumName = tag || defaultAlbum();
    var seq = dayEdit.items.slice();
    var keep = seq.filter(function (x) { return x.pid; }).map(function (x) { return x.pid; });
    (dayEdit.origIds || []).forEach(function (id) {
      if (keep.indexOf(id) >= 0) return;
      var gone = S.photos.filter(function (x) { return x.id === id; })[0];
      S.photos = S.photos.filter(function (x) { return x.id !== id; });
      delete PHOTO_URLS[id];
      if (gone) { try { Store.photos.remove(gone).catch(function () {}); } catch (e) {} }
    });
    seq.forEach(function (it) {
      if (!it.pid) return;
      var p = S.photos.filter(function (x) { return x.id === it.pid; })[0];
      if (!p) return;
      p.date = day;
      p.album = albumName;
      if (typeof p.title !== "string") p.title = "";
    });
    var chain = Promise.resolve();
    seq.forEach(function (it) {
      if (it.pid || !it.file) return;
      chain = chain.then(function () {
        return Store.photos.add(it.file, { album: albumName, date: day, title: "" }).then(function (res) {
          var rec = res.photo;
          rec.title = "";
          if (res.url) PHOTO_URLS[rec.id] = res.url;
          S.photos.push(rec);
          it.newId = rec.id;
        }).catch(function () {});
      });
    });
    return chain.then(function () {
      /* 그날 사진만 보이는 순서대로 다시 세워요 */
      var order = seq.map(function (it) { return it.pid || it.newId; }).filter(Boolean);
      var daySet = {};
      S.photos.forEach(function (p) { if (String(p.date || "").slice(0, 10) === day) daySet[p.id] = p; });
      var ordered = [];
      order.forEach(function (id) { if (daySet[id]) { ordered.push(daySet[id]); delete daySet[id]; } });
      Object.keys(daySet).forEach(function (id) { ordered.push(daySet[id]); });
      var firstIdx = -1, rest = [];
      S.photos.forEach(function (p, i) {
        if (String(p.date || "").slice(0, 10) === day) { if (firstIdx < 0) firstIdx = i; return; }
        rest.push(p);
      });
      if (firstIdx < 0) firstIdx = 0;
      S.photos = rest.slice(0, firstIdx).concat(ordered, rest.slice(firstIdx));
      upMode = "pending";
      dayEdit = null;
      save(); closeSheet(); renderPhoto(); toast("사진을 저장했어요");
    });
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
          /* v40: 고른 순서 그대로 — 시트 맨 위(1번째) 사진이 사진첩에서도 맨 앞(대표) */
          S.photos.splice(done, 0, rec);
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
      /* v40: 「캡션」 칸은 없앴어요 (사진 아래 캡션 줄도 함께 사라짐) */
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
  var personBack = false;   /* v42: 기념일 & 생일 시트에서 연 프로필이면 그 시트로 돌아와요 */
  /* ==========================================================================
     v27: 프로필 사진 — 카카오톡 프사처럼 동그라미 가이드 안에서 옮기고 키워 자르기
     · 어두운 화면 가운데 밝은 동그라미 안에서 한 손가락으로 옮기고,
       두 손가락을 벌리거나 오므려 확대·축소 (v45: 슬라이더 없이 손으로만)
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
      '<div class="avcrop-hint">두 손가락으로 벌려 확대 · 오므려 축소 · 한 손가락으로 옮기기</div>' +
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
        /* 두 손가락 사이를 잡은 점이 그대로 있도록 — 그 점을 중심으로 확대·축소 (v45) */
        var z0 = avCrop.zoom;
        var z1 = Math.min(3, Math.max(1, z0 * (dist / last.dist)));
        if (z1 !== z0) {
          var rct = stage.getBoundingClientRect();
          var relx = mx - rct.left - avCrop.box / 2;
          var rely = my - rct.top - avCrop.box / 2;
          var k = z1 / z0;
          avCrop.tx = relx - k * (relx - avCrop.tx);
          avCrop.ty = rely - k * (rely - avCrop.ty);
          avCrop.zoom = z1;
        }
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
      '<input class="field" id="personName" name="name" value="' + esc(nm) + '" placeholder="닉네임" required autocomplete="off">' +
      /* v43: 상대 프로필은 상대가 직접 — 닉네임 아래에 안내 한 줄 */
      (isMe ? "" : '<p class="sheet-sub pr-note">프로필은 상대방이 직접 설정할 수 있어요.</p>') +
      "</div>" +
      "</div>" +
      /* v45: 생일은 예전처럼 «한 번에» — 날짜 입력칸 하나 (v44 의 세 칸 고르기는 걷어냄) */
      '<div class="f" style="margin-top:16px"><label for="personBday">생일</label>' +
      '<input class="field pr-bday" id="personBday" type="date" name="bday" min="1900-01-01" max="' + today +
      '" value="' + esc(prBdayValue(who)) + '"></div>' +
      '<p class="sheet-sub pr-bday-txt" id="prBdayTxt">' +
      (prBdayValue(who) ? bdayFullText(prBdayValue(who)) + " · " : "") +
      "생일을 골라 주세요. 홈 D-day 에는 월·일로 보여요.</p>" +
      (canPic ? "" : '<div class="set-hint" style="margin-top:10px;padding:0">프로필 사진은 ' + esc(nm) + " 본인 폰에서 바꿀 수 있어요.</div>") +
      '<button class="btn-primary" type="submit" style="margin-top:18px">저장</button></form>' +
      /* v43: 컬러 동그라미 한 줄 — 고르면 프로필 사진 대신 그 컬러로 */
      '<div class="pr-color"><span class="set-lbl">컬러</span>' + prColorRow(who) +
      '<p class="sheet-sub pr-color-hint">컬러를 고르면 프로필 사진 대신 동그라미 색으로 보여요.</p></div>';
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
  function openPersonSheet(who, back) {
    /* v42: 기념일 시트에서 들어왔으면 저장·닫을 때 그 시트로 돌아가요 */
    var keep = personBack;
    openSheet(formPerson(who));
    personSheetWho = who;
    personBack = back === undefined ? keep : !!back;
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
    /* v35: 이 설정들은 이 폰에만 저장된다는 한 줄 안내 */
    h += '<p class="cp-note" style="margin:14px 0 0;text-align:center">화면 모드·색·폰트는 내 폰에만 저장돼요</p>';
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
    /* v35: 모드·색·폰트는 각자 폰에만 */
    h += '<div class="set-hint" style="margin:10px 20px 0">화면 모드·컬러·폰트는 이 폰에만 저장돼요. 내가 바꿔도 상대 폰 화면은 그대로예요.</div>';

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
    /* v34: 노트 탭으로 들어올 때는 늘 「메모」부터 — 다른 탭에서 고른 노트 탭은
       노트 화면에 머무는 동안만 유지돼요 (v28 캘린더와 같은 방식). */
    if (name === "diary" && current !== "diary" && !(opts && opts.keepSeg)) S.ui.seg = "todo";
    /* v37: 사진첩으로 들어올 때는 늘 기본 사진 화면부터 — 달력 보기는 달력 아이콘을
       눌렀을 때만 열리고, 다른 탭에 갔다 오거나 앱을 다시 켜면 다시 목록으로 돌아와요. */
    if (name === "photo" && current !== "photo") {
      S.ui.photoCal = false; photoDayView = null;
      photoToBottom = true;          /* v39: 목록은 가장 최근 날짜(맨 아래)부터 보이게 */
    }
    current = name;
    showScreen(name);
    $("#screens").scrollTop = 0;
    renderAll();
  }

  /* ------------------------------------------------------------------ actions */
  document.addEventListener("click", function (ev) {
    var closeEl = ev.target.closest("[data-close]");
    if (closeEl) {
      /* v44: 모눈 다이어리 — «저장» 단추 없이, 나갈 때(‹ 뒤로) 자동 저장해요.
         아무것도 안 쓴 새 다이어리는 빈 항목을 남기지 않아요 */
      if (diary && document.getElementById("d41Paper")) d41AutoSave();
      /* v42: 기념일 시트에서 연 프로필 편집을 닫으면 그 시트로 */
      if (personBack && personSheetWho) { personBack = false; openDdaySheet(); return; }
      closeSheet(); return;
    }

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
      go(el.getAttribute("data-screen") || "diary", { keepSeg: true });
      return;
    }

    if (act === "editDday") { openDdaySheet(); return; }

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

    /* v45: 지출·정산 — 달 넘기기 · 내역/달력 · 날짜 고르기 · 예산 · 시트 안 고르기 */
    if (act === "expPrev" || act === "expNext") {
      expShiftMonth(el.getAttribute("data-list"), act === "expNext" ? 1 : -1);
      return;
    }
    if (act === "expView") {
      EXP_VIEW[el.getAttribute("data-list")] = el.getAttribute("data-v") === "cal" ? "cal" : "list";
      renderDiary();
      return;
    }
    if (act === "expDay") {
      EXP_DAY[el.getAttribute("data-list")] = el.getAttribute("data-day");
      renderDiary();
      return;
    }
    if (act === "expAdd") {
      openExpSheet(containerOf(el.getAttribute("data-list")), null, el.getAttribute("data-tx"));
      return;
    }
    if (act === "expBudget") { openExpBudget(containerOf(el.getAttribute("data-list"))); return; }
    if (act === "expBudgetOff") {
      var bcid = el.getAttribute("data-list");
      expSetBudget(bcid, expMon(bcid), 0);
      save(); closeSheet(); renderDiary(); toast("예산을 지웠어요");
      return;
    }
    if (act === "expTx") {
      var xtx = el.getAttribute("data-tx") === "deposit" ? "deposit" : "expense";
      var xseg = el.closest(".exp-seg");
      if (xseg) xseg.querySelectorAll("button").forEach(function (b) { b.classList.toggle("on", b === el); });
      var xform = sheet.querySelector("#sheetForm");
      if (xform) xform.setAttribute("data-tx", xtx);
      var xtin = sheet.querySelector('#sheetForm input[name="txType"]');
      if (xtin) xtin.value = xtx;
      var xcats = sheet.querySelector(".exp-cats");
      if (xcats) xcats.hidden = xtx === "deposit";
      var xmemo = sheet.querySelector('#sheetForm input[name="memo"]');
      if (xmemo) xmemo.setAttribute("placeholder", xtx === "deposit" ? "예: 11월 월급" : "예: 장보기");
      return;
    }
    if (act === "expWho") {
      var xgrp = el.closest(".exp-whos");
      if (xgrp) xgrp.querySelectorAll(".exp-who").forEach(function (b) { b.classList.toggle("on", b === el); });
      var xwin = sheet.querySelector('#sheetForm input[name="who"]');
      if (xwin) xwin.value = el.getAttribute("data-who") || "both";
      return;
    }
    if (act === "expCat") {
      var xgrid = document.getElementById("expCatGrid");
      if (xgrid) xgrid.querySelectorAll(".exp-cat").forEach(function (b) { b.classList.remove("on"); });
      el.classList.add("on");
      var xcin = sheet.querySelector('#sheetForm input[name="cat"]');
      if (xcin) xcin.value = el.getAttribute("data-cat") || "";
      var xnw = document.getElementById("expCatNew");
      if (xnw) xnw.hidden = true;
      return;
    }
    if (act === "expCatNew") {
      var xnw2 = document.getElementById("expCatNew");
      if (!xnw2) return;
      xnw2.hidden = false;
      var xni = document.getElementById("expCatIn");
      if (xni) { try { xni.focus(); } catch (e) {} }
      return;
    }
    if (act === "expCatAdd") {
      var xni2 = document.getElementById("expCatIn");
      var xval = xni2 ? String(xni2.value || "").trim().slice(0, 10) : "";
      if (!xval) { if (xni2) xni2.focus(); return; }
      var xcin2 = sheet.querySelector('#sheetForm input[name="cat"]');
      if (xcin2) xcin2.value = xval;
      var xgrid2 = document.getElementById("expCatGrid");
      if (xgrid2) {
        xgrid2.querySelectorAll(".exp-cat").forEach(function (b) { b.classList.remove("on"); });
        var xmore = xgrid2.querySelector(".exp-cat-more");
        var xtile = document.createElement("button");
        xtile.type = "button";
        xtile.className = "exp-cat on";
        xtile.setAttribute("data-act", "expCat");
        xtile.setAttribute("data-cat", xval);
        xtile.innerHTML = '<span class="ic">' + expIconSvg(xval, "expense") + '</span><span class="nm">' + esc(xval) + "</span>";
        if (xmore) xgrid2.insertBefore(xtile, xmore); else xgrid2.appendChild(xtile);
      }
      var xnw3 = document.getElementById("expCatNew");
      if (xnw3) xnw3.hidden = true;
      return;
    }

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
      /* v34: + 시트 하나에서 새 카테고리 추가 · 탭 이름 수정 · 순서 바꾸기를 모두 해요 */
      openSheet(formNewList(), function () { saveNoteSheet(); });
      return;
    }

    if (act === "nordAdd") { nordAddTemp(); return; }

    if (act === "nordDel") {
      /* 줄을 지우면 화면에서만 빼 두고, 저장할 때 S.lists 에서 지웁니다 */
      var nRow = el.closest(".nord-row");
      var nId = el.getAttribute("data-id") || "";
      if (nRow && nRow.parentNode) nRow.parentNode.removeChild(nRow);
      var nDelInp = document.querySelector("#sheet #noteDelIds");
      if (nDelInp && nId) nDelInp.value = nDelInp.value ? nDelInp.value + "," + nId : nId;
      if (document.getElementById("nkPanel")) nkSelectRow(null);   /* v40: 지운 줄의 패널은 접어요 */
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

    /* v39: + 시트의 속지 레이아웃 — 고른 카테고리 줄이 있으면 그 줄의 속지를 바꾸고,
       줄을 고르지 않았으면 새 카테고리의 속지를 바꿔요. 「카드」(data-kind="")는 기본 카테고리만. */
    if (act === "nkind") {
      var nk = el.getAttribute("data-kind") || "";
      if (!el.closest('[data-group="nkind"]')) return;
      var nrow = document.querySelector("#sheet #noteOrderList .nord-row.active");
      if (nrow) {
        var nKey = nrow.getAttribute("data-key") || "";
        if (nk === "" && NOTE_BASE.indexOf(nKey) < 0) return;
        /* v42: 글이 있는 카테고리는 다른 속지로 못 바꿔요 — 고른 속지는 그대로 두고 안내만 */
        if ((nrow.getAttribute("data-kind") || "") !== nk && catHasContent(nKey)) { kindBlocked(nrow); return; }
        nrow.setAttribute("data-kind", nk);
      } else if (!nk) {
        return;                       /* 새 카테고리는 「카드」가 없어요 */
      } else {
        /* 아직 줄을 고르지 않았을 때 — 새 카테고리의 기본 속지로 기억해 둬요 */
        var ninN = document.querySelector('#sheet input[name="nkind"]');
        if (ninN) ninN.value = nk;
      }
      nkPaint();                      /* 패널은 고른 속지에 체크를 다시 그리고, hidden nkind 도 맞춰요 */
      return;
    }

    /* v39: 기본 카테고리 속지 화면의 「카드」 — 속지를 걷고 지금 모양(카드)으로 되돌리기 */
    if (act === "baseKindClear") {
      var bkT = el.getAttribute("data-tab") || "";
      if (NOTE_BASE.indexOf(bkT) >= 0) {
        if (catHasContent(bkT)) { kindBlocked(null); return; }
        delete S.noteKinds[bkT];
        save(); renderDiary(); toast("카드로 돌아왔어요");
      }
      return;
    }

    /* v40: 모눈 메모 시트의 사진 한 장 — 고르기/빼기 */
    /* v41: 모눈 메모 — 모눈종이 풀스크린 다이어리 */
    if (act === "openDiary") {
      openDiary(el.getAttribute("data-list"), el.getAttribute("data-id"));
      return;
    }
    if (act === "d41Text") { d41TextTool(); return; }
    if (act === "d41Pen") { d41PanelOpen("pen"); return; }
    if (act === "d41Img") {
      var d41In = document.getElementById("d41ImgIn");
      if (d41In) d41In.click();
      return;
    }
    if (act === "d41Size") { d41SetSize(Number(el.getAttribute("data-size")) || 16.5); return; }
    if (act === "d41SizeStep") { d41SizeStep(Number(el.getAttribute("data-d")) || 0); return; }
    if (act === "d41Color") { d41SetColor(el.getAttribute("data-color") || ""); return; }
    if (act === "d41ColorPick") { d41SpOpen("text"); return; }
    if (act === "d41SpClose") { d41SpClose(); return; }
    if (act === "d41Bold") { d41SetTFlag("bold"); return; }
    if (act === "d41Strike") { d41SetTFlag("strike"); return; }
    if (act === "d41Underline") { d41SetTFlag("underline"); return; }
    if (act === "d41Align") { d41CycleAlign(); return; }
    if (act === "d41TxDel") {
      d41DelText(String(el.getAttribute("data-tx") || ""));
      return;
    }
    if (act === "d41ImgDel") {
      d41DelImg(String(el.getAttribute("data-img") || ""));
      return;
    }
    /* v43: 고른 글 상자에 입력(키보드) / 키보드 내리기 */
    if (act === "d41Edit") {
      var d41Eid = String(el.getAttribute("data-tx") || "");
      if (d41Eid) d41FocusText(d41Eid);
      return;
    }
    if (act === "d41Blur") { d41BlurAll(); return; }
    if (act === "d41ImgCrop") {
      var d41Cid2 = el.getAttribute("data-img") || (d41SelImg() || {}).id || "";
      d41OpenCrop(d41Cid2);
      return;
    }
    if (act === "d41PenMode") {
      if (!diary) return;
      var m44 = el.getAttribute("data-mode");
      diary.pmode = (m44 === "erase" || m44 === "hl") ? m44 : "pen";
      /* v45: 가는 펜(2) · 일반 펜(4.5) — 한 단추가 굵기까지 함께 골라요 */
      var w45 = el.getAttribute("data-w");
      if (w45) diary.pw = Number(w45) || diary.pw;
      d41PanelRefresh();
      return;
    }
    if (act === "d41PenColorPick") {
      d41SpOpen("pen");
      return;
    }
    if (act === "d41PenColor") {
      if (!diary) return;
      diary.pcolor = el.getAttribute("data-color") || "#111111";
      diary.pcpick = false;
      d41SpShut();
      d41PanelRefresh();
      return;
    }
    if (act === "d41PenW") {
      if (!diary) return;
      diary.pw = Number(el.getAttribute("data-w")) || 3.5;
      d41PanelRefresh();
      return;
    }
    if (act === "d41Undo") { d41HistGo(-1); return; }
    if (act === "d41Redo") { d41HistGo(1); return; }
    if (act === "d41PenDel") {
      var selP = d41SelPen();
      if (selP) d41DelPen(selP.id);
      return;
    }
    if (act === "d41Clear") {
      if (!diary) return;
      diary.pen = [];
      d41Paint();
      d41Sync();
      d41HistPush();
      d41AutoSave();
      return;
    }

    /* v38: 리뷰 시트의 별점 — 누른 별까지 채워지고 hidden rating 이 따라가요 */
    if (act === "fstar") {
      var fv = Number(el.getAttribute("data-r")) || 0;
      var fgrp = el.closest('[data-group="fstar"]');
      if (!fgrp) return;
      fgrp.setAttribute("data-v", String(fv));
      Array.prototype.forEach.call(fgrp.querySelectorAll(".fstar"), function (b, i) {
        b.classList.toggle("on", i < fv);
      });
      var frin = fgrp.parentNode.querySelector('input[name="rating"]');
      if (frin) frin.value = String(fv);
      return;
    }

    /* v38: 리뷰 목록에서 별을 눌러 점수 바로 매기기 */
    if (act === "rateReview") {
      var rvl = containerOf(el.getAttribute("data-list"));
      var rvid = el.getAttribute("data-id");
      var rvv = Number(el.getAttribute("data-r")) || 0;
      if (!rvl) return;
      rvl.items.forEach(function (x) { if (x.id === rvid) x.rating = rvv; });
      save(); renderDiary();
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
      var tl = containerOf(el.getAttribute("data-list"));
      var ti = el.getAttribute("data-id");
      var ltBefore = rowTops("#s-diary .dbody");
      if (tl) tl.items.forEach(function (it) { if (it.id === ti) it.done = !it.done; });
      save(); renderDiary(); rowMoveAnim("#s-diary .dbody", ltBefore); return;
    }

    if (act === "delListItem") {
      if (dropDraftItem(el.getAttribute("data-id"))) return;
      var dl = containerOf(el.getAttribute("data-list"));
      var di = el.getAttribute("data-id");
      if (dl) {
        if (isBaseContainer(dl)) S[GROUP_ARR[dl.base]] = dl.items.filter(function (it) { return it.id !== di; });
        else dl.items = dl.items.filter(function (it) { return it.id !== di; });
      }
      save();
      /* v40: 카드 시트 안에서 지울 때는 시트를 닫지 않고 목록만 새로 그려요 */
      if (inCardSheet(el)) { renderDiary(); toast("지웠어요"); return; }
      closeSheet(); renderDiary(); return;
    }

    if (act === "editListItem") {
      var elCid = el.getAttribute("data-list"), elId = el.getAttribute("data-id");
      var elL = containerOf(elCid);
      var elIt = elL ? elL.items.filter(function (x) { return x.id === elId; })[0] : null;
      if (!elL || !elIt) return;
      var edKind = listKindOf(elL);
      /* v41: 모눈 메모는 시트 대신 모눈종이 풀스크린 다이어리로 열어요 */
      if (edKind === "memo") { openDiary(elCid, elId); return; }
      /* v45: 지출·정산은 전용 시트 */
      if (edKind === "expense") { openExpSheet(elL, elIt); return; }
      openSheet(formListItem(elL, elIt), function (fd) {
        var L2 = containerOf(elCid);
        var I2 = L2 ? L2.items.filter(function (x) { return x.id === elId; })[0] : null;
        if (!I2) return;
        var txt = String(fd.get("text") || "").trim();
        if (edKind === "memo") {
          var mbody = String(fd.get("memo") || "").trim();
          if (!txt && !mbody) { toast("제목이나 본문을 적어 주세요"); return; }
          setItTitle(I2, txt);
          setItBody(I2, mbody);
          /* v40: 모눈 메모의 사진 한 장 — 비우면 지워요 */
          var mimg2 = String(fd.get("img") || "");
          if (mimg2) I2.img = mimg2; else delete I2.img;
        } else if (edKind === "review") {
          if (!txt) { toast("이름을 적어 주세요"); return; }
          setItTitle(I2, txt);
          I2.rating = Math.max(0, Math.min(5, Math.round(Number(fd.get("rating")) || 0)));
          I2.place = String(fd.get("place") || "").trim();
          I2.date = String(fd.get("date") || "").slice(0, 10) || today;
          setItBody(I2, String(fd.get("memo") || "").trim());
        } else {
          if (!txt) { toast("내용을 적어 주세요"); return; }
          setItTitle(I2, txt);
          setItBody(I2, String(fd.get("memo") || "").trim());
        }
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
      askConfirm("‘" + esc(groupTitleOf(dcK, dcg)) + "’ 카드를 지울까요? 안에 적은 항목도 함께 사라져요.", "지우기", function () {
        S.groups[dcK] = (S.groups[dcK] || []).filter(function (g) { return g.id !== dcGid; });
        /* v40: 내 카테고리 투두리스트는 항목이 그 리스트(items) 안에 있어요 */
        var dcl = listOfSeg(dcK);
        if (GROUP_ARR[dcK]) S[GROUP_ARR[dcK]] = (S[GROUP_ARR[dcK]] || []).filter(function (x) { return x.gid !== dcGid; });
        else if (dcl) dcl.items = (dcl.items || []).filter(function (x) { return x.gid !== dcGid; });
        openCard = null;
        save(); closeSheet(); renderDiary(); toast("카드를 지웠어요");
      });
      return;
    }

    if (act === "addGroup") {
      /* v41: 중간 단계 없이 바로 카드 시트(제목·제목 색·To-do) */
      openNewCardSheet(el.getAttribute("data-tab") || "todo");
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
      var alId = el.getAttribute("data-list");
      var alL = containerOf(alId);
      if (!alL) return;
      var alKind = listKindOf(alL);
      /* v41: 모눈 메모는 새 다이어리로 */
      if (alKind === "memo") { openDiary(alId, null); return; }
      /* v45: 지출·정산은 전용 시트 */
      if (alKind === "expense") { openExpSheet(alL, null, null); return; }
      openSheet(formListItem(alL, null), function (fd) {
        var L0 = containerOf(alId);
        if (!L0) return;
        var txt0 = String(fd.get("text") || "").trim();
        var body0 = String(fd.get("memo") || "").trim();
        if (alKind === "memo") {
          if (!txt0 && !body0) { toast("제목이나 본문을 적어 주세요"); return; }
          var img0 = String(fd.get("img") || "");
          if (isBaseContainer(L0)) basePush(L0.base, { text: txt0, memo: body0 });
          else {
            var mit = { id: uid(), text: txt0, memo: body0, done: false, date: today };
            if (img0) mit.img = img0;
            L0.items.push(mit);
          }
        } else if (alKind === "review") {
          if (!txt0) { toast("이름을 적어 주세요"); return; }
          var rate0 = Math.max(0, Math.min(5, Math.round(Number(fd.get("rating")) || 0)));
          var place0 = String(fd.get("place") || "").trim();
          var when0 = String(fd.get("date") || "").slice(0, 10) || today;
          if (isBaseContainer(L0)) basePush(L0.base, { text: txt0, memo: body0, rating: rate0, place: place0, date: when0 });
          else L0.items.push({
            id: uid(), text: txt0, memo: body0, done: false,
            rating: rate0, place: place0, date: when0
          });
        } else {
          if (isBaseContainer(L0)) basePush(L0.base, { text: txt0, memo: body0 });
          else L0.items.push({ id: uid(), text: txt0, memo: body0, done: false });
        }
        save(); closeSheet(); renderDiary(); toast("추가했어요");
      });
      return;
    }

    if (act === "editList") {
      var eLid = el.getAttribute("data-id");
      var eL = findList(eLid);
      if (!eL) return;
      openSheet(formNewList(eL), function () { saveNoteSheet(); });
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
      if (dropDraftItem(el.getAttribute("data-id"))) return;
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
      if (dropDraftItem(el.getAttribute("data-id"))) return;
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
      if (dropDraftItem(el.getAttribute("data-id"))) return;
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
      var ccTab = el.getAttribute("data-tab") || "", ccGid = el.getAttribute("data-gid") || "";
      if (newCard && ccGid === newCard.gid) {
        /* 아직 저장 전인 새 카드 — 색만 기억해 두고 시트의 컬러판 표시를 바꿔요 */
        var ccv0 = String(el.getAttribute("data-color") || "");
        newCard.titleBg = /^#[0-9a-fA-F]{6}$/.test(ccv0) ? ccv0.toUpperCase() : "";
        var cp0 = el.closest(".cp");
        if (cp0) {
          cp0.querySelectorAll(".sw").forEach(function (b) {
            b.classList.toggle("sel", String(b.getAttribute("data-color") || "").toUpperCase() === newCard.titleBg);
          });
          var rs0 = cp0.querySelector(".cp-reset");
          if (rs0) rs0.classList.toggle("on", !newCard.titleBg);
        }
        return;
      }
      var ccg = groupOf(ccTab, ccGid);
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
      var poWho = el.getAttribute("data-who") || "me";
      var poInProfile = !!(el.closest && el.closest("#sheet .pr-sws"));
      setOwnerColor(poWho, el.getAttribute("data-color") || "");
      /* v43: 프로필에서 컬러를 고르면 프로필 사진 대신 그 컬러 동그라미로 (사진을 다시 올리면 사진이 우선) */
      if (poInProfile && avPic(poWho) && canEditAvatar(poWho)) setAvatarPic(poWho, "");
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
      openPersonSheet(el.getAttribute("data-who") === "you" ? "you" : "me", !!el.getAttribute("data-back"));
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
      else photoToBottom = true;     /* v39: 달력에서 목록으로 돌아오면 가장 최근 날짜(맨 아래)로 */
      save(); renderPhoto(); return;
    }
    if (act === "pcalPrev" || act === "pcalNext") {
      S.ui = S.ui || {};
      S.ui.photoMonth = shiftYm(photoMonthYM(), act === "pcalPrev" ? -1 : 1);
      save(); renderPhoto(); return;
    }
    if (act === "pcalDay") {
      var pcds = el.getAttribute("data-date");
      /* v38: 날짜 칸은 바로 크게 보기가 아니라 그날 사진 모아보기부터 */
      openDayGallery(pcds);
      return;
    }

    if (act === "openPhotoDay") { openDayGallery(el.getAttribute("data-date")); return; }

    /* v38: 사진 검색 · 검색 결과로 그날 모아보기 · 날짜 태그 고치기 */
    if (act === "photoSearch") {
      sheetCenter = true;
      openSheet(formPhotoSearch(""));
      var psi = document.getElementById("photoSearchIn");
      if (psi) { try { psi.focus({ preventScroll: true }); } catch (e) { psi.focus(); } }
      return;
    }
    if (act === "goPhotoDay") {
      var gpd = String(el.getAttribute("data-date") || "");
      closeSheet();
      openDayGallery(gpd);
      return;
    }
    if (act === "dateTag") {
      var tgd = String(el.getAttribute("data-date") || "").slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(tgd)) return;
      openSheet(formDateTag(tgd), function (fd) {
        setDateTag(tgd, fd.get("tag"));
        closeSheet();
        if (current === "photo") renderPhoto();
        toast("기록 이름을 저장했어요");
      });
      return;
    }
    if (act === "photoDayExpand") {
      photoDayAll = true;
      if (current === "photo") renderPhoto();
      return;
    }
    if (act === "photoDayBack") {
      photoDayView = null;
      photoDayAll = false;
      photoToBottom = true;          /* v39: 목록으로 돌아오면 가장 최근 날짜(맨 아래)로 */
      renderPhoto();
      return;
    }
    if (act === "addPhotoDay") {
      pendingPhotoDate = String(el.getAttribute("data-date") || "").slice(0, 10);
      var pdi = $("#photoInput");
      if (pdi) { pdi.value = ""; pdi.click(); }
      return;
    }

    if (act === "photoStep") { photoStep(Number(el.getAttribute("data-step")) || 1); return; }

    if (act === "addPhoto") {
      pendingPhotoDate = "";
      photoAddMore = false;
      var pi = $("#photoInput");
      if (pi) { pi.value = ""; pi.click(); }
      return;
    }

    /* v38: 사진 추가 시트 — 고른 사진 한 장 빼기 / 목록에 더 담기 */
    if (act === "upDel") {
      var udIdx = Number(el.getAttribute("data-i"));
      var udArr = upArray();
      if (isNaN(udIdx) || !udArr[udIdx]) return;
      udArr.splice(udIdx, 1);
      if (upMode === "day") { refreshDayEdit(); return; }      /* v40: 날짜 편집에서는 줄만 빼요 */
      if (!pendingFiles.length) { closeSheet(); return; }
      refreshAddPhoto();
      return;
    }
    if (act === "upAdd") {
      dayAddMore = upMode === "day";
      photoAddMore = !dayAddMore;
      var pai = $("#photoInput");
      if (pai) { pai.value = ""; pai.click(); }
      return;
    }
    /* v40: 모아보기 오른쪽 위 수정 아이콘 — 그날 사진 편집 시트 */
    if (act === "editPhotoDay") {
      var edDay = String(el.getAttribute("data-date") || "").slice(0, 10);
      if (!/^\d{4}-\d{2}-\d{2}$/.test(edDay)) return;
      openSheet(formEditPhotoDay(edDay), function (fd) { saveDayEdit(fd); });
      return;
    }

    /* v41: 날짜(챕터) 댓글 — 답글 모드 · 삭제 · ⋯ 메뉴 */
    if (act === "cmtReply") {
      var rowR = el.closest ? el.closest(".cmt") : null;
      var secR = el.closest ? el.closest(".dcmt") : null;
      var fR = secR ? secR.querySelector(".cmt-form") : null;
      if (!fR) return;
      var rePidIn = fR.querySelector('input[name="repid"]');
      if (rePidIn) rePidIn.value = rowR ? (rowR.getAttribute("data-pid") || "") : "";
      var reIn = fR.querySelector('input[name="re"]');
      if (reIn) reIn.value = el.getAttribute("data-id") || "";
      var whoName = el.getAttribute("data-name") || "";
      var tin = fR.querySelector(".cmt-in");
      if (tin) { tin.setAttribute("placeholder", "@" + whoName + "에게 답글"); tin.focus(); }
      var cur = fR.querySelector(".cmt-cancel");
      if (cur) cur.parentNode.removeChild(cur);
      var cbR = document.createElement("button");
      cbR.type = "button";
      cbR.className = "cmt-cancel";
      cbR.setAttribute("data-act", "cmtReplyCancel");
      cbR.textContent = "취소";
      fR.insertBefore(cbR, fR.querySelector(".cmt-send"));
      if (tin && tin.scrollIntoView) { try { tin.scrollIntoView({ block: "nearest" }); } catch (e) {} }
      return;
    }
    if (act === "cmtReplyCancel") {
      var secC = el.closest ? el.closest(".dcmt") : null;
      var fC = secC ? secC.querySelector(".cmt-form") : null;
      if (fC) {
        var reC = fC.querySelector('input[name="re"]');
        if (reC) reC.value = "";
        var rePidC = fC.querySelector('input[name="repid"]');
        if (rePidC) rePidC.value = "";
        var tC = fC.querySelector(".cmt-in");
        if (tC) tC.setAttribute("placeholder", "댓글 달기");
      }
      var cbC = secC ? secC.querySelector(".cmt-cancel") : null;
      if (cbC) cbC.parentNode.removeChild(cbC);
      return;
    }
    if (act === "cmtDel") {
      var rowD = el.closest ? el.closest(".cmt") : null;
      var pidD = rowD ? (rowD.getAttribute("data-pid") || "") : "";
      var cidDel = el.getAttribute("data-id");
      var pD = S.photos.filter(function (x) { return x.id === pidD; })[0];
      if (!pD) {
        /* 어느 사진에 달린 댓글인지 모를 때 — 그날 사진에서 찾아요 */
        pD = S.photos.filter(function (x) {
          return ((x.comments) || []).some(function (c) {
            return c.id === cidDel || (c.replies || []).some(function (r) { return r.id === cidDel; });
          });
        })[0];
      }
      if (!pD) return;
      pD.comments = (pD.comments || []).filter(function (c) {
        if (c.id === cidDel) return false;
        c.replies = (c.replies || []).filter(function (r) { return r.id !== cidDel; });
        return true;
      });
      save();
      refreshDayCmt(pD);
      toast("댓글을 지웠어요");
      return;
    }
    /* ⋯ — 사진 정보 수정 · 삭제 (사진 화면에는 아무 버튼도 두지 않고 여기서만) */
    if (act === "photoMenu") {
      var mid = el.getAttribute("data-id");
      var mp = S.photos.filter(function (x) { return x.id === mid; })[0];
      if (!mp) return;
      openSheet('<div class="sheet-hd"><h2>사진</h2><button class="icon-btn" data-close="1" aria-label="닫기">' + IC.x + "</button></div>" +
        '<p class="sheet-sub">' + esc(mp.title || mp.album || "사진") + "</p>" +
        '<div class="pv-menu"><button type="button" class="set-btn" data-act="photoEdit" data-id="' + esc(mp.id) + '">정보 수정</button>' +
        '<button type="button" class="set-btn warn" data-act="photoDelete" data-id="' + esc(mp.id) + '">삭제</button></div>' +
        '<div style="height:12px"></div><button class="btn-line" data-close="1">닫기</button>');
      return;
    }

    if (act === "photoEdit") {
      var pe = S.photos.filter(function (x) { return x.id === el.getAttribute("data-id"); })[0];      var pe = S.photos.filter(function (x) { return x.id === el.getAttribute("data-id"); })[0];
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
        if (pvKeep && photoShow(p2.id)) { openSheet(photoViewBody(), null, { full: true }); }
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
          openSheet(photoViewBody(), null, { full: true });
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
        if (doc) { var k = S.ui; S = normalizeState(doc); S.ui = k; applyLocalTheme(); applyTheme(); renderAll(); }
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

  /* v45: 사진 댓글 — Enter 로 바로 등록, Shift+Enter 는 줄바꿈 (한글 조합 중에는 그대로) */
  document.addEventListener("keydown", function (ev) {
    var t = ev.target;
    if (!t || !t.classList || !t.classList.contains("cmt-in") || t.tagName !== "TEXTAREA") return;
    if (ev.key !== "Enter" || ev.shiftKey || ev.isComposing) return;
    ev.preventDefault();
    var f = t.closest(".cmt-form");
    if (!f) return;
    if (f.requestSubmit) f.requestSubmit();
    else { var b = f.querySelector(".cmt-send"); if (b) b.click(); }
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

  /* v38: 사진첩 달력은 달들이 세로로 이어져 있어, 위아래로 미는 것이 곧 «달 넘기기»입니다.
     (예전처럼 밀 때마다 달을 새로 그리지 않고 화면이 자연스럽게 스크롤돼요) */

  /* v21: 달력에서 손가락으로 좌우로 밀면 이전/다음 달 — 사진 크게 보기의 넘기기와 같은 방식.
     왼쪽으로 밀면 다음 달, 오른쪽으로 밀면 이전 달. 탭(날짜 선택)과 세로 스크롤은 그대로 둡니다.
     v38: 미는 곳을 달력 칸(#s-cal .cal)뿐 아니라 캘린더 화면 전체(#s-cal — 헤더·아래 지난 일정까지)로 넓히고,
          기준도 45px/1.3배 → 32px/1.1배로 부드럽게 — «옆으로 밀었는데 안 넘어간다»를 줄였습니다. */
  var calSwipe = null, calSwiped = false;
  document.addEventListener("touchstart", function (ev) {
    calSwipe = null;
    if (current !== "cal" || photoView) return;
    if (sheetWrap.classList.contains("open")) return;      /* 시트(일정 추가·검색) 안에서는 그대로 */
    var g = ev.target.closest && ev.target.closest("#s-cal");
    if (!g || !ev.touches || !ev.touches.length) return;
    calSwipe = { x: ev.touches[0].clientX, y: ev.touches[0].clientY };
  }, { passive: true });
  document.addEventListener("touchend", function (ev) {
    if (!calSwipe || !ev.changedTouches || !ev.changedTouches.length) { calSwipe = null; return; }
    var t = ev.changedTouches[0];
    var dx = t.clientX - calSwipe.x, dy = t.clientY - calSwipe.y;
    calSwipe = null;
    /* 가로로 32px 넘게, 세로 움직임보다 조금만 크게 밀어도 넘어가요 — 그냥 누른 날짜는 그대로 선택 */
    if (Math.abs(dx) < 32 || Math.abs(dx) < Math.abs(dy) * 1.1) return;
    calSwiped = true;
    setTimeout(function () { calSwiped = false; }, 400);
    calMove(dx < 0 ? 1 : -1);
  }, { passive: true });

  /* v41: 카드 시트의 To-do 입력줄 — 폼(form) 안에 넣기 위해 div 로 바꿔도 같은 동작 */
  function cardAddFrom(lf) {
      var lid = lf.getAttribute("data-list");
      if (lid) {
        /* 사용자 리스트(리스트 탭) 안에서 바로 더하기 */
        var lobj = containerOf(lid);
        if (!lobj) return;
        var cin = lf.querySelector('input[name="text"]');
        var ctx = String((cin && cin.value) || "").trim();
        if (!ctx) { if (cin) cin.focus(); return; }
        var cit;
        if (isBaseContainer(lobj)) {
          cit = basePush(lobj.base, { text: ctx, memo: "" });
        } else {
          cit = { id: uid(), text: ctx, memo: "", done: false };
          lobj.items.push(cit);
        }
        save();
        var cbox = document.querySelector('#s-diary .todo-items[data-list="' + lid + '"]');
        if (cbox) {
          var cem = cbox.querySelector(".empty");
          if (cem) cem.remove();
          cbox.insertAdjacentHTML("beforeend", listItemRow(cit, '<div class="t tw">' + esc(itTitle(cit)) + "</div>",
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
      else if (isListSeg(lk)) { lit.text = ltxt; lit.memo = ""; }
      else { lit.kind = "movie"; lit.title = ltxt; lit.rating = 4; lit.date = today; lit.review = ""; lit.place = ""; lit.done = true; }
      /* v41: 저장 전인 새 카드 — 항목은 카드와 함께 저장될 때까지 잠깐 들고 있어요 */
      if (newCard && newCard.gid === lgid) {
        newCard.items.push(lit);
        var nbox0 = document.querySelector("#sheet .card-items");
        if (nbox0) {
          var nem0 = nbox0.querySelector(".empty");
          if (nem0) nem0.remove();
          nbox0.insertAdjacentHTML("beforeend", diaryRow(lk, lit));
        }
        if (lin) { lin.value = ""; lin.focus(); }
        return;
      }
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

  }

  document.addEventListener("submit", function (ev) {
    if (ev.target.id === "personForm") {
      ev.preventDefault();
      var pfWho = ev.target.getAttribute("data-who") === "you" ? "you" : "me";
      var pfFd = new FormData(ev.target);
      var pfName = String(pfFd.get("name") || "").trim();
      if (!pfName) { toast("이름을 적어 주세요"); return; }
      var beforeDef = defaultPhrase();
      if (pfWho === "me") S.couple.me = pfName; else S.couple.you = pfName;
      /* 문구를 기본값 그대로 두고 있었다면 새 이름에 맞춰 같이 바꿔 줍니다 */
      if (S.couple.phrase === beforeDef) S.couple.phrase = defaultPhrase();
      /* v42: 생일도 프로필에서 — 빈 값이면 지워요 */
      if (pfFd.has("bday")) {
        S.couple.birthdays = S.couple.birthdays || {};
        S.couple.birthdays[pfWho] = String(pfFd.get("bday") || "").trim();
      }
      save(); renderAll();
      if (personBack) { personBack = false; openDdaySheet(); }
      else closeSheet();
      toast("저장했어요");
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

    /* v41: 날짜(챕터) 댓글·대댓글 달기 — 작성자 프사·이름과 함께 그날 사진에 담겨요.
       새 댓글은 그날의 대표(첫 번째) 사진에, 대댓글은 원래 댓글이 있던 사진에 붙어요. */
    if (ev.target.classList && ev.target.classList.contains("cmt-form")) {
      ev.preventDefault();
      var cf = ev.target;
      var dayC = String(cf.getAttribute("data-day") || "").slice(0, 10) || String(photoDayView || "");
      var cin = cf.querySelector(".cmt-in");
      var txt = String((cin && cin.value) || "").trim();
      if (!txt) { if (cin) cin.focus(); return; }
      var reId = String((cf.querySelector('input[name="re"]') || {}).value || "");
      var rePid = String((cf.querySelector('input[name="repid"]') || {}).value || "");
      var rep = (dayC ? dayRepPhoto(dayC) : null) ||
        S.photos.filter(function (x) { return x.id === cf.getAttribute("data-id"); })[0];
      if (!rep) return;
      var at = new Date().toISOString();
      if (reId) {
        var owner = S.photos.filter(function (x) { return x.id === rePid; })[0] ||
          S.photos.filter(function (x) {
            return ((x.comments) || []).some(function (c) {
              return c.id === reId || ((c.replies || [])).some(function (r) { return r.id === reId; });
            });
          })[0] || rep;
        owner.comments = Array.isArray(owner.comments) ? owner.comments : [];
        var par = owner.comments.filter(function (c) { return c.id === reId; })[0];
        var toName = par ? cmtName(par.who) : "";
        if (!par) {
          owner.comments.forEach(function (c) {
            (c.replies || []).forEach(function (r) {
              if (r.id === reId) { par = c; toName = cmtName(r.who); }
            });
          });
        }
        if (par) {
          par.replies = Array.isArray(par.replies) ? par.replies : [];
          par.replies.push({ id: uid(), who: "me", text: txt, at: at, to: toName });
        }
      } else {
        rep.comments = Array.isArray(rep.comments) ? rep.comments : [];
        rep.comments.push({ id: uid(), who: "me", text: txt, at: at, replies: [] });
      }
      save();
      refreshDayCmt(dayC || rep);
      var nf2 = document.querySelector("#s-photo .dcmt.dcmt-day .cmt-in");
      if (nf2) { try { nf2.focus(); } catch (e) {} }
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
          kind: LIST_KINDS.indexOf(String(nf.get("new_kind") || "")) >= 0 ? String(nf.get("new_kind")) : "check", items: []
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
                  applyLocalTheme();
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
          /* v35: 로그인해 진짜 기록을 받으면 이 폰 테마를 다시 얹습니다 */
          applyLocalTheme();
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
    if (ev.target.id === "listQuickForm") {
      /* v38: 모눈 메모 · 별점 리뷰 · 지출·정산의 맨 위 빠른 추가 한 줄 */
      ev.preventDefault();
      var qf = ev.target;
      var qid = qf.getAttribute("data-list");
      var ql = containerOf(qid);
      var qk = qf.getAttribute("data-kind") || "check";
      if (!ql) return;
      var qin = qf.querySelector('input[name="text"]');
      var qtxt = String((qin && qin.value) || "").trim();
      if (!qtxt) { if (qin) qin.focus(); return; }
      if (isBaseContainer(ql)) {
        var qam0 = qf.querySelector('input[name="amount"]');
        basePush(ql.base, { text: qtxt, memo: "", rating: qk === "review" ? 0 : null, place: qk === "review" ? "" : null,
          amount: qk === "expense" ? parseAmount(qam0 && qam0.value) : null });
      } else {
        var qit = { id: uid(), text: qtxt, memo: "", done: false, date: today };
        if (qk === "review") { qit.rating = 0; qit.place = ""; }
        if (qk === "expense") {
          var qam = qf.querySelector('input[name="amount"]');
          qit.amount = parseAmount(qam && qam.value);
        }
        ql.items.push(qit);
      }
      save();
      renderDiary();
      var qnew = document.querySelector('#s-diary #listQuickForm input[name="text"]');
      if (qnew) qnew.focus();
      return;
    }
    if (ev.target.id === "listAddForm") {
      ev.preventDefault();
      cardAddFrom(ev.target);
      return;
    }
    if (ev.target.id !== "sheetForm" || !sheetSubmit) return;
    ev.preventDefault();
    var fd = new FormData(ev.target);
    try { sheetSubmit(fd); } catch (e) { toast("저장하지 못했어요"); }
  });

  /* v41: 카드 시트의 To-do 「Add」 — 폼 안에 넣으면서 div 로 바뀌어 클릭·엔터로 더해요 */
  document.addEventListener("click", function (ev) {
    var b = ev.target && ev.target.closest ? ev.target.closest("#sheet #listAddForm .todo-add-btn") : null;
    if (!b) return;
    ev.preventDefault();
    var lf = b.closest("#listAddForm");
    if (lf) cardAddFrom(lf);
  }, true);
  document.addEventListener("keydown", function (ev) {
    if (ev.key !== "Enter") return;
    var t = ev.target;
    if (!t || !t.closest || !t.closest("#sheet #listAddForm input[name=\"text\"]")) return;
    ev.preventDefault();
    cardAddFrom(t.closest("#listAddForm"));
  }, true);

  document.addEventListener("input", function (ev) {
    var t = ev.target;
    /* v45: 사진 댓글 칸 — 쓰는 만큼 아래로 늘어나요 */
    if (t && t.classList && t.classList.contains("cmt-in") && t.tagName === "TEXTAREA") { cmtGrow(t); return; }
    /* v45: 지출·정산 금액·예산 — 치는 대로 1,000 단위 쉼표 */
    if (t && t.closest && t.closest("#sheet") && (t.name === "amount" || t.name === "budget")) {
      var digits = String(t.value || "").replace(/[^\d]/g, "").slice(0, 12);
      var fmt = digits ? won(Number(digits)) : "";
      if (t.value !== fmt) t.value = fmt;
      return;
    }
    /* v42: 모눈 다이어리 글 상자 — 적는 만큼 종이가 길어지고, 그림 좌표도 함께 맞춰요 */
    if (t && t.classList && t.classList.contains("d41-txt")) {
      var d41TidIn = t.getAttribute("data-txedit");
      var d41To = (diary && diary.texts || []).filter(function (x) { return x.id === d41TidIn; })[0];
      if (d41To) d41To.text = String(t.innerText || "").replace(/\u00a0/g, " ");
      d41Grow();
      d41Sync();
      return;
    }
    /* v42: 글씨 크기 가로 슬라이더 — v44 에서 − + 조절로 바꿨어요 */
    /* v19: 일정 검색 — 글자를 칠 때마다 결과를 바로 */
    if (t && t.id === "calSearchIn") {
      var sOut = document.getElementById("calSearchOut");
      if (sOut) sOut.innerHTML = calSearchResults(t.value);
      return;
    }
    /* v38: 사진 검색 — 글자를 칠 때마다 그 글자가 들어간 날짜 태그·캡션·장소의 날이 나와요 */
    if (t && t.id === "photoSearchIn") {
      var pOut = document.getElementById("photoSearchOut");
      if (pOut) pOut.innerHTML = photoSearchResults(t.value);
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
    /* v44: 기념일 시트 상단 문구 — 쓰는 만큼 라벨 옆 남은 글자 수가 줄어요 */
    if (t && t.name === "phrase" && t.closest && t.closest("#sheetForm")) {
      var pcnt = document.getElementById("ddayPhraseCnt");
      if (pcnt) pcnt.textContent = "최대 14자 · " + Math.max(0, 14 - String(t.value || "").length);
      return;
    }
    /* v44: 다이어리 제목·날짜를 바꾸면 자동 저장 */
    if (t && (t.classList.contains("d41-title") || t.classList.contains("d41-datein"))) {
      d41AutoSaveSoon();
      return;
    }
    /* v45: 프로필 생일 — 고르는 순간 바로 아래 줄에 「1992년 6월 26일」로 보여요 */
    if (t && t.classList && t.classList.contains("pr-bday")) {
      var pbv = String(t.value || "").slice(0, 10);
      var prb = document.getElementById("prBdayTxt");
      if (prb) prb.textContent = (pbv && parseBirthday(pbv) ? bdayFullText(pbv) + " · " : "") +
        "생일을 골라 주세요. 홈 D-day 에는 월·일로 보여요.";
      return;
    }
  });

  /* v44: 한글 조합(한 글자로 뭉치는 입력)으로 문구를 쓰고 나서도 남은 글자 수를 바로 맞춰요 */
  document.addEventListener("compositionend", function (ev) {
    var t = ev.target;
    if (!t || t.name !== "phrase" || !t.closest || !t.closest("#sheetForm")) return;
    var pcnt = document.getElementById("ddayPhraseCnt");
    if (pcnt) pcnt.textContent = "최대 14자 · " + Math.max(0, 14 - String(t.value || "").length);
  });

  /* 파일 선택 → 프로필 사진 (동그란 아바타) */
  document.addEventListener("change", function (ev) {
    /* v21: 일정 시간을 고르고 나면 그 칸은 접고, 고른 시간만 버튼에 남겨요 (다시 누르면 또 고름) */
    if (ev.target && ev.target.classList && ev.target.classList.contains("js-evtime") && ev.target.value) {
      ev.target.hidden = true;
    }
    /* v41: 모눈 다이어리 사진 — 720px 로 줄여 여러 장 붙이고, 붙인 자리에서 크기·삭제 */
    if (ev.target && ev.target.classList && ev.target.classList.contains("d41-datein")) {
      var dBig = document.getElementById("d41DateBig");
      if (dBig) dBig.textContent = d41Stamp(ev.target.value);
      return;
    }
    if (ev.target && ev.target.id === "d41ImgIn") {
      var dFiles = Array.prototype.slice.call(ev.target.files || []);
      ev.target.value = "";
      if (!dFiles.length || !diary) return;
      var dSeq = Promise.resolve();
      var dCursorY = null, dLastAr = 0.75;   /* v42: 여러 장을 붙이면 서로 겹치지 않게 차례로 아래로 */
      dFiles.forEach(function (f) {
        dSeq = dSeq.then(function () {
          var comp = (window.TwoLog && window.TwoLog.compressImage)
            ? window.TwoLog.compressImage(f, 720, 0.6)
            : Promise.reject(new Error("no_compress"));
          return comp.then(function (res) {
            if (res && res.width && res.height) dLastAr = res.height / res.width;
            return new Promise(function (ok, no) {
              var fr = new FileReader();
              fr.onload = function () { ok(String(fr.result || "")); };
              fr.onerror = function () { no(fr.error || new Error("read_failed")); };
              fr.readAsDataURL(res.blob);
            });
          }).then(function (dataUrl) {
            if (!dataUrl || !diary) return;
            /* v42: 사진은 지금 내용 아래에 자유롭게 놓여요 (끌어서 옮기고 모서리로 크기 조절) */
            var W = d41WPx();
            if (dCursorY == null) {
              var paper0 = document.getElementById("d41Paper");
              var btm = 0;
              if (paper0) Array.prototype.forEach.call(paper0.querySelectorAll(".d41-tx, .d41-imgb"), function (el) {
                btm = Math.max(btm, el.offsetTop + el.offsetHeight + Math.round(W * 0.03));
              });
              dCursorY = btm ? btm / W : 0.6;
            }
            var ny = dCursorY;
            dCursorY = ny + dLastAr * 0.74 + 0.05;
            var rec = { id: uid(), src: dataUrl, x: 0.06, y: ny, w: 0.74 };
            diary.imgs.push(rec);
            diary.sel = "img:" + rec.id;
          }).catch(function () { toast("사진을 붙이지 못했어요"); });
        });
      });
      dSeq.then(function () {
        if (!diary) return;
        d41RenderNodes();
        d41PanelOpen("text");
        if (diary.sel) d41Select(diary.sel);
        d41HistPush();
        d41AutoSave();
      });
      return;
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
    ev.target.value = "";
    if (!files.length) return;
    /* v40: 날짜 사진 편집 시트의 「+ 추가」 — 그날 사진 목록에 이어 담아요 */
    if (dayAddMore && dayEdit) {
      dayAddMore = false;
      files.forEach(function (f) {
        var u = "";
        try { u = URL.createObjectURL(f); pendingUrls.push(u); } catch (e) {}
        dayEdit.items.push({ file: f, url: u });
      });
      refreshDayEdit();
      return;
    }
    /* v38: 목록 위 「추가」로 더 담을 때는 지금 고른 사진에 이어 붙여요 */
    if (photoAddMore && pendingFiles.length) {
      photoAddMore = false;
      var dIn = document.querySelector("#sheet input[name=date]");
      var keepDate = dIn ? dIn.value : "";
      pendingFiles = pendingFiles.concat(files);
      refreshAddPhoto();
      var dKeep = document.querySelector("#sheet input[name=date]");
      if (dKeep && keepDate) dKeep.value = keepDate;
      return;
    }
    photoAddMore = false;
    var upHtml = formAddPhoto(files);
    pendingPhotoDate = "";            /* v38: 날짜 기본값은 이 시트 한 번만 */
    openSheet(upHtml, function (fd) {
      var list = pendingFiles.slice();
      if (!list.length) { closeSheet(); return; }
      var date = fd.get("date") || today;
      var title = String(fd.get("title") || "").trim();
      /* v38: 태그(경주여행)가 있으면 그날 사진들의 앨범 이름으로 — 없으면 기본 앨범 */
      var tag = String(fd.get("album_tag") || "").trim();
      addPhotoFiles(list, { album: tag || defaultAlbum(), date: date, title: title }).then(function () {
        if (tag) setDateTag(date, tag);
      });
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
    /* v35: 이 폰에 저장해 둔 모드·색·폰트를 먼저 엎어 둡니다 */
    applyLocalTheme(!!(opts && opts.signedOut));
    /* v28: 앱을 새로 켜면 캘린더는 지난번에 보던 달이 아니라 오늘의 달로 열립니다 */
    syncCalToday();
    if (opts && opts.signedOut) { S.auth.out = true; S.auth.email = ""; }
    SIGNED_OUT = !!(opts && opts.signedOut);
    /* v36: 폰에 들어와 있는 노트 중복 항목을 먼저 하나로 정리합니다.
       실제로 줄었으면 저장해 서버(notes)에서도 중복 행이 지워지게 합니다. */
    dedupeNotesAndSave();
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
    var prev = S;
    var unchanged = false;
    S = normalizeState(doc);
    if (ui) S.ui = ui;
    /* v35: 상대가 무엇을 바꿨든 화면 모드·색·폰트는 내 폰 설정을 그대로 유지합니다 */
    applyLocalTheme();
    /* v36: 상대가 준 상태에 같은 줄이 두 번 들어 있으면 하나로 정리 (줄었으면 서버에도 반영) */
    dedupeNotesAndSave();
    if (prev) { try { unchanged = JSON.stringify(stripUi(S)) === JSON.stringify(stripUi(prev)); } catch (e) {} }
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
