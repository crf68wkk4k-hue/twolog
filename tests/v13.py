"""투로그 v13 확인 — 홈 여백·섹션 뮤트색·캘린더 생일·노트 리스트·My 테마/알림 메뉴·배민 폰트.

    python3 tests/v13.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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
  const s = getComputedStyle(el); return {bw: s.borderTopWidth, bg: s.backgroundColor,
  mt: s.marginTop, fs: s.fontSize, lh: s.lineHeight, h: s.height}; }"""
DAY_OFFSET = """(n) => { const d = new Date(); d.setDate(d.getDate() + n);
  const p = x => String(x).padStart(2, '0');
  return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()); }"""


def shot(page, name, settle=1900):
    """토스트가 사라진 뒤 찍어 화면이 깔끔하게 남도록."""
    page.wait_for_timeout(settle)
    page.screenshot(path=os.path.join(SHOT, name))


with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    page.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page.wait_for_timeout(600)

    # ---------- 오늘·내일 일정 두 개 만들기 ----------
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(350)
    for title, offset in (("성수 데이트", 0), ("영화 보는 날", 1)):
        page.locator('#s-cal [data-act="addEvent"]').first.click()
        page.wait_for_timeout(300)
        page.fill('#sheetForm input[name="title"]', title)
        if offset:
            day = page.evaluate(DAY_OFFSET, offset)
            page.fill('#sheetForm input[name="start"]', day)
            page.fill('#sheetForm input[name="end"]', day)
        page.click('#sheetForm button[type="submit"]')
        page.wait_for_timeout(400)

    # ---------- 캘린더: 글씨 크기 (v15 에서 생일 줄은 지웠어요) ----------
    eb = page.evaluate(CSS_OF, ".ebar")
    check("캘린더 일정 글씨 9.5px", eb and eb["fs"] == "9.5px", eb)
    check("캘린더 일정 막대 높이", eb and float(eb["h"].replace("px", "")) >= 14, eb)
    check("생일 줄 없음", page.locator("#s-cal .bday-note").count() == 0,
          page.locator("#s-cal .bday-note").count())
    page.locator("#s-cal .cal").scroll_into_view_if_needed()
    shot(page, "cal-v13.png")

    # ---------- D-day 시트: 주년·생일 ----------
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(400)
    page.locator("#s-home .dday").click()
    page.wait_for_timeout(400)
    mile = page.locator("#sheet").inner_text()
    check("주년 세 줄", all(k in mile for k in ["1주년", "2주년", "3주년"]), mile[:120])
    check("생일 두 줄", ("소영 생일" in mile) and ("준영 생일" in mile))
    check("주년 날짜", mile.count(".") >= 3)
    page.fill('#sheetForm input[name="since"]', "2025-11-16")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(500)
    check("기념일 저장", "D+365" in page.locator("#s-home .dday").inner_text(), page.locator("#s-home .dday").inner_text())

    # ---------- 홈: D-day 테두리 없이 아래로 ----------
    dd = page.evaluate(CSS_OF, ".dday")
    check("D-day 테두리 없음", dd and dd["bw"] == "0px", dd)
    check("D-day 바탕 없음", dd and dd["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), dd)
    check("D-day 위 여백", dd and float(dd["mt"].replace("px", "")) >= 30, dd)
    check("홈 섹션 두 개", page.locator(".home-sec").count() == 2, page.locator(".home-sec").count())
    secs = page.evaluate(CSS_OF, ".home-sec[data-sec='sched']")
    check("홈 섹션 테두리 없음", secs and secs["bw"] == "0px", secs)
    h2 = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec h2")
    check("섹션 제목 16px", h2 and h2["fs"] == "16px", h2)
    lb = page.evaluate(CSS_OF, ".bcard .lb")
    check("카드 라벨 확대", lb and float(lb["fs"].replace("px", "")) >= 10, lb)
    t = page.evaluate(CSS_OF, ".row.sched .t")
    check("일정 글씨 확대", t and float(t["fs"].replace("px", "")) >= 14, t)
    check("일정 색 띠", page.locator(".row.sched .bar").count() >= 1, page.locator(".row.sched .bar").count())
    check("일정 날짜 표시", page.locator(".row.sched .smeta .sd").count() >= 1)
    check("공동 일정 하트", page.locator("#s-cal .who-row.both .heart").count() >= 1)
    shot(page, "home-v13.png")

    # ---------- 상단 팔레트: 다가오는 일정 / 11월의 우리 뮤트색 ----------
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(350)
    sheet_txt = page.locator("#sheet").inner_text()
    check("테마 시트 항목", ("다가오는 일정" in sheet_txt) and ("월의 우리" in sheet_txt), sheet_txt[:120])
    check("테마 시트 뮤트 12색", page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count() == 12,
          page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count())
    check("컬러 라벨", page.locator('#sheet .js-color[data-target="homeTitleBg"]').count() == 1)
    shot(page, "theme-sheet-v13.png", settle=300)
    page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').nth(0).click()
    page.wait_for_timeout(350)
    tint = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    check("제목 줄 바탕 적용", tint and tint["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"), tint)
    check("시트 유지", page.locator("#sheetWrap.open").count() == 1)
    page.keyboard.press("Escape")
    shot(page, "home-tinted-v13.png")
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(300)
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    check("뮤트색 해제", page.locator(".sec-tint").first.evaluate("el => getComputedStyle(el).backgroundColor")
          in ("rgba(0, 0, 0, 0)", "transparent"))

    # ---------- 노트: 리스트 안 To-do + 새 리스트 ----------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(450)
    check("메모 카드", page.locator("#s-diary .ncard").count() == 2, page.locator("#s-diary .ncard").count())
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(400)
    check("To-do 라벨", page.locator("#sheet .todo-label").count() == 1)
    check("To-do 입력 줄", page.locator('#sheet #listAddForm input[name="text"]').count() == 1)
    check("Add 버튼", page.locator("#sheet .todo-add-btn").count() == 1)
    for word in ("우유 사기", "계란", "카카오페이 충전"):
        page.fill('#sheet #listAddForm input[name="text"]', word)
        page.click("#sheet .todo-add-btn")
        page.wait_for_timeout(300)
    check("항목 바로 추가", page.locator("#sheet .card-items .trow").count() == 3, page.locator("#sheet .card-items .trow").count())
    page.locator("#sheet .card-items .trow .circ").first.click()
    page.wait_for_timeout(350)
    check("완료 표시", page.locator("#sheet .card-items .trow.done").count() >= 1)
    check("완료는 아래로", page.locator("#sheet .card-items .trow").last.evaluate("el => el.classList.contains('done')"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(350)
    page.fill('#sheetForm input[name="title"]', "장보기")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(450)
    check("새 리스트 추가", page.locator("#s-diary .ncard").count() == 3, page.locator("#s-diary .ncard").count())
    # v17: 한 줄 메모(캡션)·「주제」 칸은 없어졌어요 — 카드는 제목·항목만 보여 줍니다
    check("새 리스트 제목", "장보기" in page.locator("#s-diary").inner_text())
    shot(page, "note-v13.png")
    # 다크 모드도 같은 화면으로 확인
    page.evaluate("document.documentElement.setAttribute('data-mode','dark')")
    page.wait_for_timeout(300)
    shot(page, "note-dark-v13.png", settle=300)
    page.evaluate("document.documentElement.setAttribute('data-mode','light')")
    page.wait_for_timeout(200)

    # ---------- My: 이름 크게 + 테마 관리 / 알림 설정 메뉴 ----------
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(400)
    nm = page.evaluate(CSS_OF, "#s-set .set-who-nm")
    check("커플 이름 확대", nm and float(nm["fs"].replace("px", "")) >= 16, nm)
    rows = page.locator("#s-set .menu-row")
    check("메뉴 줄 두 개", rows.count() == 2, rows.count())
    shot(page, "my-v13.png")
    page.locator('#s-set .menu-row[data-act="openThemeManager"]').click()
    page.wait_for_timeout(400)
    tm = page.locator("#sheet").inner_text()
    check("테마 관리 시트", all(k in tm for k in ["화면", "페이지 캡션 색", "일정 색", "홈 제목 색", "폰트"]), tm[:160])
    check("배민 폰트 5종", all(n in tm for n in ["배민 주아체", "배민 도현체", "배민 한나체 Pro", "배민 연성체", "배민 을지로체"]))
    shot(page, "theme-manager-v13.png", settle=400)
    loaded = page.evaluate("""() => {
      const want = ['BM Jua','BM Dohyeon','BM Hanna Pro','BM Yeonsung','BM Euljiro'];
      return Promise.all(want.map(f => document.fonts.load("16px '" + f + "'").then(() => document.fonts.check("16px '" + f + "'")).catch(() => false)));
    }""")
    check("배민 폰트 로드", all(loaded), loaded)
    page.locator('#sheet .font-row[data-font="jua"]').click()
    page.wait_for_timeout(400)
    fam = page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--font')")
    check("폰트 적용", "BM Jua" in fam, fam)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    page.locator('#s-set .menu-row[data-act="openNotifSheet"]').click()
    page.wait_for_timeout(400)
    check("알림 시트", page.locator("#sheet .notif").count() == 3, page.locator("#sheet .notif").count())
    page.locator('#sheet .notif[data-key="anni"]').click()
    page.wait_for_timeout(300)
    check("알림 토글", page.locator('#sheet .notif[data-key="anni"] .tgl.on').count() == 0)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    # ---------- 사람 시트: 닉네임 / 연결 버튼 ----------
    page.locator('#s-set .row[data-who="me"]').first.click()
    page.wait_for_timeout(400)
    me_txt = page.locator("#sheet").inner_text()
    check("내 프로필 닉네임", "닉네임 바꾸기" in me_txt, me_txt[:80])
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)
    page.locator('#s-set .row[data-who="you"]').first.click()
    page.wait_for_timeout(400)
    you_txt = page.locator("#sheet").inner_text()
    check("상대 닉네임", "닉네임 설정" in you_txt, you_txt[:80])
    check("연결 버튼", ("연결 끊기" in you_txt) or ("연결하기" in you_txt) or ("재연결" in you_txt), you_txt[:120])
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("콘솔 오류 없음", len(errors) == 0, errors[:3])
    browser.close()

print()
print("실패:", fails if fails else "없음")
print("스크린샷:", SHOT)
sys.exit(1 if fails else 0)
