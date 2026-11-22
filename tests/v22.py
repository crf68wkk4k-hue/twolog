"""투로그 v22 확인 — 검색창 위쪽 고정 · 컬러판 동그라미 한 줄 · 카드 제목 · My 버전.

1) 일정 검색 모달이 «화면 위쪽»에 고정 — 아이폰 키보드가 아래를 덮어도 검색칸·결과가 보임.
   (작은 화면 390x420, 키보드가 올라온 것처럼 390x470 에서도 모달이 화면 안에 들어오는지)
2) 일정 추가 · 테마/컬러 · 노트 카드 제목 색 — 12색 컬러판이 «작은 동그라미 한 줄».
3) 노트 카드 제목은 작고(13.5px) 한 줄(…), 옆 숫자·꺾쇠와 아래 +N개 표기는 없음.
4) 캘린더 한글은 My 에서 고른 앱 폰트를 그대로, 숫자만 닉스곤체.
5) My 탭 맨 윗줄 오른쪽에 「버전 v22」.

    python3 tests/v22.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, json, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
errors = []

with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                              has_touch=True, device_scale_factor=2)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")  # v25: 이 테스트는 로컬 모드 고정
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # ---------------- 0. 서비스워커 캐시 버전 ----------------
    sw = page.request.get(URL + "sw.js").text()
    # v24: 캐시 버전은 배포마다 올라가므로 v24 으로
    check("sw.js 캐시 버전 twolog-v47", 'const VERSION = "twolog-v47"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:2])
    app_js = page.request.get(URL + "app.js").text()
    check("app.js 버전 상수 v44", 'var APP_VERSION = "v47"' in app_js)

    # 예시 데이터로 한 번 열어 상태를 만들고, 저장되는 일반 모드로 옮겨요
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)

    # ==================================================================
    # 1. 노트 카드 — 제목 작게·한 줄, 숫자/꺾쇠/+N개 없음
    # ==================================================================
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(650)
    card = page.evaluate("""(() => {
      const cs = Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)'));
      const c = cs[0];
      const t = c.querySelector('.nc-t');
      const ts = getComputedStyle(t);
      const tr = t.getBoundingClientRect(), hr = c.querySelector('.nc-hd').getBoundingClientRect();
      return {n: cs.length,
              fs: ts.fontSize, fw: ts.fontWeight, ws: ts.whiteSpace, ov: ts.overflow, to: ts.textOverflow,
              lines: Math.round(tr.height / parseFloat(ts.lineHeight)),
              hFitsHd: tr.height <= hr.height + 0.6,
              meta: c.querySelectorAll('.nc-meta').length,
              num: c.querySelectorAll('.nc-n').length,
              go: c.querySelectorAll('.nc-go').length,
              more: c.querySelectorAll('.cmore').length,
              txt: c.innerText.replace(/\\n/g, ' | ').trim()};
    })()""")
    check("노트 카드 있음", card["n"] >= 1, card["n"])
    check("카드 제목 13.5px로 작아짐", card["fs"] == "13.5px", card["fs"])
    check("카드 제목은 한 줄 고정(nowrap·…)",
          card["ws"] == "nowrap" and card["ov"] == "hidden" and card["to"] == "ellipsis",
          (card["ws"], card["ov"], card["to"]))
    check("제목이 띠 안에서 한 줄", card["lines"] == 1 and card["hFitsHd"], (card["lines"], card["hFitsHd"]))
    check("제목 옆 숫자·꺾쇠 삭제", card["meta"] == 0 and card["num"] == 0 and card["go"] == 0,
          (card["meta"], card["num"], card["go"]))
    check("카드 아래 +N개 표기 삭제", card["more"] == 0, card["more"])
    ct = page.evaluate("""(() => {
      const c = document.querySelector('#s-diary .ngrid .ncard:not(.new)');
      const t = c.querySelector('.nc-t').innerText;
      const body = c.innerText.split('\\n').slice(1).join(' ');
      return {title: t.trim(), hasPlus: /\\+\\s*\\d+\\s*개/.test(c.innerText),
              moreTxt: (c.querySelector('.nc-more') || {}).textContent || '',
              moreOn: !!(c.querySelector('.nc-more')),
              numbers: (c.innerText.match(/(^|\\s)\\d+(개)?(\\s|$)/g) || []).join(',')};
    })()""")
    check("카드에 개수 숫자 없음 · 넘칠 때만 「+N개 더」 (v42)",
          ct["numbers"] == "" and (not ct["hasPlus"] or
                                   (ct["moreOn"] and re.search(r"^\+\d+개 더$", ct["moreTxt"].strip()) is not None)), ct)

    # 긴 제목 카드를 하나 더 만들어 «한 줄 + …» 인지 확인 (사용자 예: 이달의장보기·나중에살것)
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(450)
    page.fill('#sheet #sheetForm input[name="title"]', "이달의 장보기 목록 정리하고 나중에 살 것도 적어 두기")
    page.locator('#sheet button[type="submit"]').click()
    page.wait_for_timeout(600)
    long_t = page.evaluate("""(() => {
      const cs = Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)'));
      const c = cs.filter(x => x.innerText.indexOf('이달의 장보기') >= 0)[0];
      if (!c) return {ok: false, n: cs.length};
      const t = c.querySelector('.nc-t');
      const cs2 = getComputedStyle(t);
      const hr = c.querySelector('.nc-hd').getBoundingClientRect(), tr = t.getBoundingClientRect();
      return {ok: true, n: cs.length, txt: t.innerText, cut: t.scrollWidth > t.clientWidth + 1,
              lines: Math.round(tr.height / parseFloat(cs2.lineHeight)),
              oneRow: tr.height <= hr.height && hr.height < 40, fs: cs2.fontSize};
    })()""")
    check("긴 제목도 한 줄로 잘림(…)", long_t.get("ok") and long_t.get("cut")
          and long_t.get("lines") == 1, long_t)
    check("카드 두 개가 나란히", long_t.get("n", 0) >= 2, long_t.get("n"))
    page.wait_for_timeout(1800)   # 안내(toast)가 사라진 뒤
    page.screenshot(path=os.path.join(SHOT, "note-v22.png"))

    # 카드 상세 시트 — 제목 색 컬러판도 작은 동그라미 한 줄
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-t").tap()
    page.wait_for_timeout(550)
    cpal = page.evaluate("""(() => {
      const g = document.querySelector('#sheet .sw-grid[data-sw="cardTitleBg"]');
      if (!g) return {ok: false};
      const els = Array.from(g.querySelectorAll('.sw'));
      const rs = els.map(e => e.getBoundingClientRect());
      const cs = getComputedStyle(g);
      const scs = els[0] ? getComputedStyle(els[0]) : null;
      const foot = document.querySelector('#sheet .cp-reset[data-act="pickCardColor"]');
      return {ok: true, n: els.length, display: cs.display, wrap: cs.flexWrap,
              rows: new Set(rs.map(r => Math.round(r.top))).size,
              w: Math.round(rs[0].width), h: Math.round(rs[0].height),
              radius: scs.borderTopLeftRadius,
              inSheet: (() => { const s = document.querySelector('#sheet').getBoundingClientRect();
                return rs.every(r => r.left >= s.left - 1 && r.right <= s.right + 1); })(),
              resetInHd: foot ? !!foot.closest('.cp-hd') : null,
              hdAbove: (() => { const hd = document.querySelector('#sheet .cp-hd').getBoundingClientRect();
                return hd.bottom <= rs[0].top + 1; })()};
    })()""")
    check("카드 시트 제목 색 컬러판 12색", cpal.get("ok") and cpal.get("n") == 12, cpal)
    check("카드 시트 컬러판은 한 줄(줄바꿈 없음)",
          cpal.get("display") == "flex" and cpal.get("wrap") == "nowrap" and cpal.get("rows") == 1, cpal)
    check("카드 시트 컬러판 작은 동그라미(20px·둥글게)",
          cpal.get("w") == 20 and cpal.get("h") == 20 and "999px" in str(cpal.get("radius"))
          or "50%" in str(cpal.get("radius")), cpal)
    check("카드 시트 컬러판이 시트 안에 들어옴", bool(cpal.get("inSheet")), cpal.get("inSheet"))
    check("「기본」은 제목 색 줄 오른쪽 · 팔레트는 그 아래", bool(cpal.get("resetInHd")) and bool(cpal.get("hdAbove")), cpal)
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(SHOT, "note-detail-v22.png"))

    # 색 고르기 — 고른 색이 카드 띠에 칠해지고 시트는 열린 채
    page.locator('#sheet .sw-grid[data-sw="cardTitleBg"] .sw[data-color="#EFD353"]').click()
    page.wait_for_timeout(500)
    pick = page.evaluate("""(() => {
      const c = document.querySelector('#s-diary .ngrid .ncard:not(.new)');
      const hd = c.querySelector('.nc-hd');
      return {bg: getComputedStyle(hd).backgroundColor,
              sel: document.querySelectorAll('#sheet .sw-grid[data-sw="cardTitleBg"] .sw.sel').length,
              open: document.getElementById('sheetWrap').classList.contains('open')};
    })()""")
    check("고른 색이 카드 띠에 반영", pick["bg"] == "rgb(239, 211, 83)" and pick["sel"] == 1 and pick["open"], pick)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # ==================================================================
    # 2. 캘린더 — 검색 모달이 위쪽, 일정 시트 컬러 한 줄
    # ==================================================================
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(650)
    today_str = time.strftime("%Y-%m-%d")
    if page.locator("#s-cal .day[data-date='%s']" % today_str).count():
        page.locator("#s-cal .day[data-date='%s']" % today_str).click()
        page.wait_for_timeout(450)

    page.locator('#s-cal [data-act="calSearch"]').click()
    page.wait_for_timeout(500)
    pos = page.evaluate("""(() => {
      const sh = document.querySelector('#sheet'); const r = sh.getBoundingClientRect();
      const w = document.getElementById('sheetWrap');
      const cs = getComputedStyle(w);
      const inp = document.querySelector('#calSearchIn');
      const ir = inp.getBoundingClientRect();
      return {top: r.top, bottom: r.bottom, h: r.height, vh: window.innerHeight,
              align: cs.alignItems, padTop: cs.paddingTop, cls: w.className,
              inInput: ir.top >= r.top && ir.bottom <= r.bottom,
              inView: r.top >= 0 && r.bottom <= window.innerHeight};
    })()""")
    check("검색 모달은 위쪽에 붙음(flex-start · padding-top)",
          pos["align"] in ("flex-start", "start", "flow-start") and pos["padTop"].startswith("64") and "sheet-center" in pos["cls"], pos)
    check("검색 모달이 화면 위쪽(top≈64)", 55 <= pos["top"] <= 90, pos["top"])
    check("검색 모달이 화면 안에 들어옴", pos["inView"] and pos["inInput"], pos)
    check("검색 모달이 하단 절반을 비워 둠(키보드 자리)", pos["bottom"] <= pos["vh"] * 0.62,
          (pos["bottom"], pos["vh"]))
    page.fill("#calSearchIn", "성")
    page.wait_for_timeout(500)
    red = page.evaluate("""(() => {
      const sh = document.querySelector('#sheet'); const r = sh.getBoundingClientRect();
      const rows = Array.from(document.querySelectorAll('#sheet .sres'));
      return {n: rows.length, top: r.top, bottom: r.bottom,
              first: rows[0] ? rows[0].getBoundingClientRect().top : null,
              vh: window.innerHeight};
    })()""")
    check("검색 결과가 모달 안 위쪽에 보임", red["n"] >= 1 and red["top"] <= 90
          and red["first"] < red["vh"] * 0.6, red)
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "calendar-search-v22.png"))

    # 아이폰 키보드가 올라온 것처럼 «보이는 화면»만 줄여도 모달이 따라 줄어드는지
    page.set_viewport_size({"width": 390, "height": 470})
    page.wait_for_timeout(700)
    kb = page.evaluate("""(() => {
      const sh = document.querySelector('#sheet'); const r = sh.getBoundingClientRect();
      const inp = document.querySelector('#calSearchIn').getBoundingClientRect();
      return {top: r.top, bottom: r.bottom, maxH: sh.style.maxHeight, vh: window.innerHeight,
              inpIn: inp.top >= r.top && inp.bottom <= r.bottom};
    })()""")
    check("키보드가 올라와도 검색 모달이 화면 안", kb["bottom"] <= kb["vh"] - 6 and kb["top"] >= 40, kb)
    check("키보드 높이에 맞춰 모달 최대 높이 조정", kb["maxH"] != "", kb["maxH"])
    check("검색칸은 키보드 위에 그대로", kb["inpIn"], kb)
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(SHOT, "calendar-search-v22-keyboard.png"))

    # 아주 작은 화면(390x420)
    page.set_viewport_size({"width": 390, "height": 420})
    page.wait_for_timeout(600)
    small = page.evaluate("""(() => {
      const r = document.querySelector('#sheet').getBoundingClientRect();
      return {top: r.top, bottom: r.bottom, vh: window.innerHeight, h: r.height,
              fits: r.top >= 0 && r.bottom <= window.innerHeight};
    })()""")
    check("390x420 화면에서도 검색 모달이 잘리지 않음", small["fits"] and small["h"] > 100, small)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(500)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(450)

    # ---------------- 일정 추가 시트 컬러판 ----------------
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(550)
    ev = page.evaluate("""(() => {
      const g = document.querySelector('#sheet [data-sw="evColor"]');
      const els = Array.from(g.querySelectorAll('.sw'));
      const rs = els.map(e => e.getBoundingClientRect());
      const cs = getComputedStyle(g), scs = getComputedStyle(els[0]);
      const ti = document.querySelector('#sheetForm input[name="title"]').getBoundingClientRect();
      const reset = document.querySelector('#sheet .cp-reset[data-act="pickEvColor"]');
      const top = Array.from(document.querySelectorAll('#sheet .sheet-hd, #sheet #sheetForm .f, #sheet #sheetForm .cp'))
        .map(e => [e.className, Math.round(e.getBoundingClientRect().top)]);
      return {n: els.length, display: cs.display, wrap: cs.flexWrap,
              rows: new Set(rs.map(r => Math.round(r.top))).size,
              w: Math.round(rs[0].width), h: Math.round(rs[0].height),
              radius: scs.borderTopLeftRadius,
              inSheet: (() => { const s = document.querySelector('#sheet').getBoundingClientRect();
                return rs.every(r => r.left >= s.left - 1 && r.right <= s.right + 1); })(),
              titleAbove: ti.bottom <= rs[0].top + 1,
              resetText: reset ? reset.textContent.trim() : null, top};
    })()""")
    check("일정 시트 컬러 12색", ev["n"] == 12, ev["n"])
    check("일정 시트 컬러 한 줄",
          ev["display"] == "flex" and ev["wrap"] == "nowrap" and ev["rows"] == 1, ev)
    check("일정 시트 컬러 작은 동그라미(20px)", ev["w"] == 20 and ev["h"] == 20
          and ("999px" in str(ev["radius"]) or "50%" in str(ev["radius"])), ev)
    check("일정 시트 컬러가 시트 밖으로 넘치지 않음", ev["inSheet"], ev["inSheet"])
    check("제목 다음에 컬러 한 줄", ev["titleAbove"] and ev["resetText"] == "기본", (ev["titleAbove"], ev["resetText"]))
    check("일정 시트 구조(제목 → 컬러 → 날짜 → 추가하기)",
          page.evaluate("""(() => {
            const sh = document.querySelector('#sheet');
            const t = sh.querySelector('.ev-title').getBoundingClientRect();
            const c = sh.querySelector('.ev-cp').getBoundingClientRect();
            const w = sh.querySelector('.ev-when').getBoundingClientRect();
            const who = sh.querySelector('.wsel').getBoundingClientRect();
            const add = sh.querySelector('#sheetForm .btn-primary').getBoundingClientRect();
            const bigs = Array.from(sh.querySelectorAll('.ev-dbig')).map(e => e.textContent.trim());
            const times = Array.from(sh.querySelectorAll('.ev-time-btn')).map(e => e.textContent.trim());
            return t.top < c.top && c.top < w.top && w.bottom <= who.top + 1 && who.top < add.top
              && bigs.length === 2 && times.length === 0;
          })()"""))
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "event-sheet-v22.png"))
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # ---------------- 테마/컬러 시트 컬러판 ----------------
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    page.locator('#s-set .menu-row[data-act="openThemeManager"]').click()
    page.wait_for_timeout(500)
    th = page.evaluate("""(() => {
      const g = document.querySelector('#sheet .sw-grid[data-sw="homeTitleBg"]');
      if (!g) return {ok: false};
      const els = Array.from(g.querySelectorAll('.sw'));
      const rs = els.map(e => e.getBoundingClientRect());
      const cs = getComputedStyle(g), scs = getComputedStyle(els[0]);
      const foot = document.querySelector('#sheet .cp-foot').getBoundingClientRect();
      return {ok: true, n: els.length, display: cs.display, wrap: cs.flexWrap,
              rows: new Set(rs.map(r => Math.round(r.top))).size,
              w: Math.round(rs[0].width), h: Math.round(rs[0].height),
              radius: scs.borderTopLeftRadius,
              inSheet: (() => { const s = document.querySelector('#sheet').getBoundingClientRect();
                return rs.every(r => r.left >= s.left - 1 && r.right <= s.right + 1); })(),
              footBelow: foot.top >= rs[0].bottom - 1,
              colors: els.map(e => e.getAttribute('data-color'))};
    })()""")
    check("테마 시트에 12색 컬러판", th.get("ok") and th.get("n") == 12, th)
    check("테마 시트 컬러판 한 줄",
          th.get("display") == "flex" and th.get("wrap") == "nowrap" and th.get("rows") == 1, th)
    check("테마 시트 컬러판 작은 동그라미(20px)",
          th.get("w") == 20 and th.get("h") == 20 and ("999px" in str(th.get("radius")) or "50%" in str(th.get("radius"))), th)
    check("테마 컬러판이 시트 안·컬러/기본 아래", th.get("inSheet") and th.get("footBelow"), th)
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "theme-manager-v22.png"))
    page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw[data-color="#D2CBE3"]').click()
    page.wait_for_timeout(450)
    check("테마에서 고른 색이 저장됨",
          page.evaluate("window.__app.state.theme.homeTitleBg") == "#D2CBE3",
          page.evaluate("window.__app.state.theme.homeTitleBg"))
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(300)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # 홈에서 여는 「컬러」 시트(formTheme)도 같은 모양인지
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(500)
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(500)
    ts = page.evaluate("""(() => {
      const g = document.querySelector('#sheet .sw-grid[data-sw="homeTitleBg"]');
      if (!g) return {ok: false};
      const els = Array.from(g.querySelectorAll('.sw'));
      const rs = els.map(e => e.getBoundingClientRect());
      const cs = getComputedStyle(g), scs = getComputedStyle(els[0]);
      return {ok: true, n: els.length, display: cs.display, wrap: cs.flexWrap,
              rows: new Set(rs.map(r => Math.round(r.top))).size,
              w: Math.round(rs[0].width), h: Math.round(rs[0].height), radius: scs.borderTopLeftRadius,
              title: document.querySelector('#sheet .sheet-hd h2').textContent.trim()};
    })()""")
    check("홈 「컬러」 시트도 12색 동그라미 한 줄",
          ts.get("ok") and ts.get("n") == 12 and ts.get("display") == "flex"
          and ts.get("rows") == 1 and ts.get("w") == 20, ts)
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "theme-sheet-v22.png"))
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # ==================================================================
    # 3. My 탭 맨 윗줄 버전
    # ==================================================================
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    my = page.evaluate("""(() => {
      const hd = document.querySelector('#s-set .hdr');
      const v = document.querySelector('#s-set .hdr .app-ver');
      const next = document.querySelector('#s-set .sec');
      if (!v) return {ok: false};
      const hr = hd.getBoundingClientRect(), vr = v.getBoundingClientRect(), nr = next.getBoundingClientRect();
      return {ok: true, txt: v.textContent.trim(), vTop: vr.top, hTop: hr.top, hBottom: hr.bottom,
              right: window.innerWidth - vr.right,
              aboveList: vr.bottom <= nr.top,
              topOfPage: hr.top < window.innerHeight * 0.2};
    })()""")
    check("My 탭에 버전 표시 있음", my.get("ok"), my)
    # v24: 화면에 찍히는 버전도 배포마다 올라가므로 v24
    check("버전 문구가 v47", "v47" in str(my.get("txt")), my.get("txt"))
    check("버전이 My 머리줄 맨 위에", my.get("vTop", 999) <= my.get("hTop", 0) + 40 and my.get("topOfPage"), my)
    check("버전이 오른쪽 끝", 12 <= my.get("right", 999) <= 26, my.get("right"))
    check("버전이 계정 목록보다 위", bool(my.get("aboveList")), my.get("aboveList"))
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "my-v22.png"))

    # ==================================================================
    # 4. 캘린더 한글 폰트 상속 / 숫자만 닉스곤체
    # ==================================================================
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(650)
    f = page.evaluate("""(async () => {
      await document.fonts.ready;
      const body = getComputedStyle(document.body).fontFamily;
      const pick = s => { const e = document.querySelector(s); return e ? getComputedStyle(e).fontFamily : null; };
      const d = document.querySelector('#s-cal .day .dnum');
      return {body, month: pick('#s-cal .cal-month'), week: pick('#s-cal .cal-week span'),
              panel: pick('#s-cal .daypanel-hd .d'), evt: pick('#s-cal .daylist .ev .t'),
              who: pick('#s-cal .daylist .ev .wname'), ebar: pick('#s-cal .ebar'),
              dnum: d ? getComputedStyle(d).fontFamily : null,
              loaded: document.fonts.check("600 15px 'Nixgon'")};
    })()""")
    check("캘린더 한글(달·요일·날짜줄·일정)이 앱 폰트 그대로",
          all(f[k] == f["body"] for k in ("month", "week", "panel", "evt", "who", "ebar"))
          and "Nixgon" not in f["month"], f)
    check("캘린더 숫자만 닉스곤체", f["dnum"].startswith("Nixgon") and f["loaded"], (f["dnum"], f["loaded"]))
    page.evaluate("document.documentElement.style.setProperty('--font', \"'Gowun Dodum', Pretendard, sans-serif\"); 0")
    page.wait_for_timeout(300)
    inh = page.evaluate("""(() => ({
      m: getComputedStyle(document.querySelector('#s-cal .cal-month')).fontFamily,
      p: getComputedStyle(document.querySelector('#s-cal .daypanel-hd .d')).fontFamily,
      d: getComputedStyle(document.querySelector('#s-cal .day .dnum')).fontFamily}))()""")
    check("My 폰트를 바꾸면 캘린더 한글도 따라감", "Gowun Dodum" in inh["m"] and "Gowun Dodum" in inh["p"], inh)
    check("숫자는 그대로 닉스곤체", inh["d"].startswith("Nixgon"), inh["d"])
    page.evaluate("document.documentElement.style.removeProperty('--font'); 0")
    page.wait_for_timeout(250)

    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
