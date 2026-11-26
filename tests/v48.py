"""투로그 v50 확인 — 모눈 다이어리 세 가지 손질.

1) 버전: sw.js 캐시 twolog-v51 · APP_VERSION v51 · My 탭 「버전 v51」
2) 모눈종이가 «화면 맨 위»까지 — 위 줄의 «새 다이어리» 글씨·제목 칸을 없애고,
   모눈이 위 모서리(0)부터 깔림 · ‹ 뒤로는 모눈 위에 떠 있음 (투명한 위 줄)
   글·사진·그림은 위 줄+도구 줄 아래(머리 높이)부터 놓여 겹치지 않음
3) 글을 쓰고 아이폰 키보드 «완료»(blur)를 누르면 — 점선 테두리·× 가 사라져
   다 쓴 레이아웃 그대로 (글은 그대로 남고, 다시 톡 누르면 또 고를 수 있어요)
4) 펜 모드에서 바탕을 «톡» 누르면(< 4px, 끌지 않음) 도구 줄·도구 판이 사라진
   전체화면 보기로 — 끌면 그대로 선이 그려짐 (톡 누른 점은 남지 않아요)
   보기 화면에서 종이를 다시 톡 누르면 도구 줄이 돌아옴

    python3 tests/v50.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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
  st.lists = (st.lists || []).concat([{ id: 'Ld48', title: '그림판', emoji: '', kind: 'memo', items: [] }]);
  st.groups = st.groups || {}; st.groups['list:Ld48'] = [];
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Ld48').concat(['list:Ld48']);
  return JSON.stringify(st);
}"""

# 위 줄·모눈 위치 — 편집/보기 어느 쪽에서도 같은 값을 봐요
TOP = """() => {
  const q = s => document.querySelector('#sheet ' + s);
  const sheet = document.getElementById('sheet');
  const top = q('.d41-top'), canvas = document.getElementById('d41Canvas');
  const paper = document.getElementById('d41Paper'), nodes = document.getElementById('d41Nodes');
  const back = q('.d41-back'), date = q('.d41-date');
  const r = e => e ? e.getBoundingClientRect() : null;
  const sr = r(sheet), pr = r(paper), cr = r(canvas), tr = r(top), br = r(back), nr = r(nodes), dr = r(date);
  const cs = top ? getComputedStyle(top) : null;
  const ps = paper ? getComputedStyle(paper) : null;
  return {
    sheetTop: sr ? Math.round(sr.top) : -1,
    canvasTop: cr ? Math.round(cr.top) : -1,
    paperTop: pr ? Math.round(pr.top) : -1,
    paperBottom: pr ? Math.round(pr.bottom) : -1,
    paperH: pr ? Math.round(pr.height) : 0,
    grid: ps ? ps.backgroundImage : '',
    gridSize: ps ? ps.backgroundSize : '',
    topBg: cs ? cs.backgroundColor : '',
    topH: tr ? Math.round(tr.height) : -1,
    topInputs: document.querySelectorAll('#sheet .d41-top input, #sheet .d41-top textarea').length,
    topText: top ? (top.textContent || '').trim() : '',
    topBtns: [...document.querySelectorAll('#sheet .d41-top button')].map(b => b.getAttribute('aria-label')),
    backTop: br ? Math.round(br.top) : -1,
    backLeft: br ? Math.round(br.left) : -1,
    backOverPaper: (br && pr) ? (br.top >= pr.top - 1 && br.bottom <= pr.bottom) : false,
    nodesTop: nr ? Math.round(nr.top) : -1,
    dateTop: dr ? Math.round(dr.top) : -1,
    newDiaryWord: (document.getElementById('sheet').textContent || '').indexOf('새 다이어리') >= 0,
    titleInput: !!document.querySelector('#sheet .d41-title')
  };
}"""

