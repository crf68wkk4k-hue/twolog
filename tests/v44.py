"""투로그 v44 확인 — 동기화 오류 덮어쓰기 방지 · 기념일·프로필 시트 손보기.

1) 버전: sw.js 캐시 twolog-v48 · APP_VERSION v48 · My 탭 「버전 v48」
2) 동기화 오류 덮어쓰기 방지 (v44 핵심)
   - 서버 표(events/notes/photos/settings) 읽기가 하나라도 실패하면 load() 가 실패로 끝나고
     빈 배열로 화면을 덮어쓰지 않음 — Realtime 재읽기(scheduleReload)·당겨오기(store.pull) 뒤에도
     홈·노트 내용이 그대로, backend.prev 도 그대로
   - 실패 플래그를 켜 둔 채 다시 켜면(초기 store.load 실패) localStorage 캐시로 화면을 채움
   - 실패가 끝나면(플래그 해제) 다시 당겨 와서 online 으로 돌아옴
3) 기념일 & 생일 시트 — 「상단 문구」·「우리의 시작」 줄이 가운데로 (두 칸 폭 같게·글자 가운데 정렬·높이 같게),
   상단 문구 라벨 옆 「최대 14자 · 남은 글자」 가 쓰는 동안 줄어듦 (한글 조합 입력 포함)
4) 내 프로필 — 닉네임 라벨은 크고 진하게(14px·700·진한 색), 닉네임 글씨도 크게(20px·700)
5) 생일은 예전처럼 «한 번에» 날짜칸 하나 (type=date · name=bday · 1900-01-01~오늘) —
   v44 의 «년/월/일» 세 칸 고르기는 v45 에서 걷어냄,
   고르면 아래에 「1992년 6월 26일」 이 바로 보이고 저장하면 YYYY-MM-DD 로 남음(서버 settings birthdays 포함),
   날짜칸을 비우면 생일이 지워짐
6) 콘솔/페이지 오류 0건

    python3 tests/v44.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import base64, functools, http.server, json, os, re, socketserver, sys, threading, time

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


def tab(page, idx, wait=520):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def seed_demo(page, extra_list=False):
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    """예시 화면(저 저장 잠김)에서 상태를 꺼내 심어요 — «그림판» 카테고리를 추가로 심을 수도 있습니다.
       (일반 화면에서 localStorage 를 고치면 나갈 때 자동 저장이 덮어쓰므로, 예시 화면 위에서 심어요)"""
    inject = ""
    if extra_list:
        inject = ("st.lists = (st.lists || []).concat([{id: 'Lc44', title: '그림판', emoji: '', kind: 'memo', items: []}]);"
                  "st.groups = st.groups || {}; st.groups['list:Lc44'] = [];")
    seed = page.evaluate("() => { const st = JSON.parse(JSON.stringify(window.__app.state)); " + inject +
                         " return JSON.stringify(st); }")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)


DRAW_JS = """([pts]) => {
  /* pts: [[x, y], ...] — 종이 폭 기준 0~1 좌표로 펜 획을 그려요 */
  const svgEl = document.getElementById('d41Pen');
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const W = r.width;
  const mk = (type, p) => new PointerEvent(type, {pointerId: 700, pointerType: 'touch',
    clientX: r.left + p[0] * W, clientY: r.top + p[1] * W, bubbles: true, cancelable: true});
  svgEl.dispatchEvent(mk('pointerdown', pts[0]));
  for (let i = 1; i < pts.length; i++) svgEl.dispatchEvent(mk('pointermove', pts[i]));
  svgEl.dispatchEvent(mk('pointerup', pts[pts.length - 1]));
  return JSON.parse(document.getElementById('d41PenIn').value).length;
}"""

DRAG_PEN_JS = """([x0, y0, dx, dy]) => {
  const paper = document.getElementById('d41Paper');
  const r = paper.getBoundingClientRect();
  const W = r.width;
  const mk = (type, x, y) => new PointerEvent(type, {pointerId: 801, pointerType: 'touch',
    clientX: r.left + x * W, clientY: r.top + y * W, bubbles: true, cancelable: true});
  paper.dispatchEvent(mk('pointerdown', x0, y0));
  for (let i = 1; i <= 4; i++) document.dispatchEvent(mk('pointermove', x0 + dx * i / 4, y0 + dy * i / 4));
  document.dispatchEvent(mk('pointerup', x0 + dx, y0 + dy));
  return JSON.parse(document.getElementById('d41PenIn').value)[0].p.slice(0, 2);
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
    check("sw.js 캐시 버전 twolog-v48", 'const VERSION = "twolog-v48"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v48", 'var APP_VERSION = "v48"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v44 문자열이 남아 있지 않음",
          "twolog-v44" not in sw and 'APP_VERSION = "v44"' not in app_js)

    seed_demo(page)
    tab(page, 4, 600)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v48」", ver.strip() == "버전 v48", ver)
    ctx.close()

    # ==================================================================
    # 2. 기념일 & 생일 시트 — 줄 가운데 정렬 · 남은 글자 수
    # ==================================================================
    ctxA = new_ctx(browser)
    ctxA.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageA = ctxA.new_page()
    errsA = []
    watch(pageA, errsA)
    seed_demo(pageA)
    tab(pageA, 0, 560)
    pageA.locator("#s-home .dday").click()
    pageA.wait_for_timeout(700)
    d1 = pageA.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const ph = sh.querySelector('input[name=phrase]');
      const since = sh.querySelector('input[name=since]');
      const cnt = document.getElementById('ddayPhraseCnt');
      const rp = ph.getBoundingClientRect(), rs = since.getBoundingClientRect();
      const row = sh.querySelector('.dday-row').getBoundingClientRect();
      const phSt = getComputedStyle(ph), siSt = getComputedStyle(since);
      return {head: (sh.querySelector('.sheet-hd h2') || {}).textContent || '',
        mileHd: (sh.querySelector('.mile-hd') || {}).textContent || '',
        labels: [...sh.querySelectorAll('.dday-row label')].map(l => l.textContent.trim()),
        cnt: cnt ? cnt.textContent.trim() : '',
        cntInLbl: !!(cnt && cnt.closest('label')),
        maxlen: ph.getAttribute('maxlength'),
        taPh: phSt.textAlign, taSi: siSt.textAlign,
        hPh: Math.round(rp.height), hSi: Math.round(rs.height),
        wPh: Math.round(rp.width), wSi: Math.round(rs.width),
        sameRow: Math.abs(rp.top - rs.top) < 6 && rp.right <= rs.left,
        leftGap: Math.round(rp.left - row.left), rightGap: Math.round(row.right - rs.right),
        bottom: Math.abs(rp.bottom - rs.bottom) <= 2,
        val: ph.value};
    }""")
    check("시트 이름은 «프로필 편집» · 맨 아래 묶음은 «기념일»", d1["head"] == "프로필 편집"
          and d1["mileHd"] == "기념일", (d1["head"], d1["mileHd"]))
    check("기념일 시트 — 「상단 문구」·「우리의 시작」이 한 줄", d1["sameRow"], d1)
    check("두 칸 폭이 같고 줄이 가운데로 (왼쪽 빈칸 ≈ 오른쪽 빈칸)",
          abs(d1["wPh"] - d1["wSi"]) <= 6 and abs(d1["leftGap"] - d1["rightGap"]) <= 8, d1)
    check("두 입력칸 글씨가 가운데 정렬 · 높이와 밑줄이 맞음",
          d1["taPh"] == "center" and d1["taSi"] == "center"
          and abs(d1["hPh"] - d1["hSi"]) <= 2 and d1["bottom"], d1)
    check("상단 문구 라벨 옆에 「최대 14자 · 남은 글자」 (라벨 안)",
          d1["cntInLbl"] and re.match(r"^최대 14자 · \d+$", d1["cnt"]) is not None, d1["cnt"])
    cnt0 = int(d1["cnt"].split("·")[1].strip())
    check("열자 때 남은 글자 수가 지금 쓴 글자수와 맞음",
          cnt0 == 14 - len(d1["val"]), {"cnt": d1["cnt"], "len": len(d1["val"])})
    # 쓰는 동안 줄어드는지 (8자 → 6)
    pageA.fill('#sheetForm input[name="phrase"]', "준영이가 소영이")
    pageA.wait_for_timeout(200)
    c1 = pageA.evaluate("(document.getElementById('ddayPhraseCnt')||{}).textContent || ''")
    check("글씨를 쓰면 남은 글자가 줄어듦 (8자 → 6)",
          c1.strip() == "최대 14자 · %d" % (14 - len("준영이가 소영이")), c1)
    pageA.fill('#sheetForm input[name="phrase"]', "준영이가 소영이 쫓아다닌지")
    pageA.wait_for_timeout(200)
    c2 = pageA.evaluate("(document.getElementById('ddayPhraseCnt')||{}).textContent || ''")
    check("14자(맥스)를 쓰면 남은 글자가 0", c2.strip() == "최대 14자 · 0", c2)
    # 한글 조합(IME) 입력 뒤에도 맞는지 — compositionend 로 검사
    pageA.evaluate("""() => {
      const el = document.querySelector('#sheetForm input[name=phrase]');
      el.value = '함께한 지';
      el.dispatchEvent(new Event('compositionend', {bubbles: true}));
    }""")
    pageA.wait_for_timeout(160)
    c3 = pageA.evaluate("(document.getElementById('ddayPhraseCnt')||{}).textContent || ''")
    check("한글 조합 입력(compositionend) 뒤에도 남은 글자가 맞음 (5자 → 9)",
          c3.strip() == "최대 14자 · %d" % (14 - len("함께한 지")), c3)
    pageA.screenshot(path=os.path.join(SHOT, "dday-v44-sheet.png"))
    check("브라우저 콘솔/페이지 오류 없음 (기념일 시트)", len(errsA) == 0, errsA[:4])

    # ==================================================================
    # 3. 내 프로필 — 닉네임 크게 · 생일은 날짜칸 한 개 (v45 에서 세 칸 고르기를 걷어냄)
    # ==================================================================
    pageA.locator('#sheet .dday-profs button[data-act="personSheet"][data-who="me"]').click()
    pageA.wait_for_timeout(560)
    pr = pageA.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const lbl = sh.querySelector('.pr-lbl');
      const nm = document.getElementById('personName');
      const inp = sh.querySelector('input[name=bday]');
      const ls = lbl ? getComputedStyle(lbl) : null, ns = nm ? getComputedStyle(nm) : null;
      const txt = document.getElementById('prBdayTxt');
      return {lbl: ls ? {fs: ls.fontSize, fw: ls.fontWeight, color: ls.color} : null,
        nm: ns ? {fs: ns.fontSize, fw: ns.fontWeight} : null,
        date: !!inp && inp.type === 'date', min: inp ? inp.getAttribute('min') : '',
        max: inp ? inp.getAttribute('max') : '',
        sel3: !!(sh.querySelector('select.pr-bday-y') || sh.querySelector('select.pr-bday-m') || sh.querySelector('select.pr-bday-d')),
        txt: txt ? txt.textContent : ''};
    }""")
    check("내 프로필 생일은 날짜칸 하나 (type=date · 세 칸 고르기 없음)",
          pr["date"] and not pr["sel3"] and pr["min"] == "1900-01-01", pr)
    check("닉네임 라벨이 크고 진하게 (14px·700·진한 글씨)",
          pr["lbl"] and pr["lbl"]["fs"] == "14px" and pr["lbl"]["fw"] in ("700", "bold")
          and pr["lbl"]["color"] not in ("", "rgba(0, 0, 0, 0)"), pr["lbl"])
    check("닉네임 글씨가 크게 (20px·700)",
          pr["nm"] and pr["nm"]["fs"] == "20px" and pr["nm"]["fw"] in ("700", "bold"), pr["nm"])
    # 1992년 6월 26일 고르기 — 고르는 순간 아래 줄에 보임
    pageA.fill("#sheet input[name=bday]", "1992-06-26")
    pageA.wait_for_timeout(260)
    picked = pageA.evaluate("""() => ({val: document.querySelector('#sheet input[name=bday]').value,
      txt: document.getElementById('prBdayTxt').textContent.trim()})""")
    check("1992-06-26 을 고르면 아래에 「1992년 6월 26일」", picked["val"] == "1992-06-26"
          and "1992년 6월 26일" in picked["txt"], picked)
    pageA.screenshot(path=os.path.join(SHOT, "person-v44-sheet.png"))
    # 윤년 날짜도 그대로 담김 (2024-02-29)
    pageA.fill("#sheet input[name=bday]", "2024-02-29")
    pageA.wait_for_timeout(200)
    leap = pageA.evaluate("() => document.querySelector('#sheet input[name=bday]').value")
    check("윤년 2024-02-29 도 그대로 담김", leap == "2024-02-29", leap)
    # 비우면 지워짐
    pageA.fill("#sheet input[name=bday]", "")
    pageA.wait_for_timeout(200)
    empty = pageA.evaluate("""() => ({v: document.querySelector('#sheet input[name=bday]').value,
      txt: document.getElementById('prBdayTxt').textContent.trim()})""")
    check("날짜칸을 비우면 생일이 지워짐", empty["v"] == "" and "년" not in empty["txt"], empty)
    # 다시 1992-06-26 으로 골라 저장
    pageA.fill("#sheet input[name=bday]", "1992-06-26")
    pageA.wait_for_timeout(220)
    pageA.locator('#sheet button.btn-primary[type="submit"]').click()
    pageA.wait_for_timeout(700)
    saved = pageA.evaluate("""() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      return (s.couple && s.couple.birthdays || {}).me || ''; }""")
    check("저장하면 생일이 1992-06-26 으로 남음", saved == "1992-06-26", saved)
    # 기념일 시트에서 들어왔으면 저장 뒤 그 시트로 돌아옴 — 닫고 홈으로
    pageA.keyboard.press("Escape")
    pageA.wait_for_timeout(300)
    # 다시 열어도 세 칸에 그대로
    tab(pageA, 0, 480)
    pageA.locator("#s-home .dday").click()
    pageA.wait_for_timeout(600)
    pageA.locator('#sheet .dday-profs button[data-act="personSheet"][data-who="me"]').click()
    pageA.wait_for_timeout(520)
    back = pageA.evaluate("""() => ({v: (document.querySelector('#sheet input[name=bday]') || {}).value || '',
      txt: document.getElementById('prBdayTxt').textContent.trim()})""")
    check("다시 열어도 1992-06-26 이 채워진 채", back["v"] == "1992-06-26"
          and "1992년 6월 26일" in back["txt"], back)
    check("브라우저 콘솔/페이지 오류 없음 (내 프로필)", len(errsA) == 0, errsA[:4])
    pageA.keyboard.press("Escape")
    pageA.wait_for_timeout(300)
    pageA.keyboard.press("Escape")
    pageA.wait_for_timeout(300)
    # ==================================================================
    # 4. 달력 — 여러 주에 걸친 일정은 제목이 첫 주에만 (이어지는 주는 빈 막대)
    # ==================================================================
    pageA.evaluate("""() => { const s = window.TwoLogUI.state;
      s.events = (s.events || []).concat([{id: 'E44w', date: '2026-11-25', endDate: '2026-11-30',
        title: '가족 여행', place: '', who: 'both', color: '#625A7F', memo: ''}]);
      window.TwoLogUI.rerender(); }""")
    pageA.wait_for_timeout(500)
    tab(pageA, 1, 560)
    cal4 = pageA.evaluate("""() => {
      const bars = [...document.querySelectorAll('#s-cal .ebar')];
      const titled = bars.filter(b => (b.textContent || '').trim() === '가족 여행');
      const cont = bars.filter(b => b.classList.contains('openl') && !(b.textContent || '').trim());
      return {titled: titled.length, cont: cont.length};
    }""")
    check("여러 주에 걸친 일정(11.25~11.30) — 제목은 첫 주 막대에만, 이어지는 주 막대는 빈 막대",
          cal4["titled"] == 1 and cal4["cont"] == 1, cal4)

    ctxA.close()

    # ==================================================================
    # 5. 모눈 다이어리 — 위로 옮긴 도구 바 · 글씨 도구 · 펜 도크 · 되돌리기 · 자동 저장
    # ==================================================================
    ctxB = new_ctx(browser)
    ctxB.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageB = ctxB.new_page()
    errsB = []
    watch(pageB, errsB)
    seed_demo(pageB, extra_list=True)
    tab(pageB, 2, 620)
    pageB.locator("#s-diary .lchip", has_text="그림판").first.click()
    pageB.wait_for_timeout(520)
    pageB.locator("#s-diary .d41-new").click()
    pageB.wait_for_timeout(760)
    ed4 = pageB.evaluate("""() => {
      const tools = document.querySelector('#sheet .d41-tools');
      const canvas = document.getElementById('d41Canvas');
      const panel = document.getElementById('d41Panel');
      const rt = tools ? tools.getBoundingClientRect() : null;
      const rc = canvas ? canvas.getBoundingClientRect() : null;
      return {saveBtn: !!document.querySelector('#sheet .d41-save'),
        undo: !!document.getElementById('d41UndoBtn'), redo: !!document.getElementById('d41RedoBtn'),
        undoDis: (document.getElementById('d41UndoBtn') || {}).disabled,
        toolsTop: rt ? Math.round(rt.top) : -1, canvasTop: rc ? Math.round(rc.top) : -1,
        panelBelow: rt && rc ? rt.bottom <= rc.top + 2 : false,
        panelHidden: panel ? panel.hidden : null};
    }""")
    check("«저장» 단추는 없고, 되돌리기·다시 실행 단추가 상단에 (처음엔 모두 비활성)",
          not ed4["saveBtn"] and ed4["undo"] and ed4["redo"] and ed4["undoDis"], ed4)
    check("아이콘바(펜·글씨·사진)는 위로 — 위 줄 아래에, 모눈 위로 떠 있음 (v48)",
          ed4["toolsTop"] >= 52 and ed4["canvasTop"] == 0, ed4)

    # (a) T 도구 — 바로 새 글 상자, 배경을 누르면 글쓰기 끝(새 상자 안 만듦) + 자동 저장
    pageB.locator("#sheet .d41-tool[aria-label='글씨']").click()
    pageB.wait_for_timeout(360)
    tb4 = pageB.evaluate("""() => ({n: document.querySelectorAll('#sheet .d41-tx').length,
      focused: (document.activeElement || {}).className || '',
      open: !document.getElementById('d41Panel').hidden,
      align: !!document.querySelector('#sheet .d41-tb[data-act=d41Align]'),
      b: !!document.querySelector('#sheet .d41-tb[data-act=d41Bold]'),
      s: !!document.querySelector('#sheet .d41-tb[data-act=d41Strike]'),
      u: !!document.querySelector('#sheet .d41-tb[data-act=d41Underline]'),
      tc: !!document.querySelector('#sheet .d41-tc[data-act=d41ColorPick]'),
      minus: !!document.querySelector('#sheet [data-act=d41SizeStep][data-d="-1"]'),
      plus: !!document.querySelector('#sheet [data-act=d41SizeStep][data-d="1"]'),
      pv: (document.querySelector('#sheet .d41-pv') || {}).textContent || ''})""")
    check("T 를 누르면 바로 새 글 상자가 생기고 글씨 도구 두 줄(정렬·B·S·U·색 / − 크기 +)이 열림",
          tb4["n"] == 1 and "d41-txt" in tb4["focused"] and tb4["open"]
          and tb4["align"] and tb4["b"] and tb4["s"] and tb4["u"] and tb4["tc"]
          and tb4["minus"] and tb4["plus"], tb4)
    check("글씨 크기 기본 표시는 17 (16.5 의 반올림)", tb4["pv"] == "17", tb4["pv"])
    pageB.keyboard.type("바닥을 눌러도 새 상자가 안 생겨요")
    pageB.wait_for_timeout(240)
    pb4 = pageB.locator("#d41Paper").bounding_box()
    pageB.mouse.click(pb4["x"] + 300, pb4["y"] + 470)
    pageB.wait_for_timeout(420)
    after4 = pageB.evaluate("""() => ({n: document.querySelectorAll('#sheet .d41-tx').length,
      sel: document.querySelectorAll('#sheet .d41-tx.sel').length,
      panelHidden: document.getElementById('d41Panel').hidden,
      toolOn: document.querySelectorAll('#sheet .d41-tool.on').length,
      saved: (() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
        const l = (s.lists || []).filter(x => x.id === 'Lc44')[0] || {}; const it = (l.items || [])[0] || {};
        return ((it.texts || [])[0] || {}).text || ''; })()})""")
    check("글을 쓰고 배경을 누르면 — 새 상자가 더 생기지 않고(1개), 고르기도 풀리고 도구 판도 덮임",
          after4["n"] == 1 and after4["sel"] == 0 and after4["panelHidden"] and after4["toolOn"] == 0, after4)
    check("배경을 눌렀을 때 쓴 글이 자동 저장됨 (저장 단추 없이)",
          "바닥을 눌러도" in after4["saved"], after4["saved"])

    # (b) 굵게·취소선·밑줄·정렬·색·−+ 크기
    tb4b = pageB.locator("#sheet .d41-tx").first.bounding_box()
    pageB.mouse.click(tb4b["x"] + 14, tb4b["y"] + 10)
    pageB.wait_for_timeout(300)
    pageB.locator("#sheet .d41-tb[data-act=d41Bold]").click()
    pageB.wait_for_timeout(160)
    pageB.locator("#sheet .d41-tb[data-act=d41Strike]").click()
    pageB.wait_for_timeout(160)
    pageB.locator("#sheet .d41-tb[data-act=d41Underline]").click()
    pageB.wait_for_timeout(160)
    pageB.locator("#sheet .d41-tb[data-act=d41Align]").click()
    pageB.wait_for_timeout(160)
    pageB.locator("#sheet .d41-tb[data-act=d41Align]").click()
    pageB.wait_for_timeout(160)
    pageB.locator("#sheet .d41-tc[data-act=d41ColorPick]").click()
    pageB.wait_for_timeout(320)
    cp4 = pageB.evaluate("document.querySelectorAll('#sheet .d41-sp-dotb[data-act=d41Color]').length")
    pageB.locator("#sheet .d41-sp-dotb[data-act=d41Color]").nth(1).click()
    pageB.wait_for_timeout(240)
    pageB.locator("#sheet [data-act=d41SizeStep][data-d='1']").click()
    pageB.locator("#sheet [data-act=d41SizeStep][data-d='1']").click()
    pageB.wait_for_timeout(240)
    sty4 = pageB.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value)[0];
      const el = document.querySelector('#sheet .d41-tx');
      const cs = getComputedStyle(el);
      return {bold: t.bold, strike: t.strike, under: t.underline, align: t.align, color: t.color, size: t.size,
        fw: cs.fontWeight, deco: cs.textDecorationLine, ta: cs.textAlign}; }""")
    check("B·S·U 를 함께 쓸 수 있고, 정렬은 왼쪽→가운데→오른쪽으로 돌아감",
          sty4["bold"] == 1 and sty4["strike"] == 1 and sty4["under"] == 1
          and sty4["fw"] in ("700", "bold")
          and "line-through" in sty4["deco"] and "underline" in sty4["deco"], sty4)
    check("색 동그라미를 누르면 색 판이 열리고 고른 색·−+ 크기(19)가 반영",
          cp4 >= 5 and sty4["color"] and sty4["color"] != "#111111"
          and sty4["size"] == 19, (cp4, sty4))
    pageB.screenshot(path=os.path.join(SHOT, "diary-v44-text.png"))

    # (c) 펜 도크 — 형광펜 · 되돌리기·다시 실행 · 그림(획) 끌어 옮기기
    pageB.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    pageB.wait_for_timeout(340)
    dock4 = pageB.evaluate("""() => ({on: document.getElementById('d41Pen').classList.contains('on'),
      pens: [...document.querySelectorAll('#sheet .d41-dk')].map(b => b.getAttribute('aria-label')),
      ws: [...document.querySelectorAll('#sheet [data-act=d41PenMode][data-w]')].map(b => b.getAttribute('data-w')),
      texts: [...document.querySelectorAll('#sheet .d41-prow-dock .d41-pl')].length,
      dots: document.querySelectorAll('#sheet .d41-dot[data-act=d41PenColor]').length})""")
    # v45: 글씨 라벨 없는 한 줄 도크 — 가는 펜 · 일반 펜 · 형광펜 · 지우개 · 색 · 전체 지우기
    check("펜을 누르면 한 줄짜리 그림 도크가 바로 열림 (글씨 라벨 없음)",
          dock4["on"] and dock4["pens"] == ["가는 펜", "일반 펜", "형광펜", "지우개", "펜 색", "전체 지우기"]
          and dock4["ws"] == ["2", "4.5"] and dock4["texts"] == 0 and dock4["dots"] == 0, dock4)
    n0 = pageB.evaluate(DRAW_JS, [[[0.15, 0.62], [0.3, 0.66], [0.45, 0.63]]])
    pageB.wait_for_timeout(300)
    saved4a = pageB.evaluate("""() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      const l = (s.lists || []).filter(x => x.id === 'Lc44')[0] || {}; const it = (l.items || [])[0] || {};
      return (it.pen || []).length; }""")
    check("펜으로 한 획을 그리면 화면에 선이 남고 자동 저장됨 (저장 단추 없이)",
          n0 == 1 and saved4a == 1, (n0, saved4a))
    pageB.locator("#sheet .d41-dk[data-mode='hl']").click()
    pageB.wait_for_timeout(220)
    n1 = pageB.evaluate(DRAW_JS, [[[0.55, 0.7], [0.7, 0.74], [0.85, 0.71]]])
    pageB.wait_for_timeout(260)
    hl4 = pageB.evaluate("""() => { const p = JSON.parse(document.getElementById('d41PenIn').value)[1] || {};
      const path = [...document.querySelectorAll('#d41Pen path')][1];
      return {hl: p.hl, op: path ? path.getAttribute('stroke-opacity') : null}; }""")
    check("형광펜은 반투명(stroke-opacity 0.35)으로 그려지고 함께 저장 준비됨",
          n1 == 2 and hl4["hl"] == 1 and hl4["op"] == "0.35", hl4)
    pageB.screenshot(path=os.path.join(SHOT, "diary-v44-pen.png"))
    # 되돌리기 → 1획, 다시 실행 → 2획
    pageB.locator("#d41UndoBtn").click()
    pageB.wait_for_timeout(240)
    u1 = pageB.evaluate("JSON.parse(document.getElementById('d41PenIn').value).length")
    pageB.locator("#d41RedoBtn").click()
    pageB.wait_for_timeout(240)
    r1 = pageB.evaluate("JSON.parse(document.getElementById('d41PenIn').value).length")
    check("되돌리기(↶)로 마지막 획이 지워지고 다시 실행(↷)으로 돌아옴", u1 == 1 and r1 == 2, (u1, r1))
    # 그림(획)도 고르고 끌어 옮기기 — 글씨 모드에서 획을 누르면 점선 테두리
    pageB.locator("#sheet .d41-tool[aria-label='글씨']").click()
    pageB.wait_for_timeout(300)
    pos0 = pageB.evaluate(DRAG_PEN_JS, [0.56, 0.71, 0.08, 0.05])
    pageB.wait_for_timeout(300)
    penmov = pageB.evaluate("""() => ({sel: document.querySelectorAll('#d41Pen rect').length,
      x: !!document.getElementById('d41PenX'),
      p: JSON.parse(document.getElementById('d41PenIn').value)[1].p.slice(0, 2)})""")
    check("그린 획을 눌러 고르면 점선 테두리와 × 가 붙고, 끌면 획이 옮겨짐",
          penmov["sel"] == 1 and penmov["x"] and penmov["p"][0] > pos0[0] + 0.06, (pos0, penmov))
    pageB.locator("#d41PenX").click()
    pageB.wait_for_timeout(260)
    pendel = pageB.evaluate("""() => ({n: JSON.parse(document.getElementById('d41PenIn').value).length,
      x: !!document.getElementById('d41PenX'),
      saved: (() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
        const l = (s.lists || []).filter(x => x.id === 'Lc44')[0] || {}; const it = (l.items || [])[0] || {};
        return (it.pen || []).length; })()})""")
    check("× 를 누르면 그 획만 지워지고 자동 저장됨", pendel["n"] == 1 and not pendel["x"]
          and pendel["saved"] == 1, pendel)

    # (d) 사진 도구 — 누르면 곧바로 앨범(파일 고르기)
    with pageB.expect_file_chooser() as fc4:
        pageB.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    check("사진 도구를 누르면 앱 판 없이 곧바로 사진 고르기가 열림 (아이폰에서는 시스템 앨범 메뉴)", True)

    # (e) 나가면 자동 저장 — ‹ 뒤로로 닫아도 내용이 남고, 빈 다이어리는 안 남김
    pageB.locator("#sheet .d41-back").click()
    pageB.wait_for_timeout(700)
    kept4 = pageB.evaluate("""() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      const l = (s.lists || []).filter(x => x.id === 'Lc44')[0] || {}; const it = (l.items || [])[0] || {};
      return {n: (l.items || []).length, title: it.text || '', texts: (it.texts || []).length,
        pen: (it.pen || []).length}; }""")
    check("‹ 뒤로로 나가면 자동 저장 — 글·그림이 다이어리로 남음",
          kept4["n"] == 1 and kept4["texts"] == 1 and kept4["pen"] == 1, kept4)
    pageB.locator("#s-diary .d41-new").click()
    pageB.wait_for_timeout(700)
    pageB.locator("#sheet .d41-back").click()
    pageB.wait_for_timeout(600)
    ghost4 = pageB.evaluate("""() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      const l = (s.lists || []).filter(x => x.id === 'Lc44')[0] || {}; return (l.items || []).length; }""")
    check("아무것도 안 쓴 새 다이어리는 나가도 빈 항목이 남지 않음", ghost4 == 1, ghost4)
    check("브라우저 콘솔/페이지 오류 없음 (모눈 다이어리)", len(errsB) == 0, errsB[:4])
    ctxB.close()

    # ==================================================================
    # 5. 동기화 오류 덮어쓰기 방지 — 서버 표 읽기 실패 시 화면 유지
    # ==================================================================
    cid = "couple-v44"
    uid = "user-v44"
    mail = "v44@twolog.app"
    note_row = {"id": "L44", "couple_id": cid, "kind": "list", "sort": 0, "deleted": False,
                "payload": {"title": "우리의 메모", "emoji": "", "kind": "memo", "items": []}}
    db = {
        "users": {uid: {"id": uid, "email": mail, "password": "pw123456"}},
        "couples": [{"id": cid, "invite_code": "441744", "members": [uid],
                     "me": "소영", "you": "준영", "since": "2025-11-21", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [{"id": "E44", "couple_id": cid, "date": "2026-12-24", "title": "크리스마스 데이트",
                    "time": "19:00", "place": "성수", "who": "both", "color": "#625A7F", "memo": ""}],
        "photos": [],
        "notes": [note_row],
        "settings": [{"couple_id": cid, "key": "note_meta",
                      "value": {"tabs": {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"},
                                         "log": {"e": "", "n": "미정"}},
                                "order": ["todo", "bucket", "log", "list:L44"],
                                "kinds": {"log": "memo"}}}],
        "uploads": [], "seq": 44,
    }
    seed = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({access_token: 't', refresh_token: 'r',
        user: {id: %s, email: %s}}));
    })();""" % (json.dumps(json.dumps(db, ensure_ascii=False)), json.dumps(uid), json.dumps(mail))
    ctxD = new_ctx(browser)
    ctxD.add_init_script(seed)
    # 실패 플래그는 localStorage 로 넘겨 새로고침 뒤에도 유지되게 (init script 는 매 부팅마다 다시 실행됨)
    ctxD.add_init_script("window.__STUB_FAIL_TABLE = localStorage.getItem('stub-fail-table') || '';")
    pageD = ctxD.new_page()
    errsD = []
    watch(pageD, errsD)
    stub_route(pageD)
    pageD.goto(URL, wait_until="domcontentloaded")
    pageD.wait_for_selector("#tabbar .tab", timeout=25000)
    pageD.wait_for_timeout(2600)

    def snap_state(pg):
        return pg.evaluate("""() => {
          const s = window.TwoLogUI.state;
          const be = window.TwoLogStore.backend;
          return {lists: (s.lists || []).length,
            notes: (s.lists || []).reduce((n, l) => n + (l.items || []).length, 0),
            listTitle: ((s.lists || [])[0] || {}).title || '',
            events: (s.events || []).length,
            evTitle: (s.events || [])[0] ? (s.events[0].title || '') : '',
            prevNotes: be && be.prev ? Object.keys(be.prev.notes || {}).length : -1,
            status: window.TwoLogStore.status.state};
        }""")

    before = snap_state(pageD)
    check("처음 읽기 — 서버 내용이 화면에 있음 (일정 1 · 카테고리 1 · prev 1)",
          before["events"] == 1 and before["lists"] == 1 and before["prevNotes"] == 1
          and before["evTitle"] == "크리스마스 데이트" and before["listTitle"] == "우리의 메모"
          and before["status"] == "online", before)

    # (a) notes 표 읽기 실패 + Realtime 재읽기 → 화면·prev 그대로
    pageD.evaluate("() => { window.__STUB_FAIL_TABLE = 'notes'; }")
    pageD.evaluate("(cid) => window.__stubEmit('notes', cid)", cid)
    pageD.wait_for_timeout(1500)
    after_emit = snap_state(pageD)
    check("Realtime 재읽기가 실패해도 홈·노트 화면이 그대로",
          after_emit["events"] == 1 and after_emit["lists"] == 1
          and after_emit["listTitle"] == "우리의 메모"
          and after_emit["evTitle"] == "크리스마스 데이트", after_emit)
    check("실패한 재읽기가 서버 앞면(backend.prev)을 비우지 않음",
          after_emit["prevNotes"] == 1, after_emit["prevNotes"])
    # (b) 당겨오기(store.pull) 실패 → 상태 유지
    pulled = pageD.evaluate("""() => window.TwoLogStore.pull().then(r => ({r: r === null ? 'null' : 'doc',
      lists: (window.TwoLogUI.state.lists || []).length, status: window.TwoLogStore.status.state}))""")
    check("당겨오기가 실패하면 화면을 덮어쓰지 않고 지금 상태를 유지",
          pulled["r"] == "null" and pulled["lists"] == 1, pulled)
    # (c) load 가 실패로 끝나는지 — reject 확인
    rej = pageD.evaluate("""() => window.TwoLogStore.backend.load()
      .then(() => 'resolved', e => 'rejected: ' + (e && e.message || e))""")
    check("표 읽기가 실패하면 load() 가 실패(reject)로 끝남 (빈 문서로 끝나지 않음)",
          rej.startswith("rejected"), rej)
    pageD.evaluate("() => { window.__STUB_FAIL_TABLE = ''; }")

    # (d) 실패 플래그를 켜 둔 채 다시 켜면 → localStorage 캐시로 화면 채우기
    pageD.evaluate("""() => { const s = window.TwoLogUI.state;
      localStorage.setItem('twolog:v1:state', JSON.stringify(s)); }""")
    pageD.evaluate("() => localStorage.setItem('stub-fail-table', 'notes')")
    pageD.reload(wait_until="domcontentloaded")
    pageD.wait_for_selector("#tabbar .tab", timeout=25000)
    pageD.wait_for_timeout(2600)
    pageD.evaluate("() => localStorage.removeItem('stub-fail-table')")
    booted = snap_state(pageD)
    check("켤 때 서버 읽기가 실패해도 캐시로 홈·노트를 채움 (빈 화면 아님)",
          booted["events"] == 1 and booted["lists"] == 1
          and booted["listTitle"] == "우리의 메모"
          and booted["evTitle"] == "크리스마스 데이트", booted)
    pageD.evaluate("() => { window.__STUB_FAIL_TABLE = ''; }")

    # (e) 실패가 끝나면 다시 당겨 옴
    ok = pageD.evaluate("""() => window.TwoLogStore.pull().then(r => ({got: !!r,
      status: window.TwoLogStore.status.state, lists: (window.TwoLogUI.state.lists || []).length}))""")
    check("실패가 끝나면 당겨 오기가 다시 서버로 (online · 내용 그대로)",
          ok["got"] and ok["status"] == "online" and ok["lists"] == 1, ok)

    # (f) 생일 저장 → 서버 settings birthdays 에 YYYY-MM-DD 로
    tab(pageD, 0, 520)
    pageD.locator("#s-home .dday").click()
    pageD.wait_for_timeout(600)
    pageD.locator('#sheet .dday-profs button[data-act="personSheet"][data-who="me"]').click()
    pageD.wait_for_timeout(520)
    pageD.fill('#sheet input[name=bday]', '1992-06-26')
    pageD.wait_for_timeout(240)
    pageD.locator('#sheet button.btn-primary[type="submit"]').click()
    pageD.wait_for_timeout(2800)
    srv = pageD.evaluate("""() => { const row = (window.__stub.settings || []).filter(x => x.key === 'birthdays')[0];
      return row ? ((row.value || {}).me || '') : ''; }""")
    check("생일이 서버 settings(birthdays) 에도 1992-06-26 으로 남음", srv == "1992-06-26", srv)
    # 실시간으로 다시 읽어도 생일이 남는지 (실패 없이)
    pageD.evaluate("(cid) => window.__stubEmit('settings', cid)", cid)
    pageD.wait_for_timeout(1500)
    kept = pageD.evaluate("""() => { const s = window.TwoLogUI.state;
      return ((s.couple && s.couple.birthdays) || {}).me || ''; }""")
    check("Realtime 재읽기 뒤에도 생일이 그대로", kept == "1992-06-26", kept)
    pageD.keyboard.press("Escape")
    pageD.wait_for_timeout(300)
    pageD.keyboard.press("Escape")
    pageD.wait_for_timeout(300)

    # (g) 펜만 있는 다이어리 — 제목·글·사진 없이 그림만 그려도 저장되고 서버 왕복에도 남음
    tab(pageD, 2, 620)
    pageD.locator("#s-diary .seg-btn", has_text="미정").first.click()
    pageD.wait_for_timeout(600)
    pageD.locator("#s-diary .d41-new").click()
    pageD.wait_for_timeout(760)
    pageD.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    pageD.wait_for_timeout(340)
    penOnly = pageD.evaluate(DRAW_JS, [[[0.2, 0.5], [0.4, 0.56], [0.6, 0.52]]])
    pageD.wait_for_timeout(400)
    pageD.locator("#sheet .d41-back").click()
    pageD.wait_for_timeout(2600)
    penRow = pageD.evaluate("""() => { const rows = (window.__stub.notes || []).filter(x => x.kind === 'log' || x.kind === 'list');
      const hit = rows.map(r => r.payload || {}).filter(p => Array.isArray(p.pen) && p.pen.length)
        .filter(p => !(p.title || '').trim() && !(p.items || []).length)[0];
      return hit ? {pen: hit.pen.length, id: hit.pen[0].id, hl: hit.pen[0].hl,
        pts: hit.pen[0].p.length, c: hit.pen[0].c, w: hit.pen[0].w} : null; }""")
    check("펜만 그린 다이어리도 저장됨 — notes payload 에 획(id·c·w·p)이 실림",
          penOnly == 1 and penRow and penRow["pen"] == 1 and penRow["pts"] >= 4
          and penRow["id"] and penRow["c"] and penRow["w"] > 0, (penOnly, penRow))
    pageD.reload(wait_until="domcontentloaded")
    pageD.wait_for_selector("#tabbar .tab", timeout=25000)
    pageD.wait_for_timeout(3000)
    tab(pageD, 2, 620)
    pageD.locator("#s-diary .seg-btn", has_text="미정").first.click()
    pageD.wait_for_timeout(600)
    try:
        pageD.wait_for_selector("#s-diary .d41-penz", timeout=12000)
    except Exception:
        dump = pageD.evaluate("""() => ({cards: document.querySelectorAll('#s-diary .d41-card').length,
          segs: [...document.querySelectorAll('#s-diary .seg-btn, #s-diary .lchip')].map(b => [b.textContent.trim(), b.className.indexOf('active') >= 0 || b.className.indexOf('on') >= 0]).slice(0, 8),
          logs: (window.__stub.notes || []).filter(x => x.kind === 'log').map(x => ({t: (x.payload || {}).title, pen: ((x.payload || {}).pen || []).length})),
          lists: (window.TwoLogUI.state.lists || []).map(l => [l.title, (l.items || []).length, ((l.items || [])[0] || {}).pen ? 1 : 0]),
          slog: (window.TwoLogUI.state.logs || []).map(l => [l.title, l.date, (l.pen || []).length]),
          status: window.TwoLogStore.status.state})""")
        print("DEBUG dump:", json.dumps(dump, ensure_ascii=False)[:800])
        raise
    cardPen = pageD.evaluate("""() => { const c = [...document.querySelectorAll('#s-diary .d41-card')]
      .filter(x => x.querySelector('.d41-penz'))[0];
      return c ? {label: c.querySelector('.d41-penz').textContent} : null; }""")
    check("다시 켜면 펜만 있는 다이어리가 «손그림» 카드로 남음", cardPen and cardPen["label"] == "손그림", cardPen)
    pageD.locator("#s-diary .d41-card").first.click()
    pageD.wait_for_timeout(900)
    penOpen = pageD.evaluate("""() => { const svg = document.getElementById('d41Pen');
      const vb = (svg && svg.getAttribute('viewBox') || '').split(' ');
      return {paths: svg ? svg.querySelectorAll('path').length : 0, vw: Number(vb[2] || 0)}; }""")
    check("다시 열면 그림이 종이에 그대로 그려짐 (선 1개 · 종이 폭이 잡힌 viewBox)",
          penOpen["paths"] == 1 and penOpen["vw"] > 100, penOpen)
    check("브라우저 콘솔/페이지 오류 없음 (동기화 오류 방지)", len(errsD) == 0, errsD[:4])
    ctxD.close()

    # ==================================================================
    # 마무리
    # ==================================================================
    print("")
    if fails:
        print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
        sys.exit(1)
    print("ALL PASS — v44")
