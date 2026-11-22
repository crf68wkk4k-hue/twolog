"""투로그 v32 확인 — 달력 칸 일정 막대(.ebar) 글씨를 늘 흰색으로.

전에는 막대 글씨를 배경 밝기(inkOn)에 맞춰 밝은 일정은 검정, 어두운 일정은 흰색으로
칠했습니다. v32 부터는 달력 칸 안의 일정 막대 글씨만 배경과 상관없이 항상
#FFFFFF(rgb(255, 255, 255))입니다.

1) 버전: sw.js 캐시 twolog-v46 · APP_VERSION v46 · My 탭 「버전 v46」
2) 코드: app.js 의 .ebar 렌더가 color:#FFFFFF 고정, styles.css 의 .ebar 도 흰색
3) 밝은 일정(#E8D48B · #D8C7B8 · #BFD4DB)과 어두운 일정(#3D5C82 · #625A7F · #111111)
   모두 달력 막대 글씨가 rgb(255, 255, 255) — 여러 칸에 걸친 막대도 같음
   (막대 배경색은 일정 색 그대로)
4) inkOn 은 다른 곳에서 그대로: 홈 섹션 제목 줄(--sec-ink)·노트 카드 제목은
   밝은 바탕이면 검정, 아주 어두운 바탕이면 흰색
5) 다크 모드에서도 막대 글씨 흰색
6) 다른 화면(홈·노트·사진첩·My) 그대로, 콘솔/페이지 오류 없음

    python3 tests/v32.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import datetime, functools, http.server, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

WHITE = "rgb(255, 255, 255)"
INK = "rgb(17, 17, 17)"

LIGHT = ["#E8D48B", "#D8C7B8", "#BFD4DB"]
DARK = ["#3D5C82", "#625A7F", "#111111"]

fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + (("  :: " + str(extra)) if extra else ""))
    if not cond:
        fails.append(name)


def rgb(hex6):
    h = hex6.lstrip("#")
    return "rgb(%d, %d, %d)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def d(offset):
    return (datetime.date.today() + datetime.timedelta(days=offset)).isoformat()


# 달력 막대는 한 주에 두 줄까지만 펼치므로, 겹치지 않게 이번 달 날짜에 하나씩 놓습니다
_T = datetime.date.today()
_MONTH_FIRST = _T.replace(day=1)
MONTH = _MONTH_FIRST.strftime("%Y-%m")


def iso(day):
    return _MONTH_FIRST.replace(day=day).isoformat()


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


def bars(page):
    """달력 칸 안의 막대(.ebar) — 제목·배경색·글씨색"""
    return page.evaluate("""() => Array.from(document.querySelectorAll('#s-cal .cal-bars .ebar')).map(b => {
      const cs = getComputedStyle(b);
      return {t: b.textContent.trim(), bg: cs.backgroundColor, color: cs.color,
              inline: b.getAttribute('style') || ''};
    })""")


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전 · 코드
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    css = page.request.get(URL + "styles.css").text()
    check("sw.js 캐시 버전 twolog-v46", 'const VERSION = "twolog-v46"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v44", 'var APP_VERSION = "v46"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    # .ebar 렌더 줄이 흰색 고정인지 (inkOn(edge) 가 사라졌는지)
    ebar_line = [l for l in app_js.splitlines() if 'class=\\"ebar' in l or "class=\"ebar" in l]
    hold = app_js.split('var mid = b.eCol > b.sCol')[1][:600]
    check("app.js: .ebar 인라인 style 이 color:#FFFFFF 고정", '"; color:#FFFFFF"' in hold, hold[:220])
    check("app.js: .ebar 렌더에 inkOn(edge) 가 더 이상 없음", "inkOn(edge)" not in app_js, "inkOn(edge) 발견")
    # v38: 노트 카드 제목은 띠 색과 상관없이 늘 검정 — inkOn 은 홈 섹션 제목 줄에서만 씁니다
    check("app.js: inkOn 은 홈 섹션 제목 줄에서 그대로",
          "return ' style=\"--sec-bg:' + bg + \";--sec-ink:\" + inkOn(bg) + '\"'" in app_js)
    css_ebar = re.search(r"\.ebar\{([^}]*)\}", css)
    check("styles.css: .ebar 기본 글씨색도 #FFFFFF",
          bool(css_ebar) and "color:#FFFFFF" in css_ebar.group(1), css_ebar.group(1)[:200] if css_ebar else None)
    ctx.close()

    # ==================================================================
    # 2. 달력 막대 — 밝은 일정도 어두운 일정도 글씨는 흰색
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(700)
    tab(page, 1, 600)

    made = page.evaluate("""(args) => {
      const S = window.TwoLogUI.state;
      const mk = (t, c, a, b) => ({ id: 'v32e' + t, date: a, endDate: b || a,
        time: '', title: t, type: 'etc', memo: '', color: c, who: 'both' });
      const evs = [];
      args.light.forEach((c, i) => evs.push(mk('밝은 ' + (i + 1), c, args.days[i])));
      args.dark.forEach((c, i) => evs.push(mk('어두운 ' + (i + 1), c, args.days[i + 3])));
      evs.push(mk('색없음', '', args.days[6]));
      evs.push(mk('밝은 여러날', args.light[0], args.multi[0], args.multi[1]));
      evs.push(mk('어두운 여러날', args.dark[0], args.multi[2], args.multi[3]));
      S.events = evs;
      S.ui.selDate = args.days[0]; S.ui.calMonth = args.month;
      window.TwoLogUI.rerender();
      return S.events.length;
    }""", {"light": LIGHT, "dark": DARK, "month": MONTH,
           "days": [iso(2), iso(4), iso(6), iso(8), iso(10), iso(12), iso(14)],
           "multi": [iso(17), iso(19), iso(21), iso(23)]})
    page.wait_for_timeout(700)
    page.locator("#s-cal .cal").scroll_into_view_if_needed()
    page.wait_for_timeout(300)

    got = bars(page)
    check("달력에 일정 막대가 여러 개 그려짐", len(got) >= 8, len(got))
    check("모든 막대 글씨가 rgb(255, 255, 255)",
          len(got) >= 8 and all(b["color"] == WHITE for b in got), [(b["t"], b["color"]) for b in got])
    check("막대 인라인 style 도 color:#FFFFFF",
          all("color:#FFFFFF" in b["inline"] or "color: #FFFFFF" in b["inline"] for b in got),
          [b["inline"][-60:] for b in got[:3]])

    by_title = {b["t"]: b for b in got}
    light_ok = all(by_title.get("밝은 %d" % (i + 1), {}).get("color") == WHITE for i in range(3))
    dark_ok = all(by_title.get("어두운 %d" % (i + 1), {}).get("color") == WHITE for i in range(3))
    check("밝은 일정(#E8D48B · #D8C7B8 · #BFD4DB) 막대 글씨 흰색", light_ok,
          [(t, by_title.get(t, {}).get("color")) for t in ("밝은 1", "밝은 2", "밝은 3")])
    check("어두운 일정(#3D5C82 · #625A7F · #111111) 막대 글씨 흰색", dark_ok,
          [(t, by_title.get(t, {}).get("color")) for t in ("어두운 1", "어두운 2", "어두운 3")])
    check("색을 고르지 않은 일정(담당자 색)도 글씨 흰색",
          by_title.get("색없음", {}).get("color") == WHITE, by_title.get("색없음"))
    check("여러 칸에 걸친 밝은 일정 막대도 글씨 흰색",
          by_title.get("밝은 여러날", {}).get("color") == WHITE, by_title.get("밝은 여러날"))
    check("여러 칸에 걸친 어두운 일정 막대도 글씨 흰색",
          by_title.get("어두운 여러날", {}).get("color") == WHITE, by_title.get("어두운 여러날"))
    # 배경은 일정 색 그대로 (글씨색만 바꾼 것이지 색 자체를 잃지 않았는지)
    bg_ok = (by_title.get("밝은 1", {}).get("bg") == rgb(LIGHT[0])
             and by_title.get("어두운 1", {}).get("bg") == rgb(DARK[0])
             and by_title.get("밝은 2", {}).get("bg") == rgb(LIGHT[1])
             and by_title.get("어두운 3", {}).get("bg") == rgb(DARK[2]))
    check("막대 배경색은 고른 일정 색 그대로", bg_ok,
          [(b["t"], b["bg"]) for b in got if b["t"] in ("밝은 1", "밝은 2", "어두운 1", "어두운 3")])
    page.screenshot(path=os.path.join(SHOT, "cal-v32-white-bars.png"))

    # ==================================================================
    # 3. inkOn 은 다른 곳에서 그대로 — 홈 섹션 제목 줄 · 노트 카드 제목
    # ==================================================================
    def home_sec_ink(bg):
        page.evaluate("""(bg) => {
          window.TwoLogUI.state.theme.homeTitleBg = bg;
          window.TwoLogUI.rerender();
        }""", bg)
        page.wait_for_timeout(400)
        return page.evaluate("""() => {
          const el = document.querySelector('#s-home .home-sec .sec-tint');
          const h2 = el ? el.querySelector('h2') : null;
          return {sec: el ? getComputedStyle(el).color : null,
                  h2: h2 ? getComputedStyle(h2).color : null,
                  ink: el ? el.style.getPropertyValue('--sec-ink').trim() : null};
        }""")

    tab(page, 0, 500)
    light_sec = home_sec_ink(LIGHT[0])
    check("홈 섹션 제목 줄: 밝은 바탕이면 글씨 검정(inkOn 그대로)",
          light_sec["h2"] == INK and light_sec["ink"] == "#111111", light_sec)
    dark_sec = home_sec_ink(DARK[2])
    check("홈 섹션 제목 줄: 어두운 바탕이면 글씨 흰색(inkOn 그대로)",
          dark_sec["h2"] == WHITE and dark_sec["ink"] == "#FFFFFF", dark_sec)
    page.screenshot(path=os.path.join(SHOT, "home-v32-section-ink.png"))

    tab(page, 2, 700)

    def card_ink(bg):
        page.evaluate("""(bg) => {
          const S = window.TwoLogUI.state;
          Object.keys(S.groups || {}).forEach(k => (S.groups[k] || []).forEach(g => { g.titleBg = bg; }));
          window.TwoLogUI.rerender();
        }""", bg)
        page.wait_for_timeout(400)
        return page.evaluate("""() => {
          const t = document.querySelector('#s-diary .ncard .nc-hd .nc-t');
          return t ? getComputedStyle(t).color : null;
        }""")

    card_light = card_ink(LIGHT[1])
    check("노트 카드 제목: 밝은 바탕이면 검정(inkOn 그대로)", card_light == INK, card_light)
    card_dark = card_ink(DARK[1])
    # v38: 띠 색과 상관없이 늘 검정 글씨
    check("노트 카드 제목: 어두운 바탕이어도 검정", card_dark == INK, card_dark)
    # 원래대로 되돌립니다 (다른 화면 확인에 영향 없게)
    page.evaluate("""() => {
      const S = window.TwoLogUI.state;
      S.theme.homeTitleBg = null;
      Object.keys(S.groups || {}).forEach(k => (S.groups[k] || []).forEach(g => { g.titleBg = null; }));
      window.TwoLogUI.rerender();
    }""")
    page.wait_for_timeout(300)

    # ==================================================================
    # 4. 다크 모드에서도 막대 글씨 흰색
    # ==================================================================
    page.evaluate("document.documentElement.setAttribute('data-mode', 'dark'); 0")
    tab(page, 1, 700)
    page.evaluate("""(m) => {
      const S = window.TwoLogUI.state;
      S.ui.calMonth = m; S.ui.selDate = m + '-02';
      window.TwoLogUI.rerender();
    }""", MONTH)
    page.wait_for_timeout(500)
    dark_bars = bars(page)
    check("다크 모드에서도 모든 막대 글씨 rgb(255, 255, 255)",
          len(dark_bars) >= 8 and all(b["color"] == WHITE for b in dark_bars),
          [(b["t"], b["color"]) for b in dark_bars[:5]])
    page.screenshot(path=os.path.join(SHOT, "cal-v32-dark-bars.png"))
    page.evaluate("document.documentElement.removeAttribute('data-mode'); 0")
    page.wait_for_timeout(300)

    # ==================================================================
    # 5. 다른 화면 그대로 · 버전 표시 · 오류 없음
    # ==================================================================
    for idx, name, sid in ((0, "홈", "s-home"), (2, "노트", "s-diary"), (3, "사진첩", "s-photo"), (4, "My", "s-set")):
        tab(page, idx, 550)
        ok = page.evaluate("(id) => { const el = document.getElementById(id);"
                           " return !!el && el.classList.contains('active') && el.innerText.trim().length > 0; }", sid)
        check("%s 화면이 정상으로 뜸" % name, bool(ok), sid)
    ver = page.inner_text("#s-set .app-ver")
    check("My 맨 위 버전 표시가 v45", "v46" in ver, ver)
    page.screenshot(path=os.path.join(SHOT, "my-v32.png"))
    check("콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    browser.close()

print()
if fails:
    print("FAILED %d: %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS")
