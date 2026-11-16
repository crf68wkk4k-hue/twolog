"""투로그 v14 확인 — 홈 D-day 히어로(프사 양옆·크게)·일정 색 띠·홈 제목 색 통합·
기념일 시트(「우리는」·생일 달력)·캘린더 생일 위치·노트 카드 그리드.

    python3 tests/v14.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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
  const s = getComputedStyle(el); const r = el.getBoundingClientRect();
  return {bw: s.borderTopWidth, bg: s.backgroundColor, mt: s.marginTop, fs: s.fontSize,
  lh: s.lineHeight, h: r.height, w: r.width, x: r.x, y: r.y, txt: el.innerText}; }"""
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

    # ---------- 1. 캘린더: 생일 줄이 달력 바로 아래 ----------
    cal_box = page.evaluate(CSS_OF, "#s-cal .cal")
    bd = page.evaluate(CSS_OF, "#s-cal .bday-note")
    panel = page.evaluate(CSS_OF, "#s-cal .daypanel")
    check("생일 줄 있음", bd is not None and "생일" in (bd["txt"] or ""), bd and bd["txt"].replace("\n", " / "))
    check("생일 줄이 달력 아래", bd and cal_box and bd["y"] > cal_box["y"] + cal_box["h"] - 2,
          (cal_box and round(cal_box["y"] + cal_box["h"]), bd and round(bd["y"])))
    check("생일 줄이 날짜 목록 위", bd and panel and bd["y"] < panel["y"],
          (bd and round(bd["y"]), panel and round(panel["y"])))
    check("생일 「6월 26일」 표기", bd and "6월 26일" in bd["txt"], bd and bd["txt"])
    page.locator(".bday-note").scroll_into_view_if_needed()
    shot(page, "cal-v14.png")

    # 생일 시트: 달력(input[type=date])로 고치기
    page.locator(".bday-note").click()
    page.wait_for_timeout(400)
    kinds = page.evaluate("""() => Array.from(document.querySelectorAll('#sheet input[name], #sheet input'))
      .filter(i => i.name === 'me' || i.name === 'you').map(i => i.type + ':' + i.value)""")
    check("생일 시트 달력 입력", len(kinds) == 2 and all(k.startswith("date:") for k in kinds), kinds)
    page.fill('#sheetForm input[name="you"]', "2000-03-14")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(600)
    check("생일 저장", "3월 14일" in page.locator(".bday-note").inner_text(), page.locator(".bday-note").inner_text())

    # ---------- 2. 홈 D-day 히어로 ----------
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(500)
    dd = page.evaluate(CSS_OF, ".dday")
    check("D-day 테두리 없음", dd and dd["bw"] == "0px", dd and dd["bw"])
    check("D-day 바탕 없음", dd and dd["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), dd and dd["bg"])
    check("D-day 위 여백", dd and float(dd["mt"].replace("px", "")) >= 30, dd and dd["mt"])

    sides = page.evaluate("""() => Array.from(document.querySelectorAll('.dday .dday-side .av')).map(el => {
      const r = el.getBoundingClientRect(); return {x: r.x, y: r.y, w: r.width, h: r.height}; })""")
    mid = page.evaluate(CSS_OF, ".dday-mid")
    check("프사 두 개", len(sides) == 2, sides)
    check("프사 크게(64px 이상)", all(s["w"] >= 64 and abs(s["w"] - s["h"]) < 1 for s in sides), sides)
    check("프사 동그라미", page.evaluate(
        "() => getComputedStyle(document.querySelector('.dday .dday-side .av')).borderRadius") in ("50%", "999px", "33px"),
        page.evaluate("() => getComputedStyle(document.querySelector('.dday .dday-side .av')).borderRadius"))
    check("가운데 글씨 왼쪽 프사 오른쪽", sides and mid and sides[0]["x"] + sides[0]["w"] <= mid["x"] + 1
          and sides[1]["x"] >= mid["x"] + mid["w"] - 1,
          (sides and round(sides[0]["x"] + sides[0]["w"]), mid and round(mid["x"]), mid and round(mid["x"] + mid["w"]),
           sides and round(sides[1]["x"])))
    check("D+ 숫자 가운데", page.locator(".dday-mid .dday-num").count() == 1 and
          page.locator(".dday-mid").inner_text().startswith("소영과 준영이 함께한 지"))
    check("한 줄에 다 들어감", dd and all(s["x"] >= 0 and s["x"] + s["w"] <= 391 for s in sides), sides)
    shot(page, "home-v14.png")

    # ---------- 3. 다가오는 일정: 프사 없이 색 띠만 ----------
    check("일정 줄 색 띠", page.locator(".row.sched .bar").count() >= 1, page.locator(".row.sched .bar").count())
    check("일정 줄 프사 없음", page.locator(".row.sched .av").count() == 0, page.locator(".row.sched .av").count())
    check("일정 줄 who-row 없음", page.locator(".row.sched .who-row").count() == 0)
    check("일정 날짜·D-day", page.locator(".row.sched .smeta .sd").count() >= 1 and page.locator(".row.sched .sl").count() >= 1)
    bar = page.evaluate(CSS_OF, ".row.sched .bar")
    check("색 띠 색 있음", bar and bar["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"), bar and bar["bg"])

    # ---------- 4. 홈 제목 색: 한 곳으로 묶이고 제목 줄에만 ----------
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(420)
    stxt = page.locator("#sheet").inner_text()
    check("테마 시트 이름 컬러", "컬러" in stxt, stxt[:60])
    check("제목 색 항목 하나로 통합", "다가오는 일정 · " in stxt and "월의 우리" in stxt, stxt[:160])
    check("옛 두 항목 없음", stxt.count("다가오는 일정") == 1, stxt.count("다가오는 일정"))
    check("컬러 라벨", page.locator("#sheet .cp-pick span", has_text="컬러").count() >= 1)
    check("뮤트 10색", page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count() == 10,
          page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count())
    shot(page, "theme-sheet-v14.png", settle=350)
    page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').nth(0).click()
    page.wait_for_timeout(450)
    check("시트 유지", page.locator("#sheetWrap.open").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    sec_sched = page.evaluate(CSS_OF, ".home-sec[data-sec='sched']")
    sec_our = page.evaluate(CSS_OF, ".home-sec[data-sec='our']")
    hd_sched = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    hd_our = page.evaluate(CSS_OF, ".home-sec[data-sec='our'] .sec-tint")
    check("섹션 전체는 투명", sec_sched and sec_sched["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), sec_sched and sec_sched["bg"])
    check("두 제목 줄 같은 색", hd_sched and hd_our and hd_sched["bg"] == hd_our["bg"], (hd_sched and hd_sched["bg"], hd_our and hd_our["bg"]))
    check("제목 줄에만 색", hd_sched and hd_sched["bg"] not in ("rgba(0, 0, 0, 0)", "transparent"), hd_sched and hd_sched["bg"])
    check("카드는 흰 바탕", page.evaluate("() => getComputedStyle(document.querySelector('.home-sec .bcard')).backgroundColor")
          != (hd_sched and hd_sched["bg"]))
    check("제목 글씨 진하게", hd_sched and page.evaluate(
        "() => getComputedStyle(document.querySelector(\".home-sec[data-sec='sched'] .sec-tint h2\")).color") == "rgb(17, 17, 17)",
        page.evaluate("() => getComputedStyle(document.querySelector(\".home-sec[data-sec='sched'] .sec-tint h2\")).color"))
    shot(page, "home-tinted-v14.png")

    # 색 해제
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(350)
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(350)
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    check("제목 색 해제", page.evaluate("() => getComputedStyle(document.querySelector('.sec-tint')).backgroundColor")
          in ("rgba(0, 0, 0, 0)", "transparent"))

    # ---------- 5. D-day 시트 ----------
    page.locator("#s-home .dday").click()
    page.wait_for_timeout(450)
    labels = page.evaluate("""() => Array.from(document.querySelectorAll('#sheetForm label')).map(l => l.innerText.trim())""")
    check("첫 라벨이 「우리는」", labels and labels[0] == "우리는", labels[:4])
    check("「기념일 문구」 사라짐", "기념일 문구" not in page.locator("#sheet").inner_text())
    stxt2 = page.locator("#sheet").inner_text()
    check("주년 세 줄", all(k in stxt2 for k in ["1주년", "2주년", "3주년"]), stxt2[:160])
    check("생일 두 줄", ("소영 생일" in stxt2) and ("준영 생일" in stxt2))
    bdays = page.evaluate("""() => Array.from(document.querySelectorAll('#sheet input.js-bday')).map(i => i.type + '|' + i.name + '|' + i.value)""")
    check("생일 달력 입력 두 개", len(bdays) == 2 and all(b.startswith("date|bd") for b in bdays), bdays)
    check("소영 생일 1992", any("1992-06-26" in b for b in bdays), bdays)
    shot(page, "dday-sheet-v14.png", settle=350)
    # 달력으로 바꾸면 D-day 가 바로 바뀌는지
    page.fill('#sheet input[name="bdYou"]', "2000-11-20")
    page.wait_for_timeout(350)
    left = page.locator('#sheet [data-bdleft="you"]').inner_text()
    check("생일 D-day 즉시 갱신", left.startswith("D-"), left)
    page.fill('#sheetForm input[name="phrase"]', "우리 둘의 기록")
    page.fill('#sheetForm input[name="since"]', "2025-11-16")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(650)
    check("문구 저장", "우리 둘의 기록" in page.locator("#s-home .dday").inner_text(), page.locator("#s-home .dday").inner_text())
    page.locator("#s-home .dday").click()
    page.wait_for_timeout(400)
    check("생일 저장 유지", "11월 20일" in page.locator("#sheet").inner_text(), page.locator("#sheet [data-bdtxt='you']").inner_text())
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---------- 6. 노트: 카드 그리드 ----------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(500)
    cards = page.locator("#s-diary .ngrid .ncard")
    check("카드 그리드 있음", cards.count() >= 1, cards.count())
    grid = page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ngrid')).gridTemplateColumns")
    check("두 열", len(grid.split(" ")) == 2, grid)
    first = page.locator("#s-diary .ncard").first
    check("카드 프사+이름", page.locator("#s-diary .ncard .nc-av").count() >= 1 and
          page.locator("#s-diary .ncard .nc-who").first.inner_text().strip() == "소영",
          page.locator("#s-diary .ncard .nc-who").first.inner_text())
    check("카드 제목", page.locator("#s-diary .ncard .nc-t").first.inner_text().strip() == "메모",
          page.locator("#s-diary .ncard .nc-t").first.inner_text())
    check("카드 날짜", page.locator("#s-diary .ncard .nc-d").first.inner_text().strip().count(".") == 2,
          page.locator("#s-diary .ncard .nc-d").first.inner_text())
    check("카드 각진 모서리", page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ncard')).borderTopLeftRadius")
          in ("0px", "0"), page.evaluate("() => getComputedStyle(document.querySelector('#s-diary .ncard')).borderTopLeftRadius"))
    check("새 리스트 카드", page.locator("#s-diary .ncard.new").count() == 1)

    # 카드 안에서 바로 체크
    page.locator("#s-diary .ncard .nc-t").first.click()
    page.wait_for_timeout(450)
    check("카드 상세 시트", page.locator("#sheet .card-items").count() == 1)
    check("To-do 입력 줄", page.locator('#sheet #listAddForm input[name="text"]').count() == 1)
    check("Add 버튼", page.locator("#sheet .todo-add-btn").count() == 1)
    for word in ("우유 사기", "계란", "카카오페이 충전"):
        page.fill('#sheet #listAddForm input[name="text"]', word)
        page.click("#sheet .todo-add-btn")
        page.wait_for_timeout(320)
    check("시트에서 항목 추가", page.locator("#sheet .card-items .trow").count() == 3,
          page.locator("#sheet .card-items .trow").count())
    page.locator("#sheet .card-items .trow .circ").first.click()
    page.wait_for_timeout(420)
    check("시트 안에서 완료", page.locator("#sheet .card-items .trow.done").count() == 1,
          page.locator("#sheet .card-items .trow.done").count())
    check("시트 유지(닫히지 않음)", page.locator("#sheetWrap.open").count() == 1)
    shot(page, "note-detail-v14.png", settle=500)
    # 닫으면 카드에도 바로 반영 (시트에서만 바뀌고 카드가 낡지 않도록)
    page.keyboard.press("Escape")
    page.wait_for_timeout(450)
    check("닫으면 카드에 반영", page.locator("#s-diary .ncard .nc-items .cti").count() == 3,
          page.locator("#s-diary .ncard .nc-items .cti").count())
    page.locator("#s-diary .ncard .cti").nth(1).click()
    page.wait_for_timeout(400)
    check("카드에서 체크해도 시트 안 열림", page.locator("#sheetWrap.open").count() == 0)
    page.locator("#s-diary .ncard .nc-t").first.click()
    page.wait_for_timeout(400)
    check("카드 다시 열림", page.locator("#sheetWrap.open").count() == 1)
    page.fill('#sheetForm input[name="caption"]', "이번 주말에 사 올 것")
    page.locator('#sheetForm .seg-btn[data-who="you"]').click()
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(700)
    check("카드 저장 후 닫힘", page.locator("#sheetWrap.open").count() == 0)
    check("카드 캡션 반영", "이번 주말에 사 올 것" in page.locator("#s-diary .ncard").first.inner_text(),
          page.locator("#s-diary .ncard").first.inner_text()[:80])
    check("카드 작성자 변경", page.locator("#s-diary .ncard .nc-who").first.inner_text().strip() == "준영",
          page.locator("#s-diary .ncard .nc-who").first.inner_text())
    check("카드에 항목 미리보기", page.locator("#s-diary .ncard .nc-items .cti").count() >= 3,
          page.locator("#s-diary .ncard .nc-items .cti").count())
    check("완료 항목 취소선", page.evaluate(
        "() => { const el = document.querySelector('#s-diary .ncard .cti.on .cx'); return el ? getComputedStyle(el).textDecorationLine : ''; }")
        == "line-through")
    shot(page, "note-v14.png")
    # 카드 밖에서 체크 토글
    done_before = page.locator("#s-diary .ncard .cti.on").count()
    page.locator("#s-diary .ncard .cti").last.click()
    page.wait_for_timeout(500)
    check("카드에서 바로 체크", page.locator("#s-diary .ncard .cti.on").count() != done_before,
          (done_before, page.locator("#s-diary .ncard .cti.on").count()))
    # 다크 모드
    page.evaluate("document.documentElement.setAttribute('data-mode','dark')")
    page.wait_for_timeout(350)
    shot(page, "note-dark-v14.png", settle=300)
    page.evaluate("document.documentElement.setAttribute('data-mode','light')")
    page.wait_for_timeout(250)

    # 새 카드 만들기
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(400)
    page.fill('#sheetForm input[name="title"]', "여행 준비물")
    page.fill('#sheetForm input[name="caption"]', "제주도 가기 전에")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(600)
    check("새 카드 추가", page.locator("#s-diary .ncard").count() == 3, page.locator("#s-diary .ncard").count())

    # 다른 탭도 카드로
    page.locator("#s-diary .seg-btn").nth(1).click()
    page.wait_for_timeout(450)
    check("버킷리스트도 카드", page.locator("#s-diary .ncard").count() >= 1, page.locator("#s-diary .ncard").count())
    page.locator("#s-diary .seg-btn").nth(2).click()
    page.wait_for_timeout(450)
    check("영화·먹방도 카드", page.locator("#s-diary .ncard").count() >= 1, page.locator("#s-diary .ncard").count())

    # ---------- 7. 375px 폭에서도 히어로가 넘치지 않는지 ----------
    ctx2 = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    page2 = ctx2.new_page()
    errs2 = []
    page2.on("pageerror", lambda e: errs2.append(str(e)))
    page2.on("console", lambda m: errs2.append(m.text) if m.type == "error" else None)
    page2.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page2.wait_for_timeout(700)
    wide = page2.evaluate("""() => {
      const d = document.querySelector('.dday');
      const avs = Array.from(document.querySelectorAll('.dday .dday-side .av')).map(e => {
        const r = e.getBoundingClientRect(); return {x: r.x, w: r.width}; });
      return {overflow: d.scrollWidth - d.clientWidth, left: avs[0].x, right: avs[1].x + avs[1].w,
              mid: document.querySelector('.dday-mid').getBoundingClientRect().width}; }""")
    check("375px 히어로 넘침 없음", wide["overflow"] <= 1 and wide["left"] >= 0 and wide["right"] <= 375, wide)
    check("375px 가운데 폭 확보", wide["mid"] >= 150, wide["mid"])
    page2.screenshot(path=os.path.join(SHOT, "home-375-v14.png"))
    check("375px 콘솔 오류 없음", len(errs2) == 0, errs2[:2])
    ctx2.close()

    # ---------- 8. 서비스 워커 버전 ----------
    ver = page.evaluate("fetch('sw.js').then(r => r.text()).then(t => (t.match(/twolog-v\\d+/) || [''])[0])")
    check("sw 캐시 v14", ver == "twolog-v14", ver)
    check("콘솔 오류 없음", len(errors) == 0, errors[:3])
    browser.close()

print()
print("실패:", fails if fails else "없음")
print("스크린샷:", SHOT)
sys.exit(1 if fails else 0)
