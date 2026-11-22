"""투로그 v30 확인 — 사진첩 폴라로이드를 더 작고 아담하게.

1) 버전: sw.js 캐시 twolog-v45 · APP_VERSION v45
2) 사진첩 목록의 폴라로이드 카드가 v29보다 확실히 작아짐
   - 사진 한 칸(정사각) 118.7px → 93.3px, 카드 130.7 → 103.3px, 카드 높이 142.7 → 113.3px
   - 흰 프레임 위·옆 5px, 아래 턱 15px (v29 6px·18px), 캡션 글씨 9px (v29 9.5px)
3) 3열·하루 3개(+N)·살짝 기울임은 그대로, 카드는 이제 서로 겹치지 않고 사이가 띄워짐
4) 사진·날짜·캡션은 그대로 보이고, 눌러서 크게 보기(넘기기)가 열림
5) 사진첩 달력 보기(photo-cal)는 v24 그대로 — 손대지 않음
6) 다른 화면(홈·캘린더·노트·My)은 그대로, 페이지 오류 없음

    python3 tests/v30.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

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


def tab(page, idx, wait=500):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def pola_state(page):
    return page.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('#s-photo .pola'));
      const polas = document.querySelector('#s-photo .polas');
      if (!els.length) return {n: 0};
      const p = els[0], pic = p.querySelector('.pola-pic'), chin = p.querySelector('.pola-chin');
      const cs = getComputedStyle(p), pcs = getComputedStyle(pic);
      const gs = getComputedStyle(polas);
      const r = e => e.getBoundingClientRect();
      const rows = els.slice(0, 3);
      return {n: els.length,
        cols: gs.gridTemplateColumns.split(' ').length,
        gap: gs.columnGap,
        cardW: parseFloat(cs.width), cardH: parseFloat(cs.height),
        picW: parseFloat(pcs.width), picH: parseFloat(pcs.height),
        padTop: cs.paddingTop, padSide: cs.paddingLeft, padBottom: cs.paddingBottom,
        chinFs: chin ? getComputedStyle(chin).fontSize : null,
        chinH: chin ? parseFloat(getComputedStyle(chin).height) : null,
        chinText: chin ? chin.textContent.trim() : null,
        shadow: cs.boxShadow,
        radius: cs.borderTopLeftRadius,
        bg: cs.backgroundColor,
        tilts: els.slice(0, 3).map(e => getComputedStyle(e).transform),
        /* 카드 사이 실제 간격(기울어진 카드의 바깥 상자를 기준) */
        gaps: rows.length > 1 ? Math.round(r(rows[1])['left'] - r(rows[0])['right']) : null,
        overflow: document.querySelector('#s-photo').scrollWidth - document.querySelector('#s-photo').clientWidth,
        imgs: els.map(e => { const i = e.querySelector('.pola-pic img, .pola-pic svg'); return !!i; }),
        more: (document.querySelector('#s-photo .pola-more') || {}).textContent || null,
        days: Array.from(document.querySelectorAll('#s-photo .pday'))
                .map(d => d.querySelectorAll('.pola').length),
        heads: Array.from(document.querySelectorAll('#s-photo .pday-hd')).map(h => h.innerText.replace(/\\n/g, ' ')),
      };
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
    css = page.request.get(URL + "styles.css").text()
    check("sw.js 캐시 버전 twolog-v45", 'const VERSION = "twolog-v45"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v37", 'var APP_VERSION = "v45"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v45", 'const SHELL = "shell-" + VERSION' in sw)
    check("달력 칸(pcell)은 정사각(aspect-ratio)", "aspect-ratio:1/1" in css.replace(" ", "") and ".pcal-grid" in css)

    # 예시 데이터로 한 번 열어 상태를 만들고, 저장이 되는 일반 모드로 옮겨요
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(800)

    # ==================================================================
    # 2. 사진첩 — v37: 폴라로이드 대신 정사각형 사진 3열 (간격 3px)
    # ==================================================================
    tab(page, 3, 700)
    ph = pola_state(page)
    check("사진첩에 사진 타일이 보임", ph["n"] >= 3, ph["n"])
    check("한 줄에 3열 그대로", ph["cols"] == 3, ph["cols"])
    check("사진 칸 111~118px (좌우 20px·간격 3px)", 111 <= ph["picW"] <= 118, ph["picW"])
    check("카드 폭 = 사진 칸 (흰 틀 없음)", abs(ph["cardW"] - ph["picW"]) <= 0.6, (ph["cardW"], ph["picW"]))
    check("사진 칸이 정사각", abs(ph["picW"] - ph["picH"]) <= 0.5, (ph["picW"], ph["picH"]))
    check("흰 프레임·아래 턱 없음 (padding 0)",
          ph["padTop"] == "0px" and ph["padSide"] == "0px" and ph["padBottom"] == "0px",
          (ph["padTop"], ph["padSide"], ph["padBottom"]))
    # v40: 사진 아래 캡션 줄은 없앴어요 — 사진만 보입니다
    check("사진 아래 캡션 줄 없음 (v40)", not ph["chinText"] and not ph["chinH"],
          (ph["chinH"], ph["chinText"]))
    check("그림자·기울임·바탕 없음", ph["shadow"] in (None, "none", "")
          and all(t in ("none", "matrix(1, 0, 0, 1, 0, 0)") for t in ph["tilts"]),
          (str(ph["shadow"])[:20], ph["tilts"]))
    check("사진 사이 간격 3px", ph["gaps"] is not None and abs(ph["gaps"] - 3) <= 1, ph["gaps"])
    check("사진첩 가로 넘침 없음", ph["overflow"] <= 1, ph["overflow"])
    check("사진이 모두 그려짐(이미지 또는 그림)", all(ph["imgs"]), ph["imgs"])
    check("하루 3개·넘치면 +N 그대로", all(d <= 3 for d in ph["days"]) and ph["more"] == "+3",
          (ph["days"], ph["more"]))
    # v39: 날짜 머리글에서 요일을 뺐습니다 — 「M월 D일」만 (옆에 태그는 글씨로)
    check("날짜 머리글은 M월 D일 (요일 없음)", all("월" in h and "요일" not in h for h in ph["heads"]), ph["heads"])
    page.screenshot(path=os.path.join(SHOT, "photo-v30.png"))
    page.screenshot(path=os.path.join(SHOT, "photo-v30-full.png"), full_page=True)

    # ==================================================================
    # 3. 작아져도 눌러서 크게 보기·넘기기는 그대로
    # ==================================================================
    # v39: 목록은 예전 → 최근 순이라 사진이 가장 많은 «최근 날짜»(맨 아래)를 봅니다
    first_title = page.evaluate("(document.querySelector('#s-photo .pday:last-child .pola .pola-chin') || {}).textContent || ''")
    page.locator("#s-photo .pola").last.click()
    page.wait_for_timeout(500)
    page.locator("#s-photo .dg-cell").first.click()   # v38: 날짜 모아보기를 거쳐 크게 보기
    page.wait_for_timeout(500)
    pv = page.evaluate("""() => { const v = document.querySelector('#sheet .pview');
      const im = v ? v.querySelector('img, svg') : null;
      const c = document.querySelector('#sheet .pv-count');
      return {open: !!v, h: v ? Math.round(v.getBoundingClientRect().height) : 0,
              img: !!im, count: c ? c.textContent.trim() : null,
              head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent}; }""")
    slides = page.evaluate("document.querySelectorAll('#sheet .pv40-slide').length")
    check("작은 폴라로이드를 눌러도 크게 보기가 열림", pv["open"] and pv["img"] and pv["h"] > 200, pv)
    # v40: 크게 보기는 사진만 — 옆으로 밀어서 같은 날 사진을 넘겨요
    check("같은 날 사진 6장이 옆으로 이어짐", slides == 6, slides)
    page.screenshot(path=os.path.join(SHOT, "photo-v30-viewer.png"))
    page.evaluate("(() => { const s = document.querySelector('#sheet .pv40-strip'); s.scrollBy({ left: s.clientWidth }); })()")
    page.wait_for_timeout(420)
    left2 = page.evaluate("Math.round(document.querySelector('#sheet .pv40-strip').scrollLeft)")
    check("옆으로 밀면 다음 사진으로 넘어감", left2 > 100, left2)
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    page.locator('#s-photo [data-act="photoDayBack"]').click()   # v38: 모아보기에서 목록으로
    page.wait_for_timeout(450)

    # ==================================================================
    # 4. 사진첩 달력 보기(photo-cal)는 손대지 않음 — v24 크기 그대로
    # ==================================================================
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(600)
    cal = page.evaluate("""() => { const g = document.querySelector('#s-photo .pcal-grid');
      const c = g ? g.children[0] : null;
      return {on: !!g, h: c ? Math.round(c.getBoundingClientRect().height) : 0,
              cols: g ? getComputedStyle(g).gridTemplateColumns.split(' ').length : 0,
              polas: document.querySelectorAll('#s-photo .pola').length}; }""")
    check("달력 보기로 전환", cal["on"] and cal["cols"] == 7 and cal["polas"] == 0, cal)
    check("달력 칸은 정사각형(v37) — 세로로 늘리지 않음", cal["h"] == 50, cal["h"])
    page.screenshot(path=os.path.join(SHOT, "photo-v30-cal.png"))
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(500)
    back = page.evaluate("document.querySelectorAll('#s-photo .pola').length")
    check("다시 누르면 목록으로", back >= 3, back)

    # ==================================================================
    # 5. 다른 화면 그대로 · 버전 표시 · 오류 없음
    # ==================================================================
    for idx, name, sid in ((0, "홈", "s-home"), (1, "캘린더", "s-cal"), (2, "노트", "s-diary"), (4, "My", "s-set")):
        tab(page, idx, 550)
        ok = page.evaluate("(id) => { const el = document.getElementById(id);"
                           " return !!el && el.classList.contains('active') && el.innerText.trim().length > 0; }", sid)
        check("%s 화면이 정상으로 뜸" % name, bool(ok), sid)
    ver = page.inner_text("#s-set .app-ver")
    check("My 맨 위 버전 표시가 v45", "v45" in ver, ver)
    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:4])

    ctx.close()
    browser.close()

print()
if fails:
    print("FAILED %d: %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS")
