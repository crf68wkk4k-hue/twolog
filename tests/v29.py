"""투로그 v29 확인 — 노트 맨 윗줄의 네모 설정 버튼을 지우고 그 자리에 동그란 +, 알약 탭은 조금 작게.

1) 버전: sw.js 캐시 twolog-v47 · APP_VERSION v47
2) 노트 맨 윗줄(📖 노트) 오른쪽에 동그란 점선 + 가 있고, 누르면 「새 카테고리」 시트가 열림
3) 예전 네모 설정 버튼(톱니 아이콘)은 사라짐 — 알약 탭 아래 칩 줄에도 + 는 없음
4) 알약 탭(메모·버킷리스트·영화·먹방)이 조금 작아짐: 높이 40px · 글씨 14px · 글씨 잘림 없음
   (v28: 높이 44px · 글씨 15.5px)
5) + 로 만든 새 카테고리 탭이 칩으로 붙고, 그 안에 항목을 넣을 수 있음
6) 탭 이름 바꾸기(노트 설정)는 「📖 노트」 제목을 꾹 눌러 엽니다 — 짧게 누르면 열리지 않음
7) 다른 화면(홈·캘린더·사진첩·My)은 그대로, 페이지 오류 없음

    python3 tests/v29.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

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
      head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent})""")


def close_sheet(page):
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)


def long_press_note_title(page, ms=720):
    """「📖 노트」 제목을 꾹 눌러 노트 설정을 엽니다."""
    box = page.locator("#s-diary .note-h1").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(ms)
    page.mouse.up()
    page.wait_for_timeout(500)


def note_header(page):
    return page.evaluate("""() => {
      const hdr = document.querySelector('#s-diary .hdr');
      const h1 = document.querySelector('#s-diary .note-h1');
      const segs = document.querySelector('#s-diary .segs');
      const btn = document.querySelector('#s-diary .hdr .note-add');
      const o = {gear: !!document.querySelector('#s-diary [data-act=\\'noteSettings\\']'),
                 roundGear: Array.from(document.querySelectorAll('#s-diary .hdr-acts button'))
                   .filter(b => (b.getAttribute('aria-label') || '').indexOf('설정') >= 0).length,
                 oks: !!hdr && !!h1 && !!segs};
      if (!btn) { o.ok = false; return o; }
      const r = btn.getBoundingClientRect();
      const h1r = h1.getBoundingClientRect();
      const sr = segs.getBoundingClientRect();
      const cs = getComputedStyle(btn);
      o.ok = true;
      o.x = Math.round(r.x); o.y = Math.round(r.y);
      o.w = Math.round(r.width); o.h = Math.round(r.height);
      o.radius = cs.borderTopLeftRadius;
      o.border = cs.borderTopStyle;
      o.right = Math.round(window.innerWidth - r.right);
      o.inHeader = !!btn.closest('.hdr');
      o.sameRowAsTitle = Math.abs((r.top + r.height / 2) - (h1r.top + h1r.height / 2)) <= 12;
      o.abovePills = r.bottom <= sr.top + 1;
      o.svg = !!btn.querySelector('svg');
      o.act = btn.getAttribute('data-act');
      o.label = btn.getAttribute('aria-label');
      o.headerBtns = document.querySelectorAll('#s-diary .hdr-acts button').length;
      o.plusInChipBar = !!document.querySelector('#s-diary .lstbar .lst-new, #s-diary .lstbar .note-add');
      return o;
    }""")


def pill_state(page):
    return page.evaluate("""() => {
      const btns = Array.from(document.querySelectorAll('#s-diary .segs .seg-btn'));
      const cs = btns.length ? getComputedStyle(btns[0]) : null;
      const segs = document.querySelector('#s-diary .segs');
      return {n: btns.length, h: btns.length ? Math.round(btns[0].getBoundingClientRect().height) : null,
              w: btns.length ? Math.round(btns[0].getBoundingClientRect().width) : null,
              fs: cs ? cs.fontSize : null, pad: cs ? cs.paddingLeft : null,
              gap: segs ? getComputedStyle(segs).gap : null,
              trunc: btns.some(e => e.scrollWidth > e.clientWidth + 1),
              labels: btns.map(e => e.textContent.trim())};
    }""")


