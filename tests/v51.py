"""투로그 v51 확인 — 모눈 다이어리에서 글씨·사진 상자를 끌 때 손가락 자리에 붙어 움직이는지.

1) 버전: sw.js 캐시 twolog-v51 · APP_VERSION v51 · My 탭 「버전 v51」
2) 머리 높이(d41Top) 108px 확인 — 상자를 끄는 기준(자)이 종이(#d41Paper)가 아니라
   글·사진이 놓이는 칸(#d41Nodes)이어야 하는 이유(두 자가 108px 차이)
3) 글 상자를 끌 때 «끄는 도중»(pointermove 직후 · pointerup 전) 상자의 화면 자리가
   시작 자리 + 손가락이 움직인 거리(dx, dy)와 같음 (예전엔 위로 108px 떠서 따라왔어요)
   · 손을 떼도 튀지 않고 그 자리 그대로 · 저장된 좌표(y·x)도 화면 자리와 일치
   · 앱을 닫아도(저장) 그 자리 그대로
4) 사진 상자도 같은 자로 끌림 (도중 · 손 뗀 뒤 · 저장 좌표)
5) 위로 세게 끌어도 종이 위로 나가지 않고 맨 위(머리 높이)에서 멈춤 · 오른쪽으로 세게 끌어도 종이 안
6) 그린 그림(획)을 끌어 옮기는 것도 손가락 거리 그대로 (다른 이동 함수 점검)
7) 콘솔/페이지 오류 없음

    python3 tests/v51.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import base64 as _b64, functools, http.server, json, os, re, socketserver, sys, threading, time

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


SEED_JS = """() => {
  const st = JSON.parse(JSON.stringify(window.__app.state));
  st.couple.me = '소영'; st.couple.you = '준영';
  st.lists = (st.lists || []).concat([{ id: 'Ld51', title: '그림판', emoji: '', kind: 'memo', items: [] }]);
  st.groups = st.groups || {}; st.groups['list:Ld51'] = [];
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Ld51').concat(['list:Ld51']);
  return JSON.stringify(st);
}"""

# 상자·종이·머리 높이와 저장된 좌표
BOX = """() => {
  const nodes = document.getElementById('d41Nodes');
  const paper = document.getElementById('d41Paper');
  const nr = nodes.getBoundingClientRect(), pr = paper.getBoundingClientRect();
  const R = e => { const r = e.getBoundingClientRect();
    return {l: r.left, t: r.top, r: r.right, b: r.bottom, w: r.width, h: r.height}; };
  const txs = [...document.querySelectorAll('#sheet .d41-tx')].map(e => Object.assign(R(e),
    {id: e.getAttribute('data-tx'), txt: (e.innerText || '').trim(), tf: e.style.transform}));
  const imgs = [...document.querySelectorAll('#sheet .d41-imgb')].map(e => Object.assign(R(e),
    {id: e.getAttribute('data-img'), tf: e.style.transform}));
  return {headH: nodes.offsetTop, nodesL: nr.left, nodesT: nr.top,
    paperL: pr.left, paperT: pr.top, paperR: pr.right, paperW: paper.clientWidth,
    txs: txs, imgs: imgs,
    texts: JSON.parse((document.getElementById('d41TextsIn') || {}).value || '[]'),
    im: JSON.parse((document.getElementById('d41ImgsIn') || {}).value || '[]')};
}"""

SAVED = """() => {
  const st = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
  const out = {texts: null, imgs: null};
  (st.lists || []).forEach(l => (l.items || []).forEach(it => {
    if (!out.texts && it.texts && it.texts.length) out.texts = it.texts[0];
    if (!out.imgs && it.imgs && it.imgs.length) out.imgs = it.imgs[0];
  }));
  return out;
}"""

PEN_LIVE = """([pts, pid]) => {
  const svg = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const mk = (t, p) => new PointerEvent(t, {pointerId: pid, pointerType: 'touch', isPrimary: true,
    clientX: r.left + p[0], clientY: r.top + p[1], bubbles: true, cancelable: true});
  svg.dispatchEvent(mk('pointerdown', pts[0]));
  for (let i = 1; i < pts.length; i++) svg.dispatchEvent(mk('pointermove', pts[i]));
  const live = [...svg.querySelectorAll('path')].pop();
  return {d: live ? live.getAttribute('d') : '', headH: document.getElementById('d41Nodes').offsetTop};
}"""

PEN_UP = """(pid) => {
  const svg = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const last = svg.__lastPt || [0, 0];
  svg.dispatchEvent(new PointerEvent('pointerup', {pointerId: pid, pointerType: 'touch', isPrimary: true,
    clientX: r.left + last[0], clientY: r.top + last[1], bubbles: true, cancelable: true}));
  const paths = [...svg.querySelectorAll('path')];
  const p = paths[paths.length - 1];
  return {n: paths.length, d: p ? p.getAttribute('d') : ''};
}"""

PEN_PATH = """() => {
  const paths = [...document.querySelectorAll('#d41Pen path')];
  return paths.map(p => p.getAttribute('d'));
}"""


def pts(d):
    return [(float(a), float(b)) for a, b in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", d or "")]


def drag(page, sx, sy, dx, dy, steps=12, settle=200, shot=None):
    """누른 채 끌어 (dx, dy) 만큼 옮긴 «도중»의 상태를 재고 손을 뗀 «뒤»의 상태도 잰다."""
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.mouse.move(sx + dx, sy + dy, steps=steps)
    page.wait_for_timeout(settle)
    during = page.evaluate(BOX)
    if shot:
        page.screenshot(path=os.path.join(SHOT, shot))
    page.mouse.up()
    page.wait_for_timeout(520)
    after = page.evaluate(BOX)
    return during, after


def add_photo(page, path):
    page.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    page.wait_for_timeout(220)
    page.set_input_files("#d41ImgIn", [path])
    page.wait_for_timeout(1300)


with sync_playwright() as p:
    browser = launch(p)

    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    watch(page, errs)

    # ==================================================================
    # 1. 버전
    # ==================================================================
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    check('sw.js 캐시 버전 twolog-v51', 'const VERSION = "twolog-v51"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v51", 'var APP_VERSION = "v51"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v50 문자열이 남아 있지 않음",
          "twolog-v50" not in sw and 'APP_VERSION = "v50"' not in app_js)

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", page.evaluate(SEED_JS))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 4, 620)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v51」", ver.strip() == "버전 v51", ver)

    # ==================================================================
    # 2. 글 상자 끌기 — 끄는 도중에도 손가락 자리
    # ==================================================================
    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="그림판").first.click()
    page.wait_for_timeout(560)
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(820)

    b0 = page.evaluate(BOX)
    check("머리 높이(d41Top) 108px — 두 자(종이·놓이는 칸)의 차이", b0["headH"] == 108, b0["headH"])

    # 빈 종이를 톡 눌러 글 상자를 만들고 글을 써요
    page.mouse.click(b0["paperL"] + 80, b0["paperT"] + 108 + 150)
    page.wait_for_timeout(520)
    page.keyboard.type("끌어 보는 글씨")
    page.wait_for_timeout(320)
    page.mouse.click(b0["paperL"] + 330, b0["paperT"] + 760)   # 빈 종이 → 글쓰기 마침
    page.wait_for_timeout(560)
    b1 = page.evaluate(BOX)
    check("글 상자 하나 (글자 그대로)", len(b1["txs"]) == 1 and b1["txs"][0]["txt"] == "끌어 보는 글씨",
          [(t["txt"], round(t["l"]), round(t["t"])) for t in b1["txs"]])

    tx = b1["txs"][0]
    sx, sy = tx["l"] + 26, tx["t"] + 12
    dx, dy = 34, 150
    during, after = drag(page, sx, sy, dx, dy, shot="diary-v51-drag-text-during.png")
    dtx = during["txs"][0]
    adx = after["txs"][0]
    err_x = dtx["l"] - (tx["l"] + dx)
    err_y = dtx["t"] - (tx["t"] + dy)
    check("끄는 «도중» 글 상자가 시작 자리 + 이동 거리 그대로 (위로 뜨지 않음) — ±1.5px",
          abs(err_x) <= 1.5 and abs(err_y) <= 1.5, (round(err_x, 1), round(err_y, 1), dtx["tf"]))
    check("끄는 도중 위로 108px 떠 있지 않음 (머리 높이만큼 어긋나지 않음)",
          abs(err_y + during["headH"]) > 20, round(err_y, 1))
    grab0 = (tx["l"] - sx, tx["t"] - sy)
    grab1 = (dtx["l"] - (sx + dx), dtx["t"] - (sy + dy))
    check("손가락과 상자의 거리가 끄는 동안 그대로 (상자가 손가락에 붙어 있음) — ±1.5px",
          abs(grab1[0] - grab0[0]) <= 1.5 and abs(grab1[1] - grab0[1]) <= 1.5,
          (round(grab0[0], 1), round(grab0[1], 1), round(grab1[0], 1), round(grab1[1], 1)))
    check("손을 떼도 튀지 않음 (떼기 전 = 떼고 난 뒤) — ±1.5px",
          abs(adx["l"] - dtx["l"]) <= 1.5 and abs(adx["t"] - dtx["t"]) <= 1.5,
          (round(adx["l"] - dtx["l"], 1), round(adx["t"] - dtx["t"], 1)))
    check("끈 자리가 상자에 남아 있음 (왼쪽·위로 되돌아가지 않음)",
          adx["l"] > tx["l"] + 20 and adx["t"] > tx["t"] + 100,
          (round(tx["l"]), round(adx["l"]), round(tx["t"]), round(adx["t"])))
    W = after["paperW"]
    mx = after["texts"][0]["x"] * W + after["nodesL"] - adx["l"]
    my = after["texts"][0]["y"] * W + after["nodesT"] - adx["t"]
    check("저장 좌표(x·y)가 화면 자리와 같음 — 상자를 다시 열어도 그 자리 (±2px)",
          abs(mx) <= 2 and abs(my) <= 2, (round(mx, 1), round(my, 1)))
    page.wait_for_timeout(900)
    saved = page.evaluate(SAVED)
    sy_err = abs(saved["texts"]["y"] * W + after["nodesT"] - adx["t"]) if saved["texts"] else 999
    check("앱 저장(폰에 남는 기록)에도 그 자리 (±2px)", sy_err <= 2, (saved["texts"], round(sy_err, 1)))
    page.screenshot(path=os.path.join(SHOT, "diary-v51-drag-text-after.png"))

    # 위로 세게 끌어도 종이 위로 나가지 않음
    adx = after["txs"][0]
    during2, after2 = drag(page, adx["l"] + 26, adx["t"] + 12, 0, -420)
    up_t = after2["txs"][0]
    check("위로 세게 끌어도 종이 맨 위(머리 높이)에서 멈춤 — 종이 밖으로 안 나감",
          abs(up_t["t"] - after2["nodesT"]) <= 2, (round(up_t["t"], 1), round(after2["nodesT"], 1)))
    # 오른쪽으로 세게 끌어도 종이 안
    during3, after3 = drag(page, up_t["l"] + 26, up_t["t"] + 12, 400, 40)
    rt = after3["txs"][0]
    check("오른쪽으로 세게 끌어도 종이 안에 머묾 (잘리지 않음)",
          rt["r"] <= after3["paperR"] + 1 and rt["l"] >= after3["nodesL"] - 1,
          (round(rt["l"], 1), round(rt["r"], 1), round(after3["paperR"], 1)))
    page.screenshot(path=os.path.join(SHOT, "diary-v51-drag-text-edge.png"))

    # ==================================================================
    # 3. 사진 상자 끌기 — 같은 자
    # ==================================================================
    durl = page.evaluate("""() => { const c = document.createElement('canvas'); c.width = 400; c.height = 300;
      const x = c.getContext('2d'); x.fillStyle = '#E8C9C1'; x.fillRect(0, 0, 400, 300);
      x.fillStyle = '#3D6E8A'; x.fillRect(40, 40, 320, 220); return c.toDataURL('image/jpeg', 0.9); }""")
    with open("/tmp/v51-photo.jpg", "wb") as f:
        f.write(_b64.b64decode(durl.split(",", 1)[1]))
    add_photo(page, "/tmp/v51-photo.jpg")
    g1 = page.evaluate(BOX)
    check("사진을 붙이면 종이 위 사진 상자", len(g1["imgs"]) == 1, g1["im"])
    im = g1["imgs"][0]
    pdx, pdy = -22, 64
    d1, a1 = drag(page, im["l"] + 40, im["t"] + 30, pdx, pdy, shot="diary-v51-drag-photo-during.png")
    p1 = d1["imgs"][0]
    pex = p1["l"] - (im["l"] + pdx)
    pey = p1["t"] - (im["t"] + pdy)
    check("사진도 끄는 «도중» 시작 자리 + 이동 거리 그대로 (±1.5px)",
          abs(pex) <= 1.5 and abs(pey) <= 1.5, (round(pex, 1), round(pey, 1)))
    a1i = a1["imgs"][0]
    check("사진도 손을 떼도 튀지 않음 (±1.5px)",
          abs(a1i["l"] - p1["l"]) <= 1.5 and abs(a1i["t"] - p1["t"]) <= 1.5,
          (round(a1i["l"] - p1["l"], 1), round(a1i["t"] - p1["t"], 1)))
    pixx = a1["im"][0]["x"] * W + a1["nodesL"] - a1i["l"]
    pixy = a1["im"][0]["y"] * W + a1["nodesT"] - a1i["t"]
    check("사진 저장 좌표도 화면 자리와 같음 (±2px)", abs(pixx) <= 2 and abs(pixy) <= 2,
          (round(pixx, 1), round(pixy, 1)))
    page.screenshot(path=os.path.join(SHOT, "diary-v51-drag-photo-after.png"))

    # ==================================================================
    # 4. 그린 그림(획) 옮기기 — 다른 이동 함수 점검
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(460)
    pts0 = [[90, 620], [180, 660], [270, 635]]
    page.evaluate(PEN_LIVE, [pts0, 5151])
    page.evaluate("([pts]) => { document.getElementById('d41Pen').__lastPt = pts[pts.length - 1]; }", [pts0])
    page.evaluate(PEN_UP, 5151)
    page.wait_for_timeout(400)
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()   # 펜 → 글씨 (새 상자는 안 생겨요)
    page.wait_for_timeout(420)
    before_path = page.evaluate(PEN_PATH)
    check("그린 그림이 하나 (펜 모드에서 그림)", len(before_path) >= 1, len(before_path))
    gsx = b0["paperL"] + 180
    gsy = b0["paperT"] + 660
    page.mouse.move(gsx, gsy)
    page.mouse.down()
    page.mouse.move(gsx + 30, gsy - 46, steps=12)
    page.wait_for_timeout(200)
    mid_path = page.evaluate(PEN_PATH)
    page.mouse.up()
    page.wait_for_timeout(420)
    end_path = page.evaluate(PEN_PATH)
    p_before = pts(before_path[-1]) if before_path else []
    p_mid = pts(mid_path[-1]) if mid_path else []
    shift = max(((b[0] - a[0]), (b[1] - a[1])) for a, b in zip(p_before, p_mid)) if p_before and p_mid else (999, 999)
    check("그림을 끄는 «도중» 손가락 거리(30, -46) 그대로 — ±1.5px",
          abs(shift[0] - 30) <= 1.5 and abs(shift[1] + 46) <= 1.5, (round(shift[0], 1), round(shift[1], 1)))
    shift2 = max(((b[0] - a[0]), (b[1] - a[1])) for a, b in zip(p_mid, pts(end_path[-1]))) if p_mid else (999, 999)
    check("그림도 손을 떼도 튀지 않음 (±1.5px)",
          abs(shift2[0]) <= 1.5 and abs(shift2[1]) <= 1.5, (round(shift2[0], 1), round(shift2[1], 1)))
    page.screenshot(path=os.path.join(SHOT, "diary-v51-drag-pen-stroke.png"))

    check("끌기 점검 중 콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()
    browser.close()

print("")
if fails:
    print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS — v51")
