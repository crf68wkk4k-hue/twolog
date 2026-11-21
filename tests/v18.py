"""투로그 v18 확인 — 홈 간격, 사진첩 3폴라로이드+뷰어, 노트 설정 이모지 통합,
노트 상단 탭 네모 분리·글씨 확대, 꾹 눌러 순서 이동, 캘린더 그날 타임라인,
My 4자리 잠금, PDF 내보내기.

    python3 tests/v18.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

fails = []


def check(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + str(extra)) if extra else ""))
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
errors = []


def open_note_settings(page):
    """v29: 노트 맨 윗줄의 네모 설정 버튼이 없어져, 「📖 노트」 제목을 600ms 꾹 눌러 노트 설정을 엽니다."""
    box = page.locator("#s-diary .note-h1").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.wait_for_timeout(720)
    page.mouse.up()
    page.wait_for_timeout(500)


with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")  # v25: 이 테스트는 로컬 모드 고정
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # 예시 데이터로 한 번 열어 상태를 만들고, 저장이 되는 일반 모드로 옮겨요
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)

    # ---------------- 홈 간격 ----------------
    dday = page.evaluate("(() => { const e = document.querySelector('#s-home .dday'); const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return {mt: cs.marginTop, top: r.top}; })()")
    check("홈 D-day 한 줄 위로 (margin-top 74px)", dday["mt"] == "74px", dday)
    sec = page.evaluate("(() => { const e = document.querySelector('#s-home .dday + .home-sec'); return {mt: getComputedStyle(e).marginTop, txt: e.innerText.split('\\n')[0]}; })()")
    check("다가오는 일정 두 줄 아래로 (margin-top 58px)", sec["mt"] == "58px" and "다가오는" in sec["txt"], sec)
    # v23: 홈에서 「N월의 우리」 섹션이 사라져 다가오는 일정이 마지막 섹션
    sec2 = page.evaluate("(() => { const a = document.querySelectorAll('#s-home .home-sec'); return a.length; })()")
    check("홈 섹션은 다가오는 일정 하나", sec2 == 1, sec2)
    page.screenshot(path=os.path.join(SHOT, "home-v18.png"))
    page.screenshot(path=os.path.join(SHOT, "home-v18-full.png"), full_page=True)

    # ---------------- 사진첩 ----------------
    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(500)
    days = page.evaluate("Array.from(document.querySelectorAll('#s-photo .pday')).map(d => d.querySelectorAll('.pola').length)")
    check("날짜마다 폴라로이드 3개까지", all(n <= 3 for n in days) and days[:1] == [3], days)
    more = page.evaluate("(() => { const m = document.querySelector('#s-photo .pola-more'); return m ? m.textContent : null; })()")
    check("3장 넘는 날은 +N 표기", more == "+3", more)
    grid = page.evaluate("getComputedStyle(document.querySelector('#s-photo .polas')).gridTemplateColumns")
    check("한 줄에 3열", len(grid.split(" ")) == 3, grid)
    page.screenshot(path=os.path.join(SHOT, "photo-v18.png"))

    # v39: 목록은 예전 날짜가 위 · 최근 날짜가 아래 — 사진이 가장 많은(6장) 최근 날짜를 봅니다
    first = page.locator("#s-photo .pola").last
    first_title = page.evaluate("(window.__app.state.photos[0] || {}).title || ''")   # v40: 목록엔 캡션 줄이 없어요
    first.click()
    page.wait_for_timeout(500)
    # v38: 날짜 모아보기가 먼저 — 사진을 누르면 크게 보기
    check("폴라로이드를 누르면 그날 모아보기", page.locator("#s-photo .dgrid").count() == 1)
    page.locator("#s-photo .dg-cell").first.click()
    page.wait_for_timeout(450)
    check("사진 크게 보기 열림", page.locator("#sheet .pview").count() == 1)
    img = page.evaluate("(() => { const v = document.querySelector('#sheet .pview img'); const s = document.querySelector('#sheet .pview svg'); return {img: !!v, svg: !!s, h: document.querySelector('#sheet .pview').getBoundingClientRect().height}; })()")
    check("사진이 뷰어에 크게", (img["img"] or img["svg"]) and img["h"] > 200, img)
    # v40: 크게 보기는 사진만 — 같은 날 사진은 «옆으로 밀어서» 넘어가요
    slides = page.evaluate("document.querySelectorAll('#sheet .pv40-slide').length")
    check("같은 날 사진이 옆으로 이어짐 (넘겨보기)", slides == 6, slides)
    page.screenshot(path=os.path.join(SHOT, "photo-detail-v18.png"))
    page.evaluate("(() => { const s = document.querySelector('#sheet .pv40-strip'); s.scrollBy({ left: s.clientWidth }); })()")
    page.wait_for_timeout(420)
    left1 = page.evaluate("Math.round(document.querySelector('#sheet .pv40-strip').scrollLeft)")
    check("옆으로 밀면 다음 사진으로 넘어감", left1 > 100, left1)
    page.evaluate("(() => { const s = document.querySelector('#sheet .pv40-strip'); s.scrollBy({ left: -s.clientWidth }); })()")
    page.wait_for_timeout(420)
    left2 = page.evaluate("Math.round(document.querySelector('#sheet .pv40-strip').scrollLeft)")
    check("되돌아오면 첫 사진", left2 <= 4, left2)
    # v43: 사진마다 ⋯ 메뉴는 없앴어요 — 크게 보기에는 아무 버튼도 없고,
    #      날짜·기록 이름·순서·빼기·추가는 모아보기 오른쪽 위 연필(사진 수정) 시트에서 해요
    page.locator("#sheet .pv40-slide").first.click()
    page.wait_for_timeout(600)
    check("크게 보기에는 수정·삭제 버튼이 없음", page.locator('#sheet [data-act="photoDelete"]').count() == 0)
    page.locator('#s-photo [data-act="editPhotoDay"]').first.click()
    page.wait_for_timeout(600)
    check("날짜 사진 수정 시트에서 사진을 뺄 수 있음 (⋯ 메뉴 대신)",
          page.locator('#sheet [data-act="upDel"]').count() >= 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    # ---------------- 노트 상단 탭 ----------------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(450)
    segs = page.evaluate("""(() => {
      const box = document.querySelector('#s-diary .segs');
      if (!box) return null;
      const btns = Array.from(box.querySelectorAll('.seg-btn'));
      const cs = getComputedStyle(box);
      return {n: btns.length, gap: cs.gap, fs: getComputedStyle(btns[0]).fontSize, h: btns[0].getBoundingClientRect().height,
              bw: btns[0].getBoundingClientRect().width, bg: cs.backgroundColor};
    })()""")
    check("탭이 각각 네모 칸으로 분리", segs is not None and segs["n"] == 3 and segs["gap"] == "8px", segs)
    # v29: 알약 탭을 조금 줄였어요 (15.5px·44px → 14px·40px)
    check("탭 글씨 14px", segs is not None and segs["fs"] == "14px", segs.get("fs") if segs else None)
    check("탭 칸 높이 40px", segs is not None and round(segs["h"]) == 40, segs.get("h") if segs else None)
    nct = page.evaluate("getComputedStyle(document.querySelector('#s-diary .ncard .nc-t')).fontSize")
    # v22: 사용자 요청으로 카드 제목을 더 작게(13.5px) 줄였어요
    check("카드 제목 13.5px", nct == "13.5px", nct)
    page.screenshot(path=os.path.join(SHOT, "note-v18.png"))

    # ---------------- 노트 설정: 이모지 + 이름 한 칸 ----------------
    open_note_settings(page)
    emo_inputs = page.locator("#sheet .nt-emo").count()
    names = page.evaluate("Array.from(document.querySelectorAll('#sheet #noteForm .nt-nm')).map(i => i.name + '=' + i.value)")
    check("이모지 칸이 사라짐", emo_inputs == 0, emo_inputs)
    # v33: 기본 탭은 이모지 없이 이름만
    check("탭 이름이 한 칸에 함께 표시", names[:3] == ["t_todo=메모", "t_bucket=버킷리스트", "t_log=영화·먹방"], names[:3])
    page.screenshot(path=os.path.join(SHOT, "note-settings-v18.png"))
    # 이모지 없이 이름만 넣어도 그대로 보이게
    page.fill("#sheet input[name='t_log']", "함께 보는 기록")
    page.click("#sheet #noteForm button[type='submit']")
    page.wait_for_timeout(450)
    labels = page.evaluate("Array.from(document.querySelectorAll('#s-diary .segs .seg-btn')).map(b => b.textContent)")
    check("이모지 없이 적은 이름 그대로", labels[2] == "함께 보는 기록", labels)
    # 다시 이모지 + 이름
    open_note_settings(page)
    page.fill("#sheet input[name='t_log']", "🍿 함께 보는 기록")
    page.click("#sheet #noteForm button[type='submit']")
    page.wait_for_timeout(400)
    labels2 = page.evaluate("Array.from(document.querySelectorAll('#s-diary .segs .seg-btn')).map(b => b.textContent)")
    check("이모지 + 이름 함께 저장", labels2[2] == "🍿 함께 보는 기록", labels2)

    # ---------------- 꾹 눌러 순서 바꾸기 ----------------
    # 순서를 바꿔 볼 카드 두 장을 먼저 만들어요
    for nm in ("장보기", "여행 준비"):
        page.locator("#s-diary .ncard.new").click()
        page.wait_for_timeout(300)
        page.fill("#sheetForm input[name='title']", nm)
        page.click("#sheet #sheetForm button[type='submit']")
        page.wait_for_timeout(400)
    page.wait_for_timeout(200)
    before = page.evaluate("Array.from(document.querySelectorAll('#s-diary .ngrid .ncard[data-gid]')).map(n => n.querySelector('.nc-t').textContent)")
    if len(before) >= 2:
        box0 = page.locator("#s-diary .ngrid .ncard[data-gid]").nth(0).bounding_box()
        box1 = page.locator("#s-diary .ngrid .ncard[data-gid]").nth(1).bounding_box()
        page.mouse.move(box0["x"] + box0["width"] / 2, box0["y"] + 20)
        page.mouse.down()
        page.wait_for_timeout(520)
        lifted = page.evaluate("document.querySelectorAll('#s-diary .ncard.lift').length")
        check("꾹 누르면 카드가 들림", lifted == 1, lifted)
        page.mouse.move(box1["x"] + box1["width"] / 2 + 10, box1["y"] + 20, steps=8)
        page.wait_for_timeout(160)
        page.mouse.move(box1["x"] + box1["width"] - 6, box1["y"] + 20, steps=4)
        page.wait_for_timeout(120)
        page.mouse.up()
        page.wait_for_timeout(500)
        after = page.evaluate("Array.from(document.querySelectorAll('#s-diary .ngrid .ncard[data-gid]')).map(n => n.querySelector('.nc-t').textContent)")
        check("끌어 놓은 자리로 순서 변경", after != before and sorted(after) == sorted(before), (before, after))
        saved = page.evaluate("window.__app.state.groups.todo.map(g => g.title)")
        check("바뀐 순서가 상태에 저장", saved == after, saved)
        page.reload(wait_until="networkidle")
        page.wait_for_timeout(700)
        page.locator("#tabbar .tab").nth(2).click()
        page.wait_for_timeout(400)
        after2 = page.evaluate("Array.from(document.querySelectorAll('#s-diary .ngrid .ncard[data-gid]')).map(n => n.querySelector('.nc-t').textContent)")
        check("새로 열어도 순서 유지", after2 == after, (after, after2))
    else:
        check("순서 바꾸기 (카드 2개 이상 필요)", False, before)

    # 내 리스트의 To-do 항목도 꾹 눌러 순서를 바꿀 수 있어요
    # (v40: 내 카테고리는 2열 카드 묶음 — 카드를 열어 그 안의 항목 순서를 바꿉니다)
    chip = page.locator("#s-diary .lchip").first
    if chip.count():
        chip.click()
        page.wait_for_timeout(420)
        is_cards = page.evaluate("!!document.querySelector('#s-diary .ngrid .ncard[data-gid]')")
        if is_cards:
            page.locator("#s-diary .ngrid .ncard[data-gid]").first.click()
            page.wait_for_timeout(520)
        rows0 = page.evaluate("Array.from(document.querySelectorAll('#sheet .card-items .trow .t')).map(e => e.textContent)")
        if len(rows0) >= 2:
            rb0 = page.locator("#sheet .card-items .trow").nth(0).bounding_box()
            rb1 = page.locator("#sheet .card-items .trow").nth(1).bounding_box()
            page.mouse.move(rb0["x"] + 30, rb0["y"] + rb0["height"] / 2)
            page.mouse.down()
            page.wait_for_timeout(520)
            page.mouse.move(rb1["x"] + 30, rb1["y"] + rb1["height"] - 4, steps=8)
            page.wait_for_timeout(160)
            page.mouse.up()
            page.wait_for_timeout(450)
            rows1 = page.evaluate("Array.from(document.querySelectorAll('#sheet .card-items .trow .t')).map(e => e.textContent)")
            check("카드 안 항목 순서도 바뀜", rows1 != rows0 and sorted(rows1) == sorted(rows0), (rows0, rows1))
            saved_rows = page.evaluate("(window.__app.state.lists.find(l => l.items.length >= 2) || {items: []}).items.map(i => i.text || i.title)")
            check("항목 순서도 저장됨", saved_rows == rows1, (saved_rows, rows1))
            page.keyboard.press("Escape")
            page.wait_for_timeout(350)
        else:
            check("카드 안 항목 2개 이상", False, rows0)
    else:
        check("내 리스트 칩", False)

    # ---------------- 캘린더: 그날 «일정만» (v21 에서 메모·기록·사진 묶음 삭제) ----------------
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(450)
    day = page.evaluate("(() => { const p = window.__app.state.photos[0]; return p ? p.date.slice(0,10) : null; })()")
    page.locator("#s-cal .day[data-date='%s']" % day).click()
    page.wait_for_timeout(400)
    tl = page.evaluate("""(() => {
      const ph = document.querySelectorAll('#s-cal .dp-ph').length;
      const memo = document.querySelectorAll('#s-cal .dp-memo').length;
      const sec = document.querySelectorAll('#s-cal .dp-sec').length;
      const empty = document.querySelector('#s-cal .daylist .empty');
      return {ph, memo, sec, empty: empty ? empty.textContent.trim() : null};
    })()""")
    check("사진이 있는 날에도 사진 묶음은 안 보임", tl["ph"] == 0, tl)
    check("기록·메모 묶음도 안 보임", tl["memo"] == 0 and tl["sec"] == 0, tl)
    check("일정이 없는 날은 안내 문구만", tl["empty"] == "이 날은 아직 일정이 없어요.", tl)
    # 일정을 하나 더해 그날에는 일정만 보이는지
    page.locator("#s-cal [data-act='addEvent']").first.click()
    page.wait_for_timeout(300)
    page.fill("#sheetForm input[name='title']", "그날의 데이트")
    page.click("#sheet #sheetForm button[type='submit']")
    page.wait_for_timeout(500)
    tl2 = page.evaluate("""(() => {
      const ev = document.querySelectorAll('#s-cal .daylist .ev').length;
      const ph = document.querySelectorAll('#s-cal .dp-ph').length;
      const sec = document.querySelectorAll('#s-cal .dp-sec').length;
      return {ev, ph, sec};
    })()""")
    check("그날 일정은 그대로 보임", tl2["ev"] >= 1, tl2)
    check("일정 외 다른 묶음은 없음", tl2["ph"] == 0 and tl2["sec"] == 0, tl2)

    # 오늘 만든 메모 카드도 캘린더 날짜 칸에는 나오지 않음
    today_str = time.strftime("%Y-%m-%d")
    page.locator("#s-cal .day[data-date='%s']" % today_str).click()
    page.wait_for_timeout(450)
    memo_rows = page.evaluate("document.querySelectorAll('#s-cal .dp-memo').length")
    check("그날 메모는 캘린더에 없음", memo_rows == 0, memo_rows)
    page.screenshot(path=os.path.join(SHOT, "calendar-day-v18.png"))

    # ---------------- My: 4자리 잠금 ----------------
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(400)
    check("My 에 잠금 항목", page.locator("#s-set [data-act='lockSheet']").count() == 1)
    check("My 에 PDF 내보내기 항목", page.locator("#s-set [data-act='exportSheet']").count() == 1)
    page.locator("#s-set [data-act='lockSheet']").click()
    page.wait_for_timeout(350)
    page.fill("#sheet input[name='pin']", "1234")
    page.fill("#sheet input[name='pin2']", "1234")
    page.click("#sheet #lockForm button[type='submit']")
    page.wait_for_timeout(400)
    check("잠금 설정이 기기에 저장", page.evaluate("(() => { const c = JSON.parse(localStorage.getItem('twolog:v1:lock') || '{}'); return !!c.on && c.pin === '1234'; })()"))
    check("잠금 PIN 은 공유 기록에 남지 않음", page.evaluate("!('lock' in window.__app.state)"))
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(800)
    check("앱을 열면 잠금 화면", page.evaluate("!document.getElementById('lockScreen').hidden"))
    page.screenshot(path=os.path.join(SHOT, "lock-v18.png"))
    for k in "9999":
        page.locator("#lockScreen .lk-key[data-k='%s']" % k).click()
    page.wait_for_timeout(400)
    msg = page.evaluate("document.querySelector('#lockScreen .lk-msg').textContent")
    check("틀린 비밀번호는 안내 + 재시도", "달라요" in msg, msg)
    for k in "1234":
        page.locator("#lockScreen .lk-key[data-k='%s']" % k).click()
    page.wait_for_timeout(400)
    check("맞는 비밀번호로 잠금 해제", page.evaluate("document.getElementById('lockScreen').hidden"))

    # ---------------- PDF 내보내기 ----------------
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(350)
    page.evaluate("window.__printed = 0; window.print = function () { window.__printed++; }; 0")
    page.locator("#s-set [data-act='exportSheet']").click()
    page.wait_for_timeout(350)
    check("기간 선택 3가지", page.locator("#sheet .ex-btn").count() == 3)
    page.locator("#sheet .ex-btn[data-scope='month']").click()
    page.wait_for_timeout(900)
    pr = page.evaluate("""(() => {
      const r = document.getElementById('printRoot');
      if (!r) return null;
      return {secs: r.querySelectorAll('.pr-sec').length, ph: r.querySelectorAll('.pr-photos .pr-ph').length,
              ev: r.querySelectorAll('.pr-ev').length, title: r.querySelector('.pr-head h1').textContent,
              printed: window.__printed};
    })()""")
    check("PDF 뷰에 일정·사진 담김", pr is not None and pr["secs"] >= 3 and pr["ph"] >= 1 and pr["ev"] >= 1, pr)
    check("인쇄 창(window.print) 호출", pr is not None and pr["printed"] == 1, pr)
    check("PDF 전용 레이아웃(@media print)", "#printRoot" in page.evaluate("Array.from(document.styleSheets).map(s => { try { return Array.from(s.cssRules).map(r => r.cssText).join('\\n'); } catch(e) { return ''; } }).join('\\n').slice(0, 400000)"))

    # 홈으로 돌아와 최종 화면
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(350)
    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
