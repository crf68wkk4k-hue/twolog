"""투로그 v39 확인 — 카테고리마다 속지 고르기(+ 기본 카테고리도) · 사진 달력 아이폰식.

1) 버전: sw.js 캐시 twolog-v39 · APP_VERSION v39 · My 탭 「버전 v39」
2) + 시트 — 카테고리 줄마다 지금 속지 배지, 누르면 그 카테고리의 속지를 고치는 모드
   - 메모·버킷리스트·영화·먹방(기본)은 「카드」, 내가 만든 카테고리는 그 속지 이름
   - 줄을 누르면 .active · 제목 「속지 레이아웃 · 버킷리스트」 · 안내에 그 이름
   - 2×2 카드가 그 카테고리의 속지를 체크 · 다른 속지를 누르면 줄 배지가 바로 바뀜
   - 기본 카테고리에만 「카드」(지금 모양으로 되돌리기) 가 보임
   - 「저장하기」로 S.noteKinds(기본) · list.kind(내 카테고리) 에 반영
3) 기본 카테고리 화면이 고른 속지로 그려짐 — 지출·정산(합계·금액) · 줄글 메모 · 별점 리뷰
   - 속지 화면 머리의 「카드」로 지금 모양(카드)으로 되돌아감
4) 내 카테고리 · 방금 추가한 줄
   - 줄을 골라 속지 바꾸기 · 「추가」로 붙인 줄이 자동 선택
   - 추가를 누르지 않고 위 칸에 이름만 적어 저장하는 예전 흐름도 그대로
   - 줄 안 이름 수정 · ≡ 드래그 · 삭제는 방해받지 않음
5) Supabase 동기화 — settings note_meta 왕복
   - 예전(v38) 모양 note_meta(tabs·order 만)도 그대로 읽힘
   - 기본 카테고리 속지를 바꾸면 note_meta.kinds 로 올라가고 새로고침 뒤에도 유지
   - 속지에서 적은 금액이 notes 행 payload(amount)로 올라감
6) 사진첩 달력 — 요일 한 줄 sticky · 앞뒤 12개월(25개월) 이어짐 · 오늘 날짜 점
   - 열면 이번 달이 화면 가운데쯤 · 스크롤해도 요일 줄이 위에 붙어 있음
7) 콘솔/페이지 오류 0건

    python3 tests/v39.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, json, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

STUB = open(os.path.join(HERE, "stub-supabase.js"), encoding="utf-8").read()
ESM = re.compile(r"https://esm\.sh/.*")

fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (("  :: " + str(extra)) if extra else ""))
    if not cond:
        fails.append(name)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


socketserver.ThreadingTCPServer.allow_reuse_address = True
PORT = 0


def serve():
    global PORT
    handler = functools.partial(Quiet, directory=ROOT)
    httpd = socketserver.ThreadingTCPServer(("127.0.0.1", 0), handler)
    PORT = httpd.server_address[1]
    httpd.serve_forever()


threading.Thread(target=serve, daemon=True).start()
time.sleep(0.8)

LIB = "/workspace/.libs/usr/lib/x86_64-linux-gnu"
CHROMES = [
    None,
    "/workspace/.cache/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell",
    "/workspace/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome",
]


def launch(p):
    env = dict(os.environ)
    if os.path.isdir(LIB):
        env["LD_LIBRARY_PATH"] = LIB
    last = None
    for exe in CHROMES:
        try:
            kw = {"args": ["--no-sandbox"], "env": env}
            if exe:
                kw["executable_path"] = exe
            return p.chromium.launch(**kw)
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


URL = "http://127.0.0.1:%d/" % PORT


def new_ctx(browser, **kw):
    args = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                device_scale_factor=2)
    args.update(kw)
    return browser.new_context(**args)


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def watch(page, bucket):
    page.on("pageerror", lambda e: bucket.append("pageerror: " + str(e)))
    page.on("console", lambda m: bucket.append("console: " + m.text) if m.type == "error" else None)


def tab(page, idx, wait=520):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def note_tab(page):
    tab(page, 2, 620)


def open_add_sheet(page):
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(560)


def pick_kind(page, kind):
    page.locator("#sheet .nk-card[data-kind='%s']" % kind).click()
    page.wait_for_timeout(140)


def row_loc(page, text):
    """이름칸 값으로 카테고리 줄을 찾습니다 (줄 이름은 input value 라 has_text 로는 못 찾아요)."""
    n = page.evaluate("""(nm) => {
      const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
      return rows.findIndex(r => { const i = r.querySelector('.nord-nm'); return i && i.value.indexOf(nm) >= 0; });
    }""", text)
    return page.locator("#sheet #noteOrderList .nord-row").nth(n)


def state_of(page):
    return page.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")


def remote_seed(db, user_id, email):
    return """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: %s, email: %s } }));
    })();""" % (json.dumps(json.dumps(db, ensure_ascii=False)), json.dumps(user_id), json.dumps(email))


def remote_db(cid, uid_, email, notes, settings=None):
    return {
        "users": {uid_: {"id": uid_, "email": email, "password": "pw123456"}},
        "couples": [{"id": cid, "invite_code": "482913", "members": [uid_],
                     "me": "소영", "you": "준영", "since": "2025-11-19", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "photos": [],
        "notes": notes,
        "settings": settings or [],
        "uploads": [], "seq": 40
    }


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    watch(page, errs)

    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    check("sw.js 캐시 버전 twolog-v39", 'const VERSION = "twolog-v39"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v39", 'var APP_VERSION = "v39"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed_state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed_state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)

    tab(page, 4, 600)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v39」", ver.strip() == "버전 v39", ver)

    # ==================================================================
    # 2. + 시트 — 카테고리 줄마다 속지 배지 · 줄을 누르면 그 카테고리 속지 고르기
    # ==================================================================
    note_tab(page)
    open_add_sheet(page)
    ui = page.evaluate("""() => {
      const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
      const name = r => { const i = r.querySelector('.nord-nm'); return i ? i.value : ''; };
      const badge = r => ((r.querySelector('.nord-kb') || {}).textContent || '').trim();
      const cardsBtn = document.querySelector('#sheet .nk-cards');
      return {
        rows: rows.map(r => ({name: name(r), badge: badge(r), kind: r.getAttribute('data-kind'),
                              active: r.classList.contains('active')})),
        cardsBtn: !!cardsBtn,
        cardsShown: cardsBtn ? getComputedStyle(cardsBtn).display !== 'none' : false,
        label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || '',
        hint: (document.querySelector('#sheet #nkindHint') || {}).textContent || '',
        activeKinds: [...document.querySelectorAll('#sheet .nk-card.active')].map(c => c.getAttribute('data-kind'))};
    }""")
    by_name = {r["name"]: r for r in ui["rows"]}
    check("카테고리 줄마다 지금 속지 배지가 있음",
          len(ui["rows"]) >= 4 and all(r["badge"] for r in ui["rows"]), ui["rows"])
    check("기본 카테고리 배지는 「카드」", by_name.get("메모", {}).get("badge") == "카드"
          and by_name.get("버킷리스트", {}).get("badge") == "카드"
          and by_name.get("영화·먹방", {}).get("badge") == "카드",
          {k: v["badge"] for k, v in by_name.items()})
    custom_badges = [r["badge"] for r in ui["rows"] if "여행 준비물" in r["name"] or "주말 데이트" in r["name"]]
    check("내 카테고리 배지는 그 속지 이름", custom_badges == ["투두리스트", "줄글 메모"], custom_badges)
    check("처음에는 고른 줄이 없고 속지는 새 카테고리용 (투두리스트)",
          not any(r["active"] for r in ui["rows"]) and ui["activeKinds"] == ["check"], ui["activeKinds"])
    check("기본 카테고리용 「카드」 선택지는 줄을 고르기 전엔 숨어 있음",
          ui["cardsBtn"] and not ui["cardsShown"], ui["cardsShown"])

    row_loc(page, "버킷리스트").locator(".nord-nm").click()
    page.wait_for_timeout(260)
    sel = page.evaluate("""() => {
      const r = document.querySelector('#sheet #noteOrderList .nord-row.active');
      const cardsBtn = document.querySelector('#sheet .nk-cards');
      return {
        row: r ? (r.querySelector('.nord-nm') || {}).value : null,
        border: r ? getComputedStyle(r).borderTopColor : null,
        label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || '',
        hint: (document.querySelector('#sheet #nkindHint') || {}).textContent || '',
        activeKinds: [...document.querySelectorAll('#sheet .nk-card.active')].map(c => c.getAttribute('data-kind')),
        cardsShown: cardsBtn ? getComputedStyle(cardsBtn).display !== 'none' : false,
        cardsActive: cardsBtn ? cardsBtn.classList.contains('active') : false};
    }""")
    check("기본 카테고리 줄을 누르면 그 줄이 선택됨", sel["row"] == "버킷리스트"
          and sel["border"] not in ("", "rgb(232, 232, 237)"), sel)
    check("속지 제목에 고른 카테고리 이름", "속지 레이아웃" in sel["label"] and "버킷리스트" in sel["label"], sel["label"])
    check("안내 문구도 그 카테고리", "버킷리스트" in sel["hint"], sel["hint"])
    check("지금은 「카드」가 체크되고 2×2 는 비어 있음",
          sel["cardsShown"] and sel["cardsActive"] and sel["activeKinds"] == [], sel)

    pick_kind(page, "expense")
    page.wait_for_timeout(240)
    after = page.evaluate("""() => {
      const r = document.querySelector('#sheet #noteOrderList .nord-row.active');
      const cardsBtn = document.querySelector('#sheet .nk-cards');
      return {badge: ((r.querySelector('.nord-kb') || {}).textContent || '').trim(),
              kind: r.getAttribute('data-kind'),
              cardsActive: cardsBtn ? cardsBtn.classList.contains('active') : false,
              hidden: (document.querySelector('#sheet input[name="nkind"]') || {}).value,
              activeKinds: [...document.querySelectorAll('#sheet .nk-card.active')].map(c => c.getAttribute('data-kind'))};
    }""")
    check("속지를 고르면 그 줄 배지가 바로 바뀜", after["badge"] == "지출·정산" and after["kind"] == "expense", after)
    check("고른 속지 카드만 체크 · 「카드」는 풀림",
          after["activeKinds"] == ["expense"] and after["cardsActive"] is False, after)
    page.evaluate("document.querySelector('#sheet').scrollTop = 9999")
    page.wait_for_timeout(280)
    page.screenshot(path=os.path.join(SHOT, "note-v39-templates.png"))

    # 이름 수정이 방해받지 않는지 — 줄 안 이름칸에 글자를 넣는다
    nm = row_loc(page, "영화·먹방").locator(".nord-nm")
    nm.click()
    page.wait_for_timeout(140)
    nm.fill("영화·먹방")
    page.wait_for_timeout(120)
    check("줄 안 이름칸을 눌러도 그 줄이 선택됨",
          page.evaluate("""() => { const r = document.querySelector('#sheet #noteOrderList .nord-row.active');
            const i = r ? r.querySelector('.nord-nm') : null; return i ? i.value : ''; }""") == "영화·먹방")

    # 다른 카테고리 줄도 배지가 따로 논다 (메모 → 별점 리뷰)
    row_loc(page, "버킷리스트").locator(".nord-nm").click()
    page.wait_for_timeout(200)
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(760)
    st1 = state_of(page)
    check("저장하면 기본 카테고리 속지가 S.noteKinds 에 담김", st1.get("noteKinds", {}).get("bucket") == "expense",
          st1.get("noteKinds"))

    # ==================================================================
    # 3. 기본 카테고리 화면이 고른 속지로
    # ==================================================================
    ba = page.evaluate("""() => {
      const on = document.querySelector('#s-diary .seg-btn.active');
      return {on: on ? on.textContent.trim() : ''};
    }""")
    page.locator("#s-diary .seg-btn", has_text="버킷리스트").first.click()
    page.wait_for_timeout(560)
    bk = page.evaluate("""() => ({
      on: (document.querySelector('#s-diary .seg-btn.active') || {}).textContent || '',
      tag: (document.querySelector('#s-diary .note-hd .k') || {}).textContent,
      sum: (document.querySelector('#s-diary .ex-sum .v') || {}).textContent || '',
      quick: !!document.querySelector('#s-diary #listQuickForm input[name="amount"]'),
      back: !!document.querySelector('#s-diary .nh-back'),
      cards: document.querySelectorAll('#s-diary .ncard').length})""")
    check("버킷리스트 탭이 지출·정산 속지로 그려짐", bk["tag"] == "지출·정산" and bk["quick"] and bk["sum"], bk)
    check("속지 화면에는 카드 대신 목록 · 「카드」로 돌아갈 버튼", bk["cards"] == 0 and bk["back"], bk)

    page.fill("#s-diary #listQuickForm input[name=text]", "주말 외식")
    page.fill("#s-diary #listQuickForm input[name=amount]", "32000")
    page.locator("#s-diary #listQuickForm button").click()
    page.wait_for_timeout(520)
    money = page.evaluate("""() => {
      const rows = [...document.querySelectorAll('#s-diary .ex-row')];
      const hit = rows.filter(r => (r.querySelector('.ex-t') || {}).textContent === '주말 외식')[0] || null;
      return {sum: (document.querySelector('#s-diary .ex-sum .v') || {}).textContent || '',
              row: hit ? (hit.querySelector('.ex-t') || {}).textContent : '',
              amt: hit ? (hit.querySelector('.ex-a') || {}).textContent : '',
              item: (window.__app.state.bucket || []).filter(x => x.title === '주말 외식')[0] || null}; }""")
    check("기본 카테고리에도 항목·금액이 들어가고 합계가 계산됨",
          money["row"] == "주말 외식" and money["amt"] == "32,000원" and money["sum"].endswith("원"), money)
    check("항목은 원래 탭 항목(S.bucket)으로 저장 — amount·gid 유지",
          bool(money["item"]) and money["item"].get("amount") == 32000 and bool(money["item"].get("gid")), money["item"])

    page.locator("#s-diary .nh-back").click()
    page.wait_for_timeout(520)
    back = page.evaluate("""() => ({cards: document.querySelectorAll('#s-diary .ncard').length,
      kinds: window.__app.state.noteKinds || {}})""")
    check("「카드」를 누르면 지금 모양(카드)으로 되돌아감", back["cards"] > 0 and "bucket" not in back["kinds"], back)

    # 메모 → 줄글 메모
    open_add_sheet(page)
    row_loc(page, "메모").locator(".nord-nm").click()
    page.wait_for_timeout(200)
    pick_kind(page, "memo")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(720)
    page.locator("#s-diary .seg-btn", has_text="메모").first.click()
    page.wait_for_timeout(520)
    mm = page.evaluate("""() => ({tag: (document.querySelector('#s-diary .note-hd .k') || {}).textContent,
      cards: document.querySelectorAll('#s-diary .memo-card').length,
      quick: !!document.querySelector('#s-diary #listQuickForm'),
      circles: document.querySelectorAll('#s-diary .trow .circ').length})""")
    check("메모 탭이 줄글 메모 속지로 (체크 동그라미 없음)", mm["tag"] == "줄글 메모" and mm["quick"] and mm["circles"] == 0, mm)
    page.locator("#s-diary .nh-back").click()
    page.wait_for_timeout(460)

    # 영화·먹방 → 별점 리뷰
    open_add_sheet(page)
    row_loc(page, "영화·먹방").locator(".nord-nm").click()
    page.wait_for_timeout(200)
    pick_kind(page, "review")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(720)
    page.locator("#s-diary .seg-btn", has_text="영화·먹방").first.click()
    page.wait_for_timeout(520)
    rv = page.evaluate("""() => ({tag: (document.querySelector('#s-diary .note-hd .k') || {}).textContent,
      cards: document.querySelectorAll('#s-diary .rv-card').length,
      stars: document.querySelectorAll('#s-diary .rv-card .rvs').length})""")
    check("영화·먹방 탭이 별점 리뷰 속지로", rv["tag"] == "별점 리뷰" and rv["cards"] >= 1 and rv["stars"] >= 5, rv)
    page.locator("#s-diary .rv-card .rvs").nth(4).click()
    page.wait_for_timeout(460)
    first_log = page.evaluate("""() => (window.__app.state.logs || [])[0] || null""")
    check("기본 카테고리 리뷰에서 별을 누르면 그 항목 rating 이 바뀜",
          bool(first_log) and first_log.get("rating") == 5, first_log)
    page.locator("#s-diary .nh-back").click()
    page.wait_for_timeout(460)

    # ==================================================================
    # 4. 내 카테고리 · 방금 추가한 줄
    # ==================================================================
    open_add_sheet(page)
    row_loc(page, "여행 준비물").locator(".nord-nm").click()
    page.wait_for_timeout(200)
    pick_kind(page, "review")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(720)
    ch = page.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '여행 준비물')[0] || {};
      return {kind: l.kind, items: (l.items || []).length}; }""")
    check("내 카테고리는 줄에서 고른 속지로 바뀜", ch["kind"] == "review" and ch["items"] >= 1, ch)

    # 「추가」로 붙인 줄이 자동 선택 → 바로 속지 고르기
    open_add_sheet(page)
    page.locator("#sheet .nord-new").fill("가계부")
    page.evaluate("document.querySelector('#sheet .nord-add-btn').click()")
    page.wait_for_timeout(280)
    addrow = page.evaluate("""() => {
      const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
      const last = rows[rows.length - 1];
      return {active: last.classList.contains('active'),
              name: (last.querySelector('.nord-nm') || {}).value,
              label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || '',
              cardsShown: (() => { const c = document.querySelector('#sheet .nk-cards');
                return c ? getComputedStyle(c).display !== 'none' : false; })()};
    }""")
    check("「추가」로 붙인 줄이 바로 선택됨", addrow["active"] and addrow["name"] == "가계부", addrow)
    check("그 줄의 속지를 고르는 모드 · 새 카테고리라 「카드」는 없음",
          "가계부" in addrow["label"] and addrow["cardsShown"] is False, addrow)
    pick_kind(page, "expense")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(760)
    nw = page.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '가계부')[0] || {};
      return {kind: l.kind, on: (document.querySelector('#s-diary .lchip.active') || {}).textContent || '',
              sum: (document.querySelector('#s-diary .ex-sum .v') || {}).textContent || ''}; }""")
    check("붙인 줄로 만든 카테고리가 그 속지로 열림", nw["kind"] == "expense" and nw["on"].strip() == "가계부" and nw["sum"] != "", nw)

    # 추가를 누르지 않고 위 칸 이름만 → 그 속지로 새 카테고리 (예전 흐름)
    open_add_sheet(page)
    page.locator("#sheet .nord-new").fill("생각 정리")
    page.wait_for_timeout(160)
    state_after_focus = page.evaluate("""() => ({sel: !!document.querySelector('#sheet #noteOrderList .nord-row.active'),
      cardsShown: (() => { const c = document.querySelector('#sheet .nk-cards');
        return c ? getComputedStyle(c).display !== 'none' : false; })()})""")
    check("위 「새 카테고리 이름」 칸으로 가면 새 카테고리 모드로",
          state_after_focus["sel"] is False and state_after_focus["cardsShown"] is False, state_after_focus)
    pick_kind(page, "memo")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(760)
    plain = page.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '생각 정리')[0] || {};
      return {kind: l.kind, cards: document.querySelectorAll('#s-diary .memo-card').length}; }""")
    check("이름만 적고 저장해도 그 속지로 새 카테고리", plain["kind"] == "memo", plain)

    check("브라우저 콘솔/페이지 오류 없음 (로컬)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 5. Supabase 동기화 — note_meta 왕복 · 기본 카테고리 속지·금액
    # ==================================================================
    cid, uid2, mail = "couple-v39", "user-v39", "v39@twolog.app"
    gid = "g-bucket-1"
    seed_notes = [
        {"id": "B1", "couple_id": cid, "kind": "bucket", "sort": 0, "deleted": False,
         "payload": {"title": "제주도", "memo": "3박 4일", "done": False, "gid": gid}},
        {"id": "T1", "couple_id": cid, "kind": "todo", "sort": 1, "deleted": False,
         "payload": {"text": "장보기", "memo": "", "done": False, "gid": "g-todo-1"}},
    ]
    settings = [
        {"couple_id": cid, "key": "groups",
         "value": {"todo": [{"id": "g-todo-1", "title": "메모", "caption": ""}],
                   "bucket": [{"id": gid, "title": "버킷리스트", "caption": ""}], "log": []}},
        # v38 모양 — kinds 없이 tabs·order 만
        {"couple_id": cid, "key": "note_meta",
         "value": {"tabs": {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"},
                            "log": {"e": "", "n": "영화·먹방"}},
                   "order": ["todo", "bucket", "log"]}},
    ]
    db2 = remote_db(cid, uid2, mail, seed_notes, settings)
    ctx2 = new_ctx(browser)
    ctx2.add_init_script(remote_seed(db2, uid2, mail))
    page2 = ctx2.new_page()
    errs2 = []
    watch(page2, errs2)
    stub_route(page2)
    page2.goto(URL, wait_until="domcontentloaded")
    page2.wait_for_selector("#tabbar .tab", timeout=25000)
    page2.wait_for_timeout(2800)
    old = page2.evaluate("""() => ({kinds: window.__app.state.noteKinds || {},
      note: window.__app.state.note || {}, order: window.__app.state.noteOrder || []})""")
    check("예전(v38) note_meta 를 그대로 읽음 — 이름·순서 유지", old["note"].get("bucket", {}).get("n") == "버킷리스트"
          and old["order"][:3] == ["todo", "bucket", "log"], old)
    check("예전 note_meta 에는 kinds 가 없어 기본 카테고리는 카드 그대로", old["kinds"] == {}, old["kinds"])

    tab(page2, 2, 700)
    open_add_sheet(page2)
    row_loc(page2, "버킷리스트").locator(".nord-nm").click()
    page2.wait_for_timeout(220)
    pick_kind(page2, "expense")
    page2.locator("#sheet button.btn-primary").click()
    page2.wait_for_timeout(2000)
    meta = page2.evaluate("""() => {
      const r = (window.__stub.settings || []).filter(x => x.key === 'note_meta')[0] || null;
      return r ? r.value : null; }""")
    check("기본 카테고리 속지가 서버 note_meta.kinds 로 올라감",
          bool(meta) and (meta.get("kinds") or {}).get("bucket") == "expense", meta)
    check("예전 값(이름·순서)도 note_meta 에 그대로 남아 있음",
          bool(meta) and (meta.get("tabs") or {}).get("bucket", {}).get("n") == "버킷리스트"
          and (meta.get("order") or [])[:3] == ["todo", "bucket", "log"], meta)

    page2.locator("#s-diary .seg-btn", has_text="버킷리스트").first.click()
    page2.wait_for_timeout(560)
    page2.fill("#s-diary #listQuickForm input[name=text]", "숙소")
    page2.fill("#s-diary #listQuickForm input[name=amount]", "150000")
    page2.locator("#s-diary #listQuickForm button").click()
    page2.wait_for_timeout(2000)
    brow = page2.evaluate("""() => {
      const rows = (window.__stub.notes || []).filter(x => x.kind === 'bucket' && !x.deleted);
      const hit = rows.filter(x => (x.payload || {}).title === '숙소')[0] || null;
      return {hit: hit ? hit.payload : null, n: rows.length}; }""")
    check("속지에서 적은 금액이 notes 행 payload(amount)로 올라감",
          bool(brow["hit"]) and brow["hit"].get("amount") == 150000 and bool(brow["hit"].get("gid")), brow)

    page2.reload(wait_until="domcontentloaded")
    page2.wait_for_selector("#tabbar .tab", timeout=25000)
    page2.wait_for_timeout(2600)
    tab(page2, 2, 700)
    page2.locator("#s-diary .seg-btn", has_text="버킷리스트").first.click()
    page2.wait_for_timeout(560)
    again = page2.evaluate("""() => ({kinds: window.__app.state.noteKinds || {},
      tag: (document.querySelector('#s-diary .note-hd .k') || {}).textContent,
      sum: (document.querySelector('#s-diary .ex-sum .v') || {}).textContent || '',
      rows: document.querySelectorAll('#s-diary .ex-row').length})""")
    check("새로고침해도 기본 카테고리 속지가 유지됨", again["kinds"].get("bucket") == "expense"
          and again["tag"] == "지출·정산" and again["rows"] >= 2, again)
    check("새로고침해도 금액·합계가 그대로 (150,000원 포함)", again["sum"].endswith("원"), again["sum"])
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errs2) == 0, errs2[:4])
    ctx2.close()

    # ==================================================================
    # 6. 사진첩 달력 — 요일 한 줄 sticky · 앞뒤 12개월 · 오늘 점
    # ==================================================================
    ctx3 = new_ctx(browser)
    ctx3.add_init_script("window.__TWOLOG_MODE = 'local';")
    page3 = ctx3.new_page()
    errs3 = []
    watch(page3, errs3)
    page3.goto(URL + "?demo=1", wait_until="networkidle")
    page3.wait_for_timeout(700)
    seed3 = page3.evaluate("JSON.stringify(window.__app.state)")
    page3.goto(URL, wait_until="domcontentloaded")
    page3.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed3)
    page3.reload(wait_until="networkidle")
    page3.wait_for_timeout(900)
    tab(page3, 3, 620)
    page3.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page3.wait_for_timeout(900)

    cal = page3.evaluate("""() => {
      const box = document.getElementById('screens');
      const br = box.getBoundingClientRect();
      const ms = [...document.querySelectorAll('#s-photo .pcal-m')];
      const weeks = [...document.querySelectorAll('#s-photo .pcal-week')];
      const stick = document.querySelector('#s-photo .pcal-stick');
      const ymNow = (() => { const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'); })();
      const cur = document.querySelector('#s-photo .pcal-m[data-ym="' + ymNow + '"]');
      const curR = cur ? cur.getBoundingClientRect() : null;
      const dots = [...document.querySelectorAll('#s-photo .pcell.today .pdot')];
      const d0 = dots[0] ? dots[0].getBoundingClientRect() : null;
      const cell = dots[0] ? dots[0].closest('.pcell').getBoundingClientRect() : null;
      const g = document.querySelector('#s-photo .pcal-grid');
      const c0 = g ? g.querySelector('.pcell:not(.blank)') : null;
      const c0r = c0 ? c0.getBoundingClientRect() : null;
      return {
        months: ms.length, first: ms.length ? ms[0].getAttribute('data-ym') : null,
        last: ms.length ? ms[ms.length - 1].getAttribute('data-ym') : null,
        ymNow, weeks: weeks.length,
        stick: stick ? {pos: getComputedStyle(stick).position,
                        labels: [...stick.querySelectorAll('span')].map(s => s.textContent).join(''),
                        top: Math.round(stick.getBoundingClientRect().top - br.top)} : null,
        curTop: curR ? Math.round(curR.top - br.top) : null, boxH: Math.round(br.height),
        todayCells: document.querySelectorAll('#s-photo .pcell.today').length,
        dots: dots.length,
        dot: d0 ? {w: Math.round(d0.width), h: Math.round(d0.height),
                   radius: getComputedStyle(dots[0]).borderRadius,
                   inside: cell ? (d0.top >= cell.top - 1 && d0.bottom <= cell.bottom + 1) : false} : null,
        cellW: c0r ? Math.round(c0r.width) : null, cellH: c0r ? Math.round(c0r.height) : null,
        perMonthWeeks: (() => {
          const m = ms[ms.length - 1]; return m ? m.querySelectorAll('.pcal-week').length : 0; })()};
    }""")
    this_ym = time.strftime("%Y-%m")

    def shift_ym(ym, step):
        y, m = int(ym[:4]), int(ym[5:]) - 1 + step
        return "%04d-%02d" % (y + m // 12, m % 12 + 1)

    minus12, plus12 = shift_ym(this_ym, -12), shift_ym(this_ym, 12)
    check("사진 달력 요일 줄은 한 줄뿐 (달마다 반복하지 않음)",
          cal["weeks"] == 1 and cal["perMonthWeeks"] == 0, (cal["weeks"], cal["perMonthWeeks"]))
    check("요일 줄이 달력 위에 고정(sticky)", cal["stick"] and cal["stick"]["pos"] == "sticky"
          and cal["stick"]["labels"].replace(" ", "") == "일월화수목금토", cal["stick"])
    check("앞뒤 12개월이 이어짐 (25개월 이상)", cal["months"] >= 25, cal["months"])
    m_first = cal["first"] or ""
    m_last = cal["last"] or ""
    check("12개월 전부터 12개월 뒤까지", m_first <= minus12 and m_last >= plus12,
          (m_first, minus12, plus12, m_last))
    check("열면 이번 달이 화면 가운데쯤", cal["curTop"] is not None and 0 <= cal["curTop"] <= cal["boxH"] * 0.6,
          (cal["curTop"], cal["boxH"]))
    check("오늘 날짜는 한 칸 · 점 하나", cal["todayCells"] == 1 and cal["dots"] == 1, (cal["todayCells"], cal["dots"]))
    check("오늘 점은 동그랗고 칸 안에 있음", bool(cal["dot"]) and cal["dot"]["inside"]
          and cal["dot"]["w"] == cal["dot"]["h"] and cal["dot"]["radius"] not in ("0px", ""), cal["dot"])
    check("칸은 그대로 정사각형", cal["cellW"] == cal["cellH"] or abs(cal["cellW"] - cal["cellH"]) <= 1,
          (cal["cellW"], cal["cellH"]))
    page3.screenshot(path=os.path.join(SHOT, "photo-cal-v39.png"))

    # 스크롤해도 요일 줄은 위에 붙어 있고, 달은 계속 이어짐
    page3.evaluate("document.getElementById('screens').scrollTop += 520")
    page3.wait_for_timeout(420)
    sc = page3.evaluate("""() => { const box = document.getElementById('screens');
      const br = box.getBoundingClientRect();
      const s = document.querySelector('#s-photo .pcal-stick');
      const m = document.querySelector('#s-photo .pcal-m');
      return {stickTop: s ? Math.round(s.getBoundingClientRect().top - br.top) : null,
              scroll: Math.round(box.scrollTop),
              months: document.querySelectorAll('#s-photo .pcal-m').length}; }""")
    check("위아래로 넘겨도 요일 줄은 화면 위에 붙어 있음", sc["stickTop"] == 0 and sc["scroll"] > 300, sc)
    check("스크롤 뒤에도 달력은 계속 이어짐", sc["months"] >= 25, sc["months"])
    page3.evaluate("document.getElementById('screens').scrollTop += 99999")
    page3.wait_for_timeout(420)
    end = page3.evaluate("""() => { const ms = [...document.querySelectorAll('#s-photo .pcal-m')];
      const last = ms[ms.length - 1];
      const box = document.getElementById('screens');
      return {last: last.getAttribute('data-ym'),
              visible: last.getBoundingClientRect().top < box.getBoundingClientRect().bottom}; }""")
    check("맨 아래까지 밀면 마지막 달(+12개월)까지 보임", end["visible"], end)
    check("브라우저 콘솔/페이지 오류 없음 (사진 달력)", len(errs3) == 0, errs3[:4])
    ctx3.close()

    # ==================================================================
    # 7. 사진첩 날짜 머리글 — 요일 없이 「11월 18일 · 태그」 (태그는 글씨로)
    # ==================================================================
    ctx4 = new_ctx(browser)
    ctx4.add_init_script("window.__TWOLOG_MODE = 'local';")
    page4 = ctx4.new_page()
    errs4 = []
    watch(page4, errs4)
    page4.goto(URL + "?demo=1", wait_until="networkidle")
    page4.wait_for_timeout(700)
    seed4 = page4.evaluate("JSON.stringify(window.__app.state)")
    page4.goto(URL, wait_until="domcontentloaded")
    page4.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed4)
    page4.reload(wait_until="networkidle")
    page4.wait_for_timeout(900)
    tab(page4, 3, 620)
    head = page4.evaluate("""() => {
      const days = [...document.querySelectorAll('#s-photo .pday')];
      const heads = days.map(d => d.querySelector('.pday-hd'));
      const tags = [...document.querySelectorAll('#s-photo .pday-tag')];
      const t0 = tags[0], d0 = days[0].querySelector('.d');
      const cs = t0 ? getComputedStyle(t0) : null;
      return {n: days.length,
        texts: heads.map(h => [...h.children].map(c => c.textContent.trim()).filter(Boolean).join(' ')),
        hasWeekday: heads.some(h => h.textContent.indexOf('요일') >= 0),
        dots: document.querySelectorAll('#s-photo .pday-dot').length,
        tagged: tags.filter(t => !t.classList.contains('empty')).length,
        tagFs: cs ? cs.fontSize : '', dateFs: d0 ? getComputedStyle(d0).fontSize : '',
        borders: cs ? [cs.borderTopWidth, cs.borderRightWidth, cs.borderBottomWidth, cs.borderLeftWidth] : [],
        bg: cs ? cs.backgroundColor : ''};
    }""")
    check("날짜 머리글에 요일이 없음", head["n"] >= 1 and head["hasWeekday"] is False, head["texts"])
    check("태그가 있는 날은 날짜 옆 가운데 점 + 태그", head["tagged"] >= 1 and head["dots"] == head["tagged"],
          (head["tagged"], head["dots"], head["texts"]))
    check("태그 글씨가 날짜와 같은 크기", head["tagFs"] == head["dateFs"] and head["tagFs"] not in ("",), head)
    check("태그에 테두리·바탕 상자 없음", all(b == "0px" for b in (head["borders"] or ["x"]))
          and head["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), (head["borders"], head["bg"]))
    page4.screenshot(path=os.path.join(SHOT, "photo-list-v39.png"))

    # 태그가 없는 날 — 사진 한 장을 앨범 이름 없이 넣고 「+ 태그」로 달아 보기
    page4.evaluate("""() => {
      const st = window.__app.state;
      const d = new Date();
      const x = new Date(d.getFullYear(), d.getMonth(), d.getDate() - 60);
      const ds = x.getFullYear() + '-' + String(x.getMonth() + 1).padStart(2, '0') + '-' + String(x.getDate()).padStart(2, '0');
      st.photos.push({ id: 'v39-untagged', date: ds, album: '', title: '', art: 1, capBg: '' });
      window.__app.rerender();
    }""")
    page4.wait_for_timeout(700)
    empty = page4.evaluate("""() => ({empty: document.querySelectorAll('#s-photo .pday-tag.empty').length,
      dots: document.querySelectorAll('#s-photo .pday-dot').length,
      labeled: [...document.querySelectorAll('#s-photo .pday-tag.empty')].map(b => b.textContent.trim())})""")
    check("태그 없는 날은 「+ 태그」로 바로 달 수 있음", empty["empty"] == 1 and empty["labeled"] == ["+ 태그"], empty)

    page4.locator("#s-photo .pday-tag.empty").first.click()
    page4.wait_for_timeout(520)
    page4.fill("#sheet input[name=tag]", "빼빼로데이")
    page4.locator("#sheet button.btn-primary").click()
    page4.wait_for_timeout(760)
    tagd = page4.evaluate("""() => {
      const tags = [...document.querySelectorAll('#s-photo .pday-tag')];
      const tag = tags.filter(t => t.textContent.trim() === '빼빼로데이')[0] || null;
      const h = tag ? tag.closest('.pday-hd') : null;
      const d = h ? h.querySelector('.d') : null;
      const dot = h ? h.querySelector('.pday-dot') : null;
      const cs = tag ? getComputedStyle(tag) : null, ds = d ? getComputedStyle(d) : null;
      return {text: h ? [...h.children].map(c => c.textContent.trim()).filter(Boolean).join(' ') : '',
              dateText: d ? d.textContent.trim() : '',
              dot: dot ? dot.textContent.trim() : '',
              tagFs: cs ? cs.fontSize : '', dateFs: ds ? ds.fontSize : '',
              borders: cs ? [cs.borderTopWidth, cs.borderBottomWidth] : []};
    }""")
    check("태그를 달면 「날짜 · 태그」로 이어짐", tagd["dot"] == "·" and tagd["tagFs"] == tagd["dateFs"]
          and "빼빼로데이" in tagd["text"], tagd)
    check("새로 단 태그도 테두리 없이 글씨로", all(b == "0px" for b in (tagd["borders"] or ["x"])), tagd["borders"])

    # 태그를 누르면 그대로 고치기
    page4.locator("#s-photo .pday-tag", has_text="빼빼로데이").first.click()
    page4.wait_for_timeout(520)
    val = page4.evaluate("() => (document.querySelector('#sheet input[name=tag]') || {}).value")
    check("태그를 누르면 고치기 시트에 그 태그가 들어 있음", val == "빼빼로데이", val)
    page4.locator("#sheet [data-close]").first.click()
    page4.wait_for_timeout(400)

    # 날짜 정렬 — 가장 최근 날짜가 맨 아래
    order = page4.evaluate("""() => {
      const days = [...document.querySelectorAll('#s-photo .pday')];
      const st = window.__app.state.photos;
      return days.map(d => d.querySelector('.pday-hd').getAttribute('data-date'));
    }""")
    check("목록은 예전 날짜가 위 · 최근 날짜가 아래", order == sorted(order) and len(order) >= 2, order)

    # 3일 제한 없이 모두 — 날짜를 6개 더 넣어도 잘리지 않고 다 그려지며 스크롤됨
    page4.evaluate("""() => {
      const st = window.__app.state;
      const d = new Date();
      const day = (n) => { const x = new Date(d.getFullYear(), d.getMonth(), d.getDate() - n);
        return x.getFullYear() + '-' + String(x.getMonth() + 1).padStart(2, '0') + '-' + String(x.getDate()).padStart(2, '0'); };
      [1, 2, 3, 4, 40, 200].forEach((n, i) => {
        st.photos.push({ id: 'v39-many-' + i, date: day(n), album: '', title: '검사' + i, art: i, capBg: '' });
      });
      window.__app.rerender();
    }""")
    page4.wait_for_timeout(800)
    many = page4.evaluate("""() => {
      const days = [...document.querySelectorAll('#s-photo .pday')];
      const dates = days.map(d => d.querySelector('.pday-hd').getAttribute('data-date'));
      const st = window.__app.state.photos.map(p => p.date);
      const uniq = [...new Set(st)].sort();
      const scr = document.getElementById('screens');
      return {rendered: days.length, uniq: uniq.length, dates: dates,
              asc: dates.join() === dates.slice().sort().join(),
              last: dates[dates.length - 1], newest: uniq[uniq.length - 1],
              scrollable: scr.scrollHeight > scr.clientHeight + 40,
              atBottom: (scr.scrollHeight - scr.scrollTop - scr.clientHeight) <= 6,
              perDay: days.map(d => d.querySelectorAll('.pola').length)};
    }""")
    check("사진이 있는 날짜가 하나도 빠지지 않고 모두 그려짐", many["rendered"] == many["uniq"] and many["rendered"] >= 8,
          (many["rendered"], many["uniq"]))
    check("위아래로 쭉 스크롤되는 목록", many["scrollable"] is True, many["scrollable"])
    check("가장 최근 날짜가 맨 아래", many["last"] == many["newest"], (many["last"], many["newest"]))
    check("날짜 순서는 오래된 날 → 최근 날", many["asc"] is True, many["dates"][:4])
    check("날마다 3장까지 (그대로)", all(n <= 3 for n in many["perDay"]), many["perDay"])
    check("목록에 들어오면 맨 아래(가장 최근 날짜)가 보임", many["atBottom"] is True,
          many["atBottom"])
    page4.screenshot(path=os.path.join(SHOT, "photo-list-many-v39.png"))

    # 다른 탭에 갔다가 사진첩으로 돌아와도 맨 아래부터
    tab(page4, 0, 500)
    tab(page4, 3, 700)
    back2 = page4.evaluate("""() => { const scr = document.getElementById('screens');
      return {atBottom: (scr.scrollHeight - scr.scrollTop - scr.clientHeight) <= 12,
              scrollTop: Math.round(scr.scrollTop)}; }""")
    check("사진첩 탭으로 다시 들어와도 맨 아래(최근)부터", back2["atBottom"] is True, back2)

    # 검색 결과도 같은 순서
    page4.locator("#s-photo [data-act=photoSearch]").click()
    page4.wait_for_timeout(520)
    page4.fill("#sheet #photoSearchIn", "검사")
    page4.wait_for_timeout(400)
    sres = page4.evaluate("""() => {
      const b = [...document.querySelectorAll('#sheet .sres')];
      const dates = b.map(x => x.getAttribute('data-date'));
      return {n: dates.length, dates: dates};
    }""")
    check("검색 결과도 예전 날짜가 위 (오름차순)", sres["n"] >= 2 and sres["dates"] == sorted(sres["dates"]), sres)
    page4.locator("#sheet [data-close]").first.click()
    page4.wait_for_timeout(350)
    check("브라우저 콘솔/페이지 오류 없음 (사진 목록)", len(errs4) == 0, errs4[:4])
    ctx4.close()

    browser.close()

print("")
if fails:
    print("실패 %d개:" % len(fails))
    for f in fails:
        print(" - " + f)
    sys.exit(1)
print("실패: 없음")
