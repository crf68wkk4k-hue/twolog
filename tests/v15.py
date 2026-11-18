"""투로그 v15 확인 — 홈 제목 줄 둥근 알약·캘린더 생일 줄 삭제·노트 카드 3D(큰 글씨).

    python3 tests/v15.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

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

# 이 환경은 시스템 라이브러리(libatk 등)가 없어 LD_LIBRARY_PATH 로 넘겨 줍니다.
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
  return {br: s.borderTopLeftRadius, bt: s.borderTopRightRadius, pl: s.paddingLeft, pt: s.paddingTop,
  bw: s.borderTopWidth, bg: s.backgroundColor, col: s.color, fs: s.fontSize, fw: s.fontWeight,
  sh: s.boxShadow, h: r.height, w: r.width, x: r.x, y: r.y, txt: el.innerText}; }"""
DAY_OFFSET = """(n) => { const d = new Date(); d.setDate(d.getDate() + n);
  const p = x => String(x).padStart(2, '0');
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); }"""


def shot(page, name, settle=1900):
    """토스트가 사라진 뒤 찍어 화면이 깔끔하게 남도록."""
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

    # ---------- 일정 두 개(오늘·내일) ----------
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(350)
    for title, offset in (("성수 데이트", 0), ("영화 보는 날", 1)):
        page.locator('#s-cal [data-act="addEvent"]').first.click()
        page.wait_for_timeout(320)
        page.fill('#sheetForm input[name="title"]', title)
        if offset:
            day = page.evaluate(DAY_OFFSET, offset)
            page.fill('#sheetForm input[name="start"]', day)
            page.fill('#sheetForm input[name="end"]', day)
        page.click('#sheetForm button[type="submit"]')
        page.wait_for_timeout(450)

    # ---------- 1. 캘린더: 생일 줄이 사라졌는지 ----------
    check("캘린더 생일 줄 없음", page.locator("#s-cal .bday-note").count() == 0,
          page.locator("#s-cal .bday-note").count())
    check("캘린더 생일 이름 없음", page.locator("#s-cal .bd-nm").count() == 0,
          page.locator("#s-cal .bd-nm").count())
    check("캘린더에 「날짜 입력」 없음", "날짜 입력" not in page.locator("#s-cal").inner_text())
    cal = page.evaluate(CSS_OF, "#s-cal .cal")
    panel = page.evaluate(CSS_OF, "#s-cal .daypanel")
    check("달력 바로 아래가 날짜 목록", cal and panel and panel["y"] > cal["y"] + cal["h"] - 2,
          (cal and round(cal["y"] + cal["h"]), panel and round(panel["y"])))
    check("날짜 목록은 그대로", page.locator("#s-cal .day").count() >= 28, page.locator("#s-cal .day").count())
    ebars = page.evaluate(
        "() => Array.from(document.querySelectorAll('#s-cal .ebar')).map(e => e.innerText.trim())")
    check("일정은 그대로", "성수 데이트" in ebars and "영화 보는 날" in ebars, ebars)
    check("날짜 목록에 일정 표시", page.locator("#s-cal .ev").count() >= 1, page.locator("#s-cal .ev").count())
    page.locator("#s-cal .cal").scroll_into_view_if_needed()
    shot(page, "cal-v15.png")

    # ---------- 2. 홈: 제목 줄이 둥근 알약 ----------
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(450)
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(420)
    check("테마 시트 제목 색 항목", "다가오는 일정 · " in page.locator("#sheet").inner_text())
    shot(page, "theme-sheet-v15.png", settle=350)
    page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').nth(0).click()
    page.wait_for_timeout(450)
    page.keyboard.press("Escape")
    page.wait_for_timeout(450)

    t_sched = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    t_our = page.evaluate(CSS_OF, ".home-sec[data-sec='our'] .sec-tint")
    check("제목 줄 둥글게(20px 이상)", t_sched and px(t_sched["br"]) >= 20, t_sched and t_sched["br"])
    check("제목 줄 알약(높이의 절반 이상)", t_sched and px(t_sched["br"]) >= t_sched["h"] / 2 - 1,
          (t_sched and t_sched["br"], t_sched and round(t_sched["h"], 1)))
    # v23: 「N월의 우리」 섹션이 빠져 제목 줄은 하나만 남음
    check("남은 제목 줄도 둥글게", not t_our, t_our)
    check("제목 줄 좌우 여백 16px", t_sched and px(t_sched["pl"]) >= 15, t_sched and t_sched["pl"])
    check("제목 줄 색 그대로", t_sched and t_sched["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"),
          t_sched and t_sched["bg"])
    check("제목 글씨 진하게", page.evaluate(
        "() => getComputedStyle(document.querySelector(\".home-sec[data-sec='sched'] .sec-tint h2\")).color") == "rgb(17, 17, 17)",
        page.evaluate("() => getComputedStyle(document.querySelector(\".home-sec[data-sec='sched'] .sec-tint h2\")).color"))
    check("제목 글씨 잘리지 않음", page.evaluate(
        "() => { const h = document.querySelector(\".home-sec[data-sec='sched'] .sec-tint h2\");"
        " return h.scrollWidth <= h.clientWidth + 1 && h.getBoundingClientRect().height > 12; }"))
    page.locator(".home-sec[data-sec='sched']").scroll_into_view_if_needed()
    shot(page, "home-tinted-v15.png")

    # 색 해제 — 색이 없어도 모양은 알약 그대로
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(350)
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(350)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    t_off = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    check("색 해제 시 투명", t_off and t_off["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), t_off and t_off["bg"])
    check("색 없어도 둥근 모양", t_off and px(t_off["br"]) >= 20, t_off and t_off["br"])

    # ---------- 3. 생일은 홈 D-day 시트에 그대로 ----------
    page.locator("#s-home .dday").click()
    page.wait_for_timeout(450)
    bdays = page.evaluate("""() => Array.from(document.querySelectorAll('#sheet input.js-bday'))
      .map(i => i.type + '|' + i.name + '|' + i.value)""")
    check("D-day 시트 생일 달력 두 개", len(bdays) == 2 and all(b.startswith("date|bd") for b in bdays), bdays)
    check("소영 생일 1992", any("1992-06-26" in b for b in bdays), bdays)
    page.fill('#sheet input[name="bdYou"]', "2000-11-20")
    page.wait_for_timeout(350)
    check("생일 D-day 즉시 갱신", page.locator('#sheet [data-bdleft="you"]').inner_text().startswith("D-"),
          page.locator('#sheet [data-bdleft="you"]').inner_text())
    shot(page, "dday-sheet-v15.png", settle=350)
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(650)
    page.locator("#s-home .dday").click()
    page.wait_for_timeout(420)
    check("생일 저장 유지", "11월 20일" in page.locator("#sheet").inner_text(),
          page.locator("#sheet [data-bdtxt='you']").inner_text())
    check("캘린더 안내 문구 갱신", "캘린더 아래" not in page.locator("#sheet").inner_text())
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---------- 4. 노트 카드: 제목·큰 글씨·입체 ----------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(500)
    cards = page.locator("#s-diary .ngrid .ncard")
    check("카드 그리드 있음", cards.count() >= 1, cards.count())
    grid = page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ngrid')).gridTemplateColumns")
    check("두 열", len(grid.split(" ")) == 2, grid)
    # v17: 「주제」 줄이 없어져 카드는 제목부터 시작해요
    check("카드에 주제 줄 없음", page.locator("#s-diary .ncard .nc-topic").count() == 0 and
          page.locator("#s-diary .ncard .nc-top").count() == 0,
          page.locator("#s-diary .ncard .nc-topic").count())
    first_cls = page.evaluate("() => { const c = document.querySelector('#s-diary .ncard'); const k = c.firstElementChild; return k ? k.className : ''; }")
    check("카드 맨 윗줄은 제목", first_cls.startswith("nc-t"), first_cls)
    card_txt = page.locator("#s-diary .ncard").first.inner_text()
    check("카드에 날짜 없음", page.locator("#s-diary .ncard .nc-d").count() == 0 and
          not re.search(r"\d{4}\.\s*\d{1,2}\.\s*\d{1,2}", card_txt), card_txt.replace("\n", " / "))
    card_css = page.evaluate(CSS_OF, "#s-diary .ncard")
    # v21: 카드 끝을 둥글게(16px) 다듬었어요 — 예전 「각진 모서리」 기준을 현행에 맞춥니다
    check("카드 둥근 모서리(16px)", px(card_css["br"]) == 16, card_css["br"])
    check("카드 입체 그림자", card_css["sh"] not in ("none", ""), card_css["sh"])
    check("카드 그림자 두 겹", card_css["sh"].count("rgb") + card_css["sh"].count("rgba") >= 2, card_css["sh"])
    t_css = page.evaluate(CSS_OF, "#s-diary .ncard .nc-t")
    check("카테고리명 16px", px(t_css["fs"]) >= 16, t_css["fs"])
    # v23: 카드 제목은 얇게(400) · 가운데 정렬로 바뀜
    check("카테고리명 얇게(400)", int(t_css["fw"]) <= 400, t_css["fw"])
    body_fs = page.evaluate("() => getComputedStyle(document.body).fontSize")
    topic_fs = page.evaluate(
        "() => { const el = document.createElement('span'); el.className = 'nc-topic';"
        " document.querySelector('#s-diary').appendChild(el);"
        " const fs = getComputedStyle(el).fontSize; el.remove(); return fs; }")
    check("주제 줄 스타일 없음", topic_fs == body_fs, (topic_fs, body_fs))
    check("새 리스트 카드", page.locator("#s-diary .ncard.new").count() == 1)
    check("새 리스트 카드는 그림자 없음",
          page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ncard.new')).boxShadow")
          in ("none", ""), page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ncard.new')).boxShadow"))

    # 카드 상세: 제목만 고치기
    page.locator("#s-diary .ncard .nc-t").first.click()
    page.wait_for_timeout(450)
    check("카드 상세 시트", page.locator("#sheet .card-items").count() == 1)
    check("시트에 주제 입력칸 없음", page.locator('#sheetForm input[name="topic"]').count() == 0)
    labels = page.evaluate("() => Array.from(document.querySelectorAll('#sheetForm label')).map(l => l.innerText.trim())")
    check("시트 라벨은 제목만", labels == ["제목"], labels)
    check("날짜 안내 문구 없음", "만든 날" not in page.locator("#sheet").inner_text())
    for word in ("우유 사기", "계란", "카카오페이 충전"):
        page.fill('#sheet #listAddForm input[name="text"]', word)
        page.click("#sheet .todo-add-btn")
        page.wait_for_timeout(320)
    check("시트에서 항목 추가", page.locator("#sheet .card-items .trow").count() == 3,
          page.locator("#sheet .card-items .trow").count())
    page.locator("#sheet .card-items .trow .circ").first.click()
    page.wait_for_timeout(420)
    check("시트 안에서 완료", page.locator("#sheet .card-items .trow.done").count() == 1)
    shot(page, "note-detail-v15.png", settle=700)
    page.click('#sheet .card-acts .btn-primary')
    page.wait_for_timeout(700)
    check("카드 저장 후 닫힘", page.locator("#sheetWrap.open").count() == 0)
    check("저장해도 카드엔 제목만", page.locator("#s-diary .ncard .nc-topic").count() == 0,
          page.locator("#s-diary .ncard .nc-topic").count())
    check("카테고리명은 그대로", page.locator("#s-diary .ncard .nc-t").first.inner_text().strip() == "메모",
          page.locator("#s-diary .ncard .nc-t").first.inner_text())
    check("카드에 항목 미리보기", page.locator("#s-diary .ncard .nc-items .cti").count() >= 3,
          page.locator("#s-diary .ncard .nc-items .cti").count())
    items_css = page.evaluate(CSS_OF, "#s-diary .ncard .nc-items .cti .cx")
    check("리스트 14px", px(items_css["fs"]) >= 14, items_css["fs"])
    check("리스트 얇게(400 이하)", int(items_css["fw"]) <= 400, items_css["fw"])
    check("리스트가 제목보다 작음", px(items_css["fs"]) < px(t_css["fs"]), (items_css["fs"], t_css["fs"]))
    check("완료 항목 취소선", page.evaluate(
        "() => { const el = document.querySelector('#s-diary .ncard .cti.on .cx'); return el ? getComputedStyle(el).textDecorationLine : ''; }")
        == "line-through")
    page.locator("#s-diary .ncard .nc-t").first.scroll_into_view_if_needed()
    shot(page, "note-v15.png")

    # 카드 밖에서 체크 토글은 그대로
    done_before = page.locator("#s-diary .ncard .cti.on").count()
    page.locator("#s-diary .ncard .cti").last.click()
    page.wait_for_timeout(500)
    check("카드에서 바로 체크", page.locator("#s-diary .ncard .cti.on").count() != done_before,
          (done_before, page.locator("#s-diary .ncard .cti.on").count()))

    # 새 카드 만들기 (v17: 제목만)
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(400)
    check("새 카드 시트에 주제 칸 없음", page.locator('#sheetForm input[name="topic"]').count() == 0)
    page.fill('#sheetForm input[name="title"]', "장보기")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(650)
    check("새 카드 추가", page.locator("#s-diary .ncard").count() == 3, page.locator("#s-diary .ncard").count())
    new_titles = page.evaluate("() => Array.from(document.querySelectorAll('#s-diary .ncard .nc-t')).map(e => e.innerText.trim())")
    check("새 카드 제목 저장", "장보기" in new_titles, new_titles)

    # 새로 열어도 제목·그림자 그대로
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(600)
    titles2 = page.evaluate("() => Array.from(document.querySelectorAll('#s-diary .ncard .nc-t')).map(e => e.innerText.trim())")
    check("새로 열어도 제목 유지", "메모" in titles2 and "장보기" in titles2, titles2)
    check("새로 열어도 주제 줄 없음", page.locator("#s-diary .ncard .nc-topic").count() == 0)
    check("새로 열어도 그림자", page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ncard')).boxShadow")
          not in ("none", ""))

    # 다크 모드
    page.evaluate("document.documentElement.setAttribute('data-mode','dark')")
    page.wait_for_timeout(400)
    dark_sh = page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ncard')).boxShadow")
    check("다크 카드 그림자", dark_sh not in ("none", ""), dark_sh)
    shot(page, "note-dark-v15.png", settle=320)
    page.evaluate("document.documentElement.setAttribute('data-mode','light')")
    page.wait_for_timeout(300)

    # ---------- 5. 좁은 화면(375px)에서 카드가 넘치지 않는지 ----------
    ctx2 = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    page2 = ctx2.new_page()
    errs2 = []
    page2.on("pageerror", lambda e: errs2.append(str(e)))
    page2.on("console", lambda m: errs2.append(m.text) if m.type == "error" else None)
    page2.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page2.wait_for_timeout(700)
    page2.locator("#tabbar .tab").nth(2).click()
    page2.wait_for_timeout(500)
    wide = page2.evaluate("""() => {
      const g = document.querySelector('#s-diary .ngrid');
      const cards = Array.from(document.querySelectorAll('#s-diary .ncard')).map(c => {
        const r = c.getBoundingClientRect(); return {x: r.x, w: r.width, right: r.right, over: c.scrollWidth - c.clientWidth}; });
      return {pageOver: document.documentElement.scrollWidth - 375, gridOver: g.scrollWidth - g.clientWidth, cards: cards}; }""")
    check("375px 카드 넘침 없음", wide["pageOver"] <= 1 and wide["gridOver"] <= 1
          and all(c["over"] <= 1 and c["right"] <= 375 for c in wide["cards"]), wide)
    page2.screenshot(path=os.path.join(SHOT, "note-375-v15.png"))
    check("375px 콘솔 오류 없음", len(errs2) == 0, errs2[:2])
    ctx2.close()

    # ---------- 6. 서비스 워커 버전 ----------
    ver = page.evaluate("fetch('sw.js').then(r => r.text()).then(t => (t.match(/twolog-v\\d+/) || [''])[0])")
    check("sw 캐시 v17", ver == "twolog-v17", ver)
    check("콘솔 오류 없음", len(errors) == 0, errors[:3])
    browser.close()

print()
print("실패:", fails if fails else "없음")
print("스크린샷:", SHOT)
sys.exit(1 if fails else 0)
