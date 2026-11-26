"""투로그 v31 확인 — 일정에 고른 색이 저장·동기화·새로고침 뒤에도 그대로 남는지.

고치기 전에는 일정을 추가·수정할 때 고른 색(e.color)이 Supabase events 행으로 올라가지
않아서(memo 칸에는 여러 날 종료일만), 확인을 누르거나 새로고침·실시간 반영이 되면
담당자 기본색(sched)으로 돌아가 버렸습니다.

v31 은 스키마를 바꾸지 않고 events.memo(text) 한 칸에
  {"end":"YYYY-MM-DD","color":"#RRGGBB"}  ← 여러 날 종료일 + 고른 색
을 함께 담고, 예전 행의 «YYYY-MM-DD» 평문 memo 도 그대로 읽습니다.

1) 버전: sw.js 캐시 twolog-v51 · APP_VERSION v51 · My 탭 「버전 v51」
2) 로컬 모드: 시트에서 색을 고르면 상태·달력 색띠에 그 색, 수정 시트에도 그 색이 선택된 채로 열림
   「기본」을 누르면 담당자 색으로 돌아감
3) 원격(대역 서버): 색을 골라 저장 → events 행 memo 에 color 가 들어가고,
   새로고침(pull) 뒤에도 상태·색띠가 고른 색 (예전에는 기본색으로 돌아갔음)
4) 왕복: 하루+색 · 여러 날+색 · 여러 날+색없음 모두 endDate·color 보존
5) 예전 행(평문 «YYYY-MM-DD» memo · 빈 memo)도 종료일이 살아나고 색은 기본색
6) Realtime 으로 상대가 색을 바꾸면 새로 열지 않아도 그 색으로
7) 다른 화면(홈·노트·사진첩·My) 그대로, 콘솔/페이지 오류 없음

    python3 tests/v31.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import datetime, functools, http.server, json, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

STUB = open(os.path.join(HERE, "stub-supabase.js")).read()
ESM = re.compile(r"https://esm\.sh/.*")

CORAL = "#DD785B"      # 코랄
TEAL = "#80A4AA"       # 청록
LEMON = "#EFD353"      # 레몬
MINT = "#B4D8D4"       # 민트
DEFAULT_BOTH = "#625A7F"   # 로컬 기본 상태에서 「함께」 일정의 담당자 색(sched.both)
REMOTE_BOTH = "#D6C5F7"    # 새로 만든 커플 행의 기본 sched.both

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


def stub(page, table):
    return page.evaluate("(t) => (window.__stub && window.__stub[t]) ? window.__stub[t] : []", table)


def signup(page, email, pw):
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', email)
    page.fill('#s-login input[name="password"]', pw)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)


def tab(page, idx, wait=500):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def state_events(page):
    return page.evaluate("""() => {
      const S = (window.TwoLogUI || {}).state || {};
      return (S.events || []).map(e => ({id: e.id, date: e.date, endDate: e.endDate,
        title: e.title, color: e.color === undefined ? '(none)' : e.color, who: e.who}));
    }""")


def bars(page):
    """달력 아래(선택한 날) 일정 줄의 색띠 색 — 제목과 함께"""
    return page.evaluate("""() => Array.from(document.querySelectorAll('#s-cal .daylist .ev')).map(ev => ({
      title: (ev.querySelector('.t') || {}).textContent || '',
      who: (ev.querySelector('.t') || {}).textContent || '',
      bar: (() => { const b = ev.querySelector('.bar'); return b ? getComputedStyle(b).backgroundColor : null; })(),
      dot: (() => { const b = ev.querySelector('.who .av'); return b ? getComputedStyle(b).backgroundColor : null; })()
    }))""")


def pick_color(page, hex6):
    page.locator('#sheet .sw-row[data-sw="evColor"] button[data-act="pickEvColor"][data-color="%s"]' % hex6).click()
    page.wait_for_timeout(200)


def add_event(page, title, color, end=None):
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(350)
    if color:
        pick_color(page, color)
    page.fill('#sheetForm input[name="title"]', title)
    if end:
        page.fill('#sheetForm input[name="end"]', end)
        page.dispatch_event('#sheetForm input[name="end"]', "change")
        page.wait_for_timeout(200)
    page.locator("#evSave").click()
    page.wait_for_timeout(900)


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전 · 코드
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    sync_js = page.request.get(URL + "sync.js").text()
    check("sw.js 캐시 버전 twolog-v51", 'const VERSION = "twolog-v51"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v51", 'var APP_VERSION = "v51"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v51", 'const SHELL = "shell-" + VERSION' in sw)
    check("sync.js: 일정 memo 에 end·color 를 함께 담는 인코더/디코더",
          "function encodeEventMemo" in sync_js and "function decodeEventMemo" in sync_js
          and "memo: encodeEventMemo(e)" in sync_js)
    check("sync.js: 읽을 때 색을 되살림(color: rD.color)", "color: rD.color" in sync_js)
    check("sync.js: 예전 평문 «YYYY-MM-DD» memo 하위 호환 주석", "예전 행: memo 칸에" in sync_js)
    check("sync.js: 중복 지문(sigEvent)이 풀어 읽은 end·color 로 비교",
          "decodeEventMemo(r.memo, r.date)" in sync_js.split("function sigEvent")[1][:220])
    ctx.close()

    # ==================================================================
    # 2. 로컬 모드 — 시트에서 고른 색이 상태·색띠·수정 시트에 그대로
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(700)
    tab(page, 1, 500)

    add_event(page, "색 유지 확인", CORAL)
    st = state_events(page)
    made = [e for e in st if e["title"] == "색 유지 확인"]
    check("로컬: 일정을 만들면 상태에 고른 색이 저장됨", made and made[0]["color"] == CORAL, made)
    check("로컬: 하루짜리 일정의 종료일 = 시작일", made and made[0]["endDate"] == made[0]["date"], made)
    b = [x for x in bars(page) if x["title"].endswith("색 유지 확인")]
    check("로컬: 달력 아래 색띠가 고른 색", b and b[0]["bar"] == rgb(CORAL), b)
    page.screenshot(path=os.path.join(SHOT, "cal-v31-local-color.png"))

    # 수정 시트에 그 색이 선택된 채로 열리고, 바꾼 색도 남는지
    page.locator("#s-cal .daylist .ev-tap", has_text="색 유지 확인").first.click()
    page.wait_for_timeout(450)
    sel = page.evaluate("""() => {
      const s = document.querySelector('#sheet .sw-row[data-sw="evColor"] .sw.sel');
      return {sel: s ? s.getAttribute('data-color') : null,
              hidden: (document.querySelector('#sheet input[name="color"]') || {}).value,
              resetOn: !!document.querySelector('#sheet .cp-reset.on')};
    }""")
    check("수정 시트: 고른 색이 선택된 채로 열림", sel["sel"] == CORAL and sel["hidden"] == CORAL and not sel["resetOn"], sel)
    pick_color(page, TEAL)
    page.locator("#evSave").click()
    page.wait_for_timeout(800)
    st2 = [e for e in state_events(page) if e["title"] == "색 유지 확인"]
    check("수정: 바꾼 색이 상태에 저장됨", st2 and st2[0]["color"] == TEAL, st2)
    b2 = [x for x in bars(page) if x["title"].endswith("색 유지 확인")]
    check("수정: 색띠도 바뀐 색", b2 and b2[0]["bar"] == rgb(TEAL), b2)

    # 여러 날 + 색
    add_event(page, "여러 날 일정", LEMON, end=d(3))
    multi = [e for e in state_events(page) if e["title"] == "여러 날 일정"]
    check("여러 날 일정: 시작/종료/색이 모두 저장됨",
          multi and multi[0]["endDate"] == d(3) and multi[0]["color"] == LEMON, multi)

    # 「기본」을 누르면 담당자 색으로
    page.locator("#s-cal .daylist .ev-tap", has_text="색 유지 확인").first.click()
    page.wait_for_timeout(400)
    page.locator('#sheet .cp-reset[data-act="pickEvColor"]').click()
    page.wait_for_timeout(200)
    page.locator("#evSave").click()
    page.wait_for_timeout(800)
    st3 = [e for e in state_events(page) if e["title"] == "색 유지 확인"]
    b3 = [x for x in bars(page) if x["title"].endswith("색 유지 확인")]
    check("「기본」으로 되돌리면 고른 색이 지워지고 담당자 색",
          st3 and st3[0]["color"] == "" and b3 and b3[0]["bar"] == rgb(DEFAULT_BOTH), (st3, b3))

    # ==================================================================
    # 2b. 노트 카드 시트 안에서 항목 × — 시트는 그대로, 그 자리에서만 지워짐
    # ==================================================================
    tab(page, 2, 700)
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(500)
    for txt in ("지울 항목", "남길 항목"):
        page.fill('#sheet #listAddForm input[name="text"]', txt)
        page.click("#sheet .todo-add-btn")
        page.wait_for_timeout(500)
    page.fill('#sheet #sheetForm input[name="title"]', "카드 제목 적는 중")
    page.wait_for_timeout(200)
    page.screenshot(path=os.path.join(SHOT, "note-v31-card-before-delete.png"))

    def sheet_now():
        return page.evaluate("""() => ({
          open: !!document.querySelector('#sheetWrap') &&
                document.querySelector('#sheetWrap').classList.contains('open'),
          card: !!document.querySelector('#sheet .card-items'),
          items: document.querySelectorAll('#sheet .card-items .trow').length,
          texts: Array.from(document.querySelectorAll('#sheet .card-items .trow .t')).map(e => e.textContent.trim()),
          title: (document.querySelector('#sheet #sheetForm input[name="title"]') || {}).value,
          toast: (document.getElementById('toast') || {}).textContent || '',
          saved: ((window.TwoLogUI.state || {}).todos || []).map(t => t.text)
        })""")

    before_del = sheet_now()
    check("카드 시트: 항목 두 개가 보임", before_del["open"] and before_del["card"] and
          "지울 항목" in before_del["texts"] and "남길 항목" in before_del["texts"], before_del)
    page.locator('#sheet .card-items .trow', has_text="지울 항목").locator("button.x").click()
    page.wait_for_timeout(700)
    after_del = sheet_now()
    check("카드 시트: 항목 × 를 눌러도 시트가 닫히지 않고 열려 있음",
          after_del["open"] and after_del["card"], after_del)
    check("카드 시트: 지운 항목만 사라지고 남긴 항목은 그대로",
          "지울 항목" not in after_del["texts"] and "남길 항목" in after_del["texts"], after_del["texts"])
    check("카드 시트: 적던 카드 제목도 그대로 ('카드 제목 적는 중')",
          after_del["title"] == "카드 제목 적는 중", after_del["title"])
    check("카드 시트: 화면 상태에서도 항목이 지워짐", "지울 항목" not in after_del["saved"], after_del["saved"])
    check("카드 시트: 지웠다는 안내가 뜸", "지웠어요" in after_del["toast"], after_del["toast"])
    page.screenshot(path=os.path.join(SHOT, "note-v31-card-after-delete.png"))

    # 버킷 카드도 같은 동작
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.locator('#s-diary .seg-btn[data-seg="bucket"]').click()
    page.wait_for_timeout(600)
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(500)
    page.fill('#sheet #listAddForm input[name="text"]', "지울 버킷")
    page.click("#sheet .todo-add-btn")
    page.wait_for_timeout(500)
    page.locator('#sheet .card-items .trow', has_text="지울 버킷").locator("button.x").click()
    page.wait_for_timeout(700)
    bucket_after = page.evaluate("""() => ({
      open: document.querySelector('#sheetWrap').classList.contains('open'),
      card: !!document.querySelector('#sheet .card-items'),
      texts: Array.from(document.querySelectorAll('#sheet .card-items .trow .t')).map(e => e.textContent.trim())
    })""")
    check("버킷 카드: 항목 × 를 눌러도 시트가 열린 채로 그 항목만 사라짐",
          bucket_after["open"] and bucket_after["card"] and "지울 버킷" not in bucket_after["texts"],
          bucket_after)

    # 항목 수정 시트(formTodo)의 「삭제」는 예전처럼 시트를 닫음
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.locator('#s-diary .seg-btn[data-seg="todo"]').click()
    page.wait_for_timeout(600)
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(500)
    page.locator('#sheet .card-items .trow', has_text="남길 항목").locator(".body").click()
    page.wait_for_timeout(500)
    page.locator("#sheet .btn-del[data-act=\"delTodo\"]").click()
    page.wait_for_timeout(700)
    edit_del = page.evaluate("""() => ({
      open: document.querySelector('#sheetWrap').classList.contains('open'),
      view: document.querySelector('#s-diary').classList.contains('active'),
      saved: ((window.TwoLogUI.state || {}).todos || []).map(t => t.text)
    })""")
    check("항목 수정 시트의 「삭제」는 예전처럼 닫히면서 지워짐",
          (not edit_del["open"]) and "남길 항목" not in edit_del["saved"], edit_del)
    check("로컬 모드 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 3. 원격(대역) — 저장·새로고침 뒤에도 고른 색 (고치기 전 버그)
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "color.v31@twolog.app", "twolog1234")
    page.wait_for_timeout(1800)
    tab(page, 1, 600)

    add_event(page, "동기화 색 확인", CORAL)
    page.wait_for_timeout(1200)
    rows = [r for r in stub(page, "events") if r.get("title") == "동기화 색 확인"]
    memo = rows[0].get("memo") if rows else None
    parsed = None
    try:
        parsed = json.loads(memo) if memo else None
    except Exception:
        parsed = None
    check("원격: events 행이 하나 만들어짐", len(rows) == 1, rows)
    check("원격: memo 칸에 고른 색이 JSON 으로 올라감", parsed == {"color": CORAL}, memo)
    check("원격: 하루짜리라 end 는 넣지 않음", parsed is not None and "end" not in parsed, parsed)
    check("원격: 바로 화면 상태에도 고른 색", [e for e in state_events(page) if e["title"] == "동기화 색 확인"][0]["color"] == CORAL,
          state_events(page))
    page.screenshot(path=os.path.join(SHOT, "cal-v31-remote-color.png"))

    # --- 새로고침(= 원격에서 다시 읽기) 뒤에도 색이 살아 있는지: 이번 수정의 핵심
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2200)
    tab(page, 1, 700)
    after = [e for e in state_events(page) if e["title"] == "동기화 색 확인"]
    check("새로고침 뒤에도 일정의 고른 색이 살아 있음", after and after[0]["color"] == CORAL, after)
    ba = [x for x in bars(page) if x["title"].endswith("동기화 색 확인")]
    check("새로고침 뒤 달력 색띠가 고른 색(기본색 아님)", ba and ba[0]["bar"] == rgb(CORAL), ba)
    check("새로고침으로 일정이 겹쳐 생기지 않음",
          len([r for r in stub(page, "events") if r.get("title") == "동기화 색 확인"]) == 1,
          len([r for r in stub(page, "events") if r.get("title") == "동기화 색 확인"]))

    # --- 수정에서 색 바꾸기 → 원격 행도 바뀌고, 다시 열어도 그 색
    page.locator("#s-cal .daylist .ev-tap", has_text="동기화 색 확인").first.click()
    page.wait_for_timeout(450)
    pick_color(page, TEAL)
    page.locator("#evSave").click()
    page.wait_for_timeout(1600)
    rows2 = [r for r in stub(page, "events") if r.get("title") == "동기화 색 확인"]
    memo2 = json.loads(rows2[0]["memo"]) if rows2 and rows2[0].get("memo") else None
    check("수정: 원격 행 memo 의 색도 바뀜", memo2 == {"color": TEAL}, (memo2, rows2[:1]))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2200)
    tab(page, 1, 700)
    after2 = [e for e in state_events(page) if e["title"] == "동기화 색 확인"]
    b5 = [x for x in bars(page) if x["title"].endswith("동기화 색 확인")]
    check("다시 열어도 수정한 색", after2 and after2[0]["color"] == TEAL and b5 and b5[0]["bar"] == rgb(TEAL),
          (after2, b5))

    # ==================================================================
    # 4. 왕복 — 하루+색 · 여러 날+색 · 여러 날+색없음
    # ==================================================================
    page.evaluate("""(ds) => {
      const S = window.TwoLogUI.state;
      S.events = [
        {id: 'rt-one', date: ds.a, endDate: ds.a, time: '', title: '왕복 하루+색',
         type: 'etc', memo: '', color: ds.c1, who: 'both'},
        {id: 'rt-multi', date: ds.b, endDate: ds.bend, time: '', title: '왕복 여러 날+색',
         type: 'etc', memo: '', color: ds.c2, who: 'me'},
        {id: 'rt-plain', date: ds.c, endDate: ds.cend, time: '', title: '왕복 여러 날 색없음',
         type: 'etc', memo: '', color: '', who: 'you'}
      ];
      S.ui.selDate = ds.a; S.ui.calMonth = ds.a.slice(0, 7);
      return window.TwoLogStore.flush();
    }""", {"a": d(10), "b": d(12), "bend": d(15), "c": d(18), "cend": d(21), "c1": LEMON, "c2": MINT})
    page.wait_for_timeout(1800)
    rr = {r["title"]: r.get("memo") for r in stub(page, "events")}
    def j(v):
        try:
            return json.loads(v) if v else {}
        except Exception:
            return "(파싱 실패: %s)" % v
    check("왕복: 하루+색 → memo 에 color 만", j(rr.get("왕복 하루+색")) == {"color": LEMON}, rr.get("왕복 하루+색"))
    check("왕복: 여러 날+색 → memo 에 end·color",
          j(rr.get("왕복 여러 날+색")) == {"end": d(15), "color": MINT}, rr.get("왕복 여러 날+색"))
    check("왕복: 여러 날·색없음 → memo 에 end 만",
          j(rr.get("왕복 여러 날 색없음")) == {"end": d(21)}, rr.get("왕복 여러 날 색없음"))

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2200)
    back = {e["title"]: e for e in state_events(page)}
    one, multi3, plain3 = back.get("왕복 하루+색"), back.get("왕복 여러 날+색"), back.get("왕복 여러 날 색없음")
    check("왕복: 하루+색 — color·endDate 보존",
          one and one["color"] == LEMON and one["endDate"] == d(10), one)
    check("왕복: 여러 날+색 — color·endDate 보존",
          multi3 and multi3["color"] == MINT and multi3["endDate"] == d(15), multi3)
    check("왕복: 여러 날·색없음 — color 는 빈 값, endDate 보존",
          plain3 and plain3["color"] == "" and plain3["endDate"] == d(21), plain3)

    # 색띠도 확인 (여러 날+색 일정은 시작일을 골라 봄)
    tab(page, 1, 600)
    page.evaluate("""(ds) => {
      const S = window.TwoLogUI.state;
      S.ui.selDate = ds; S.ui.calMonth = ds.slice(0, 7);
      window.TwoLogUI.rerender();
    }""", d(12))
    page.wait_for_timeout(500)
    bt = [x for x in bars(page) if x["title"].endswith("왕복 여러 날+색")]
    check("왕복: 여러 날 일정의 색띠도 고른 색", bt and bt[0]["bar"] == rgb(MINT), bt)
    page.screenshot(path=os.path.join(SHOT, "cal-v31-roundtrip.png"))

    # ==================================================================
    # 5. 예전 행 — memo 에 «YYYY-MM-DD» 평문 / 빈 값 (v30 이전에 올라간 일정)
    # ==================================================================
    page.evaluate("""(ds) => {
      const st = window.__stub;
      const cid = window.TwoLogStore.coupleId;
      st.events.push({id: 'old-legacy', couple_id: cid, title: '예전 여러 날 일정', date: ds.st,
                      time: '', type: 'date', memo: ds.end, who: 'both'});
      st.events.push({id: 'old-plain', couple_id: cid, title: '예전 하루 일정', date: ds.st,
                      time: '', type: 'date', memo: '', who: 'both'});
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
    }""", {"st": d(24), "end": d(27)})
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2200)
    old = {e["title"]: e for e in state_events(page)}
    lg, pl = old.get("예전 여러 날 일정"), old.get("예전 하루 일정")
    check("예전 행(평문 종료일): 종료일을 그대로 읽음", lg and lg["endDate"] == d(27), lg)
    check("예전 행(평문 종료일): 고른 색이 없으니 빈 값(담당자 색)", lg and lg["color"] == "", lg)
    check("예전 행(빈 memo): 종료일 = 시작일", pl and pl["endDate"] == d(24) and pl["color"] == "", pl)
    tab(page, 1, 600)
    page.evaluate("""(ds) => {
      const S = window.TwoLogUI.state; S.ui.selDate = ds; S.ui.calMonth = ds.slice(0, 7);
      window.TwoLogUI.rerender();
    }""", d(24))
    page.wait_for_timeout(400)
    bl = [x for x in bars(page) if x["title"].endswith("예전 여러 날 일정")]
    now_both = page.evaluate("(((window.TwoLogUI.state||{}).couple||{}).sched||{}).both")
    check("예전 행의 색띠는 담당자 기본색", bl and bl[0]["bar"] == rgb(now_both or DEFAULT_BOTH), (bl, now_both))
    # 앱이 예전 행을 다시 올려 memo 형식을 바꿔도 일정은 그대로 (겹침 없음)
    page.wait_for_timeout(1200)
    legacy_rows = [r for r in stub(page, "events") if r.get("title") == "예전 여러 날 일정"]
    check("예전 행이 겹쳐 생기지 않음", len(legacy_rows) == 1, len(legacy_rows))

    # ==================================================================
    # 6. Realtime — 상대가 색을 바꾸면 새로 열지 않아도 그 색
    # ==================================================================
    page.evaluate("""(args) => {
      const st = window.__stub;
      const row = (st.events || []).filter(r => r.id === args.id)[0];
      row.memo = JSON.stringify({color: args.color});
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      return window.__stubEmit('events', args.cid);
    }""", {"id": "rt-one", "color": CORAL, "cid": page.evaluate("window.TwoLogStore.coupleId")})
    page.wait_for_timeout(2600)
    rt = [e for e in state_events(page) if e["title"] == "왕복 하루+색"]
    check("Realtime: 상대가 바꾼 색이 새로 열지 않아도 반영", rt and rt[0]["color"] == CORAL, rt)

    # ==================================================================
    # 7. 다른 화면 그대로 · 버전 표시 · 오류 없음
    # ==================================================================
    for idx, name, sid in ((0, "홈", "s-home"), (2, "노트", "s-diary"), (3, "사진첩", "s-photo"), (4, "My", "s-set")):
        tab(page, idx, 550)
        ok = page.evaluate("(id) => { const el = document.getElementById(id);"
                           " return !!el && el.classList.contains('active') && el.innerText.trim().length > 0; }", sid)
        check("%s 화면이 정상으로 뜸" % name, bool(ok), sid)
    ver = page.inner_text("#s-set .app-ver")
    check("My 맨 위 버전 표시가 v51", "v51" in ver, ver)
    page.screenshot(path=os.path.join(SHOT, "my-v31.png"))
    check("여기까지 콘솔/페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    browser.close()

print()
if fails:
    print("FAILED %d: %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS")
