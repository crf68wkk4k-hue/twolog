"""투로그 v25 확인 — Supabase 실시간 연결(remote 모드) · 로그인/초대코드 화면 · 버전.

1) sync.js CONFIG 에 프로젝트 주소·publishable 키가 들어가 isRemote() == true
2) remote 모드 첫 로드: 스키마·세션이 없어도 흰 화면 없이 로그인 화면이 뜸
   (진짜 esm.sh + 진짜 Supabase 로 확인 — 계정·행은 만들지 않음)
3) 계정 만들기 → 홈 → My 탭(이메일·자동 동기화·내 초대 코드) → 코드 새로 만들기
   → 상대 초대 코드 입력으로 연결 → 로그아웃 → 다시 로그인
   (여기서는 tests/stub-supabase.js 로 모듈만 바꿔 끼워, 진짜 프로젝트에 시험 계정을 만들지 않음)
4) 스키마를 아직 넣지 않은 프로젝트에서도 앱이 멈추지 않음 (오프라인 표시 + 홈 렌더)
5) local 모드(?sync=local)는 예전 그대로 — 5개 탭 · 「로컬」 표시 · 기록 이 기기에 저장
6) sw.js 캐시 twolog-v25 · APP_VERSION v25

    python3 tests/v25.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

PROJ = "https://qvhupdivtfzhzymovtyy.supabase.co"
PUB_KEY = "sb_publishable_X4eO7AgGT5DnrxPdR5A3MA__hCxIqhD"
STUB = open(os.path.join(HERE, "stub-supabase.js")).read()
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


def tab_count(page):
    return page.locator("#tabbar .tab").count()


def body_text(page):
    return page.evaluate("document.body.innerText.replace(/\\s+/g, ' ').trim()")


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 0. 버전 · CONFIG
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    sync_src = page.request.get(URL + "sync.js").text()
    check("sw.js 캐시 버전 twolog-v49", 'const VERSION = "twolog-v49"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:1])
    check("app.js 버전 상수 v49", 'var APP_VERSION = "v49"' in app_js)
    check("sync.js CONFIG.supabaseUrl 반영", PROJ in sync_src,
          [l.strip() for l in sync_src.splitlines() if "supabaseUrl:" in l][:1])
    check("sync.js CONFIG.supabaseAnonKey 반영(publishable)", PUB_KEY in sync_src)
    check("service_role 키는 들어 있지 않음", "service_role" not in sync_src.lower())

    # ==================================================================
    # 1. remote 모드 첫 로드 — 진짜 모듈·진짜 프로젝트, 계정은 만들지 않음
    # ==================================================================
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)

    t0 = time.time()
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    took = round(time.time() - t0, 1)
    first = page.evaluate("""(() => {
      const li = document.querySelector('#s-login .login');
      const h1 = li ? li.querySelector('h1') : null;
      const inputs = li ? Array.from(li.querySelectorAll('input')).map(i => i.name) : [];
      const btn = li ? li.querySelector('.btn-primary') : null;
      return {mode: (window.TwoLogStore || {}).mode, remote: window.TwoLog && window.TwoLog.isRemote(),
              h1: h1 ? h1.textContent.trim() : null, inputs: inputs,
              btn: btn ? btn.textContent.trim() : null,
              tabs: document.querySelectorAll('#tabbar .tab').length,
              loginShown: !!li && li.getBoundingClientRect().height > 100,
              textLen: document.body.innerText.trim().length,
              statusState: ((window.TwoLogStore || {}).status || {}).state};
    })()""")
    check("CONFIG 값으로 isRemote() == true", first["remote"] is True)
    check("저장 모드가 remote", first["mode"] == "remote", first["mode"])
    check("로그인 전: 흰 화면 없이 로그인 화면이 뜸(2~20초 안)", first["loginShown"] and first["textLen"] > 30,
          (first["loginShown"], first["textLen"], took))
    check("로그인 화면 문구 「다시, 우리」", first["h1"] == "다시, 우리", first["h1"])
    check("이메일·비밀번호 입력칸", first["inputs"] == ["email", "password"], first["inputs"])
    check("로그인 버튼", first["btn"] == "로그인", first["btn"])
    check("로그인 전에는 하단 탭을 그리지 않음", first["tabs"] == 0, first["tabs"])
    check("스키마·세션 준비 전 로드에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    page.screenshot(path=os.path.join(SHOT, "login-v25.png"))

    # 진짜 프로젝트 응답(읽기만) — anon 키가 살아 있는지, 스키마가 들어갔는지
    health = page.request.get(PROJ + "/auth/v1/health", headers={"apikey": PUB_KEY})
    check("Supabase 인증 API 응답 200 (anon 키 유효)", health.status == 200, health.status)
    tbl = page.request.get(PROJ + "/rest/v1/couples?select=id&limit=1",
                           headers={"apikey": PUB_KEY, "Authorization": "Bearer " + PUB_KEY})
    schema_ready = tbl.status == 200
    print("INFO 스키마 상태: HTTP %d %s" % (tbl.status, tbl.text()[:120].replace("\n", " ")))
    ctx.close()

    # ==================================================================
    # 2. remote 모드 계정 흐름 — esm.sh 모듈만 stub 로 교체
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.route(ESM, lambda route: route.fulfill(status=200,
                                                content_type="application/javascript", body=STUB))

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=15000)

    # --- 계정 만들기 화면으로 전환
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(300)
    up = page.evaluate("""(() => {
      const li = document.querySelector('#s-login .login');
      const b = li.querySelector('.btn-primary');
      return {h1: li.querySelector('h1').textContent.trim(), btn: b.textContent.trim(),
              pwAuto: li.querySelector('input[name=password]').getAttribute('autocomplete')};
    })()""")
    check("「처음이에요 · 계정 만들기」로 가입 화면", up["h1"] == "처음 오셨네요" and up["btn"] == "계정 만들기", up)
    check("가입 화면 비밀번호는 new-password", up["pwAuto"] == "new-password", up["pwAuto"])
    page.screenshot(path=os.path.join(SHOT, "login-v25-signup.png"))

    # --- 가입 → 홈
    EMAIL = "soryeong.test@twolog.app"
    PW = "twolog1234"
    page.fill('#s-login input[name="email"]', EMAIL)
    page.fill('#s-login input[name="password"]', PW)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=15000)
    page.wait_for_timeout(700)
    home = page.evaluate("""(() => ({
      tabs: document.querySelectorAll('#tabbar .tab').length,
      home: (document.querySelector('#s-home h1, #s-home .brand b') || {}).textContent || '',
      loginScreen: !!document.querySelector('#s-login.active'),
      coupleId: (window.TwoLogStore || {}).coupleId,
      email: ((window.TwoLogUI || {}).state || {}).auth
    }))()""")
    check("가입 뒤 홈으로 들어옴 (탭 5개 · 로그인 화면 아님)", home["tabs"] == 5 and not home["loginScreen"], home)
    check("remote 세션에 커플 행이 만들어짐", bool(home["coupleId"]), home["coupleId"])
    check("가입한 이메일이 상태에 들어감", (home["email"] or {}).get("email") == EMAIL, home["email"])
    page.screenshot(path=os.path.join(SHOT, "home-v25-remote.png"))

    # --- My 탭: 이메일 · 자동 동기화 · 초대 코드
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(600)
    my = page.evaluate("""(() => {
      const s = document.querySelector('#s-set');
      return {txt: s.innerText.replace(/\\s+/g, ' '),
              ver: (s.querySelector('.app-ver') || {}).textContent || '',
              chip: Array.from(s.querySelectorAll('.chip')).map(c => c.textContent.trim()),
              synced: /두 대 실시간 동기화 중/.test(s.innerText),
              offline: /오프라인/.test(s.innerText),
              code: (window.TwoLogStore.couple.myCode() || '')};
    })()""")
    check("My 탭 맨 윗줄 「버전 v49」", "v49" in my["ver"], my["ver"])
    check("My 탭에 가입 이메일 표시", EMAIL in my["txt"], my["txt"][:120])
    check("동기화 「두 대 실시간 동기화 중」 · 배지 「자동」", my["synced"] and "자동" in my["chip"], my["chip"])
    check("계정 만들 때 초대 코드 6자리가 자동 생성", re.fullmatch(r"\d{6}", my["code"]) is not None, my["code"])
    page.screenshot(path=os.path.join(SHOT, "my-v25-remote.png"))

    # --- 커플 연결 시트: 내 코드 · 코드 새로 만들기 · 상대 코드 입력
    first_code = my["code"]
    page.locator('#s-set [data-act="linkSheet"]').first.click()
    page.wait_for_timeout(450)
    sheet = page.evaluate("""(() => ({
      open: document.getElementById('sheetWrap').classList.contains('open'),
      code: (document.querySelector('#sheet .set-code') || {}).textContent || '',
      newBtn: !!document.querySelector('#sheet [data-act="newCode"]'),
      input: !!document.querySelector('#sheet #linkForm input[name="code"]'),
      sub: (document.querySelector('#sheet .sheet-sub') || {}).textContent || ''
    }))()""")
    check("커플 연결 시트가 열리고 내 초대 코드를 보여줌",
          sheet["open"] and sheet["code"].replace(" ", "") == first_code, (sheet["open"], sheet["code"], first_code))
    check("「상대 초대 코드」 입력칸이 있음", sheet["input"], sheet)
    page.screenshot(path=os.path.join(SHOT, "link-v25.png"))

    page.locator('#sheet [data-act="newCode"]').click()
    page.wait_for_timeout(800)
    second = page.evaluate("""(() => ({
      shown: (document.querySelector('#sheet .set-code') || {}).textContent || '',
      stored: (window.TwoLogStore.couple.myCode() || ''),
      server: (window.__stub.couples[0] || {}).invite_code || ''
    }))()""")
    check("「코드 새로 만들기」로 코드가 실제로 바뀜(서버 행까지)",
          second["stored"] != first_code and second["server"] == second["stored"] and
          second["shown"].replace(" ", "") == second["stored"], second)
    check("새 코드도 6자리 숫자", re.fullmatch(r"\d{6}", second["stored"]) is not None, second["stored"])

    partner_code = "654321" if second["stored"] != "654321" else "654322"
    # 상대 기기가 먼저 계정을 만들고 코드를 들고 있는 상황(진짜 DB 의 상대 커플 행)
    page.evaluate("""(code) => {
      const st = window.__stub;
      st.couples.push({id: 'partner-couple', invite_code: code, members: ['partner-user'],
        me: '\uC900\uC601', you: '\uC18C\uC601', since: '2026-05-01', phrase: '\uD568\uAED8\uD55C \uC9C0', fmt: 'D',
        colors: {me: '#BCE0F7', you: '#F7C6D4'}, sched: {me: '#BCE0F7', you: '#F7C6D4', both: '#D6C5F7'}});
    }""", partner_code)
    page.fill('#sheet #linkForm input[name="code"]', partner_code)
    page.locator('#sheet #linkForm button[type="submit"]').click()
    page.wait_for_timeout(1200)
    joined = page.evaluate("""(() => ({
      open: document.getElementById('sheetWrap').classList.contains('open'),
      members: window.TwoLogStore.couple.memberCount(),
      connected: !!((window.TwoLogUI.state || {}).link || {}).connected,
      chip: (document.querySelector('#s-set [data-act="linkSheet"]') || {}).textContent || '',
      toast: (document.getElementById('toast') || {}).textContent || ''
    }))()""")
    check("상대 코드를 넣으면 커플이 연결됨", joined["members"] == 2 and joined["connected"], joined)
    check("My 탭 연결 표시가 「연결됨」으로 바뀜", "연결됨" in joined["chip"], joined["chip"])
    page.screenshot(path=os.path.join(SHOT, "link-v25-connected.png"))

    # 연결된 뒤에도 내 초대 코드는 그대로 보임
    page.locator('#s-set [data-act="linkSheet"]').first.click()
    page.wait_for_timeout(450)
    conn = page.evaluate("""(() => ({
      code: (document.querySelector('#sheet .set-code') || {}).textContent || '',
      on: /커플 연결됨/.test(document.querySelector('#sheet').innerText),
      unlink: !!document.querySelector('#sheet [data-act="unlink"]')
    }))()""")
    # 연결되면 두 사람은 «상대가 만들었던 그 커플 행» 하나를 함께 봅니다 —
    # 그래서 코드도 그 행의 코드(상대 코드)로 하나가 됩니다.
    check("연결된 뒤 시트에 내 초대 코드 · 연결됨 · 연결 해제", conn["on"] and conn["unlink"] and
          conn["code"].replace(" ", "") == partner_code, conn)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(350)

    # --- 로그아웃 → 로그인 화면
    page.locator('#s-set [data-act="logout"]').first.click()
    page.wait_for_timeout(450)
    page.locator("#sheetForm button[type=submit]").click()
    page.wait_for_selector("#s-login .login", timeout=10000)
    out = page.evaluate("""(() => ({
      tabs: document.querySelectorAll('#tabbar .tab').length,
      h1: (document.querySelector('#s-login h1') || {}).textContent || '',
      email: (document.querySelector('#s-login input[name=email]') || {}).value
    }))()""")
    check("로그아웃하면 로그인 화면으로 (탭 숨김)", out["tabs"] == 0 and out["h1"] == "다시, 우리", out)

    # --- 다시 로그인
    page.fill('#s-login input[name="email"]', EMAIL)
    page.fill('#s-login input[name="password"]', PW)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=15000)
    page.wait_for_timeout(800)
    back = page.evaluate("""(() => ({
      tabs: document.querySelectorAll('#tabbar .tab').length,
      members: window.TwoLogStore.couple.memberCount(),
      email: ((window.TwoLogUI.state || {}).auth || {}).email
    }))()""")
    check("같은 이메일로 다시 로그인 — 연결 상태 유지", back["tabs"] == 5 and back["members"] == 2 and back["email"] == EMAIL, back)

    # --- 틀린 비밀번호: 오류를 알려 주고 로그인 화면에 머무름
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(450)
    page.locator('#s-set [data-act="logout"]').first.click()
    page.wait_for_timeout(400)
    page.locator("#sheetForm button[type=submit]").click()
    page.wait_for_selector("#s-login .login", timeout=10000)
    page.fill('#s-login input[name="email"]', EMAIL)
    page.fill('#s-login input[name="password"]', "wrongpass")
    page.locator("#s-login .btn-primary").click()
    page.wait_for_timeout(900)
    bad = page.evaluate("""(() => ({
      toast: (document.getElementById('toast') || {}).textContent || '',
      login: !!document.querySelector('#s-login .login'),
      tabs: document.querySelectorAll('#tabbar .tab').length,
      btn: (document.querySelector('#s-login .btn-primary') || {}).textContent || ''
    }))()""")
    check("틀린 비밀번호는 안내만 하고 로그인 화면에 머무름",
          "들어가지 못했어요" in bad["toast"] and bad["login"] and bad["tabs"] == 0, bad)
    check("로그인 버튼이 다시 눌리는 상태로 복귀", bad["btn"] == "로그인", bad["btn"])
    check("remote 흐름 전체에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 3. 스키마를 넣기 전 프로젝트 — 멈추지 않고 오프라인으로 표시
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__STUB_SCHEMA_MISSING = true;")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.route(ESM, lambda route: route.fulfill(status=200,
                                                content_type="application/javascript", body=STUB))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=15000)
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', "schema.later@twolog.app")
    page.fill('#s-login input[name="password"]', "twolog1234")
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=15000)
    page.wait_for_timeout(900)
    nosc = page.evaluate("""(() => {
      const s = document.querySelector('#s-set');
      return {tabs: document.querySelectorAll('#tabbar .tab').length,
              login: !!document.querySelector('#s-login.active'),
              textLen: document.body.innerText.trim().length,
              statusState: ((window.TwoLogStore || {}).status || {}).state};
    })()""")
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    nosc["myText"] = page.evaluate("document.querySelector('#s-set').innerText.replace(/\\s+/g,' ').slice(0,200)")
    check("스키마가 없어도 앱이 멈추지 않음 (홈 렌더 · 흰 화면 아님)",
          nosc["tabs"] == 5 and not nosc["login"] and nosc["textLen"] > 30, nosc)
    check("이때 동기화는 「오프라인 · 다시 연결하는 중」으로 표시",
          "오프라인" in nosc["myText"] or nosc["statusState"] == "offline", (nosc["statusState"], nosc["myText"][:80]))
    check("스키마 없음 상황에서도 스크립트 오류(멈춤) 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 4. local 모드(?sync=local) — 예전 동작 그대로
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(600)
    loc = page.evaluate("""(() => ({
      mode: (window.TwoLogStore || {}).mode,
      tabs: document.querySelectorAll('#tabbar .tab').length,
      login: !!document.querySelector('#s-login.active')
    }))()""")
    check("강제 local 모드에서 remote 로 가지 않음", loc["mode"] == "local" and loc["tabs"] == 5 and not loc["login"], loc)

    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(500)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(450)
    page.fill('#sheetForm input[name="title"]', "로컬 저장 확인")
    page.locator("#evSave").click()
    page.wait_for_timeout(700)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(500)
    kept = page.locator('#s-cal .ev .t', has_text="로컬 저장 확인").count()
    check("local 모드는 예전처럼 이 기기에 저장·복원", kept >= 1, kept)

    # 주소 파라미터로도 같은 방식
    page.goto(URL + "?sync=local", wait_until="networkidle")
    page.wait_for_timeout(500)
    check("?sync=local 로도 local 모드", page.evaluate("(window.TwoLogStore||{}).mode") == "local",
          page.evaluate("(window.TwoLogStore||{}).mode"))

    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    chip = page.evaluate("document.querySelector('#s-set').innerText.replace(/\\s+/g,' ')")
    check("local 모드 My 탭에 「로컬」 표시", "로컬" in chip and "이 기기에 저장 중" in chip, chip[:120])
    check("local 모드에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    page.screenshot(path=os.path.join(SHOT, "my-v25-local.png"))
    ctx.close()

    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
