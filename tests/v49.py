"""투로그 v49 확인 — 모눈 다이어리 위 줄 정리 + 그리기 좌표.

1) 버전: sw.js 캐시 twolog-v49 · APP_VERSION v49 · My 탭 「버전 v49」
2) ‹ 뒤로 화살표를 크게 (22 → 28px, 획 2.2)
3) 도구 줄(↶ ↷ · 펜 · T · 사진)이 ‹ 뒤로와 «같은 줄»로 한 단계 위로 —
   375·390 폭에서 겹치거나 줄바꿈 없이 한 줄, 뒤로 단추와 나란히
4) 도구 판(펜 도크 · 글씨 도구)이 도구 줄 바로 아래(한 단계 위, 56px)에 뜸
   글·날짜도 그 높이(머리 56px)부터 시작
5) 보기 모드에서는 도구 줄·도구 판이 숨고 ‹ 뒤로만 남음
6) 그리는 «도중»에도 선이 손가락 자리에 그려짐 (v48은 머리 높이만큼 위에 그려졌어요)
7) 지출·정산 화면 — «‹ 11월 ›» 위에 한 번 더 보이던 카테고리 제목 줄(.note-hd)을 없앰
   (내 카테고리·기본 카테고리 둘 다 / 다른 속지의 제목 줄은 그대로)
8) 사진 여러 장 담기 — 3장씩 나란히(압축 1200px·품질 0.78, 서명 URL 왕복 없음, 실패 시 1회 재시도)로
   빨라지고, 3장 이상도 고른 순서 그대로 끝까지 저장 · 진행 막대는 장마다 올라감

    python3 tests/v49.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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

# 테스트용 1x1 JPEG (v40 과 같은 것)
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
    { id: 'Ld49', title: '그림판', emoji: '', kind: 'memo', items: [] },
    { id: 'Lexp49', title: '테스트지출', emoji: '', kind: 'expense', items: [
      { id: 'e49a', title: '소영 입금', amount: 50000, txType: 'deposit', who: 'me', date: '2026-11-23' },
      { id: 'e49b', title: '데이트', amount: 400000, txType: 'expense', who: 'both', cat: '데이트', date: '2026-11-23' }
    ] }
  ]);
  st.groups = st.groups || {}; st.groups['list:Ld49'] = []; st.groups['list:Lexp49'] = [];
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Ld49' && k !== 'list:Lexp49')
    .concat(['list:Lexp49', 'list:Ld49']);
  /* 기본 카테고리 » 지출·정산 속지 (viewBasePage 길도 함께 봐요) */
  st.noteKinds = Object.assign({}, st.noteKinds || {}, { bucket: 'expense' });
  return JSON.stringify(st);
}"""

