"""투로그 v16 확인 — 노트 카드 시트 정리(제목 맨 위, 한 줄 메모·누구 삭제),
노트 카드 프사 삭제·글씨 확대, 홈 제목 줄 테두리, 홈 색 → 기본 버튼 색, D-day 아래로.

    python3 tests/v16.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


CSS_OF = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
  const s = getComputedStyle(el); const r = el.getBoundingClientRect();
  return {br: s.borderTopLeftRadius, pl: s.paddingLeft, pt: s.paddingTop,
  bt: s.borderTopWidth, bs: s.borderTopStyle, bc: s.borderTopColor,
  bg: s.backgroundColor, col: s.color, fs: s.fontSize, fw: s.fontWeight,
  mt: s.marginTop, sh: s.boxShadow, h: r.height, w: r.width, x: r.x, y: r.y, txt: el.innerText}; }"""
BOX = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
  const r = el.getBoundingClientRect(); return {y: r.y, h: r.height}; }"""
LABELS = "() => Array.from(document.querySelectorAll('#sheetForm label')).map(l => l.innerText.trim())"
INK = """(hex) => { const h = String(hex).replace('#',''); const n = parseInt(h.slice(0,2),16),
  g = parseInt(h.slice(2,4),16), b = parseInt(h.slice(4,6),16);
  const lin = c => (c/255) <= 0.03928 ? (c/255)/12.92 : Math.pow((c/255 + 0.055)/1.055, 2.4);
  const L = 0.2126*lin(n) + 0.7152*lin(g) + 0.0722*lin(b);
  return L > 0.5 ? 'rgb(17, 17, 17)' : 'rgb(255, 255, 255)'; }"""
RGB = """(hex) => { const h = String(hex).replace('#','');
  return 'rgb(' + parseInt(h.slice(0,2),16) + ', ' + parseInt(h.slice(2,4),16) + ', ' + parseInt(h.slice(4,6),16) + ')'; }"""


def shot(page, name, settle=1900):
    page.wait_for_timeout(settle)
    page.screenshot(path=os.path.join(SHOT, name))


def px(v):
    try:
        return float(str(v).replace("px", ""))
    except Exception:  # noqa: BLE001
        return -1


with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    page.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page.wait_for_timeout(700)

    # ---------- 노트 탭 ----------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(600)
    n_cards = page.locator("#s-diary .ncard:not(.new)").count()
    check("노트 카드 있음", n_cards >= 1, n_cards)

    # 1. 카드에서 프사 동그라미가 사라졌는지
    check("카드에 프사 없음", page.locator("#s-diary .ncard .nc-av").count() == 0,
          page.locator("#s-diary .ncard .nc-av").count())
    top_txt = page.locator("#s-diary .ncard .nc-top").first.inner_text().strip()
    check("맨 윗줄은 주제 한 줄", "\n" not in top_txt, top_txt)
    check("맨 윗줄에 이름 없음", ("소영" not in top_txt) and ("준영" not in top_txt), top_txt)
    check("한 줄 메모 줄 없음", page.locator("#s-diary .ncard .nc-c").count() == 0,
          page.locator("#s-diary .ncard .nc-c").count())
    check("nc-av 스타일 정리", page.evaluate(
        "() => { const el = document.createElement('span'); el.className = 'nc-av';"
        " document.querySelector('#s-diary').appendChild(el);"
        " const w = getComputedStyle(el).width; el.remove(); return w; }") in ("auto", "0px"),
        page.evaluate("() => { const el = document.createElement('span'); el.className = 'nc-av';"
                      " document.querySelector('#s-diary').appendChild(el);"
                      " const w = getComputedStyle(el).width; el.remove(); return w; }"))

    # 2. 카드 글씨 확대
    tp_css = page.evaluate(CSS_OF, "#s-diary .ncard .nc-topic")
    t_css = page.evaluate(CSS_OF, "#s-diary .ncard .nc-t")
    check("주제 14px", px(tp_css["fs"]) >= 14, tp_css["fs"])
    check("제목 18px", px(t_css["fs"]) >= 18, t_css["fs"])
    check("제목 800", int(t_css["fw"]) >= 800, t_css["fw"])

    # 3. 카드 상세 시트 — 제목이 맨 위, To-do 아래
    page.locator("#s-diary .ncard .nc-t").first.scroll_into_view_if_needed()
    page.locator("#s-diary .ncard .nc-t").first.click()
    page.wait_for_timeout(500)
    check("카드 상세 시트 열림", page.locator("#sheet .card-items").count() == 1)
    check("시트 머리에 제목 중복 없음", page.locator("#sheet .sheet-hd h2").count() == 0,
          page.locator("#sheet .sheet-hd h2").count())
    labels = page.evaluate(LABELS)
    check("제목·주제 칸 있음", "제목" in labels and "주제" in labels, labels)
    check("한 줄 메모 칸 없음", "한 줄 메모 (선택)" not in labels and "한 줄 메모" not in labels, labels)
    check("누구 칸 없음", "누구" not in labels, labels)
    check("한 줄 메모 입력 없음", page.locator('#sheetForm input[name="caption"]').count() == 0)
    check("누구 선택 없음", page.locator('#sheet [data-group="gwho"]').count() == 0
          and page.locator('#sheet input[name="who"]').count() == 0)
    check("「한 줄 메모」 글씨 없음", "한 줄 메모" not in page.locator("#sheet").inner_text())

    y_title = page.evaluate(BOX, '#sheetForm input[name="title"]')
    y_topic = page.evaluate(BOX, '#sheetForm input[name="topic"]')
    y_todo = page.evaluate(BOX, "#sheet .todo-label")
    y_items = page.evaluate(BOX, "#sheet .card-items")
    check("제목이 주제보다 위", y_title and y_topic and y_title["y"] < y_topic["y"],
          (y_title and round(y_title["y"]), y_topic and round(y_topic["y"])))
    check("제목·주제가 To-do보다 위", y_title and y_todo and y_topic["y"] < y_todo["y"],
          (y_topic and round(y_topic["y"]), y_todo and round(y_todo["y"])))
    check("제목이 항목 목록보다 위", y_title and y_items and y_title["y"] < y_items["y"],
          (y_title and round(y_title["y"]), y_items and round(y_items["y"])))
    check("To-do 안내 문구는 그대로", page.locator("#sheet .todo-add input.todo-in").count() == 1)

    # 4. To-do 추가·토글은 그대로 동작
    for word in ("우유 사기", "계란", "카카오페이 충전"):
        page.fill('#sheet #listAddForm input[name="text"]', word)
        page.click("#sheet .todo-add-btn")
        page.wait_for_timeout(300)
    check("시트에서 항목 추가", page.locator("#sheet .card-items .trow").count() == 3,
          page.locator("#sheet .card-items .trow").count())
    page.locator("#sheet .card-items .trow .circ").first.click()
    page.wait_for_timeout(400)
    check("시트 안에서 완료", page.locator("#sheet .card-items .trow.done").count() == 1)
    # 항목을 체크해도 적던 제목이 날아가지 않는지
    page.fill('#sheetForm input[name="title"]', "생일 준비")
    page.fill('#sheetForm input[name="topic"]', "이번 주")
    page.locator("#sheet .card-items .trow .circ").nth(1).click()
    page.wait_for_timeout(400)
    check("체크해도 적던 제목 유지", page.input_value('#sheetForm input[name="title"]') == "생일 준비",
          page.input_value('#sheetForm input[name="title"]'))
    page.locator("#sheet .card-acts").scroll_into_view_if_needed()
    shot(page, "note-detail-v16.png", settle=600)
    page.click("#sheet .card-acts .btn-primary")
    page.wait_for_timeout(800)
    check("저장하면 시트 닫힘", page.locator("#sheetWrap.open").count() == 0)
    check("저장한 제목이 카드에", page.locator("#s-diary .ncard .nc-t").first.inner_text().strip() == "생일 준비",
          page.locator("#s-diary .ncard .nc-t").first.inner_text())
    check("저장한 주제가 카드 윗줄에",
          page.locator("#s-diary .ncard .nc-topic").first.inner_text().strip() == "이번 주",
          page.locator("#s-diary .ncard .nc-topic").first.inner_text())
    tp2 = page.evaluate(CSS_OF, "#s-diary .ncard .nc-topic")
    check("주제 채워지면 600", int(tp2["fw"]) == 600, tp2["fw"])
    check("카드에 항목 미리보기", page.locator("#s-diary .ncard .nc-items .cti").count() >= 3,
          page.locator("#s-diary .ncard .nc-items .cti").count())
    items_css = page.evaluate(CSS_OF, "#s-diary .ncard .nc-items .cti .cx")
    check("리스트 15px", px(items_css["fs"]) >= 15, items_css["fs"])
    check("리스트 얇게(300)", int(items_css["fw"]) <= 300, items_css["fw"])
    circ = page.evaluate("() => { const s = document.querySelector('#s-diary .ncard .cti .cb svg'); return s ? getComputedStyle(s).width : null; }")
    check("체크 동그라미 16px", circ == "16px", circ)
    page.locator("#s-diary .ncard .nc-t").first.scroll_into_view_if_needed()
    shot(page, "note-v16.png", settle=900)

    # ---------- 5. 새 리스트 시트 ----------
    before = page.locator("#s-diary .ncard:not(.new)").count()
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(450)
    new_labels = page.evaluate(LABELS)
    check("새 리스트에 제목·주제", "제목" in new_labels and "주제" in new_labels, new_labels)
    check("새 리스트에 한 줄 메모 없음", page.locator('#sheetForm input[name="caption"]').count() == 0,
          new_labels)
    check("새 리스트에 누구 없음", "누구" not in new_labels
          and page.locator('#sheet [data-group="gwho"]').count() == 0, new_labels)
    ny_title = page.evaluate(BOX, '#sheetForm input[name="title"]')
    ny_topic = page.evaluate(BOX, '#sheetForm input[name="topic"]')
    check("새 리스트도 제목이 맨 위", ny_title and ny_topic and ny_title["y"] < ny_topic["y"],
          (ny_title and round(ny_title["y"]), ny_topic and round(ny_topic["y"])))
    shot(page, "note-new-v16.png", settle=400)
    page.fill('#sheetForm input[name="title"]', "장보기")
    page.fill('#sheetForm input[name="topic"]', "이번 주말")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(700)
    check("새 리스트 만들어짐", page.locator("#s-diary .ncard:not(.new)").count() == before + 1,
          page.locator("#s-diary .ncard:not(.new)").count())
    new_topics = page.evaluate(
        "() => Array.from(document.querySelectorAll('#s-diary .ncard .nc-topic')).map(e => e.innerText.trim())")
    check("새 리스트 주제 저장", "이번 주말" in new_topics, new_topics)

    # 6. 카드 삭제는 그대로 동작
    page.locator("#s-diary .ncard", has_text="장보기").first.click()
    page.wait_for_timeout(450)
    page.click('#sheet [data-act="delCard"]')
    page.wait_for_timeout(450)
    check("삭제 확인 시트", "카드를 지울까요" in page.locator("#sheet").inner_text(),
          page.locator("#sheet").inner_text()[:60])
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(700)
    check("카드 삭제됨", page.locator("#s-diary .ncard:not(.new)").count() == before,
          page.locator("#s-diary .ncard:not(.new)").count())

    # ---------- 7. 홈 ----------
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(500)

    dday = page.evaluate(CSS_OF, "#s-home .dday")
    check("D-day 아래로 내려감(margin-top 90px 이상)", dday and px(dday["mt"]) >= 90, dday and dday["mt"])
    check("D-day 수정 연필 있음", page.locator("#s-home .dday .dday-edit").count() == 1)
    pencil = page.evaluate(BOX, "#s-home .dday .dday-edit")
    dd = page.evaluate(BOX, "#s-home .dday")
    check("연필은 D-day 오른쪽 위", pencil and dd and pencil["y"] - dd["y"] < 40 and pencil["y"] > dd["y"] - 2,
          (dd and round(dd["y"]), pencil and round(pencil["y"])))
    shot(page, "home-v16.png", settle=600)

    # 제목 줄 테두리
    tint = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    check("제목 줄 테두리 1px", tint and px(tint["bt"]) == 1 and tint["bs"] == "solid",
          (tint and tint["bt"], tint and tint["bs"]))
    check("제목 줄 테두리 둥글게", tint and px(tint["br"]) >= 20, tint and tint["br"])

    # 색을 고르면 기본 버튼도 같은 색
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(400)
    sw = page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').nth(0)
    picked = sw.get_attribute("data-color")
    sw.click()
    page.wait_for_timeout(450)
    btn = page.evaluate(CSS_OF, "#sheet .btn-primary")
    check("버튼이 고른 색으로", btn and btn["bg"] == page.evaluate(RGB, picked), (picked, btn and btn["bg"]))
    check("버튼 글씨 대비", btn and btn["col"] == page.evaluate(INK, picked), (picked, btn and btn["col"]))
    shot(page, "theme-sheet-v16.png", settle=350)
    page.keyboard.press("Escape")
    page.wait_for_timeout(450)
    shot(page, "home-tinted-v16.png", settle=700)
    tint2 = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    check("제목 줄도 같은 색", tint2 and tint2["bg"] == page.evaluate(RGB, picked), (picked, tint2 and tint2["bg"]))
    check("색 넣어도 테두리 유지", tint2 and px(tint2["bt"]) == 1, tint2 and tint2["bt"])

    # ‘기본’으로 되돌리면 버튼 색도 원래대로
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(400)
    reset_btn = page.evaluate(CSS_OF, "#sheet .btn-primary")
    check("색 고른 상태 버튼 유지", reset_btn and reset_btn["bg"] == page.evaluate(RGB, picked),
          reset_btn and reset_btn["bg"])
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(450)
    back = page.evaluate(CSS_OF, "#sheet .btn-primary")
    check("기본으로 되돌리면 원래 버튼 색", back and back["bg"] == "rgb(217, 107, 82)", back and back["bg"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    t_off = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    check("색 없어도 테두리 남음", t_off and px(t_off["bt"]) == 1 and px(t_off["br"]) >= 20,
          (t_off and t_off["bt"], t_off and t_off["br"]))

    # ---------- 8. 좁은 화면(375px) ----------
    ctx2 = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    page2 = ctx2.new_page()
    errs2 = []
    page2.on("pageerror", lambda e: errs2.append(str(e)))
    page2.on("console", lambda m: errs2.append(m.text) if m.type == "error" else None)
    page2.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page2.wait_for_timeout(700)
    page2.locator("#tabbar .tab").nth(2).click()
    page2.wait_for_timeout(500)
    page2.locator("#s-diary .ncard .nc-t").first.click()
    page2.wait_for_timeout(500)
    over = page2.evaluate("""() => {
      const s = document.querySelector('#sheet');
      const btn = document.querySelector('#sheet .card-acts .btn-primary').getBoundingClientRect();
      return {sheet: s.scrollWidth - s.clientWidth, btnRight: btn.right, btnW: btn.width,
              titleW: document.querySelector('#sheetForm input[name="title"]').getBoundingClientRect().width}; }""")
    check("375px 시트 넘침 없음", over["sheet"] <= 1 and over["btnRight"] <= 375 and over["btnW"] > 300, over)
    check("375px 콘솔 오류 없음", len(errs2) == 0, errs2[:2])
    ctx2.close()

    # ---------- 9. 서비스 워커 ----------
    ver = page.evaluate("fetch('sw.js').then(r => r.text()).then(t => (t.match(/twolog-v\\d+/) || [''])[0])")
    check("sw 캐시 v16", ver == "twolog-v16", ver)
    check("콘솔 오류 없음", len(errors) == 0, errors[:3])
    browser.close()

print()
print("실패:", fails if fails else "없음")
print("스크린샷:", SHOT)
sys.exit(1 if fails else 0)
