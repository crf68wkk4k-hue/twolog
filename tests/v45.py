"""투로그 v45 확인 — 지출·정산 가계부 개편 (함께 쓰는 돈 · 내역/달력 · 입금/지출 시트).

1) 버전: sw.js 캐시 twolog-v51 · APP_VERSION v51 · My 탭 「버전 v51」
2) 함께 쓰는 돈 카드 — 이번 달 총 입금 · 사용 금액 · 잔액 · 사용률 막대
   소영·준영 입금 두 칸 (함께 넣은 돈은 따로 한 줄)
3) 내역 — 날짜 최신순 · 카테고리 아이콘 · 카테고리/메모/날짜/누가 · +입금 / -지출
   예전 항목(amount 만 있고 txType 없음)은 «지출» 로 읽고, 제목 자리(text)를 그대로 보여줘요
4) 달 넘기기 ‹ 11월 › — 그 달 입금·지출만 계산, 내역도 그 달만
5) 달력 — 칸마다 그날 +입금/-지출 합계(만 단위), 날짜를 누르면 아래에 그날 내역
6) + 입금하기 / - 지출하기 시트 — 지출|입금 · 누가 · 금액(1,000 쉼표) · 카테고리 12 + 직접 입력 · 날짜 · 메모
   · 고른 카테고리로 저장, 누가·금액·날짜 반영
   · 입금 모드에서는 카테고리 칸이 숨고 기본 누가가 «나»
7) 고치기(금액·카테고리 채워짐) · × 삭제 · 달 예산 정하기/지우기
8) sync.js 왕복 — txType·cat·who·budgets 가 서버 notes 행/note_meta 에 실리고 되살아남
9) 프로필 생일은 «한 번에» 날짜칸 하나 (예전 세 칸 고르기 없음) — 고르면 아래 줄에 «1992년 6월 26일»
10) 프로필 사진 자르기 — 확대 슬라이더 없이 두 손가락 벌려 확대 · 한 손가락으로 옮기기
11) 사진 날짜 댓글 칸 — 한 줄 입력칸 대신 스스로 늘어나는 textarea (길면 아래로 줄바꿈,
    Enter 등록 · Shift+Enter 줄바꿈, 등록하면 1줄로)
12) 사진 추가 시트 — 위 장수·용량 요약 줄 없음 · 「기록 이름」 위 / 「날짜」 아래 두 줄 (각자 밑줄)
13) 사진첩 기록 이름은 날짜보다 조금 작게 (목록 15px → 13px · 모아보기 20px → 16px)
14) 모눈 다이어리 — ↶ ↷ 는 펜 옆 도구 줄로 · 펜을 누르면 글씨 없는 한 줄 그림 도크
    (가는 펜 2 · 일반 펜 4.5 · 형광펜 · 지우개 · 색 동그라미 · 전체 지우기)
15) 모눈 다이어리 글씨 도구 — 한 줄 [정렬 B S U − 크기 + 색] · 단추는 크게 · 색 동그라미 22px,
    누르면 «전체 컬러판» 9색이 펼쳐짐 · 「글 수정/키보드 내리기」 줄과 안내 글씨 없음
16) 콘솔/페이지 오류 0건

    python3 tests/v45.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import base64, functools, http.server, json, os, re, socketserver, sys, threading, time

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


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def watch(page, bucket):
    page.on("pageerror", lambda e: bucket.append("pageerror: " + str(e)))
    page.on("console", lambda m: bucket.append("console: " + m.text) if m.type == "error" else None)


def tab(page, idx, wait=560):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


SEED_JS = """() => {
  const st = JSON.parse(JSON.stringify(window.__app.state));
  st.couple.me = '소영'; st.couple.you = '준영';
  st.lists = (st.lists || []).concat([{
    id: 'Lexp', title: '우리 통장', emoji: '', kind: 'expense',
    items: [
      {id:'e1', text:'입금', cat:'입금', txType:'deposit', who:'me', amount:1000000, date:'2026-11-01', memo:'11월 월급', done:false},
      {id:'e2', text:'입금', cat:'입금', txType:'deposit', who:'you', amount:1000000, date:'2026-11-02', memo:'', done:false},
      {id:'e3', text:'식비', cat:'식비', txType:'expense', who:'me', amount:45000, date:'2026-11-21', memo:'한강 라면', done:false},
      {id:'e4', text:'생활용품', cat:'생활용품', txType:'expense', who:'you', amount:32000, date:'2026-11-20', memo:'세제', done:false},
      {id:'e5', text:'데이트', cat:'데이트', txType:'expense', who:'both', amount:20000, date:'2026-11-15', memo:'영화', done:false},
      {id:'e6', text:'교통', cat:'교통', txType:'expense', who:'me', amount:10000, date:'2026-12-03', memo:'택시', done:false},
      {id:'e7', text:'점심', amount:7000, date:'2026-11-22', who:'me'}
    ]
  }]);
  st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Lexp').concat(['list:Lexp']);
  return JSON.stringify(st);
}"""


def seed_expense(page):
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed = page.evaluate(SEED_JS)
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 2, 700)
    page.locator("#s-diary .lchip", has_text="우리 통장").first.click()
    page.wait_for_timeout(600)


def stat(page):
    return page.evaluate("""() => {
      const q = s => document.querySelector(s);
      const txt = s => (q(s) || {}).textContent || '';
      return {
        month: txt('#s-diary .exp-month b'),
        total: txt('#s-diary .exp-fund-total'),
        spent: txt('#s-diary .exp-spent'),
        pct: txt('#s-diary .exp-pct'),
        left: txt('#s-diary .exp-left'),
        budget: txt('#s-diary .exp-budget'),
        people: [...document.querySelectorAll('#s-diary .exp-p')].map(p => [(p.querySelector('.k')||{}).textContent||'', (p.querySelector('.v')||{}).textContent||'']),
        rows: [...document.querySelectorAll('#s-diary .exp-row')].map(r => ({
          id: r.getAttribute('data-id'),
          t: (r.querySelector('.exp-row-t')||{}).textContent||'',
          s: (r.querySelector('.exp-row-s')||{}).textContent||'',
          a: (r.querySelector('.exp-row-a')||{}).textContent||'',
          ic: r.querySelectorAll('.exp-ic svg').length,
          in: !!(r.querySelector('.exp-ic.in'))
        })),
        tabs: [...document.querySelectorAll('#s-diary .exp-tab')].map(b => [b.textContent.trim(), b.classList.contains('on')]),
        acts: [...document.querySelectorAll('#s-diary .exp-acts .exp-act')].map(b => b.textContent.trim()),
        cal: document.querySelectorAll('#s-diary .exp-cell').length,
        week: [...document.querySelectorAll('#s-diary .exp-week span')].map(s => s.textContent),
        dayhd: txt('#s-diary .exp-dayhd b'),
        dayrows: document.querySelectorAll('#s-diary .exp-daylist .exp-row').length,
        daynets: [...document.querySelectorAll('#s-diary .exp-daynet em')].map(e => e.textContent),
        barW: (q('#s-diary .exp-bar i') || {}).style ? q('#s-diary .exp-bar i').style.width : '',
        quick: document.querySelectorAll('#s-diary #listQuickForm').length
      };
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
    watch(page, errs)

    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    check("sw.js 캐시 버전 twolog-v51", 'const VERSION = "twolog-v51"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v51", 'var APP_VERSION = "v51"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("예전 v44 문자열이 남아 있지 않음",
          "twolog-v44" not in sw and 'APP_VERSION = "v44"' not in app_js)

    seed_expense(page)
    tab(page, 4, 620)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v51」", ver.strip() == "버전 v51", ver)
    tab(page, 2, 620)
    page.locator("#s-diary .lchip", has_text="우리 통장").first.click()
    page.wait_for_timeout(560)

    # ==================================================================
    # 2. 함께 쓰는 돈 · 소영/준영 입금 · 내역
    # ==================================================================
    s1 = stat(page)
    check("달 머리 «11월» · 내역/달력 전환 (내역이 기본)",
          s1["month"] == "11월" and [t[0] for t in s1["tabs"]] == ["내역", "달력"]
          and s1["tabs"][0][1] is True, (s1["month"], s1["tabs"]))
    check("함께 쓰는 돈 = 이번 달 총 입금 ₩2,000,000", s1["total"] == "₩2,000,000", s1["total"])
    check("사용 금액 ₩104,000 (예전 항목 7,000 포함)", s1["spent"] == "₩104,000", s1["spent"])
    check("사용률 5% · 잔액 ₩1,896,000",
          s1["pct"] == "사용 5%" and s1["left"] == "잔액 ₩1,896,000", (s1["pct"], s1["left"]))
    check("사용률 막대 폭 5%", s1["barW"] == "5%", s1["barW"])
    people = page.evaluate("""() => [...document.querySelectorAll('#s-diary .exp-p')]
      .map(p => [(p.querySelector('.k')||{}).textContent||'', (p.querySelector('.v')||{}).textContent||''])""")
    check("소영 입금 · 준영 입금 두 칸", people == [["소영 입금", "₩1,000,000"], ["준영 입금", "₩1,000,000"]], people)
    check("아래 + 입금하기 / - 지출하기 두 버튼",
          s1["acts"] == ["+입금하기", "-지출하기"], s1["acts"])
    check("예전 빠른 추가 줄은 없어짐", s1["quick"] == 0, s1["quick"])
    check("내역은 그 달 6건 · 최신순",
          [r["id"] for r in s1["rows"]] == ["e7", "e3", "e4", "e5", "e2", "e1"],
          [r["id"] for r in s1["rows"]])
    check("입금은 +₩ · 지출은 -₩",
          s1["rows"][4]["a"] == "+₩1,000,000" and s1["rows"][1]["a"] == "-₩45,000",
          [r["a"] for r in s1["rows"]])
    check("카테고리 · 메모 · 날짜 · 누가가 한 줄에",
          s1["rows"][1]["t"] == "식비" and "한강 라면" in s1["rows"][1]["s"]
          and "11.21" in s1["rows"][1]["s"] and "소영" in s1["rows"][1]["s"], s1["rows"][1])
    check("입금 줄은 «소영 입금»·«준영 입금» 으로 보임",
          s1["rows"][5]["t"] == "소영 입금" and s1["rows"][4]["t"] == "준영 입금",
          [r["t"] for r in s1["rows"]])
    check("모든 줄에 동그란 라인 아이콘", all(r["ic"] == 1 for r in s1["rows"]), [r["ic"] for r in s1["rows"]])
    check("예전 항목(txType 없음)도 지출로 읽고 제목 그대로", s1["rows"][0]["t"] == "점심" and s1["rows"][0]["a"] == "-₩7,000",
          s1["rows"][0])
    page.screenshot(path=os.path.join(SHOT, "expense-v45-main.png"))

    # ==================================================================
    # 3. 달 넘기기
    # ==================================================================
    page.locator("#s-diary .exp-nav[data-act='expNext']").click()
    page.wait_for_timeout(420)
    s2 = stat(page)
    check("다음 달로 — «12월» · 그 달 입금 0",
          s2["month"] == "12월" and s2["total"] == "₩0", (s2["month"], s2["total"]))
    check("12월 사용 ₩10,000 · 잔액 대신 «₩10,000 초과»",
          s2["spent"] == "₩10,000" and s2["left"] == "₩10,000 초과", (s2["spent"], s2["left"]))
    check("12월 내역은 1건(교통)", [r["id"] for r in s2["rows"]] == ["e6"], [r["id"] for r in s2["rows"]])
    page.locator("#s-diary .exp-nav[data-act='expPrev']").click()
    page.wait_for_timeout(420)
    s3 = stat(page)
    check("이전 달로 돌아오면 다시 11월 · 6건",
          s3["month"] == "11월" and len(s3["rows"]) == 6, (s3["month"], len(s3["rows"])))

    # ==================================================================
    # 4. 달력 보기 — 칸 합계 · 날짜 고르기
    # ==================================================================
    page.locator("#s-diary .exp-tab[data-v='cal']").click()
    page.wait_for_timeout(460)
    cal = page.evaluate("""() => {
      const cells = [...document.querySelectorAll('#s-diary .exp-cell')];
      const by = {};
      cells.forEach(c => { by[c.getAttribute('data-day')] = {
        n: (c.querySelector('.exp-cell-n')||{}).textContent||'',
        inn: (c.querySelector('.di')||{}).textContent||'',
        out: (c.querySelector('.do')||{}).textContent||'' }; });
      return {n: cells.length, week: [...document.querySelectorAll('#s-diary .exp-week span')].map(s=>s.textContent),
        d1: by['2026-11-01'], d2: by['2026-11-02'], d20: by['2026-11-20'], d21: by['2026-11-21'],
        today: (() => { const d = new Date();
          return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); })(),
        sel: (document.querySelector('#s-diary .exp-cell.sel')||{}).getAttribute ? document.querySelector('#s-diary .exp-cell.sel').getAttribute('data-day') : '',
        dayhd: (document.querySelector('#s-diary .exp-dayhd b')||{}).textContent||'',
        rows: [...document.querySelectorAll('#s-diary .exp-daylist .exp-row-t')].map(x=>x.textContent)};
    }""")
    check("달력 — 11월 30칸 · 일~토 머리", cal["n"] == 30 and cal["week"] == ["일", "월", "화", "수", "목", "금", "토"], cal)
    check("칸마다 그날 입금/지출 합계 (1일 +100만 / 20일 -3.2만)",
          cal["d1"]["inn"] == "+100만" and cal["d20"]["out"] == "-3.2만", (cal["d1"], cal["d20"]))
    check("오늘이 골라져 있고 그날 내역이 아래에",
          cal["sel"] == cal["today"]
          and cal["dayhd"] == "%d월 %d일" % (int(cal["today"][5:7]), int(cal["today"][8:10])),
          (cal["sel"], cal["dayhd"], cal["today"]))
    page.locator("#s-diary .exp-cell[data-day='2026-11-20']").click()
    page.wait_for_timeout(420)
    day = page.evaluate("""() => ({sel: (document.querySelector('#s-diary .exp-cell.sel')||{}).getAttribute('data-day'),
      hd: (document.querySelector('#s-diary .exp-dayhd b')||{}).textContent||'',
      rows: [...document.querySelectorAll('#s-diary .exp-daylist .exp-row-t')].map(x=>x.textContent),
      amts: [...document.querySelectorAll('#s-diary .exp-daylist .exp-row-a')].map(x=>x.textContent),
      net: [...document.querySelectorAll('#s-diary .exp-daynet em')].map(x=>x.textContent)})""")
    check("20일을 누르면 그날 내역만 (생활용품 -₩32,000)",
          day["sel"] == "2026-11-20" and day["hd"] == "11월 20일"
          and day["rows"] == ["생활용품"] and day["amts"] == ["-₩32,000"], day)
    page.locator("#s-diary .exp-cell[data-day='2026-11-21']").click()
    page.wait_for_timeout(400)
    day2 = page.evaluate("""() => ({hd: (document.querySelector('#s-diary .exp-dayhd b')||{}).textContent||'',
      rows: [...document.querySelectorAll('#s-diary .exp-daylist .exp-row-t')].map(x=>x.textContent)})""")
    check("21일을 누르면 식비", day2["rows"] == ["식비"] and day2["hd"] == "11월 21일", day2)
    page.screenshot(path=os.path.join(SHOT, "expense-v45-cal.png"))

    # ==================================================================
    # 5. + 지출하기 시트 — 지출|입금 · 누가 · 금액 · 카테고리 12 · 날짜 · 메모
    # ==================================================================
    page.locator("#s-diary .exp-tab[data-v='list']").click()
    page.wait_for_timeout(400)
    page.locator("#s-diary .exp-act[data-tx='expense']").click()
    page.wait_for_timeout(560)
    sh = page.evaluate("""() => {
      const q = s => document.querySelector('#sheet ' + s);
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
        seg: [...document.querySelectorAll('#sheet .exp-seg button')].map(b => [b.textContent.trim(), b.classList.contains('on')]),
        who: [...document.querySelectorAll('#sheet .exp-who')].map(b => [b.textContent.trim(), b.classList.contains('on')]),
        cats: [...document.querySelectorAll('#sheet .exp-cat .nm')].map(x => x.textContent),
        catCount: document.querySelectorAll('#sheet .exp-cat').length,
        labels: [...document.querySelectorAll('#sheet .exp-fld > label')].map(l => l.textContent.trim()),
        amount: !!q('input[name=amount]'), date: !!q('input[name=date]'), memo: !!q('input[name=memo]'),
        dateVal: (q('input[name=date]')||{}).value, whoVal: (q('input[name=who]')||{}).value,
        circ: [...document.querySelectorAll('#sheet .exp-cat .ic')].every(i => {
          const r = i.getBoundingClientRect(); return Math.abs(r.width - r.height) < 1 && r.width >= 40; })};
    }""")
    check("지출 시트가 열림 · 지출|입금 토글 (지출 선택)",
          sh["open"] and [x[0] for x in sh["seg"]] == ["지출", "입금"] and sh["seg"][0][1], sh["seg"])
    check("누가 — 소영 / 준영 / 함께 (지출 기본 «함께»)",
          [x[0] for x in sh["who"]] == ["소영", "준영", "함께"]
          and sh["who"][2][1] and sh["whoVal"] == "both", sh["who"])
    check("카테고리 12개 + 직접 입력", sh["catCount"] == 13 and sh["cats"][:12] == [
        "식비", "카페", "생활용품", "데이트", "교통", "주거", "쇼핑", "여행", "건강", "통신", "공과금", "기타"], sh["cats"])
    check("카테고리 아이콘은 동그란 라인", sh["circ"], sh["circ"])
    check("금액 · 날짜 · 메모 칸", sh["amount"] and sh["date"] and sh["memo"])
    today_js = page.evaluate("() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); }")
    check("날짜 기본은 오늘", sh["dateVal"] == today_js, (sh["dateVal"], today_js))

    page.fill("#sheet input[name=amount]", "12345")
    page.wait_for_timeout(160)
    fmt = page.evaluate("document.querySelector('#sheet input[name=amount]').value")
    check("금액을 치면 1,000 쉼표", fmt == "12,345", fmt)
    page.locator("#sheet .exp-cat[data-cat='카페']").click()
    page.wait_for_timeout(160)
    catSel = page.evaluate("""() => ({cat: document.querySelector('#sheet input[name=cat]').value,
      on: [...document.querySelectorAll('#sheet .exp-cat.on .nm')].map(x => x.textContent),
      who: [...document.querySelectorAll('#sheet .exp-who.on')].map(x => x.textContent)})""")
    check("고른 카테고리만 선택 (카페)", catSel["cat"] == "카페" and catSel["on"] == ["카페"], catSel)
    page.locator("#sheet .exp-who[data-who='me']").click()
    page.wait_for_timeout(140)
    check("누가를 «소영» 으로", page.evaluate("document.querySelector('#sheet input[name=who]').value") == "me")
    page.fill("#sheet input[name=memo]", "커피 두 잔")
    page.screenshot(path=os.path.join(SHOT, "expense-v45-sheet.png"))
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(700)
    s4 = stat(page)
    check("지출을 더하면 사용 금액·잔액이 바로 다시 (₩116,345 / ₩1,883,655)",
          s4["spent"] == "₩116,345" and s4["left"] == "잔액 ₩1,883,655", (s4["spent"], s4["left"]))
    newrow = [r for r in s4["rows"] if r["t"] == "카페"]
    check("새 지출 줄 — 카페 · 커피 두 잔 · 소영 · -₩12,345",
          bool(newrow) and "커피 두 잔" in newrow[0]["s"] and "소영" in newrow[0]["s"]
          and newrow[0]["a"] == "-₩12,345", newrow)

    # ==================================================================
    # 6. + 입금하기 — 입금 모드에서는 카테고리 숨김 · 기본 누가 «나»
    # ==================================================================
    page.locator("#s-diary .exp-act[data-tx='deposit']").click()
    page.wait_for_timeout(520)
    dep = page.evaluate("""() => ({tx: document.querySelector('#sheet input[name=txType]').value,
      who: document.querySelector('#sheet input[name=who]').value,
      catsHidden: document.querySelector('#sheet .exp-cats').hidden,
      segOn: [...document.querySelectorAll('#sheet .exp-seg button.on')].map(b => b.textContent.trim())})""")
    check("입금 시트 — 입금 선택 · 누가 기본 «소영» · 카테고리 숨김",
          dep["tx"] == "deposit" and dep["who"] == "me" and dep["segOn"] == ["입금"], dep)
    check("입금 모드에서는 카테고리 그리드가 숨음", dep["catsHidden"] is True, dep)
    page.fill("#sheet input[name=amount]", "500000")
    page.fill("#sheet input[name=memo]", "보너스")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(700)
    s5 = stat(page)
    people2 = page.evaluate("""() => [...document.querySelectorAll('#s-diary .exp-p')]
      .map(p => (p.querySelector('.v')||{}).textContent||'')""")
    check("입금을 더하면 함께 쓰는 돈이 늘어남 (₩2,500,000)",
          s5["total"] == "₩2,500,000" and people2 == ["₩1,500,000", "₩1,000,000"], (s5["total"], people2))
    check("입금 줄은 «소영 입금» +₩500,000",
          any(r["t"] == "소영 입금" and r["a"] == "+₩500,000" and "보너스" in r["s"] for r in s5["rows"]),
          [r for r in s5["rows"] if r["a"].startswith("+")])

    # ==================================================================
    # 7. 고치기 — 금액·카테고리·누가가 채워져 열림
    # ==================================================================
    page.locator("#s-diary .exp-row[data-id='e3'] .exp-row-b").click()
    page.wait_for_timeout(520)
    ed = page.evaluate("""() => ({
      amt: (document.querySelector('#sheet input[name=amount]')||{}).value,
      cat: [...document.querySelectorAll('#sheet .exp-cat.on .nm')].map(x => x.textContent),
      memo: (document.querySelector('#sheet input[name=memo]')||{}).value,
      who: [...document.querySelectorAll('#sheet .exp-who.on')].map(x => x.textContent),
      date: (document.querySelector('#sheet input[name=date]')||{}).value,
      trash: !!document.querySelector('#sheet .exp-delbtn'),
      title: (document.querySelector('#sheet .btn-primary')||{}).textContent})""")
    check("고치기 시트 — 금액 45,000 · 식비 선택 · 메모·날짜·누가 그대로",
          ed["amt"] == "45,000" and ed["cat"] == ["식비"] and ed["memo"] == "한강 라면"
          and ed["who"] == ["소영"] and ed["date"] == "2026-11-21", ed)
    check("고치기 시트에는 지우기(휴지통) 버튼", ed["trash"], ed)
    page.fill("#sheet input[name=amount]", "50000")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(680)
    s6 = stat(page)
    check("고친 금액이 바로 반영 (₩121,345)", s6["spent"] == "₩121,345", s6["spent"])

    # ==================================================================
    # 8. 직접 입력 카테고리 · 삭제
    # ==================================================================
    page.locator("#s-diary .exp-act[data-tx='expense']").click()
    page.wait_for_timeout(500)
    page.locator("#sheet .exp-cat-more").click()
    page.wait_for_timeout(220)
    page.fill("#sheet #expCatIn", "반려동물")
    page.locator("#sheet .exp-catadd").click()
    page.wait_for_timeout(260)
    custom = page.evaluate("""() => ({cat: document.querySelector('#sheet input[name=cat]').value,
      names: [...document.querySelectorAll('#sheet .exp-cat .nm')].map(x => x.textContent).slice(-3),
      on: [...document.querySelectorAll('#sheet .exp-cat.on .nm')].map(x => x.textContent),
      newHidden: document.getElementById('expCatNew').hidden})""")
    check("직접 입력한 카테고리가 바로 골라짐", custom["cat"] == "반려동물"
          and custom["on"] == ["반려동물"] and custom["newHidden"], custom)
    page.fill("#sheet input[name=amount]", "30000")
    page.fill("#sheet input[name=memo]", "모래")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(680)
    s7 = stat(page)
    check("직접 만든 카테고리로 지출이 담김 (반려동물 -₩30,000)",
          any(r["t"] == "반려동물" and r["a"] == "-₩30,000" for r in s7["rows"]), s7["rows"][:3])
    page.locator("#s-diary .exp-row[data-id='e7'] .exp-x").click()
    page.wait_for_timeout(520)
    s8 = stat(page)
    check("× 로 지우면 합계가 다시 (₩144,345)", s8["spent"] == "₩144,345", s8["spent"])
    check("지운 줄은 사라짐", not any(r["id"] == "e7" for r in s8["rows"]), [r["id"] for r in s8["rows"]])

    # ==================================================================
    # 9. 달 예산 — 정하기 · 사용률 기준 바뀜 · 지우기
    # ==================================================================
    page.locator("#s-diary .exp-budget-btn").click()
    page.wait_for_timeout(480)
    budgetForm = page.evaluate("""() => ({hd: (document.querySelector('#sheet h2')||{}).textContent||'',
      has: !!document.querySelector('#sheet input[name=budget]')})""")
    check("예산 시트 — «11월 예산» · 금액 칸", budgetForm["hd"] == "11월 예산" and budgetForm["has"], budgetForm)
    page.fill("#sheet input[name=budget]", "1500000")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(680)
    s9 = stat(page)
    check("예산을 정하면 사용률 기준이 예산으로 (₩144,345 / 10%)",
          "예산 ₩1,500,000" in s9["budget"] and s9["pct"] == "사용 10%", (s9["budget"], s9["pct"]))
    check("예산은 리스트 메타에 담김", page.evaluate(
        "(window.__app.state.lists.filter(l => l.id === 'Lexp')[0] || {}).budgets || {}") == {"2026-11": 1500000},
        page.evaluate("(window.__app.state.lists.filter(l => l.id === 'Lexp')[0] || {}).budgets"))
    page.locator("#s-diary .exp-budget-btn").click()
    page.wait_for_timeout(440)
    page.locator("#sheet .btn-line").click()
    page.wait_for_timeout(640)
    s10 = stat(page)
    check("예산을 지우면 다시 함께 쓰는 돈 기준", s10["pct"] == "사용 6%" and "예산 정하기" in s10["budget"],
          (s10["pct"], s10["budget"]))
    check("브라우저 콘솔/페이지 오류 없음 (로컬)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 10. 다크 모드 — 카드·금액 색이 보이는지
    # ==================================================================
    ctxD = new_ctx(browser)
    ctxD.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageD = ctxD.new_page()
    errsD = []
    watch(pageD, errsD)
    seed_expense(pageD)
    pageD.evaluate("() => { window.__app.state.theme.mode = 'dark'; window.__app.rerender(); }")
    pageD.wait_for_timeout(500)
    dk = pageD.evaluate("""() => {
      const g = s => getComputedStyle(document.querySelector(s));
      return {mode: document.documentElement.getAttribute('data-mode'),
        fund: g('#s-diary .exp-fund').backgroundColor,
        out: g('#s-diary .exp-row-a.out').color, inC: g('#s-diary .exp-row-a.in').color};
    }""")
    check("다크 모드에서도 카드·입금/지출 색이 살아 있음",
          dk["mode"] == "dark" and dk["fund"] not in ("", "rgb(255, 255, 255)")
          and dk["out"] != dk["inC"], dk)
    check("브라우저 콘솔/페이지 오류 없음 (다크)", len(errsD) == 0, errsD[:4])
    ctxD.close()

    # ==================================================================
    # 11. sync.js 왕복 — txType · cat · who · budgets
    # ==================================================================
    cid, uid2, mail = "couple-v45", "user-v45", "v45@twolog.app"
    seed_notes = [
        {"id": "L9", "couple_id": cid, "kind": "list", "sort": 0, "deleted": False,
         "payload": {"title": "공동 통장", "emoji": "", "kind": "expense",
                     "budgets": {"2026-11": 800000},
                     "items": [
                         {"id": "i1", "text": "입금", "memo": "월급", "done": False, "txType": "deposit",
                          "cat": "입금", "who": "me", "amount": 800000, "date": "2026-11-01"},
                         {"id": "i2", "text": "식비", "memo": "장보기", "done": False, "txType": "expense",
                          "cat": "식비", "who": "both", "amount": 12000, "date": "2026-11-21"}]}},
    ]
    db = {
        "users": {uid2: {"id": uid2, "email": mail, "password": "pw123456"}},
        "couples": [{"id": cid, "invite_code": "482913", "members": [uid2],
                     "me": "소영", "you": "준영", "since": "2025-11-19", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "photos": [], "notes": seed_notes, "settings": [], "uploads": [], "seq": 40,
    }
    seed_js = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: %s, email: %s } }));
    })();""" % (json.dumps(json.dumps(db, ensure_ascii=False)), json.dumps(uid2), json.dumps(mail))
    ctx2 = new_ctx(browser)
    ctx2.add_init_script(seed_js)
    ctx2.add_init_script("window.__TWOLOG_MODE = 'remote';")
    page2 = ctx2.new_page()
    errs2 = []
    watch(page2, errs2)
    stub_route(page2)
    page2.goto(URL, wait_until="domcontentloaded")
    page2.wait_for_selector("#tabbar .tab", timeout=25000)
    page2.wait_for_timeout(2800)
    tab(page2, 2, 760)
    page2.locator("#s-diary .lchip", has_text="공동 통장").first.click()
    page2.wait_for_timeout(620)
    remote = page2.evaluate("() => JSON.parse(JSON.stringify(window.__app.state.lists || []))")
    rl = (remote or [{}])[0]
    ri = {x["id"]: x for x in (rl.get("items") or [])}
    check("서버에서 되살린 지출 리스트 — 입금/지출·카테고리·누가 보존",
          (ri.get("i1") or {}).get("txType") == "deposit" and (ri.get("i1") or {}).get("who") == "me"
          and (ri.get("i2") or {}).get("cat") == "식비" and (ri.get("i2") or {}).get("who") == "both",
          rl.get("items"))
    check("서버에서 되살린 달 예산", (rl.get("budgets") or {}).get("2026-11") == 800000, rl.get("budgets"))
    rs = page2.evaluate("""() => ({total: (document.querySelector('#s-diary .exp-fund-total')||{}).textContent||'',
      spent: (document.querySelector('#s-diary .exp-spent')||{}).textContent||'',
      budget: (document.querySelector('#s-diary .exp-budget')||{}).textContent||''})""")
    check("서버 값으로 카드가 그려짐 (₩800,000 · ₩12,000 · 예산)",
          rs["total"] == "₩800,000" and rs["spent"] == "₩12,000" and "예산" in rs["budget"], rs)

    page2.locator("#s-diary .exp-act[data-tx='expense']").click()
    page2.wait_for_timeout(520)
    page2.fill("#sheet input[name=amount]", "8000")
    page2.locator("#sheet .exp-cat[data-cat='카페']").click()
    page2.fill("#sheet input[name=memo]", "커피")
    page2.locator("#sheet button.btn-primary").click()
    page2.wait_for_timeout(2200)
    row = page2.evaluate("""() => {
      const r = (window.__stub.notes || []).filter(x => x.id === 'L9')[0] || null;
      return r ? {kind: r.kind, payload: r.payload} : null; }""")
    p2 = (row or {}).get("payload") or {}
    items = p2.get("items") or []
    added = [it for it in items if it.get("memo") == "커피"]
    check("새 지출이 서버 notes 행 payload 에 txType·cat·who 와 함께 올라감",
          bool(added) and added[0].get("txType") == "expense" and added[0].get("cat") == "카페"
          and added[0].get("who") == "both" and added[0].get("amount") == 8000, added)
    check("리스트 행에 예산이 그대로 남음", (p2.get("budgets") or {}).get("2026-11") == 800000, p2.get("budgets"))

    page2.reload(wait_until="domcontentloaded")
    page2.wait_for_selector("#tabbar .tab", timeout=25000)
    page2.wait_for_timeout(2600)
    tab(page2, 2, 760)
    page2.locator("#s-diary .lchip", has_text="공동 통장").first.click()
    page2.wait_for_timeout(620)
    again = page2.evaluate("""() => { const l = (window.__app.state.lists || [])[0] || {};
      return {items: (l.items || []).map(x => [x.memo, x.txType, x.cat, x.amount]),
              spent: (document.querySelector('#s-diary .exp-spent')||{}).textContent||''}; }""")
    check("새로고침해도 새 지출과 사용 금액이 그대로 (₩20,000)",
          again["spent"] == "₩20,000"
          and any(x[0] == "커피" and x[1] == "expense" and x[2] == "카페" and x[3] == 8000 for x in again["items"]), again)
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errs2) == 0, errs2[:4])
    ctx2.close()

    # ==================================================================
    # 12. 프로필 생일 — «한 번에» 날짜칸 하나 (v44 세 칸 고르기 걷어냄)
    # ==================================================================
    ctxP = new_ctx(browser)
    ctxP.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageP = ctxP.new_page()
    errsP = []
    watch(pageP, errsP)
    pageP.goto(URL + "?demo=1", wait_until="networkidle")
    pageP.wait_for_timeout(700)
    seedP = pageP.evaluate("JSON.stringify(window.__app.state)")
    pageP.goto(URL, wait_until="domcontentloaded")
    pageP.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seedP)
    pageP.reload(wait_until="networkidle")
    pageP.wait_for_timeout(900)
    tab(pageP, 4, 620)
    pageP.locator('#s-set [data-act="personSheet"][data-who="me"]').click()
    pageP.wait_for_timeout(620)
    bd = pageP.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const inp = sh.querySelector('input[name=bday]');
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
        date: !!inp && inp.type === 'date',
        selects: sh.querySelectorAll('select.pr-bday-y, select.pr-bday-m, select.pr-bday-d').length,
        row: !!sh.querySelector('.pr-bday-row'),
        min: inp ? inp.getAttribute('min') : '', max: inp ? inp.getAttribute('max') : '',
        val: inp ? inp.value : '',
        txt: (document.getElementById('prBdayTxt') || {}).textContent || ''};
    }""")
    check("프로필 생일은 날짜칸 하나 (type=date · name=bday)", bd["date"], bd)
    check("«년/월/일» 세 칸 고르기는 없음", bd["selects"] == 0 and not bd["row"], bd)
    check("날짜칸 범위 1900-01-01 ~ 오늘", bd["min"] == "1900-01-01"
          and bd["max"] == pageP.evaluate("() => { const d = new Date(); return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); }"),
          (bd["min"], bd["max"]))
    pageP.fill("#sheet input[name=bday]", "1992-06-26")
    pageP.wait_for_timeout(260)
    picked = pageP.evaluate("""() => ({val: document.querySelector('#sheet input[name=bday]').value,
      txt: (document.getElementById('prBdayTxt') || {}).textContent || ''})""")
    check("날짜를 고르면 바로 «1992년 6월 26일» 로 아래 줄에 보임",
          picked["val"] == "1992-06-26" and "1992년 6월 26일" in picked["txt"], picked)
    pageP.locator('#sheet button.btn-primary[type="submit"]').click()
    pageP.wait_for_timeout(700)
    savedB = pageP.evaluate("""() => { const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      return ((s.couple || {}).birthdays || {}).me || ''; }""")
    check("저장하면 생일이 1992-06-26 으로 남음", savedB == "1992-06-26", savedB)
    # 다시 열어도 그 날짜가 그대로
    pageP.locator('#s-set [data-act="personSheet"][data-who="me"]').click()
    pageP.wait_for_timeout(520)
    againB = pageP.evaluate("""() => ({val: (document.querySelector('#sheet input[name=bday]') || {}).value || '',
      txt: (document.getElementById('prBdayTxt') || {}).textContent || ''})""")
    check("다시 열어도 1992-06-26 이 채워져 있음", againB["val"] == "1992-06-26" and "1992년 6월 26일" in againB["txt"], againB)
    pageP.keyboard.press("Escape")
    pageP.wait_for_timeout(300)

    # ==================================================================
    # 13. 프로필 사진 자르기 — 슬라이더 없이 손가락으로만
    # ==================================================================
    pageP.set_input_files("#avatarInput", os.path.join(ROOT, "icons", "icon-512.png"))
    pageP.wait_for_timeout(900)
    crop = pageP.evaluate("""() => {
      const w = document.getElementById('avCrop');
      const st = document.getElementById('avcStage');
      return {open: !!w, slider: !!document.getElementById('avcZoom'),
        zoomBar: document.querySelectorAll('.avcrop-zoom, #avCrop input[type=range]').length,
        hint: (document.querySelector('.avcrop-hint') || {}).textContent || '',
        stage: !!st, touch: st ? getComputedStyle(st).touchAction : ''};
    }""")
    check("자르기 화면에 확대 슬라이더가 없음", crop["open"] and not crop["slider"] and crop["zoomBar"] == 0, crop)
    check("두 손가락 안내 한 줄 · stage 터치 잡기(touch-action:none)", "두 손가락" in crop["hint"]
          and crop["touch"] == "none", crop)

    pinch = pageP.evaluate("""() => {
      const stage = document.getElementById('avcStage');
      const img = document.getElementById('avcImg');
      const r = stage.getBoundingClientRect();
      const cx = r.width / 2, cy = r.height / 2;
      const mk = (t, id, x, y) => new PointerEvent(t, { pointerId: id, pointerType: 'touch',
        clientX: r.left + x, clientY: r.top + y, bubbles: true, cancelable: true });
      const scaleOf = () => { const m = /scale\(([\d.]+)\)/.exec(img.style.transform || ''); return m ? Number(m[1]) : 1; };
      const before = scaleOf();
      stage.dispatchEvent(mk('pointerdown', 11, cx - 20, cy));
      stage.dispatchEvent(mk('pointerdown', 12, cx + 20, cy));
      for (let i = 1; i <= 6; i++) {
        stage.dispatchEvent(mk('pointermove', 11, cx - 20 - i * 12, cy));
        stage.dispatchEvent(mk('pointermove', 12, cx + 20 + i * 12, cy));
      }
      const afterPinch = scaleOf();
      stage.dispatchEvent(mk('pointerup', 12, cx + 92, cy));
      stage.dispatchEvent(mk('pointerup', 11, cx - 92, cy));
      /* 한 손가락으로 끌기 */
      const t0 = img.style.transform;
      stage.dispatchEvent(mk('pointerdown', 21, cx, cy));
      stage.dispatchEvent(mk('pointermove', 21, cx, cy + 1));
      stage.dispatchEvent(mk('pointermove', 21, cx + 24, cy + 24));
      const t1 = img.style.transform;
      stage.dispatchEvent(mk('pointerup', 21, cx + 24, cy + 24));
      return {before: before, afterPinch: afterPinch, moved: t0 !== t1, t1: t1};
    }""")
    check("두 손가락을 벌리면 사진이 확대됨 (1x → %.2fx)" % pinch["afterPinch"],
          pinch["afterPinch"] > pinch["before"] * 1.5, pinch)
    check("한 손가락으로 끌면 위치가 옮겨짐", pinch["moved"], pinch["t1"])
    pageP.screenshot(path=os.path.join(SHOT, "person-v45-crop.png"))
    pageP.locator("#avcApply").click()
    pageP.wait_for_timeout(700)
    applied = pageP.evaluate("""() => { const s = window.__app.state;
      const p = ((s.couple || {}).pics || {}).me || '';
      return {gone: !document.getElementById('avCrop'), head: p.slice(0, 22), len: p.length}; }""")
    check("«적용» 을 누르면 자른 사진이 프로필에 담김 (jpeg data URL)",
          applied["gone"] and applied["head"] == "data:image/jpeg;base64" and applied["len"] > 1000, applied)
    check("브라우저 콘솔/페이지 오류 없음 (프로필)", len(errsP) == 0, errsP[:4])
    ctxP.close()

    # ==================================================================
    # 14. 사진 날짜 댓글 — 길어지면 가로로 흐르지 않고 아래로 (자라는 textarea)
    # ==================================================================
    ctxC = new_ctx(browser)
    ctxC.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageC = ctxC.new_page()
    errsC = []
    watch(pageC, errsC)
    pageC.goto(URL + "?demo=1", wait_until="networkidle")
    pageC.wait_for_timeout(700)
    seedC = pageC.evaluate("JSON.stringify(window.__app.state)")
    pageC.goto(URL, wait_until="domcontentloaded")
    pageC.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seedC)
    pageC.reload(wait_until="networkidle")
    pageC.wait_for_timeout(900)
    tab(pageC, 3, 700)
    pageC.locator("#s-photo [data-act='openPhotoDay']").last.click()
    pageC.wait_for_timeout(760)
    box = pageC.evaluate("""() => {
      const el = document.querySelector('#s-photo .dcmt.dcmt-day .cmt-in');
      return {tag: el ? el.tagName : '', rows: el ? el.getAttribute('rows') : '',
        h: el ? Math.round(el.getBoundingClientRect().height) : 0,
        form: !!document.querySelector('#s-photo .dcmt.dcmt-day .cmt-form'),
        wide: el ? el.getBoundingClientRect().width : 0};
    }""")
    check("사진 날짜 댓글 칸은 한 줄짜리 textarea", box["tag"] == "TEXTAREA" and box["rows"] == "1" and box["form"], box)

    longtxt = "오늘 성수 골목은 사람이 정말 많았어. 커피도 맛있었고 사진도 잘 나왔으니 다음에 또 오자!"
    pageC.fill("#s-photo .dcmt.dcmt-day .cmt-in", longtxt)
    pageC.wait_for_timeout(320)
    grown = pageC.evaluate("""() => {
      const el = document.querySelector('#s-photo .dcmt.dcmt-day .cmt-in');
      const cs = getComputedStyle(el);
      const lh = parseFloat(cs.lineHeight) || 20;
      return {h: Math.round(el.getBoundingClientRect().height), w: Math.round(el.getBoundingClientRect().width),
        sw: el.scrollWidth, cw: el.clientWidth, sh: el.scrollHeight, ch: el.clientHeight,
        lines: Math.round((el.scrollHeight - 0) / lh), val: el.value.length};
    }""")
    check("긴 댓글은 칸이 아래로 늘어남 (한 줄 40px → %dpx)" % grown["h"], grown["h"] > 50, grown)
    check("가로로 흐르지 않고 화면 폭 안에서 줄바꿈 (scrollWidth ≤ clientWidth)",
          grown["sw"] <= grown["cw"] + 1, (grown["sw"], grown["cw"]))
    check("글이 다 보이도록 높이가 내용에 맞춰짐 (스크롤로 숨지 않음)",
          grown["sh"] <= grown["ch"] + 2 or grown["h"] >= 120, (grown["sh"], grown["ch"], grown["h"]))

    # Shift+Enter 는 줄바꿈 (등록되지 않음)
    pageC.locator("#s-photo .dcmt.dcmt-day .cmt-in").press("Shift+Enter")
    pageC.wait_for_timeout(260)
    shifted = pageC.evaluate("""() => ({val: document.querySelector('#s-photo .dcmt.dcmt-day .cmt-in').value,
      n: document.querySelectorAll('#s-photo .dcmt.dcmt-day .cmt-t').length})""")
    check("Shift+Enter 는 줄바꿈", "\n" in shifted["val"] and shifted["n"] == 0, shifted)

    # Enter 는 등록 — 댓글이 담기고 칸은 1줄로 돌아옴
    before_n = pageC.evaluate("() => document.querySelectorAll('#s-photo .dcmt.dcmt-day .cmt-t').length")
    pageC.locator("#s-photo .dcmt.dcmt-day .cmt-in").press("Enter")
    pageC.wait_for_timeout(760)
    posted = pageC.evaluate("""() => {
      const el = document.querySelector('#s-photo .dcmt.dcmt-day .cmt-in');
      return {n: document.querySelectorAll('#s-photo .dcmt.dcmt-day .cmt-t').length,
        last: (document.querySelector('#s-photo .dcmt.dcmt-day .cmt-t:last-of-type') || {}).textContent || '',
        all: [...document.querySelectorAll('#s-photo .dcmt.dcmt-day .cmt-t')].map(x => x.textContent).join(' | '),
        val: el ? el.value : 'reset?', h: el ? Math.round(el.getBoundingClientRect().height) : -1};
    }""")
    check("Enter 로 댓글이 등록됨", posted["n"] == before_n + 1 and "성수 골목" in posted["all"], posted)
    check("등록하면 칸이 1줄로 돌아감", posted["val"] == "" and posted["h"] <= 44, posted)
    pageC.screenshot(path=os.path.join(SHOT, "photo-v45-comment.png"))
    check("브라우저 콘솔/페이지 오류 없음 (댓글)", len(errsC) == 0, errsC[:4])
    ctxC.close()

    # ==================================================================
    # 15. 사진 추가 시트 — 요약 줄 없음 · 「기록 이름」 위 「날짜」 아래
    # ==================================================================
    ctxU = new_ctx(browser)
    ctxU.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageU = ctxU.new_page()
    errsU = []
    watch(pageU, errsU)
    pageU.goto(URL + "?demo=1", wait_until="networkidle")
    pageU.wait_for_timeout(700)
    seedU = pageU.evaluate("JSON.stringify(window.__app.state)")
    pageU.goto(URL, wait_until="domcontentloaded")
    pageU.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seedU)
    pageU.reload(wait_until="networkidle")
    pageU.wait_for_timeout(900)
    tab(pageU, 3, 700)
    pageU.set_input_files("#photoInput", os.path.join(ROOT, "icons", "icon-512.png"))
    pageU.wait_for_timeout(800)
    up = pageU.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const a = sh.querySelector('input[name=date]'), b = sh.querySelector('input[name=album_tag]');
      const ra = a.getBoundingClientRect(), rb = b.getBoundingClientRect();
      const sub = [...sh.querySelectorAll('.sheet-sub')].map(x => x.textContent);
      return {head: (sh.querySelector('.sheet-hd h2') || {}).textContent || '',
        labels: [...sh.querySelectorAll('.up-row label')].map(l => l.textContent),
        nmTop: Math.round(rb.top), dateTop: Math.round(ra.top),
        stacked: rb.bottom <= ra.top + 2, sameLeft: Math.abs(ra.left - rb.left) < 2,
        wN: Math.round(rb.width), wD: Math.round(ra.width),
        sub: sub.join(' | '), upSum: !!document.getElementById('upSum')};
    }""")
    check("«사진 추가» 시트가 열림", up["head"] == "사진 추가", up["head"])
    check("장수·용량·1800px 요약 줄은 없음", not up["upSum"] and "1800px" not in up["sub"], (up["upSum"], up["sub"]))
    check("「기록 이름」이 위, 「날짜」가 아래 (한 줄 아님)", up["labels"] == ["기록 이름", "날짜"]
          and up["stacked"] and up["nmTop"] < up["dateTop"], up)
    check("두 칸이 같은 왼쪽에서 화면 폭을 다 씀", up["sameLeft"] and up["wN"] > 150 and up["wD"] > 150, up)
    pageU.screenshot(path=os.path.join(SHOT, "photo-v45-upload.png"))
    pageU.keyboard.press("Escape")
    pageU.wait_for_timeout(300)

    # ==================================================================
    # 16. 사진첩 기록 이름은 날짜보다 조금 작게
    # ==================================================================
    listed = pageU.evaluate("""() => {
      const d = document.querySelector('#s-photo .pday-hd .d');
      const t = document.querySelector('#s-photo .pday-tag');
      return {d: d ? getComputedStyle(d).fontSize : '', t: t ? getComputedStyle(t).fontSize : '',
        sameLine: (() => { if (!d || !t) return false;
          return Math.abs(d.getBoundingClientRect().top - t.getBoundingClientRect().top) < 8; })()};
    }""")
    check("사진첩 목록 — 기록 이름이 날짜보다 2px 작게 (15px → 13px)",
          listed["d"] == "15px" and listed["t"] == "13px" and listed["sameLine"], listed)
    pageU.locator("#s-photo [data-act='openPhotoDay']").last.click()
    pageU.wait_for_timeout(760)
    dayhead = pageU.evaluate("""() => {
      const h = document.querySelector('#s-photo .dgal-tt h1');
      const t = document.querySelector('#s-photo .dgal-tag');
      return {h: h ? getComputedStyle(h).fontSize : '', t: t ? getComputedStyle(t).fontSize : '',
        hTxt: h ? h.textContent : '', tTxt: t ? t.textContent : ''};
    }""")
    check("날짜 모아보기 — 기록 이름이 날짜보다 작게 (20px → 16px)",
          dayhead["h"] == "20px" and dayhead["t"] == "16px" and bool(dayhead["tTxt"]), dayhead)
    pageU.screenshot(path=os.path.join(SHOT, "photo-v45-dayhead.png"))
    check("브라우저 콘솔/페이지 오류 없음 (사진 시트·머리)", len(errsU) == 0, errsU[:4])
    ctxU.close()

    # ==================================================================
    # 17. 모눈 다이어리 — 되돌리기·다시 실행은 펜 옆 · 펜 도크는 글씨 없는 한 줄
    # ==================================================================
    ctxR = new_ctx(browser)
    ctxR.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageR = ctxR.new_page()
    errsR = []
    watch(pageR, errsR)
    pageR.goto(URL + "?demo=1", wait_until="networkidle")
    pageR.wait_for_timeout(700)
    seedR = pageR.evaluate("""() => {
      const st = JSON.parse(JSON.stringify(window.__app.state));
      st.lists = (st.lists || []).concat([{ id: 'Lm45', title: '그림판', emoji: '', kind: 'memo', items: [] }]);
      st.groups = st.groups || {}; st.groups['list:Lm45'] = [];
      st.noteOrder = (st.noteOrder || []).filter(k => k !== 'list:Lm45').concat(['list:Lm45']);
      return JSON.stringify(st);
    }""")
    pageR.goto(URL, wait_until="domcontentloaded")
    pageR.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seedR)
    pageR.reload(wait_until="networkidle")
    pageR.wait_for_timeout(900)
    tab(pageR, 2, 700)
    pageR.locator("#s-diary .lchip", has_text="그림판").first.click()
    pageR.wait_for_timeout(560)
    pageR.locator("#s-diary .d41-new").click()
    pageR.wait_for_timeout(820)

    top = pageR.evaluate("""() => ({
      topBtns: [...document.querySelectorAll('#sheet .d41-top button')].map(b => b.getAttribute('aria-label')),
      title: !!document.querySelector('#sheet .d41-top .d41-title'),
      topText: (document.querySelector('#sheet .d41-top') || {}).textContent ? document.querySelector('#sheet .d41-top').textContent.trim() : '',
      undoInTools: !!document.querySelector('#sheet .d41-tools #d41UndoBtn'),
      redoInTools: !!document.querySelector('#sheet .d41-tools #d41RedoBtn'),
      undoInTop: !!document.querySelector('#sheet .d41-top #d41UndoBtn'),
      order: [...document.querySelectorAll('#sheet .d41-tools > *')].map(e => e.id || e.getAttribute('aria-label') || e.className),
      undoLeft: (() => { const u = document.querySelector('#sheet .d41-tools #d41UndoBtn');
        const p = document.querySelector('#sheet .d41-tool[aria-label="사진 넣기"]');
        return !!(u && p) && u.getBoundingClientRect().left < p.getBoundingClientRect().left; })()
    })""")
    check("위 줄(.d41-top)은 ‹ 뒤로가기 하나만 — 제목 글씨·입력칸 없음 (v50)",
          top["topBtns"] == ["뒤로"] and not top["title"] and top["topText"] == "", top)
    check("되돌리기·다시 실행은 도구 줄 왼쪽 끝 · 펜·T·사진은 오른쪽 (v46)", top["undoInTools"] and top["redoInTools"]
          and not top["undoInTop"] and top["undoLeft"], top)

    pageR.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    pageR.wait_for_timeout(360)
    dock = pageR.evaluate("""() => {
      const rows = [...document.querySelectorAll('#sheet .d41-prow-dock')];
      const btns = [...document.querySelectorAll('#sheet .d41-dk')];
      return {rows: rows.length, n: btns.length,
        labels: btns.map(b => b.getAttribute('aria-label')),
        texts: btns.map(b => (b.textContent || '').trim()).filter(Boolean),
        firstRowText: rows[0] ? (rows[0].textContent || '').trim() : '',
        dots: document.querySelectorAll('#sheet .d41-dot').length,
        on: (document.querySelector('#sheet .d41-dk.on') || {}).getAttribute ? document.querySelector('#sheet .d41-dk.on').getAttribute('aria-label') : '',
        swatch: (document.querySelector('#sheet .d41-dkk') || {}).style ? document.querySelector('#sheet .d41-dkk').style.background : ''};
    }""")
    check("펜을 누르면 한 줄짜리 그림 도크 (글씨 라벨 없음)",
          dock["rows"] == 1 and dock["n"] == 6 and dock["firstRowText"] == "" and dock["texts"] == [], dock)
    check("도크 — 가는 펜 · 일반 펜 · 형광펜 · 지우개 · 색 동그라미 · 전체 지우기",
          dock["labels"] == ["가는 펜", "일반 펜", "형광펜", "지우개", "펜 색", "전체 지우기"], dock["labels"])
    check("처음엔 일반 펜이 골라져 있고 색 동그라미는 검정",
          dock["on"] == "일반 펜" and dock["swatch"] in ("rgb(17, 17, 17)", "#111111"), (dock["on"], dock["swatch"]))
    pageR.screenshot(path=os.path.join(SHOT, "diary-v45-dock.png"))

    DRAW = """([pts]) => {
      const svgEl = document.getElementById('d41Pen');
      const paper = document.getElementById('d41Paper');
      const r = paper.getBoundingClientRect();
      const W = r.width;
      const mk = (type, p) => new PointerEvent(type, {pointerId: 901, pointerType: 'touch',
        clientX: r.left + p[0] * W, clientY: r.top + p[1] * W, bubbles: true, cancelable: true});
      svgEl.dispatchEvent(mk('pointerdown', pts[0]));
      for (let i = 1; i < pts.length; i++) svgEl.dispatchEvent(mk('pointermove', pts[i]));
      svgEl.dispatchEvent(mk('pointerup', pts[pts.length - 1]));
      return JSON.parse(document.getElementById('d41PenIn').value);
    }"""
    pageR.locator("#sheet .d41-dk[aria-label='가는 펜']").click()
    pageR.wait_for_timeout(260)
    thin = pageR.evaluate(DRAW, [[[0.2, 0.5], [0.4, 0.56], [0.6, 0.52]]])
    pageR.wait_for_timeout(320)
    check("«가는 펜» 을 고르면 가는 선(w=2)으로 그려짐", bool(thin) and abs(thin[-1].get("w", 0) - 2) < 0.01,
          [t.get("w") for t in thin])
    pageR.locator("#sheet .d41-dk[aria-label='일반 펜']").click()
    pageR.wait_for_timeout(260)
    thick = pageR.evaluate(DRAW, [[[0.2, 0.7], [0.4, 0.76], [0.6, 0.72]]])
    pageR.wait_for_timeout(320)
    check("«일반 펜» 은 조금 굵게(w=4.5)", bool(thick) and abs(thick[-1].get("w", 0) - 4.5) < 0.01,
          [t.get("w") for t in thick])

    pageR.locator("#sheet .d41-dk[aria-label='펜 색']").click()
    pageR.wait_for_timeout(380)
    pick = pageR.evaluate("""() => ({sp: !document.getElementById('d41Sp').hidden,
      presets: document.querySelectorAll('#sheet .d41-sp-dotb').length,
      on: document.querySelectorAll('#sheet .d41-dk[aria-label="펜 색"].on').length})""")
    check("색 동그라미를 누르면 색상 스펙트럼 판이 열림 (프리셋 9색)",
          pick["sp"] and pick["presets"] == 9 and pick["on"] == 1, pick)
    pageR.locator("#sheet .d41-sp-dotb").nth(2).click()
    pageR.wait_for_timeout(340)
    colored = pageR.evaluate("""() => ({sp: !document.getElementById('d41Sp').hidden,
      swatch: (document.querySelector('#sheet .d41-dkk') || {}).style ? document.querySelector('#sheet .d41-dkk').style.background : ''})""")
    check("색을 고르면 판이 접히고 동그라미 색이 바뀜", colored["sp"] is False
          and colored["swatch"] in ("rgb(220, 74, 152)", "#DC4A98"), colored)
    pageR.locator("#sheet .d41-dk[aria-label='형광펜']").click()
    pageR.wait_for_timeout(260)
    hlOn = pageR.evaluate("() => { const b = document.querySelector('#sheet .d41-dk.on'); return b ? b.getAttribute('aria-label') : ''; }")
    check("형광펜 단추도 그대로 골라짐", hlOn == "형광펜", hlOn)
    pageR.locator("#sheet .d41-dk[aria-label='전체 지우기']").click()
    pageR.wait_for_timeout(360)
    cleared = pageR.evaluate("() => ({paths: document.querySelectorAll('#d41Pen path').length, saved: JSON.parse(document.getElementById('d41PenIn').value).length})")
    check("전체 지우기로 그린 선이 모두 사라짐", cleared["paths"] == 0 and cleared["saved"] == 0, cleared)
    pageR.locator("#sheet .d41-dk[aria-label='일반 펜']").click()
    pageR.wait_for_timeout(240)
    pageR.evaluate(DRAW, [[[0.2, 0.3], [0.5, 0.34]]])
    pageR.wait_for_timeout(420)
    pageR.locator("#d41UndoBtn").click()
    pageR.wait_for_timeout(360)
    check("도구 줄의 ↶ 로 마지막 선이 되돌려짐",
          pageR.evaluate("document.querySelectorAll('#d41Pen path').length") == 0)
    # ---- 글씨 도구도 한 줄 ----
    pageR.locator("#sheet .d41-tool[aria-label='글씨']").click()
    pageR.wait_for_timeout(420)
    tp = pageR.evaluate("""() => {
      const p = document.getElementById('d41Panel');
      const row = p.querySelector('.d41-trow');
      const btns = row ? [...row.querySelectorAll('button, .d41-pv')] : [];
      const r = e => e ? e.getBoundingClientRect() : null;
      const cs = s => { const e = p.querySelector(s); return e ? getComputedStyle(e) : null; };
      const align = p.querySelector('[data-act=d41Align]');
      const b = p.querySelector('[data-act=d41Bold]');
      const c = p.querySelector('.d41-tc');
      const core = btns.filter(e => !e.classList.contains('d41-tc'));
      const centers = core.map(e => Math.round(r(e).top + r(e).height / 2));
      const spread = centers.length ? Math.max.apply(null, centers) - Math.min.apply(null, centers) : 99;
      return {row: !!row, spread: spread,
        order: btns.map(e => e.getAttribute('data-act') || e.getAttribute('aria-label') || e.textContent.trim()),
        alignH: r(align) ? Math.round(r(align).height) : 0,
        bFs: cs('[data-act=d41Bold]') ? cs('[data-act=d41Bold]').fontSize : '',
        sizeFs: cs('[data-act=d41SizeStep]') ? cs('[data-act=d41SizeStep]').fontSize : '',
        colorW: r(c) ? Math.round(r(c).width) : 0,
        dots: p.querySelectorAll('.d41-dot').length,
        edit: p.querySelectorAll('[data-act=d41Edit]').length,
        blur: p.querySelectorAll('[data-act=d41Blur]').length,
        hint: p.querySelectorAll('.d41-phint').length,
        panelText: (p.innerText || '').replace(/\s+/g, ' ').trim()};
    }""")
    check("글씨 도구가 «한 줄» (정렬 · B · S · U · − 크기 + · 색)",
          tp["row"] and tp["spread"] <= 2 and tp["order"] == ["d41Align", "d41Bold", "d41Strike", "d41Underline",
            "d41SizeStep", "17", "d41SizeStep", "d41ColorPick"], tp)
    check("단추 글씨·아이콘이 커짐 (정렬 40px · B 17px · − 21px)",
          tp["alignH"] >= 38 and tp["bFs"] in ("17px",) and tp["sizeFs"] in ("21px",), tp)
    check("색 동그라미는 22px 로 작게 · 처음엔 컬러판 접힘",
          tp["colorW"] == 22 and tp["dots"] == 0, (tp["colorW"], tp["dots"]))
    check("「글 수정 / 키보드 내리기」 줄과 안내 글씨 없음",
          tp["edit"] == 0 and tp["blur"] == 0 and tp["hint"] == 0
          and "글 수정" not in tp["panelText"] and "키보드 내리기" not in tp["panelText"]
          and "한 번 더" not in tp["panelText"], tp["panelText"])
    pageR.locator("#sheet .d41-tc[data-act=d41ColorPick]").click()
    pageR.wait_for_timeout(380)
    pal = pageR.evaluate("""() => ({presets: document.querySelectorAll('#sheet .d41-sp-dotb').length,
      colors: [...document.querySelectorAll('#sheet .d41-sp-dotb')].map(d => d.getAttribute('data-color')),
      cvTop: (() => { const c = document.getElementById('d41SpCv');
        const t = document.querySelector('#sheet #d41Panel .d41-trow');
        return c && t ? Math.round(c.getBoundingClientRect().top) > Math.round(t.getBoundingClientRect().top) : false; })()})""")
    check("색 동그라미를 누르면 색상 스펙트럼 판(프리셋 9색)이 아래에 펼쳐짐",
          pal["presets"] == 9 and len(set(pal["colors"])) == 9 and pal["cvTop"], pal)
    pageR.locator("#sheet .d41-sp-dotb").nth(3).click()
    pageR.wait_for_timeout(340)
    picked = pageR.evaluate("""() => ({sp: !document.getElementById('d41Sp').hidden,
      swatch: (document.querySelector('#sheet .d41-tc') || {}).style ? document.querySelector('#sheet .d41-tc').style.background : ''})""")
    check("색을 고르면 판이 접히고 동그라미에 그 색",
          picked["sp"] is False and picked["swatch"] in ("rgb(146, 104, 201)", "#9268C9"), picked)
    pageR.screenshot(path=os.path.join(SHOT, "diary-v45-textbar.png"))
    check("브라우저 콘솔/페이지 오류 없음 (다이어리 도구)", len(errsR) == 0, errsR[:4])
    ctxR.close()

    # ==================================================================
    # 마무리
    # ==================================================================
    print("")
    if fails:
        print("FAILED (%d): %s" % (len(fails), ", ".join(fails)))
        sys.exit(1)
    print("ALL PASS — v45")
