"""투로그 v50 확인 — 모눈 다이어리 위 줄 «두 줄» 복원 + 사진과 글씨를 바로 밑·옆에 배치.

1) 버전: sw.js 캐시 twolog-v51 · APP_VERSION v51 · My 탭 「버전 v51」
2) 위 줄은 ‹ 뒤로 하나만 (52px) · 도구 줄(↶ ↷ · 펜 · T · 사진)은 그 «아래 줄»(52px 부터,
   ↶ ↷ 왼쪽 · 펜·T·사진 오른쪽) — v50 에서 한 줄로 합쳤던 것을 두 줄로 되돌림
   · ‹ 뒤로 화살표는 v49 의 28px · 획 2.2 그대로
   · 375px 폭에서도 도구 6개가 줄바꿈 없이 한 줄
3) 도구 판(펜 도크 · 글씨 도구)은 도구 줄 바로 아래 — 그리고 판이 열려 있으면 날짜(11.23 MON)가
   그 «아래»로 내려가 가려지지 않음 (v50 에서 날짜를 가리던 문제)
4) 글·사진은 머리 높이 108px 부터 (v49 의 그리기 좌표·지출 제목·사진 병렬 업로드는 그대로)
5) 사진 + 글씨 배치
   · 사진을 붙이면 사진이 골라진 채 — 그 «바로 아래» 빈 종이를 톡 누르면 그 자리에 글 상자가 생김
     (v49 까지는 «고르기만 풀리고» 글 상자가 안 생겼어요)
   · 사진을 고른 채 T 를 누르면 그 사진 «바로 밑»(14px 아래, 같은 x)에 새 글 상자
   · 글 상자를 사진 옆으로 끌어 옮기면 종이 밖으로 나가 잘리지 않고 폭이 줄어 안으로 들어옴
   · 글 상자는 사진보다 위(z) — 사진 위에 겹쳐도 가려지지 않고 그 자리에서 잡힘

    python3 tests/v50.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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

JPG_HEX = ("ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c1912130f141d1a1f1e1d1a1"
           "c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b080001000101011100ffc4001f000001050101010101"
           "01000000000000000102030405060708090a0bffc400b5100002010303020403050504040000017d01020300041105122131410613516107"
           "227114328191a1082342b1c11552d1f02433627282090a161718191a25262728292a3435363738393a434445464748494a535455565758595a63"
           "6465666768696a737475767778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9ca"
           "d2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9")


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
  st.lists = (st.lists || []).concat([
    { id: 'Ld50', title: '그림판', emoji: '', kind: 'memo', items: [] },
    { id: 'Lexp50', title: '테스트지출', emoji: '', kind: 'expense', items: [
      { id: 'e50a', title: '소영 입금', amount: 50000, txType: 'deposit', who: 'me', date: '2026-11-23' },
      { id: 'e50b', title: '데이트', amount: 400000, txType: 'expense', who: 'both', cat: '데이트', date: '2026-11-23' }
    ] }
  ]);
  st.groups = st.groups || {}; st.groups['list:Ld50'] = []; st.groups['list:Lexp50'] = [];
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Ld50' && k !== 'list:Lexp50')
    .concat(['list:Lexp50', 'list:Ld50']);
  st.noteKinds = Object.assign({}, st.noteKinds || {}, { bucket: 'expense' });
  return JSON.stringify(st);
}"""

EXP = """() => {
  const body = document.getElementById('dbody');
  const hd = document.querySelector('#s-diary .note-hd');
  const exp = document.querySelector('#s-diary .exp-page');
  const month = document.querySelector('#s-diary .exp-month');
  const first = body ? body.firstElementChild : null;
  return {
    noteHd: !!hd, noteHdText: hd ? (hd.textContent || '').trim() : '',
    expPage: !!exp, monthTxt: month ? (month.textContent || '').trim() : '',
    firstCls: first ? first.className : '',
    bodyText: body ? (body.innerText || '') : ''
  };
}"""

