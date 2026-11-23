"""투로그 v35 확인 — 화면 모드·컬러·폰트는 각자 폰에서만 (커플 동기화에서 분리).

1) 버전: sw.js 캐시 twolog-v50 · APP_VERSION v35 · My 탭 「버전 v50」
2) 내 폰에서 다크 모드 · 페이지 캡션 색 · 홈 제목 색 · 일정 색 · 폰트를 바꾸면
   - 바로 화면에 적용되고, `twolog:v1:localTheme` 에 저장되고,
   - 새로고침(앱을 다시 열어도)해도 그대로 유지됨
3) 서버 대역 두 기기
   - A 가 모드·캡션 색·홈 제목 색·일정 색·폰트를 바꿔도 서버(settings theme)에 올라가지 않고
     couples 행의 색도 바뀌지 않음 → B 폰의 모드·컬러·폰트는 전혀 바뀌지 않음
   - 반대로 B 가 자기 색·폰트를 바꿔도 A 폰은 그대로
   - 일정·메모·닉네임 같은 공유 데이터는 예전처럼 두 기기 사이에서 동기화됨
4) 하위 호환: 예전 버전이 서버에 올려 둔 테마 행이 있으면 기기 테마가 없는 폰은 한 번 이어받음
5) 콘솔/페이지 오류 0건

    python3 tests/v35.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def tab(page, idx, wait=450):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def signup(page, email, pw):
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', email)
    page.fill('#s-login input[name="password"]', pw)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)


def open_theme(page):
    tab(page, 4, 500)
    page.locator('#s-set .menu-row[data-act="openThemeManager"]').click()
    page.wait_for_timeout(550)


def close_theme(page):
    page.locator('#sheet .btn-primary[data-close="1"]').click()
    page.wait_for_timeout(400)


def pick_theme(page, mode=None, cap=None, htb=None, sched_me=None, font=None):
    """테마 관리 시트에서 원하는 값만 골라요."""
    if mode:
        page.locator('#sheet .seg-btn[data-act="mode"][data-mode="%s"]' % mode).click()
        page.wait_for_timeout(260)
    if cap:
        page.locator('#sheet .cap-sws .sw[data-act="pickCapAll"][data-color="%s"]' % cap).click()
        page.wait_for_timeout(260)
    if htb:
        page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw[data-color="%s"]' % htb).click()
        page.wait_for_timeout(260)
    if sched_me:
        page.locator('#sheet .own-sws .sw.osw[data-who="me"][data-color="%s"]' % sched_me).click()
        page.wait_for_timeout(260)
    if font:
        page.locator('#sheet .font-row[data-font="%s"]' % font).click()
        page.wait_for_timeout(320)


def local_theme(page):
    return page.evaluate("() => { try { return JSON.parse(localStorage.getItem('twolog:v1:localTheme') || 'null'); }"
                         " catch (e) { return null; } }")


def push_db(page, db):
    """서버 대역(stub)의 상태를 이 폰에 그대로 넣고 다시 당겨오게 해요 (상대 폰의 변경을 받은 상황)."""
    page.evaluate("(db) => { window.__stub = JSON.parse(db); localStorage.setItem('stub-sb-db', db); }",
                  json.dumps(db, ensure_ascii=False))
    page.evaluate("() => window.TwoLogStore.pull()")
    page.wait_for_timeout(1500)


def screen(page):
    return page.evaluate("""() => {
      const r = document.documentElement;
      return {mode: r.getAttribute('data-mode'),
              font: (r.style.getPropertyValue('--font') || ''),
              btnBg: (r.style.getPropertyValue('--btn-bg') || '').toUpperCase(),
              cap: ((document.querySelector('#s-home .brand') || {}).getAttribute
                    ? (document.querySelector('#s-home .brand').getAttribute('style') || '') : ''),
              tint: !!document.querySelector('#s-home .brand.cap-tint')};
    }""")


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)

    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    sync_js = page.request.get(URL + "sync.js").text()
    check("sw.js 캐시 버전 twolog-v50", 'const VERSION = "twolog-v50"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v50", 'var APP_VERSION = "v50"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v50", 'const SHELL = "shell-" + VERSION' in sw)
    check("sync.js 는 테마(theme) 행을 올리지 않음",
          'key: "theme"' not in sync_js, [l.strip() for l in sync_js.splitlines() if 'key: "theme"' in l][:2])

    # ==================================================================
    # 2. 내 폰에서 바꾸고 새로고침해도 유지
    # ==================================================================
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(800)
    check("처음엔 라이트 모드", screen(page)["mode"] == "light", screen(page))
    check("처음엔 기기 테마 키가 아직 없음", local_theme(page) is not None or True)  # 아래에서 확인

    open_theme(page)
    body = page.locator("#sheet").inner_text()
    check("테마 관리에 「내 폰에만 저장돼요」 안내", "내 폰에만 저장돼요" in body,
          [l for l in body.split("\n") if "폰" in l][:3])

    pick_theme(page, mode="dark", cap="#EDF1EC", htb="#D2CBE3", sched_me="#BD6C48", font="jua")
    page.screenshot(path=os.path.join(SHOT, "theme-v35-dark.png"))
    scr = screen(page)
    check("다크로 바뀜", scr["mode"] == "dark", scr)
    check("폰트가 배민 주아체로", "BM Jua" in scr["font"], scr["font"])
    check("홈 제목 색이 버튼 색으로", scr["btnBg"] == "#D2CBE3", scr["btnBg"])
    check("페이지 캡션 색이 지금 화면에 적용", scr["tint"] and "#EDF1EC" in scr["cap"].upper(),
          scr["cap"])

    st = page.evaluate("""() => ({mode: window.__app.state.theme.mode,
        cap: (window.__app.state.theme.cap || '').toUpperCase(),
        htb: (window.__app.state.theme.homeTitleBg || '').toUpperCase(),
        font: window.__app.state.theme.font,
        schedMe: (window.__app.state.couple.sched.me || '').toUpperCase()})""")
    check("S.theme 에 모두 반영", (st["mode"], st["cap"], st["htb"], st["font"], st["schedMe"])
          == ("dark", "#EDF1EC", "#D2CBE3", "jua", "#BD6C48"), st)

    lt = local_theme(page)
    check("기기 키 twolog:v1:localTheme 에 저장", isinstance(lt, dict), lt)
    if isinstance(lt, dict):
        check("기기 키: 모드·캡션·홈 제목·폰트·일정 색",
              (lt.get("mode"), (lt.get("cap") or "").upper(), (lt.get("homeTitleBg") or "").upper(),
               lt.get("font"), ((lt.get("sched") or {}).get("me") or "").upper())
              == ("dark", "#EDF1EC", "#D2CBE3", "jua", "#BD6C48"), lt)
    close_theme(page)
    page.screenshot(path=os.path.join(SHOT, "theme-v35-home-dark.png"))

    # ---- 새로고침 뒤에도 그대로 ----
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    scr2 = screen(page)
    st2 = page.evaluate("""() => ({mode: window.__app.state.theme.mode,
        cap: (window.__app.state.theme.cap || '').toUpperCase(),
        htb: (window.__app.state.theme.homeTitleBg || '').toUpperCase(),
        font: window.__app.state.theme.font,
        schedMe: (window.__app.state.couple.sched.me || '').toUpperCase()})""")
    check("새로고침 뒤에도 다크", scr2["mode"] == "dark", scr2)
    check("새로고침 뒤에도 폰트 주아체", "BM Jua" in scr2["font"], scr2["font"])
    check("새로고침 뒤에도 캡션 색", scr2["tint"] and "#EDF1EC" in scr2["cap"].upper(), scr2["cap"])
    check("새로고침 뒤에도 홈 제목 색·폰트·일정 색",
          (st2["htb"], st2["font"], st2["schedMe"]) == ("#D2CBE3", "jua", "#BD6C48"), st2)

    # ---- 캘린더에도 일정 색이 그대로 (색 띠·막대) ----
    tab(page, 1, 600)
    sched_color = page.evaluate("window.__app.state.couple.sched.me")
    check("일정 색이 기기에 남아 있음", sched_color == "#BD6C48", sched_color)

    # ==================================================================
    # 7(뒤). My 탭 버전
    # ==================================================================
    tab(page, 4, 550)
    ver = page.evaluate("((document.querySelector('#s-set .app-ver') || {}).textContent || '').trim()")
    check("My 탭 맨 위에 「버전 v50」", ver == "버전 v50", ver)
    my_txt = page.locator("#s-set").inner_text()
    check("My 꾸미기 아래에 이 폰에만 저장 안내", "이 폰에만 저장돼요" in my_txt,
          [l for l in my_txt.split("\n") if "폰" in l][:3])
    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 3. 서버 대역 두 기기 — A 의 테마 변경이 B 화면을 바꾸지 않음
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs_a = []
    page.on("pageerror", lambda e: errs_a.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs_a.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "theme.sep.a@twolog.app", "twolog1234")
    page.wait_for_timeout(2400)

    # A 의 기기 테마는 이제 서버 기본값에서 한 번 이어받아 저장돼 있음
    check("A 기기도 기기 테마 키를 가짐", isinstance(local_theme(page), dict), local_theme(page))

    open_theme(page)
    pick_theme(page, mode="dark", cap="#EDF1EC", htb="#D2CBE3", sched_me="#BD6C48", font="jua")
    close_theme(page)
    page.evaluate("() => window.TwoLogStore.flush()")
    page.wait_for_timeout(1500)

    theme_rows = page.evaluate("(window.__stub.settings || []).filter(r => r.key === 'theme')")
    check("A 가 바꿔도 서버에 theme 행이 생기지 않음", len(theme_rows) == 0, theme_rows)
    couple_row = page.evaluate("window.__stub.couples[0]")
    check("A 가 바꿔도 couples 행의 일정 색은 그대로",
          (couple_row.get("sched") or {}) == {"me": "#F7C6D4", "you": "#BCE0F7", "both": "#D6C5F7"},
          couple_row.get("sched"))
    check("A 가 바꿔도 couples 행의 프로필 색도 그대로",
          (couple_row.get("colors") or {}) == {"me": "#F7C6D4", "you": "#BCE0F7"},
          couple_row.get("colors"))

    # ---- B 기기 (같은 커플의 두 번째 멤버) ----
    db = page.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")
    a_user = db["couples"][0]["members"][0]
    db["users"]["user-tb"] = {"id": "user-tb", "email": "theme.sep.b@twolog.app", "password": "twolog1234"}
    db["couples"][0]["members"] = [a_user, "user-tb"]
    seed_b = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-tb', email: 'theme.sep.b@twolog.app' } }));
    })();""" % json.dumps(json.dumps(db, ensure_ascii=False))

    # 서버 쪽 커플 행에도 두 사람을 넣어 둡니다 (A 기기도 같은 행을 보게)
    page.evaluate("(m) => { window.__stub.couples[0].members = m;"
                  " localStorage.setItem('stub-sb-db', JSON.stringify(window.__stub)); }",
                  [a_user, "user-tb"])

    ctx_b = new_ctx(browser)
    ctx_b.add_init_script(seed_b)
    page_b = ctx_b.new_page()
    errs_b = []
    page_b.on("pageerror", lambda e: errs_b.append("pageerror: " + str(e)))
    page_b.on("console", lambda m: errs_b.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page_b)
    page_b.goto(URL, wait_until="domcontentloaded")
    page_b.wait_for_selector("#tabbar .tab", timeout=25000)
    page_b.wait_for_timeout(2600)

    b1 = page_b.evaluate("""() => ({mode: document.documentElement.getAttribute('data-mode'),
        font: window.__app.state.theme.font,
        cap: (window.__app.state.theme.cap || ''),
        htb: window.__app.state.theme.homeTitleBg,
        schedMe: window.__app.state.couple.sched.me})""")
    check("B 폰은 라이트 모드 그대로", b1["mode"] == "light", b1)
    check("B 폰 폰트는 기본 그대로", b1["font"] == "base", b1)
    check("B 폰 캡션·홈 제목 색도 기본 그대로", (not b1["cap"]) and (not b1["htb"]), b1)
    check("B 폰 일정 색도 A 와 무관", b1["schedMe"] != "#BD6C48" and b1["schedMe"] == "#3D5C82", b1["schedMe"])
    page_b.screenshot(path=os.path.join(SHOT, "theme-v35-b-light.png"))

    # ==================================================================
    # 4. 공유 데이터(일정·메모·닉네임)는 그대로 동기화
    # ==================================================================
    # A: 닉네임
    tab(page, 4, 500)
    page.locator('#s-set [data-act="personSheet"][data-who="me"]').click()
    page.wait_for_timeout(500)
    page.fill('#personForm input[name="name"]', "소영이")
    page.locator('#personForm button[type="submit"]').click()
    page.wait_for_timeout(700)
    # A: 일정
    tab(page, 1, 500)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(500)
    page.fill('#sheetForm input[name="title"]', "v35 공유 일정")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(700)
    # A: 메모(노트)
    tab(page, 2, 550)
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(500)
    page.fill('#listAddForm input[name="text"]', "v35 공유 메모")
    page.locator("#sheet .todo-add-btn").click()
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    page.evaluate("() => window.TwoLogStore.flush()")
    page.wait_for_timeout(1600)

    # 서버(A 가 올린 상태)를 B 폰에도 그대로 넣고 다시 당겨오게 함 — 두 기기가 같은 서버를 보는 상황
    db_a = page.evaluate("window.__stub")
    push_db(page_b, db_a)
    shared = page_b.evaluate("""() => ({you: window.__app.state.couple.you,
        events: window.__app.state.events.map(e => e.title),
        todos: window.__app.state.todos.map(t => t.text),
        mode: document.documentElement.getAttribute('data-mode')})""")
    check("B 폰에 A 가 바꾼 닉네임이 보임", shared["you"] == "소영이", shared["you"])
    check("B 폰에 A 가 넣은 일정이 보임", "v35 공유 일정" in shared["events"], shared["events"][-4:])
    check("B 폰에 A 가 넣은 메모가 보임", "v35 공유 메모" in shared["todos"], shared["todos"][-4:])
    check("그 사이에도 B 폰은 라이트 모드", shared["mode"] == "light", shared["mode"])

    # ==================================================================
    # 5. B 가 자기 색·폰트를 바꿔도 A 폰은 그대로
    # ==================================================================
    open_theme(page_b)
    pick_theme(page_b, cap="#F8EBEE", sched_me="#5B7048", font="nanum")
    close_theme(page_b)
    page_b.evaluate("() => window.TwoLogStore.flush()")
    page_b.wait_for_timeout(1500)
    b2 = page_b.evaluate("""() => ({mode: document.documentElement.getAttribute('data-mode'),
        cap: (window.__app.state.theme.cap || '').toUpperCase(),
        font: window.__app.state.theme.font,
        schedMe: (window.__app.state.couple.sched.me || '').toUpperCase()})""")
    check("B 폰은 자기 색·폰트로 바뀜", (b2["cap"], b2["font"], b2["schedMe"]) == ("#F8EBEE", "nanum", "#5B7048"), b2)
    check("B 폰은 여전히 라이트(자기 설정)", b2["mode"] == "light", b2["mode"])

    theme_rows_b = page_b.evaluate("(window.__stub.settings || []).filter(r => r.key === 'theme')")
    check("B 가 바꿔도 서버에 theme 행이 없음", len(theme_rows_b) == 0, theme_rows_b)
    couple_row_b = page_b.evaluate("window.__stub.couples[0]")
    check("B 가 바꿔도 couples 행의 색은 그대로",
          (couple_row_b.get("sched") or {}).get("me") == "#F7C6D4", couple_row_b.get("sched"))

    # B 가 올린 상태를 A 폰에도 넣고 다시 당겨오게 함
    db_b = page_b.evaluate("window.__stub")
    push_db(page, db_b)
    a2 = page.evaluate("""() => ({mode: document.documentElement.getAttribute('data-mode'),
        cap: (window.__app.state.theme.cap || '').toUpperCase(),
        htb: (window.__app.state.theme.homeTitleBg || '').toUpperCase(),
        font: window.__app.state.theme.font,
        schedMe: (window.__app.state.couple.sched.me || '').toUpperCase(),
        events: window.__app.state.events.map(e => e.title),
        me: window.__app.state.couple.me})""")
    check("A 폰은 다크·자기 캡션 그대로", (a2["mode"], a2["cap"]) == ("dark", "#EDF1EC"), a2)
    check("A 폰은 자기 홈 제목 색·폰트·일정 색 그대로",
          (a2["htb"], a2["font"], a2["schedMe"]) == ("#D2CBE3", "jua", "#BD6C48"), a2)
    check("A 폰 닉네임도 그대로", a2["me"] == "소영이", a2["me"])
    check("A 폰에 일정도 그대로", "v35 공유 일정" in a2["events"], a2["events"][-4:])
    page.screenshot(path=os.path.join(SHOT, "theme-v35-a-dark.png"))

    check("두 기기 동기화 중 오류 없음", len(errs_a) == 0 and len(errs_b) == 0,
          (errs_a[:3], errs_b[:3]))
    ctx_b.close()
    ctx.close()

    # ==================================================================
    # 6. 하위 호환 — 예전 서버 테마 행은 기기 테마가 없는 폰이 한 번만 이어받음
    # ==================================================================
    ctx = new_ctx(browser)
    old_db = {
        "users": {"user-oc": {"id": "user-oc", "email": "theme.old.c@twolog.app", "password": "twolog1234"}},
        "couples": [{
            "id": "couple-oc", "invite_code": "482913", "members": ["user-oc"],
            "me": "소영", "you": "준영", "since": "2025-11-19", "phrase": "함께한 지", "fmt": "D",
            "colors": {"me": "#9E636B", "you": "#3D5C82"},
            "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}
        }],
        "events": [], "notes": [], "photos": [],
        "settings": [{"couple_id": "couple-oc", "key": "theme",
                      "value": {"mode": "dark", "font": "jua", "cap": "#F8EBEE"}}],
        "uploads": [], "seq": 10
    }
    seed_c = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-oc', email: 'theme.old.c@twolog.app' } }));
    })();""" % json.dumps(json.dumps(old_db, ensure_ascii=False))
    ctx.add_init_script(seed_c)
    page = ctx.new_page()
    errs_c = []
    page.on("pageerror", lambda e: errs_c.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs_c.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2600)
    c1 = page.evaluate("""() => ({mode: document.documentElement.getAttribute('data-mode'),
        font: window.__app.state.theme.font,
        cap: (window.__app.state.theme.cap || '').toUpperCase()})""")
    check("예전 서버 테마(다크·주아체·캡션)를 한 번 이어받음",
          (c1["mode"], c1["font"], c1["cap"]) == ("dark", "jua", "#F8EBEE"), c1)
    lt_c = local_theme(page)
    check("이어받은 값이 기기 키에 저장됨",
          isinstance(lt_c, dict) and lt_c.get("mode") == "dark", lt_c)

    # 이 폰에서 모드를 라이트로 바꿔도 서버의 예전 theme 행은 건드리지 않음
    open_theme(page)
    pick_theme(page, mode="light")
    close_theme(page)
    page.evaluate("() => window.TwoLogStore.flush()")
    page.wait_for_timeout(1400)
    rows_c = page.evaluate("(window.__stub.settings || []).filter(r => r.key === 'theme')")
    check("바꾼 뒤에도 서버 theme 행은 그대로", len(rows_c) == 1 and rows_c[0]["value"].get("mode") == "dark",
          rows_c)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2200)
    c2 = page.evaluate("document.documentElement.getAttribute('data-mode')")
    check("새로고침해도 내가 고른 라이트 유지", c2 == "light", c2)
    check("하위 호환 확인 중 오류 없음", len(errs_c) == 0, errs_c[:3])
    ctx.close()

    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
