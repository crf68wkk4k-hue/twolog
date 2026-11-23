"""투로그 v47 확인 — 모눈 다이어리 손보기 세 가지.

1) 버전: sw.js 캐시 twolog-v50 · APP_VERSION v50 · My 탭 「버전 v50」
2) ↶ 되돌리기 · ↷ 다시 실행 아이콘을 크게 — 단추 44px · 그림 27px · 획 2.05
   (v46 은 34px·19px 이었어요 — 펜/T/사진 46px·22px 보다도 조금 크게)
3) 보기 화면은 «풀 사이즈» — 이미 쓴 다이어리를 열면 도구 줄·도구 판이 완전히 사라지고
   모눈종이가 상단 바 바로 아래부터 화면을 꽉 채움 · 종이를 한 번 톡 누르면
   도구 줄이 나타나 고치기로 바뀌고, 그 «깨우는» 탭으로 빈 글 상자가 생기지 않음
4) 색상 스펙트럼 판 — 아이폰과 같은 방향 (세로 = 색(hue) 빨강→초록→파랑, 가로 = 하양→순색→검정)
   프리셋 9색은 «날씨의 요정» 팔레트 + 검정 · 원형 동그라미가 한 줄에
5) 글 상자 끌기 — 고른 상자를 끌면 화면에서 다시 그리지 않고(같은 요소가 살아 있음)
   손가락을 따라 매끄럽게 움직이고, 손을 뗄 때만 좌표를 저장·동기화
   (끄는 동안 hidden 입력값이 그대로 · transform 으로만 이동 · 손 떼면 left/top 으로 정리)
6) 빈 상자(«글을 써 보세요»)도 고른 채로 끌 수 있고, 끌면 입력(키보드)이 열리지 않음
7) touch-action: none · 끄는 동안 글자 고르기 막음 / 보기 모드에서는 스크롤·복사 허용
8) 콘솔/페이지 오류 0건

    python3 tests/v47.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def tab(page, idx, wait=560):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


SEED_JS = """() => {
  const st = JSON.parse(JSON.stringify(window.__app.state));
  st.couple.me = '소영'; st.couple.you = '준영';
  st.lists = (st.lists || []).concat([{ id: 'Ld47', title: '그림판', emoji: '', kind: 'memo', items: [] }]);
  st.groups = st.groups || {}; st.groups['list:Ld47'] = [];
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Ld47').concat(['list:Ld47']);
  return JSON.stringify(st);
}"""

UNDO_SIZE = """() => {
  const q = s => document.querySelector('#sheet ' + s);
  const r = e => e ? e.getBoundingClientRect() : null;
  const u = q('#d41UndoBtn'), rd = q('#d41RedoBtn');
  const us = u ? u.querySelector('svg') : null, rs = rd ? rd.querySelector('svg') : null;
  const t = q('.d41-tool[aria-label="글씨"]'), p = q('.d41-tool[aria-label="펜 그리기"]');
  const ps = p ? p.querySelector('svg') : null;
  const path = us ? us.querySelector('path') : null;
  const cs = path ? getComputedStyle(path) : null;
  const ur = r(u), rr = r(rd), tr = r(t);
  return {
    btn: ur ? [Math.round(ur.width), Math.round(ur.height)] : [0, 0],
    redoBtn: rr ? [Math.round(rr.width), Math.round(rr.height)] : [0, 0],
    icon: us ? [Math.round(r(us).width), Math.round(r(us).height)] : [0, 0],
    redoIcon: rs ? Math.round(r(rs).width) : 0,
    toolIcon: ps ? Math.round(r(ps).width) : 0,
    penIcon: p ? Math.round(r(p.querySelector('svg')).width) : 0,
    stroke: cs ? parseFloat(cs.strokeWidth) : 0,
    sameRow: ur && tr ? Math.abs((ur.top + ur.height / 2) - (tr.top + tr.height / 2)) <= 2 : false,
    visible: ur ? ur.width > 0 : false
  };
}"""

VIEWMODE = """() => {
  const q = s => document.querySelector('#sheet ' + s);
  const tools = q('.d41-tools'), canvas = document.getElementById('d41Canvas');
  const top = q('.d41-top'), panel = document.getElementById('d41Panel');
  const paper = document.getElementById('d41Paper');
  const tr = tools ? tools.getBoundingClientRect() : null;
  const cr = canvas ? canvas.getBoundingClientRect() : null;
  const hr = top ? top.getBoundingClientRect() : null;
  const pr = paper ? paper.getBoundingClientRect() : null;
  return {
    editing: !!document.querySelector('#sheet .d41-txt[contenteditable="true"]'),
    toolsHidden: tools ? tools.hidden : null,
    toolsH: tr ? Math.round(tr.height) : -1,
    toolsShown: tr ? tr.height > 0 : false,
    anim: tools ? getComputedStyle(tools).animationName : '',
    canvasTop: cr ? Math.round(cr.top) : -1,
    headerTop: hr ? Math.round(hr.top) : -1,
    headerBottom: hr ? Math.round(hr.bottom) : -1,
    paperTop: pr ? Math.round(pr.top) : -1,
    canvasH: cr ? Math.round(cr.height) : 0,
    panelShown: panel ? (!panel.hidden && panel.getBoundingClientRect().height > 0) : null,
    nTx: document.querySelectorAll('#sheet .d41-tx').length,
    viewClass: !!document.querySelector('#sheet .d41-paper.view')
  };
}"""

SP = """() => {
  const el = document.getElementById('d41Sp');
  const cv = document.getElementById('d41SpCv');
  const shown = !!(el && !el.hidden && el.offsetHeight > 0);
  const pv = document.getElementById('d41SpPv');
  const dot = document.getElementById('d41SpDot');
  const dots = [...document.querySelectorAll('#sheet .d41-sp-dotb')];
  const rowTops = dots.map(d => Math.round(d.getBoundingClientRect().top));
  return {
    shown: shown, hasCv: !!cv,
    title: (document.querySelector('#sheet .d41-sp-tt') || {}).textContent || '',
    closeX: !!document.querySelector('#sheet .d41-sp-x'),
    presets: dots.map(d => d.getAttribute('data-color')),
    presetW: dots.length ? Math.round(dots[0].getBoundingClientRect().width) : 0,
    presetRound: dots.length ? getComputedStyle(dots[0]).borderRadius : '',
    rows: new Set(rowTops).size,
    hex: (document.getElementById('d41SpHex') || {}).textContent || '',
    swatch: pv ? pv.style.background : '',
    ring: dot ? [dot.style.left, dot.style.top] : [],
    cvH: cv ? Math.round(cv.getBoundingClientRect().height) : 0
  };
}"""

GRAD = """() => {
  const cv = document.getElementById('d41SpCv');
  const c = cv.getContext('2d');
  const px = (fx, fy) => { const d = c.getImageData(Math.round(fx * (cv.width - 1)), Math.round(fy * (cv.height - 1)), 1, 1).data; return [d[0], d[1], d[2]]; };
  const lum = p => Math.round(0.299 * p[0] + 0.587 * p[1] + 0.114 * p[2]);
  return {
    white: px(0.01, 0.2), black: px(0.97, 0.2), vivid: px(0.5, 0.02),
    lumL: lum(px(0.01, 0.2)), lumR: lum(px(0.97, 0.2)),
    top: px(0.5, 0.01), orange: px(0.5, 0.12), green: px(0.5, 0.34),
    cyan: px(0.5, 0.5), blue: px(0.5, 0.67), magenta: px(0.5, 0.85), bottom: px(0.5, 0.99),
    halfWhite: px(0.25, 0.01), halfDark: px(0.75, 0.01)
  };
}"""

SETUP = """() => {
  window.__v47 = {
    mk(type, x, y) {
      return new PointerEvent(type, {pointerId: 5150, pointerType: 'touch', isPrimary: true,
        clientX: x, clientY: y, bubbles: true, cancelable: true});
    },
    node(id) { return document.querySelector('#d41Nodes .d41-tx[data-tx="' + id + '"]'); },
    start(id) {
      const el = this.node(id); if (!el) return null;
      el.scrollIntoView({block: 'center'});
      const r = el.getBoundingClientRect();
      const pr = document.getElementById('d41Paper').getBoundingClientRect();
      this.id = id; this.el = el; this.tgt = el.querySelector('.d41-txt') || el;
      el.__v47probe = 1;      /* 끌기 시작할 때마다 1 — 다시 그리면 새 요소라 사라져요 */
      this.sx = r.left + 14; this.sy = r.top + 8;
      this.base = {left: Math.round(r.left), top: Math.round(r.top), W: Math.round(pr.width)};
      this.left0 = el.style.left; this.top0 = el.style.top;
      this.in0 = document.getElementById('d41TextsIn').value;
      this.tgt.dispatchEvent(this.mk('pointerdown', this.sx, this.sy));
      this.moved = false;
      return {sel: el.classList.contains('sel'), left0: this.left0, top0: this.top0,
        W: this.base.W, baseLeft: this.base.left, baseTop: this.base.top};
    },
    move(dx, dy) {
      this.moved = true;
      this.tgt.dispatchEvent(this.mk('pointermove', this.sx + dx, this.sy + dy));
    },
    end(dx, dy) { this.tgt.dispatchEvent(this.mk('pointerup', this.sx + dx, this.sy + dy)); },
    cancel(dx, dy) { this.tgt.dispatchEvent(this.mk('pointercancel', this.sx + dx, this.sy + dy)); },
    state() {
      const el = this.el, r = el.getBoundingClientRect();
      const t = el.style.transform || '';
      const m = /translate3d\\(([-\\d.]+)px,\\s*([-\\d.]+)px/.exec(t);
      return {
        same: document.querySelector('#d41Nodes .d41-tx[data-tx="' + this.id + '"]') === el,
        probe: el.__v47probe || 0, connected: el.isConnected,
        tf: t, tx: m ? parseFloat(m[1]) : 0, ty: m ? parseFloat(m[2]) : 0,
        left: el.style.left, top: el.style.top,
        rectLeft: Math.round(r.left), rectTop: Math.round(r.top),
        drag: el.classList.contains('drag'),
        sel: el.classList.contains('sel'),
        left0: this.left0, top0: this.top0, W: this.base.W,
        baseLeft: this.base.left, baseTop: this.base.top,
        inNow: document.getElementById('d41TextsIn').value,
        typing: !!(document.activeElement && document.activeElement.classList && document.activeElement.classList.contains('d41-txt')),
        nTx: document.querySelectorAll('#sheet .d41-tx').length
      };
    }
  };
  return true;
}"""

STYLE = """([id]) => {
  const el = document.querySelector('#d41Nodes .d41-tx[data-tx="' + id + '"]');
  const ed = el ? el.querySelector('.d41-txt') : null;
  const cs = el ? getComputedStyle(el) : null;
  const es = ed ? getComputedStyle(ed) : null;
  return {
    touch: cs ? cs.touchAction : '',
    select: cs ? (cs.userSelect || cs.webkitUserSelect) : '',
    edSelect: es ? (es.userSelect || es.webkitUserSelect) : '',
    txCount: document.querySelectorAll('#sheet .d41-tx').length,
    selCount: document.querySelectorAll('#sheet .d41-tx.sel').length
  };
}"""

NK = """() => {
  const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
  const p = document.getElementById('nkPanel');
  const act = document.querySelector('#sheet #noteOrderList .nord-row.active');
  const cards = p ? [...p.querySelectorAll('.nk-card')] : [];
  const ca = cards.filter(c => c.classList.contains('active'))[0];
  const pr = p ? p.getBoundingClientRect() : null;
  return {
    rows: rows.map(r => (r.getAttribute('data-key') || '') + ':' + ((r.querySelector('.nord-nm') || {}).value || '')),
    rowKinds: rows.map(r => r.getAttribute('data-kind') || ''),
    active: act ? act.getAttribute('data-key') : '',
    activeKind: ca ? ca.getAttribute('data-kind') : '',
    panelHidden: p ? p.hidden : null,
    panelKey: p ? (p.querySelector('.nkind') || {}).getAttribute ? p.querySelector('.nkind').getAttribute('data-key') : '' : '',
    afterRow: p && p.previousElementSibling ? (p.previousElementSibling.getAttribute('data-key') || '') : '',
    kinds: cards.map(c => c.getAttribute('data-kind')),
    panelTop: pr ? Math.round(pr.top) : -1,
    panelBottom: pr ? Math.round(pr.bottom) : -1,
    vh: window.innerHeight,
    focused: (document.activeElement || {}).className || ''
  };
}"""

SAVED = """() => {
  const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
  const l = (s.lists || []).filter(x => x.id === 'Ld47')[0] || {};
  const items = (l.items || []);
  const it = items.filter(x => (x.texts || []).some(t => String(t.text || '').indexOf('v47') >= 0))[0]
    || items[items.length - 1] || {};
  const t = (it.texts || [])[0] || {};
  return {count: items.length, x: t.x, y: t.y, text: t.text || '',
    nTexts: (it.texts || []).length, nPen: (it.pen || []).length};
}"""

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
    check('sw.js 캐시 버전 twolog-v50', 'const VERSION = "twolog-v50"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v50", 'var APP_VERSION = "v50"' in app_js,
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
    check("My 탭 맨 위에 「버전 v50」", ver.strip() == "버전 v50", ver)

    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="그림판").first.click()
    page.wait_for_timeout(560)

    # ==================================================================
    # 2. ↶ ↷ 아이콘 크게 (새 다이어리는 바로 고치기 — 도구 줄이 보여요)
    # ==================================================================
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(760)
    uz = page.evaluate(UNDO_SIZE)
    check("새 다이어리는 바로 고치기 — ↶ ↷ 단추가 보임", uz["visible"] and uz["sameRow"], uz)
    check("↶ ↷ 단추 44px (v46 은 34px)", uz["btn"] == [44, 44] and uz["redoBtn"] == [44, 44],
          (uz["btn"], uz["redoBtn"]))
    check("↶ ↷ 그림 27px — 펜·T·사진(22px)보다 크고 v46(19px)보다 확실히 큼",
          uz["icon"] == [27, 27] and uz["redoIcon"] == 27 and uz["toolIcon"] == 22
          and uz["icon"][0] > uz["toolIcon"], (uz["icon"], uz["toolIcon"]))
    check("↶ ↷ 획이 조금 굵어짐 (2.05)", abs(uz["stroke"] - 2.05) < 0.01, uz["stroke"])
    page.screenshot(path=os.path.join(SHOT, "diary-v47-tools.png"))

    # ==================================================================
    # 3. 색상 스펙트럼 판 — 방향 · 프리셋 (날씨의 요정)
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(360)
    page.locator("#sheet .d41-dk[aria-label='펜 색']").click()
    page.wait_for_timeout(420)
    sp = page.evaluate(SP)
    want = ["#111111", "#F46B62", "#DC4A98", "#9268C9", "#4E8EC1", "#4FA78E", "#F7CE46", "#F69B42", "#8D6F61"]
    check("스펙트럼 판이 열림 — «색상» 제목 · × 닫기 · 캔버스", sp["shown"] and sp["hasCv"]
          and sp["title"] == "색상" and sp["closeX"], (sp["shown"], sp["title"]))
    check("프리셋 9색이 «날씨의 요정» 팔레트 + 검정 (순서까지)", sp["presets"] == want, sp["presets"])
    check("프리셋은 원형 · 한 줄에 가지런히 (24px)", sp["presetW"] == 24
          and sp["presetRound"].startswith("50%") and sp["rows"] == 1,
          (sp["presetW"], sp["presetRound"], sp["rows"]))
    gr = page.evaluate(GRAD)
    check("가로 — 왼쪽은 하양, 오른쪽은 검정", gr["lumL"] >= 240 and gr["lumR"] <= 30,
          (gr["lumL"], gr["lumR"]))
    check("가운데는 순색 (빨강 255,0,0 근처)",
          gr["vivid"][0] >= 240 and gr["vivid"][1] < 60 and gr["vivid"][2] < 40, gr["vivid"])
    check("세로가 색(hue) — 위 빨강 → 주황 → 초록 → 하늘 → 파랑 → 자홍 → 아래 빨강",
          gr["top"][0] >= 240 and gr["top"][1] < 40
          and gr["orange"][0] >= 220 and 90 <= gr["orange"][1] <= 200 and gr["orange"][2] < 60
          and gr["green"][1] >= 240 and gr["green"][0] < 40
          and gr["cyan"][1] >= 200 and gr["cyan"][2] >= 200 and gr["cyan"][0] < 90
          and gr["blue"][2] >= 240 and gr["blue"][0] < 40
          and gr["magenta"][0] >= 200 and gr["magenta"][2] >= 200 and gr["magenta"][1] < 90
          and gr["bottom"][0] >= 240 and gr["bottom"][2] < 40,
          (gr["top"], gr["orange"], gr["green"], gr["cyan"], gr["blue"], gr["magenta"], gr["bottom"]))
    check("왼쪽 1/4 은 흰색과 순색 사이(분홍) · 오른쪽 1/4 은 검정 쪽",
          gr["halfWhite"][0] >= 240 and 100 <= gr["halfWhite"][1] <= 200
          and gr["halfDark"][0] <= 140 and gr["halfDark"][0] >= gr["halfDark"][1],
          (gr["halfWhite"], gr["halfDark"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v47-spectrum.png"))

    page.locator("#sheet .d41-sp-dotb").nth(6).click()      # #F7CE46
    page.wait_for_timeout(360)
    pick = page.evaluate("""() => ({shown: !document.getElementById('d41Sp').hidden,
      swatch: (document.querySelector('#sheet .d41-dkk') || {}).style.background || ''})""")
    check("프리셋을 누르면 그 색이 칠해지고 판이 닫힘 (#F7CE46)", pick["shown"] is False
          and pick["swatch"] == "rgb(247, 206, 70)", pick)

    # ==================================================================
    # 4. 글 상자 끌기 — 고른 상자 · 끄는 동안 다시 그리지 않음
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(420)
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(520)
    wrote = page.evaluate("""() => {
      const ed = document.querySelector('#d41Nodes .d41-txt');
      if (!ed) return false;
      ed.innerText = 'v47 옮겨 볼 글';
      ed.dispatchEvent(new Event('input', {bubbles: true}));
      return true;
    }""")
    page.wait_for_timeout(400)
    check("글 상자에 글을 씀", wrote is True)
    page.evaluate(SETUP)
    tid = page.evaluate("() => { const e = document.querySelector('#d41Nodes .d41-tx'); return e ? e.getAttribute('data-tx') : ''; }")

    # 4-1. 톡 눌러 고르기 (키보드 내리기) — 두 번 탭이 되지 않게 잠깐 기다려요
    page.wait_for_timeout(640)
    page.evaluate("(id) => window.__v47.start(id)", tid)
    page.evaluate("() => window.__v47.end(0, 0)")
    page.wait_for_timeout(240)
    tap = page.evaluate("() => window.__v47.state()")
    check("상자를 톡 누르면 고른 채(점선)로 남고 키보드는 내려감",
          tap["sel"] and tap["same"] and not tap["typing"], (tap["sel"], tap["typing"]))
    check("톡 누르기는 상자를 옮기지 않음 (자리 그대로 · transform 없음)",
          tap["tf"] == "" and tap["left"] == tap["left0"], (tap["tf"], tap["left"], tap["left0"]))

    # 4-2. 끌기 — 5px · 20px · 45px · 70px
    page.evaluate("(id) => window.__v47.start(id)", tid)
    page.evaluate("([dx, dy]) => window.__v47.move(dx, dy)", [5, 0])
    page.wait_for_timeout(70)
    s1 = page.evaluate("() => window.__v47.state()")
    check("4px 를 넘기면 곧바로 손가락을 따라옴 (5px → 5px, 튀지 않음)",
          s1["same"] and s1["probe"] == 1 and s1["drag"] and abs(s1["tx"] - 5) <= 1.5
          and abs((s1["rectLeft"] - s1["baseLeft"]) - s1["tx"]) <= 1.5,
          (s1["tx"], s1["rectLeft"] - s1["baseLeft"], s1["drag"]))
    check("끄는 동안 같은 요소가 그대로 (다시 그리지 않음)", s1["same"] and s1["connected"] and s1["probe"] == 1, s1["probe"])
    check("끄는 동안에는 저장·동기화하지 않음 (hidden 입력값 그대로)",
          s1["inNow"] == tap["inNow"], (len(s1["inNow"]), len(tap["inNow"])))
    txs = [s1["tx"]]
    for dx, dy in ((20, 10), (45, 25), (70, 40)):
        page.evaluate("([dx, dy]) => window.__v47.move(dx, dy)", [dx, dy])
        page.wait_for_timeout(70)
        txs.append(page.evaluate("() => window.__v47.state()")["tx"])
    check("손가락을 따라 계단 없이 이어짐 (5 → 20 → 45 → 70 근처)",
          all(abs(a - b) <= 2.2 for a, b in zip(txs, [5, 20, 45, 70])), txs)
    page.screenshot(path=os.path.join(SHOT, "diary-v47-drag.png"))

    page.evaluate("([dx, dy]) => window.__v47.end(dx, dy)", [70, 40])
    page.wait_for_timeout(420)
    fin = page.evaluate("() => window.__v47.state()")
    left_pct = float(fin["left"].strip("%"))
    base_pct = float(fin["left0"].strip("%"))
    check("손을 떼면 transform 을 지우고 left/top 으로 자리를 정리",
          fin["tf"] == "" and fin["left"] != "" and fin["top"].endswith("px"), (fin["tf"], fin["left"], fin["top"]))
    check("떼는 순간의 자리가 그대로 저장 (오른쪽 +70px)",
          abs(left_pct - (base_pct + 70 / max(1, fin["W"]) * 100)) <= 1.2, (left_pct, base_pct, fin["W"]))
    check("저장·동기화는 손을 뗄 때 한 번 (hidden 입력값이 바뀜)", fin["inNow"] != tap["inNow"])
    saved = page.evaluate(SAVED)
    check("자동 저장된 다이어리에 옮긴 좌표가 남음",
          abs(float(saved["x"] or 0) - left_pct / 100) <= 0.02 and "v47" in saved["text"],
          (saved["x"], left_pct / 100, saved["text"]))
    check("끌어도 글이 사라지지 않음 (DOM·저장 모두 유지)",
          fin["same"] and fin["nTx"] == s1["nTx"] and saved["nTexts"] >= 1, (fin["nTx"], saved["nTexts"]))

    css = page.evaluate(STYLE, [tid])
    check("글 상자는 touch-action:none · 고를 때 글자 고르기 막음",
          css["touch"] == "none" and css["select"] == "none", (css["touch"], css["select"]))
    check("상자는 그대로 하나 · 고른 상자 하나", css["txCount"] == 1 and css["selCount"] == 1,
          (css["txCount"], css["selCount"]))

    # ==================================================================
    # 5. 빈 상자(«글을 써 보세요»)도 고른 채로 끌기
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(620)
    empty = page.evaluate("""() => {
      const els = [...document.querySelectorAll('#d41Nodes .d41-tx')];
      const e = els.filter(x => !(x.innerText || '').trim())[0];
      return e ? {id: e.getAttribute('data-tx'), ph: (e.querySelector('.d41-txt') || {}).getAttribute
        ? e.querySelector('.d41-txt').getAttribute('data-ph') : ''} : null;
    }""")
    check("T 도구로 빈 글 상자가 생김 («글을 써 보세요»)", bool(empty) and empty["ph"] == "글을 써 보세요", empty)
    page.wait_for_timeout(700)
    page.evaluate("(id) => window.__v47.start(id)", empty["id"])
    page.evaluate("() => window.__v47.end(0, 0)")
    page.wait_for_timeout(220)
    page.evaluate("(id) => window.__v47.start(id)", empty["id"])
    page.evaluate("([dx, dy]) => window.__v47.move(dx, dy)", [12, 6])
    page.wait_for_timeout(70)
    page.evaluate("([dx, dy]) => window.__v47.move(dx, dy)", [40, 20])
    page.wait_for_timeout(70)
    e1 = page.evaluate("() => window.__v47.state()")
    check("빈 상자도 끌면 바로 따라옴 (튀지 않고 · 입력창 열리지 않음)",
          e1["same"] and e1["drag"] and abs(e1["tx"] - 40) <= 2 and not e1["typing"], (e1["tx"], e1["typing"]))
    page.evaluate("([dx, dy]) => window.__v47.end(dx, dy)", [40, 20])
    page.wait_for_timeout(320)
    e2 = page.evaluate("() => window.__v47.state()")
    check("빈 상자도 손을 떼면 자리가 남고 상자는 지워지지 않음",
          e2["tf"] == "" and e2["connected"] and e2["left"] != e2["left0"],
          (e2["left0"], e2["left"], e2["top"]))
    check("빈 상자를 끌어도 키보드/입력이 열리지 않음", not e2["typing"])

    # ==================================================================
    # 6. 보기 화면은 풀 사이즈 · 종이를 톡 누르면 도구 줄
    # ==================================================================
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(700)
    check("뒤로 나가면 다이어리 카드가 남음",
          page.evaluate("() => document.querySelectorAll('#s-diary .d41-card').length") >= 1)
    page.locator("#s-diary .d41-card").first.click()
    page.wait_for_timeout(760)
    vm = page.evaluate(VIEWMODE)
    check("다시 열면 보기(스크롤) 모드 — 글은 고칠 수 없고 보기 클래스",
          (not vm["editing"]) and vm["viewClass"], (vm["editing"], vm["viewClass"]))
    check("도구 줄이 «완전히» 숨겨져 자리를 차지하지 않음 (display:none · 높이 0)",
          vm["toolsHidden"] and not vm["toolsShown"] and vm["toolsH"] == 0, (vm["toolsH"], vm["toolsShown"]))
    check("도구 판도 숨김 · 모눈종이가 화면 맨 위(0)까지 깔려 화면을 꽉 채움 (v50)",
          (not vm["panelShown"]) and vm["canvasTop"] == vm["paperTop"] == vm["headerTop"] == 0
          and vm["canvasH"] >= 500, (vm["canvasTop"], vm["paperTop"], vm["canvasH"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v47-view.png"))

    n_before = vm["nTx"]
    page.locator("#d41Canvas").click(position={"x": 120, "y": 300})
    page.wait_for_timeout(420)
    vm2 = page.evaluate(VIEWMODE)
    check("종이를 한 번 톡 누르면 도구 줄이 나타나고 고치기로 바뀜",
          vm2["editing"] and vm2["toolsShown"] and abs(vm2["toolsH"] - 56) <= 14, (vm2["editing"], vm2["toolsH"]))
    check("«깨우는» 탭으로 빈 글 상자가 생기지 않음", vm2["nTx"] == n_before, (n_before, vm2["nTx"]))
    check("도구 줄이 부드럽게 내려오는 애니메이션", vm2["anim"] == "d41ToolsIn", vm2["anim"])
    vm3 = page.evaluate("""() => { const e = document.querySelector('#d41Nodes .d41-tx');
      const cs = e ? getComputedStyle(e) : null;
      return {touch: cs ? cs.touchAction : '', viewClass: !!document.querySelector('#sheet .d41-paper.view'),
        undo: !!document.getElementById('d41UndoBtn')}; }""")
    check("고치기로 바뀌면 다시 끌 수 있게 (touch-action none · view 클래스 풀림)",
          vm3["touch"] == "none" and (not vm3["viewClass"]) and vm3["undo"], vm3)

    # ==================================================================
    # 7. 노트 카테고리 «+» 시트 — 새 이름을 더하면 그 줄의 속지가 바로 열림
    #    (예전엔 함께 줄에 붙은 채로 남아 새 카테고리의 속지를 고를 수 없었어요)
    # ==================================================================
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(620)
    page.locator("#s-diary .note-add").click()
    page.wait_for_timeout(760)
    page.locator("#sheet #noteOrderList .nord-row").first.click()      # 글이 있는 카테고리
    page.wait_for_timeout(420)
    first = page.evaluate(NK)
    first_key = first["rows"][0].rsplit(":", 1)[0]
    check("카테고리 줄을 누르면 그 줄 아래에 속지 판이 열림",
          first["active"] == first_key and not first["panelHidden"]
          and first["panelKey"] == first["active"] and first["kinds"] == ["check", "memo", "review", "expense"],
          first)

    page.fill("#sheet .nord-new", "요우아아아")
    page.locator("#sheet .nord-add-btn").click()
    page.wait_for_timeout(900)
    nk = page.evaluate(NK)
    new_key = nk["rows"][-1].rsplit(":", 1)[0] if nk["rows"] else ""
    check("«추가» 를 누르면 새 카테고리 줄이 생김", new_key.startswith("new:")
          and "요우아아아" in nk["rows"][-1], nk["rows"][-1])
    check("«추가» 직후 새 줄이 골라져 있음 (예전처럼 다른 줄에 붙어 있지 않음)",
          nk["active"] == new_key, (nk["active"], new_key))
    check("새 줄 바로 아래에 속지 판이 열렸음 (투두리스트·모눈 메모·별점 리뷰·지출·정산)",
          (not nk["panelHidden"]) and nk["afterRow"] == new_key and nk["panelKey"] == new_key
          and nk["kinds"] == ["check", "memo", "review", "expense"], nk)
    check("속지 판이 화면 안으로 부드럽게 따라와 바로 고를 수 있음",
          nk["panelTop"] >= 0 and nk["panelBottom"] <= nk["vh"] - 8, (nk["panelTop"], nk["panelBottom"]))
    check("이름 칸에 커서를 남기지 않음 (아이폰 키보드가 판을 가리지 않게)",
          "nord-new" not in nk["focused"], nk["focused"])
    page.screenshot(path=os.path.join(SHOT, "diary-v47-newcat.png"))

    page.locator("#sheet #nkPanel .nk-card[data-kind='memo']").click()
    page.wait_for_timeout(360)
    nk2 = page.evaluate(NK)
    check("새 줄에서 «모눈 메모» 속지를 고를 수 있음",
          nk2["activeKind"] == "memo" and "memo" in nk2["rowKinds"], (nk2["activeKind"], nk2["rowKinds"]))

    page.locator("#sheet button[type=submit]").click()
    page.wait_for_timeout(900)
    land = page.evaluate("""() => {
      const chip = document.querySelector('#s-diary .lchip.active');
      const sheetOpen = document.getElementById('sheetWrap').classList.contains('open');
      return {chip: chip ? chip.textContent.trim() : '', sheetOpen: sheetOpen,
        seg: (window.__app && window.__app.state.ui) ? window.__app.state.ui.seg : '',
        lists: (window.__app.state.lists || []).map(l => l.title + ':' + (l.kind || ''))};
    }""")
    check("«저장하기» 를 누르면 새 카테고리 탭으로 바로 넘어감",
          (not land["sheetOpen"]) and land["chip"] == "요우아아아" and "list:" in land["seg"], land)
    check("새 카테고리에 고른 속지(모눈 메모)가 그대로 붙음",
          any(x == "요우아아아:memo" for x in land["lists"]), land["lists"])

    check("브라우저 콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()
    browser.close()

print("")
if fails:
    print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS — v47")