# 위 줄 · 도구 줄 · 도구 판 · 날짜 자리
LAYOUT = """() => {
  const q = s => document.querySelector('#sheet ' + s);
  const sheet = document.getElementById('sheet');
  const top = q('.d41-top'), tools = q('.d41-tools'), back = q('.d41-back');
  const panel = document.getElementById('d41Panel');
  const nodes = document.getElementById('d41Nodes'), date = q('.d41-date'), paper = document.getElementById('d41Paper');
  const R = e => e ? e.getBoundingClientRect() : null;
  const tr = R(tools), br = R(back), pr = R(panel), nr = R(nodes), dr = R(date), ppr = R(paper), tor = R(top);
  const kids = tools ? [...tools.children].filter(e => R(e).width > 0) : [];
  const btns = kids.filter(e => e.tagName === 'BUTTON');
  const kr = btns.map(e => R(e));
  const svg = back ? back.querySelector('svg') : null;
  const path = svg ? svg.querySelector('path') : null;
  const sb = svg ? getComputedStyle(svg) : null;
  const topKids = top ? [...top.children].filter(e => R(e).width > 0) : [];
  return {
    vw: window.innerWidth,
    sheetTop: Math.round(R(sheet).top),
    paperTop: Math.round(ppr.top),
    topRowTop: Math.round(tor.top), topRowH: Math.round(tor.height),
    topKids: topKids.map(e => e.getAttribute('aria-label') || e.className || e.tagName),
    backTop: Math.round(br.top), backLeft: Math.round(br.left), backRight: Math.round(br.right),
    backBottom: Math.round(br.bottom), backW: Math.round(br.width), backH: Math.round(br.height),
    svgW: sb ? sb.width : '', svgH: sb ? sb.height : '', svgStroke: path ? getComputedStyle(path).strokeWidth : '',
    toolsTop: Math.round(tr.top), toolsLeft: Math.round(tr.left), toolsRight: Math.round(tr.right),
    toolsBottom: Math.round(tr.bottom), toolsH: Math.round(tr.height),
    toolsDisplay: tools ? getComputedStyle(tools).display : '',
    toolsHidden: tools ? tools.hidden : null,
    kidsN: kids.length,
    kidsLabels: kids.map(e => e.getAttribute('aria-label') || e.className),
    kidsCenterSpread: kr.length
      ? Math.round(Math.max(...kr.map(r => (r.top + r.bottom) / 2)) - Math.min(...kr.map(r => (r.top + r.bottom) / 2))) : -1,
    kidWidths: kr.map(r => Math.round(r.width)),
    undoLeft: kr.length ? Math.round(kr[0].left) : -1,
    photoRight: kr.length ? Math.round(kr[kr.length - 1].right) : -1,
    panelTop: pr ? Math.round(pr.top) : -1, panelH: pr ? Math.round(pr.height) : 0,
    panelBottom: pr ? Math.round(pr.bottom) : -1,
    panelHidden: panel ? panel.hidden : null,
    panelDisplay: panel ? getComputedStyle(panel).display : '',
    nodesTop: Math.round(nr.top), dateTop: Math.round(dr.top), headH: nodes.offsetTop,
    dateBottomOfPanel: pr ? Math.round(dr.top) - Math.round(pr.bottom) : -999
  };
}"""

PANEL = """() => {
  const p = document.getElementById('d41Panel');
  const r = p.getBoundingClientRect();
  return {hidden: p.hidden, top: Math.round(r.top), h: Math.round(r.height), bottom: Math.round(r.bottom),
    display: getComputedStyle(p).display};
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
  const nodes = document.getElementById('d41Nodes');
  return {d: live ? live.getAttribute('d') : '', T: nodes.offsetTop};
}"""

PEN_UP = """(pid) => {
  const svg = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const last = svg.__lastPt || [0, 0];
  svg.dispatchEvent(new PointerEvent('pointerup', {pointerId: pid, pointerType: 'touch', isPrimary: true,
    clientX: r.left + last[0], clientY: r.top + last[1], bubbles: true, cancelable: true}));
  const paths = [...svg.querySelectorAll('path')];
  const lastPath = paths[paths.length - 1];
  return {nPath: paths.length, d: lastPath ? lastPath.getAttribute('d') : '',
    nStroke: JSON.parse((document.getElementById('d41PenIn') || {}).value || '[]').length};
}"""

