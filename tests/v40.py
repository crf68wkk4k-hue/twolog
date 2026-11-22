"""투로그 v40 확인 — 투두리스트 속지의 2열 카드 묶음 + 카테고리 줄 아래 속지 아코디언 + 모눈 메모.

1) 버전: sw.js 캐시 twolog-v47 · APP_VERSION v47 · My 탭 「버전 v47」
2) + 시트 — 속지 레이아웃이 목록 맨 아래가 아니라 «카테고리 줄 바로 아래»로 펼쳐짐
   - 처음엔 접힘 · 줄을 누르면 그 줄 바로 아래에 2×2 · 다른 줄을 누르면 이전 줄은 접힘
   - 같은 줄을 한 번 더 누르면 접힘 · 「추가」로 붙인 줄은 바로 펼쳐짐
   - ≡ 드래그를 시작하면 펼친 패널이 접혀 끌기 계산을 방해하지 않음
   - 고른 속지가 그 줄 배지·저장(S.noteKinds / list.kind)에 반영
3) 내 카테고리 「투두리스트」 — 2열 카드 묶음 + 「+ 새 리스트」
   - 새 카테고리를 투두리스트로 만들면 .ngrid + 「+ 새 리스트」만 보임
   - 「+ 새 리스트」로 카드를 만들고, 카드를 눌러 제목 수정 · 항목 추가(Add/엔터) ·
     체크(완료는 아래로) · 항목 × 삭제(시트는 그대로) · 카드 삭제
   - 카드 두 개는 2열로 나란히
4) 예전(v38·v39) 단일 체크 항목 — 카드 없이 items 만 있어도 카테고리 이름의 첫 카드로 이어짐
5) 기본 카테고리 — 「카드」는 그대로(카드 묶음), 투두리스트 선택지는 「카드」로 정리됨
   (저장돼 있던 noteKinds 의 check 값은 카드 화면으로 되돌아감)
6) 모눈 메모 — 이름·모눈 바탕(background-image) · 둥근 카드(16px) · 왼쪽 날짜(2026.11.21 토요일)
   · 제목 없이 본문만 써도 저장 · 사진 한 장 선택(선택 사항)
7) Supabase 스텁 왕복 — 내 카테고리 카드 묶음(settings groups 의 list:<id>)과
   카드 안 항목(gid)이 서버에 올라가고, 새로고침해도 그대로
8) 줄글 대신 모눈이 된 것 말고 다른 속지(별점 리뷰·지출·정산)는 그대로
9) 콘솔/페이지 오류 0건

    python3 tests/v40.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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
    tab(page, 2, 640)


def open_add_sheet(page):
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(580)


def pick_kind(page, kind):
    page.locator("#sheet #nkPanel .nk-card[data-kind='%s']" % kind).click()
    page.wait_for_timeout(170)


def row_loc(page, text):
    n = page.evaluate("""(nm) => {
      const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
      return rows.findIndex(r => { const i = r.querySelector('.nord-nm'); return i && i.value.indexOf(nm) >= 0; });
    }""", text)
    return page.locator("#sheet #noteOrderList .nord-row").nth(n)


def panel_state(page):
    return page.evaluate("""() => {
      const p = document.getElementById('nkPanel');
      const row = document.querySelector('#sheet #noteOrderList .nord-row.active');
      return {exists: !!p, hidden: p ? p.hidden : null,
              h: p ? Math.round(p.getBoundingClientRect().height) : 0,
              gap: (p && row) ? Math.round(p.getBoundingClientRect().top - row.getBoundingClientRect().bottom) : null,
              row: row ? (row.querySelector('.nord-nm') || {}).value : null,
              kinds: [...document.querySelectorAll('#sheet #nkPanel .nk-card')].map(c => c.getAttribute('data-kind')),
              active: [...document.querySelectorAll('#sheet #nkPanel .nk-card.active')].map(c => c.getAttribute('data-kind')),
              label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || ''};
    }""")


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
    check("sw.js 캐시 버전 twolog-v47", 'const VERSION = "twolog-v47"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v44", 'var APP_VERSION = "v47"' in app_js,
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
    check("My 탭 맨 위에 「버전 v47」", ver.strip() == "버전 v47", ver)

    # ==================================================================
    # 2. + 시트 — 카테고리 줄 아래로 펼쳐지는 속지 레이아웃 (아코디언)
    # ==================================================================
    note_tab(page)
    open_add_sheet(page)
    p0 = panel_state(page)
    check("+ 시트를 열면 속지 패널은 접혀 있음", p0["exists"] and p0["hidden"] is True and p0["h"] == 0, p0)
    check("목록 맨 아래에 고정된 속지 칸은 없음 (패널 안에만 있어요)",
          page.evaluate("""() => [...document.querySelectorAll('#sheet .set-lbl')]
            .filter(e => !e.closest('#nkPanel') && e.textContent.trim() === '속지').length""") == 0)

    row1 = page.locator("#sheet #noteOrderList .nord-row").nth(1)
    r1name = page.evaluate("(i) => document.querySelectorAll('#sheet #noteOrderList .nord-row')[i].querySelector('.nord-nm').value", 1)
    row1.locator(".nord-nm").click()
    page.wait_for_timeout(320)
    pa = panel_state(page)
    check("카테고리 줄을 누르면 그 줄 «바로 아래»로 패널이 펼쳐짐",
          pa["hidden"] is False and pa["row"] == r1name and 0 <= pa["gap"] <= 16, pa)
    check("패널 제목은 「속지」만 (v42)", pa["label"].strip() == "속지" and "레이아웃" not in pa["label"], pa["label"])
    check("기본 카테고리 패널은 「투두리스트」 + 세 속지 (2×2)",
          pa["kinds"] == ["", "memo", "review", "expense"] and pa["active"] == [""], pa)
    check("기본 카테고리 패널 첫 칸 이름은 「투두리스트」",
          page.evaluate("""() => (document.querySelector("#sheet #nkPanel .nk-card[data-kind=''] .nk-n") || {}).textContent""") == "투두리스트")
    box = page.evaluate("""() => {
      const cs = [...document.querySelectorAll('#sheet #nkPanel .nk-card')].map(c => {
        const b = c.getBoundingClientRect(); return {t: Math.round(b.top), l: Math.round(b.left), w: Math.round(b.width)}; });
      return cs; }""")
    check("2×2 로 놓임", box[0]["t"] == box[1]["t"] and box[2]["t"] > box[0]["t"]
          and box[2]["t"] == box[3]["t"] and box[0]["w"] == box[1]["w"], box)

    # 다른 줄을 누르면 이전 줄은 접히고 새 줄 아래로
    page.locator("#sheet #noteOrderList .nord-row").nth(2).locator(".nord-nm").click()
    page.wait_for_timeout(300)
    pb = panel_state(page)
    check("다른 줄을 누르면 새 줄 아래로 옮겨가고 이전 줄은 접힘",
          pb["hidden"] is False and pb["gap"] is not None and 0 <= pb["gap"] <= 16
          and page.evaluate("document.querySelectorAll('#sheet #noteOrderList .nord-row.active').length") == 1, pb)

    # v42: 배지가 없어져 이름칸을 다시 누르면 «이름 고치기»로 이어져요 (패널은 그 줄에 그대로)
    page.locator("#sheet #noteOrderList .nord-row").nth(2).locator(".nord-nm").click()
    page.wait_for_timeout(280)
    pc = panel_state(page)
    check("이름칸을 다시 눌러도 패널은 열린 채 (이름 고치기)", pc["hidden"] is False, pc)

    # 「추가」로 붙인 줄 → 그 아래에서 바로 고르기
    page.fill("#sheet .nord-new", "장보기 리스트")
    page.locator("#sheet .nord-add-btn").click()
    page.wait_for_timeout(320)
    pd = panel_state(page)
    check("「추가」로 붙인 새 줄 아래에서 속지가 바로 펼쳐짐",
          pd["hidden"] is False and pd["row"] == "장보기 리스트" and 0 <= pd["gap"] <= 16, pd)
    check("새 카테고리 패널은 투두리스트부터 (「카드」 없음)",
          pd["kinds"] == ["check", "memo", "review", "expense"] and pd["active"] == ["check"], pd)

    page.screenshot(path=os.path.join(SHOT, "note-v40-accordion.png"))

    # ≡ 드래그를 시작하면 패널이 접힘
    grip = page.locator("#sheet #noteOrderList .nord-row").last.locator(".nord-grip")
    gb = grip.bounding_box()
    page.mouse.move(gb["x"] + gb["width"] / 2, gb["y"] + gb["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(220)
    drag_panel = panel_state(page)
    check("≡ 를 끌기 시작하면 펼친 패널이 접힘", drag_panel["hidden"] is True, drag_panel)
    page.mouse.move(gb["x"] + gb["width"] / 2, gb["y"] - 60, steps=6)
    page.mouse.up()
    page.wait_for_timeout(420)

    # 끌고 난 뒤에는 패널이 접혀 있으니, 그 줄을 다시 눌러 펼쳐요
    row_loc(page, "장보기 리스트").locator(".nord-nm").click()
    page.wait_for_timeout(300)
    check("끌고 난 뒤 줄을 다시 누르면 패널이 그 줄 아래로 다시 펼쳐짐",
          panel_state(page)["hidden"] is False and panel_state(page)["row"] == "장보기 리스트", panel_state(page))
    pick_kind(page, "check")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(780)
    saved = page.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '장보기 리스트')[0] || {};
      return {kind: l.kind, seg: (document.querySelector('#s-diary .lchip.active') || {}).textContent,
              grid: !!document.querySelector('#s-diary .ngrid')}; }""")
    check("고른 속지로 카테고리가 만들어지고 바로 열림",
          saved["kind"] == "check" and saved["grid"] and saved["seg"] is not None, saved)

    # ==================================================================
    # 3. 내 카테고리 투두리스트 — 2열 카드 묶음 + 「+ 새 리스트」
    # ==================================================================
    page.locator("#s-diary .lchip", has_text="장보기 리스트").first.click()
    page.wait_for_timeout(520)
    v = page.evaluate("""() => ({
      badge: !!document.querySelector('#s-diary .nh-l .k'),
      grid: !!document.querySelector('#s-diary .ngrid'),
      newCard: !!document.querySelector('#s-diary .ngrid .ncard.new'),
      newLabel: (document.querySelector('#s-diary .ncard.new') || {}).textContent || '',
      cards: document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)').length,
      prog: !!document.querySelector('#s-diary .progress'),
      addForm: document.querySelectorAll('#s-diary #listAddForm').length })""")
    check("본문 위에는 속지 배지가 없음 (카테고리 이름만)", v["badge"] is False, v["badge"])
    check("카드가 없으면 「+ 새 리스트」 카드 하나만", v["grid"] and v["newCard"] and v["cards"] == 0, v)
    check("「+ 새 리스트」 라고 적혀 있음", "새 리스트" in v["newLabel"], v["newLabel"])
    check("예전 한 줄 체크 화면(진행률·Add 줄)은 없음", v["prog"] is False and v["addForm"] == 0, v)
    page.screenshot(path=os.path.join(SHOT, "note-v40-todo-cards.png"))

    # + 새 리스트 → 카드 두 개
    for nm in ["장보기", "집안일"]:
        page.locator("#s-diary .ngrid .ncard.new").click()
        page.wait_for_timeout(520)
        page.fill("#sheet input[name=title]", nm)
        page.locator("#sheet button.btn-primary").click()
        page.wait_for_timeout(620)
    cards = page.evaluate("""() => {
      const c = [...document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)')];
      const r = c.map(x => { const b = x.getBoundingClientRect(); return {t: Math.round(b.top), l: Math.round(b.left), w: Math.round(b.width)}; });
      return {n: c.length, titles: c.map(x => (x.querySelector('.nc-t') || {}).textContent), pos: r}; }""")
    check("「+ 새 리스트」로 카드를 두 개 만듦", cards["n"] == 2 and cards["titles"] == ["장보기", "집안일"], cards["titles"])
    check("카드 두 개가 2열로 나란히", cards["pos"][0]["t"] == cards["pos"][1]["t"]
          and cards["pos"][0]["l"] != cards["pos"][1]["l"], cards["pos"])

    # 카드 상세 — 항목 추가(Add·엔터) · 체크 · 삭제 · 제목 수정
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.click()
    page.wait_for_timeout(560)
    page.fill("#sheet #listAddForm input[name=text]", "우유")
    page.locator("#sheet #listAddForm button").click()
    page.wait_for_timeout(400)
    page.fill("#sheet #listAddForm input[name=text]", "계란")
    page.press("#sheet #listAddForm input[name=text]", "Enter")
    page.wait_for_timeout(420)
    added = page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      rows: [...document.querySelectorAll('#sheet .card-items .trow')].map(r => r.textContent.trim()),
      items: (window.__app.state.lists.filter(l => l.title === '장보기 리스트')[0] || {items: []}).items.map(i => ({t: i.text, g: i.gid}))})""")
    check("카드 안에서 Add·엔터로 항목이 더해지고 시트는 그대로",
          added["open"] and added["rows"] == ["우유", "계란"], added["rows"])
    check("더한 항목은 그 카드(gid) 안에 저장됨",
          len(added["items"]) == 2 and all(i["g"] for i in added["items"])
          and added["items"][0]["g"] == added["items"][1]["g"], added["items"])

    page.locator("#sheet .card-items .trow .circ").first.click()
    page.wait_for_timeout(420)
    toggled = page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      done: [...document.querySelectorAll('#sheet .card-items .trow')].map(r => r.classList.contains('done'))})""")
    check("체크하면 완료 표시되고 완료 항목은 아래로 내려감 (시트 유지)",
          toggled["open"] and toggled["done"] == [False, True], toggled)

    page.locator("#sheet .card-items .trow").last.locator(".x").click()
    page.wait_for_timeout(420)
    deleted = page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      rows: document.querySelectorAll('#sheet .card-items .trow').length})""")
    check("항목 × 로 지우면 시트는 그대로, 목록만 줄어듦", deleted["open"] and deleted["rows"] == 1, deleted)

    page.fill("#sheet input[name=title]", "마트 장보기")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(600)
    renamed = page.evaluate("[...document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-t')].map(t => t.textContent)")
    check("카드 제목을 고치면 그리드에 바로 반영", "마트 장보기" in renamed, renamed)
    left_item = page.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '장보기 리스트')[0] || {items: []};
      return l.items[0] ? l.items[0].text : ''; }""")
    check("카드 안 남은 항목이 그리드 카드에 보임",
          bool(left_item) and page.evaluate("""() => (document.querySelector('#s-diary .ngrid .ncard:not(.new) .nc-items') || {}).textContent || ''""").find(left_item) >= 0,
          left_item)
    page.screenshot(path=os.path.join(SHOT, "note-v40-todo-cards.png"))

    # 카드 삭제
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.click()
    page.wait_for_timeout(520)
    page.locator("#sheet button.btn-del").click()
    page.wait_for_timeout(400)
    check("카드 삭제는 한 번 더 물어봄",
          page.evaluate("(document.querySelector('#sheet h2') || {}).textContent") == "리스트 삭제")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(560)
    after_del = page.evaluate("""() => ({cards: document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)').length,
      items: (window.__app.state.lists.filter(l => l.title === '장보기 리스트')[0] || {items: []}).items.length})""")
    check("카드를 지우면 그 카드와 안의 항목이 사라짐", after_del["cards"] == 1 and after_del["items"] == 0, after_del)
    page.evaluate("""() => { const c = document.querySelector('#sheet [data-close]');
      if (c && document.getElementById('sheetWrap').classList.contains('open')) c.click(); }""")
    page.wait_for_timeout(350)

    check("브라우저 콘솔/페이지 오류 없음 (로컬)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 4. 예전(v38·v39) 단일 체크 항목 — 카드 안으로 자연스럽게 이어짐
    # ==================================================================
    ctx2 = new_ctx(browser)
    ctx2.add_init_script("window.__TWOLOG_MODE = 'local';")
    page2 = ctx2.new_page()
    errs2 = []
    watch(page2, errs2)
    page2.goto(URL + "?demo=1", wait_until="networkidle")
    page2.wait_for_timeout(700)
    old_seed = page2.evaluate("() => window.__app.demoState ? 'demo' : 'other'")
    base = page2.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")
    legacy_list = {"id": "Lold1", "title": "여행 준비물", "emoji": "", "kind": "check",
                   "items": [{"id": "i1", "text": "여권", "memo": "", "done": True},
                             {"id": "i2", "text": "충전기", "memo": "", "done": False}]}
    base["lists"] = [legacy_list]
    base["noteOrder"] = ["todo", "bucket", "log", "list:Lold1"]
    base["ui"]["seg"] = "list:Lold1"
    base.pop("groups", None)
    page2.goto(URL, wait_until="domcontentloaded")
    page2.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", base)
    page2.reload(wait_until="networkidle")
    page2.wait_for_timeout(1000)
    tab(page2, 2, 700)
    page2.locator("#s-diary .lchip", has_text="여행 준비물").first.click()
    page2.wait_for_timeout(560)
    mig = page2.evaluate("""() => {
      const l = window.__app.state.lists[0];
      const gs = window.__app.state.groups['list:Lold1'] || [];
      const card = document.querySelector('#s-diary .ngrid .ncard:not(.new)');
      return {cards: gs.length, cardTitle: gs[0] ? gs[0].title : null,
              sameGid: (l.items || []).every(i => !!i.gid),
              gids: (l.items || []).map(i => i.gid),
              items: (l.items || []).length,
              grid: !!document.querySelector('#s-diary .ngrid'),
              shown: card ? card.textContent.replace(/\\s+/g, ' ').trim() : null,
              cardItems: document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-items .cti').length}; }""")
    check("카드 없이 항목만 있던 카테고리도 카드 하나로 이어짐",
          mig["cards"] == 1 and mig["cardTitle"] == "여행 준비물" and mig["grid"], mig)
    check("예전 항목이 유실 없이 그 카드 안에 (개수 그대로)",
          mig["items"] == 2 and mig["sameGid"] and len(set(mig["gids"])) == 1, mig["gids"])
    check("카드 미리보기에 예전 항목 두 개가 보임", mig["cardItems"] == 2 and "여권" in (mig["shown"] or ""), mig["shown"])
    page2.screenshot(path=os.path.join(SHOT, "note-v40-legacy.png"))
    check("브라우저 콘솔/페이지 오류 없음 (예전 데이터)", len(errs2) == 0, errs2[:4])
    ctx2.close()

    # ==================================================================
    # 5. 기본 카테고리 — 「카드」는 그대로 · 저장돼 있던 check 는 카드로
    # ==================================================================
    ctx3 = new_ctx(browser)
    ctx3.add_init_script("window.__TWOLOG_MODE = 'local';")
    page3 = ctx3.new_page()
    errs3 = []
    watch(page3, errs3)
    page3.goto(URL + "?demo=1", wait_until="networkidle")
    page3.wait_for_timeout(700)
    b3 = page3.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")
    b3["noteKinds"] = {"bucket": "check"}
    b3["ui"]["seg"] = "bucket"
    page3.goto(URL, wait_until="domcontentloaded")
    page3.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", b3)
    page3.reload(wait_until="networkidle")
    page3.wait_for_timeout(900)
    tab(page3, 2, 680)
    page3.locator("#s-diary .seg-btn", has_text="버킷리스트").first.click()
    page3.wait_for_timeout(560)
    bk = page3.evaluate("""() => ({kinds: window.__app.state.noteKinds || {},
      seg: (document.querySelector('#s-diary .seg-btn.active') || {}).textContent,
      cards: document.querySelectorAll('#s-diary .ngrid .ncard').length,
      stats: document.querySelectorAll('#s-diary .progress').length})""")
    check("버킷리스트에 저장돼 있던 「투두리스트」는 카드 화면으로 (혼동 없이 정리)",
          "bucket" not in bk["kinds"] and bk["cards"] > 0 and bk["stats"] == 0, bk)

    open_add_sheet(page3)
    row_loc(page3, "버킷리스트").locator(".nord-nm").click()
    page3.wait_for_timeout(300)
    check("기본 카테고리 줄에는 속지 배지가 없음 (v42 — ≡ · 이름만)",
          page3.evaluate("!document.querySelector('#sheet #noteOrderList .nord-kb')"))
    # v42: 글이 있는 카테고리는 속지를 못 바꿔요 — 빈 버킷리스트로 확인
    page3.evaluate("() => { window.__app.state.bucket = []; window.__app.state.groups.bucket = []; }")
    pick_kind(page3, "memo")
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(760)
    check("기본 카테고리는 모눈 메모 속지로도 바뀜 (빈 카테고리)",
          page3.evaluate("(window.__app.state.noteKinds || {}).bucket") == "memo")


    # ==================================================================
    # 6. 모눈 메모 — 이름 · 모눈 바탕 · 둥근 카드 · 왼쪽 날짜 · 제목 없이 본문만
    # ==================================================================
    page3.locator("#s-diary .seg-btn", has_text="메모").first.click()
    page3.wait_for_timeout(520)
    open_add_sheet(page3)
    row_loc(page3, "메모").locator(".nord-nm").click()
    page3.wait_for_timeout(300)
    kinds = page3.evaluate("""() => ([...document.querySelectorAll('#sheet #nkPanel .nk-card')].map(c => [
      c.getAttribute('data-kind'), (c.querySelector('.nk-n') || {}).textContent, (c.querySelector('.nk-d') || {}).textContent]))""")
    memo_def = [k for k in kinds if k[0] == "memo"][0]
    check("속지 이름이 「모눈 메모」 (설명도 모눈 바탕)", memo_def[1] == "모눈 메모" and "모눈" in memo_def[2], memo_def)

    # 모눈 메모 속지의 내 카테고리를 만들어 그 화면을 봐요
    page3.fill("#sheet .nord-new", "오늘의 기록")
    page3.locator("#sheet .nord-add-btn").click()
    page3.wait_for_timeout(320)
    pick_kind(page3, "memo")
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(780)
    page3.locator("#s-diary .lchip", has_text="오늘의 기록").first.click()
    page3.wait_for_timeout(520)

    # v41: 「+ 새 다이어리」 → 모눈종이 풀스크린 다이어리 (제목 없이 본문만)
    page3.locator("#s-diary .d41-new").click()
    page3.wait_for_timeout(640)
    memo_sheet = page3.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      full: document.getElementById('sheetWrap').classList.contains('sheet-full'),
      paper: (() => { const p = document.querySelector('#sheet .d41-paper');
        return p ? getComputedStyle(p).backgroundImage : null; })(),
      tools: [...document.querySelectorAll('#sheet .d41-tool')].map(b => b.getAttribute('aria-label'))})""")
    check("다이어리는 화면을 꽉 채우고 본문 칸이 모눈 바탕",
          memo_sheet["open"] and memo_sheet["full"] and "linear-gradient" in (memo_sheet["paper"] or ""), memo_sheet)
    check("다이어리 아래에 펜 · 글씨 · 사진 도구가 있음",
          memo_sheet["tools"] == ["펜 그리기", "글씨", "사진 넣기"], memo_sheet["tools"])
    mbox = page3.locator("#d41Paper").bounding_box()
    page3.mouse.click(mbox["x"] + 70, mbox["y"] + 200)
    page3.wait_for_timeout(320)
    page3.keyboard.type("아침에 창문을 열었더니 바람이 차가웠다.")
    page3.wait_for_timeout(200)
    page3.locator("#sheet .d41-back").click()
    page3.wait_for_timeout(760)
    memo = page3.evaluate("""() => {
      const cards = [...document.querySelectorAll('#s-diary .nmemo-card')];
      const d = cards[0] ? cards[0].querySelector('.nmemo-date') : null;
      const list = document.querySelector('#s-diary .nmemo-list');
      const body = cards[0] ? cards[0].querySelector('.nmemo-b') : null;
      return {n: cards.length,
              date: d ? d.textContent.trim() : null,
              align: d ? getComputedStyle(d).textAlign : null,
              radius: cards[0] ? getComputedStyle(cards[0]).borderTopLeftRadius : null,
              bg: list ? getComputedStyle(list).backgroundImage : null,
              title: cards[0] && cards[0].querySelector('.nmemo-t') ? cards[0].querySelector('.nmemo-t').textContent : null,
              body: body ? body.textContent : null}; }""")
    check("제목 없이 본문만 써도 모눈 메모 카드가 보임",
          memo["n"] == 1 and memo["title"] is None and "바람이 차가웠다" in (memo["body"] or ""), memo)
    check("카드 모서리는 둥글게 (16px)", memo["radius"] == "16px", memo["radius"])
    check("날짜는 맨 위 왼쪽에 「YYYY.MM.DD 요일」",
          memo["align"] == "left" and len(memo["date"] or "") == 14
          and (memo["date"] or "")[:4].isdigit() and (memo["date"] or "").endswith("요일"), memo["date"])
    check("메모 목록 바탕에 모눈 격자(linear-gradient)", "linear-gradient" in (memo["bg"] or ""), (memo["bg"] or "")[:60])
    page3.screenshot(path=os.path.join(SHOT, "note-v40-grid-memo.png"))

    # 사진 한 장 붙이기 (선택) — 고르면 카드 아래에 함께 보여요
    memo_jpg = "/tmp/v40-memo.jpg"
    _durl = page3.evaluate("""() => { const c = document.createElement('canvas'); c.width = 300; c.height = 200;
      const x = c.getContext('2d'); x.fillStyle = '#8FB39B'; x.fillRect(0, 0, 300, 200); return c.toDataURL('image/jpeg', 0.9); }""")
    with open(memo_jpg, "wb") as _f:
        _f.write(__import__("base64").b64decode(_durl.split(",", 1)[1]))
    page3.locator("#s-diary .d41-card").first.click()
    page3.wait_for_timeout(620)
    page3.set_input_files("#d41ImgIn", [memo_jpg])
    page3.wait_for_timeout(1300)
    page3.locator("#sheet .d41-back").click()
    page3.wait_for_timeout(820)
    pimg = page3.evaluate("""() => { const l = window.__app.state.lists.filter(x => x.title === '오늘의 기록')[0] || {items: []};
      return {img: String((((l.items[0] || {}).imgs) || [{}])[0].src || '').slice(0, 20),
              shown: document.querySelectorAll('#s-diary .d41-th').length}; }""")
    check("모눈 메모에 사진 한 장을 붙이면 카드에 미리보기로 보임",
          pimg["img"].startswith("data:image") and pimg["shown"] == 1, pimg)

    # 다크 모드에서도 모눈 결이 보임
    page3.evaluate("document.documentElement.setAttribute('data-mode', 'dark')")
    page3.wait_for_timeout(350)
    dark = page3.evaluate("""() => { const l = document.querySelector('#s-diary .nmemo-list');
      const c = document.querySelector('#s-diary .nmemo-card');
      return {bg: l ? getComputedStyle(l).backgroundImage : null, card: c ? getComputedStyle(c).backgroundColor : null}; }""")
    check("다크 모드에서도 모눈 격자가 보임", "linear-gradient" in (dark["bg"] or ""), (dark["bg"] or "")[:50])
    page3.evaluate("document.documentElement.setAttribute('data-mode', 'light')")
    page3.wait_for_timeout(250)

    # 다른 속지는 그대로 (별점 리뷰 · 지출·정산)
    open_add_sheet(page3)
    page3.fill("#sheet .nord-new", "맛집 기록")
    page3.locator("#sheet .nord-add-btn").click()
    page3.wait_for_timeout(300)
    pick_kind(page3, "review")
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(740)
    page3.fill("#s-diary #listQuickForm input[name=text]", "성수 카페")
    page3.locator("#s-diary #listQuickForm button").click()
    page3.wait_for_timeout(480)
    rv = page3.evaluate("""() => ({badge: !!document.querySelector('#s-diary .note-hd .k'),
      cards: document.querySelectorAll('#s-diary .rv-card').length,
      stars: document.querySelectorAll('#s-diary .rv-card .rvs').length})""")
    check("별점 리뷰 속지는 그대로", rv["badge"] is False and rv["cards"] == 1 and rv["stars"] == 5, rv)

    open_add_sheet(page3)
    page3.fill("#sheet .nord-new", "데이트 통장")
    page3.locator("#sheet .nord-add-btn").click()
    page3.wait_for_timeout(300)
    pick_kind(page3, "expense")
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(740)
    page3.locator("#s-diary .exp-act[data-tx='expense']").click()
    page3.wait_for_timeout(460)
    page3.fill("#sheet input[name=amount]", "24000")
    page3.locator("#sheet .exp-cat[data-cat='식비']").click()
    page3.fill("#sheet input[name=memo]", "점심")
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(600)
    ex = page3.evaluate("""() => ({badge: !!document.querySelector('#s-diary .note-hd .k'),
      sum: (document.querySelector('#s-diary .exp-spent') || {}).textContent,
      rows: document.querySelectorAll('#s-diary .exp-row').length})""")
    check("지출·정산 속지는 그대로 (사용 금액 계산)", ex["badge"] is False and ex["sum"] == "₩24,000" and ex["rows"] == 1, ex)
    check("브라우저 콘솔/페이지 오류 없음 (속지)", len(errs3) == 0, errs3[:4])
    ctx3.close()

    # ==================================================================
    # 7. Supabase 스텁 왕복 — 내 카테고리 카드 묶음 + 카드 안 항목(gid)
    # ==================================================================
    cid, uid2, mail = "couple-v40", "user-v40", "v40@twolog.app"
    gid1 = "g-card-1"
    seed_notes = [
        {"id": "L1", "couple_id": cid, "kind": "list", "sort": 0, "deleted": False,
         "payload": {"title": "여행 준비", "emoji": "", "kind": "check",
                     "items": [{"id": "i1", "text": "여권", "memo": "", "done": True, "gid": gid1},
                               {"id": "i2", "text": "충전기", "memo": "", "done": False, "gid": gid1}]}},
        {"id": "T1", "couple_id": cid, "kind": "todo", "sort": 1, "deleted": False,
         "payload": {"text": "장보기", "memo": "", "done": False, "gid": "g-todo-1"}},
    ]
    settings = [
        {"couple_id": cid, "key": "groups",
         "value": {"todo": [{"id": "g-todo-1", "title": "메모"}],
                   "bucket": [{"id": "g-bucket-1", "title": "버킷리스트"}],
                   "log": [{"id": "g-log-1", "title": "영화·먹방"}],
                   "list:L1": [{"id": gid1, "title": "여권 · 충전기", "who": "me", "date": "2026-11-20"}]}},
        {"couple_id": cid, "key": "note_meta",
         "value": {"tabs": {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"},
                            "log": {"e": "", "n": "영화·먹방"}},
                   "order": ["todo", "bucket", "log", "list:L1"], "kinds": {}}},
    ]
    db = remote_db(cid, uid2, mail, seed_notes, settings)
    ctx4 = new_ctx(browser)
    ctx4.add_init_script(remote_seed(db, uid2, mail))
    page4 = ctx4.new_page()
    errs4 = []
    watch(page4, errs4)
    stub_route(page4)
    page4.goto(URL, wait_until="domcontentloaded")
    page4.wait_for_selector("#tabbar .tab", timeout=25000)
    page4.wait_for_timeout(2800)
    tab(page4, 2, 700)
    page4.locator("#s-diary .lchip", has_text="여행 준비").first.click()
    page4.wait_for_timeout(560)
    remote = page4.evaluate("""() => ({cards: [...document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-t')].map(t => t.textContent),
      items: (window.__app.state.lists[0] || {items: []}).items.map(i => ({t: i.text, g: i.gid}))})""")
    check("서버에 있던 내 카테고리 카드가 그대로 보임", remote["cards"] == ["여권 · 충전기"], remote["cards"])
    check("카드 안 항목과 gid 도 그대로", len(remote["items"]) == 2 and all(i["g"] == gid1 for i in remote["items"]), remote["items"])

    # 화면에서 카드를 하나 더 만들고 항목을 넣어 서버로
    page4.locator("#s-diary .ngrid .ncard.new").click()
    page4.wait_for_timeout(520)
    page4.fill("#sheet input[name=title]", "세면도구")
    page4.locator("#sheet button.btn-primary").click()
    page4.wait_for_timeout(620)
    page4.locator("#s-diary .ngrid .ncard:not(.new)", has_text="세면도구").first.click()
    page4.wait_for_timeout(520)
    page4.fill("#sheet #listAddForm input[name=text]", "칫솔")
    page4.locator("#sheet #listAddForm button").click()
    page4.wait_for_timeout(2000)
    page4.evaluate("""() => { const c = document.querySelector('#sheet [data-close]');
      if (c && document.getElementById('sheetWrap').classList.contains('open')) c.click(); }""")
    page4.wait_for_timeout(1600)
    srv = page4.evaluate("""() => {
      const g = (window.__stub.settings || []).filter(x => x.key === 'groups')[0] || null;
      const row = (window.__stub.notes || []).filter(x => x.kind === 'list')[0] || null;
      return {groups: g ? Object.keys(g.value).sort() : null,
              listCards: g ? (g.value['list:L1'] || []).map(c => c.title) : null,
              items: row ? row.payload.items.map(i => ({t: i.text, g: i.gid})) : null}; }""")
    check("카드 묶음이 settings groups 의 list:<id> 로 올라감",
          bool(srv["groups"]) and "list:L1" in srv["groups"], srv["groups"])
    check("새로 만든 카드도 서버 카드 묶음에 들어감",
          srv["listCards"] is not None and "세면도구" in srv["listCards"], srv["listCards"])
    check("카드 안 항목과 gid 가 notes 행 payload 에 담김",
          any(i["t"] == "칫솔" and i["g"] for i in (srv["items"] or [])), srv["items"])

    page4.reload(wait_until="domcontentloaded")
    page4.wait_for_selector("#tabbar .tab", timeout=25000)
    page4.wait_for_timeout(2600)
    tab(page4, 2, 700)
    page4.locator("#s-diary .lchip", has_text="여행 준비").first.click()
    page4.wait_for_timeout(600)
    again = page4.evaluate("""() => ({cards: [...document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-t')].map(t => t.textContent),
      items: (window.__app.state.lists[0] || {items: []}).items.map(i => ({t: i.text, g: i.gid}))})""")
    check("새로고침 뒤에도 카드 두 개와 항목이 그대로",
          sorted(again["cards"]) == sorted(["여권 · 충전기", "세면도구"]) and len(again["items"]) == 3, again)
    check("새로고침 뒤에도 항목마다 카드 gid 유지", all(i["g"] for i in again["items"]), again["items"])
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errs4) == 0, errs4[:4])
    ctx4.close()

    # ==================================================================
    # 8. 사진첩 달력 — 머리줄(달력 아이콘)은 위에 붙어 있고, 달력은 그 아래에서
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
    page5.wait_for_timeout(900)
    tab(page5, 3, 680)
    page5.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page5.wait_for_timeout(950)

    cal = page5.evaluate("""() => {
      const box = document.getElementById('screens'), br = box.getBoundingClientRect();
      const hd = document.querySelector('#s-photo .hdr');
      const btn = document.querySelector('#s-photo .pc-toggle');
      const s = document.querySelector('#s-photo .pcal-stick');
      const ymNow = (() => { const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0'); })();
      const cur = document.querySelector('#s-photo .pcal-m[data-ym="' + ymNow + '"]');
      const hb = hd.getBoundingClientRect();
      return {hdrTop: Math.round(hb.top - br.top), hdrH: Math.round(hb.height),
              btnVisible: !!btn && btn.getBoundingClientRect().height > 0,
              btnOn: btn ? btn.classList.contains('on') : null,
              btnLabel: btn ? btn.getAttribute('aria-label') : null,
              btnCalIcon: btn ? btn.innerHTML.indexOf('<rect') >= 0 : false,
              stickTop: s ? Math.round(s.getBoundingClientRect().top - br.top) : null,
              curTop: cur ? Math.round(cur.getBoundingClientRect().top - br.top) : null,
              months: document.querySelectorAll('#s-photo .pcal-m').length,
              scroll: Math.round(box.scrollTop)};
    }""")
    check("달력 보기에서도 머리줄이 화면 위에 붙어 있음", cal["hdrTop"] == 0 and cal["hdrH"] > 40, cal)
    check("오른쪽 위 달력 아이콘이 보이고 지금 켜져 있음",
          cal["btnVisible"] and cal["btnOn"] is True and cal["btnLabel"] == "사진 목록으로" and cal["btnCalIcon"], cal)
    check("요일 줄은 머리줄 «아래»에서 시작", cal["stickTop"] == cal["hdrH"], (cal["stickTop"], cal["hdrH"]))
    check("이번 달도 머리줄 아래로 내려와 시작", cal["curTop"] is not None and cal["curTop"] > cal["hdrH"], cal)
    page5.screenshot(path=os.path.join(SHOT, "photo-cal-v40.png"))

    page5.evaluate("document.getElementById('screens').scrollTop += 620")
    page5.wait_for_timeout(420)
    sc2 = page5.evaluate("""() => { const box = document.getElementById('screens'), br = box.getBoundingClientRect();
      const hd = document.querySelector('#s-photo .hdr'), s = document.querySelector('#s-photo .pcal-stick');
      return {hdrTop: Math.round(hd.getBoundingClientRect().top - br.top),
              hdrH: Math.round(hd.getBoundingClientRect().height),
              stickTop: Math.round(s.getBoundingClientRect().top - br.top),
              scroll: Math.round(box.scrollTop),
              months: document.querySelectorAll('#s-photo .pcal-m').length}; }""")
    check("스크롤해도 머리줄은 위에 그대로 (달력 아이콘 계속 보임)",
          sc2["hdrTop"] == 0 and sc2["stickTop"] == sc2["hdrH"] and sc2["scroll"] > 400, sc2)
    check("스크롤해도 달력은 계속 이어짐", sc2["months"] >= 25, sc2["months"])

    page5.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page5.wait_for_timeout(760)
    back = page5.evaluate("""() => ({cal: !!document.querySelector('#s-photo .pcal'),
      days: document.querySelectorAll('#s-photo .pday').length,
      on: document.querySelector('#s-photo .pc-toggle').classList.contains('on')})""")
    check("달력 아이콘을 한 번 더 누르면 사진첩 목록으로 돌아감",
          back["cal"] is False and back["days"] > 0 and back["on"] is False, back)
    check("브라우저 콘솔/페이지 오류 없음 (사진 달력)", len(errs5) == 0, errs5[:4])
    ctx5.close()

    # ==================================================================
    # 9. 사진 추가 시트 — 맨 앞 ≡ 손잡이로 고른 사진 순서 바꾸기 (담는 순서까지)
    # ==================================================================
    ctx6 = new_ctx(browser)
    ctx6.add_init_script("window.__TWOLOG_MODE = 'local';")
    page6 = ctx6.new_page()
    errs6 = []
    watch(page6, errs6)
    page6.goto(URL, wait_until="domcontentloaded")
    page6.wait_for_selector("#tabbar .tab", timeout=25000)
    page6.wait_for_timeout(900)
    tab(page6, 3, 680)
    shots = ["/tmp/v40-up1.jpg", "/tmp/v40-up2.jpg", "/tmp/v40-up3.jpg"]
    jpg_hex = ("ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9")
    for _p in shots:
        with open(_p, "wb") as _f:
            _f.write(bytes.fromhex(jpg_hex))
    page6.set_input_files("#photoInput", shots)
    page6.wait_for_timeout(800)
    up0 = page6.evaluate("""() => ({
      rows: document.querySelectorAll('#sheet .up-grid .up-cell').length,
      xs: document.querySelectorAll('#sheet .up-grid .up-cell .up-x').length,
      cols: getComputedStyle(document.querySelector('#sheet #upList')).gridTemplateColumns.split(' ').length,
      btn: (document.querySelector('#sheet #upBtn') || {}).textContent || ''})""")
    check("고른 사진이 5열 네모 칸으로 (사진 3장 · 칸마다 ×) — v43",
          up0["rows"] == 3 and up0["xs"] == 3 and up0["cols"] == 5, up0)
    page6.evaluate("() => document.querySelectorAll('#sheet .up-cell').forEach((c, i) => c.dataset.mk = 'abc'[i])")
    page6.screenshot(path=os.path.join(SHOT, "photo-v40-addsheet.png"))

    # 세 번째 칸을 끌어 맨 앞으로
    c3 = page6.locator("#sheet .up-cell").nth(2).bounding_box()
    c0 = page6.locator("#sheet .up-cell").nth(0).bounding_box()
    page6.mouse.move(c3["x"] + c3["width"] / 2, c3["y"] + c3["height"] / 2)
    page6.mouse.down()
    page6.wait_for_timeout(120)
    for i in range(1, 9):
        page6.mouse.move(c3["x"] + c3["width"] / 2 + (c0["x"] - c3["x"]) * i / 8,
                         c3["y"] + c3["height"] / 2)
        page6.wait_for_timeout(30)
    check("칸을 끌기 시작하면 떠 있음 (dragging)",
          page6.evaluate("document.querySelectorAll('#sheet .up-cell.dragging').length") == 1)
    page6.mouse.up()
    page6.wait_for_timeout(600)
    order1 = page6.evaluate("() => [...document.querySelectorAll('#sheet .up-cell')].map(c => c.dataset.mk)")
    idx1 = page6.evaluate("() => [...document.querySelectorAll('#sheet .up-cell')].map(c => c.getAttribute('data-i'))")
    check("세 번째 사진을 끌어 맨 앞으로 옮김", order1 == ["c", "a", "b"], order1)
    check("끌고 나면 data-i 도 지금 순서로 다시 매겨짐",
          idx1 == ["0", "1", "2"] and page6.evaluate("document.querySelectorAll('#sheet .up-cell.dragging').length") == 0, idx1)

    # 키보드 → ← 로도
    page6.locator("#sheet .up-cell").nth(0).focus()
    page6.keyboard.press("ArrowRight")
    page6.wait_for_timeout(300)
    order2 = page6.evaluate("() => [...document.querySelectorAll('#sheet .up-cell')].map(c => c.dataset.mk)")
    check("칸에서 → 키로 한 칸 오른쪽", order2 == ["a", "c", "b"], order2)
    page6.locator("#sheet .up-cell").nth(1).focus()
    page6.keyboard.press("ArrowLeft")
    page6.wait_for_timeout(300)
    order3 = page6.evaluate("() => [...document.querySelectorAll('#sheet .up-cell')].map(c => c.dataset.mk)")
    check("← 키로 다시 왼쪽", order3 == ["c", "a", "b"], order3)

    # 담기 → 고른 순서 그대로 저장 (1번째가 사진첩 맨 앞 = 대표)
    page6.locator("#sheet #upBtn").click()
    page6.wait_for_timeout(2600)
    saved = page6.evaluate("""() => ({titles: (window.__app.state.photos || []).map(p => p.title),
      n: (window.__app.state.photos || []).length})""")
    check("담은 사진이 옮긴 순서 그대로 저장됨 (1번째가 맨 앞)",
          saved["n"] == 3 and saved["titles"] == ["v40-up3", "v40-up1", "v40-up2"], saved)
    # v40: 태그 칸은 새로 열 때 늘 비어 있어요 (예전에 쓴 태그가 따라 올라오지 않음)
    tag_shots = ["/tmp/v40-tag1.jpg", "/tmp/v40-tag2.jpg"]
    for _p in tag_shots:
        with open(_p, "wb") as _f:
            _f.write(bytes.fromhex(jpg_hex))
    page6.set_input_files("#photoInput", [tag_shots[0]])
    page6.wait_for_timeout(700)
    page6.fill("#sheet input[name=album_tag]", "롯데 리조트")
    page6.locator("#sheet #upBtn").click()
    page6.wait_for_timeout(2400)
    page6.set_input_files("#photoInput", [tag_shots[1]])
    page6.wait_for_timeout(800)
    tag_new = page6.evaluate("""() => ({
      tag: (document.querySelector('#sheet input[name=album_tag]') || {}).value,
      date: (document.querySelector('#sheet input[name=date]') || {}).value,
      labels: [...document.querySelectorAll('#sheet .up-row label')].map(l => l.textContent),
      stacked: (() => { const a = document.querySelector('#sheet input[name=date]');
        const b = document.querySelector('#sheet input[name=album_tag]');
        if (!a || !b) return false; const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return rb.bottom <= ra.top + 2 && Math.abs(ra.left - rb.left) < 2 && Math.min(ra.width, rb.width) > 100; })(),
      sub: (document.querySelector('#sheet .sheet-sub') || {}).textContent || ''})""")
    check("「기록 이름」을 적어 올린 뒤 새 시트를 열면 그 칸이 비어 있음 (라벨도 기록 이름)",
          tag_new["tag"] == "" and tag_new["labels"] == ["기록 이름", "날짜"], tag_new)
    check("「기록 이름」과 「날짜」는 한 줄이 아니라 위아래 두 줄 (각자 밑줄) — v45", tag_new["stacked"] is True, tag_new)
    check("「사진 추가」 아래 장수·용량·줄이는 말 줄은 없음 — v45", "1800px" not in tag_new["sub"], tag_new["sub"])
    # 한 시트 안에서 「추가」로 더 담을 때는 적어 둔 태그가 그대로
    page6.fill("#sheet input[name=album_tag]", "제주 여행")
    with page6.expect_file_chooser() as fc:
        page6.locator("#sheet .up-add").click()
    fc.value.set_files([tag_shots[0]])
    page6.wait_for_timeout(700)
    kept = page6.evaluate("() => (document.querySelector('#sheet input[name=album_tag]') || {}).value")
    check("한 시트에서 「+ 추가」로 더 담을 때는 기록 이름이 그대로", kept == "제주 여행", kept)
    page6.keyboard.press("Escape")
    page6.wait_for_timeout(400)
    check("브라우저 콘솔/페이지 오류 없음 (사진 순서)", len(errs6) == 0, errs6[:4])
    ctx6.close()

    # ==================================================================
    # 10. 노트 카드 상세 시트 — 「제목」 위 · 한 칸 띄우고 「제목 색」 · 큰 제목 글씨
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
    page7.wait_for_timeout(900)
    tab(page7, 2, 680)
    page7.locator("#s-diary .lchip", has_text="여행 준비물").first.click()
    page7.wait_for_timeout(560)
    page7.locator("#s-diary .ngrid .ncard:not(.new)").first.click()
    page7.wait_for_timeout(620)
    cs = page7.evaluate("""() => {
      const inp = document.querySelector('#sheet .card-meta input[name="title"]');
      const cp = document.querySelector('#sheet .ccp');
      const lbl = cp ? (cp.querySelector('.cp-hd span') || {}).textContent : '';
      const ir = inp ? inp.getBoundingClientRect() : null;
      const pr = cp ? cp.getBoundingClientRect() : null;
      const csIn = inp ? getComputedStyle(inp) : null;
      const lblTitle = [...document.querySelectorAll('#sheet .card-meta label')].map(l => l.textContent)[0] || '';
      return {title: !!inp, titleTop: ir ? Math.round(ir.top) : null, titleH: ir ? Math.round(ir.height) : null,
              color: !!cp, colorTop: pr ? Math.round(pr.top) : null,
              gap: (ir && pr) ? Math.round(pr.top - ir.bottom) : null,
              font: csIn ? csIn.fontSize : null, weight: csIn ? csIn.fontWeight : null,
              lblTitle, colorLbl: lbl}; }""")
    check("카드 시트에서 「제목」 입력칸이 「제목 색」보다 위",
          cs["title"] and cs["color"] and cs["titleTop"] < cs["colorTop"]
          and cs["lblTitle"] == "제목" and "제목 색" in (cs["colorLbl"] or ""), cs)
    check("「제목」과 「제목 색」 사이에 한 줄 여백 (16px 이상)", cs["gap"] is not None and cs["gap"] >= 16, cs["gap"])
    check("제목 입력칸 글씨가 크고 굵음 (19px · 700)",
          cs["font"] == "19px" and cs["weight"] in ("700", "bold"), (cs["font"], cs["weight"]))
    page7.screenshot(path=os.path.join(SHOT, "note-v40-card-sheet.png"))
    page7.keyboard.press("Escape")
    page7.wait_for_timeout(400)
    check("브라우저 콘솔/페이지 오류 없음 (카드 시트)", len(errs7) == 0, errs7[:4])
    ctx7.close()

    # ==================================================================
    # 11. 사진 크게 보기 — 사진만 · 옆으로 밀어 넘기기 · 탭하면 닫힘
    #    + 날짜 모아보기의 ‹ 뒤로가기 (날짜·태그 왼쪽)
    # ==================================================================
    ctx8 = new_ctx(browser)
    ctx8.add_init_script("window.__TWOLOG_MODE = 'local';")
    page8 = ctx8.new_page()
    errs8 = []
    watch(page8, errs8)
    page8.goto(URL + "?demo=1", wait_until="networkidle")
    page8.wait_for_timeout(700)
    seed8 = page8.evaluate("JSON.stringify(window.__app.state)")
    page8.goto(URL, wait_until="domcontentloaded")
    page8.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed8)
    page8.reload(wait_until="networkidle")
    page8.wait_for_timeout(900)
    tab(page8, 3, 700)
    more = page8.evaluate("""() => {
      const days = [...document.querySelectorAll('#s-photo .pday')];
      for (const day of days) {
        const last = [...day.querySelectorAll('.pola')].pop();
        const b = last ? last.querySelector('.pola-more') : null;
        if (!b) continue;
        const pic = last.querySelector('.pola-pic').getBoundingClientRect();
        const br = b.getBoundingClientRect();
        const total = (window.__app.state.photos || []).filter(p =>
          String(p.date || '').slice(0, 10) === day.querySelector('.pday-hd').getAttribute('data-date')).length;
        return {ok: true, n: day.querySelectorAll('.pola').length, text: b.textContent,
                total, head: (day.querySelector('.pday-hd .c') || {}).textContent || '',
                w: Math.round(br.width), h: Math.round(br.height),
                rightGap: Math.round(pic.right - br.right),
                bottomGap: Math.round(pic.bottom - br.bottom),
                inside: (br.left >= pic.left && br.right <= pic.right + 1 && br.top >= pic.top && br.bottom <= pic.bottom + 1),
                badgesInDay: day.querySelectorAll('.pola-more').length,
                allDaysHeadMeta: [...document.querySelectorAll('#s-photo .pday-hd .c')].length};
      }
      return {ok: false};
    }""")
    check("3장을 넘긴 날은 마지막 사진에만 「+N」 배지",
          more["ok"] and more["n"] == 3 and more["badgesInDay"] == 1
          and more["text"].startswith("+") and more["total"] > 3, more)
    check("+N 은 마지막 사진 오른쪽 아래 구석에 조그맣게 (사진을 가리지 않음)",
          more["inside"] and more["rightGap"] is not None and 0 <= more["rightGap"] <= 10
          and 0 <= more["bottomGap"] <= 10 and more["h"] <= 22 and more["w"] <= 46, more)
    check("날짜 줄 오른쪽 「+N장」 표기는 없음", more["head"] == "" and more["allDaysHeadMeta"] == 0, more)
    page8.screenshot(path=os.path.join(SHOT, "_probe-more.png"))
    page8.locator("#s-photo .pday-hd").last.click()   # 최근 날짜 (사진 6장)
    page8.wait_for_timeout(750)
    hd = page8.evaluate("""() => {
      const l = document.querySelector('#s-photo .dgal-l');
      const back = document.querySelector('#s-photo .dgal-back');
      const h1 = document.querySelector('#s-photo .dgal-tt h1');
      const tag = document.querySelector('#s-photo .dgal-tag');
      const br = back ? back.getBoundingClientRect() : null;
      const tr = h1 ? h1.getBoundingClientRect() : null;
      return {first: l ? l.firstElementChild.className : null,
              back: !!back, backRight: br ? Math.round(br.right) : null,
              titleLeft: tr ? Math.round(tr.left) : null, title: h1 ? h1.textContent : null,
              tag: tag ? tag.textContent : null};
    }""")
    check("모아보기 헤더 맨 왼쪽에 ‹ 뒤로가기", hd["first"] == "dgal-back" and hd["back"], hd)
    check("‹ 뒤로가기가 날짜·태그 글씨보다 왼쪽", hd["backRight"] is not None and hd["titleLeft"] is not None
          and hd["backRight"] <= hd["titleLeft"] + 2, hd)

    # v40: 날짜 모아보기 오른쪽 위는 «수정(연필)» — 그날 사진 편집 시트 · 캡션 칸은 없음
    hd2 = page8.evaluate("""() => ({
      edit: !!document.querySelector('#s-photo [data-act="editPhotoDay"]'),
      plus: !!document.querySelector('#s-photo [data-act="addPhotoDay"]'),
      chins: document.querySelectorAll('#s-photo .pola-chin').length})""")
    check("모아보기 오른쪽 위는 수정 아이콘 (+ 아님)", hd2["edit"] and not hd2["plus"], hd2)
    check("사진첩 목록에 캡션 줄이 없음", hd2["chins"] == 0, hd2["chins"])
    page8.locator('#s-photo [data-act="editPhotoDay"]').click()
    page8.wait_for_timeout(650)
    de = page8.evaluate("""() => ({
      head: (document.querySelector('#sheet h2') || {}).textContent,
      date: (document.querySelector('#sheet input[name=date]') || {}).value,
      tag: (document.querySelector('#sheet input[name=album_tag]') || {}).value,
      caption: !!document.querySelector('#sheet input[name=title]'),
      rows: document.querySelectorAll('#sheet .up-cell').length,
      grips: document.querySelectorAll('#sheet .up-cell .up-x').length,
      dels: document.querySelectorAll('#sheet .up-cell .up-x').length,
      add: !!document.querySelector('#sheet .up-add')})""")
    check("수정 아이콘 → 그날 사진 편집 시트 (날짜·기록 이름·사진 칸 그리드)",
          de["head"] == "사진 수정" and len(de["date"] or "") == 10 and (de["date"] or "")[4] == "-"
          and de["rows"] == 6 and de["grips"] == 6 and de["dels"] == 6 and de["add"], de)
    check("사진 편집 시트에 캡션 칸 없음", de["caption"] is False, de["caption"])
    page8.screenshot(path=os.path.join(SHOT, "_probe-dayedit2.png"))
    before_ids = page8.evaluate("() => window.__app.state.photos.map(p => p.id)")
    page8.locator("#sheet .up-cell").first.focus()
    page8.keyboard.press("ArrowRight")
    page8.wait_for_timeout(400)
    page8.locator("#sheet button.btn-primary").click()
    page8.wait_for_timeout(1500)
    after_ids = page8.evaluate("() => window.__app.state.photos.map(p => p.id)")
    check("칸을 옮긴 사진 순서가 저장됨 (그날 첫 사진부터)",
          before_ids[:2] == after_ids[1::-1] and sorted(before_ids) == sorted(after_ids),
          (before_ids[:3], after_ids[:3]))

    page8.locator("#s-photo .dg-cell").first.click()
    page8.wait_for_timeout(800)
    pv = page8.evaluate("""() => {
      const v = document.querySelector('#sheet .pview');
      const r = v ? v.getBoundingClientRect() : null;
      const strip = document.querySelector('#sheet .pv40-strip');
      return {ok: !!v, w: r ? Math.round(r.width) : 0, h: r ? Math.round(r.height) : 0,
              full: document.getElementById('sheetWrap').classList.contains('sheet-full'),
              btns: document.querySelectorAll('#sheet .pv40-btn, #sheet .pv-nav, #sheet .pv-x, #sheet .pv-bar').length,
              text: (document.getElementById('sheet').textContent || '').trim().length,
              slides: document.querySelectorAll('#sheet .pv40-slide').length,
              snap: strip ? getComputedStyle(strip).scrollSnapType : '',
              vh: window.innerHeight};
    }""")
    check("사진을 누르면 검은 바탕 화면 가득 크게 보기",
          pv["ok"] and pv["full"] and pv["w"] == 390 and pv["h"] >= int(pv["vh"] * 0.95), pv)
    check("위아래 어떤 글씨·버튼도 없이 사진만", pv["btns"] == 0 and pv["text"] == 0, (pv["btns"], pv["text"]))
    check("같은 날 사진이 옆으로 이어지고 가로 스냅", pv["slides"] == 6 and "x mandatory" in pv["snap"], pv["snap"])
    page8.screenshot(path=os.path.join(SHOT, "photo-v40-viewer.png"))

    page8.evaluate("(() => { const s = document.querySelector('#sheet .pv40-strip'); s.scrollBy({ left: s.clientWidth }); })()")
    page8.wait_for_timeout(500)
    sw = page8.evaluate("""() => { const s = document.querySelector('#sheet .pv40-strip');
      return {left: Math.round(s.scrollLeft), w: Math.round(s.clientWidth)}; }""")
    check("옆으로 밀면 다음 사진으로 넘어감", sw["left"] >= sw["w"] - 4, sw)
    page8.evaluate("(() => { const s = document.querySelector('#sheet .pv40-strip'); s.scrollBy({ left: -s.clientWidth }); })()")
    page8.wait_for_timeout(450)

    page8.mouse.click(195, 420)     # 사진을 한 번 탭하면 닫힘
    page8.wait_for_timeout(700)
    closed = page8.evaluate("""() => ({sheet: document.getElementById('sheetWrap').classList.contains('open'),
      cells: document.querySelectorAll('#s-photo .dg-cell').length})""")
    check("사진을 한 번 탭하면 모아보기로 닫힘", closed["sheet"] is False and closed["cells"] == 6, closed)

    # ==================================================================
    # 12. 모아보기의 댓글 · 대댓글 (v41: 사진마다가 아니라 날짜 한 칸)
    # ==================================================================
    page8.wait_for_timeout(200)
    dv = page8.evaluate("""() => ({blocks: document.querySelectorAll('#s-photo .dcmt').length,
      forms: document.querySelectorAll('#s-photo .dcmt .cmt-form').length,
      thumbs: document.querySelectorAll('#s-photo .dcmt .dcmt-th').length})""")
    check("날짜 사진 전체에 댓글 칸 하나 (사진 6장이어도 칸 1개)", dv["blocks"] == 1 and dv["forms"] == 1, dv)

    first_cmt = page8.locator("#s-photo .dcmt").first
    first_cmt.locator(".cmt-form .cmt-in").fill("여기 진짜 좋았다 🤍")
    first_cmt.locator(".cmt-form .cmt-send").click()
    page8.wait_for_timeout(650)
    c1 = page8.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      return {rows: sec.querySelectorAll('.cmt').length,
              name: (sec.querySelector('.cmt-h b') || {}).textContent,
              text: (sec.querySelector('.cmt-t') || {}).textContent,
              av: !!sec.querySelector('.cmt .av'),
              time: (sec.querySelector('.cmt-h span') || {}).textContent,
              replyBtns: sec.querySelectorAll('button[data-act="cmtReply"]').length,
              delBtns: sec.querySelectorAll('button[data-act="cmtDel"]').length}; }""")
    check("댓글에 작성자 프사·이름·내용·시각이 보임",
          c1["rows"] == 1 and c1["name"] == "소영" and "여기 진짜 좋았다" in (c1["text"] or "")
          and c1["av"] and (c1["time"] or "").startswith("오"), c1)
    check("단 댓글에는 답글·삭제 버튼이 함께 보임", c1["replyBtns"] == 1 and c1["delBtns"] == 1, c1)

    page8.locator("#s-photo .dcmt").first.locator(".cmt-acts button[data-act='cmtReply']").first.click()
    page8.wait_for_timeout(350)
    rm = page8.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      return {ph: (sec.querySelector('.cmt-in') || {}).placeholder,
              re: !!sec.querySelector('input[name="re"]') && sec.querySelector('input[name="re"]').value}; }""")
    check("답글을 누르면 「@이름에게 답글」 모드",
          rm["ph"] == "@소영에게 답글" and bool(rm["re"]), rm)
    page8.locator("#s-photo .dcmt").first.locator(".cmt-in").fill("다음에 또 오자")
    page8.locator("#s-photo .dcmt").first.locator(".cmt-send").click()
    page8.wait_for_timeout(700)
    c2 = page8.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      const re = sec.querySelector('.cmt.re');
      const top = sec.querySelector('.cmt');
      return {rows: sec.querySelectorAll('.cmt').length, re: sec.querySelectorAll('.cmt.re').length,
              indent: (re && top) ? Math.round(re.getBoundingClientRect().left - top.getBoundingClientRect().left) : null,
              to: (re && re.querySelector('.cmt-to')) ? re.querySelector('.cmt-to').textContent : null,
              text: re ? (re.querySelector('.cmt-t') || {}).textContent : null,
              av: re ? !!re.querySelector('.av') : false,
              name: re ? (re.querySelector('.cmt-h b') || {}).textContent : null}; }""")
    check("대댓글이 그 댓글 아래에 들여쓰여 붙음 (프사·이름·내용)",
          c2["rows"] == 2 and c2["re"] == 1 and c2["indent"] and c2["indent"] >= 14
          and c2["to"] == "@소영" and "다음에 또 오자" in (c2["text"] or "") and c2["av"] and c2["name"] == "소영", c2)
    page8.screenshot(path=os.path.join(SHOT, "photo-v40-comments.png"))

    # 내 댓글은 삭제할 수 있어요
    page8.locator("#s-photo .dcmt").first.locator(".cmt.re button[data-act='cmtDel']").click()
    page8.wait_for_timeout(600)
    c3 = page8.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      return {rows: sec.querySelectorAll('.cmt').length,
              state: ((window.__app.state.photos.filter(p => (p.comments || []).length)[0] || {}).comments || [])
                .reduce((n, c) => n + 1 + (c.replies || []).length, 0)}; }""")
    check("대댓글 삭제 — 화면과 저장된 댓글에서 함께 사라짐", c3["rows"] == 1 and c3["state"] == 1, c3)
    page8.screenshot(path=os.path.join(SHOT, "photo-v40-comments.png"))
    check("브라우저 콘솔/페이지 오류 없음 (사진 댓글)", len(errs8) == 0, errs8[:4])
    ctx8.close()

    # ==================================================================
    # 13. 사진 댓글 Supabase 왕복 — photos.memo 로 두 폰이 같은 댓글을 봐요
    # ==================================================================
    cid5, uidA, uidB = "couple-v40c", "user-v40a", "user-v40b"
    db5 = remote_db(cid5, uidA, "a@twolog.app", [])
    db5["users"][uidB] = {"id": uidB, "email": "b@twolog.app", "password": "pw123456"}
    db5["couples"][0]["members"] = [uidA, uidB]
    db5["photos"] = [{"id": "P1", "couple_id": cid5, "date": time.strftime("%Y-%m-%d"),
                      "album": "바닷가", "title": "바다", "place": "", "memo": "",
                      "art": 3, "cap_bg": None, "storage_path": None, "sort": 0}]

    ctx9 = new_ctx(browser)
    ctx9.add_init_script(remote_seed(db5, uidA, "a@twolog.app"))
    page9 = ctx9.new_page()
    errs9 = []
    watch(page9, errs9)
    stub_route(page9)
    page9.goto(URL, wait_until="domcontentloaded")
    page9.wait_for_selector("#tabbar .tab", timeout=25000)
    page9.wait_for_timeout(2800)
    tab(page9, 3, 700)
    page9.locator("#s-photo .pday-hd").first.click()
    page9.wait_for_timeout(700)
    page9.locator("#s-photo .dcmt").first.locator(".cmt-in").fill("서버로 가는 댓글")
    page9.locator("#s-photo .dcmt").first.locator(".cmt-send").click()
    page9.wait_for_timeout(2200)
    srv = page9.evaluate("""() => { const r = (window.__stub.photos || []).filter(x => x.id === 'P1')[0] || null;
      return r ? {memo: r.memo} : null; }""")
    check("댓글이 photos 행 memo 에 표시와 함께 실려 올라감",
          bool(srv) and str(srv["memo"]).startswith("twolog:c:") and "서버로 가는 댓글" in str(srv["memo"]), srv)

    page9.reload(wait_until="domcontentloaded")
    page9.wait_for_selector("#tabbar .tab", timeout=25000)
    page9.wait_for_timeout(2600)
    tab(page9, 3, 700)
    page9.locator("#s-photo .pday-hd").first.click()
    page9.wait_for_timeout(750)
    after = page9.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      return {rows: document.querySelectorAll('#s-photo .dcmt .cmt').length,
              text: (sec.querySelector('.cmt-t') || {}).textContent,
              name: (sec.querySelector('.cmt-h b') || {}).textContent,
              del: !!sec.querySelector('button[data-act="cmtDel"]')}; }""")
    check("새로고침해도 댓글이 그대로 (내 댓글은 삭제 가능)",
          after["rows"] == 1 and "서버로 가는 댓글" in (after["text"] or "") and after["del"], after)
    # 이 폰이 올린 서버 상태를 그대로 상대 폰 시드로 (스텁은 컨텍스트마다 따로 저장돼요)
    db5_now = page9.evaluate("() => JSON.parse(localStorage.getItem('stub-sb-db') || 'null')") or db5
    ctx9.close()

    # 상대 폰(두 번째 멤버) 시점 — 같은 댓글이 «소영» 이름으로 보이고 삭제 버튼은 없어요
    ctx10 = new_ctx(browser)
    ctx10.add_init_script(remote_seed(db5_now, uidB, "b@twolog.app"))
    page10 = ctx10.new_page()
    errs10 = []
    watch(page10, errs10)
    stub_route(page10)
    page10.goto(URL, wait_until="domcontentloaded")
    page10.wait_for_selector("#tabbar .tab", timeout=25000)
    page10.wait_for_timeout(2800)
    tab(page10, 3, 700)
    page10.locator("#s-photo .pday-hd").first.click()
    page10.wait_for_timeout(750)
    other = page10.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      return {me: window.__app.state.couple.me, you: window.__app.state.couple.you,
              name: (sec.querySelector('.cmt-h b') || {}).textContent,
              text: (sec.querySelector('.cmt-t') || {}).textContent,
              del: !!sec.querySelector('button[data-act="cmtDel"]')}; }""")
    check("상대 폰에서도 같은 댓글이 소영 이름으로 보임",
          other["name"] == other["you"] and "서버로 가는 댓글" in (other["text"] or ""), other)
    check("남의 댓글에는 삭제 버튼이 없음", other["del"] is False, other)
    check("브라우저 콘솔/페이지 오류 없음 (사진 댓글 동기화)", len(errs9) == 0 and len(errs10) == 0,
          (errs9[:3], errs10[:3]))
    ctx10.close()

    browser.close()

print()
if fails:
    print("실패 %d개:" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("실패: 없음")
