"""투로그 v38 확인 — 노트 + 시트 속지 레이아웃 4종 (투두리스트 · 줄글 메모 · 별점 리뷰 · 지출·정산).

1) 버전: sw.js 캐시 twolog-v39 · APP_VERSION v39 · My 탭 「버전 v39」
2) + 시트 하단 「속지 레이아웃」
   - 노트 카테고리 목록(#noteOrderList) 아래 · 「저장하기」 버튼 위
   - 카드 4개 · 2×2 (첫 두 장 같은 줄, 셋째 줄에 두 장) · 각진 네모 · 제목 + 한 줄 설명
   - 이름: 투두리스트 / 줄글 메모 / 별점 리뷰 / 지출·정산
   - 기본값 투두리스트(active) · hidden nkind=check
   - 하나를 고르면 그것만 active · hidden nkind 가 따라감
3) 새 카테고리를 속지별로 만들면 그 속지 화면이 열림
   - check: 진행률 · ○ + Add · 체크하면 완료(취소선)
   - memo: 체크 동그라미 없음 · 메모 카드 · Add 로 제목 추가 · 눌러서 본문 저장
   - review: 별 5개 · 별을 누르면 그 점수 · 이름·장소·날짜·한줄평
   - expense: 위에 합계 · 항목+금액 Add · 합계 자동(24,000 + 28,000 + 9,500 = 61,500원)
4) 기존 카테고리·기본 탭은 그대로
   - 기본 탭 메모·버킷리스트·영화·먹방 동작 · 예전 「메모(kind=memo)」 리스트는 줄글 메모로
   - 예전 체크 리스트는 투두리스트 그대로
5) 카테고리 수정 시트에서 속지를 바꾸면 그 카테고리 화면이 바뀜 (항목은 그대로)
6) Supabase 동기화 — notes(kind=list) payload 에 kind 와 항목 rating·place·date·amount 보존
   (원격 seed → 화면, 화면에서 추가 → 서버 행)
7) 다크 모드에서도 속지 선택 카드·별점이 보임
8) 콘솔/페이지 오류 0건

    python3 tests/v38.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def create_kind(page, name, kind):
    """+ 시트에서 이름을 적고 속지를 고른 뒤 저장 → 그 카테고리가 열립니다."""
    open_add_sheet(page)
    pick_kind(page, kind)
    page.fill("#sheet .nord-new", name)
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(720)


def seg(page):
    return page.evaluate("""() => {
      const on = document.querySelector('#s-diary .lchip.active, #s-diary .seg-btn.active');
      return on ? on.textContent.trim() : '';
    }""")


def state_lists(page):
    return page.evaluate("() => JSON.parse(JSON.stringify(window.__app.state.lists || []))")


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
    # 2. + 시트 — 속지 레이아웃 선택 UI
    # ==================================================================
    note_tab(page)
    open_add_sheet(page)
    ui = page.evaluate("""() => {
      const sheet = document.querySelector('#sheet');
      const list = document.querySelector('#sheet #noteOrderList');
      const sec = [...document.querySelectorAll('#sheet .set-lbl')].filter(e => e.textContent.trim() === '속지 레이아웃')[0] || null;
      const grid = document.querySelector('#sheet .nkind');
      const cards = [...document.querySelectorAll('#sheet .nk-card')];
      const save = document.querySelector('#sheet button.btn-primary');
      const r = e => { if (!e) return null; const b = e.getBoundingClientRect();
        return {top: Math.round(b.top), left: Math.round(b.left), w: Math.round(b.width), h: Math.round(b.height)}; };
      const cs = grid ? getComputedStyle(grid) : null;
      return {
        sec: !!sec, secTop: r(sec) ? r(sec).top : null,
        listBottom: r(list) ? Math.round(r(list).top + r(list).h) : null,
        saveTop: r(save) ? r(save).top : null,
        count: cards.length,
        kinds: cards.map(c => c.getAttribute('data-kind')),
        names: cards.map(c => (c.querySelector('.nk-n') || {}).textContent || ''),
        descs: cards.map(c => ((c.querySelector('.nk-d') || {}).textContent || '').trim()),
        active: cards.filter(c => c.classList.contains('active')).map(c => c.getAttribute('data-kind')),
        cols: cs ? cs.gridTemplateColumns : '',
        radius: cards[0] ? getComputedStyle(cards[0]).borderTopLeftRadius : '',
        hidden: (document.querySelector('#sheet input[name="nkind"]') || {}).value,
        pos: cards.map(c => r(c)),
        order: [...document.querySelectorAll('#sheet > *')].length
      };
    }""")
    check("+ 시트에 「속지 레이아웃」 칸이 있음", ui["sec"] is True, ui.get("sec"))
    check("카테고리 목록(#noteOrderList) 아래에 놓임", ui["listBottom"] is not None and ui["secTop"] >= ui["listBottom"], (ui.get("listBottom"), ui.get("secTop")))
    check("「저장하기」 버튼 위에 놓임", ui["saveTop"] is not None and ui["secTop"] < ui["saveTop"], (ui.get("secTop"), ui.get("saveTop")))
    check("속지 카드는 4개", ui["count"] == 4, ui["kinds"])
    check("속지 이름 — 투두리스트 · 줄글 메모 · 별점 리뷰 · 지출·정산",
          ui["names"] == ["투두리스트", "줄글 메모", "별점 리뷰", "지출·정산"], ui["names"])
    check("속지마다 한 줄 설명", all(len(d) > 3 for d in ui["descs"]), ui["descs"])
    check("2×2 로 놓임 (두 줄 · 한 줄에 두 장)",
          ui["pos"][0]["top"] == ui["pos"][1]["top"] and ui["pos"][2]["top"] > ui["pos"][0]["top"]
          and ui["pos"][2]["top"] == ui["pos"][3]["top"] and ui["pos"][0]["w"] == ui["pos"][1]["w"], ui["pos"])
    check("각진 네모 (모서리 둥글지 않음)", ui["radius"] in ("0px", ""), ui["radius"])
    check("기본값은 투두리스트", ui["active"] == ["check"] and ui["hidden"] == "check", (ui["active"], ui["hidden"]))
    rnd = page.evaluate("""() => {
      const r = s => { const e = document.querySelector(s); return e ? getComputedStyle(e).borderTopLeftRadius : null; };
      return {row: r('#sheet .nord-row'), add: r('#sheet .nord-add-btn'), card: r('#sheet .nk-card'), save: r('#sheet button.btn-primary')};
    }""")
    check("노트 카테고리 줄은 둥근 모서리 (12px)", rnd["row"] in ("12px",), rnd)
    check("추가·속지 카드·저장하기 버튼은 그대로 각짐",
          rnd["add"] in (None, "0px") and rnd["card"] in (None, "0px") and rnd["save"] in (None, "0px"), rnd)
    title_txt = page.evaluate("document.querySelector('#s-diary .note-h1').textContent.trim()")
    check("노트 제목은 이모지 없이 「노트」", title_txt == "노트" and "📖" not in title_txt, title_txt)

    pick_kind(page, "expense")
    one = page.evaluate("""() => ({
      active: [...document.querySelectorAll('#sheet .nk-card.active')].map(c => c.getAttribute('data-kind')),
      hidden: (document.querySelector('#sheet input[name="nkind"]') || {}).value,
      border: getComputedStyle(document.querySelector('#sheet .nk-card.active')).borderTopColor })""")
    check("고른 카드 하나만 active", one["active"] == ["expense"], one)
    check("고르면 hidden nkind 도 따라감", one["hidden"] == "expense", one["hidden"])
    check("고른 카드는 진한 테두리", one["border"] not in ("", "rgb(229, 229, 234)"), one["border"])

    page.evaluate("document.querySelector('#sheet').scrollTop = 9999")
    page.wait_for_timeout(260)
    page.screenshot(path=os.path.join(SHOT, "note-v38-templates.png"))
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(450)

    # ==================================================================
    # 3. 네 가지 속지 — 만들고 화면 확인
    # ==================================================================
    # 3-1) 투두리스트
    create_kind(page, "여행 준비", "check")
    page.fill("#s-diary #listAddForm input[name=text]", "충전기")
    page.locator("#s-diary #listAddForm button").click()
    page.wait_for_timeout(420)
    ck = page.evaluate("""() => ({
      seg: document.querySelector('#s-diary .lchip.active').textContent.trim(),
      kindTag: (document.querySelector('#s-diary .nh-l .k') || {}).textContent,
      prog: !!document.querySelector('#s-diary .progress'),
      forms: document.querySelectorAll('#s-diary #listAddForm').length,
      circ: document.querySelectorAll('#s-diary .todo-items .trow .circ').length,
      quick: document.querySelectorAll('#s-diary #listQuickForm').length,
      memoCards: document.querySelectorAll('#s-diary .memo-card').length })""")
    check("투두리스트 카테고리 — 탭 이름", ck["seg"] == "여행 준비", ck["seg"])
    check("투두리스트 — 속지 이름 표시", ck["kindTag"] == "투두리스트", ck["kindTag"])
    check("투두리스트 — 진행률 · 체크 동그라미 · Add 그대로",
          ck["prog"] and ck["forms"] == 1 and ck["circ"] == 1 and ck["quick"] == 0 and ck["memoCards"] == 0, ck)
    page.locator("#s-diary .todo-items .trow .circ").first.click()
    page.wait_for_timeout(420)
    check("투두리스트 — 체크하면 완료 표시",
          page.evaluate("!!document.querySelector('#s-diary .todo-items .trow.done')") is True)
    page.screenshot(path=os.path.join(SHOT, "note-v38-todo.png"))

    # 3-2) 줄글 메모
    create_kind(page, "생각 정리", "memo")
    page.fill("#s-diary #listQuickForm input[name=text]", "11월에 해보고 싶은 것")
    page.locator("#s-diary #listQuickForm button").click()
    page.wait_for_timeout(460)
    mm = page.evaluate("""() => ({
      seg: document.querySelector('#s-diary .lchip.active').textContent.trim(),
      kindTag: (document.querySelector('#s-diary .nh-l .k') || {}).textContent,
      cards: document.querySelectorAll('#s-diary .memo-card').length,
      title: (document.querySelector('#s-diary .memo-card .mc-t') || {}).textContent,
      circ: document.querySelectorAll('#s-diary .trow .circ').length,
      prog: !!document.querySelector('#s-diary .progress'),
      date: ((document.querySelector('#s-diary .memo-card .mc-d') || {}).textContent || '').trim() })""")
    check("줄글 메모 — 속지 이름 표시", mm["kindTag"] == "줄글 메모", mm["kindTag"])
    check("줄글 메모 — 메모 카드로 보임", mm["cards"] == 1 and mm["title"] == "11월에 해보고 싶은 것", mm)
    check("줄글 메모 — 체크 동그라미·진행률 없음", mm["circ"] == 0 and mm["prog"] is False, mm)
    check("줄글 메모 — 카드에 날짜", re.match(r"^\d{4}\.\d{2}\.\d{2}$", mm["date"] or "") is not None, mm["date"])
    page.locator("#s-diary .memo-card").first.click()
    page.wait_for_timeout(480)
    check("줄글 메모 — 눌러서 본문 쓰기 시트",
          page.evaluate("""() => !!document.querySelector('#sheet textarea[name=memo]') &&
            document.querySelector('#sheet h2').textContent.indexOf('메모') >= 0""") is True)
    page.fill("#sheet textarea[name=memo]", "주말마다 한 번은 산책하기.\n사진도 한 장씩 남기기.")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(560)
    body = page.evaluate("(document.querySelector('#s-diary .memo-card .mc-b') || {}).textContent || ''")
    check("줄글 메모 — 본문이 카드에 그대로", "주말마다 한 번은 산책하기." in body and "사진도 한 장씩" in body, body[:40])
    page.screenshot(path=os.path.join(SHOT, "note-v38-memo.png"))

    # 3-3) 별점 리뷰
    create_kind(page, "맛집 기록", "review")
    for nm in ["성수 카페 온도", "을지로 노포"]:
        page.fill("#s-diary #listQuickForm input[name=text]", nm)
        page.locator("#s-diary #listQuickForm button").click()
        page.wait_for_timeout(430)
    rv = page.evaluate("""() => ({
      kindTag: (document.querySelector('#s-diary .nh-l .k') || {}).textContent,
      cards: document.querySelectorAll('#s-diary .rv-card').length,
      stars: document.querySelectorAll('#s-diary .rv-card .rvs').length,
      on: document.querySelectorAll('#s-diary .rv-card .rvs.on').length,
      circ: document.querySelectorAll('#s-diary .trow .circ').length })""")
    check("별점 리뷰 — 속지 이름 표시", rv["kindTag"] == "별점 리뷰", rv["kindTag"])
    check("별점 리뷰 — 카드마다 별 5개", rv["cards"] == 2 and rv["stars"] == 10, rv)
    check("별점 리뷰 — 처음엔 별점 없음", rv["on"] == 0, rv["on"])
    # 첫 카드 4점, 둘째 카드 5점
    page.locator("#s-diary .rv-card").nth(0).locator(".rvs").nth(3).click()
    page.wait_for_timeout(430)
    page.locator("#s-diary .rv-card").nth(1).locator(".rvs").nth(4).click()
    page.wait_for_timeout(430)
    stars = page.evaluate("""() => [...document.querySelectorAll('#s-diary .rv-card')]
      .map(c => c.querySelectorAll('.rvs.on').length)""")
    check("별점 리뷰 — 별을 누르면 그 점수로", stars == [4, 5], stars)
    check("별점 리뷰 — 누른 별은 강조색",
          page.evaluate("getComputedStyle(document.querySelector('#s-diary .rvs.on')).color")
          != page.evaluate("getComputedStyle(document.querySelector('#s-diary .rvs:not(.on)')).color"))
    # 이름·장소·날짜·한줄평
    page.locator("#s-diary .rv-card").nth(0).locator(".rv-t").click()
    page.wait_for_timeout(480)
    form = page.evaluate("""() => ({
      title: document.querySelector('#sheet h2').textContent,
      fstars: document.querySelectorAll('#sheet .fstar').length,
      rating: (document.querySelector('#sheet input[name=rating]') || {}).value,
      place: !!document.querySelector('#sheet input[name=place]'),
      date: !!document.querySelector('#sheet input[name=date]'),
      memo: !!document.querySelector('#sheet textarea[name=memo]') })""")
    check("리뷰 시트 — 별점·장소·날짜·한줄평 칸", form["fstars"] == 5 and form["place"] and form["date"] and form["memo"], form)
    check("리뷰 시트 — 저장된 별점이 채워져 있음 (4점)", form["rating"] == "4", form["rating"])
    page.fill("#sheet input[name=place]", "성수 · 연무장길")
    page.fill("#sheet textarea[name=memo]", "라떼가 진하고 조용해요.")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(560)
    meta = page.evaluate("""() => ({
      meta: (document.querySelector('#s-diary .rv-card .rv-meta') || {}).textContent || '',
      note: (document.querySelector('#s-diary .rv-card .rv-note') || {}).textContent || '',
      on: document.querySelectorAll('#s-diary .rv-card')[0].querySelectorAll('.rvs.on').length })""")
    check("별점 리뷰 — 장소가 카드에", "성수" in meta["meta"], meta["meta"])
    check("별점 리뷰 — 한줄평이 카드에", "라떼가 진하고" in meta["note"], meta["note"])
    check("별점 리뷰 — 저장 뒤에도 별점 4", meta["on"] == 4, meta["on"])
    page.screenshot(path=os.path.join(SHOT, "note-v38-review.png"))

    # 3-4) 지출·정산
    create_kind(page, "데이트 통장", "expense")
    for nm, am in [("점심", "24000"), ("영화표", "28000"), ("커피", "9,500")]:
        page.fill("#s-diary #listQuickForm input[name=text]", nm)
        page.fill("#s-diary #listQuickForm input[name=amount]", am)
        page.locator("#s-diary #listQuickForm button").click()
        page.wait_for_timeout(430)
    ex = page.evaluate("""() => ({
      kindTag: (document.querySelector('#s-diary .nh-l .k') || {}).textContent,
      sum: (document.querySelector('#s-diary .ex-sum .v') || {}).textContent,
      cnt: (document.querySelector('#s-diary .ex-sum .c') || {}).textContent,
      rows: [...document.querySelectorAll('#s-diary .ex-row')].map(r => [
        r.querySelector('.ex-t').textContent, r.querySelector('.ex-a').textContent]),
      amountFields: document.querySelectorAll('#s-diary #listQuickForm input[name=amount]').length })""")
    check("지출·정산 — 속지 이름 표시", ex["kindTag"] == "지출·정산", ex["kindTag"])
    check("지출·정산 — 맨 위에 합계", ex["sum"] == "61,500원", ex["sum"])
    check("지출·정산 — 건수 표시", ex["cnt"] == "3건", ex["cnt"])
    check("지출·정산 — 항목과 금액", ex["rows"] == [["점심", "24,000원"], ["영화표", "28,000원"], ["커피", "9,500원"]], ex["rows"])
    check("지출·정산 — 빠른 추가에 금액 칸", ex["amountFields"] == 1, ex["amountFields"])
    page.screenshot(path=os.path.join(SHOT, "note-v38-expense.png"))

    # 합계는 항목을 지우면 바로 다시 계산
    page.locator("#s-diary .ex-row").nth(2).locator(".x").click()
    page.wait_for_timeout(500)
    check("지출·정산 — 항목을 지우면 합계도 다시",
          page.evaluate("document.querySelector('#s-diary .ex-sum .v').textContent") == "52,000원",
          page.evaluate("document.querySelector('#s-diary .ex-sum .v').textContent"))

    # 지출 항목 수정 시트
    page.locator("#s-diary .ex-row").first.locator(".ex-t").click()
    page.wait_for_timeout(470)
    check("지출 시트 — 항목·금액 칸",
          page.evaluate("""() => !!document.querySelector('#sheet input[name=amount]') &&
            document.querySelector('#sheet input[name=amount]').value === '24000'""") is True)
    page.fill("#sheet input[name=amount]", "31000")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(540)
    check("지출 — 고친 금액이 합계에 반영 (59,000원)",
          page.evaluate("document.querySelector('#s-diary .ex-sum .v').textContent") == "59,000원",
          page.evaluate("document.querySelector('#s-diary .ex-sum .v').textContent"))

    # ==================================================================
    # 4. 기존 카테고리 · 기본 탭은 그대로
    # ==================================================================
    st = state_lists(page)
    kinds = {l["title"]: l["kind"] for l in st}
    check("새 카테고리 4개가 고른 속지로 저장됨",
          kinds.get("여행 준비") == "check" and kinds.get("생각 정리") == "memo"
          and kinds.get("맛집 기록") == "review" and kinds.get("데이트 통장") == "expense", kinds)
    check("예전 「주말 데이트」 메모 리스트가 그대로 (kind=memo)",
          kinds.get("주말 데이트") == "memo", kinds)
    check("예전 체크 리스트 「여행 준비물」 그대로",
          any(l["title"] == "여행 준비물" and l["kind"] == "check" for l in st),
          [(l["title"], l["kind"]) for l in st])

    note_tab(page)
    tabnames = page.evaluate("[...document.querySelectorAll('#s-diary .seg-btn, #s-diary .lchip')].map(b => b.textContent.trim())")
    check("기본 탭 3개 + 내 카테고리 6개가 모두 남아 있음", len(tabnames) == 9, tabnames)

    # 예전 memo 리스트 → 줄글 메모 화면
    page.locator("#s-diary .lchip", has_text="주말 데이트").first.click()
    page.wait_for_timeout(520)
    old_memo = page.evaluate("""() => ({
      kindTag: (document.querySelector('#s-diary .nh-l .k') || {}).textContent,
      cards: document.querySelectorAll('#s-diary .memo-card').length,
      items: (window.__app.state.lists.filter(l => l.title === '주말 데이트')[0] || {items: []}).items.length })""")
    check("예전 메모 리스트는 줄글 메모로 열림", old_memo["kindTag"] == "줄글 메모", old_memo)
    check("예전 메모 항목이 카드로 보임", old_memo["cards"] == old_memo["items"] and old_memo["items"] > 0, old_memo)

    # 기본 탭(메모·버킷리스트·영화·먹방) 그대로
    for name, idx, sel in [("메모", 0, "#s-diary .ncard"), ("버킷리스트", 1, "#s-diary .ncard"),
                           ("영화·먹방", 2, "#s-diary .ncard")]:
        page.locator("#s-diary .seg-btn").nth(idx).click()
        page.wait_for_timeout(450)
        n = page.evaluate("document.querySelectorAll('%s').length" % sel)
        check("기본 탭 「%s」 카드 그대로" % name, n > 0, n)

    # ==================================================================
    # 5. 카테고리 수정 시트 — 속지 바꾸기
    # ==================================================================
    page.locator("#s-diary .lchip", has_text="생각 정리").first.click()
    page.wait_for_timeout(420)
    page.evaluate("""() => {
      const l = window.__app.state.lists.filter(x => x.title === '생각 정리')[0];
      window.__app.state.ui.seg = 'list:' + l.id;
    }""")
    # 카테고리 수정은 editList 액션 — + 시트의 「카테고리 수정」과 같은 시트를 씁니다
    page.evaluate("() => window.__app.rerender()")
    page.wait_for_timeout(400)
    open_add_sheet(page)
    edit_ui = page.evaluate("""() => ({
      active: [...document.querySelectorAll('#sheet .nk-card.active')].map(c => c.getAttribute('data-kind')),
      target: (document.querySelector('#sheet input[name="nkind_target"]') || {}).value || '',
      title: document.querySelector('#sheet h2').textContent })""")
    check("+ 시트는 새 카테고리용 — 속지 기본값 투두리스트", edit_ui["active"] == ["check"], edit_ui)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # 카테고리 수정 시트 (editList)
    page.evaluate("""() => {
      const l = window.__app.state.lists.filter(x => x.title === '생각 정리')[0];
      const b = document.createElement('button');
      b.setAttribute('data-act', 'editList'); b.setAttribute('data-id', l.id);
      document.querySelector('#s-diary').appendChild(b); b.click(); b.remove();
    }""")
    page.wait_for_timeout(560)
    ed = page.evaluate("""() => ({
      title: document.querySelector('#sheet h2').textContent,
      active: [...document.querySelectorAll('#sheet .nk-card.active')].map(c => c.getAttribute('data-kind')),
      target: (document.querySelector('#sheet input[name="nkind_target"]') || {}).value || '' })""")
    check("카테고리 수정 시트에 그 카테고리의 속지가 선택돼 있음", ed["active"] == ["memo"] and ed["title"] == "카테고리 수정", ed)
    pick_kind(page, "review")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(700)
    changed = page.evaluate("""() => ({
      kind: (window.__app.state.lists.filter(x => x.title === '생각 정리')[0] || {}).kind,
      cards: document.querySelectorAll('#s-diary .rv-card').length,
      items: (window.__app.state.lists.filter(x => x.title === '생각 정리')[0] || {items: []}).items.length,
      title: document.querySelector('#s-diary .lchip.active').textContent.trim() })""")
    check("속지를 바꾸면 그 카테고리가 리뷰 화면이 됨", changed["kind"] == "review" and changed["cards"] == changed["items"], changed)
    check("속지를 바꿔도 항목과 이름은 그대로", changed["items"] == 1 and changed["title"] == "생각 정리", changed)

    check("브라우저 콘솔/페이지 오류 없음 (로컬)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 6. Supabase 동기화 — kind · rating · place · date · amount 보존
    # ==================================================================
    cid, uid2, mail = "couple-v38", "user-v38", "v38@twolog.app"
    seed_notes = [
        {"id": "L1", "couple_id": cid, "kind": "list", "sort": 0, "deleted": False,
         "payload": {"title": "맛집", "emoji": "", "kind": "review",
                     "items": [{"id": "i1", "text": "성수 카페", "memo": "조용해요", "done": False,
                                "rating": 4, "place": "성수", "date": "2026-11-20"}]}},
        {"id": "L2", "couple_id": cid, "kind": "list", "sort": 1, "deleted": False,
         "payload": {"title": "가계부", "emoji": "", "kind": "expense",
                     "items": [{"id": "i2", "text": "점심", "memo": "", "done": False,
                                "amount": 12000, "date": "2026-11-21"}]}},
        {"id": "L3", "couple_id": cid, "kind": "list", "sort": 2, "deleted": False,
         "payload": {"title": "생각", "emoji": "", "kind": "memo",
                     "items": [{"id": "i3", "text": "제목", "memo": "본문", "done": False}]}},
        {"id": "L4", "couple_id": cid, "kind": "list", "sort": 3, "deleted": False,
         "payload": {"title": "예전 체크", "emoji": "✅", "kind": "check",
                     "items": [{"id": "i4", "text": "우산", "memo": "", "done": True}]}},
    ]
    db2 = remote_db(cid, uid2, mail, seed_notes)
    ctx2 = new_ctx(browser)
    ctx2.add_init_script(remote_seed(db2, uid2, mail))
    page2 = ctx2.new_page()
    errs2 = []
    watch(page2, errs2)
    stub_route(page2)
    page2.goto(URL, wait_until="domcontentloaded")
    page2.wait_for_selector("#tabbar .tab", timeout=25000)
    page2.wait_for_timeout(2600)
    tab(page2, 2, 700)
    remote = page2.evaluate("() => JSON.parse(JSON.stringify(window.__app.state.lists || []))")
    by = {l["title"]: l for l in remote}
    check("원격 리뷰 리스트 — kind 가 review 로 살아남", by.get("맛집", {}).get("kind") == "review",
          {k: v.get("kind") for k, v in by.items()})
    item1 = (by.get("맛집", {}).get("items") or [{}])[0]
    check("원격 리뷰 항목 — 별점·장소·날짜 보존",
          item1.get("rating") == 4 and item1.get("place") == "성수" and item1.get("date") == "2026-11-20"
          and item1.get("memo") == "조용해요", item1)
    check("원격 지출 리스트 — kind·금액 보존",
          by.get("가계부", {}).get("kind") == "expense" and (by.get("가계부", {}).get("items") or [{}])[0].get("amount") == 12000,
          by.get("가계부"))
    check("원격 메모·체크 리스트 — 예전 값 그대로",
          by.get("생각", {}).get("kind") == "memo" and by.get("예전 체크", {}).get("kind") == "check"
          and (by.get("예전 체크", {}).get("items") or [{}])[0].get("done") is True,
          {k: v.get("kind") for k, v in by.items()})

    # 화면에도 그 속지로
    page2.locator("#s-diary .lchip", has_text="맛집").first.click()
    page2.wait_for_timeout(520)
    check("원격 리뷰 리스트 화면 — 별 4개가 켜져 있음",
          page2.evaluate("document.querySelectorAll('#s-diary .rv-card .rvs.on').length") == 4,
          page2.evaluate("document.querySelectorAll('#s-diary .rv-card .rvs.on').length"))
    page2.locator("#s-diary .lchip", has_text="가계부").first.click()
    page2.wait_for_timeout(520)
    check("원격 지출 리스트 화면 — 합계 12,000원",
          page2.evaluate("(document.querySelector('#s-diary .ex-sum .v') || {}).textContent") == "12,000원",
          page2.evaluate("(document.querySelector('#s-diary .ex-sum .v') || {}).textContent"))

    # 화면에서 한 줄 더 → 서버 notes 행에 kind·필드가 담겨 올라감
    page2.fill("#s-diary #listQuickForm input[name=text]", "택시")
    page2.fill("#s-diary #listQuickForm input[name=amount]", "8000")
    page2.locator("#s-diary #listQuickForm button").click()
    page2.wait_for_timeout(1800)
    row = page2.evaluate("""() => {
      const r = (window.__stub.notes || []).filter(x => x.id === 'L2')[0] || null;
      return r ? {payload: r.payload, kind: r.kind} : null;
    }""")
    p2 = (row or {}).get("payload") or {}
    newitem = [it for it in (p2.get("items") or []) if it.get("text") == "택시"]
    check("서버 notes 행 kind=list · payload.kind=expense", row and row["kind"] == "list" and p2.get("kind") == "expense", p2.get("kind"))
    check("새 지출 항목의 amount·date 가 서버 payload 에 있음",
          bool(newitem) and newitem[0].get("amount") == 8000 and bool(newitem[0].get("date")), newitem)

    # 리뷰 별점을 화면에서 바꾸면 서버 payload 에도 rating
    page2.locator("#s-diary .lchip", has_text="맛집").first.click()
    page2.wait_for_timeout(500)
    page2.locator("#s-diary .rv-card .rvs").nth(4).click()
    page2.wait_for_timeout(1800)
    rr = page2.evaluate("""() => {
      const r = (window.__stub.notes || []).filter(x => x.id === 'L1')[0] || null;
      return r ? r.payload : null;
    }""")
    it1 = ((rr or {}).get("items") or [{}])[0]
    check("별점을 바꾸면 서버 payload rating 도 5", (rr or {}).get("kind") == "review" and it1.get("rating") == 5, it1)
    check("별점 바꿔도 장소·날짜는 남아 있음",
          it1.get("place") == "성수" and it1.get("date") == "2026-11-20", it1)

    # 새로고침해도 그대로 (서버에서 되살아남)
    page2.reload(wait_until="domcontentloaded")
    page2.wait_for_selector("#tabbar .tab", timeout=25000)
    page2.wait_for_timeout(2400)
    tab(page2, 2, 700)
    again = page2.evaluate("() => JSON.parse(JSON.stringify(window.__app.state.lists || []))")
    ag = {l["title"]: l for l in again}
    agi = (ag.get("맛집", {}).get("items") or [{}])[0]
    check("새로고침 뒤에도 리뷰 별점 5 · 장소 그대로", agi.get("rating") == 5 and agi.get("place") == "성수", agi)
    check("새로고침 뒤에도 지출 합계 항목 2건",
          len(ag.get("가계부", {}).get("items") or []) == 2, ag.get("가계부"))
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errs2) == 0, errs2[:4])
    ctx2.close()

    # ==================================================================
    # 7. 다크 모드 — 속지 선택 카드 · 별점이 보임
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
    page3.wait_for_timeout(800)
    page3.evaluate("document.documentElement.setAttribute('data-mode', 'dark')")
    page3.wait_for_timeout(300)
    note_tab(page3)
    create_kind(page3, "밤 리뷰", "review")
    page3.fill("#s-diary #listQuickForm input[name=text]", "야식집")
    page3.locator("#s-diary #listQuickForm button").click()
    page3.wait_for_timeout(430)
    page3.locator("#s-diary .rv-card .rvs").nth(2).click()
    page3.wait_for_timeout(430)
    dk = page3.evaluate("""() => {
      const on = document.querySelector('#s-diary .rvs.on'), off = document.querySelector('#s-diary .rvs:not(.on)');
      return { on: on ? getComputedStyle(on).color : '', off: off ? getComputedStyle(off).color : '' };
    }""")
    check("다크 모드에서도 켜진 별은 강조색", dk["on"] not in ("", dk["off"]), dk)
    open_add_sheet(page3)
    page3.evaluate("document.querySelector('#sheet').scrollTop = 9999")
    page3.wait_for_timeout(250)
    dks = page3.evaluate("""() => {
      const c = document.querySelector('#sheet .nk-card'), a = document.querySelector('#sheet .nk-card.active');
      return { visible: !!c && c.getBoundingClientRect().height > 40,
               border: a ? getComputedStyle(a).borderTopColor : '' };
    }""")
    check("다크 모드 + 시트 — 속지 카드가 보임", dks["visible"] is True, dks)
    page3.screenshot(path=os.path.join(SHOT, "note-v38-dark.png"))
    check("브라우저 콘솔/페이지 오류 없음 (다크)", len(errs3) == 0, errs3[:4])
    ctx3.close()

    # ==================================================================
    # 8. 노트 카드 제목은 띠 색과 상관없이 검정 · 캘린더 좌우 밀기 반응
    # ==================================================================
    ctx5 = new_ctx(browser)
    ctx5.add_init_script("window.__TWOLOG_MODE = 'local';")
    page5 = ctx5.new_page()
    errs5 = []
    watch(page5, errs5)
    page5.goto(URL + "?demo=1", wait_until="networkidle")
    page5.wait_for_timeout(700)
    seed5 = page5.evaluate("JSON.stringify(window.__app.state)")
    page5.goto(URL, wait_until="domcontentloaded")
    page5.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed5)
    page5.reload(wait_until="networkidle")
    page5.wait_for_timeout(800)
    tab(page5, 2, 650)
    plain_col = page5.evaluate("getComputedStyle(document.querySelector('#s-diary .nc-hd .nc-t')).color")
    page5.evaluate("""() => { const g = window.__app.state.groups.todo[0];
      g.titleBg = '#EFD353'; window.__app.rerender(); }""")
    page5.wait_for_timeout(500)
    tint = page5.evaluate("""() => { const h = document.querySelector('#s-diary .ncard .nc-hd');
      const t = h ? h.querySelector('.nc-t') : null;
      return {bg: h ? getComputedStyle(h).backgroundColor : '', col: t ? getComputedStyle(t).color : ''}; }""")
    check("카드 제목 — 기본 띠에서도 검정", plain_col == "rgb(17, 17, 17)", plain_col)
    check("카드 제목 — 색 띠에서도 검정", tint["col"] == "rgb(17, 17, 17)" and tint["bg"] == "rgb(239, 211, 83)", tint)
    page5.evaluate("""() => { window.__app.state.groups.todo[0].titleBg = ''; window.__app.rerender(); }""")

    # 캘린더: 화면 어디를 좌우로 밀어도(달력 칸이 아니어도) 달이 넘어감 — 32px 부터
    tab(page5, 1, 650)
    def cal_month():
        return page5.evaluate("document.querySelector('#s-cal .cal-month').textContent.trim()")

    def cal_swipe(dx, sel="#s-cal"):
        page5.evaluate("""([sel, dx]) => {
          const el = document.querySelector(sel);
          const t = (x) => new Touch({identifier: 1, target: el, clientX: x, clientY: 420});
          el.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, cancelable: true,
            touches: [t(200)], changedTouches: [t(200)]}));
          el.dispatchEvent(new TouchEvent('touchend', {bubbles: true, cancelable: true,
            touches: [], changedTouches: [t(200 + dx)]}));
        }""", [sel, dx])
        page5.wait_for_timeout(520)

    m0 = cal_month()
    cal_swipe(-40)
    m1 = cal_month()
    check("캘린더 — 40px만 옆으로 밀어도 다음 달", m1 != m0, (m0, m1))
    cal_swipe(40)
    m2 = cal_month()
    check("캘린더 — 반대로 밀면 이전 달", m2 == m0, (m1, m2))
    cal_swipe(-20)
    check("캘린더 — 20px 살짝 밀면 그대로 (누른 날짜 선택 유지)", cal_month() == m0, cal_month())
    # 달력 칸이 아닌 아래쪽(지난 일정) 영역에서도
    cal_swipe(-60, "#s-cal .daypanel")
    check("캘린더 — 달력 칸이 아닌 아래 영역을 밀어도 넘어감", cal_month() != m0, cal_month())
    check("브라우저 콘솔/페이지 오류 없음 (카드 제목·캘린더)", len(errs5) == 0, errs5[:4])
    ctx5.close()

    # ==================================================================
    # 7. 사진날짜 모아보기(3열) → 꽉 채운 크게 보기 → 다시 모아보기
    #    (v38: 폴라로이드·날짜 줄·달력 칸은 바로 크게 보기가 아니라 그날 모음)
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
    page4.wait_for_timeout(800)
    tab(page4, 3, 700)

    list_shots = page4.evaluate("document.querySelectorAll('#s-photo .pola').length")
    check("기본 사진첩은 최근 날짜 3장까지 미리보기 그대로", list_shots >= 1, list_shots)
    # v39: 목록은 예전 → 최근 순 — 사진이 가장 많은 «최근 날짜»(맨 아래)를 봅니다
    page4.locator("#s-photo .pola").last.click()
    page4.wait_for_timeout(700)
    day = page4.evaluate("""() => {
      const g = document.querySelector('#s-photo .dgrid');
      const cs = g ? getComputedStyle(g) : null;
      const cells = [...document.querySelectorAll('#s-photo .dg-cell')];
      const rr = cells.length ? cells[0].getBoundingClientRect() : null;
      const hd = document.querySelector('#s-photo .dgal-hd');
      return {grid: !!g, cells: cells.length,
              cols: cs ? cs.gridTemplateColumns.split(' ').length : 0,
              gap: cs ? cs.gap : '',
              box: rr ? [Math.round(rr.width), Math.round(rr.height)] : null,
              title: (document.querySelector('#s-photo .dgal-tt h1') || {}).textContent || '',
              year: (document.querySelector('#s-photo .dgal-y') || {}).textContent || '',
              meta: (document.querySelector('#s-photo .dgal-meta') || {}).textContent || '',
              back: !!document.querySelector('#s-photo [data-act="photoDayBack"]'),
              plus: !!document.querySelector('#s-photo [data-act="addPhotoDay"]'),
              plusDate: (document.querySelector('#s-photo [data-act="addPhotoDay"]') || {}).getAttribute ? document.querySelector('#s-photo [data-act="addPhotoDay"]').getAttribute('data-date') : '',
              sheet: document.getElementById('sheetWrap').classList.contains('open'),
              hdTop: hd ? Math.round(hd.getBoundingClientRect().top) : -1};
    }""")
    check("사진을 누르면 그날 모아보기가 먼저 (크게 보기 아님)", day["grid"] and day["cells"] == 6 and day["sheet"] is False, day)
    check("그날 사진이 3열 정사각 격자", day["cols"] == 3 and day["gap"] in ("2px", "3px")
          and abs(day["box"][0] - day["box"][1]) <= 1, day)
    check("위에 ‹ 뒤로 · 날짜 제목 · + 사진 추가", day["back"] and day["plus"] and re.match(r"^\d{1,2}월 \d{1,2}일$", day["title"]) is not None
          and "년" in day["year"], (day["title"], day["year"]))
    check("날짜 아래 「총 6장」", "총 6장" in day["meta"], day["meta"])
    page4.screenshot(path=os.path.join(SHOT, "photo-v38-daygrid.png"))

    # 모아보기 사진을 누르면 → 화면을 꽉 채운 크게 보기
    page4.locator("#s-photo .dg-cell").first.click()
    page4.wait_for_timeout(700)
    big = page4.evaluate("""() => {
      const v = document.querySelector('#sheet .pview');
      if (!v) return {ok: false};
      const r = v.getBoundingClientRect();
      const im = v.querySelector('img, svg');
      const cs = im ? getComputedStyle(im) : null;
      return {ok: true, w: Math.round(r.width), h: Math.round(r.height),
              full: document.getElementById('sheetWrap').classList.contains('sheet-full'),
              fit: cs ? cs.objectFit : '',
              date: (document.querySelector('#sheet .pv-da') || {}).textContent || '',
              bar: !!document.querySelector('#sheet .pv-bar'),
              edit: !!document.querySelector('#sheet [data-act="photoEdit"]'),
              del: !!document.querySelector('#sheet [data-act="photoDelete"]'),
              close: !!document.querySelector('#sheet .pv-x'),
              vh: window.innerHeight};
    }""")
    check("사진을 누르면 화면을 꽉 채운 크게 보기", big["ok"] and big["full"] and big["w"] == 390, big)
    check("크게 보기는 세로로도 크게 (화면의 60% 이상)", big["h"] >= int(big["vh"] * 0.6), (big["h"], big["vh"]))
    check("사진은 잘리지 않게 contain", big["fit"] == "contain", big["fit"])
    check("위에 닫기·날짜 / 아래에 캡션·수정·삭제 바", big["close"] and "년" in big["date"] and big["bar"] and big["edit"] and big["del"], big)
    page4.screenshot(path=os.path.join(SHOT, "photo-v38-viewer.png"))

    page4.locator("#sheet [data-close]").first.click()
    page4.wait_for_timeout(600)
    back4 = page4.evaluate("""() => ({sheet: document.getElementById('sheetWrap').classList.contains('open'),
      cells: document.querySelectorAll('#s-photo .dg-cell').length,
      grid: !!document.querySelector('#s-photo .dgrid')})""")
    check("크게 보기를 닫으면 그날 모아보기로 돌아옴", back4["sheet"] is False and back4["grid"] and back4["cells"] == 6, back4)

    # 날짜 줄을 눌러도 모아보기
    page4.locator('#s-photo [data-act="photoDayBack"]').click()
    page4.wait_for_timeout(500)
    page4.locator("#s-photo .pday-hd .d").last.click()   # 날짜 글씨(태그가 아닌 곳)를 누름 — 최근 날짜
    page4.wait_for_timeout(600)
    check("날짜 줄을 눌러도 그날 모아보기", page4.evaluate("document.querySelectorAll('#s-photo .dg-cell').length") == 6,
          page4.evaluate("document.querySelectorAll('#s-photo .dg-cell').length"))
    page4.locator('#s-photo [data-act="photoDayBack"]').click()
    page4.wait_for_timeout(450)
    check("뒤로 가면 기본 사진 화면", page4.evaluate("document.querySelectorAll('#s-photo .pola').length") >= 1)

    # 사진 달력의 날짜 칸 → 모아보기 (v38: 세로로 이어진 달력)
    page4.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page4.wait_for_timeout(800)
    page4.screenshot(path=os.path.join(SHOT, "photo-cal-v38.png"))
    page4.locator('#s-photo .pcell.has').first.click()
    page4.wait_for_timeout(650)
    cal4 = page4.evaluate("""() => ({cells: document.querySelectorAll('#s-photo .dg-cell').length,
      sheet: document.getElementById('sheetWrap').classList.contains('open'),
      cal: !!document.querySelector('#s-photo .pcal')})""")
    check("달력의 날짜 칸을 누르면 바로 뷰어가 아니라 모아보기", cal4["cells"] >= 1 and cal4["sheet"] is False, cal4)
    page4.locator('#s-photo [data-act="photoDayBack"]').click()
    page4.wait_for_timeout(500)
    check("모아보기에서 뒤로 가면 보던 달력으로", page4.evaluate("!!document.querySelector('#s-photo .pcal')") is True)
    page4.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page4.wait_for_timeout(500)

    # 모아보기의 + — 그 날짜로 사진 추가
    page4.locator("#s-photo .pola").first.click()
    page4.wait_for_timeout(600)
    day_date = page4.evaluate("document.querySelector('#s-photo .dgrid').getAttribute('data-day')")
    jpg_path = os.path.join("/tmp", "v38-photo.jpg")
    with open(jpg_path, "wb") as f:
        f.write(bytes.fromhex(
            "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9"))
    page4.locator('#s-photo [data-act="addPhotoDay"]').click()
    page4.wait_for_timeout(400)
    page4.set_input_files("#photoInput", [jpg_path])
    page4.wait_for_timeout(700)
    add_date = page4.evaluate("(document.querySelector('#sheet input[name=date]') || {}).value || ''")
    check("모아보기의 + 는 그 날짜로 사진 추가 시트", add_date == day_date, (add_date, day_date))
    page4.keyboard.press("Escape")
    page4.wait_for_timeout(400)
    check("브라우저 콘솔/페이지 오류 없음 (사진)", len(errs4) == 0, errs4[:4])
    ctx4.close()

    # ==================================================================
    # 9. 사진 추가 시트 — 앨범 없음 · 날짜 맨 위 · 줄마다 「삭제」 · 목록 위 「추가」
    # ==================================================================
    ctx6 = new_ctx(browser)
    ctx6.add_init_script("window.__TWOLOG_MODE = 'local';")
    page6 = ctx6.new_page()
    errs6 = []
    watch(page6, errs6)
    page6.goto(URL, wait_until="domcontentloaded")
    page6.wait_for_selector("#tabbar .tab", timeout=25000)
    page6.wait_for_timeout(800)
    tab(page6, 3, 650)
    shots = ["/tmp/v38-up1.jpg", "/tmp/v38-up2.jpg", "/tmp/v38-up3.jpg"]
    jpg_hex = ("ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9")
    for _p in shots:
        with open(_p, "wb") as _f:
            _f.write(bytes.fromhex(jpg_hex))
    page6.set_input_files("#photoInput", shots[:2])
    page6.wait_for_timeout(700)
    up = page6.evaluate("""() => {
      const q = s => document.querySelector('#sheet ' + s);
      const d = q('input[name=date]');
      return {sheet: document.getElementById('sheetWrap').classList.contains('open'),
              album: !!q('input[name=album]'), datalist: !!q('#albumList'),
              firstLabel: (q('.form .f label') || {}).textContent || '',
              dateVal: d ? d.value : '',
              dateIn: d ? (d.getBoundingClientRect().right <= q('') ? true : d.getBoundingClientRect().right <= document.querySelector('#sheet').getBoundingClientRect().right + 0.5) : false,
              rows: document.querySelectorAll('#sheet .up-item').length,
              sizeTxt: document.querySelectorAll('#sheet .up-size').length,
              dels: document.querySelectorAll('#sheet .up-del').length,
              addBtn: !!q('.up-add'),
              addTxt: (q('.up-add') || {}).textContent ? q('.up-add').textContent.trim() : '',
              sum: (q('#upSum') || {}).textContent || '',
              btn: (q('#upBtn') || {}).textContent || ''};
    }""")
    check("사진 추가 시트에 앨범 칸이 없음", up["album"] is False and up["datalist"] is False, up)
    check("맨 위 칸은 날짜", up["firstLabel"] == "날짜" and re.match(r"^\d{4}-\d{2}-\d{2}$", up["dateVal"]) is not None, up)
    check("날짜 칸이 시트 폭 안에 들어옴", up["dateIn"] is True, up)
    check("고른 사진 줄에 파일 용량 글씨 없음", up["sizeTxt"] == 0, up["sizeTxt"])
    check("사진 줄마다 「삭제」 버튼", up["rows"] == 2 and up["dels"] == 2, (up["rows"], up["dels"]))
    check("목록 위에 「추가」 버튼", up["addBtn"] and "추가" in up["addTxt"], up)
    check("요약·담기 버튼이 2장", "2장" in up["sum"] and "2장 담기" in up["btn"], (up["sum"], up["btn"]))
    page6.screenshot(path=os.path.join(SHOT, "photo-v38-addsheet.png"))

    page6.locator("#sheet .up-del").first.click()
    page6.wait_for_timeout(400)
    one = page6.evaluate("""() => ({rows: document.querySelectorAll('#sheet .up-item').length,
      sum: (document.querySelector('#sheet #upSum') || {}).textContent || '',
      cnt: (document.querySelector('#sheet #upCount') || {}).textContent || '',
      btn: (document.querySelector('#sheet #upBtn') || {}).textContent || ''})""")
    check("「삭제」로 한 장 빼면 목록·요약·담기 버튼이 바로 갱신",
          one["rows"] == 1 and "1장" in one["sum"] and one["cnt"] == "1" and "1장 담기" in one["btn"], one)

    with page6.expect_file_chooser() as fc:
        page6.locator("#sheet .up-add").click()
    fc.value.set_files([shots[2]])
    page6.wait_for_timeout(600)
    two = page6.evaluate("""() => ({rows: document.querySelectorAll('#sheet .up-item').length,
      btn: (document.querySelector('#sheet #upBtn') || {}).textContent || '',
      date: (document.querySelector('#sheet input[name=date]') || {}).value || ''})""")
    check("「추가」로 사진을 더 담으면 목록에 이어 붙음", two["rows"] == 2 and "2장 담기" in two["btn"], two)
    check("더 담아도 고른 날짜는 그대로", two["date"] == up["dateVal"], two)

    # 다 지우면 시트가 닫힘
    page6.locator("#sheet .up-del").first.click()
    page6.wait_for_timeout(300)
    page6.locator("#sheet .up-del").first.click()
    page6.wait_for_timeout(500)
    check("담을 사진을 다 지우면 시트가 닫힘", page6.evaluate("document.getElementById('sheetWrap').classList.contains('open')") is False)

    # 다시 담아 실제로 저장 — 앨범은 기본 이름으로
    page6.set_input_files("#photoInput", [shots[0]])
    page6.wait_for_timeout(700)
    page6.locator("#sheet #upBtn").click()
    page6.wait_for_timeout(2200)
    saved = page6.evaluate("""() => { const p = (window.__app.state.photos || [])[0] || {};
      return {n: (window.__app.state.photos || []).length, album: p.album || '', sheet: document.getElementById('sheetWrap').classList.contains('open')}; }""")
    check("앨범 칸 없이도 기본 앨범 이름으로 저장", saved["n"] >= 1 and saved["album"] != "" and saved["sheet"] is False, saved)
    check("브라우저 콘솔/페이지 오류 없음 (사진 추가 시트)", len(errs6) == 0, errs6[:4])
    ctx6.close()

    # ==================================================================
    # 10. 날짜 태그(경주여행) + 사진첩 검색
    # ==================================================================
    ctx7 = new_ctx(browser)
    ctx7.add_init_script("window.__TWOLOG_MODE = 'local';")
    page7 = ctx7.new_page()
    errs7 = []
    watch(page7, errs7)
    page7.goto(URL + "?demo=1", wait_until="networkidle")
    page7.wait_for_timeout(700)
    seed7 = page7.evaluate("JSON.stringify(window.__app.state)")
    page7.goto(URL, wait_until="domcontentloaded")
    page7.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed7)
    page7.reload(wait_until="networkidle")
    page7.wait_for_timeout(800)
    tab(page7, 3, 700)

    # 그날 사진의 날짜 태그 달기 (모아보기 위)
    page7.locator("#s-photo .pola").first.click()
    page7.wait_for_timeout(650)
    day_date = page7.evaluate("document.querySelector('#s-photo .dgrid').getAttribute('data-day')")
    check("모아보기 위에 날짜 태그 자리", page7.evaluate("!!document.querySelector('#s-photo .dgal-tag')") is True)
    page7.locator("#s-photo .dgal-tag").click()
    page7.wait_for_timeout(500)
    check("태그 시트가 열림", page7.evaluate("""() => !!document.querySelector('#sheet input[name=tag]')""") is True,
          page7.evaluate("(document.querySelector('#sheet h2')||{}).textContent"))
    page7.fill("#sheet input[name=tag]", "경주여행")
    page7.locator("#sheet button.btn-primary").click()
    page7.wait_for_timeout(700)
    tagged = page7.evaluate("""() => ({
      head: (document.querySelector('#s-photo .dgal-tag') || {}).textContent,
      albums: [...new Set((window.__app.state.photos || []).filter(p => String(p.date).slice(0,10) === '%s').map(p => p.album))],
      sheet: document.getElementById('sheetWrap').classList.contains('open')})""" % day_date)
    check("모아보기 위에 태그가 보임", tagged["head"] == "경주여행", tagged)
    check("그날 사진들의 album 이 태그로 저장", tagged["albums"] == ["경주여행"], tagged["albums"])

    page7.locator('#s-photo [data-act="photoDayBack"]').click()
    page7.wait_for_timeout(600)
    list_tag = page7.evaluate("""() => [...document.querySelectorAll('#s-photo .pday-tag')].map(b => b.textContent)""")
    check("목록의 날짜 머리글 옆에도 태그", "경주여행" in list_tag, list_tag)
    page7.screenshot(path=os.path.join(SHOT, "photo-v38-tag.png"))

    # 태그를 눌러 바로 고치기
    page7.locator("#s-photo .pday-tag").first.click()
    page7.wait_for_timeout(500)
    check("날짜 태그를 누르면 바로 고치기 시트", page7.evaluate("""() => (document.querySelector('#sheet input[name=tag]') || {}).value""") == "경주여행")
    page7.fill("#sheet input[name=tag]", "경주 벚꽃")
    page7.locator("#sheet button.btn-primary").click()
    page7.wait_for_timeout(600)
    check("고친 태그가 목록에 반영", "경주 벚꽃" in page7.evaluate("[...document.querySelectorAll('#s-photo .pday-tag')].map(b => b.textContent)"),
          page7.evaluate("[...document.querySelectorAll('#s-photo .pday-tag')].map(b => b.textContent)"))

    # 돋보기 검색
    check("사진첩 위에 돋보기 버튼", page7.evaluate("!!document.querySelector('#s-photo .photo-search')") is True)
    page7.locator("#s-photo .photo-search").click()
    page7.wait_for_timeout(550)
    page7.fill("#sheet #photoSearchIn", "경주")
    page7.wait_for_timeout(500)
    res = page7.evaluate("""() => ({n: document.querySelectorAll('#sheet .sres').length,
      txt: (document.querySelector('#sheet #photoSearchOut') || {}).innerText || ''})""")
    check("검색어로 그 날짜가 나옴", res["n"] >= 1 and "경주 벚꽃" in res["txt"], res)
    check("검색 결과에 날짜·장수", re.search(r"\d{1,2}월 \d{1,2}일", res["txt"]) is not None and "장" in res["txt"], res["txt"][:60])
    page7.screenshot(path=os.path.join(SHOT, "photo-v38-search.png"))
    page7.locator("#sheet .sres").first.click()
    page7.wait_for_timeout(700)
    jump = page7.evaluate("""() => ({sheet: document.getElementById('sheetWrap').classList.contains('open'),
      cells: document.querySelectorAll('#s-photo .dg-cell').length})""")
    check("검색 결과를 누르면 그날 모아보기로 이동", jump["sheet"] is False and jump["cells"] >= 1, jump)

    # 캡션·장소로도 검색
    page7.locator('#s-photo [data-act="photoDayBack"]').click()
    page7.wait_for_timeout(500)
    page7.locator("#s-photo .photo-search").click()
    page7.wait_for_timeout(500)
    page7.fill("#sheet #photoSearchIn", "성수")
    page7.wait_for_timeout(500)
    hit2 = page7.evaluate("(document.querySelector('#sheet #photoSearchOut') || {}).innerText || ''")
    check("장소·캡션 글자로도 찾아짐", "월" in hit2 and "일" in hit2, hit2[:60])
    page7.fill("#sheet #photoSearchIn", "없는말없는말")
    page7.wait_for_timeout(400)
    check("없는 말은 안내 문구", "없어요" in page7.evaluate("(document.querySelector('#sheet #photoSearchOut') || {}).innerText || ''"))
    page7.keyboard.press("Escape")
    page7.wait_for_timeout(400)
    check("브라우저 콘솔/페이지 오류 없음 (태그·검색)", len(errs7) == 0, errs7[:4])
    ctx7.close()



    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