TYPE = """() => {
  const ed = document.querySelector('#d41Nodes .d41-txt');
  if (!ed) return null;
  ed.innerText = 'v50 완료를 누른 글';
  ed.dispatchEvent(new Event('input', {bubbles: true}));
  try { ed.focus(); } catch (e) {}
  const box = ed.closest('.d41-tx');
  const x = box ? box.querySelector('.d41-txx') : null;
  const cs = getComputedStyle(ed);
  return {sel: box ? box.classList.contains('sel') : false,
    focus: document.activeElement === ed,
    outlineStyle: cs.outlineStyle, outlineWidth: cs.outlineWidth,
    xShown: x ? getComputedStyle(x).display !== 'none' : false,
    saved: (document.getElementById('d41TextsIn') || {}).value || ''};
}"""

CLEAN = """() => {
  const box = document.querySelector('#d41Nodes .d41-tx');
  const ed = box ? box.querySelector('.d41-txt') : null;
  const cs = ed ? getComputedStyle(ed) : null;
  const x = box ? box.querySelector('.d41-txx') : null;
  const st = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
  const l = (st.lists || []).filter(v => v.id === 'Ld48')[0] || {};
  const items = l.items || [];
  const it = items.filter(v => (v.texts || []).some(t => String(t.text || '').indexOf('v50') >= 0))[0] || {};
  return {
    nBox: document.querySelectorAll('#d41Nodes .d41-tx').length,
    selN: document.querySelectorAll('#d41Nodes .d41-tx.sel').length,
    hasText: !!ed && (ed.innerText || '').indexOf('v50 완료') >= 0,
    outlineStyle: cs ? cs.outlineStyle : '',
    xShown: x ? getComputedStyle(x).display !== 'none' : false,
    panelHidden: (document.getElementById('d41Panel') || {}).hidden,
    hidden: (document.getElementById('d41TextsIn') || {}).value || '',
    savedTexts: ((it.texts || [])[0] || {}).text || ''
  };
}"""

# 글 상자를 다시 톡 누르면 또 골라지는지
TAPBOX = """() => {
  const ed = document.querySelector('#d41Nodes .d41-txt');
  if (!ed) return null;
  const r = ed.getBoundingClientRect();
  const mk = t => new PointerEvent(t, {pointerId: 7070, pointerType: 'touch', isPrimary: true,
    clientX: r.left + 10, clientY: r.top + 8, bubbles: true, cancelable: true});
  ed.dispatchEvent(mk('pointerdown'));
  ed.dispatchEvent(mk('pointerup'));
  return {sel: document.querySelectorAll('#d41Nodes .d41-tx.sel').length,
    xShown: (() => { const x = document.querySelector('#d41Nodes .d41-tx .d41-txx');
      return x ? getComputedStyle(x).display !== 'none' : false; })()};
}"""

# 펜 — 바탕을 톡 (움직임 0) / 끌기 (60px 이상)
PEN = """([pts, pid]) => {
  const svg = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const mk = (t, p) => new PointerEvent(t, {pointerId: pid || 8080, pointerType: 'touch', isPrimary: true,
    clientX: r.left + p[0], clientY: r.top + p[1], bubbles: true, cancelable: true});
  svg.dispatchEvent(mk('pointerdown', pts[0]));
  for (let i = 1; i < pts.length; i++) svg.dispatchEvent(mk('pointermove', pts[i]));
  svg.dispatchEvent(mk('pointerup', pts[pts.length - 1]));
  return true;
}"""