PEN_TAP = """([x, y, pid]) => {
  const svg = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const mk = t => new PointerEvent(t, {pointerId: pid, pointerType: 'touch', isPrimary: true,
    clientX: r.left + x, clientY: r.top + y, bubbles: true, cancelable: true});
  svg.dispatchEvent(mk('pointerdown'));
  svg.dispatchEvent(mk('pointerup'));
  const tools = document.querySelector('#sheet .d41-tools');
  const panel = document.getElementById('d41Panel');
  const back = document.querySelector('#sheet .d41-back');
  const date = document.querySelector('#sheet .d41-date');
  return {view: paper.classList.contains('view'),
    toolsHidden: tools.hidden, toolsDisplay: getComputedStyle(tools).display,
    panelHidden: panel.hidden, panelDisplay: getComputedStyle(panel).display,
    dateTop: date ? Math.round(date.getBoundingClientRect().top) : -1,
    backShown: !!back && getComputedStyle(back).display !== 'none' && back.getBoundingClientRect().width > 0};
}"""

# 사진·글 상자 자리와 z
NODES = """() => {
  const paper = document.getElementById('d41Paper').getBoundingClientRect();
  const R = e => { const r = e.getBoundingClientRect();
    return {l: Math.round(r.left), t: Math.round(r.top), r: Math.round(r.right), b: Math.round(r.bottom),
            w: Math.round(r.width), h: Math.round(r.height), z: getComputedStyle(e).zIndex}; };
  const imgs = [...document.querySelectorAll('#sheet .d41-imgb')].map(e => Object.assign(R(e),
    {sel: e.classList.contains('sel'), id: e.getAttribute('data-img')}));
  const txs = [...document.querySelectorAll('#sheet .d41-tx')].map(e => { const inner = e.querySelector('.d41-txt'); return Object.assign(R(e),
    {sel: e.classList.contains('sel'), id: e.getAttribute('data-tx'),
     txt: (e.innerText || '').trim(), clipped: !!inner && inner.scrollWidth > inner.clientWidth + 1,
     maxW: e.style.maxWidth}); });
  return {paper: {l: Math.round(paper.left), r: Math.round(paper.right), w: Math.round(paper.width)},
    imgs: imgs, txs: txs,
    texts: JSON.parse((document.getElementById('d41TextsIn') || {}).value || '[]'),
    im: JSON.parse((document.getElementById('d41ImgsIn') || {}).value || '[]'),
    focused: (document.activeElement || {}).className || ''};
}"""

# 그 자리에서 무엇이 잡히는지 (글 상자가 사진 위에 있는지)
HIT = """([x, y]) => {
  const el = document.elementFromPoint(x, y);
  if (!el) return 'none';
  if (el.closest('.d41-tx')) return 'tx';
  if (el.closest('.d41-imgb')) return 'img';
  if (el.closest('.d41-txx')) return 'txx';
  return (el.className || el.tagName || '').toString();
}"""


