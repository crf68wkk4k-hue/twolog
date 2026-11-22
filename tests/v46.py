"""투로그 v46 확인 — 모눈 다이어리 도구 줄 순서(↶ ↷ 왼쪽 · 펜/T/사진 오른쪽)와
«색상 스펙트럼 판»(아이폰 색상 › 스펙트럼 모양), 글씨 크기 숫자 크게.

1) 버전: sw.js 캐시 twolog-v48 · APP_VERSION v48 · My 탭 「버전 v48」
2) 도구 줄 순서 — ↶ 되돌리기 · ↷ 다시 실행이 «맨 왼쪽», 펜 · T · 사진이 «오른쪽»
   (x 좌표 undo < redo < pen < text < photo, 두 묶음 사이는 넓게 벌어짐)
3) 펜 도크의 색 동그라미는 22px 로 작게 · 누르면 스펙트럼 판이 올라옴
   · «색상» 제목 · × 닫기 · 캔버스 스펙트럼 · 색 견본/코드(#…) · 프리셋 9색
4) 스펙트럼 캔버스 — 왼쪽은 하얗고 오른쪽은 진한 색, 위는 밝고 아래는 어두움
5) 판을 톡 누르면 그 자리 색(#HEX)이 나오고 펜 색 동그라미에 바로 칠해짐
   끌면 지나는 자리마다 색이 따라 바뀌고, 손을 떼면 펜 색으로 저장
6) 그 색으로 그린 선의 색(c)이 고른 색과 같음 · 프리셋 색 점을 누르면 칠해지고 판이 닫힘
7) 글씨 도구의 색 동그라미도 같은 스펙트럼 판 — 고른 색이 고른 글 상자에 바로 칠해지고
   저장(texts[].color)까지 따라감 · × 로 닫힘
8) 글씨 크기 숫자가 «검정·굵게·17px» 로 커짐
9) 콘솔/페이지 오류 0건

    python3 tests/v46.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

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


def tab(page, idx, wait=560):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def hex_rgb(h):
    h = h.lstrip("#")
    return "rgb(%d, %d, %d)" % (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


SEED_JS = """() => {
  const st = JSON.parse(JSON.stringify(window.__app.state));
  st.couple.me = '소영'; st.couple.you = '준영';
  st.lists = (st.lists || []).concat([{ id: 'Ld46', title: '그림판', emoji: '', kind: 'memo', items: [] }]);
  st.groups = st.groups || {}; st.groups['list:Ld46'] = [];
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Ld46').concat(['list:Ld46']);
  return JSON.stringify(st);
}"""

TOOLS = """() => {
  const q = s => document.querySelector('#sheet ' + s);
  const r = e => e ? e.getBoundingClientRect() : null;
  const u = q('#d41UndoBtn'), rd = q('#d41RedoBtn');
  const p = q('.d41-tool[aria-label="펜 그리기"]'), t = q('.d41-tool[aria-label="글씨"]');
  const im = q('.d41-tool[aria-label="사진 넣기"]');
  const bar = q('.d41-tools');
  const br = r(bar);
  return {
    order: [...bar.children].map(e => e.id || e.getAttribute('aria-label') || e.className),
    xs: [u, rd, p, t, im].map(e => Math.round(r(e).left)),
    rights: [u, rd, p, t, im].map(e => Math.round(r(e).right)),
    barLeft: Math.round(br.left), barRight: Math.round(br.right),
    undoGapLeft: Math.round(r(u).left - br.left),
    photoGapRight: Math.round(br.right - r(im).right),
    groupGap: Math.round(r(p).left - r(rd).right),
    barW: Math.round(br.width),
    sameRow: (() => { const c = [u, rd, p, t, im].map(e => Math.round(r(e).top + r(e).height / 2));
      return Math.max.apply(null, c) - Math.min.apply(null, c) <= 2; })()
  };
}"""

DOCK = """() => {
  const q = s => document.querySelector('#sheet ' + s);
  const dkk = q('.d41-dkk');
  const b = dkk ? dkk.getBoundingClientRect() : null;
  return {
    labels: [...document.querySelectorAll('#sheet .d41-dk')].map(x => x.getAttribute('aria-label')),
    swatchW: b ? Math.round(b.width) : 0, swatchH: b ? Math.round(b.height) : 0,
    swatch: dkk ? dkk.style.background : '',
    dots: document.querySelectorAll('#sheet .d41-dot').length,
    on: q('.d41-dk-color.on') ? 1 : 0
  };
}"""

SP = """() => {
  const el = document.getElementById('d41Sp');
  const cv = document.getElementById('d41SpCv');
  const shown = !!(el && !el.hidden && el.offsetHeight > 0);
  const b = cv ? cv.getBoundingClientRect() : null;
  const pv = document.getElementById('d41SpPv');
  const hx = document.getElementById('d41SpHex');
  const dot = document.getElementById('d41SpDot');
  return {
    shown: shown, hasCv: !!cv,
    px: cv ? [cv.width, cv.height] : [0, 0],
    css: b ? [Math.round(b.width), Math.round(b.height)] : [0, 0],
    inView: b ? (b.top >= 0 && b.bottom <= window.innerHeight + 1) : false,
    title: (document.querySelector('#sheet .d41-sp-tt') || {}).textContent || '',
    preset: document.querySelectorAll('#sheet .d41-sp-dotb').length,
    presetColors: [...document.querySelectorAll('#sheet .d41-sp-dotb')].map(d => d.getAttribute('data-color')),
    closeX: !!document.querySelector('#sheet .d41-sp-x'),
    hex: hx ? hx.textContent : '',
    swatch: pv ? pv.style.background : '',
    ring: dot ? [dot.style.left, dot.style.top] : []
  };
}"""

GRAD = """() => {
  const cv = document.getElementById('d41SpCv');
  const c = cv.getContext('2d');
  const px = (fx, fy) => { const d = c.getImageData(Math.round(fx * (cv.width - 1)), Math.round(fy * (cv.height - 1)), 1, 1).data; return [d[0], d[1], d[2]]; };
  const lum = p => Math.round(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]);
  /* v47: 판 방향 — 왼쪽 하양 · 가운데 순색 · 오른쪽 검정 (가로) · 세로는 색(hue) */
  return {
    left: lum(px(0.01, 0.1)), right: lum(px(0.97, 0.1)),
    white: px(0.01, 0.1), black: px(0.97, 0.1),
    top: px(0.5, 0.01), midG: px(0.5, 0.34), midB: px(0.5, 0.67), bottom: px(0.5, 0.99),
    pink: px(0.25, 0.01), vivid: px(0.5, 0.01)
  };
}"""

SP_TAP = """([fx, fy]) => {
  const cv = document.getElementById('d41SpCv');
  const b = cv.getBoundingClientRect();
  const mk = (type, x, y) => new PointerEvent(type, {pointerId: 771, pointerType: 'touch', isPrimary: true,
    clientX: b.left + x * b.width, clientY: b.top + y * b.height, bubbles: true, cancelable: true});
  cv.dispatchEvent(mk('pointerdown', fx, fy));
  cv.dispatchEvent(mk('pointermove', fx, fy));
  cv.dispatchEvent(mk('pointerup', fx, fy));
  return (document.getElementById('d41SpHex') || {}).textContent || '';
}"""

SP_DRAG = """([pts]) => {
  const cv = document.getElementById('d41SpCv');
  const b = cv.getBoundingClientRect();
  const hex = () => (document.getElementById('d41SpHex') || {}).textContent || '';
  const mk = (type, p) => new PointerEvent(type, {pointerId: 772, pointerType: 'touch', isPrimary: true,
    clientX: b.left + p[0] * b.width, clientY: b.top + p[1] * b.height, bubbles: true, cancelable: true});
  const out = [hex()];
  cv.dispatchEvent(mk('pointerdown', pts[0]));
  for (let i = 1; i < pts.length; i++) { cv.dispatchEvent(mk('pointermove', pts[i])); out.push(hex()); }
  cv.dispatchEvent(mk('pointerup', pts[pts.length - 1]));
  const dot = document.getElementById('d41SpDot');
  return {hexes: out, ring: [dot.style.left, dot.style.top]};
}"""

DRAW = """([pts]) => {
  const svgEl = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const W = r.width;
  const mk = (type, p) => new PointerEvent(type, {pointerId: 901, pointerType: 'touch',
    clientX: r.left + p[0] * W, clientY: r.top + p[1] * W, bubbles: true, cancelable: true});
  svgEl.dispatchEvent(mk('pointerdown', pts[0]));
  for (let i = 1; i < pts.length; i++) svgEl.dispatchEvent(mk('pointermove', pts[i]));
  svgEl.dispatchEvent(mk('pointerup', pts[pts.length - 1]));
  return JSON.parse(document.getElementById('d41PenIn').value);
}"""

ROW = """() => {
  const p = document.getElementById('d41Panel');
  const pv = p.querySelector('.d41-trow .d41-pv');
  const cs = pv ? getComputedStyle(pv) : null;
  const tc = p.querySelector('.d41-tc');
  const r = tc ? tc.getBoundingClientRect() : null;
  return {
    text: pv ? pv.textContent.trim() : '',
    fs: cs ? cs.fontSize : '', fw: cs ? cs.fontWeight : '', color: cs ? cs.color : '',
    colorW: r ? Math.round(r.width) : 0,
    tcBg: tc ? tc.style.background : '',
    dots: p.querySelectorAll('.d41-dot').length
  };
}"""

HASHEX = re.compile(r"^#[0-9A-F]{6}$")

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
    check('sw.js 캐시 버전 twolog-v48', 'const VERSION = "twolog-v48"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v48", 'var APP_VERSION = "v48"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v46 문자열이 남아 있지 않음",
          "twolog-v46" not in sw and 'APP_VERSION = "v46"' not in app_js)

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed = page.evaluate(SEED_JS)
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 4, 620)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v48」", ver.strip() == "버전 v48", ver)

    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="그림판").first.click()
    page.wait_for_timeout(560)
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(900)

    # ==================================================================
    # 2. 도구 줄 순서 — ↶ ↷ 왼쪽, 펜·T·사진 오른쪽
    # ==================================================================
    tl = page.evaluate(TOOLS)
    check("도구 줄 차례 — ↶ · ↷ · (벌림) · 펜 · T · 사진",
          tl["order"] == ["d41UndoBtn", "d41RedoBtn", "d41-tools-gap", "펜 그리기", "글씨", "사진 넣기"], tl["order"])
    xs = tl["xs"]
    check("x 좌표 undo < redo < pen < T < 사진",
          xs == sorted(xs) and len(set(xs)) == 5, xs)
    check("↶ ↷ 가 도구 줄 맨 왼쪽 (왼쪽 여백 20px 안)",
          tl["undoGapLeft"] <= 20, (tl["undoGapLeft"], tl["barLeft"]))
    check("펜·T·사진이 오른쪽 끝 (오른쪽 여백 20px 안)",
          tl["photoGapRight"] <= 20, (tl["photoGapRight"], tl["barRight"]))
    check("두 묶음이 한 줄에 있고 사이는 넓게 벌어짐 (>= 100px)",
          tl["sameRow"] and tl["groupGap"] >= 100, (tl["sameRow"], tl["groupGap"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v46-tools.png"))

    # ==================================================================
    # 3. 펜 색 동그라미 → 스펙트럼 판
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(380)
    dk = page.evaluate(DOCK)
    check("도크는 그대로 — 가는 펜 · 일반 펜 · 형광펜 · 지우개 · 펜 색 · 전체 지우기",
          dk["labels"] == ["가는 펜", "일반 펜", "형광펜", "지우개", "펜 색", "전체 지우기"], dk["labels"])
    check("색 동그라미는 22px 로 작게 (글씨 도구와 같은 크기)",
          dk["swatchW"] == 22 and dk["swatchH"] == 22, (dk["swatchW"], dk["swatchH"]))
    check("색 동그라미를 누르기 전에는 색 점 줄이 없음", dk["dots"] == 0, dk["dots"])

    page.locator("#sheet .d41-dk[aria-label='펜 색']").click()
    page.wait_for_timeout(420)
    sp = page.evaluate(SP)
    check("펜 색 동그라미를 누르면 스펙트럼 판이 올라옴",
          sp["shown"] and sp["hasCv"] and sp["css"][0] > 240 and sp["css"][1] >= 120, sp)
    check("판 — «색상» 제목 · × 닫기 · 프리셋 색 9개",
          sp["title"] == "색상" and sp["closeX"] and sp["preset"] == 9
          and len(set(sp["presetColors"])) == 9, (sp["title"], sp["preset"]))
    check("캔버스가 화면 안에 · 해상도는 CSS 크기의 2배(레티나)",
          sp["inView"] and sp["px"][0] >= sp["css"][0] * 1.9, (sp["px"], sp["css"]))
    check("지금 펜 색(#111111)이 견본·코드로 보이고 동그라미도 판 위에 놓임",
          sp["hex"] == "#111111" and sp["swatch"] in ("rgb(17, 17, 17)", "#111111")
          and len(sp["ring"]) == 2 and sp["ring"][0].endswith("%"), sp)
    gr = page.evaluate(GRAD)
    check("스펙트럼 — 왼쪽은 하얗고 오른쪽은 검정 (가로 = 하양→순색→검정)",
          gr["left"] >= 240 and gr["right"] <= 30, (gr["left"], gr["right"]))
    check("스펙트럼 — 세로가 색(hue): 위 빨강 · 가운데 초록 · 그 아래 파랑",
          gr["top"][0] >= 240 and gr["top"][1] < 30 and gr["top"][2] < 30
          and gr["midG"][1] >= 240 and gr["midG"][0] < 30
          and gr["midB"][2] >= 240 and gr["midB"][0] < 30, (gr["top"], gr["midG"], gr["midB"]))
    check("스펙트럼 — 아래는 다시 빨강 · 왼쪽 1/4 은 흰색과 순색 사이",
          gr["bottom"][0] >= 240 and gr["bottom"][2] < 40
          and 90 <= gr["pink"][1] <= 200 and gr["pink"][0] >= 240, (gr["bottom"], gr["pink"]))

    # ==================================================================
    # 4. 판을 톡 누르면 그 자리 색 · 끌면 따라 바뀜
    # ==================================================================
    hex1 = page.evaluate(SP_TAP, [0.86, 0.18])
    page.wait_for_timeout(320)
    one = page.evaluate(SP)
    dk1 = page.evaluate(DOCK)
    check("판을 톡 누르면 그 자리 색(#HEX)이 나옴", bool(HASHEX.match(hex1)), hex1)
    check("누른 색이 펜 색 동그라미에 바로 칠해짐",
          dk1["swatch"] == hex_rgb(hex1), (dk1["swatch"], hex1))
    check("견본·코드도 그 색으로 바뀜", one["hex"] == hex1 and one["swatch"] == hex_rgb(hex1), one["hex"])

    hex_left = page.evaluate(SP_TAP, [0.08, 0.10])
    page.wait_for_timeout(240)
    lum_left = (0.299 * int(hex_left[1:3], 16) + 0.587 * int(hex_left[3:5], 16)
                + 0.114 * int(hex_left[5:7], 16)) if HASHEX.match(hex_left) else -1
    check("왼쪽 가장자리를 누르면 하얀 쪽 색 (밝기 200 이상)",
          HASHEX.match(hex_left) and lum_left >= 200 and hex_left != hex1, (hex_left, round(lum_left)))

    drag = page.evaluate(SP_DRAG, [[[0.15, 0.2], [0.35, 0.35], [0.55, 0.6], [0.8, 0.3]]])
    page.wait_for_timeout(360)
    hx = drag["hexes"]
    check("끌면 지나는 자리마다 색이 따라 바뀜 (4가지 모두 다름)",
          len(set(hx)) == 4 and all(HASHEX.match(x) for x in hx), hx)
    check("끌고 난 자리에 동그라미가 옮겨 감 (80% · 30% 근처)",
          drag["ring"][0].startswith("80") and drag["ring"][1].startswith("30"), drag["ring"])

    pen_hex = hx[-1].upper()
    dk2 = page.evaluate(DOCK)
    check("손을 떼면 고른 색이 펜 색으로 저장됨", dk2["swatch"] == hex_rgb(pen_hex),
          (dk2["swatch"], pen_hex))

    # ==================================================================
    # 5. 그 색으로 그린 선 · × 로 닫기 · 프리셋
    # ==================================================================
    page.locator("#sheet .d41-sp-x").click()
    page.wait_for_timeout(360)
    off = page.evaluate(SP)
    check("× 를 누르면 판이 닫힘", off["shown"] is False, off)
    strokes = page.evaluate(DRAW, [[[0.2, 0.55], [0.45, 0.6], [0.7, 0.58]]])
    page.wait_for_timeout(340)
    drawn = strokes[-1] if strokes else {}
    check("그 색으로 그린 선의 색(c)이 고른 색과 같음",
          bool(drawn) and str(drawn.get("c", "")).upper() == pen_hex, (drawn.get("c"), pen_hex))

    page.locator("#sheet .d41-dk[aria-label='펜 색']").click()
    page.wait_for_timeout(380)
    page.locator("#sheet .d41-sp-dotb").nth(1).click()
    page.wait_for_timeout(360)
    pre = page.evaluate("""() => ({
      shown: !document.getElementById('d41Sp').hidden,
      swatch: (document.querySelector('#sheet .d41-dkk') || {}).style.background || ''})""")
    check("프리셋 색 점을 누르면 칠해지고 판이 닫힘 (v47 날씨의 요정 팔레트)",
          pre["shown"] is False and pre["swatch"] == "rgb(244, 107, 98)", pre)

    # ==================================================================
    # 6. 글씨 도구 — 스펙트럼 · 글씨 크기 숫자
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(420)
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(500)
    wrote = page.evaluate("""() => {
      const ed = document.querySelector('#d41Nodes .d41-txt');
      if (!ed) return false;
      ed.innerText = '색 확인';
      ed.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    }""")
    page.wait_for_timeout(260)
    check("글씨 도구로 새 글 상자가 생김", wrote is True)
    row = page.evaluate(ROW)
    check("글씨 크기 숫자가 검정·굵게·17px 로 커짐",
          row["fs"] == "17px" and row["fw"] in ("800", "bold") and row["color"] == "rgb(9, 9, 11)", row)
    check("글씨 색 동그라미는 22px · 판은 접혀 있음", row["colorW"] == 22 and row["dots"] == 0, row)
    page.locator("#sheet .d41-tc[data-act=d41ColorPick]").click()
    page.wait_for_timeout(420)
    spt = page.evaluate(SP)
    check("글씨 색 동그라미도 같은 스펙트럼 판을 엶",
          spt["shown"] and spt["title"] == "색상" and spt["preset"] == 9, spt)
    page.screenshot(path=os.path.join(SHOT, "diary-v46-spectrum.png"))

    hex_t = page.evaluate(SP_TAP, [0.62, 0.12])
    page.wait_for_timeout(320)
    page.locator("#sheet .d41-sp-x").click()
    page.wait_for_timeout(420)
    done = page.evaluate("""() => ({
      shown: !document.getElementById('d41Sp').hidden,
      tc: (document.querySelector('#sheet .d41-tc') || {}).style.background || '',
      txColor: (() => { const t = document.querySelector('#d41Nodes .d41-tx'); return t ? getComputedStyle(t).color : ''; })(),
      saved: (() => { try { return JSON.parse(document.getElementById('d41TextsIn').value); } catch (e) { return []; } })(),
      textW: (() => { const t = document.querySelector('#d41Nodes .d41-tx'); return t ? t.getBoundingClientRect().width : 0; })()
    })""")
    saved_colors = [str(t.get("color", "")).upper() for t in done["saved"]]
    check("고른 색이 고른 글 상자에 바로 칠해짐",
          done["txColor"] == hex_rgb(hex_t), (done["txColor"], hex_t))
    check("쓴 글도 그대로 저장됨 (빈 상자로 남지 않음)",
          any(t.get("text") == "색 확인" for t in done["saved"]),
          [t.get("text") for t in done["saved"]])
    check("그 색이 저장(texts[].color)까지 따라감",
          hex_t in saved_colors, (saved_colors, hex_t))
    check("색 동그라미도 그 색으로 · × 로 판이 닫힘",
          done["shown"] is False and done["tc"] == hex_rgb(hex_t), done)

    check("브라우저 콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 마무리
    # ==================================================================
    print("")
    if fails:
        print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
        sys.exit(1)
    print("ALL PASS — v46")