PENSTATE = """() => {
  const tools = document.querySelector('#sheet .d41-tools');
  const panel = document.getElementById('d41Panel');
  const pen = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const tr = tools ? tools.getBoundingClientRect() : null;
  return {
    nStroke: JSON.parse((document.getElementById('d41PenIn') || {}).value || '[]').length,
    nPath: document.querySelectorAll('#d41Pen path').length,
    editing: !!document.querySelector('#sheet .d41-txt[contenteditable="true"]'),
    view: paper ? paper.classList.contains('view') : null,
    penOn: pen ? pen.classList.contains('on') : null,
    toolsHidden: tools ? tools.hidden : null,
    toolsH: tr ? Math.round(tr.height) : -1,
    panelHidden: panel ? panel.hidden : null
  };
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
    check('sw.js 캐시 버전 twolog-v51', 'const VERSION = "twolog-v51"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v51", 'var APP_VERSION = "v51"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v47 문자열이 남아 있지 않음",
          "twolog-v47" not in sw and 'APP_VERSION = "v47"' not in app_js)

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed = page.evaluate(SEED_JS)
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 4, 620)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v51」", ver.strip() == "버전 v51", ver)

    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="그림판").first.click()
    page.wait_for_timeout(560)

    # ==================================================================
    # 2. 새 다이어리 — «새 다이어리» 글씨 없이 모눈이 맨 위까지
    # ==================================================================
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(820)
    top = page.evaluate(TOP)
    check("위 줄(.d41-top)에는 ‹ 뒤로 하나만 — 제목 글씨·제목 칸 없음",
          top["topBtns"] == ["뒤로"] and top["topText"] == "" and top["topInputs"] == 0
          and not top["titleInput"], top)
    check("화면 어디에도 «새 다이어리» 글씨가 없음",
          top["newDiaryWord"] is False, top["newDiaryWord"])
    check("모눈종이가 화면 위 모서리(0)까지 — 위에 흰 띠가 없음",
          top["paperTop"] == 0 and top["canvasTop"] == 0 and top["paperTop"] == top["sheetTop"],
          (top["paperTop"], top["canvasTop"], top["sheetTop"]))
    check("위 줄은 투명 — 모눈이 그대로 비침", top["topBg"] in ("rgba(0, 0, 0, 0)", "transparent"),
          top["topBg"])
    check("‹ 뒤로는 모눈 위에 떠 있음 (화면 위쪽·왼쪽)",
          top["backOverPaper"] and top["backTop"] <= 12 and top["backLeft"] <= 14,
          (top["backTop"], top["backLeft"], top["backOverPaper"]))
    check("모눈 무늬가 종이에 깔려 있음 (22px 격자)",
          "linear-gradient" in top["grid"] and top["gridSize"].startswith("22px"),
          (top["grid"][:40], top["gridSize"]))
    check("글·날짜는 위 줄+도구 줄 아래(머리 높이 108px · v50 두 줄)부터",
          top["nodesTop"] >= 104 and top["dateTop"] >= 104, (top["nodesTop"], top["dateTop"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v50-fullgrid.png"))

    # ==================================================================
    # 3. 글 쓰고 «완료»(blur) — 점선·× 가 사라진 깨끗한 레이아웃
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(460)
    if page.evaluate("() => document.querySelectorAll('#d41Nodes .d41-txt').length") == 0:
        page.locator("#sheet .d41-tool[aria-label='글씨']").click()
        page.wait_for_timeout(460)
    typed = page.evaluate(TYPE)
    check("글 상자에 쓰는 동안은 점선 테두리·× 가 보임 (고른 상자)",
          bool(typed) and typed["sel"] and typed["xShown"] and typed["outlineStyle"] == "dashed"
          and typed["focus"], typed)

    page.evaluate("() => { const ed = document.querySelector('#d41Nodes .d41-txt'); if (ed) ed.blur(); }")
    page.wait_for_timeout(520)
    clean = page.evaluate(CLEAN)
    check("키보드 «완료»(blur)를 누르면 점선 테두리가 사라짐",
          clean["selN"] == 0 and clean["outlineStyle"] != "dashed", clean)
    check("× 삭제 단추도 함께 사라져 다 쓴 레이아웃 그대로",
          clean["xShown"] is False, clean["xShown"])
    check("글은 그대로 남고 저장도 됨 (상자·내용·자동 저장)",
          clean["nBox"] == 1 and clean["hasText"] and "v50 완료" in clean["hidden"]
          and "v50 완료" in clean["savedTexts"], clean)
    page.screenshot(path=os.path.join(SHOT, "diary-v50-cleanblur.png"))

    page.wait_for_timeout(620)
    again = page.evaluate(TAPBOX)
    page.wait_for_timeout(260)
    check("그 상자를 다시 톡 누르면 또 골라짐 (점선·× 돌아옴)",
          bool(again) and again["sel"] == 1 and again["xShown"], again)

    # ==================================================================
    # 4. 펜 모드 — 바탕을 톡 누르면 전체화면 보기, 끌면 그대로 그려짐
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(420)
    before = page.evaluate(PENSTATE)
    check("펜을 고르면 끌어 그릴 수 있는 상태 (도구 줄·도구 판 보임)",
          before["penOn"] and before["editing"] and before["toolsH"] >= 40, before)

    page.evaluate(PEN, [[[210, 430]], 8080])          # 톡 — 움직이지 않음
    page.wait_for_timeout(420)
    tapst = page.evaluate(PENSTATE)
    check("펜 모드에서 바탕을 «톡» 누르면 전체화면 보기로 (도구 줄·판 숨김)",
          (not tapst["editing"]) and tapst["toolsHidden"] and tapst["toolsH"] == 0
          and tapst["panelHidden"] and tapst["view"], tapst)
    check("톡 누른 점은 선이 되지 않음 (그린 획 0개)", tapst["nStroke"] == 0 and tapst["nPath"] == 0, tapst)
    check("보기에서는 펜이 잠겨 화면을 밀어 넘길 수 있음", tapst["penOn"] is False, tapst["penOn"])
    page.screenshot(path=os.path.join(SHOT, "diary-v50-pentap.png"))

    page.locator("#d41Canvas").click(position={"x": 120, "y": 300})
    page.wait_for_timeout(460)
    woke = page.evaluate(PENSTATE)
    check("보기에서 종이를 다시 톡 누르면 도구 줄이 돌아오고 고치기로",
          woke["editing"] and (not woke["toolsHidden"]) and woke["toolsH"] >= 40 and woke["penOn"],
          woke)

    drawn = page.evaluate(PEN, [[[80, 300], [170, 340], [250, 315]], 8080])
    page.wait_for_timeout(420)
    dst = page.evaluate(PENSTATE)
    check("끌면(< 4px 이상) 그대로 선이 그려지고 고치기 상태 유지",
          bool(drawn) and dst["nStroke"] == 1 and dst["nPath"] == 1 and dst["editing"]
          and (not dst["view"]), dst)

    # ==================================================================
    # 5. 저장한 다이어리를 다시 열면 — 보기 화면에서도 위 줄 없이 모눈이 맨 위
    # ==================================================================
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(760)
    check("뒤로 나가면 다이어리 카드가 남음",
          page.evaluate("() => document.querySelectorAll('#s-diary .d41-card').length") >= 1)
    page.locator("#s-diary .d41-card").first.click()
    page.wait_for_timeout(820)
    vtop = page.evaluate(TOP)
    vmode = page.evaluate("""() => {
      const t = document.querySelector('#sheet .d41-tools');
      return {editing: !!document.querySelector('#sheet .d41-txt[contenteditable="true"]'),
        toolsHidden: t ? t.hidden : null,
        view: !!document.querySelector('#sheet .d41-paper.view')};
    }""")
    check("다시 열면 보기(전체화면) — 도구 줄 없음",
          vmode["editing"] is False and vmode["toolsHidden"] and vmode["view"], vmode)
    check("보기 화면도 모눈이 화면 맨 위(0)까지 · «새 다이어리» 글씨 없음",
          vtop["paperTop"] == 0 and vtop["canvasTop"] == 0 and vtop["newDiaryWord"] is False
          and vtop["topText"] == "" and vtop["backOverPaper"], vtop)

    check("브라우저 콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()
    browser.close()

print("")
if fails:
    print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS — v50")
