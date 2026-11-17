"""투로그 v20 확인 — 캘린더 상단 「🗓️ 캘린더」 제목 줄 삭제,
그 자리에 「11월」을 제목과 같은 25px 로 왼쪽에 · 같은 줄 오른쪽 끝에 돋보기,
달 이동은 「11월」 옆 작은 화살표로.
달력 날짜 숫자는 2px 키워 15px·가운데 정렬, 주 사이 가로선까지 모두 삭제.
하단 날짜 줄은 「2026년 11월 17일」만 (요일·공휴일 배지·개수 없음).
공휴일은 더 진한 빨강. 홈 상단 「투로그」 앞 두 네모 로고 삭제.

    python3 tests/v20.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


URL = "http://127.0.0.1:%d/" % PORT
errors = []

with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # ---------------- 서비스워커 캐시 버전 ----------------
    sw = page.request.get(URL + "sw.js").text()
    # v21 에서 캐시 이름이 올라갔어요 — sw.js 는 지금 버전의 이름을 가집니다
    check("sw.js 캐시 버전 twolog-v20 이상", 'const VERSION = "twolog-v2' in sw and 'const VERSION = "twolog-v20"' not in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:2])

    # 예시 데이터로 한 번 열어 상태를 만들고, 저장되는 일반 모드로 옮겨요
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)

    # ---------------- 1. 홈 상단: 「투로그 (twolog)」만 ----------------
    home = page.evaluate("""(() => {
      const b = document.querySelector('#s-home .brand');
      const r = b.getBoundingClientRect();
      const bt = b.querySelector('b').getBoundingClientRect();
      return {mark: document.querySelectorAll('#s-home .brand .mark').length,
              markAll: document.querySelectorAll('#s-home .brand .mark i').length,
              txt: b.innerText.replace(/\\n/g, ' ').trim(), brandLeft: r.left, titleLeft: bt.left,
              h: r.height};
    })()""")
    check("홈 상단 두 네모 로고 없음", home["mark"] == 0 and home["markAll"] == 0, home)
    check("홈 상단은 「투로그 (twolog)」만", home["txt"].startswith("투로그") and "(twolog)" in home["txt"], home["txt"])
    check("홈 상단 이름이 맨 왼쪽", abs(home["titleLeft"] - 20) <= 1, (home["titleLeft"], home["brandLeft"]))
    page.screenshot(path=os.path.join(SHOT, "home-v20.png"))

    # 다른 화면(노트)을 한 번 열어 두면 제목(h1) 글씨와 비교할 수 있어요
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(600)
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(400)

    # ---------------- 2. 캘린더 상단 ----------------
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(700)

    first = page.evaluate("() => { const s = document.querySelector('#s-cal'); return s.firstElementChild ? s.firstElementChild.className : null; }")
    check("캘린더 화면 첫 줄이 달력 머리(제목 줄 없음)", first == "cal-top", first)
    check("「🗓️ 캘린더」 제목 줄 삭제", page.locator("#s-cal .hdr").count() == 0
          and "🗓️" not in page.locator("#s-cal").inner_text(), page.locator("#s-cal .hdr").count())

    head = page.evaluate("""(() => {
      const cal = document.querySelector('#s-cal .cal'); const cr = cal.getBoundingClientRect();
      const top = document.querySelector('#s-cal .cal-top'); const tr = top.getBoundingClientRect();
      const mo = document.querySelector('#s-cal .cal-month');
      const mr = mo.getBoundingClientRect(); const ms = getComputedStyle(mo);
      const prev = document.querySelector('#s-cal [data-act="calPrev"]');
      const next = document.querySelector('#s-cal [data-act="calNext"]');
      const srch = document.querySelector('#s-cal [data-act="calSearch"]');
      const sr = srch.getBoundingClientRect();
      const week = document.querySelector('#s-cal .cal-week').getBoundingClientRect();
      const diaryH1 = document.querySelector('#s-diary .hdr h1');
      const dh = diaryH1 ? getComputedStyle(diaryH1) : null;
      const dnumFs = dh ? dh.fontSize : null;
      return {txt: mo.textContent.trim(), fs: ms.fontSize, fw: ms.fontWeight,
              ls: ms.letterSpacing, lh: ms.lineHeight, color: ms.color,
              diaryFs: dnumFs, diaryFw: dh ? dh.fontWeight : null,
              lh2: dh ? dh.lineHeight : null, ls2: dh ? dh.letterSpacing : null,
              monLeft: mr.left, monMidY: mr.top + mr.height / 2,
              searchRight: window.innerWidth - sr.right, searchMidY: sr.top + sr.height / 2,
              rowTop: tr.top, weekTop: week.top,
              hasPrev: !!prev, hasNext: !!next, prevSvg: !!prev.querySelector('svg'),
              prevW: prev.getBoundingClientRect().width,
              searchIcon: !!srch.querySelector('svg'),
              titleAttr: document.querySelector('#s-cal .cal-title').getAttribute('title'),
              yearShown: document.querySelectorAll('#s-cal .cal-year').length};
    })()""")
    check("왼쪽에 「11월」", head["txt"] == "11월" and abs(head["monLeft"]) <= 24, (head["txt"], head["monLeft"]))
    check("「11월」 글씨 = 제목과 같은 25px·700", head["fs"] == "25px" and head["fw"] == "700"
          and head["fs"] == head["diaryFs"] and head["fw"] == head["diaryFw"],
          {"cal": (head["fs"], head["fw"]), "h1": (head["diaryFs"], head["diaryFw"])})
    check("「11월」 자간·줄높이도 제목과 같음", head["ls"] == head["ls2"] and head["lh"] == head["lh2"],
          (head["ls"], head["ls2"], head["lh"], head["lh2"]))
    check("돋보기가 같은 줄 맨 오른쪽 끝", head["searchIcon"] and head["searchRight"] <= 24, head["searchRight"])
    check("「11월」·돋보기가 같은 높이", abs(head["monMidY"] - head["searchMidY"]) <= 6,
          (head["monMidY"], head["searchMidY"]))
    check("달 이동 화살표 작게 두 개", head["hasPrev"] and head["hasNext"] and head["prevSvg"] and head["prevW"] <= 30,
          head["prevW"])
    check("제목 줄이 요일 줄 위", head["rowTop"] < head["weekTop"], (head["rowTop"], head["weekTop"]))
    check("이번 해는 연도 안 붙임", head["yearShown"] == 0, head["yearShown"])
    check("달 이름 툴팁에 연도", (head["titleAttr"] or "").startswith("2026년 11월"), head["titleAttr"])

    # 오른쪽 끝 = 화면 오른쪽 여백 20px 과 맞는지
    edge = page.evaluate("""(() => { const s = document.querySelector('#s-cal [data-act="calSearch"]').getBoundingClientRect();
      const sc = document.querySelector('#s-photo .hdr h1') ? 0 : 0;
      return {right: window.innerWidth - s.right}; })()""")
    check("돋보기 오른쪽 여백 20px", abs(edge["right"] - 20) <= 2, edge["right"])

    # ---------------- 3. 달 이동 ----------------
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(450)
    m1 = page.evaluate("() => document.querySelector('#s-cal .cal-month').textContent.trim()")
    check("다음 달로 이동", m1 == "12월", m1)
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(450)
    y1 = page.evaluate("""(() => ({m: document.querySelector('#s-cal .cal-month').textContent.trim(),
      y: document.querySelector('#s-cal .cal-year') ? document.querySelector('#s-cal .cal-year').textContent.trim() : null}))()""")
    check("다른 해로 가면 작은 연도 표시", y1["m"] == "1월" and y1["y"] == "2027", y1)
    page.wait_for_timeout(1800)   # 이동 안내(toast)가 사라진 뒤
    page.locator('#s-cal [data-act="calPrev"]').click()
    page.wait_for_timeout(400)
    page.locator('#s-cal [data-act="calPrev"]').click()
    page.wait_for_timeout(500)
    m2 = page.evaluate("() => document.querySelector('#s-cal .cal-month').textContent.trim()")
    check("이전 달로 되돌아옴", m2 == "11월", m2)
    page.locator('#s-cal .day', has_text="17").first.click()
    page.wait_for_timeout(450)

    # ---------------- 4. 날짜 숫자: 15px·가운데, 가로선 없음 ----------------
    grid = page.evaluate("""(() => {
      const rows = Array.from(document.querySelectorAll('#s-cal .cal-row'));
      const days = Array.from(document.querySelectorAll('#s-cal .cal-daygrid .day:not(.blank)'));
      const dn = days[0].querySelector('.dnum');
      const cs = getComputedStyle(dn);
      const r = document.createRange(); r.selectNodeContents(dn);
      const tx = r.getBoundingClientRect();
      const cell = days[0].getBoundingClientRect();
      const week = Array.from(document.querySelectorAll('#s-cal .cal-week span'));
      const cal = document.querySelector('#s-cal .cal');
      const ccs = getComputedStyle(cal);
      const rowBorder = rows.filter(x => { const s = getComputedStyle(x);
        return s.borderTopWidth !== '0px' || s.borderBottomWidth !== '0px'; }).length;
      const dayBorder = days.filter(x => { const s = getComputedStyle(x);
        return s.borderTopWidth !== '0px' || s.borderBottomWidth !== '0px'
          || s.borderLeftWidth !== '0px' || s.borderRightWidth !== '0px'; }).length;
      return {fs: cs.fontSize, fw: cs.fontWeight, align: cs.textAlign,
              textMid: tx.left + tx.width / 2, cellMid: cell.left + cell.width / 2,
              textTop: tx.top, cellTop: cell.top,
              rowBorder, dayBorder, calBorder: ccs.borderTopWidth + '/' + ccs.borderBottomWidth,
              weekAlign: week.map(s => getComputedStyle(s).textAlign).join(','),
              weekFs: week.length ? getComputedStyle(week[0]).fontSize : null,
              weekMid: week.length ? (week[0].getBoundingClientRect().left + week[0].getBoundingClientRect().width / 2) : null,
              firstCellMid: cell.left + cell.width / 2};
    })()""")
    check("날짜 숫자 15px (13 → +2)", grid["fs"] == "15px", grid["fs"])
    check("날짜 숫자 가운데 정렬 (text-align)", grid["align"] == "center", grid["align"])
    check("날짜 숫자가 칸 가운데에 실제로 놓임", abs(grid["textMid"] - grid["cellMid"]) <= 1.5,
          (grid["textMid"], grid["cellMid"]))
    check("요일 이름도 가운데 정렬", set(grid["weekAlign"].split(",")) == {"center"}, grid["weekAlign"])
    check("요일 이름과 날짜 칸 중심 일치", abs(grid["weekMid"] - grid["firstCellMid"]) <= 1.5,
          (grid["weekMid"], grid["firstCellMid"]))
    check("주 행 사이 가로선 모두 삭제", grid["rowBorder"] == 0, grid["rowBorder"])
    check("날짜 칸 테두리 없음", grid["dayBorder"] == 0, grid["dayBorder"])
    check("달력 바깥 테두리 없음", grid["calBorder"] == "0px/0px", grid["calBorder"])

    # ---------------- 5. 하단 날짜 줄: 「2026년 11월 17일」만 ----------------
    dp = page.evaluate("""(() => { const hd = document.querySelector('#s-cal .daypanel-hd');
      const d = hd.querySelector('.d');
      const cs = getComputedStyle(d);
      return {txt: hd.innerText.replace(/\\n/g, ' ').trim(), dTxt: d.innerText.replace(/\\n/g, ' ').trim(),
              kids: hd.children.length, em: hd.querySelectorAll('em').length,
              badge: hd.querySelectorAll('.hol-badge').length,
              fs: cs.fontSize, fw: cs.fontWeight}; })()""")
    check("하단 날짜는 「2026년 11월 17일」만", dp["txt"] == "2026년 11월 17일", dp["txt"])
    check("요일 표시 없음", "(" not in dp["txt"] and "요일" not in dp["txt"] and dp["em"] == 0, dp)
    check("공휴일 배지·개수 없음", dp["badge"] == 0 and "개" not in dp["txt"] and dp["kids"] == 1, dp)
    check("하단 날짜 글씨는 그대로 18.5px·800", dp["fs"] == "18.5px" and dp["fw"] == "800", (dp["fs"], dp["fw"]))

    # ---------------- 6. 공휴일 더 진한 빨강 ----------------
    page.wait_for_timeout(2200)   # 안내(toast)가 사라진 뒤 깔끔한 화면
    page.screenshot(path=os.path.join(SHOT, "calendar-v20.png"))
    page.locator('#s-cal [data-act="calPrev"]').click()
    page.wait_for_timeout(500)
    hol = page.evaluate("""(() => { const d = document.querySelector('#s-cal .day.hol .dnum');
      const n = document.querySelector('#s-cal .day.hol .dhol');
      const b = document.querySelector('#s-cal .cal-month').textContent.trim();
      return {month: b, num: d ? getComputedStyle(d).color : null,
              name: n ? getComputedStyle(n).color : null,
              count: document.querySelectorAll('#s-cal .day.hol').length}; })()""")
    check("공휴일 숫자 진한 빨강(#F01414)", hol["num"] == "rgb(240, 20, 20)" and hol["count"] >= 1, hol)
    check("공휴일 이름도 같은 빨강", hol["name"] == "rgb(240, 20, 20)", hol)
    check("달력 칸의 공휴일 표기는 유지", hol["count"] >= 2 and hol["month"] == "10월", hol)
    page.screenshot(path=os.path.join(SHOT, "calendar-holiday-v20.png"))

    # 다크 모드는 더 밝은 빨강(#FF3B3B)
    page.evaluate("document.documentElement.setAttribute('data-mode','dark'); 0")
    page.wait_for_timeout(350)
    dk = page.evaluate("""(() => { const d = document.querySelector('#s-cal .day.hol .dnum');
      return d ? getComputedStyle(d).color : null; })()""")
    check("다크에서 공휴일 #FF3B3B", dk == "rgb(255, 59, 59)", dk)
    page.screenshot(path=os.path.join(SHOT, "calendar-v20-dark.png"))
    page.evaluate("document.documentElement.setAttribute('data-mode','light'); 0")
    page.wait_for_timeout(350)

    # ---------------- 7. 다른 화면은 그대로 ----------------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(450)
    check("노트 제목 줄 그대로", page.locator("#s-diary .hdr h1").count() == 1
          and "노트" in page.locator("#s-diary .hdr h1").inner_text())
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(450)
    check("홈 브랜드 이름 그대로", page.locator("#s-home .brand b").inner_text().strip() == "투로그")

    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
