"""투로그 v34 확인 — 노트 탭은 늘 「메모」부터, + 시트 한 장에서 카테고리 추가·이름·순서까지.

1) 버전: sw.js 캐시 twolog-v41 · APP_VERSION v41 · My 탭 「버전 v41」
2) 노트 탭에 들어올 때마다 늘 「메모」가 먼저 — 안에서 고른 탭은 그 화면에 머무는 동안만 유지
   (다른 노트 탭 → 홈/캘린더 → 노트 : 메모 / 새로고침 뒤 노트 : 메모)
3) + 시트 개편
   - 「카테고리 이름」·「형식」 라벨과 체크리스트/메모 버튼이 없음
   - 「탭 이름 수정 (노트 설정)」 버튼이 없음 (한 장으로 합침)
   - 위에는 새 카테고리 이름 칸, 아래에는 기본 탭 3개 + 내 카테고리가 한 목록으로
   - 각 줄: 3줄(≡) 손잡이 · 이름 칸 · (내 카테고리만) 삭제
4) 새 카테고리 추가 · 기존 탭 이름 수정 · 삭제가 이 시트에서 됨
5) ≡ 를 끌어 순서를 바꾸면 노트 상단 탭 순서가 바뀌고, 새로고침해도 유지
   (키보드 ↑ ↓ 로도 옮겨짐)
6) My 탭 「버전 v41」 · 콘솔/페이지 오류 없음

    python3 tests/v34.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def tab(page, idx, wait=500):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def sheet_state(page):
    return page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      head: ((document.querySelector('#sheet .sheet-hd h2') || {}).textContent || '').trim(),
      text: (document.querySelector('#sheet') || {}).innerText || ''})""")


def open_app(page):
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(700)
    tab(page, 2, 650)


def seg_labels(page):
    return page.evaluate("Array.from(document.querySelectorAll('#s-diary .segs .seg-btn'))"
                         ".map(b => b.textContent.trim())")


def tab_order(page):
    return page.evaluate("""Array.from(document.querySelectorAll('#s-diary .segs > button'))
        .map(b => ({key: b.getAttribute('data-seg'), label: b.textContent.trim(),
                    cls: b.className}))""")


def body_text(page):
    return page.evaluate("(document.querySelector('#s-diary #dbody') || {}).innerText || ''")


def active_seg(page):
    return page.evaluate("(window.__app.state.ui || {}).seg")