def note_state(page):
    return page.evaluate("""() => {
      const S = window.__app.state;
      const seg = (S.ui || {}).seg;
      const cur = String(seg || '').indexOf('list:') === 0 ? (S.lists || []).filter(l => l.id === seg.slice(5))[0] : null;
      return {seg, lists: (S.lists || []).map(l => ({id: l.id, title: l.title, emoji: l.emoji,
                items: (l.items || []).map(i => i.text)})),
              chips: Array.from(document.querySelectorAll('#s-diary .lchip')).map(c => c.textContent.trim()),
              body: (document.querySelector('#s-diary #dbody') || {}).innerText || '',
              cur: cur ? cur.title : null};
    }""")


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
    css = page.request.get(URL + "styles.css").text()
    check("sw.js 캐시 버전 twolog-v47", 'const VERSION = "twolog-v47"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v44", 'var APP_VERSION = "v47"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v47", 'const SHELL = "shell-" + VERSION' in sw)
    check("예전 칩 줄 + 스타일(.lst-new)은 남아 있지 않음", ".lst-new" not in css)

    # ==================================================================
    # 2. 노트 맨 윗줄 — 네모 설정 대신 동그란 +
    # ==================================================================
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(800)
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    tab(page, 2, 650)

    hd = note_header(page)
    check("노트 맨 윗줄에 + 버튼이 있음", hd.get("ok") and hd.get("act") == "newList", hd)
    check("+ 버튼은 맨 윗줄(📖 노트) 오른쪽", hd.get("inHeader") and hd.get("sameRowAsTitle")
          and hd.get("abovePills"), (hd.get("inHeader"), hd.get("sameRowAsTitle"), hd.get("abovePills")))
    # v37: 44px 터치 영역 + 바깥 상자 오른쪽 끝 17px (＋ 아이콘 끝은 28px)
    check("+ 버튼은 오른쪽 끝 17px (＋ 아이콘 28px)", abs((hd.get("right") or 0) - 17) <= 1, hd.get("right"))
    check("+ 버튼은 테두리·바탕 없이 (v37)", hd.get("radius") in ("0px", "0") and hd.get("border") in ("none", ""),
          (hd.get("radius"), hd.get("border")))
    check("+ 버튼 아이콘은 ＋ 모양", hd.get("svg"))
    check("+ 버튼 터치 영역 44px 정사각 (v37)", hd.get("w") == 44 and hd.get("h") == 44, (hd.get("w"), hd.get("h")))
    check("예전 네모 설정 버튼은 사라짐", hd.get("gear") is False and hd.get("roundGear") == 0,
          (hd.get("gear"), hd.get("roundGear")))
    check("맨 윗줄 오른쪽 버튼은 + 하나뿐", hd.get("headerBtns") == 1, hd.get("headerBtns"))
    check("알약 탭 아래 칩 줄에는 + 가 없음", hd.get("plusInChipBar") is False, hd.get("plusInChipBar"))
    page.screenshot(path=os.path.join(SHOT, "note-v29.png"))

    # ==================================================================
    # 3. 알약 탭 크기 축소
    # ==================================================================
    pl = pill_state(page)
    check("알약 탭 3개 그대로", pl["n"] == 3, pl["labels"])
    check("알약 탭 높이 40px (v28 44px)", pl["h"] == 40, pl["h"])
    check("알약 탭 글씨 14px (v28 15.5px)", pl["fs"] == "14px", pl["fs"])
    # v38: 탭은 글자 수에 맞춰 너비가 정해져 좌우 여백이 넉넉해짐
    check("알약 탭 좌우 여백 16px (v38 글자 수 맞춤)", pl["pad"] == "16px", pl["pad"])
    check("알약 탭 사이 간격 8px 그대로", pl["gap"] == "8px", pl["gap"])
    check("메모·버킷리스트·영화·먹방 글씨가 잘리지 않음", pl["trunc"] is False, pl["labels"])
    # v38: 화면 폭을 똑같이 나누지 않고 글자 수에 맞춰 너비가 정해짐(최소 72px)
    widths = page.evaluate("() => [...document.querySelectorAll('#s-diary .note-segs .seg-btn')].map(b => Math.round(b.getBoundingClientRect().width))")
    check("알약 탭은 글자 수에 맞춰 너비가 정해짐",
          len(set(widths)) >= 2 and min(widths) >= 70
          and widths[1] > widths[0], widths)

    # ==================================================================
    # 4. + 를 누르면 새 카테고리 탭 시트
    # ==================================================================
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    sh = sheet_state(page)
    # v33: + 시트 이름이 「새 카테고리」로 바뀌고 이모지 고르는 줄은 사라졌어요
    check("+ 를 누르면 「새 카테고리」 시트가 열림", sh["open"] and sh["head"] == "새 카테고리", sh)
    page.screenshot(path=os.path.join(SHOT, "note-v29-newlist.png"))

    page.fill('#sheet input[name="title"]', "장보기")
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(800)
    ns = note_state(page)
    check("새 카테고리 탭이 만들어짐", [l["title"] for l in ns["lists"]] == ["장보기"], ns["lists"])
    check("칩 줄에 새 탭이 붙고 바로 열림", ns["chips"] == ["장보기"] and ns["cur"] == "장보기",
          (ns["chips"], ns["cur"]))
    check("칩 줄에도 + 는 여전히 없음", note_header(page).get("plusInChipBar") is False)

    # v40: 새 카테고리는 2열 카드 묶음 — 「+ 새 리스트」로 카드를 만들고 그 안에 항목을 넣어요
    check("새 탭 화면은 2열 카드 묶음 (v40)", "새 리스트" in ns["body"], ns["body"][:80])
    page.locator("#s-diary .ngrid .ncard.new").click()
    page.wait_for_timeout(480)
    page.fill("#sheet input[name=title]", "장보기 목록")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(600)
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.click()
    page.wait_for_timeout(520)
    page.fill('#sheet #listAddForm input[name="text"]', "우유 사기")
    page.locator('#sheet #listAddForm button').click()
    page.wait_for_timeout(520)
    page.keyboard.press("Escape")
    page.wait_for_timeout(420)
    ns2 = note_state(page)
    check("새 탭 안에 항목을 넣을 수 있음",
          ns2["lists"][0]["items"] == ["우유 사기"] and "우유 사기" in ns2["body"], ns2["lists"])
    page.screenshot(path=os.path.join(SHOT, "note-v29-lists.png"))

    # ==================================================================
    # 5. 탭 이름 바꾸기 — 「📖 노트」 제목을 꾹 눌러 노트 설정
    # ==================================================================
    page.locator("#s-diary .note-h1").click()
    page.wait_for_timeout(500)
    check("제목을 짧게 누르면 노트 설정이 열리지 않음", sheet_state(page)["open"] is False, sheet_state(page))

    long_press_note_title(page)
    sh2 = sheet_state(page)
    check("제목을 꾹 누르면 노트 설정 시트가 열림", sh2["open"] and sh2["head"] == "노트 설정", sh2)
    page.screenshot(path=os.path.join(SHOT, "note-v29-settings.png"))
    page.fill("#sheet input[name='t_bucket']", "🎯 버킷")
    page.locator("#sheet #noteForm button[type='submit']").click()
    page.wait_for_timeout(600)
    labels = page.evaluate("Array.from(document.querySelectorAll('#s-diary .segs .seg-btn')).map(b => b.textContent.trim())")
    check("노트 설정으로 알약 탭 이름을 바꿀 수 있음", labels[1] == "🎯 버킷", labels)

    # ==================================================================
    # 6. 다른 화면은 그대로 · 오류 없음
    # ==================================================================
    for idx, name, sid in ((0, "홈", "s-home"), (1, "캘린더", "s-cal"), (3, "사진첩", "s-photo"), (4, "My", "s-set")):
        tab(page, idx, 550)
        ok = page.evaluate("(id) => { const el = document.getElementById(id);"
                           " return !!el && el.classList.contains('active') && el.innerText.trim().length > 0; }", sid)
        check("%s 화면이 정상으로 뜸" % name, bool(ok), sid)
    tab(page, 2, 600)
    page.screenshot(path=os.path.join(SHOT, "note-v29-final.png"))
    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:4])

    ctx.close()
    browser.close()

print()
if fails:
    print("FAILED %d: %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS")
