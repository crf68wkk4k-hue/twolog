"""라이브 배포 확인 — https://crf68wkk4k-hue.github.io/twolog/ 가 방금 올린 버전을 서빙하는지.

    python3 tests/live.py

- 주요 파일 HTTP 200 (index · app.js · sync.js · sw.js · styles.css · manifest · 아이콘)
- sw.js 캐시 이름 = app.js 버전 상수 (지금은 twolog-v46 / v46)
- 라이브 첫 화면이 remote 모드 로그인 화면으로 뜨고 콘솔 오류·4xx/5xx 없음
- ?sync=local 로는 예전 로컬 모드로 열림
"""
import os, sys
from playwright.sync_api import sync_playwright

LIVE = "https://crf68wkk4k-hue.github.io/twolog/"
LIB = "/workspace/.libs/usr/lib/x86_64-linux-gnu"
CHROMES = [None,
    "/workspace/.cache/ms-playwright/chromium_headless_shell-1255/chrome-headless-shell-linux64/chrome-headless-shell",
    "/workspace/.cache/ms-playwright/chromium-1255/chrome-linux64/chrome"]
fails = []
def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (("  :: " + str(extra)) if extra else ""))
    if not cond: fails.append(name)

def launch(p):
    env = dict(os.environ)
    if os.path.isdir(LIB): env["LD_LIBRARY_PATH"] = LIB
    last = None
    for exe in CHROMES:
        try:
            kw = {"args": ["--no-sandbox"], "env": env}
            if exe: kw["executable_path"] = exe
            return p.chromium.launch(**kw)
        except Exception as e:
            last = e
    raise last

with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    errs, badresp = [], []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.on("response", lambda r: badresp.append("%s %s" % (r.status, r.url)) if r.status >= 400 else None)

    for path in ["", "index.html", "styles.css", "app.js", "sync.js", "sw.js", "manifest.json",
                 "icons/icon-192.png", "icons/apple-touch-icon.png"]:
        r = page.request.get(LIVE + path)
        check("HTTP 200 " + (path or "/"), r.status == 200, r.status)

    sw = page.request.get(LIVE + "sw.js").text()
    check("라이브 sw.js 가 twolog-v46", 'const VERSION = "twolog-v46"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:1])
    check("라이브 app.js 가 v46", 'var APP_VERSION = "v46"' in page.request.get(LIVE + "app.js").text())

    page.goto(LIVE, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=25000)
    page.wait_for_timeout(1200)
    st = page.evaluate("""(() => ({
      mode: (window.TwoLogStore || {}).mode, remote: window.TwoLog && window.TwoLog.isRemote(),
      h1: (document.querySelector('#s-login h1') || {}).textContent || '',
      tabs: document.querySelectorAll('#tabbar .tab').length,
      textLen: document.body.innerText.trim().length,
      status: ((window.TwoLogStore || {}).status || {}).state }))()""")
    check("라이브가 remote 모드로 뜸", st["mode"] == "remote" and st["remote"] is True, st)
    check("로그인 화면이 흰 화면 없이 렌더", st["h1"] == "다시, 우리" and st["textLen"] > 30 and st["tabs"] == 0, st)
    page.wait_for_timeout(2500)
    cache = page.evaluate("""navigator.serviceWorker.ready.then(() => caches.keys())""")
    check("서비스워커 캐시 shell-twolog-v46", any("twolog-v46" in c for c in (cache or [])), cache)
    check("라이브 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:4])
    check("라이브에서 4xx/5xx 응답 없음", len(badresp) == 0, badresp[:4])
    page.screenshot(path="/workspace/downloads/twolog-screens/live-v29-login.png")

    page.goto(LIVE + "?sync=local", wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    loc = page.evaluate("""(() => ({mode: (window.TwoLogStore||{}).mode,
      tabs: document.querySelectorAll('#tabbar .tab').length}))()""")
    check("라이브에서 ?sync=local 은 로컬 모드", loc["mode"] == "local" and loc["tabs"] == 5, loc)
    check("local 모드까지 포함해 콘솔 오류 없음", len(errs) == 0, errs[:4])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