# 지출·정산 화면 머리 — 카테고리 제목 줄(.note-hd)이 없고 «‹ 11월 ›» 부터
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
    bodyText: body ? (body.innerText || '') : '',
    chipActive: (document.querySelector('#s-diary .lchip.active') || {}).textContent || ''
  };
}"""

# 다른 속지(모눈 메모)는 제목 줄이 그대로
MEMO_HEAD = """() => {
  const hd = document.querySelector('#s-diary .note-hd');
  return {noteHd: !!hd, txt: hd ? (hd.textContent || '').trim() : '',
    listView: !!document.querySelector('#s-diary .d41-list')};
}"""

# 위 줄·도구 줄·도구 판 위치, ‹ 뒤로 화살표 크기
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
  return {
    vw: window.innerWidth,
    sheetTop: Math.round(R(sheet).top),
    paperTop: Math.round(ppr.top),
    topRowTop: Math.round(tor.top), topRowH: Math.round(tor.height),
    backTop: Math.round(br.top), backLeft: Math.round(br.left), backRight: Math.round(br.right),
    backBottom: Math.round(br.bottom), backW: Math.round(br.width), backH: Math.round(br.height),
    svgW: sb ? sb.width : '', svgH: sb ? sb.height : '',
    svgStroke: path ? getComputedStyle(path).strokeWidth : '',
    toolsTop: Math.round(tr.top), toolsLeft: Math.round(tr.left), toolsRight: Math.round(tr.right),
    toolsBottom: Math.round(tr.bottom), toolsH: Math.round(tr.height),
    toolsDisplay: tools ? getComputedStyle(tools).display : '',
    toolsHidden: tools ? tools.hidden : null,
    kidsN: kids.length,
    kidsLabels: kids.map(e => e.getAttribute('aria-label') || e.className),
    kidsTopSpread: kr.length ? Math.round(Math.max(...kr.map(r => r.top)) - Math.min(...kr.map(r => r.top))) : -1,
    kidsCenterSpread: kr.length
      ? Math.round(Math.max(...kr.map(r => (r.top + r.bottom) / 2)) - Math.min(...kr.map(r => (r.top + r.bottom) / 2))) : -1,
    kidsBottomMax: kr.length ? Math.round(Math.max(...kr.map(r => r.bottom))) : -1,
    kidWidths: kr.map(r => Math.round(r.width)),
    panelTop: pr ? Math.round(pr.top) : -1, panelH: pr ? Math.round(pr.height) : 0,
    panelHidden: panel ? panel.hidden : null,
    panelDisplay: panel ? getComputedStyle(panel).display : '',
    nodesTop: Math.round(nr.top), dateTop: Math.round(dr.top), headH: nodes.offsetTop
  };
}"""

# 글씨 도구 판도 같은 자리에 뜨는지
PANEL = """() => {
  const p = document.getElementById('d41Panel');
  const r = p.getBoundingClientRect();
  const rows = [...p.querySelectorAll('.d41-prow')].map(e => Math.round(e.getBoundingClientRect().top));
  return {hidden: p.hidden, top: Math.round(r.top), h: Math.round(r.height), rows: rows,
    display: getComputedStyle(p).display};
}"""

# 펜 — pointerdown + pointermove 까지만 (그리는 «도중»의 선을 봐요)
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
  const ppr = paper.getBoundingClientRect();
  return {d: live ? live.getAttribute('d') : '', T: nodes.offsetTop,
    paperTop: Math.round(ppr.top), paperLeft: Math.round(ppr.left),
    svgTop: Math.round(svg.getBoundingClientRect().top),
    W: Math.round(paper.clientWidth)};
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