def pairs(d):
    return [(float(a), float(b)) for a, b in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", d or "")]


def add_photo(page, path):
    page.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    page.wait_for_timeout(220)
    page.set_input_files("#d41ImgIn", [path])
    page.wait_for_timeout(1300)


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전 · 지출 제목( v49 ) · 두 줄 툴바
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    watch(page, errs)

    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    css = page.request.get(URL + "styles.css").text()
    check('sw.js 캐시 버전 twolog-v51', 'const VERSION = "twolog-v51"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v51", 'var APP_VERSION = "v51"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v49 문자열이 남아 있지 않음",
          "twolog-v49" not in sw and 'APP_VERSION = "v49"' not in app_js)

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", page.evaluate(SEED_JS))
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 4, 620)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v51」", ver.strip() == "버전 v51", ver)

    # 지출·정산 — «‹ 11월 ›» 위 카테고리 제목 줄 없음 (v50 그대로)
    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="테스트지출").first.click()
    page.wait_for_timeout(560)
    exp1 = page.evaluate(EXP)
    check("지출·정산 화면에 카테고리 제목 줄(.note-hd)이 없음 (v50 그대로)",
          exp1["noteHd"] is False, exp1["noteHdText"])
    check("«‹ 11월 ›» 머리가 맨 위 — 함께 쓰는 돈 화면",
          exp1["expPage"] and "11월" in exp1["monthTxt"]
          and str(exp1["firstCls"]).split(" ")[0] == "exp-page",
          (exp1["expPage"], exp1["monthTxt"], exp1["firstCls"]))

    page.locator("#s-diary .lchip", has_text="그림판").first.click()
    page.wait_for_timeout(560)
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(820)

    lay = page.evaluate(LAYOUT)
    check("‹ 뒤로 화살표 28px · 획 2.2 (v50 그대로)",
          lay["svgW"] == "28px" and lay["svgH"] == "28px" and lay["svgStroke"] in ("2.2", "2.2px"),
          (lay["svgW"], lay["svgH"], lay["svgStroke"]))
    check("‹ 뒤로 단추는 44px 그대로", lay["backW"] == 44 and lay["backH"] == 44, (lay["backW"], lay["backH"]))
    check("위 줄은 ‹ 뒤로 «하나만» (새 다이어리 글씨·도구 없음)",
          lay["topKids"] == ["뒤로"] and lay["topRowH"] == 52, (lay["topKids"], lay["topRowH"]))
    check("도구 줄은 위 줄 «아래» 줄 — 위 52px, ‹ 뒤로와 겹치지 않음",
          lay["toolsTop"] == 52 and lay["toolsTop"] >= lay["topRowTop"] + lay["topRowH"] - 1
          and lay["toolsLeft"] <= 2,
          (lay["toolsTop"], lay["topRowTop"], lay["topRowH"], lay["toolsLeft"]))
    check("도구 6개(↶ ↷ · 펜 · T · 사진)가 한 줄 — 줄바꿈 없음",
          lay["kidsN"] == 6 and lay["kidsCenterSpread"] <= 1
          and lay["kidsLabels"] == ["되돌리기", "다시 실행", "d41-tools-gap", "펜 그리기", "글씨", "사진 넣기"],
          (lay["kidsN"], lay["kidsCenterSpread"], lay["kidsLabels"]))
    check("↶ ↷ 는 도구 줄 왼쪽 끝 (왼쪽 여백 20px 안)",
          lay["undoLeft"] <= 20 and lay["undoLeft"] >= 0, lay["undoLeft"])
    check("펜·T·사진은 도구 줄 오른쪽 끝 (오른쪽 여백 20px 안)",
          lay["vw"] - lay["photoRight"] <= 20, (lay["photoRight"], lay["vw"]))
    check("도구 단추는 줄지 않음 (44·44·46·46·46px)",
          lay["kidWidths"] == [44, 44, 46, 46, 46], lay["kidWidths"])
    check("글·사진은 머리 높이 108px 부터 (두 줄 아래)",
          lay["headH"] == 108 and lay["nodesTop"] == 108 and lay["dateTop"] == 108,
          (lay["headH"], lay["nodesTop"], lay["dateTop"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v50-toolbar.png"))

    # ==================================================================
    # 2. 도구 판 — 도구 줄 바로 아래 · 날짜를 가리지 않음
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(520)
    pen = page.evaluate(PANEL)
    lay2 = page.evaluate(LAYOUT)
    check("펜 도크 판이 도구 줄 바로 아래(108px)에 뜸",
          (not pen["hidden"]) and pen["display"] != "none" and pen["top"] == 108 and lay2["toolsBottom"] <= pen["top"],
          (pen, lay2["toolsBottom"]))
    check("판이 열리면 날짜(11.23 MON)가 판 «아래»로 내려가 가려지지 않음",
          lay2["dateTop"] >= pen["bottom"] - 1 and lay2["dateBottomOfPanel"] >= -1,
          (lay2["dateTop"], pen["bottom"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v50-pen-panel-date.png"))

    # 도구 판을 닫으면 날짜는 다시 머리 높이로
    page.locator("#d41Canvas").click(position={"x": 200, "y": 700})
    page.wait_for_timeout(520)
    lay3 = page.evaluate(LAYOUT)
    check("판을 닫으면 날짜는 다시 108px 자리로", lay3["dateTop"] == 108, lay3["dateTop"])
    page.locator("#d41Canvas").click(position={"x": 200, "y": 700})
    page.wait_for_timeout(360)

    # ==================================================================
    # 3. 그리기 좌표 (v49 고침 그대로) — 머리 108px
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(460)
    pts = [[80, 320], [170, 360], [250, 335]]
    live = page.evaluate(PEN_LIVE, [pts, 8181])
    T = live["T"]
    lp = pairs(live["d"])
    yerr = [round((lp[i][1] if i < len(lp) else -999) - pts[i][1], 1) for i in range(len(pts))]
    check("머리 높이(d41Top) 108px — 두 줄", T == 108, T)
    check("그리는 «도중» 선이 손가락 y 그대로 (±1.5px)",
          live["d"].startswith("M") and len(lp) == len(pts) and all(abs(e) <= 1.5 for e in yerr),
          (live["d"][:40], yerr))
    page.evaluate("([pts]) => { document.getElementById('d41Pen').__lastPt = pts[pts.length - 1]; }", [pts])
    up = page.evaluate(PEN_UP, 8181)
    fp = pairs(up["d"])
    jump = max(abs(a[1] - b[1]) for a, b in zip(lp, fp)) if lp and fp else 999
    check("손을 떼도 선이 튀지 않음 (그리던 자리 = 다 그린 자리)",
          up["nStroke"] == 1 and jump <= 1.5, (up["nStroke"], jump))

    # ==================================================================
    # 4. 보기 모드 — 도구 줄·도구 판 숨고 ‹ 만, 날짜는 제자리
    # ==================================================================
    vt = page.evaluate(PEN_TAP, [120, 520, 9191])
    page.wait_for_timeout(460)
    check("보기로 가면 도구 줄·도구 판이 숨고 ‹ 뒤로만 남음",
          vt["view"] and vt["toolsHidden"] and vt["toolsDisplay"] == "none"
          and vt["panelHidden"] and vt["panelDisplay"] == "none" and vt["backShown"], vt)
    vlay = page.evaluate(LAYOUT)
    check("보기에서 날짜는 머리 높이(108px) 자리로 돌아옴 — 판이 닫히니",
          vlay["dateTop"] == 108 and vlay["headH"] == 108, (vlay["dateTop"], vlay["headH"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v50-view.png"))
    page.locator("#d41Canvas").click(position={"x": 120, "y": 520})
    page.wait_for_timeout(460)

    # ==================================================================
    # 5. 375px 폭에서도 두 줄 · 도구 한 줄
    # ==================================================================
    page.set_viewport_size({"width": 375, "height": 812})
    page.wait_for_timeout(520)
    n375 = page.evaluate(LAYOUT)
    check("375px 폭에서도 위 줄(‹) 따로 · 도구 줄 따로 (52px)",
          n375["topRowH"] == 52 and n375["toolsTop"] == 52, (n375["topRowH"], n375["toolsTop"]))
    check("375px 폭에서도 도구 6개가 한 줄 — 넘치지 않음",
          n375["toolsDisplay"] != "none" and n375["kidsN"] == 6 and n375["kidsCenterSpread"] <= 1
          and n375["toolsRight"] <= n375["vw"],
          (n375["kidsN"], n375["kidsCenterSpread"], n375["toolsRight"], n375["vw"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v50-toolbar-375.png"))
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(420)
    check("브라우저 콘솔/페이지 오류 없음 (툴바)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 6. 사진 + 글씨 — 사진 바로 밑·옆에 배치
    # ==================================================================
    ctxp = new_ctx(browser)
    ctxp.add_init_script("window.__TWOLOG_MODE = 'local';")
    pp = ctxp.new_page()
    errsp = []
    watch(pp, errsp)
    pp.goto(URL + "?demo=1", wait_until="networkidle")
    pp.wait_for_timeout(700)
    pp.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", pp.evaluate(SEED_JS))
    pp.goto(URL, wait_until="networkidle")
    pp.wait_for_timeout(900)
    tab(pp, 2, 700)
    pp.locator("#s-diary .lchip", has_text="그림판").first.click()
    pp.wait_for_timeout(560)
    pp.locator("#s-diary .d41-new").click()
    pp.wait_for_timeout(820)

    durl = pp.evaluate("""() => { const c = document.createElement('canvas'); c.width = 400; c.height = 300;
      const x = c.getContext('2d'); x.fillStyle = '#E8C9C1'; x.fillRect(0, 0, 400, 300);
      x.fillStyle = '#3D6E8A'; x.fillRect(40, 40, 320, 220); return c.toDataURL('image/jpeg', 0.9); }""")
    with open("/tmp/v50-photo.jpg", "wb") as f:
        f.write(_b64.b64decode(durl.split(",", 1)[1]))
    add_photo(pp, "/tmp/v50-photo.jpg")
    g1 = pp.evaluate(NODES)
    check("사진을 붙이면 종이 위 사진 상자 (자리·폭과 함께)",
          len(g1["imgs"]) == 1 and 0 <= g1["im"][0]["x"] <= 1 and 0 <= g1["im"][0]["w"] <= 1,
          g1["im"][0] if g1["im"] else "")

    # 사진을 톡 눌러 고른 «그 상태에서» 사진 바로 아래 빈 종이를 톡
    img = g1["imgs"][0]
    pp.mouse.click(img["l"] + 40, img["t"] + 40)
    pp.wait_for_timeout(460)
    gsel = pp.evaluate(NODES)
    check("사진을 톡 누르면 골라짐 (자르기·삭제 판)",
          gsel["imgs"][0]["sel"] and pp.evaluate("!document.getElementById('d41Panel').hidden"),
          gsel["imgs"][0])

    # (a) 사진이 고른 채인 그 상태에서 사진 «바로 아래» 빈 종이를 톡 → 그 자리에 글 상자
    #     (v49 까지는 «고르기만 풀리고» 글 상자가 안 생겼어요)
    tap_y = img["b"] + 28
    pp.mouse.click(img["l"] + 40, tap_y)
    pp.wait_for_timeout(520)
    g2 = pp.evaluate(NODES)
    near_below = [t for t in g2["txs"] if abs(t["t"] - (tap_y - 12)) <= 22 and abs(t["l"] - img["l"] - 40) <= 24]
    check("사진을 고른 채 사진 «바로 아래»를 톡 누르면 그 자리에 글 상자",
          len(g2["txs"]) == 1 and len(near_below) == 1,
          [(t["l"], t["t"]) for t in g2["txs"]])
    check("새 글 상자가 바로 입력 상태 (점선·커서)",
          "d41-txt" in (g2["focused"] or "") and g2["txs"] and g2["txs"][0]["sel"],
          (g2["focused"], g2["txs"][0]["sel"] if g2["txs"] else None))
    pp.keyboard.type("사진 바로 밑에 쓴 글씨")
    pp.wait_for_timeout(320)
    pp.locator("#d41Canvas").click(position={"x": 330, "y": 760})
    pp.wait_for_timeout(520)
    g3 = pp.evaluate(NODES)
    check("쓴 글이 사진 밑에 그대로 저장 (자리·글)",
          len(g3["txs"]) == 1 and g3["txs"][0]["txt"] == "사진 바로 밑에 쓴 글씨"
          and g3["texts"][0]["text"] == "사진 바로 밑에 쓴 글씨"
          and g3["txs"][0]["t"] >= img["b"] - 2,
          (g3["txs"][0]["txt"] if g3["txs"] else "", g3["texts"]))
    page_path = os.path.join(SHOT, "diary-v50-photo-text.png")
    pp.screenshot(path=page_path)
    # (b) 사진을 고른 채 T → 사진 «바로 밑»(14px) · 같은 x 에 새 글 상자
    pp.mouse.click(g3["imgs"][0]["l"] + 40, g3["imgs"][0]["t"] + 40)
    pp.wait_for_timeout(420)
    sel_img = pp.evaluate(NODES)
    check("사진을 톡 누르면 골라짐 (자르기·삭제 판)", sel_img["imgs"][0]["sel"], sel_img["imgs"][0])
    pp.locator("#sheet .d41-tool[aria-label='글씨']").click()
    pp.wait_for_timeout(520)
    g4 = pp.evaluate(NODES)
    fresh = [t for t in g4["txs"] if not t["txt"]]
    check("사진을 고른 채 T 를 누르면 사진 «바로 밑»에 새 글 상자",
          len(fresh) == 1 and abs(fresh[0]["t"] - (sel_img["imgs"][0]["b"] + 14)) <= 6
          and abs(fresh[0]["l"] - sel_img["imgs"][0]["l"]) <= 2,
          [(t["l"], t["t"]) for t in fresh] + [("photo bottom", sel_img["imgs"][0]["b"])])
    pp.keyboard.type("T 로 만든 글")
    pp.wait_for_timeout(300)
    pp.locator("#d41Canvas").click(position={"x": 330, "y": 780})
    pp.wait_for_timeout(500)

    # 그 상자는 지워 두고 (사진 + 밑 글씨 한 개만 남겨요)
    g5 = pp.evaluate(NODES)
    tnew = [t for t in g5["txs"] if t["txt"] == "T 로 만든 글"]
    if tnew:
        pp.mouse.click(tnew[0]["l"] + 20, tnew[0]["t"] + 12)
        pp.wait_for_timeout(320)
        pp.locator("#sheet .d41-tx.sel .d41-txx").first.click()
        pp.wait_for_timeout(420)
    check("글 상자 × 로 지우면 사진·다른 글이 남음",
          len(pp.evaluate(NODES)["txs"]) == 1, len(pp.evaluate(NODES)["txs"]))

    # (c) 글 상자를 사진 «옆»(오른쪽)으로 끌기 — 종이 밖으로 나가 잘리지 않음
    g6 = pp.evaluate(NODES)
    tx, im = g6["txs"][0], g6["imgs"][0]
    pp.mouse.move(tx["l"] + 24, tx["t"] + 12)
    pp.mouse.down()
    pp.mouse.move(im["r"] + 28, im["t"] + 40, steps=14)
    pp.mouse.up()
    pp.wait_for_timeout(520)
    g7 = pp.evaluate(NODES)
    tx7 = g7["txs"][0]
    check("글 상자를 사진 «옆»으로 끌어 옮김 (x 가 오른쪽으로)",
          tx7["l"] > tx["l"] + 60, (tx["l"], tx7["l"]))
    check("옆으로 옮긴 글 상자가 종이 밖으로 나가 잘리지 않음",
          tx7["r"] <= g7["paper"]["r"] - 1 and not tx7["clipped"] and tx7["w"] >= 40,
          (tx7["r"], g7["paper"]["r"], tx7["clipped"], tx7["w"], tx7["maxW"]))
    pp.screenshot(path=os.path.join(SHOT, "diary-v50-photo-text-side.png"))

    # (d) 글 상자를 사진 «위»로 끌어도 사진에 가려지지 않음 (z)
    pp.mouse.move(tx7["l"] + 20, tx7["t"] + 12)
    pp.mouse.down()
    pp.mouse.move(im["l"] + 70, im["t"] + 70, steps=14)
    pp.mouse.up()
    pp.wait_for_timeout(520)
    g8 = pp.evaluate(NODES)
    tx8 = g8["txs"][0]
    zimg = int(g8["imgs"][0]["z"] or 0)
    ztx = int(tx8["z"] or 0)
    hit = pp.evaluate(HIT, [tx8["l"] + 16, tx8["t"] + 10])
    check("글 상자는 사진보다 위 (z)", ztx > zimg, (ztx, zimg))
    check("사진 위에 겹쳐도 글 상자가 잡히고 보임 (가려지지 않음)", hit == "tx", hit)
    check("겹친 글씨도 잘리지 않음", not tx8["clipped"], (tx8["clipped"], tx8["maxW"]))
    pp.screenshot(path=os.path.join(SHOT, "diary-v50-photo-text-overlap.png"))
    check("사진·글씨 배치 중 콘솔/페이지 오류 없음", len(errsp) == 0, errsp[:4])
    ctxp.close()

    # ==================================================================
    # 7. 사진 여러 장 담기 (v50 그대로 — 3장씩 나란히 · 순서 · 진행 막대)
    # ==================================================================
    ctxr = new_ctx(browser)
    ctxr.add_init_script("window.__TWOLOG_MODE = 'local';")
    rp = ctxr.new_page()
    errsr = []
    watch(rp, errsr)
    rp.goto(URL, wait_until="domcontentloaded")
    rp.wait_for_selector("#tabbar .tab", timeout=25000)
    rp.wait_for_timeout(900)
    tab(rp, 3, 680)
    shots = []
    for nm in ["v50a", "v50b", "v50c", "v50d"]:
        sp = "/tmp/v50-%s.jpg" % nm
        with open(sp, "wb") as f:
            f.write(bytes.fromhex(JPG_HEX))
        shots.append(sp)
    rp.set_input_files("#photoInput", shots)
    rp.wait_for_timeout(700)
    upn = rp.evaluate("""() => ({rows: document.querySelectorAll('#sheet .up-grid .up-cell').length,
      btn: (document.querySelector('#upBtn') || {}).textContent || ''})""")
    check("4장을 고르면 「사진 추가」 시트에 4장", upn["rows"] == 4 and upn["btn"].startswith("4장"), upn)
    rp.evaluate("""() => {
      window.__bar = [];
      const el = document.querySelector('#upBar i');
      if (!el) return;
      window.__bar.push(el.style.width || '0%');
      new MutationObserver(() => window.__bar.push(el.style.width || '0%'))
        .observe(el, {attributes: true, attributeFilter: ['style']});
    }""")
    t0 = time.time()
    rp.locator("#sheet #upBtn").click()
    for _ in range(200):
        rp.wait_for_timeout(50)
        if rp.evaluate("() => (window.__app.state.photos || []).length") >= 4:
            break
    elapsed = time.time() - t0
    rp.wait_for_timeout(900)
    savedr = rp.evaluate("""() => ({titles: (window.__app.state.photos || []).map(p => p.title),
      n: (window.__app.state.photos || []).length,
      ls: JSON.parse(localStorage.getItem('twolog:v1:state') || '{}').photos || [],
      bar: window.__bar || []})""")
    check("4장 모두 끝까지 담김 (앱을 닫아도 남게 저장)", savedr["n"] == 4 and len(savedr["ls"]) == 4,
          (savedr["n"], len(savedr["ls"])))
    check("고른 순서 그대로 저장 — 1번째 사진이 맨 앞",
          savedr["titles"] == ["v50-v50a", "v50-v50b", "v50-v50c", "v50-v50d"], savedr["titles"])
    check("사진 4장을 몇 초 안에 (병렬 업로드 그대로)", elapsed < 6.0, round(elapsed, 2))
    steps = []
    for b in savedr["bar"]:
        if b and (not steps or steps[-1] != b):
            steps.append(b)
    check("진행 막대가 장마다 올라가 100%까지",
          steps[-1:] == ["100%"] and len(steps) >= 4
          and [int(x.replace("%", "")) for x in steps] == sorted(int(x.replace("%", "")) for x in steps),
          steps)
    check("사진 담기 콘솔/페이지 오류 없음", len(errsr) == 0, errsr[:4])
    ctxr.close()
    browser.close()

print("")
if fails:
    print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS — v50")
