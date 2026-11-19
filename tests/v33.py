"""투로그 v33 확인 — 노트 탭의 이모지를 걷어내고, 카테고리(탭) 설정을 쓰기 쉽게.

1) 버전: sw.js 캐시 twolog-v34 · APP_VERSION v34 · My 탭 「버전 v34」
2) 기본 탭 「메모」·「버킷리스트」·「영화·먹방」에 이모지가 없음 (예전 📝·🎯·🎬)
3) 예전에 저장된 기본 이모지는 한 번만 정리 — 내가 넣은 다른 이모지(🌙)는 그대로
4) + 시트: 「새 카테고리」 — 이모지 고르는 줄·안내가 없고, 이름·형식만
   → 만든 칩은 이모지 없이 「장보기」, 새로고침해도 📌 가 다시 붙지 않음
5) + 시트 아래 「탭 이름 수정 (노트 설정)」 버튼 → 바로 노트 설정
   노트 설정에서 메모·버킷리스트·영화·먹방 이름을 바꾸면 알약 탭에 바로 반영·유지
   (「📖 노트」 제목 꾹 누르기로도 그대로 열림)
6) 노트 설정에서 이모지 안내 문구·이모지 placeholder·이모지 칸이 사라짐
7) 다른 화면(홈·캘린더·사진첩) 그대로, 콘솔/페이지 오류 없음

    python3 tests/v33.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

EMO = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D\u20E3]")

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


def close_sheet(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)


def long_press_note_title(page, ms=720):
    box = page.locator("#s-diary .note-h1").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(ms)
    page.mouse.up()
    page.wait_for_timeout(500)


def seg_labels(page):
    return page.evaluate("Array.from(document.querySelectorAll('#s-diary .segs .seg-btn'))"
                         ".map(b => b.textContent.trim())")


def note_vals(page):
    return page.evaluate("""() => {
      const S = window.__app.state;
      return {todo: S.note.todo, bucket: S.note.bucket, log: S.note.log,
              lists: (S.lists || []).map(l => ({title: l.title, emoji: l.emoji})),
              chips: Array.from(document.querySelectorAll('#s-diary .lchip')).map(c => c.textContent.trim())};
    }""")


def open_app(page):
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(700)
    tab(page, 2, 650)


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
    check("sw.js 캐시 버전 twolog-v34", 'const VERSION = "twolog-v34"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v34", 'var APP_VERSION = "v34"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v34", 'const SHELL = "shell-" + VERSION' in sw)

    # ==================================================================
    # 2. 기본 탭 — 이모지 없이 이름만
    # ==================================================================
    open_app(page)
    labels = seg_labels(page)
    check("기본 탭 세 개 그대로", len(labels) == 3, labels)
    check("기본 탭 이름에 이모지 없음", not any(EMO.search(x) for x in labels), labels)
    check("탭 이름 = 메모·버킷리스트·영화·먹방", labels == ["메모", "버킷리스트", "영화·먹방"], labels)
    nv = note_vals(page)
    check("저장값도 이모지 빈 문자열",
          (nv["todo"]["e"], nv["bucket"]["e"], nv["log"]["e"]) == ("", "", ""),
          (nv["todo"], nv["bucket"], nv["log"]))
    check("기본 카드 제목에 이모지 없음",
          not any(EMO.search(t) for t in page.evaluate(
              "Array.from(document.querySelectorAll('#s-diary .ngrid .ncard .nc-t')).map(e => e.textContent.trim())")),
          page.evaluate("Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-t'))"
                        ".map(e => e.textContent.trim())"))
    page.screenshot(path=os.path.join(SHOT, "note-v33-tabs.png"))

    # ==================================================================
    # 3. + 시트 — 이모지 고르는 줄 없이 「새 카테고리」
    # ==================================================================
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(650)
    sh = sheet_state(page)
    check("+ 를 누르면 「새 카테고리」 시트", sh["open"] and sh["head"] == "새 카테고리", sh)
    check("이모지 고르는 줄(.emk-row) 없음", page.locator("#sheet .emk-row").count() == 0)
    check("이모지 버튼(data-act=lpick) 없음", page.locator('#sheet [data-act="lpick"]').count() == 0)
    check("시트에 「이모지」 글씨 없음", "이모지" not in sh["text"], sh["text"][:200])
    flabels = page.evaluate("Array.from(document.querySelectorAll('#sheet .f > label'))"
                             ".map(e => e.textContent.trim())")
    # v34: 「카테고리 이름」「형식」 라벨은 없어지고, 바로 적는 칸 하나 + 아래 카테고리 목록
    check("「카테고리 이름」「형식」 라벨 없음", flabels == [], flabels)
    check("시트에 새 카테고리 이름 칸",
          page.evaluate("(document.querySelector('#sheet input[name=\\'title\\']') || {}).placeholder")
          == "새 카테고리 이름")
    bottom = page.evaluate("""() => {
      const b = document.querySelector('#sheet .btn-line');
      if (!b) return null;
      return {act: b.getAttribute('data-act'), txt: b.textContent.trim(),
              inSheet: !!b.closest('#sheet')};
    }""")
    # v34: 「탭 이름 수정」 링크는 + 시트 안으로 합쳐져 사라졌어요
    check("시트 아래 「탭 이름 수정 (노트 설정)」 버튼 없음", bottom is None, bottom)
    check("시트에 이모지 없이 안내 문구", "카테고리" in sh["text"], sh["text"][:200])
    page.screenshot(path=os.path.join(SHOT, "note-v33-newcat.png"))

    # ==================================================================
    # 4. 새 카테고리 만들기 — 이모지 없이
    # ==================================================================
    page.fill('#sheet input[name="title"]', "장보기")
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(800)
    nv = note_vals(page)
    check("새 카테고리 제목", [l["title"] for l in nv["lists"]] == ["장보기"], nv["lists"])
    check("새 카테고리 이모지 없음(빈 값)", nv["lists"] and nv["lists"][0]["emoji"] == "", nv["lists"])
    check("칩은 이모지 없이 「장보기」", nv["chips"] == ["장보기"], nv["chips"])
    check("새 카테고리 화면에 To-do 입력칸",
          "To-do" in page.evaluate("(document.querySelector('#s-diary #dbody') || {}).innerText || ''"))

    page.fill('#s-diary #listAddForm input[name="text"]', "우유 사기")
    page.locator("#s-diary #listAddForm .todo-add-btn").click()
    page.wait_for_timeout(700)
    items = page.evaluate("window.__app.state.lists[0].items.map(i => i.text)")
    check("새 카테고리에 항목 추가", items == ["우유 사기"], items)

    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    tab(page, 2, 600)
    nv2 = note_vals(page)
    check("새로고침해도 이모지 없는 카테고리 유지",
          [l["title"] for l in nv2["lists"]] == ["장보기"] and nv2["lists"][0]["emoji"] == ""
          and nv2["chips"] == ["장보기"], (nv2["lists"], nv2["chips"]))

    # ==================================================================
    # 5. 탭 이름 수정 — 「📖 노트」 제목을 꾹 눌러 노트 설정 (v34: + 시트로도 됨)
    # ==================================================================
    close_sheet(page)
    long_press_note_title(page)
    page.wait_for_timeout(300)
    sh2 = sheet_state(page)
    check("노트 설정이 열림", sh2["open"] and sh2["head"] == "노트 설정", sh2)
    check("노트 설정에 이모지 칸(.nt-emo) 없음", page.locator("#sheet .nt-emo").count() == 0)
    check("노트 설정에 이모지 고르는 줄 없음", page.locator("#sheet .emk-row").count() == 0)
    check("이모지 안내 문구 사라짐",
          "이모지와 이름을" not in sh2["text"] and "이모지" not in sh2["text"], sh2["text"][:240])
    ph = page.evaluate("""Array.from(document.querySelectorAll('#sheet #noteForm input')).map(i => i.placeholder)""")
    check("placeholder 는 순수 텍스트", "예) 메모" in ph and "예) 여행 준비물" in ph, ph)
    check("placeholder 에 이모지 없음", not any(EMO.search(x or "") for x in ph), ph)
    names = page.evaluate("Array.from(document.querySelectorAll('#sheet #noteForm .nt-nm'))"
                          ".slice(0,3).map(i => i.name + '=' + i.value)")
    check("기본 탭 이름이 이모지 없이 보임",
          names == ["t_todo=메모", "t_bucket=버킷리스트", "t_log=영화·먹방"], names)
    page.screenshot(path=os.path.join(SHOT, "note-v33-settings.png"))

    page.fill("#sheet input[name='t_todo']", "할 일")
    page.fill("#sheet input[name='t_bucket']", "버킷")
    page.fill("#sheet input[name='t_log']", "영화")
    page.locator("#sheet #noteForm button[type='submit']").click()
    page.wait_for_timeout(800)
    labels2 = seg_labels(page)
    check("노트 설정으로 탭 이름이 바로 바뀜", labels2[:3] == ["할 일", "버킷", "영화"], labels2)
    check("바뀐 탭 이름에도 이모지 없음", not any(EMO.search(x) for x in labels2), labels2)

    tab(page, 0, 500)
    tab(page, 2, 550)
    check("다른 탭 갔다 와도 이름 유지", seg_labels(page)[:3] == ["할 일", "버킷", "영화"], seg_labels(page))

    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    tab(page, 2, 600)
    check("새로고침해도 바뀐 탭 이름 유지", seg_labels(page)[:3] == ["할 일", "버킷", "영화"], seg_labels(page))

    # 「📖 노트」 꾹 누르기로도 그대로 열림
    page.locator("#s-diary .note-h1").click()
    page.wait_for_timeout(450)
    check("제목을 짧게 누르면 노트 설정이 열리지 않음", sheet_state(page)["open"] is False)
    long_press_note_title(page)
    check("제목을 꾹 누르면 노트 설정이 열림", sheet_state(page)["head"] == "노트 설정", sheet_state(page))
    close_sheet(page)

    # ==================================================================
    # 6. My 탭 버전 · 다른 화면 · 오류
    # ==================================================================
    tab(page, 4, 600)
    ver = page.evaluate("((document.querySelector('#s-set .app-ver') || {}).textContent || '').trim()")
    check("My 탭 맨 위에 「버전 v34」", ver == "버전 v34", ver)
    page.screenshot(path=os.path.join(SHOT, "my-v33.png"))

    for idx, name, sid in ((0, "홈", "s-home"), (1, "캘린더", "s-cal"), (3, "사진첩", "s-photo")):
        tab(page, idx, 550)
        ok = page.evaluate("(id) => { const el = document.getElementById(id);"
                           " return !!el && el.classList.contains('active') && el.innerText.trim().length > 0; }", sid)
        check("%s 화면이 정상으로 뜸" % name, bool(ok), sid)
    tab(page, 2, 550)
    page.screenshot(path=os.path.join(SHOT, "note-v33-final.png"))
    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 7. 예전 기본 이모지 정리 — 기본값만, 내가 넣은 이모지는 그대로
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
      s.note = { todo: {e: '📝', n: '메모'}, bucket: {e: '🌙', n: '버킷리스트'}, log: {e: '🎬', n: '영화·먹방'} };
      if (s.mig) delete s.mig.noteEmo;      // v32 에서 쓰던 폰
      if (!s.mig) s.mig = {};
      localStorage.setItem(k, JSON.stringify(s));
    }""")
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    tab(page, 2, 600)
    nv3 = note_vals(page)
    check("예전 기본 이모지 📝·🎬 는 지워짐",
          nv3["todo"]["e"] == "" and nv3["log"]["e"] == "", (nv3["todo"], nv3["log"]))
    check("내가 넣은 이모지 🌙 는 그대로", nv3["bucket"]["e"] == "🌙", nv3["bucket"])
    check("탭 표시도 그대로 반영", seg_labels(page) == ["메모", "🌙 버킷리스트", "영화·먹방"], seg_labels(page))
    page.screenshot(path=os.path.join(SHOT, "note-v33-migrate.png"))
    check("이전 데이터 정리 중 오류 없음", len(errs2) == 0, errs2[:4])
    ctx.close()

    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