# 펜 — 톡 (움직임 0) 으로 보기(전체화면) 전환
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
  return {view: paper.classList.contains('view'),
    toolsHidden: tools.hidden, toolsDisplay: getComputedStyle(tools).display,
    panelHidden: panel.hidden, panelDisplay: getComputedStyle(panel).display,
    backShown: !!back && getComputedStyle(back).display !== 'none' && back.getBoundingClientRect().width > 0};
}"""


def pairs(d):
    return [(float(a), float(b)) for a, b in re.findall(r"[ML](-?[\d.]+) (-?[\d.]+)", d or "")]


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
    css = page.request.get(URL + "styles.css").text()
    check('sw.js 캐시 버전 twolog-v49', 'const VERSION = "twolog-v49"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v49", 'var APP_VERSION = "v49"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v48 문자열이 남아 있지 않음",
          "twolog-v48" not in sw and 'APP_VERSION = "v48"' not in app_js)

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed = page.evaluate(SEED_JS)
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 4, 620)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v49」", ver.strip() == "버전 v49", ver)

    # ==================================================================
    # 2. 지출·정산 — «‹ 11월 ›» 위의 메모 타이틀(카테고리 이름) 없앰
    # ==================================================================
    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="테스트지출").first.click()
    page.wait_for_timeout(560)
    exp1 = page.evaluate(EXP)
    check("지출·정산 화면에 카테고리 제목 줄(.note-hd)이 없음",
          exp1["noteHd"] is False, exp1["noteHdText"])
    check("«‹ 11월 ›» 머리가 맨 위 — 함께 쓰는 돈 화면",
          exp1["expPage"] and "11월" in exp1["monthTxt"]
          and str(exp1["firstCls"]).split(" ")[0] == "exp-page",
          (exp1["expPage"], exp1["monthTxt"], exp1["firstCls"]))
    check("화면 안에 카테고리 이름이 제목으로 한 번 더 나오지 않음",
          "테스트지출" not in exp1["bodyText"], exp1["bodyText"][:60])
    page.screenshot(path=os.path.join(SHOT, "expense-v49-no-title.png"))

    page.locator("#s-diary .seg-btn", has_text="버킷리스트").first.click()
    page.wait_for_timeout(520)
    exp2 = page.evaluate(EXP)
    check("기본 카테고리에 고른 지출·정산 속지도 제목 줄 없이 월 머리부터",
          exp2["noteHd"] is False and exp2["expPage"] and "11월" in exp2["monthTxt"],
          (exp2["noteHd"], exp2["noteHdText"], exp2["monthTxt"]))

    # ==================================================================
    # 3. 새 다이어리 — 위 줄 하나로 (‹ 뒤로 오른쪽에 도구 줄)
    # ==================================================================
    page.locator("#s-diary .lchip", has_text="그림판").first.click()
    page.wait_for_timeout(560)
    mh = page.evaluate(MEMO_HEAD)
    check("다른 속지(모눈 메모)는 제목 줄이 그대로 있음 (지출만 없앰)",
          mh["noteHd"] and mh["txt"] == "그림판" and mh["listView"], mh)
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(820)

    lay = page.evaluate(LAYOUT)
    check("‹ 뒤로 화살표 28px (22 → 28) · 획 2.2",
          lay["svgW"] == "28px" and lay["svgH"] == "28px" and lay["svgStroke"] in ("2.2", "2.2px"),
          (lay["svgW"], lay["svgH"], lay["svgStroke"]))
    check("‹ 뒤로 단추 자체는 44px 그대로 (누르기 편하게)",
          lay["backW"] == 44 and lay["backH"] == 44, (lay["backW"], lay["backH"]))
    check("도구 줄이 ‹ 뒤로와 «같은 줄» (위 4px)",
          abs(lay["toolsTop"] - lay["backTop"]) <= 1 and lay["toolsTop"] <= 6,
          (lay["toolsTop"], lay["backTop"]))
    check("도구 줄은 ‹ 뒤로 오른쪽에서 시작 — 겹치지 않음",
          lay["backRight"] <= lay["toolsLeft"] + 1 and lay["toolsLeft"] <= 60,
          (lay["backRight"], lay["toolsLeft"]))
    check("도구 6개(↶ ↷ · 펜 · T · 사진)가 한 줄 — 줄바꿈 없음",
          lay["kidsN"] == 6 and lay["kidsCenterSpread"] <= 1
          and lay["kidsLabels"] == ["되돌리기", "다시 실행", "d41-tools-gap", "펜 그리기", "글씨", "사진 넣기"],
          (lay["kidsN"], lay["kidsCenterSpread"], lay["kidsLabels"]))
    check("도구 줄이 ‹ 뒤로와 같은 높이에 나란히 (가운데 높이 ±1px)",
          abs((lay["toolsTop"] + lay["toolsBottom"]) / 2 - (lay["backTop"] + lay["backBottom"]) / 2) <= 1,
          (lay["toolsTop"], lay["toolsBottom"], lay["backTop"], lay["backBottom"]))
    check("도구 줄이 화면 폭 안에 들어옴 (390px)",
          lay["toolsRight"] <= lay["vw"] and lay["kidsBottomMax"] <= lay["backBottom"] + 1,
          (lay["toolsRight"], lay["vw"], lay["kidsBottomMax"], lay["backBottom"]))
    check("되돌리기·다시 실행 44px · 펜·T·사진 46px 그대로 (눌러도 줄지 않음)",
          lay["kidWidths"] == [44, 44, 46, 46, 46], lay["kidWidths"])
    check("위 줄 전체가 한 단계 위 — 도구 줄이 예전 52px 자리에서 4px 로",
          lay["topRowTop"] == 0 and lay["topRowH"] == 52, (lay["topRowTop"], lay["topRowH"]))
    check("글·날짜도 한 단계 위(머리 56px)부터",
          lay["headH"] == 56 and lay["nodesTop"] == 56 and lay["dateTop"] == 56,
          (lay["headH"], lay["nodesTop"], lay["dateTop"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v49-toolbar.png"))

    # ==================================================================
    # 4. 도구 판(펜 도크) — 도구 줄 바로 아래, 한 단계 위 자리
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(460)
    pen = page.evaluate(PANEL)
    check("펜 도크 판이 도구 줄 바로 아래(56px)에 뜸 — 예전 108px 아님",
          (not pen["hidden"]) and pen["display"] != "none" and pen["top"] == 56 and lay["toolsBottom"] <= pen["top"],
          (pen, lay["toolsBottom"]))
    check("펜 도크 판이 한 줄(가는 펜·일반 펜·형광펜·지우개·색·전체 지우기)",
          pen["h"] <= 70, (pen["h"], pen["rows"]))

    # ==================================================================
    # 5. 그리는 «도중»에도 선이 손가락 자리에 — v48 좌표 어긋남 고침
    # ==================================================================
    pts = [[80, 300], [170, 340], [250, 315]]
    page.evaluate("(p) => { window.__pts = p; }", pts)
    live = page.evaluate(PEN_LIVE, [pts, 8080])
    check("그리는 도중 선이 생김 (손 떼기 전)", live["d"].startswith("M"), live["d"][:60])
    T = live["T"]
    check("머리 높이(d41Top) 56px — 예전엔 이만큼 위에 그려졌어요", T == 56, T)
    lp = pairs(live["d"])
    check("그리는 도중 선의 점 개수가 손가락 점 개수와 같음", len(lp) == len(pts),
          (len(lp), len(pts)))
    yerr = [round((lp[i][1] if i < len(lp) else -999) - pts[i][1], 1) for i in range(len(pts))]
    xerr = [round((lp[i][0] if i < len(lp) else -999) - pts[i][0], 1) for i in range(len(pts))]
    check("그리는 도중 선 y 가 손가락 y 그대로 (어긋남 없음, ±1.5px)",
          all(abs(e) <= 1.5 for e in yerr), yerr)
    check("그리는 도중 선 x 도 손가락 x 그대로 (±1.5px)",
          all(abs(e) <= 1.5 for e in xerr), xerr)
    check("예전처럼 머리 높이(56px)만큼 위로 어긋나지 않음",
          all(abs(e) < 20 for e in yerr), yerr)
    page.screenshot(path=os.path.join(SHOT, "diary-v49-pen.png"))

    page.evaluate("([pts]) => { document.getElementById('d41Pen').__lastPt = pts[pts.length - 1]; }", [pts])
    up = page.evaluate(PEN_UP, 8080)
    check("손을 떼도 선이 제자리 — 그리던 선과 다 그린 선이 같음",
          up["nStroke"] == 1 and up["nPath"] == 1, up["nStroke"])
    fp = pairs(up["d"])
    ferr = [round((fp[i][1] if i < len(fp) else -999) - pts[i][1], 1) for i in range(len(pts))]
    check("다 그린 선도 손가락 y 그대로 (±1.5px)", all(abs(e) <= 1.5 for e in ferr), ferr)
    jump = max(abs(a[1] - b[1]) for a, b in zip(lp, fp)) if lp and fp else 999
    check("손 떼는 순간 선이 튀지 않음 (그리던 자리 = 다 그린 자리, ±1.5px)", jump <= 1.5, jump)

    # ==================================================================
    # 6. 글씨 도구 판도 같은 자리
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(460)
    tp = page.evaluate(PANEL)
    check("글씨 도구 판도 도구 줄 바로 아래(56px)",
          (not tp["hidden"]) and tp["display"] != "none" and tp["top"] == 56, tp)
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(300)

    # ==================================================================
    # 7. 보기(전체화면) — 도구 줄·도구 판 없이 ‹ 뒤로만
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(420)
    vt = page.evaluate(PEN_TAP, [120, 430, 9090])
    page.wait_for_timeout(460)
    check("보기로 가면 도구 줄·도구 판이 숨고 ‹ 뒤로만 남음",
          vt["view"] and vt["toolsHidden"] and vt["toolsDisplay"] == "none"
          and vt["panelHidden"] and vt["panelDisplay"] == "none" and vt["backShown"], vt)
    vlay = page.evaluate(LAYOUT)
    check("보기에서도 ‹ 뒤로 화살표는 28px 그대로", vlay["svgW"] == "28px", vlay["svgW"])
    check("보기에서도 화살표·도구 줄 자리는 위 그대로 (52px 줄 하나)",
          vlay["topRowH"] == 52 and vlay["headH"] == 56, (vlay["topRowH"], vlay["headH"]))
    page.screenshot(path=os.path.join(SHOT, "diary-v49-view.png"))

    # ==================================================================
    # 8. 좁은 폰(375px)에서도 도구 줄이 한 줄에
    # ==================================================================
    page.set_viewport_size({"width": 375, "height": 812})
    page.wait_for_timeout(420)
    page.locator("#d41Canvas").click(position={"x": 120, "y": 430})
    page.wait_for_timeout(520)
    n375 = page.evaluate(LAYOUT)
    check("375px 폭에서도 도구 6개가 한 줄 — 줄바꿈 없음",
          n375["toolsDisplay"] != "none" and n375["kidsN"] == 6 and n375["kidsCenterSpread"] <= 1
          and n375["toolsRight"] <= n375["vw"],
          (n375["toolsDisplay"], n375["kidsN"], n375["kidsCenterSpread"], n375["toolsRight"], n375["vw"]))
    check("375px 폭에서도 ‹ 뒤로와 겹치지 않음",
          n375["backRight"] <= n375["toolsLeft"] + 1 and n375["toolsLeft"] <= 60,
          (n375["backRight"], n375["toolsLeft"]))
    check("375px 폭에서 도구 단추가 줄지 않음 (44·46px)",
          n375["kidWidths"] == [44, 44, 46, 46, 46], n375["kidWidths"])
    page.screenshot(path=os.path.join(SHOT, "diary-v49-toolbar-375.png"))
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(420)

    check("브라우저 콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 9. 사진 여러 장 담기 — 3장씩 나란히 · 고른 순서 그대로 · 끝까지
    # ==================================================================
    ctxp = new_ctx(browser)
    ctxp.add_init_script("window.__TWOLOG_MODE = 'local';")
    pp = ctxp.new_page()
    errsp = []
    watch(pp, errsp)
    pp.goto(URL, wait_until="domcontentloaded")
    pp.wait_for_selector("#tabbar .tab", timeout=25000)
    pp.wait_for_timeout(900)
    tab(pp, 3, 680)
    shots = []
    for nm in ["v49a", "v49b", "v49c", "v49d"]:
        sp = "/tmp/v49-%s.jpg" % nm
        with open(sp, "wb") as f:
            f.write(bytes.fromhex(JPG_HEX))
        shots.append(sp)
    pp.set_input_files("#photoInput", shots)
    pp.wait_for_timeout(700)
    upn = pp.evaluate("""() => ({rows: document.querySelectorAll('#sheet .up-grid .up-cell').length,
      btn: (document.querySelector('#upBtn') || {}).textContent || ''})""")
    check("4장을 고르면 「사진 추가」 시트에 4장", upn["rows"] == 4 and upn["btn"].startswith("4장"), upn)

    # 진행 막대가 장마다 올라가는지 지켜보는 관찰기
    pp.evaluate("""() => {
      window.__bar = [];
      const el = document.querySelector('#upBar i');
      if (!el) return;
      window.__bar.push(el.style.width || '0%');
      new MutationObserver(() => window.__bar.push(el.style.width || '0%'))
        .observe(el, {attributes: true, attributeFilter: ['style']});
    }""")
    t0 = time.time()
    pp.locator("#sheet #upBtn").click()
    got = 0
    for _ in range(200):
        pp.wait_for_timeout(50)
        got = pp.evaluate("() => (window.__app.state.photos || []).length")
        if got >= 4:
            break
    elapsed = time.time() - t0
    pp.wait_for_timeout(900)          # 저장(save)이 한 번에 끝난 뒤 localStorage 까지 확인
    savedp = pp.evaluate("""() => ({titles: (window.__app.state.photos || []).map(p => p.title),
      n: (window.__app.state.photos || []).length,
      ls: JSON.parse(localStorage.getItem('twolog:v1:state') || '{}').photos || [],
      bar: window.__bar || [],
      sheetOpen: !!document.querySelector('#sheet.sheet-open')})""")
    check("4장 모두 끝까지 담김 (앱을 닫아도 남게 저장)", savedp["n"] == 4 and len(savedp["ls"]) == 4,
          (savedp["n"], len(savedp["ls"])))
    check("고른 순서 그대로 저장 — 1번째 사진이 맨 앞",
          savedp["titles"] == ["v49-v49a", "v49-v49b", "v49-v49c", "v49-v49d"], savedp["titles"])
    check("사진 4장을 몇 초 안에 (예전엔 한 장씩 기다려 아주 느렸어요)", elapsed < 6.0, round(elapsed, 2))
    bar = [b for b in savedp["bar"]]
    steps = []
    for b in bar:
        if b and (not steps or steps[-1] != b):
            steps.append(b)
    check("진행 막대가 장마다 올라가 100%까지 (25 → 50 → 75 → 100%)",
          steps[-1:] == ["100%"] and len(steps) >= 4
          and [int(x.replace("%", "")) for x in steps] == sorted(int(x.replace("%", "")) for x in steps),
          steps)
    check("담은 뒤 시트가 닫힘", savedp["sheetOpen"] is False, savedp["sheetOpen"])

    sync_js = pp.request.get(URL + "sync.js").text()
    app_src = pp.request.get(URL + "app.js").text()
    check("사진 압축 설정 — 긴 변 1200px · 품질 0.78 (예전 1800px·0.82)",
          "photoMaxDim: 1200" in sync_js and "photoQuality: 0.78" in sync_js)
    m = re.search(r"SupabaseBackend\.prototype\.addPhoto = function.*?(?=SupabaseBackend\.prototype\.photoUrls)", sync_js, re.S)
    body = m.group(0) if m else ""
    check("사진을 올린 뒤 서명 URL 왕복(createSignedUrl)을 기다리지 않음",
          body != "" and "createSignedUrl" not in body, body[:80])
    check("방금 압축한 사진(blob)으로 바로 보여 줌", "createObjectURL(res.blob)" in body)
    check("업로드가 한 번 실패하면 1회 자동 재시도", "attempt >= 1" in body and "put(attempt + 1)" in body)
    m2 = re.search(r"function addPhotoFiles\(files, meta\).*?(?=function formEditPhoto)", app_src, re.S)
    fn = m2.group(0) if m2 else ""
    check("사진을 3장씩 나란히 담음 (동시성 3)", "runLimited(files, 3," in fn, fn[:80])
    check("장마다 save() 하지 않음 (addPhotoFiles 안 save() 2번 이하)", fn.count("save();") <= 2,
          fn.count("save();"))
    check("사진 담기 콘솔/페이지 오류 없음", len(errsp) == 0, errsp[:4])
    ctxp.close()
    browser.close()

print("")
if fails:
    print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS — v49")