def rows_state(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('#sheet #noteOrderList .nord-row'))
      .map(r => ({key: r.getAttribute('data-key'),
                  name: ((r.querySelector('.nord-nm') || {}).value || ''),
                  grip: !!r.querySelector('.nord-grip'),
                  del: !!r.querySelector('.nord-del')}))""")


def close_sheet(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def signup(page, email, pw):
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', email)
    page.fill('#s-login input[name="password"]', pw)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)


def drag_row(page, key, to_key, below=False):
    """≡ 손잡이를 끌어 다른 줄 위(또는 아래)로 옮깁니다."""
    grip = page.locator("#sheet #noteOrderList .nord-row[data-key='%s'] .nord-grip" % key).first
    gb = grip.bounding_box()
    target = page.locator("#sheet #noteOrderList .nord-row[data-key='%s']" % to_key).first.bounding_box()
    sx, sy = gb["x"] + gb["width"] / 2, gb["y"] + gb["height"] / 2
    ty = target["y"] + (target["height"] * 0.8 if below else target["height"] * 0.2)
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.wait_for_timeout(80)
    steps = 12
    for i in range(1, steps + 1):
        page.mouse.move(sx, sy + (ty - sy) * i / steps)
        page.wait_for_timeout(22)
    page.mouse.up()
    page.wait_for_timeout(300)


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)

    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    check("sw.js 캐시 버전 twolog-v41", 'const VERSION = "twolog-v41"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v41", 'var APP_VERSION = "v41"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v41", 'const SHELL = "shell-" + VERSION' in sw)

    # ==================================================================
    # 2. 노트 탭에 들어오면 늘 「메모」부터
    # ==================================================================
    open_app(page)
    check("노트 탭을 켜면 「메모」가 먼저", active_seg(page) == "todo", active_seg(page))
    check("첫 탭이 「메모」로 열림",
          page.evaluate("(document.querySelector('#s-diary .segs > button.active') || {}).textContent || ''") == "메모")

    # 노트 안에서 다른 탭을 고르면 그 탭에 머무름 (다시 그려도 유지)
    page.locator("#s-diary .segs .seg-btn").nth(1).click()
    page.wait_for_timeout(400)
    check("노트 안에서 「버킷리스트」로 이동", active_seg(page) == "bucket", active_seg(page))
    page.evaluate("window.__app.rerender()")
    page.wait_for_timeout(350)
    check("다시 그려도 고른 탭 유지", active_seg(page) == "bucket", active_seg(page))

    tab(page, 0, 450)
    tab(page, 2, 550)
    check("홈에 갔다 노트로 오면 다시 「메모」", active_seg(page) == "todo", active_seg(page))
    check("화면도 메모 내용", "메모" not in body_text(page)[:0] and body_text(page).strip() != "")

    tab(page, 1, 450)
    tab(page, 2, 550)
    check("캘린더에 갔다 노트로 오면 다시 「메모」", active_seg(page) == "todo", active_seg(page))

    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(800)
    tab(page, 2, 600)
    check("새로고침 뒤 노트도 「메모」부터", active_seg(page) == "todo", active_seg(page))

    # ==================================================================
    # 3. + 시트 — 한 장으로 합쳐진 카테고리 설정
    # ==================================================================
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(650)
    sh = sheet_state(page)
    check("+ 를 누르면 「새 카테고리」 시트", sh["open"] and sh["head"] == "새 카테고리", sh["head"])
    check("「카테고리 이름」 라벨 없음", "카테고리 이름" not in sh["text"], sh["text"][:200])
    check("「형식」 라벨·버튼 없음",
          "형식" not in sh["text"] and page.locator('#sheet [data-act="lkind"]').count() == 0,
          page.locator('#sheet [data-act="lkind"]').count())
    # v38: 예전 체크/메모 고르는 버튼 대신 «속지 레이아웃» 카드 4개
    check("예전 체크리스트/메모 버튼은 없고 속지 카드 4개",
          page.locator('#sheet [data-act="lkind"]').count() == 0
          and page.locator('#sheet .nk-card').count() == 4,
          page.locator('#sheet .nk-card').count())
    check("「탭 이름 수정 (노트 설정)」 버튼 없음",
          page.locator('#sheet [data-act="noteSettings"]').count() == 0)
    check("시트 아래 별도 버튼 없음", page.locator("#sheet .btn-line").count() == 0)
    check("새 카테고리 이름 칸이 있음(placeholder 「새 카테고리 이름」)",
          page.evaluate("(document.querySelector('#sheet input[name=\\'title\\']') || {}).placeholder") == "새 카테고리 이름",
          page.evaluate("(document.querySelector('#sheet input[name=\\'title\\']') || {}).placeholder"))
    check("새 이름 칸은 비어 있음", page.evaluate("document.querySelector('#sheet input[name=\\'title\\']').value") == "")
    check("이름 칸은 필수가 아님(required 없음)",
          page.evaluate("!document.querySelector('#sheet input[name=\\'title\\']').required"))

    rows = rows_state(page)
    check("아래 목록에 기본 탭 세 개가 이름과 함께", [r["name"] for r in rows] == ["메모", "버킷리스트", "영화·먹방"],
          [r["name"] for r in rows])
    check("목록 키는 todo·bucket·log", [r["key"] for r in rows] == ["todo", "bucket", "log"], [r["key"] for r in rows])
    check("모든 줄에 3줄(≡) 손잡이", all(r["grip"] for r in rows), rows)
    check("기본 탭에는 삭제 버튼 없음", not any(r["del"] for r in rows), rows)
    page.screenshot(path=os.path.join(SHOT, "note-v34-sheet.png"))

    # 빈 이름으로 저장 — 새 카테고리 없이 그대로
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(700)
    st = page.evaluate("({open: document.getElementById('sheetWrap').classList.contains('open'),"
                       " lists: window.__app.state.lists.length})")
    check("이름을 비우고 저장하면 새 카테고리 없이 닫힘", st["open"] is False and st["lists"] == 0, st)

    # ==================================================================
    # 4. 새 카테고리 추가 + 이름 수정
    # ==================================================================
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    page.fill('#sheet input[name="title"]', "장보기")
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(800)
    st = page.evaluate("({lists: window.__app.state.lists.map(l => ({title: l.title, emoji: l.emoji, kind: l.kind})),"
                       " order: window.__app.state.noteOrder, seg: window.__app.state.ui.seg})")
    check("새 카테고리가 만들어짐", [l["title"] for l in st["lists"]] == ["장보기"], st["lists"])
    check("새 카테고리는 이모지 없이 체크리스트", st["lists"][0]["emoji"] == "" and st["lists"][0]["kind"] == "check",
          st["lists"])
    check("새 카테고리가 바로 열림", str(st["seg"]).startswith("list:"), st["seg"])
    check("순서 목록 맨 뒤에 붙음", len(st["order"]) == 4 and str(st["order"][-1]).startswith("list:"), st["order"])
    check("노트 탭 맨 끝에 새 탭", tab_order(page)[-1]["label"] == "장보기", [t["label"] for t in tab_order(page)])

    # + 시트에서 기본 탭·내 카테고리 이름을 한 번에 바꿔요
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    rows = rows_state(page)
    check("내 카테고리도 목록에 있음", [r["key"] for r in rows][-1].startswith("list:"), [r["key"] for r in rows])
    check("내 카테고리에만 삭제 버튼", rows[-1]["del"] and not any(r["del"] for r in rows[:-1]), rows)
    page.fill("#sheet .nord-row[data-key='todo'] .nord-nm", "할 일")
    page.fill("#sheet .nord-row[data-key='bucket'] .nord-nm", "버킷")
    last_key = rows[-1]["key"]
    page.fill("#sheet .nord-row[data-key='%s'] .nord-nm" % last_key, "마트")
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(800)
    st = page.evaluate("({note: window.__app.state.note, lists: window.__app.state.lists.map(l => l.title),"
                       " seg: window.__app.state.ui.seg})")
    check("기본 탭 이름이 시트에서 바로 바뀜", (st["note"]["todo"]["n"], st["note"]["bucket"]["n"]) == ("할 일", "버킷"),
          st["note"])
    check("내 카테고리 이름도 바뀜", st["lists"] == ["마트"], st["lists"])
    check("바뀐 이름이 노트 탭에 보임", seg_labels(page)[:2] == ["할 일", "버킷"], seg_labels(page))
    check("이름만 바꿨으면 보던 탭 유지", st["seg"] == last_key, (st["seg"], last_key))

    # ==================================================================
    # 5. ≡ 로 순서 바꾸기 — 저장하면 노트 탭 순서가 바뀌고 새로고침해도 유지
    # ==================================================================
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    before = [r["key"] for r in rows_state(page)]
    check("시트 목록 순서 = 지금 노트 순서", before[0] == "todo" and before[-1] == last_key, before)
    drag_row(page, last_key, "todo", below=False)
    after = [r["key"] for r in rows_state(page)]
    check("≡ 를 끌면 시트 안 순서가 바로 바뀜", after[0] == last_key, after)
    page.screenshot(path=os.path.join(SHOT, "note-v34-drag.png"))
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(800)
    order = [t["key"] for t in tab_order(page)]
    check("노트 상단 탭 순서가 저장한 순서대로", order == [last_key, "todo", "bucket", "log"],
          [t["label"] for t in tab_order(page)])
    check("바꾼 순서가 S.noteOrder 에 저장", page.evaluate("window.__app.state.noteOrder") == [last_key, "todo", "bucket", "log"],
          page.evaluate("window.__app.state.noteOrder"))

    # 키보드 ↑ ↓ 로도 옮겨짐
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    grip = page.locator("#sheet #noteOrderList .nord-row[data-key='log'] .nord-grip").first
    grip.focus()
    page.keyboard.press("ArrowUp")
    page.wait_for_timeout(300)
    kb = [r["key"] for r in rows_state(page)]
    check("손잡이에서 ↑ 키로 한 칸 올라감", kb == [last_key, "todo", "log", "bucket"], kb)
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(300)
    kb2 = [r["key"] for r in rows_state(page)]
    check("↓ 키로 다시 내려감", kb2 == kb2 and kb2[2] == "bucket" and kb2[3] == "log", kb2)
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    check("저장하지 않고 닫으면 순서 그대로", page.evaluate("window.__app.state.noteOrder") == [last_key, "todo", "bucket", "log"],
          page.evaluate("window.__app.state.noteOrder"))

    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    tab(page, 2, 650)
    order2 = [t["key"] for t in tab_order(page)]
    check("새로고침해도 바뀐 순서 유지", order2 == [last_key, "todo", "bucket", "log"], order2)
    check("새로고침해도 「메모」부터 열림", active_seg(page) == "todo", active_seg(page))
    check("새로고침해도 바뀐 이름 유지", seg_labels(page)[:2] == ["할 일", "버킷"], seg_labels(page))
    page.screenshot(path=os.path.join(SHOT, "note-v34-tabs.png"))

    # ==================================================================
    # 6. 내 카테고리 삭제 (시트의 삭제 → 저장)
    # ==================================================================
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    page.locator("#sheet #noteOrderList .nord-row[data-key='%s'] .nord-del" % last_key).click()
    page.wait_for_timeout(300)
    check("삭제를 누르면 시트에서 줄이 빠짐",
          all(r["key"] != last_key for r in rows_state(page)), [r["key"] for r in rows_state(page)])
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(800)
    st = page.evaluate("({lists: window.__app.state.lists.length, order: window.__app.state.noteOrder,"
                       " seg: window.__app.state.ui.seg})")
    check("저장하면 내 카테고리가 지워짐", st["lists"] == 0, st)
    check("지운 탭이 순서에서도 빠짐", st["order"] == ["todo", "bucket", "log"], st["order"])

    # ==================================================================
    # 7. My 탭 버전 · 다른 화면 · 오류
    # ==================================================================
    tab(page, 4, 600)
    ver = page.evaluate("((document.querySelector('#s-set .app-ver') || {}).textContent || '').trim()")
    check("My 탭 맨 위에 「버전 v41」", ver == "버전 v41", ver)
    for idx, name, sid in ((0, "홈", "s-home"), (1, "캘린더", "s-cal"), (3, "사진첩", "s-photo")):
        tab(page, idx, 550)
        ok = page.evaluate("(id) => { const el = document.getElementById(id);"
                           " return !!el && el.classList.contains('active') && el.innerText.trim().length > 0; }", sid)
        check("%s 화면이 정상으로 뜸" % name, bool(ok), sid)
    tab(page, 2, 550)
    page.screenshot(path=os.path.join(SHOT, "note-v34-final.png"))

    # 카테고리가 많아지면 탭 줄은 옆으로 넘어가되, 글씨가 뭉개지지 않음
    page.evaluate("""() => {
      const S = window.__app.state;
      ['운동', '책', '요리', '선물'].forEach((t, i) => {
        const id = 'many' + i;
        S.lists.push({id: id, title: t, emoji: '', kind: 'check', items: []});
        S.noteOrder.push('list:' + id);
      });
      window.__app.rerender();
    }""")
    page.wait_for_timeout(450)
    many = page.evaluate("""() => {
      const s = document.querySelector('#s-diary .segs');
      const btns = Array.from(s.querySelectorAll(':scope > button'));
      const segs = btns.filter(b => b.classList.contains('seg-btn'));
      return {n: btns.length, scroll: s.scrollWidth, client: s.clientWidth,
              ox: getComputedStyle(s).overflowX,
              segMinW: Math.min.apply(null, segs.map(b => Math.round(b.getBoundingClientRect().width))),
              trunc: btns.some(b => b.scrollWidth > b.clientWidth + 1)};
    }""")
    check("카테고리 7개가 한 줄에 모두 있음", many["n"] == 7, many)
    check("많아지면 탭 줄을 옆으로 넘겨서 봄", many["ox"] in ("auto", "scroll") and many["scroll"] > many["client"], many)
    check("기본 탭은 최소 폭을 지켜 글씨가 뭉개지지 않음", many["segMinW"] >= 70 and not many["trunc"], many)
    page.screenshot(path=os.path.join(SHOT, "note-v34-many.png"))

    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 8. 예전 데이터(순서 정보 없음) 그대로 열림 — 하위 호환
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs2 = []
    page.on("pageerror", lambda e: errs2.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs2.append("console: " + m.text) if m.type == "error" else None)
    open_app(page)
    page.evaluate("""() => {
      const k = Object.keys(localStorage).filter(x => /:state$/.test(x))[0] || 'twolog:v1:state';
      const s = JSON.parse(JSON.stringify(window.__app.state));
      delete s.noteOrder;
      s.note = { todo: {e: '', n: '메모'}, bucket: {e: '', n: '버킷리스트'}, log: {e: '', n: '영화·먹방'} };
      s.lists = [{ id: 'old1', title: '여행', emoji: '', kind: 'check', items: [] }];
      localStorage.setItem(k, JSON.stringify(s));
    }""")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    tab(page, 2, 650)
    old = tab_order(page)
    check("순서 정보가 없던 기기도 기본 순서로 열림",
          [t["key"] for t in old] == ["todo", "bucket", "log", "list:old1"], [t["label"] for t in old])
    check("순서가 자동으로 저장됨", page.evaluate("window.__app.state.noteOrder") == ["todo", "bucket", "log", "list:old1"],
          page.evaluate("window.__app.state.noteOrder"))
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    check("예전 데이터도 + 시트에 한 목록으로", [r["name"] for r in rows_state(page)] == ["메모", "버킷리스트", "영화·먹방", "여행"],
          [r["name"] for r in rows_state(page)])
    close_sheet(page)
    check("예전 데이터 정리 중 오류 없음", len(errs2) == 0, errs2[:4])
    ctx.close()

    # ==================================================================
    # 9. 두 기기 — 탭 이름·순서(note_meta)도 함께 (서버 대역)
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs3 = []
    page.on("pageerror", lambda e: errs3.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs3.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "note.meta.a@twolog.app", "twolog1234")
    page.wait_for_timeout(2200)

    tab(page, 2, 600)
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(500)
    page.fill("#sheet .nord-row[data-key='todo'] .nord-nm", "할 일")
    page.fill('#sheet input[name="title"]', "장보기")
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(900)

    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    new_key = page.evaluate("window.__app.state.noteOrder[window.__app.state.noteOrder.length - 1]")
    drag_row(page, new_key, "todo", below=False)
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(900)
    page.evaluate("() => window.TwoLogStore.flush()")
    page.wait_for_timeout(1600)

    meta_rows = page.evaluate("(window.__stub.settings || []).filter(r => r.key === 'note_meta')")
    check("서버(settings)에 note_meta 행이 올라감", len(meta_rows) == 1, len(meta_rows))
    meta_val = (meta_rows[0] or {}).get("value") if meta_rows else {}
    check("note_meta 에 바뀐 탭 이름", ((meta_val.get("tabs") or {}).get("todo") or {}).get("n") == "할 일", meta_val)
    check("note_meta 에 바뀐 순서", (meta_val.get("order") or [None])[0] == new_key, meta_val.get("order"))

    db = page.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")
    a_user = db["couples"][0]["members"][0]
    db["users"]["user-nb"] = {"id": "user-nb", "email": "note.meta.b@twolog.app", "password": "twolog1234"}
    db["couples"][0]["members"] = [a_user, "user-nb"]
    seed_b = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-nb', email: 'note.meta.b@twolog.app' } }));
    })();""" % json.dumps(json.dumps(db, ensure_ascii=False))

    ctx_b = new_ctx(browser)
    ctx_b.add_init_script(seed_b)
    page_b = ctx_b.new_page()
    errs_b = []
    page_b.on("pageerror", lambda e: errs_b.append("pageerror: " + str(e)))
    page_b.on("console", lambda m: errs_b.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page_b)
    page_b.goto(URL, wait_until="domcontentloaded")
    page_b.wait_for_selector("#tabbar .tab", timeout=25000)
    page_b.wait_for_timeout(2600)
    tab(page_b, 2, 700)
    order_b = [t["label"] for t in tab_order(page_b)]
    check("상대 폰에도 바뀐 탭 이름·순서가 함께", order_b == ["장보기", "할 일", "버킷리스트", "영화·먹방"], order_b)
    check("상대 폰도 노트를 열면 「할 일(메모)」부터", page_b.evaluate("(window.__app.state.ui || {}).seg") == "todo",
          page_b.evaluate("(window.__app.state.ui || {}).seg"))
    check("동기화 중 오류 없음", len(errs3) == 0 and len(errs_b) == 0, (errs3[:3], errs_b[:3]))
    ctx_b.close()
    ctx.close()

    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
