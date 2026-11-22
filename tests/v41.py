"""투로그 v41 확인 — 모눈 메모가 «모눈종이 풀스크린 다이어리»로 바뀐 것 + + 시트 문구 정리.

1) 버전: sw.js 캐시 twolog-v46 · APP_VERSION v46 · My 탭 「버전 v46」
2) + 시트 문구 정리
   - 고른 카테고리 아래 패널 제목은 「속지 · 이름」 (「속지 레이아웃」 아님)
   - 기본 카테고리(메모·버킷리스트·영화·먹방)의 배지와 첫 선택지도 「투두리스트」
     (데이터는 그대로 — 예전 「카드」 화면·항목 유지)
3) 노트 본문 화면 — 카테고리 이름 옆 속지 배지 없음 (이름만)
4) 모눈 메모 목록 단순화
   - 위 「오늘 있었던 일을 적고 Add」 입력줄과 아래 「본문까지 길게 쓰기」가 사라짐
   - 모눈 바탕 위 둥근 카드(날짜·제목·본문·사진 미리보기·× 삭제)
   - 빈 화면이면 「+ 새 다이어리」 카드 · 맨 아래에도 「+ 새 다이어리」
5) 모눈종이 풀스크린 다이어리
   - ‹ 뒤로 · 가운데 제목(새 다이어리) · 저장 · 큰 날짜 「11.21 SAT」(눌러서 바꾸기)
   - 본문 칸이 모눈 바탕 · 아래 도구 T · 사진 · 펜
   - T: 글씨 크기(작게·보통·크게) · 색 · 정렬(왼쪽·가운데) — 본문에 바로 반영, 저장됨
   - 사진: 여러 장 붙이기(720px 압축) · 고른 사진 크기 조절(작게·보통·크게) · × 삭제
   - 펜: 손가락으로 그리기 · 되돌리기 · 지우개 — 좌표는 폭 기준 0~1 로 보관
6) 저장·수정 — 카드에 날짜·제목·본문·사진 미리보기, 눌러서 이어 쓰기, 날짜 바꾸기
7) Supabase 스텁 왕복 — notes(kind=list) payload 에 imgs·sty·pen 이 실려 양쪽 폰에서 그대로
8) 다른 속지(별점 리뷰·지출·정산)는 그대로 · 다크 모드에서도 모눈
9) 콘솔/페이지 오류 0건

    python3 tests/v41.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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

JPG_HEX = (
    "ffd8ffe000104a46494600010100000100010000ffdb004300080606070605080707070909080a0c140d0c0b0b0c191213"
    "0f141d1a1f1e1d1a1c1c20242e2720222c231c1c2837292c30313434341f27393d38323c2e333432ffc0000b08000100"
    "0101011100ffc4001f0000010501010101010100000000000000000102030405060708090a0bffc400b5100002010303"
    "020403050504040000017d01020300041105122131410613516107227114328191a1082342b1c11552d1f02433627282"
    "090a161718191a25262728292a3435363738393a434445464748494a535455565758595a636465666768696a73747576"
    "7778797a838485868788898a92939495969798999aa2a3a4a5a6a7a8a9aab2b3b4b5b6b7b8b9bac2c3c4c5c6c7c8c9"
    "cad2d3d4d5d6d7d8d9dae1e2e3e4e5e6e7e8e9eaf1f2f3f4f5f6f7f8f9faffda0008010100003f00fbfcffd9")
SHOT_A = "/tmp/v41-a.jpg"
SHOT_B = "/tmp/v41-b.jpg"
for _p in (SHOT_A, SHOT_B):
    with open(_p, "wb") as _f:
        _f.write(bytes.fromhex(JPG_HEX))


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


def note_tab(page):
    tab(page, 2, 660)


def open_add_sheet(page):
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(560)


def pick_kind(page, kind):
    page.locator("#sheet #nkPanel .nk-card[data-kind='%s']" % kind).click()
    page.wait_for_timeout(180)


def row_loc(page, text):
    n = page.evaluate("""(nm) => {
      const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
      return rows.findIndex(r => { const i = r.querySelector('.nord-nm'); return i && i.value.indexOf(nm) >= 0; });
    }""", text)
    return page.locator("#sheet #noteOrderList .nord-row").nth(n)


def create_kind(page, name, kind):
    """+ 시트에서 이름을 적고 「추가」로 줄을 붙인 뒤 그 줄 아래에서 속지를 골라 저장."""
    open_add_sheet(page)
    page.fill("#sheet .nord-new", name)
    page.locator("#sheet .nord-add-btn").click()
    page.wait_for_timeout(300)
    pick_kind(page, kind)
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(780)


def open_new_diary(page):
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(640)


def editor(page):
    return page.evaluate("""() => {
      const q = (s) => document.querySelector(s);
      const paper = q('#sheet .d41-paper');
      const body = q('#sheet .d41-body');
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
              full: document.getElementById('sheetWrap').classList.contains('sheet-full'),
              back: !!q('#sheet .d41-back'),
              save: (q('#sheet .d41-save') || {}).textContent,
              noSave: !q('#sheet .d41-save'),
              titlePh: (q('#sheet .d41-title') || {}).placeholder,
              date: (q('#d41DateBig') || {}).textContent,
              dateVal: (q('#sheet input[name=date]') || {}).value,
              paper: paper ? getComputedStyle(paper).backgroundImage : '',
              bodyBg: body ? getComputedStyle(body).backgroundColor : '',
              bodyFs: body ? getComputedStyle(body).fontSize : '',
              bodyAlign: body ? getComputedStyle(body).textAlign : '',
              tools: [...document.querySelectorAll('#sheet .d41-tool')].map(b => b.getAttribute('aria-label')),
              h: Math.round((q('#sheet .d41') || {getBoundingClientRect: () => ({height: 0})}).getBoundingClientRect().height),
              vh: window.innerHeight};
    }""")


def state_list(page, title):
    return page.evaluate("""(t) => {
      const l = (window.__app.state.lists || []).filter(x => x.title === t)[0];
      return l ? JSON.parse(JSON.stringify(l)) : null;
    }""", title)


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
    check("sw.js 캐시 버전 twolog-v46", 'const VERSION = "twolog-v46"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v44", 'var APP_VERSION = "v46"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed_state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed_state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)

    tab(page, 4, 600)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v46」", ver.strip() == "버전 v46", ver)

    # ==================================================================
    # 2. + 시트 문구 — 「속지」 · 기본 카테고리도 「투두리스트」
    # ==================================================================
    note_tab(page)
    open_add_sheet(page)
    row_loc(page, "메모").locator(".nord-nm").click()
    page.wait_for_timeout(320)
    pn = page.evaluate("""() => ({
      label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || '',
      cards: [...document.querySelectorAll('#sheet #nkPanel .nk-card')].map(c => [
        c.getAttribute('data-kind'), (c.querySelector('.nk-n') || {}).textContent]),
      kind: (document.querySelector('#sheet #noteOrderList .nord-row.active') || {}).getAttribute
        ? document.querySelector('#sheet #noteOrderList .nord-row.active').getAttribute('data-kind') : null,
      fixed: [...document.querySelectorAll('#sheet .set-lbl')]
        .filter(e => !e.closest('#nkPanel') && e.textContent.trim() === '속지').length})""")
    check("패널 제목이 「속지」만 (v42 — 「속지 레이아웃」·이름 없이)",
          pn["label"].strip() == "속지" and "레이아웃" not in pn["label"], pn["label"])
    check("기본 카테고리 줄에는 속지 배지가 없음 (data-kind 는 지금 모양 그대로)",
          pn["kind"] == "" and "nord-kb" not in page.evaluate("document.querySelector('#sheet #noteOrderList').innerHTML"), pn["kind"])
    check("기본 카테고리 첫 선택지 이름도 「투두리스트」",
          pn["cards"] and pn["cards"][0][0] == "" and pn["cards"][0][1] == "투두리스트", pn["cards"][:2])
    check("선택지는 그대로 네 칸 (투두리스트·모눈 메모·별점 리뷰·지출·정산)",
          [c[1] for c in pn["cards"]] == ["투두리스트", "모눈 메모", "별점 리뷰", "지출·정산"], pn["cards"])

    # 내 카테고리도 같은 「속지」 문구
    page.fill("#sheet .nord-new", "주말 기록")
    page.locator("#sheet .nord-add-btn").click()
    page.wait_for_timeout(320)
    pn2 = page.evaluate("""() => ({
      label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || '',
      kinds: [...document.querySelectorAll('#sheet #nkPanel .nk-card')].map(c => c.getAttribute('data-kind'))})""")
    check("새로 더한 줄도 「속지」 · 네 속지",
          pn2["label"].strip() == "속지"
          and pn2["kinds"] == ["check", "memo", "review", "expense"], pn2)
    pick_kind(page, "memo")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(780)

    # ==================================================================
    # 3. 노트 본문 화면 — 이름 옆 속지 배지 없음
    # ==================================================================
    page.locator("#s-diary .lchip", has_text="주말 기록").first.click()
    page.wait_for_timeout(560)
    hd = page.evaluate("""() => ({
      name: (document.querySelector('#s-diary .note-hd .nh-l .t') || {}).textContent || '',
      badges: document.querySelectorAll('#s-diary .note-hd .nh-l .k').length})""")
    check("노트 본문 위에는 카테고리 이름만 (속지 배지 없음)",
          hd["name"] == "주말 기록" and hd["badges"] == 0, hd)

    # ==================================================================
    # 4. 모눈 메모 목록 단순화
    # ==================================================================
    lst = page.evaluate("""() => ({
      text: (document.querySelector('#s-diary .dbody') || {}).textContent || '',
      quick: document.querySelectorAll('#s-diary #listQuickForm').length,
      addrow: document.querySelectorAll('#s-diary .addrow').length,
      emptyCard: !!document.querySelector('#s-diary .d41-empty'),
      emptyText: (document.querySelector('#s-diary .d41-empty') || {}).textContent || '',
      newBtn: !!document.querySelector('#s-diary .d41-new'),
      grid: (() => { const l = document.querySelector('#s-diary .nmemo-list');
        return l ? getComputedStyle(l).backgroundImage : ''; })()})""")
    check("위 「오늘 있었던 일을 적고 Add」 입력줄이 사라짐",
          lst["quick"] == 0 and "오늘 있었던 일을 적고" not in lst["text"], lst["quick"])
    check("아래 「본문까지 길게 쓰기」가 사라짐",
          lst["addrow"] == 0 and "본문까지 길게 쓰기" not in lst["text"], lst["addrow"])
    check("비어 있으면 「+ 새 다이어리」 카드가 보임",
          lst["emptyCard"] and "새 다이어리" in lst["emptyText"], lst["emptyText"].strip())
    check("맨 아래에도 「+ 새 다이어리」 버튼", lst["newBtn"] is True)
    check("목록 바탕은 모눈 격자", "linear-gradient" in (lst["grid"] or ""), (lst["grid"] or "")[:50])
    page.screenshot(path=os.path.join(SHOT, "note-v41-grid-list.png"))

    # 빈 화면 카드를 눌러도 새 다이어리
    page.locator("#s-diary .d41-empty").click()
    page.wait_for_timeout(620)
    ed = editor(page)
    check("빈 화면 카드를 누르면 새 다이어리가 열림", ed["open"] and ed["full"], ed["open"])
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(460)

    # ==================================================================
    # 5. 모눈종이 풀스크린 다이어리
    # ==================================================================
    open_new_diary(page)
    ed = editor(page)
    d = time.localtime()
    stamp = "%d.%02d %s" % (d.tm_mon, d.tm_mday, ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"][d.tm_wday])
    check("새 다이어리는 화면을 꽉 채움", ed["open"] and ed["full"] and ed["h"] >= int(ed["vh"] * 0.98),
          (ed["h"], ed["vh"]))
    check("위에 ‹ 뒤로 · 가운데 「새 다이어리」 · «저장» 단추는 없음(나가면 자동 저장)", ed["back"] and ed["noSave"]
          and ed["titlePh"] == "새 다이어리", (ed["back"], ed["save"], ed["titlePh"]))
    check("큰 날짜는 「11.21 SAT」 꼴", ed["date"] == stamp, (ed["date"], stamp))
    check("날짜 줄을 눌러 바꿀 수 있는 날짜 칸이 있음",
          re.match(r"^\d{4}-\d{2}-\d{2}$", ed["dateVal"] or "") is not None, ed["dateVal"])
    check("본문 칸이 모눈 바탕", "linear-gradient" in (ed["paper"] or ""), (ed["paper"] or "")[:50])
    check("아래에 펜 · 글씨(T) · 사진 도구", ed["tools"] == ["펜 그리기", "글씨", "사진 넣기"], ed["tools"])

    # 날짜 바꾸기
    page.fill("#sheet input[name=date]", "2026-11-19")
    page.wait_for_timeout(420)
    check("날짜를 바꾸면 「11.19 THU」로 바뀜",
          page.evaluate("document.getElementById('d41DateBig').textContent") == "11.19 THU",
          page.evaluate("document.getElementById('d41DateBig').textContent"))

    # ==================================================================
    # 6. T — 종이를 눌러 그 자리에 글 · 크기 슬라이더 · 색·정렬
    #    (v42: 한 덩어리 본문 → 자유 배치 글 상자)
    # ==================================================================
    page.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page.wait_for_timeout(300)
    tp = page.evaluate("""() => ({
      open: !document.getElementById('d41Panel').hidden,
      align: !!document.querySelector('#sheet .d41-tb[data-act=d41Align]'),
      b: !!document.querySelector('#sheet .d41-tb[data-act=d41Bold]'),
      s: !!document.querySelector('#sheet .d41-tb[data-act=d41Strike]'),
      u: !!document.querySelector('#sheet .d41-tb[data-act=d41Underline]'),
      tc: !!document.querySelector('#sheet .d41-tc[data-act=d41ColorPick]'),
      minus: !!document.querySelector('#sheet [data-act=d41SizeStep][data-d="-1"]'),
      plus: !!document.querySelector('#sheet [data-act=d41SizeStep][data-d="1"]'),
      pv: (document.querySelector('#sheet .d41-pv') || {}).textContent || ''})""")
    check("T 를 누르면 새 글 상자와 함께 글씨 도구 두 줄(정렬·B·S·U·색 / − 크기 +)이 열림",
          tp["open"] and tp["align"] and tp["b"] and tp["s"] and tp["u"] and tp["tc"]
          and tp["minus"] and tp["plus"], tp)

    page.keyboard.type("아침에 창문을 열었더니 바람이 차가웠다")
    page.wait_for_timeout(300)
    t1 = page.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value)[0] || {};
      return {n: document.querySelectorAll('#sheet .d41-tx').length, x: t.x, y: t.y, text: t.text}; }""")
    check("T 로 만든 글 상자에 바로 써짐",
          t1["n"] == 1 and 0 < t1["x"] < 1 and t1["y"] > 0 and "바람이 차가웠다" in (t1["text"] or ""), t1)

    page.locator("#sheet .d41-tb[data-act=d41Align]").click()
    page.wait_for_timeout(180)
    page.locator("#sheet .d41-tb[data-act=d41Bold]").click()
    page.wait_for_timeout(180)
    page.locator("#sheet .d41-tc[data-act=d41ColorPick]").click()
    page.wait_for_timeout(180)
    page.locator("#sheet .d41-dot[data-act=d41Color]").nth(2).click()
    page.wait_for_timeout(180)
    page.locator("#sheet [data-act=d41SizeStep][data-d='1']").click()
    page.locator("#sheet [data-act=d41SizeStep][data-d='1']").click()
    page.locator("#sheet [data-act=d41SizeStep][data-d='1']").click()
    page.wait_for_timeout(280)
    sty = page.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value)[0];
      const el = document.querySelector('#sheet .d41-tx');
      return {size: t.size, align: t.align, color: t.color, bold: t.bold,
              fs: Math.round(parseFloat(getComputedStyle(el).fontSize)),
              ta: getComputedStyle(el).textAlign, fw: getComputedStyle(el).fontWeight}; }""")
    check("정렬(가운데)·굵게·색·−+ 크기가 그 글 상자에 바로 반영",
          sty["size"] == 20 and sty["fs"] == 20 and sty["ta"] == "center"
          and sty["color"] != "" and sty["bold"] == 1 and sty["fw"] in ("700", "bold"), sty)
    page.screenshot(path=os.path.join(SHOT, "note-v41-diary-editor.png"))

    # ==================================================================
    # 7. 사진 — 붙이면 손으로 옮기고 모서리로 크기 조절
    # ==================================================================
    import base64 as _b64
    def _make_img(page, w, h, name):
        durl = page.evaluate("""([w, h]) => { const c = document.createElement('canvas'); c.width = w; c.height = h;
          const x = c.getContext('2d'); x.fillStyle = '#D69678'; x.fillRect(0, 0, w, h);
          x.fillStyle = '#5A6E82'; x.fillRect(w / 8, h / 6, w * 3 / 4, h * 2 / 3);
          return c.toDataURL('image/jpeg', 0.9); }""", [w, h])
        path = "/tmp/%s" % name
        with open(path, "wb") as f:
            f.write(_b64.b64decode(durl.split(",", 1)[1]))
        return path

    img_a = _make_img(page, 320, 240, "v41-a.jpg")
    img_b = _make_img(page, 240, 320, "v41-b.jpg")
    page.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    page.wait_for_timeout(200)
    page.set_input_files("#d41ImgIn", [img_a, img_b])
    page.wait_for_timeout(1800)
    ph = page.evaluate("""() => ({n: document.querySelectorAll('#sheet .d41-imgb').length,
      hidden: JSON.parse(document.getElementById('d41ImgsIn').value).map(i => [i.x, i.y, i.w]),
      src: String((JSON.parse(document.getElementById('d41ImgsIn').value)[0] || {}).src || '').slice(0, 22)})""")
    check("사진 두 장을 붙이면 다이어리에 두 칸", ph["n"] == 2 and len(ph["hidden"]) == 2, ph["n"])
    check("붙인 사진은 줄여서(data:image) · 자리(x·y·폭)와 함께 보관",
          ph["src"].startswith("data:image") and all(0 <= row[0] <= 1 and 0 <= row[2] <= 1 and row[1] >= 0 for row in ph["hidden"]), ph["hidden"])

    # 사진을 눌러 고르면 자르기·삭제 칸, 모서리를 끌면 폭이 바뀜
    ib = page.locator("#sheet .d41-imgb").first.bounding_box()
    page.mouse.click(ib["x"] + 24, ib["y"] + 24)
    page.wait_for_timeout(320)
    sel = page.evaluate("""() => ({sel: document.querySelectorAll('#sheet .d41-imgb.sel').length,
      panel: (document.getElementById('d41Panel') || {}).innerText || '',
      handle: !!document.querySelector('#sheet .d41-imgb.sel .d41-rz'),
      w: JSON.parse(document.getElementById('d41ImgsIn').value)[0].w})""")
    check("사진을 누르면 「자르기·삭제」 칸과 크기 손잡이가 보임",
          sel["sel"] == 1 and "자르기" in sel["panel"] and sel["handle"], sel)
    w0 = sel["w"]
    hb = page.locator("#sheet .d41-imgb.sel .d41-rz").bounding_box()
    page.mouse.move(hb["x"] + hb["width"] / 2, hb["y"] + hb["height"] / 2)
    page.mouse.down()
    page.mouse.move(hb["x"] + hb["width"] / 2 - 70, hb["y"] + hb["height"] / 2 - 50, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    w1 = page.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].w")
    check("모서리를 끌어 사진 크기를 줄임", w1 < w0 - 0.05, (w0, w1))

    # 사진을 끌어 옮기기
    ib2 = page.locator("#sheet .d41-imgb").first.bounding_box()
    x0 = page.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].x")
    page.mouse.move(ib2["x"] + 20, ib2["y"] + 20)
    page.mouse.down()
    page.mouse.move(ib2["x"] + 90, ib2["y"] + 120, steps=8)
    page.mouse.up()
    page.wait_for_timeout(400)
    x1 = page.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].x")
    check("사진을 손으로 끌어 옮김", x1 > x0 + 0.05, (x0, x1))

    # 자르기 — 사진 위를 끌어 영역을 정하고 적용하면 실제로 잘림
    ib3 = page.locator("#sheet .d41-imgb").first.bounding_box()
    page.mouse.click(ib3["x"] + 30, ib3["y"] + 30)
    page.wait_for_timeout(300)
    page.locator("#d41Panel [data-act=d41ImgCrop]").first.click()
    page.wait_for_timeout(500)
    crop_open = page.evaluate("!!document.getElementById('d41CropWrap')")
    # v43: 자르기 테두리(손잡이)를 끌어 영역을 정해요 — 그냥 누르면 사진은 그대로
    hb = page.evaluate("""() => { const f = document.getElementById('d41CropFrame').getBoundingClientRect();
      const h = document.querySelector('#d41CropWrap .d41-ch-se').getBoundingClientRect();
      return [h.x + h.width / 2, h.y + h.height / 2, f.x, f.y, f.width, f.height]; }""")
    page.mouse.move(hb[0], hb[1])
    page.mouse.down()
    page.mouse.move(hb[2] + hb[4] * 0.6, hb[3] + hb[5] * 0.6, steps=6)
    page.mouse.up()
    page.wait_for_timeout(260)
    before = page.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img');
      return [i.naturalWidth, i.naturalHeight]; }""")
    page.locator("#d41CropWrap [data-crop=apply]").click()
    page.wait_for_timeout(700)
    after = page.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img');
      return i ? [i.naturalWidth, i.naturalHeight] : null; }""")
    check("사진 자르기 창이 열리고 적용하면 실제로 잘림", crop_open and after and after[0] < before[0],
          (before, after))

    # 펜
    page.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page.wait_for_timeout(300)
    pen_on = page.evaluate("""() => ({on: document.getElementById('d41Pen').classList.contains('on'),
      texts: [...document.querySelectorAll('#sheet .d41-prow-dock .d41-pl')].length,
      pens: [...document.querySelectorAll('#sheet .d41-dk')].map(b => b.getAttribute('aria-label')),
      undoInTools: !!document.querySelector('#sheet .d41-tools #d41UndoBtn'),
      undoInTop: !!document.querySelector('#sheet .d41-top #d41UndoBtn')})""")
    # v45: 글씨 라벨 없는 한 줄 그림 도크 · 되돌리기는 펜 옆 도구 줄로
    check("펜을 누르면 한 줄짜리 그림 도크가 열림 (글씨 라벨 없음)",
          pen_on["on"] and pen_on["pens"] == ["가는 펜", "일반 펜", "형광펜", "지우개", "펜 색", "전체 지우기"]
          and pen_on["texts"] == 0, pen_on["pens"])
    check("되돌리기는 위 줄이 아니라 펜 옆 도구 줄에", pen_on["undoInTools"] and not pen_on["undoInTop"], pen_on)
    box = page.locator("#d41Paper").bounding_box()
    sx, sy = box["x"] + 70, box["y"] + 520

    def draw(dx=0, dy=0, steps=10):
        page.mouse.move(sx + dx, sy + dy)
        page.mouse.down()
        for i in range(1, steps + 1):
            page.mouse.move(sx + dx + i * 11, sy + dy + i * 5)
            page.wait_for_timeout(16)
        page.mouse.up()
        page.wait_for_timeout(300)

    draw()
    pen1 = page.evaluate("""() => ({paths: document.querySelectorAll('#d41Pen path').length,
      saved: JSON.parse(document.getElementById('d41PenIn').value)})""")
    pts = (pen1["saved"][0]["p"] if pen1["saved"] else [])
    check("손가락(마우스)으로 그리면 선이 그려지고 저장 준비됨", pen1["paths"] == 1 and len(pen1["saved"]) == 1, pen1["paths"])
    check("그림 좌표는 폭 기준 (0~1 비율 · 아래로는 종이 길이만큼)",
          len(pts) >= 4 and all(0 <= pts[i] <= 1 for i in range(0, len(pts), 2))
          and all(pts[i] >= 0 for i in range(1, len(pts), 2)), pts[:6])
    page.locator("#d41UndoBtn").click()
    page.wait_for_timeout(300)
    check("되돌리기(↶ · 펜 옆)로 마지막 선이 지워짐",
          page.evaluate("document.querySelectorAll('#d41Pen path').length") == 0)
    draw()
    page.screenshot(path=os.path.join(SHOT, "_p41-test-pen.png"))

    # ==================================================================
    # 8. 저장 — 카드에 반영 · 다시 열어 이어 쓰기
    # ==================================================================
    page.fill("#sheet .d41-title", "비 오는 목요일")
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(900)
    card = page.evaluate("""() => { const c = document.querySelector('#s-diary .d41-card');
      return c ? {date: (c.querySelector('.nmemo-date') || {}).textContent,
                  title: (c.querySelector('.nmemo-t') || {}).textContent,
                  body: (c.querySelector('.nmemo-b') || {}).textContent,
                  thumbs: c.querySelectorAll('.d41-th').length,
                  pen: (c.querySelector('.d41-penz') || {}).textContent,
                  del: !!c.querySelector('.nmemo-x')} : null; }""")
    check("저장하면 카드에 날짜·제목·본문이 보임",
          card and card["date"] == "2026.11.19 목요일" and card["title"] == "비 오는 목요일"
          and "바람이 차가웠다" in (card["body"] or ""), card)
    check("카드에 사진 미리보기와 손그림 표시", card and card["thumbs"] == 2 and "손그림" in (card["pen"] or ""), card)
    check("카드 오른쪽에 × 삭제 버튼", card and card["del"] is True)
    saved = state_list(page, "주말 기록")["items"][0]
    check("저장된 값 — 글 상자·사진 두 장·펜 한 줄·날짜",
          len(saved.get("texts", [])) == 1 and len(saved.get("imgs", [])) == 2
          and len(saved.get("pen", [])) == 1 and saved.get("date") == "2026-11-19",
          {k: saved.get(k) for k in ("date",)})

    page.locator("#s-diary .d41-card").first.click()
    page.wait_for_timeout(700)
    again = page.evaluate("""() => ({title: document.querySelector('.d41-title').value,
      texts: JSON.parse(document.getElementById('d41TextsIn').value),
      date: document.getElementById('d41DateBig').textContent,
      imgs: document.querySelectorAll('#sheet .d41-imgb').length,
      paths: document.querySelectorAll('#d41Pen path').length})""")
    check("카드를 누르면 그 다이어리가 그대로 열림 (제목·글·날짜·사진·그림)",
          again["title"] == "비 오는 목요일" and "바람이 차가웠다" in (again["texts"][0]["text"] if again["texts"] else "")
          and again["date"] == "11.19 THU" and again["imgs"] == 2 and again["paths"] == 1, again)
    page.screenshot(path=os.path.join(SHOT, "_p41-test-reopen.png"))

    # 이어 쓰기 · 사진 한 장 삭제
    # v44: 이미 쓴 다이어리는 보기(스크롤)로 열리고, 종이를 한 번 누르면 고치기로 바뀜
    vEdit = page.evaluate("""() => ({editing: window.TwoLogUI && !!document.querySelector('#sheet .d41-txt[contenteditable="false"]'),
      toolsHidden: document.querySelector('#sheet .d41-tools').hidden})""")
    check("다시 열면 보기(스크롤) 모드 — 글 상자는 고칠 수 없고 도구 바는 숨음",
          vEdit["editing"] and vEdit["toolsHidden"], vEdit)
    page.locator("#d41Paper").click()
    page.wait_for_timeout(360)
    vEdit2 = page.evaluate("""() => ({editable: document.querySelector('#sheet .d41-txt[contenteditable="true"]') !== null,
      toolsShown: !document.querySelector('#sheet .d41-tools').hidden})""")
    check("종이를 한 번 누르면 고치기로 바뀌어요 (도구 바가 나타남)",
          vEdit2["editable"] and vEdit2["toolsShown"], vEdit2)
    # v43: 한 번 누르면 «고르기»만 — 한 번 더 톡 누르면 입력(키보드)
    page.locator("#sheet .d41-tx .d41-txt").first.click()
    page.wait_for_timeout(60)
    page.locator("#sheet .d41-tx .d41-txt").first.click()
    page.wait_for_timeout(260)
    page.keyboard.press("End")
    page.keyboard.type(" 저녁엔 산책")
    page.wait_for_timeout(260)
    ibx = page.locator("#sheet .d41-imgb").first.bounding_box()
    page.mouse.click(ibx["x"] + 20, ibx["y"] + 20)
    page.wait_for_timeout(300)
    page.locator("#sheet .d41-imgb.sel .d41-imgx").first.click()
    page.wait_for_timeout(400)
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(800)
    edited = state_list(page, "주말 기록")["items"][0]
    check("다시 열어 고친 글·지운 사진이 저장됨",
          "산책" in (edited.get("memo", "")) and len(edited.get("imgs", [])) == 1, edited.get("imgs"))

    # 카드 × 로 다이어리 삭제
    page.locator("#s-diary .d41-card .nmemo-x").first.click()
    page.wait_for_timeout(700)
    gone = page.evaluate("""() => ({cards: document.querySelectorAll('#s-diary .d41-card').length,
      items: (window.__app.state.lists.filter(l => l.title === '주말 기록')[0] || {items: []}).items.length,
      empty: !!document.querySelector('#s-diary .d41-empty')})""")
    check("카드 × 로 지우면 다이어리와 내용이 함께 사라짐",
          gone["cards"] == 0 and gone["items"] == 0 and gone["empty"], gone)

    # 다크 모드에서도 모눈
    open_new_diary(page)
    page.evaluate("document.documentElement.setAttribute('data-mode', 'dark')")
    page.wait_for_timeout(350)
    dark = page.evaluate("""() => { const p = document.querySelector('#sheet .d41-paper');
      const c = document.querySelector('#sheet .d41-canvas');
      return {paper: p ? getComputedStyle(p).backgroundImage : '',
              bg: p ? getComputedStyle(p).backgroundColor : '',
              canvas: c ? Math.round(c.getBoundingClientRect().height) : 0}; }""")
    check("다크 모드에서도 모눈 격자가 보임", "linear-gradient" in (dark["paper"] or ""), dark["bg"])
    page.evaluate("document.documentElement.setAttribute('data-mode', 'light')")
    page.locator("#sheet .d41-back").click()
    page.wait_for_timeout(400)
    check("브라우저 콘솔/페이지 오류 없음 (모눈 메모)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 9. 다른 속지는 그대로 (별점 리뷰 · 지출·정산)
    # ==================================================================
    ctx2 = new_ctx(browser)
    ctx2.add_init_script("window.__TWOLOG_MODE = 'local';")
    page2 = ctx2.new_page()
    errs2 = []
    watch(page2, errs2)
    page2.goto(URL + "?demo=1", wait_until="networkidle")
    page2.wait_for_timeout(700)
    seed2 = page2.evaluate("JSON.stringify(window.__app.state)")
    page2.goto(URL, wait_until="domcontentloaded")
    page2.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed2)
    page2.reload(wait_until="networkidle")
    page2.wait_for_timeout(900)
    note_tab(page2)

    create_kind(page2, "맛집 기록", "review")
    page2.fill("#s-diary #listQuickForm input[name=text]", "성수 카페")
    page2.locator("#s-diary #listQuickForm button").click()
    page2.wait_for_timeout(480)
    rv = page2.evaluate("""() => ({badge: !!document.querySelector('#s-diary .note-hd .k'),
      cards: document.querySelectorAll('#s-diary .rv-card').length,
      stars: document.querySelectorAll('#s-diary .rv-card .rvs').length})""")
    check("별점 리뷰 속지는 그대로 (배지 없음 · 별 5개)", rv["badge"] is False and rv["cards"] == 1 and rv["stars"] == 5, rv)

    create_kind(page2, "데이트 통장", "expense")
    page2.locator("#s-diary .exp-act[data-tx='expense']").click()
    page2.wait_for_timeout(460)
    page2.fill("#sheet input[name=amount]", "24000")
    page2.locator("#sheet .exp-cat[data-cat='식비']").click()
    page2.fill("#sheet input[name=memo]", "점심")
    page2.locator("#sheet button.btn-primary").click()
    page2.wait_for_timeout(600)
    ex = page2.evaluate("""() => ({badge: !!document.querySelector('#s-diary .note-hd .k'),
      sum: (document.querySelector('#s-diary .exp-spent') || {}).textContent,
      rows: document.querySelectorAll('#s-diary .exp-row').length})""")
    check("지출·정산 속지는 그대로 (사용 금액 계산)", ex["badge"] is False and ex["sum"] == "₩24,000" and ex["rows"] == 1, ex)
    check("브라우저 콘솔/페이지 오류 없음 (다른 속지)", len(errs2) == 0, errs2[:4])
    ctx2.close()

    # ==================================================================
    # 9-2. 투두리스트 「+ 새 리스트」 → 바로 카드 시트 (제목·제목 색·To-do)
    # ==================================================================
    ctx9 = new_ctx(browser)
    ctx9.add_init_script("window.__TWOLOG_MODE = 'local';")
    page9 = ctx9.new_page()
    errs9 = []
    watch(page9, errs9)
    page9.goto(URL + "?demo=1", wait_until="networkidle")
    page9.wait_for_timeout(700)
    seed9 = page9.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")
    page9.goto(URL, wait_until="domcontentloaded")
    page9.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", seed9)
    page9.reload(wait_until="networkidle")
    page9.wait_for_timeout(900)
    note_tab(page9)
    n_before = page9.evaluate("() => (window.__app.state.groups['todo'] || []).length")
    page9.locator("#s-diary .ngrid .ncard.new").click()
    page9.wait_for_timeout(620)
    nc = page9.evaluate("""() => ({
      title: !!document.querySelector('#sheet input[name=title]'),
      labels: [...document.querySelectorAll('#sheet .card-meta label')].map(l => l.textContent),
      colors: document.querySelectorAll('#sheet .cp.ccp .sw').length,
      colorLbl: (document.querySelector('#sheet .cp.ccp .cp-hd span') || {}).textContent,
      todo: !!document.querySelector('#sheet #listAddForm input[name=text]'),
      todoLbl: (document.querySelector('#sheet .todo-label') || {}).textContent,
      save: (document.querySelector('#sheetForm button[type=submit]') || {}).textContent,
      del: !!document.querySelector('#sheet .btn-del'),
      rows: document.querySelectorAll('#sheet .card-items .trow').length})""")
    check("「+ 새 리스트」를 누르면 바로 카드 시트 (제목·제목 색·To-do·저장하기)",
          nc["title"] and nc["labels"] == ["제목"] and nc["colors"] >= 12 and nc["todo"]
          and nc["todoLbl"] == "To-do" and nc["save"] == "저장하기", nc)
    check("새 카드에는 「카드 삭제」 없이 저장하기만", nc["del"] is False, nc["del"])

    page9.fill("#sheet input[name=title]", "장보기")
    page9.locator("#sheet .cp.ccp .sw").nth(3).click()
    page9.wait_for_timeout(250)
    page9.fill("#sheet #listAddForm input[name=text]", "우유")
    page9.locator("#sheet #listAddForm .todo-add-btn").click()
    page9.wait_for_timeout(380)
    page9.fill("#sheet #listAddForm input[name=text]", "계란")
    page9.press("#sheet #listAddForm input[name=text]", "Enter")
    page9.wait_for_timeout(380)
    mid = page9.evaluate("""() => ({rows: document.querySelectorAll('#sheet .card-items .trow').length,
      groups: (window.__app.state.groups['todo'] || []).length})""")
    check("저장 전에 To-do 두 개를 Add·엔터로 넣음 (카드는 아직 안 만들어짐)",
          mid["rows"] == 2 and mid["groups"] == n_before, mid)
    page9.screenshot(path=os.path.join(SHOT, "_p41-newcard.png"))
    page9.locator("#sheetForm button[type=submit]").click()
    page9.wait_for_timeout(820)
    made = page9.evaluate("""() => { const gs = window.__app.state.groups['todo'] || [];
      const last = gs[gs.length - 1] || {};
      return {n: gs.length, title: last.title, bg: String(last.titleBg || ''),
              items: (window.__app.state.todos || []).filter(t => t.gid === last.id).map(t => t.text),
              cards: [...document.querySelectorAll('#s-diary .ncard:not(.new) .nc-t')].map(x => x.textContent)}; }""")
    check("제목·색·항목을 한 번에 저장하면 카드가 만들어짐",
          made["n"] == n_before + 1 and made["title"] == "장보기" and made["bg"].startswith("#")
          and made["items"] == ["우유", "계란"] and "장보기" in made["cards"], made)

    # 제목 없이 항목만 → 기본 이름으로
    page9.locator("#s-diary .ngrid .ncard.new").click()
    page9.wait_for_timeout(520)
    page9.fill("#sheet #listAddForm input[name=text]", "메모만")
    page9.locator("#sheet #listAddForm .todo-add-btn").click()
    page9.wait_for_timeout(320)
    page9.locator("#sheetForm button[type=submit]").click()
    page9.wait_for_timeout(760)
    auto = page9.evaluate("() => (window.__app.state.groups['todo'] || []).map(g => g.title)")
    check("제목 없이 항목만 넣어도 기본 이름으로 카드가 만들어짐", "새 리스트" in auto, auto)

    # 그냥 닫으면 빈 카드가 남지 않음
    n0 = page9.evaluate("() => (window.__app.state.groups['todo'] || []).length")
    page9.locator("#s-diary .ngrid .ncard.new").click()
    page9.wait_for_timeout(520)
    page9.fill("#sheet #listAddForm input[name=text]", "버릴 항목")
    page9.locator("#sheet #listAddForm .todo-add-btn").click()
    page9.wait_for_timeout(320)
    page9.locator("#sheet .sheet-hd .icon-btn").click()
    page9.wait_for_timeout(620)
    left = page9.evaluate("""() => ({groups: (window.__app.state.groups['todo'] || []).length,
      stray: (window.__app.state.todos || []).filter(t => t.text === '버릴 항목').length})""")
    check("× 로 그냥 닫으면 카드도 항목도 남지 않음", left["groups"] == n0 and left["stray"] == 0, left)
    check("브라우저 콘솔/페이지 오류 없음 (새 카드)", len(errs9) == 0, errs9[:4])
    ctx9.close()

    # ==================================================================
    # 10. 사진 — 날짜(챕터) 댓글 한 칸 (사진마다 카드 없음)
    # ==================================================================
    ctx5 = new_ctx(browser)
    ctx5.add_init_script("window.__TWOLOG_MODE = 'local';")
    page5 = ctx5.new_page()
    errs5 = []
    watch(page5, errs5)
    page5.goto(URL + "?demo=1", wait_until="networkidle")
    page5.wait_for_timeout(700)
    seed5 = page5.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")
    page5.goto(URL, wait_until="domcontentloaded")
    page5.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", seed5)
    page5.reload(wait_until="networkidle")
    page5.wait_for_timeout(900)
    tab(page5, 3, 720)
    day5 = page5.evaluate("() => { const h = document.querySelector('#s-photo .pday-hd'); return h ? h.getAttribute('data-date') : ''; }")
    ids5 = page5.evaluate("(d) => (window.__app.state.photos || []).filter(p => String(p.date||'').slice(0,10) === d).map(p => p.id)", day5)
    # 예전(v40)에 사진마다 달아 둔 댓글도 그 날짜 칸에 모여 보이는지 — 서로 다른 두 사진에 하나씩
    page5.evaluate("""(o) => { const st = window.__app.state;
      st.photos.forEach(p => {
        if (p.id === o.ids[0]) p.comments = [{ id: 'c-old-1', who: 'you', text: '여기 진짜 좋았다', at: new Date().toISOString(), replies: [] }];
        if (p.id === o.ids[1]) p.comments = [{ id: 'c-old-2', who: 'me', text: '다음에 또 오자', at: new Date().toISOString(), replies: [] }];
      }); }""", {"ids": ids5})
    page5.evaluate("() => localStorage.setItem('twolog:v1:state', JSON.stringify(window.__app.state))")
    page5.reload(wait_until="networkidle")
    page5.wait_for_timeout(900)
    tab(page5, 3, 720)
    page5.locator("#s-photo .pday-hd[data-date='%s']" % day5).click()
    page5.wait_for_timeout(780)
    ch = page5.evaluate("""() => ({cells: document.querySelectorAll('#s-photo .dg-cell').length,
      blocks: document.querySelectorAll('#s-photo .dcmt').length,
      forms: document.querySelectorAll('#s-photo .dcmt .cmt-form').length,
      heads: document.querySelectorAll('#s-photo .dcmt-hd, #s-photo .dcmt-ti, #s-photo .dcmt-c, #s-photo .dcmt-th').length,
      empty: ((document.querySelector('#s-photo .dcmt') || {}).textContent || '').indexOf('아직 댓글이 없어요') >= 0,
      av: !!document.querySelector('#s-photo .dcmt .cmt-form .av, #s-photo .dcmt .cmt-form .av-img'),
      ph: (document.querySelector('#s-photo .dcmt .cmt-in') || {}).placeholder,
      send: (document.querySelector('#s-photo .dcmt .cmt-send') || {}).textContent,
      rows: [...document.querySelectorAll('#s-photo .dcmt .cmt .cmt-t')].map(t => t.textContent)}) """)
    check("날짜 모아보기의 댓글 칸은 하나 (사진마다 카드 없음)",
          ch["cells"] >= 3 and ch["blocks"] == 1 and ch["forms"] == 1, ch)
    check("「1번째 사진」 카드 머리·「아직 댓글이 없어요」 문구가 없음",
          ch["heads"] == 0 and ch["empty"] is False, (ch["heads"], ch["empty"]))
    check("작성자 프사 + 「댓글 달기」 + 「등록」이 바로 보임",
          ch["av"] and ch["ph"] == "댓글 달기" and ch["send"] == "등록", (ch["av"], ch["ph"], ch["send"]))
    check("예전에 사진마다 달았던 댓글도 그 날짜 칸에 모여 보임",
          sorted(ch["rows"]) == sorted(["여기 진짜 좋았다", "다음에 또 오자"]), ch["rows"])
    page5.screenshot(path=os.path.join(SHOT, "photo-v41-comments.png"))

    # 새 댓글 · 답글 — 한 칸 아래로 쌓여요
    page5.locator("#s-photo .dcmt .cmt-in").fill("우리 둘 다 웃고 있네")
    page5.locator("#s-photo .dcmt .cmt-send").click()
    page5.wait_for_timeout(720)
    c1 = page5.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      const rows = [...sec.querySelectorAll('.cmt')];
      const mine = rows.filter(r => ((r.querySelector('.cmt-t') || {}).textContent || '') === '우리 둘 다 웃고 있네');
      const row = mine[0];
      return {n: rows.length, mine: mine.length,
              name: row ? (row.querySelector('.cmt-h b') || {}).textContent : null,
              av: row ? !!row.querySelector('.av, .av-img') : false,
              time: row ? (row.querySelector('.cmt-h span') || {}).textContent : '',
              del: row ? !!row.querySelector('button[data-act="cmtDel"]') : false}; }""")
    check("날짜 칸에 새 댓글이 프사·이름·시각과 함께 쌓임",
          c1["n"] == 3 and c1["mine"] == 1 and c1["name"] == "소영"
          and c1["av"] and (c1["time"] or "").startswith("오") and c1["del"], c1)
    page5.locator("#s-photo .dcmt .cmt").filter(has_text="우리 둘 다 웃고 있네").first.locator("button[data-act='cmtReply']").click()
    page5.wait_for_timeout(380)
    page5.locator("#s-photo .dcmt .cmt-in").fill("이 사진 인화하자")
    page5.locator("#s-photo .dcmt .cmt-send").click()
    page5.wait_for_timeout(720)
    c2 = page5.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      const re = [...sec.querySelectorAll('.cmt.re')];
      const last = re[re.length - 1];
      const first = sec.querySelector('.cmt');
      return {re: re.length, to: last ? (last.querySelector('.cmt-to') || {}).textContent : '',
              text: last ? (last.querySelector('.cmt-t') || {}).textContent : '',
              indent: (last && first) ? Math.round(last.getBoundingClientRect().left - first.getBoundingClientRect().left) : 0}; }""")
    check("답글을 달면 그 댓글 아래에 들여쓰여 붙음 (@이름)",
          c2["re"] == 1 and c2["indent"] >= 14 and c2["to"] == "@소영" and "인화하자" in (c2["text"] or ""), c2)
    stored = page5.evaluate("""() => { const st = window.__app.state;
      const n = st.photos.reduce((k, p) => k + ((p.comments || []).length), 0);
      const rep = st.photos.filter(p => (p.comments || []).some(c => c.text === '우리 둘 다 웃고 있네'))[0];
      const re = st.photos.reduce((k, p) => k + ((p.comments || []).reduce((m, c) => m + ((c.replies || []).length), 0)), 0);
      return {threads: n, replies: re, onRep: !!rep}; }""")
    check("새 댓글은 그 날짜 사진에 하나의 댓글 줄로 저장됨",
          stored["threads"] == 3 and stored["replies"] == 1 and stored["onRep"], stored)
    page5.screenshot(path=os.path.join(SHOT, "photo-v41-comments.png"))
    check("브라우저 콘솔/페이지 오류 없음 (날짜 댓글)", len(errs5) == 0, errs5[:4])
    ctx5.close()

    # ==================================================================
    # 10-2. 사진 추가/수정 시트 — 기록 이름 + 날짜 한 줄 · 6열 네모 그리드
    # ==================================================================
    ctxA = new_ctx(browser)
    ctxA.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageA = ctxA.new_page()
    errsA = []
    watch(pageA, errsA)
    pageA.goto(URL + "?demo=1", wait_until="networkidle")
    pageA.wait_for_timeout(700)
    seedA = pageA.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")
    pageA.goto(URL, wait_until="domcontentloaded")
    pageA.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", seedA)
    pageA.reload(wait_until="networkidle")
    pageA.wait_for_timeout(900)
    tab(pageA, 3, 760)
    many = []
    for i in range(7):
        pth = "/tmp/v41-grid-%d.jpg" % i
        with open(pth, "wb") as f:
            f.write(bytes.fromhex(JPG_HEX))
        many.append(pth)
    pageA.set_input_files("#photoInput", many)
    pageA.wait_for_timeout(1100)
    g0 = pageA.evaluate("""() => {
      const a = document.querySelector('#sheet input[name=date]');
      const b = document.querySelector('#sheet input[name=album_tag]');
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      const cells = [...document.querySelectorAll('#sheet .up-cell')];
      const grid = document.querySelector('#sheet #upList');
      return {labels: [...document.querySelectorAll('#sheet .up-row label')].map(l => l.textContent),
              stacked: rb.bottom <= ra.top + 2 && Math.abs(ra.left - rb.left) < 2
                       && Math.min(ra.width, rb.width) > 100,
              cells: cells.length, xs: document.querySelectorAll('#sheet .up-cell .up-x').length,
              cols: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
              rows: new Set(cells.map(c => Math.round(c.getBoundingClientRect().top))).size,
              add: !!document.querySelector('#sheet .up-add')}; }""")
    check("사진 추가 시트 — 「기록 이름」 위 · 「날짜」 아래 두 줄 (v45)",
          g0["labels"] == ["기록 이름", "날짜"] and g0["stacked"], g0)
    check("고른 사진은 한 줄에 5개씩 들어가는 네모 그리드 (7장 → 두 줄) — v43",
          g0["cells"] == 7 and g0["cols"] == 5 and g0["rows"] == 2 and g0["xs"] == 7, g0)
    pageA.screenshot(path=os.path.join(SHOT, "photo-v41-editgrid.png"))

    pageA.evaluate("() => document.querySelectorAll('#sheet .up-cell').forEach((c, i) => c.dataset.mk = 'abcdefg'[i])")
    pageA.locator("#sheet .up-cell").nth(0).focus()
    pageA.keyboard.press("ArrowRight")
    pageA.wait_for_timeout(320)
    d1 = pageA.evaluate("() => [...document.querySelectorAll('#sheet .up-cell')].map(c => c.dataset.mk)")
    check("칸에서 → 키로 순서를 옮길 수 있음", d1 == ["b", "a", "c", "d", "e", "f", "g"], d1)
    pageA.locator("#sheet .up-cell").nth(1).locator(".up-x").click()
    pageA.wait_for_timeout(420)
    d0 = pageA.evaluate("""() => ({cells: document.querySelectorAll('#sheet .up-cell').length,
      xs: document.querySelectorAll('#sheet .up-cell .up-x').length,
      left: (document.querySelector('#sheet #upCount') || {}).textContent,
      btn: (document.querySelector('#sheet #upBtn') || {}).textContent}) """)
    check("사진 칸 오른쪽 위 × 로 그 사진만 빠짐 (7 → 6장)",
          d0["cells"] == 6 and d0["xs"] == 6 and d0["left"] == "6" and "6장" in (d0["btn"] or ""), d0)

    # 그날 사진 「사진 수정」 시트도 같은 그리드
    pageA.keyboard.press("Escape")
    pageA.wait_for_timeout(400)
    pageA.locator("#s-photo .pday-hd").last.click()
    pageA.wait_for_timeout(760)
    ed0 = pageA.evaluate("""() => ({cells: document.querySelectorAll('#s-photo .dg-cell').length,
      more: document.querySelectorAll('#s-photo .dg-more').length,
      blocks: document.querySelectorAll('#s-photo .dcmt').length}) """)
    check("날짜 모아보기 — 사진 칸마다 ⋯ 메뉴 없이 사진만(v43), 댓글 칸은 하나",
          ed0["cells"] >= 3 and ed0["more"] == 0 and ed0["blocks"] == 1, ed0)
    pageA.locator('#s-photo [data-act="editPhotoDay"]').click()
    pageA.wait_for_timeout(700)
    ed1 = pageA.evaluate("""() => ({
      labels: [...document.querySelectorAll('#sheet .up-row label')].map(l => l.textContent),
      stacked: (() => { const a = document.querySelector('#sheet input[name=date]');
        const b = document.querySelector('#sheet input[name=album_tag]');
        const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
        return rb.bottom <= ra.top + 2 && Math.abs(ra.left - rb.left) < 2
               && Math.min(ra.width, rb.width) > 100; })(),
      cells: document.querySelectorAll('#sheet .up-cell').length,
      xs: document.querySelectorAll('#sheet .up-cell .up-x').length,
      cols: getComputedStyle(document.querySelector('#sheet #upList')).gridTemplateColumns.split(' ').length}) """)
    check("사진 수정 시트도 「기록 이름」·「날짜」 두 줄 · 5열 그리드 · 칸마다 × (v45)",
          ed1["labels"] == ["기록 이름", "날짜"] and ed1["stacked"]
          and ed1["cells"] == ed0["cells"] and ed1["xs"] == ed1["cells"] and ed1["cols"] == 5, ed1)
    pageA.keyboard.press("Escape")
    pageA.wait_for_timeout(400)
    check("브라우저 콘솔/페이지 오류 없음 (사진 시트)", len(errsA) == 0, errsA[:4])
    ctxA.close()

    # ==================================================================
    # 11. Supabase 스텁 왕복 — 다이어리(사진·글씨·그림)가 서버로
    # ==================================================================
    cid = "couple-v41m"
    uid = "user-v41m"
    mail = "v41@twolog.app"
    diary_db = {
        "users": {uid: {"id": uid, "email": mail, "password": "pw123456"}},
        "couples": [{"id": cid, "invite_code": "482913", "members": [uid],
                     "me": "소영", "you": "준영", "since": "2025-11-19", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "photos": [],
        "notes": [
            {"id": "L41", "couple_id": cid, "kind": "list", "sort": 0, "deleted": False,
             "payload": {"title": "여행 일기", "emoji": "", "kind": "memo", "items": [
                 {"id": "N1", "text": "바다 보러 간 날", "memo": "파도 소리가 좋았다.", "done": False,
                  "date": "2026-11-18",
                  "imgs": [{"id": "P1", "src": "data:image/jpeg;base64,AAAA", "size": 1}],
                  "sty": {"size": 3, "color": "", "align": "center"},
                  "pen": [{"c": "#B4564E", "w": 3.5, "p": [0.1, 0.2, 0.3, 0.4]}]}]}},
        ],
        "settings": [
            {"couple_id": cid, "key": "note_meta",
             "value": {"tabs": {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"},
                                "log": {"e": "", "n": "영화·먹방"}},
                       "order": ["todo", "bucket", "log", "list:L41"], "kinds": {}}},
        ],
        "uploads": [], "seq": 41,
    }

    def remote_seed(db, user_id, email):
        return """(() => {
          if (localStorage.getItem('stub-sb-db')) return;
          localStorage.setItem('stub-sb-db', %s);
          localStorage.setItem('stub-sb-session', JSON.stringify({
            access_token: 't', refresh_token: 'r', user: { id: %s, email: %s } }));
        })();""" % (json.dumps(json.dumps(db, ensure_ascii=False)), json.dumps(user_id), json.dumps(email))

    ctx3 = new_ctx(browser)
    ctx3.add_init_script(remote_seed(diary_db, uid, mail))
    page3 = ctx3.new_page()
    errs3 = []
    watch(page3, errs3)
    stub_route(page3)
    page3.goto(URL, wait_until="domcontentloaded")
    page3.wait_for_selector("#tabbar .tab", timeout=25000)
    page3.wait_for_timeout(2800)
    note_tab(page3)
    page3.locator("#s-diary .lchip", has_text="여행 일기").first.click()
    page3.wait_for_timeout(600)
    srv_card = page3.evaluate("""() => { const c = document.querySelector('#s-diary .d41-card');
      return c ? {date: (c.querySelector('.nmemo-date') || {}).textContent,
                  title: (c.querySelector('.nmemo-t') || {}).textContent,
                  thumbs: c.querySelectorAll('.d41-th').length} : null; }""")
    check("서버에 있던 다이어리가 날짜·제목·사진과 함께 보임",
          srv_card and srv_card["date"] == "2026.11.18 수요일" and srv_card["title"] == "바다 보러 간 날"
          and srv_card["thumbs"] == 1, srv_card)

    page3.locator("#s-diary .d41-card").first.click()
    page3.wait_for_timeout(700)
    srv_open = page3.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value)[0] || {};
      const im = JSON.parse(document.getElementById('d41ImgsIn').value)[0] || {};
      const el = document.querySelector('#sheet .d41-tx');
      return {date: document.getElementById('d41DateBig').textContent,
              text: t.text, imgs: document.querySelectorAll('#sheet .d41-imgb').length,
              w: im.w, paths: document.querySelectorAll('#d41Pen path').length,
              fs: el ? getComputedStyle(el).fontSize : '', ta: el ? getComputedStyle(el).textAlign : ''}; }""")
    check("서버에서 온 사진·글씨·그림이 그대로 열림 (옛 한 덩어리 본문도 첫 글 상자로)",
          srv_open["text"] == "파도 소리가 좋았다." and srv_open["imgs"] == 1
          and srv_open["w"] is not None and srv_open["paths"] == 1
          and srv_open["ta"] == "center", srv_open)

    # 이 폰에서 새 다이어리를 써서 서버로
    page3.locator("#sheet .d41-back").click()
    page3.wait_for_timeout(500)
    page3.locator("#s-diary .d41-new").click()
    page3.wait_for_timeout(650)
    page3.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    page3.wait_for_timeout(200)
    durl3 = page3.evaluate("""() => { const c = document.createElement('canvas'); c.width = 300; c.height = 220;
      const x = c.getContext('2d'); x.fillStyle = '#C9A227'; x.fillRect(0, 0, 300, 220); return c.toDataURL('image/jpeg', 0.9); }""")
    with open("/tmp/v41-srv.jpg", "wb") as f:
        f.write(__import__("base64").b64decode(durl3.split(",", 1)[1]))
    page3.set_input_files("#d41ImgIn", ["/tmp/v41-srv.jpg"])
    page3.wait_for_timeout(1400)
    page3.fill("#sheet .d41-title", "서버로 가는 다이어리")
    pbox3 = page3.locator("#d41Paper").bounding_box()
    page3.mouse.click(pbox3["x"] + 70, pbox3["y"] + 180)
    page3.wait_for_timeout(300)
    page3.keyboard.type("두 폰에서 같이 보이는 기록.")
    page3.wait_for_timeout(200)
    page3.locator("#sheet .d41-back").click()
    page3.wait_for_timeout(2400)
    srv = page3.evaluate("""() => { const row = (window.__stub.notes || []).filter(x => x.kind === 'list')[0];
      const it = row ? (row.payload.items || []).filter(i => i.text === '서버로 가는 다이어리')[0] : null;
      return it ? {imgs: (it.imgs || []).length, src: String((it.imgs || [{}])[0].src || '').slice(0, 11),
                   w: ((it.imgs || [{}])[0] || {}).w, texts: (it.texts || []).length,
                   tx: (((it.texts || [])[0] || {}).text || ''), date: it.date} : null; }""")
    check("새 다이어리의 사진(자리·폭)·글 상자가 notes 행 payload 에 실려 올라감",
          srv and srv["imgs"] == 1 and srv["src"].startswith("data:image") and srv["w"] is not None
          and srv["texts"] == 1 and "두 폰에서" in srv["tx"] and srv["date"] == time.strftime("%Y-%m-%d"), srv)

    page3.reload(wait_until="domcontentloaded")
    page3.wait_for_selector("#tabbar .tab", timeout=25000)
    page3.wait_for_timeout(2600)
    note_tab(page3)
    page3.locator("#s-diary .lchip", has_text="여행 일기").first.click()
    page3.wait_for_timeout(650)
    reloaded = page3.evaluate("""() => ({cards: [...document.querySelectorAll('#s-diary .d41-card .nmemo-t')].map(t => t.textContent),
      thumbs: document.querySelectorAll('#s-diary .d41-card .d41-th').length})""")
    check("새로고침해도 다이어리 두 개와 사진이 그대로",
          sorted(reloaded["cards"]) == sorted(["바다 보러 간 날", "서버로 가는 다이어리"])
          and reloaded["thumbs"] == 2, reloaded)
    db_now = page3.evaluate("() => JSON.parse(localStorage.getItem('stub-sb-db') || 'null')") or diary_db
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errs3) == 0, errs3[:4])
    ctx3.close()

    # 상대 폰에서도 같은 다이어리 (소영이 쓴 글은 준영 폰에서 «소영» 기록으로)
    uid2 = "user-v41p"
    db_now["users"][uid2] = {"id": uid2, "email": "p@twolog.app", "password": "pw123456"}
    db_now["couples"][0]["members"] = [uid, uid2]
    ctx4 = new_ctx(browser)
    ctx4.add_init_script(remote_seed(db_now, uid2, "p@twolog.app"))
    page4 = ctx4.new_page()
    errs4 = []
    watch(page4, errs4)
    stub_route(page4)
    page4.goto(URL, wait_until="domcontentloaded")
    page4.wait_for_selector("#tabbar .tab", timeout=25000)
    page4.wait_for_timeout(2800)
    note_tab(page4)
    page4.locator("#s-diary .lchip", has_text="여행 일기").first.click()
    page4.wait_for_timeout(650)
    other = page4.evaluate("""() => ({me: window.__app.state.couple.me,
      cards: [...document.querySelectorAll('#s-diary .d41-card .nmemo-t')].map(t => t.textContent),
      thumbs: document.querySelectorAll('#s-diary .d41-card .d41-th').length})""")
    check("상대 폰에서도 같은 다이어리와 사진이 보임",
          "서버로 가는 다이어리" in other["cards"] and other["thumbs"] == 2, other)
    check("브라우저 콘솔/페이지 오류 없음 (상대 폰)", len(errs4) == 0, errs4[:4])
    ctx4.close()

    # ==================================================================
    # 12. 사진 날짜(챕터) 댓글 Supabase 왕복 — 두 폰이 같은 댓글을 봐요
    # ==================================================================
    pcid, puid, p2uid = "couple-v41c", "user-v41c", "user-v41d"
    pday = "2026-11-17"
    legacy_memo = "twolog:c:" + json.dumps({"m": "", "c": [
        {"id": "pc1", "who": "me", "text": "서버에 있던 댓글", "at": "2026-11-17T10:00:00.000Z", "replies": []}]},
        ensure_ascii=False)
    photo_db = {
        "users": {puid: {"id": puid, "email": "c@twolog.app", "password": "pw123456"},
                  p2uid: {"id": p2uid, "email": "d@twolog.app", "password": "pw123456"}},
        "couples": [{"id": pcid, "invite_code": "482913", "members": [puid, p2uid],
                     "me": "소영", "you": "준영", "since": "2025-11-19", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "notes": [], "settings": [], "uploads": [], "seq": 41,
        "photos": [
            {"id": "PH1", "couple_id": pcid, "date": pday, "album": "롯데 리조트", "title": "바다",
             "place": "", "memo": legacy_memo, "art": 1, "cap_bg": None, "storage_path": None, "sort": 0},
            {"id": "PH2", "couple_id": pcid, "date": pday, "album": "롯데 리조트", "title": "수영장",
             "place": "", "memo": "", "art": 2, "cap_bg": None, "storage_path": None, "sort": 1},
            {"id": "PH3", "couple_id": pcid, "date": pday, "album": "롯데 리조트", "title": "노을",
             "place": "", "memo": "", "art": 3, "cap_bg": None, "storage_path": None, "sort": 2},
        ],
    }

    ctx6 = new_ctx(browser)
    ctx6.add_init_script(remote_seed(photo_db, puid, "c@twolog.app"))
    page6 = ctx6.new_page()
    errs6 = []
    watch(page6, errs6)
    stub_route(page6)
    page6.goto(URL, wait_until="domcontentloaded")
    page6.wait_for_selector("#tabbar .tab", timeout=25000)
    page6.wait_for_timeout(2800)
    tab(page6, 3, 720)
    page6.locator("#s-photo .pday-hd[data-date='%s']" % pday).click()
    page6.wait_for_timeout(780)
    pc = page6.evaluate("""() => ({cells: document.querySelectorAll('#s-photo .dg-cell').length,
      blocks: document.querySelectorAll('#s-photo .dcmt').length,
      rows: [...document.querySelectorAll('#s-photo .dcmt .cmt .cmt-t')].map(t => t.textContent)}) """)
    check("서버에 있던 댓글이 그 날짜 한 칸에 보임",
          pc["cells"] == 3 and pc["blocks"] == 1 and pc["rows"] == ["서버에 있던 댓글"], pc)

    page6.locator("#s-photo .dcmt .cmt-in").fill("서버로 가는 날짜 댓글")
    page6.locator("#s-photo .dcmt .cmt-send").click()
    page6.wait_for_timeout(2600)
    srvp = page6.evaluate("""() => (window.__stub.photos || []).map(r => ({id: r.id, memo: String(r.memo || '')}))
      .filter(r => r.memo.indexOf('서버로 가는 날짜 댓글') >= 0) """)
    check("새 날짜 댓글이 photos 행 memo 에 실려 올라감",
          len(srvp) == 1 and srvp[0]["memo"].startswith("twolog:c:"), srvp)

    page6.reload(wait_until="domcontentloaded")
    page6.wait_for_selector("#tabbar .tab", timeout=25000)
    page6.wait_for_timeout(2600)
    tab(page6, 3, 720)
    page6.locator("#s-photo .pday-hd[data-date='%s']" % pday).click()
    page6.wait_for_timeout(800)
    after = page6.evaluate("""() => ({rows: [...document.querySelectorAll('#s-photo .dcmt .cmt .cmt-t')].map(t => t.textContent),
      blocks: document.querySelectorAll('#s-photo .dcmt').length}) """)
    check("새로고침해도 날짜 댓글이 그대로 한 칸에",
          after["blocks"] == 1 and sorted(after["rows"]) == sorted(["서버에 있던 댓글", "서버로 가는 날짜 댓글"]), after)
    photo_db_now = page6.evaluate("() => JSON.parse(localStorage.getItem('stub-sb-db') || 'null')") or photo_db
    check("브라우저 콘솔/페이지 오류 없음 (날짜 댓글 동기화)", len(errs6) == 0, errs6[:4])
    ctx6.close()

    # 상대 폰 — 같은 날짜 칸에 소영이 쓴 댓글이 보이고, 남의 댓글엔 삭제 버튼이 없어요
    ctx7 = new_ctx(browser)
    ctx7.add_init_script(remote_seed(photo_db_now, p2uid, "d@twolog.app"))
    page7 = ctx7.new_page()
    errs7 = []
    watch(page7, errs7)
    stub_route(page7)
    page7.goto(URL, wait_until="domcontentloaded")
    page7.wait_for_selector("#tabbar .tab", timeout=25000)
    page7.wait_for_timeout(2800)
    tab(page7, 3, 720)
    page7.locator("#s-photo .pday-hd[data-date='%s']" % pday).click()
    page7.wait_for_timeout(800)
    otherp = page7.evaluate("""() => { const sec = document.querySelector('#s-photo .dcmt');
      const rows = [...sec.querySelectorAll('.cmt')];
      return {you: window.__app.state.couple.you,
              names: rows.map(r => (r.querySelector('.cmt-h b') || {}).textContent),
              texts: rows.map(r => (r.querySelector('.cmt-t') || {}).textContent),
              dels: sec.querySelectorAll('button[data-act="cmtDel"]').length}; }""")
    check("상대 폰에서도 같은 날짜 칸에 댓글이 소영 이름으로 보임",
          "서버로 가는 날짜 댓글" in otherp["texts"] and otherp["you"] in otherp["names"], otherp)
    check("남의 댓글에는 삭제 버튼이 없음", otherp["dels"] == 0, otherp["dels"])
    check("브라우저 콘솔/페이지 오류 없음 (상대 폰 날짜 댓글)", len(errs7) == 0, errs7[:4])
    ctx7.close()

    # ==================================================================
    # 13. 사진첩 목록 — 아이콘 줄은 위에 고정 · 달력에서 돌아오면 맨 아래
    # ==================================================================
    ctx8 = new_ctx(browser)
    ctx8.add_init_script("window.__TWOLOG_MODE = 'local';")
    page8 = ctx8.new_page()
    errs8 = []
    watch(page8, errs8)
    page8.goto(URL + "?demo=1", wait_until="networkidle")
    page8.wait_for_timeout(700)
    seed8 = page8.evaluate("() => JSON.parse(JSON.stringify(window.__app.state))")
    page8.goto(URL, wait_until="domcontentloaded")
    page8.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", seed8)
    page8.reload(wait_until="networkidle")
    page8.wait_for_timeout(700)
    # 스크롤을 확인할 수 있게 지난 2주치 사진을 더 채워요
    page8.evaluate("""() => { const st = window.__app.state; const base = (st.photos || [])[0];
      if (!base) return;
      for (let i = 1; i <= 14; i++) {
        const d = new Date(); d.setDate(d.getDate() - i);
        const ds = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
        st.photos.push(Object.assign({}, base, { id: 'v41scroll-' + i, date: ds, album: '스크롤 확인 ' + i }));
      }
      localStorage.setItem('twolog:v1:state', JSON.stringify(st)); }""")
    page8.reload(wait_until="networkidle")
    page8.wait_for_timeout(900)
    page8.goto(URL, wait_until="domcontentloaded")
    page8.evaluate("(s) => localStorage.setItem('twolog:v1:state', JSON.stringify(s))", seed8)
    page8.reload(wait_until="networkidle")
    page8.wait_for_timeout(900)
    tab(page8, 3, 800)
    page8.evaluate("document.getElementById('screens').scrollTop = 0")
    page8.wait_for_timeout(300)
    page8.evaluate("document.getElementById('screens').scrollTop = 999999")
    page8.wait_for_timeout(600)
    fixed = page8.evaluate("""() => { const box = document.getElementById('screens');
      const br = box.getBoundingClientRect();
      const hd = document.querySelector('#s-photo .hdr');
      const hb = hd.getBoundingClientRect();
      const btns = [...document.querySelectorAll('#s-photo .hdr .round-btn')];
      return {top: Math.round(hb.top - br.top), h: Math.round(hb.height), btns: btns.length,
              seen: btns.filter(b => { const r = b.getBoundingClientRect();
                return r.width > 0 && r.top >= br.top - 2 && r.bottom <= br.top + hb.height + 2; }).length,
              scroll: Math.round(box.scrollTop), days: document.querySelectorAll('#s-photo .pday').length}; }""")
    check("목록을 맨 아래로 내려도 🔍 📅 + 아이콘 줄이 화면 위에 고정",
          fixed["top"] == 0 and fixed["btns"] == 3 and fixed["seen"] == 3 and fixed["scroll"] > 100, fixed)

    page8.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page8.wait_for_timeout(950)
    page8.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page8.wait_for_timeout(1200)
    backb = page8.evaluate("""() => { const box = document.getElementById('screens');
      const br = box.getBoundingClientRect();
      const hds = [...document.querySelectorAll('#s-photo .pday-hd')];
      const last = hds[hds.length - 1];
      const lr = last ? last.getBoundingClientRect() : null;
      return {scroll: Math.round(box.scrollTop),
              free: Math.round(box.scrollHeight - box.clientHeight),
              last: last ? last.getAttribute('data-date') : null,
              visible: lr ? (lr.top >= br.top - 2 && lr.bottom <= br.bottom + 2) : false}; }""")
    check("달력에서 📅 를 눌러 돌아오면 맨 아래(가장 최근 날짜)로",
          backb["free"] - backb["scroll"] <= 4 and backb["visible"], backb)
    check("브라우저 콘솔/페이지 오류 없음 (사진첩 머리줄)", len(errs8) == 0, errs8[:4])
    ctx8.close()

    browser.close()

print()
if fails:
    print("실패 %d개:" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("실패: 없음")
