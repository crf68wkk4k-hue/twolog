"""투로그 v42 확인 — 「기념일 & 생일」 시트 정리 + 프로필 편집에서 생일 고치기.

1) 버전: sw.js 캐시 twolog-v49 · APP_VERSION v49 · My 탭 「버전 v49」
2) 기념일 & 생일 시트 (홈 D-day 카드를 눌러 열기)
   - 「홈 D-day 위에 이 문구가 그대로 보여요.」 안내 문구가 사라짐
   - 아래쪽 생일 달력 입력칸(.bd-in.js-bday) 두 개가 사라짐 · 「고른 생일은 바로 위에 …」 안내도 사라짐
     (v45: 프로필 생일은 다시 날짜칸 하나 — type=date · name=bday)
   - 1주년·2주년·3주년 줄은 그대로, 생일은 「소영 생일 · 6월 26일 · D-…」 요약 줄만 (요약 줄 유지)
3) 프로필 편집 연결
   - 시트 안에 「프로필 편집」 버튼이 있고, 누르면 프로필 편집 화면(내 프로필 · 닉네임 · 생일)이 열림
   - 프로필에서 생일을 바꿔 저장하면 기념일 시트로 돌아와 요약 줄이 새 날짜로 바뀜
   - 「준영 생일」 줄을 눌러도 준영 프로필 편집이 열려 두 사람 생일을 모두 고칠 수 있음
   - 프로필에서 닫기만 눌러도 기념일 시트로 돌아옴
4) 저장·다시 열기 — 바꾼 생일이 남아 있고 홈 D-day 는 그대로
5) 날짜 모아보기 — 사진 12장인 날은 3×3 9장만, 9번째 칸 오른쪽 아래 「+3」 배지
   · 배지를 누르면 12장 모두 펼침 · 9번째 사진을 누르면 크게 보기에서 12장을 옆으로 넘겨 봄
6) 날짜 모아보기 머리줄이 화면 꼭대기에 붙지 않고 두 칸(28px 이상) 내려서 시작
7) + 시트 — 카테고리 줄에 속지 배지 없이 ≡ · 이름(+ 삭제)만 · 아코디언 제목 「속지」·안내에 「」 없음
   · 빈 카테고리는 속지 변경 저장 성공 / 글이 있는 카테고리는 변경 차단 + 안내 문구
8) 콘솔/페이지 오류 0건

    python3 tests/v42.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def watch(page, bucket):
    page.on("pageerror", lambda e: bucket.append("pageerror: " + str(e)))
    page.on("console", lambda m: bucket.append("console: " + m.text) if m.type == "error" else None)


def tab(page, idx, wait=520):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def open_dday(page):
    page.locator("#s-home .dday").click()
    page.wait_for_timeout(480)


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
    check("sw.js 캐시 버전 twolog-v49", 'const VERSION = "twolog-v49"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v49", 'var APP_VERSION = "v49"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed_state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed_state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)

    tab(page, 4, 600)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v49」", ver.strip() == "버전 v49", ver)

    tab(page, 0, 520)

    # ==================================================================
    # 2. 기념일 & 생일 시트 — 문구·생일 입력칸 정리
    # ==================================================================
    open_dday(page)
    sheet_txt = page.locator("#sheet").inner_text()
    check("「홈 D-day 위에 이 문구가 그대로 보여요.」 문구 없음",
          "홈 D-day 위에 이 문구가 그대로 보여요" not in sheet_txt, sheet_txt[:160])
    check("「상단 문구」 입력칸은 그대로 (v43 에서 이름만 바뀜)", page.locator('#sheetForm input[name="phrase"]').count() == 1)
    check("처음 만난 날 입력칸은 그대로", page.locator('#sheetForm input[name="since"]').count() == 1)

    bd_inputs = page.evaluate("""() => ({
      bday: document.querySelectorAll('#sheet input.js-bday').length,
      any_date: document.querySelectorAll('#sheet input[type=date]').length,
      bdin: document.querySelectorAll('#sheet .bd-in').length})""")
    check("생일 달력 입력칸(.bd-in.js-bday) 없음", bd_inputs["bday"] == 0 and bd_inputs["bdin"] == 0, bd_inputs)
    check("시트 안 date 입력은 「처음 만난 날」 하나뿐", bd_inputs["any_date"] == 1, bd_inputs)
    check("「고른 생일은 바로 위에 …」 안내 없음", "고른 생일은 바로 위에" not in sheet_txt)
    check("주년 세 줄 유지", all(k in sheet_txt for k in ["1주년", "2주년", "3주년"]), sheet_txt[:200])

    rows = page.evaluate("""() => [...document.querySelectorAll('#sheet .mile-row')].map(r => ({
        txt: r.innerText.replace(/\\s+/g, ' ').trim(),
        btn: r.tagName === 'BUTTON',
        name: (r.querySelector('.mile-n') || {}).textContent || '',
        date: (r.querySelector('.mile-d') || {}).textContent || '',
        left: ((r.querySelector('.mile-x') || {}).textContent || '').trim(), go: !!r.querySelector('.mile-go')}))""")
    bd_rows = [r for r in rows if "생일" in r["name"]]
    check("생일 요약 줄 두 개 유지", len(bd_rows) == 2 and
          any("소영 생일" in r["name"] for r in bd_rows) and any("준영 생일" in r["name"] for r in bd_rows), bd_rows)
    filled = [r for r in bd_rows if re.match(r"^\d{1,2}월 \d{1,2}일$", r["date"])]
    check("생일이 있으면 요약 줄에 「M월 D일 · D-…」", len(filled) >= 1 and
          all(r["left"].startswith("D-") or r["left"] == "오늘" for r in filled), bd_rows)
    check("생일이 없으면 요약 줄은 「생일을 넣어 주세요」", all(
          r["date"] != "생일을 넣어 주세요" or r["left"] == "—" for r in bd_rows), bd_rows)
    check("생일 줄은 눌러서 편집(버튼 · ›)", all(r["btn"] and r["go"] for r in bd_rows), bd_rows)

    # 프로필 편집 버튼
    btns = page.evaluate("""() => [...document.querySelectorAll('#sheet button')]
        .filter(b => (b.textContent || '').includes('프로필 편집'))
        .map(b => ({txt: b.textContent.trim(), who: b.getAttribute('data-who')}))""")
    check("「프로필 편집」 버튼 두 개 (소영·준영)", len(btns) == 2 and
          {b["who"] for b in btns} == {"me", "you"} and all("프로필 편집" in b["txt"] for b in btns), btns)
    page.screenshot(path=os.path.join(SHOT, "dday-v42-sheet.png"))

    # ==================================================================
    # 3. 프로필 편집 — 내 프로필 (생일 포함)
    # ==================================================================
    page.locator('#sheet button[data-act="personSheet"][data-who="me"].btn-line').click()
    page.wait_for_timeout(480)
    prof = page.evaluate("""() => {
      const q = (s) => document.querySelector(s);
      const inp = q('#sheet input[name=bday]');
      return {head: (q('#sheet .sheet-hd h2') || {}).textContent || '',
              name: (q('#sheet #personName') || {}).value || '',
              bday: inp ? inp.value : null,
              date: !!inp && inp.type === 'date',
              sel3: !!q('#sheet select.pr-bday-y'),
              bdLabel: [...document.querySelectorAll('#sheet .f label')].map(l => l.textContent.trim()),
              save: !!q('#sheet button[type=submit]')};}""")
    check("내 프로필 편집 화면이 열림", prof["head"].strip() == "내 프로필", prof)
    check("프로필에 닉네임 칸", prof["name"] == "소영", prof)
    # v45: 생일은 날짜칸 한 개 (v44 의 «년/월/일» 세 칸은 다시 걷어냄)
    check("프로필에 생일 날짜칸 하나 · «생일» 라벨", prof["date"] and not prof["sel3"]
          and "생일" in prof["bdLabel"], prof)
    page.screenshot(path=os.path.join(SHOT, "dday-v42-profile.png"))

    page.fill("#sheet input[name=bday]", "1993-03-15")
    page.wait_for_timeout(260)
    page.locator("#personForm button[type=submit]").click()
    page.wait_for_timeout(620)
    back = page.evaluate("""() => ({
      head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent || '',
      me: (document.querySelector('#sheet [data-bdtxt=me]') || {}).textContent || '',
      meLeft: ((document.querySelector('#sheet [data-bdleft=me]') || {}).textContent || '').trim(),
      stored: ((window.__app.state.couple.birthdays || {}).me) || ''})""")
    check("저장하면 기념일 시트로 돌아옴", back["head"].strip() == "프로필 편집", back)
    check("내 생일 요약 줄이 3월 15일로", back["me"].strip() == "3월 15일" and back["stored"] == "1993-03-15", back)
    check("바꾼 생일 D-day 다시 계산", back["meLeft"].startswith("D-") or back["meLeft"] == "오늘", back)

    # ==================================================================
    # 4. 「준영 생일」 줄 → 준영 프로필 편집 → 생일 바꾸기
    # ==================================================================
    page.locator('#sheet .mile-btn[data-who="you"]').click()
    page.wait_for_timeout(480)
    you = page.evaluate("""() => ({
      head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent || '',
      name: (document.querySelector('#sheet #personName') || {}).value || '',
      bday: (document.querySelector('#sheet input[name=bday]') || {}).value || ''})""")
    check("준영 생일 줄 → 준영 프로필 편집 열림", you["name"] == "준영" and "준영" in you["head"], you)
    page.fill("#sheet input[name=bday]", "1995-11-20")
    page.wait_for_timeout(260)
    page.locator("#personForm button[type=submit]").click()
    page.wait_for_timeout(620)
    back2 = page.evaluate("""() => ({
      head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent || '',
      you: (document.querySelector('#sheet [data-bdtxt=you]') || {}).textContent || ''})""")
    check("준영 생일 저장 → 기념일 시트로 · 11월 20일", back2["head"].strip() == "프로필 편집" and
          back2["you"].strip() == "11월 20일", back2)

    # 닫기만 눌러도 기념일 시트로 (바꾼 값은 저장하지 않음)
    page.locator('#sheet .mile-btn[data-who="me"]').click()
    page.wait_for_timeout(420)
    page.locator('#sheet [data-close]').first.click()
    page.wait_for_timeout(480)
    closed = page.evaluate("""() => ({
      head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent || '',
      open: document.getElementById('sheetWrap').classList.contains('open')})""")
    check("프로필에서 닫기 → 기념일 시트로 돌아옴", closed["open"] and closed["head"].strip() == "프로필 편집", closed)

    # ==================================================================
    # 5. 기념일 시트 저장 → 다시 열어도 그대로
    # ==================================================================
    page.fill('#sheetForm input[name="since"]', "2025-11-16")
    page.locator("#sheetForm button[type=submit]").click()
    page.wait_for_timeout(650)
    home = page.locator("#s-home .dday").inner_text()
    check("홈 D-day 그대로 (D+…)", re.search(r"D\+\d+", home) is not None, home[:120])
    open_dday(page)
    again = page.evaluate("""() => ({
      me: (document.querySelector('#sheet [data-bdtxt=me]') || {}).textContent || '',
      you: (document.querySelector('#sheet [data-bdtxt=you]') || {}).textContent || '',
      bdayInputs: document.querySelectorAll('#sheet input.js-bday').length})""")
    check("다시 열어도 바꾼 생일이 그대로", again["me"].strip() == "3월 15일" and
          again["you"].strip() == "11월 20일" and again["bdayInputs"] == 0, again)
    page.screenshot(path=os.path.join(SHOT, "dday-v42-sheet.png"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(320)
    check("브라우저 콘솔/페이지 오류 없음 (기념일 시트)", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 6. 날짜 모아보기 — 9장(3×3) + 9번째 칸 「+N」 · 상단 여백
    # ==================================================================
    ctx2 = new_ctx(browser)
    ctx2.add_init_script("window.__TWOLOG_MODE = 'local';")
    page2 = ctx2.new_page()
    errs2 = []
    watch(page2, errs2)
    page2.goto(URL + "?demo=1", wait_until="networkidle")
    page2.wait_for_timeout(600)
    day_ymd = page2.evaluate("""() => {
      const st = JSON.parse(JSON.stringify(window.__app.state));
      const d = new Date(), p2 = (n) => String(n).padStart(2, '0');
      const ymd = d.getFullYear() + '-' + p2(d.getMonth() + 1) + '-' + p2(d.getDate());
      st.photos = Array.from({length: 12}, (_, i) => ({
        id: 'vp42-' + (i + 1), date: ymd, album: '롯데 리조트',
        title: '사진 ' + (i + 1), place: '', memo: '', art: i % 12, capBg: '#FFFFFF'}));
      localStorage.setItem('twolog:v1:state', JSON.stringify(st));
      return ymd;
    }""")
    page2.goto(URL, wait_until="networkidle")
    page2.wait_for_timeout(900)
    tab(page2, 3, 700)
    page2.locator("#s-photo .pday-hd[data-date='%s']" % day_ymd).first.click()
    page2.wait_for_timeout(760)

    day9 = page2.evaluate("""() => {
      const scr = document.getElementById('screens');
      const hd = document.querySelector('#s-photo .dgal-hd');
      const cells = [...document.querySelectorAll('#s-photo .dgrid .dg-cell')];
      const wraps = document.querySelectorAll('#s-photo .dgrid .dg-wrap');
      const pg = document.querySelector('#s-photo .dg-moren');
      const last = cells[cells.length - 1];
      const lr = last ? last.getBoundingClientRect() : null;
      const pr = pg ? pg.getBoundingClientRect() : null;
      const gr = cells.length ? document.querySelector('#s-photo .dgrid').getBoundingClientRect() : null;
      const cols = getComputedStyle(document.querySelector('#s-photo .dgrid') || document.body).gridTemplateColumns;
      const tag = document.querySelector('#s-photo .dgal-tag');
      const h1 = document.querySelector('#s-photo .dgal-tt h1');
      const tcs = tag ? getComputedStyle(tag) : null;
      const hcs = h1 ? getComputedStyle(h1) : null;
      return {head: (document.querySelector('#s-photo .dgal-tt h1') || {}).textContent,
              headAll: (document.querySelector('#s-photo .dgal-hd') || {}).innerText || '',
              year: !!document.querySelector('#s-photo .dgal-y'),
              tagTxt: tag ? tag.textContent : null,
              tagBorder: tcs ? tcs.borderTopWidth : null,
              tagBg: tcs ? tcs.backgroundColor : null,
              tagColor: tcs ? tcs.color : null,
              tagFs: tcs ? tcs.fontSize : null,
              tagFw: tcs ? tcs.fontWeight : null,
              h1Fs: hcs ? hcs.fontSize : null,
              h1Fw: hcs ? hcs.fontWeight : null,
              meta: (document.querySelector('#s-photo .dgal-meta') || {}).textContent || '',
              cells: cells.length, wraps: wraps.length, cols: cols.split(' ').length,
              badge: pg ? pg.textContent.trim() : null,
              badgeIn: !!(pr && lr && pr.right <= lr.right + 1 && pr.bottom <= lr.bottom + 1 &&
                          pr.left > lr.left + lr.width / 2 && pr.top > lr.top + lr.height / 2),
              padTop: hd ? Math.round(hd.getBoundingClientRect().top - scr.getBoundingClientRect().top) : -1,
              gridGap: hd && gr ? Math.round(gr.top - hd.getBoundingClientRect().top) : -1,
              hasComment: !!document.querySelector('#s-photo .dcmt.dcmt-day')};}""")
    check("날짜 모아보기 머리줄", day9["head"] == "11월 21일" or "11월" in (day9["head"] or ""), day9["head"])
    check("총 12장 표기 · 오늘은 장수 옆에 「· 오늘」", "총 12장" in day9["meta"] and day9["meta"].strip() == "총 12장 · 오늘", day9["meta"])
    check("헤더에 연도(2026년)·오늘 표기 없음", not day9["year"] and "년" not in (day9["headAll"] or "")
          and "오늘" not in (day9["headAll"] or ""), {"year": day9["year"], "head": day9["headAll"]})
    check("헤더 「11월 21일 · 롯데 리조트」", "롯데 리조트" in (day9["tagTxt"] or "") and "·" in (day9["headAll"] or ""), day9["headAll"])
    check("기록 이름은 테두리·바탕 없는 검정 글씨 · 날짜보다 조금 작게 (v45)",
          day9["tagBorder"] in ("0px",) and day9["tagBg"] in ("rgba(0, 0, 0, 0)", "transparent")
          and day9["tagColor"] not in ("rgb(255, 255, 255)",)
          and float(day9["h1Fs"].replace("px", "")) - float(day9["tagFs"].replace("px", "")) >= 2,
          {k: day9[k] for k in ("tagBorder", "tagBg", "tagColor", "tagFs", "tagFw", "h1Fs", "h1Fw")})
    check("사진 12장이어도 3×3 9장만 그려짐", day9["cells"] == 9 and day9["wraps"] == 9 and day9["cols"] == 3, day9)
    check("9번째 칸 오른쪽 아래 「+3」 배지", day9["badge"] == "+3" and day9["badgeIn"], day9)
    check("댓글 칸은 9장 바로 아래", day9["hasComment"], day9)
    check("날짜 모아보기 머리줄이 위에서 두 칸(28px 이상) 내려 시작",
          day9["padTop"] >= 28 and day9["gridGap"] >= 40, {k: day9[k] for k in ("padTop", "gridGap")})
    page2.screenshot(path=os.path.join(SHOT, "photo-v42-day9.png"))

    # 9번째 사진을 누르면 (크게 보기 대신) 그 아래로 나머지 사진이 3열로 쭉 펼쳐짐
    page2.locator("#s-photo .dgrid .dg-cell").nth(8).click()
    page2.wait_for_timeout(680)
    exp = page2.evaluate("""() => {
      const cells = [...document.querySelectorAll('#s-photo .dgrid .dg-cell')];
      const g = document.querySelector('#s-photo .dgrid');
      return {cells: cells.length, badge: document.querySelectorAll('#s-photo .dg-moren').length,
              cols: g ? getComputedStyle(g).gridTemplateColumns.split(' ').length : 0,
              sheet: document.getElementById('sheetWrap').classList.contains('open'),
              comment: !!document.querySelector('#s-photo .dcmt.dcmt-day'),
              ids: cells.map(c => c.getAttribute('data-id')),
              belowGrid: !!document.querySelector('#s-photo .dcmt.dcmt-day')};}""")
    check("9번째 사진을 누르면 크게 보기가 아니라 그날 12장이 아래로 모두 펼쳐짐",
          exp["cells"] == 12 and not exp["sheet"] and exp["badge"] == 0, exp)
    check("펼친 뒤에도 3열 그리드 · 10~12번째가 댓글 위에 붙음",
          exp["cols"] == 3 and exp["ids"][9:] == ["vp42-10", "vp42-11", "vp42-12"] and exp["comment"], exp)
    page2.screenshot(path=os.path.join(SHOT, "_p42-day-all.png"))

    # 펼친 뒤에는 아무 사진이나 눌러 크게 보기 (10번째부터 12장을 옆으로 넘겨 봄)
    page2.locator("#s-photo .dgrid .dg-cell").nth(9).click()
    page2.wait_for_timeout(760)
    pv = page2.evaluate("""() => {
      const strip = document.querySelector('#sheet .pv40-strip');
      if (!strip) return {open: false};
      const slides = [...strip.querySelectorAll('.pv40-slide')].map(s => s.getAttribute('data-id'));
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
              n: slides.length, first: slides[0], ninth: slides[8], last: slides[slides.length - 1],
              at: Math.round(strip.scrollLeft / (strip.clientWidth || 1)),
              cur: slides[Math.round(strip.scrollLeft / (strip.clientWidth || 1))],
              slidesWide: Math.round(strip.scrollWidth / (strip.clientWidth || 1))};}""")
    check("펼친 뒤 사진을 누르면 크게 보기가 열림", pv.get("open") and pv.get("n") == 12, pv)
    check("크게 보기는 그날 12장을 모두 담고 누른 사진(10번째)부터", pv.get("cur") == "vp42-10" and pv.get("at") == 9, pv)
    check("옆으로 밀면 10~12번째까지 넘어감", pv.get("last") == "vp42-12" and pv.get("slidesWide") >= 12, pv)
    page2.keyboard.press("Escape")
    page2.wait_for_timeout(320)
    check("브라우저 콘솔/페이지 오류 없음 (날짜 모아보기)", len(errs2) == 0, errs2[:4])
    ctx2.close()

    # ==================================================================
    # 7. + 시트 — 카테고리 줄은 ≡ · 이름만 (속지 배지 없음) · 패널 문구
    # ==================================================================
    ctx3 = new_ctx(browser)
    ctx3.add_init_script("window.__TWOLOG_MODE = 'local';")
    page3 = ctx3.new_page()
    errs3 = []
    watch(page3, errs3)
    page3.goto(URL + "?demo=1", wait_until="networkidle")
    page3.wait_for_timeout(700)
    seed3 = page3.evaluate("JSON.stringify(window.__app.state)")
    page3.goto(URL, wait_until="domcontentloaded")
    page3.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed3)
    page3.goto(URL, wait_until="networkidle")
    page3.wait_for_timeout(900)
    tab(page3, 2, 660)
    page3.locator("#s-diary .hdr .note-add").click()
    page3.wait_for_timeout(560)

    rows = page3.evaluate("""() => [...document.querySelectorAll('#sheet #noteOrderList .nord-row')].map(r => ({
        name: (r.querySelector('.nord-nm') || {}).value || '',
        badge: !!r.querySelector('.nord-kb'), grip: !!r.querySelector('.nord-grip'),
        del: !!r.querySelector('.nord-del'),
        kind: r.getAttribute('data-kind'),
        // 이름칸 오른쪽 끝과 줄 오른쪽 끝 사이 — 배지 자리에 아무 글씨도 없어야 해요
        tailText: (r.innerText || '').replace((r.querySelector('.nord-nm') || {}).value || '', '').replace('삭제', '').trim()}))""")
    check("+ 시트 카테고리 줄에 속지 배지(.nord-kb)가 없음", len(rows) >= 4 and all(not r["badge"] for r in rows), rows)
    check("줄에는 ≡ 손잡이 + 이름만 (내 카테고리만 오른쪽 「삭제」)",
          all(r["grip"] and r["tailText"] == "" for r in rows)
          and all(r["del"] for r in rows if r["name"] in ("여행 준비물", "주말 데이트")), rows)

    panelw = page3.evaluate("""() => {
      const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
      const memo = rows.filter(r => (r.querySelector('.nord-nm') || {}).value === '메모')[0];
      memo.dispatchEvent(new PointerEvent('pointerdown', {bubbles: true}));
      const p = document.getElementById('nkPanel');
      return {label: (document.querySelector('#sheet #nkindLbl') || {}).textContent || '',
              hint: (document.querySelector('#sheet #nkindHint') || {}).textContent || '',
              open: p ? !p.hidden : false};}""")
    check("아코디언 제목은 「속지」만", panelw["label"].strip() == "속지" and panelw["open"], panelw)
    check("안내 문구는 「메모에 쓸 속지를 골라요.」 (「」 괄호 없이)",
          panelw["hint"].strip() == "메모에 쓸 속지를 골라요." and "「" not in panelw["hint"]
          and "」" not in panelw["hint"], panelw["hint"])
    page3.screenshot(path=os.path.join(SHOT, "note-v42-rows.png"))

    # (a) 내용이 없는 새 카테고리 → 속지 자유롭게 바꾸고 저장
    page3.fill("#sheet .nord-new", "빈 카테고리")
    page3.locator("#sheet .nord-add-btn").click()
    page3.wait_for_timeout(320)
    page3.locator("#sheet #nkPanel .nk-card[data-kind='expense']").click()
    page3.wait_for_timeout(240)
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(780)
    empty_ok = page3.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '빈 카테고리')[0] || {};
        return {kind: l.kind, items: (l.items || []).length}; }""")
    check("내용이 없는 빈 카테고리는 속지를 바꿔 저장할 수 있음", empty_ok["kind"] == "expense" and empty_ok["items"] == 0, empty_ok)

    # (b) 이미 항목이 있는 메모 → 다른 속지로 못 바꿈
    page3.locator("#s-diary .hdr .note-add").click()
    page3.wait_for_timeout(560)
    page3.evaluate("""() => { const rows = [...document.querySelectorAll('#sheet #noteOrderList .nord-row')];
        const memo = rows.filter(r => (r.querySelector('.nord-nm') || {}).value === '메모')[0];
        memo.querySelector('.nord-nm').dispatchEvent(new PointerEvent('pointerdown', {bubbles: true})); }""")
    page3.wait_for_timeout(280)
    page3.locator("#sheet #nkPanel .nk-card[data-kind='memo']").click()
    page3.wait_for_timeout(320)
    blocked = page3.evaluate("""() => ({
      toast: (document.querySelector('#toast') || {}).textContent || '',
      shown: document.getElementById('toast').classList.contains('show'),
      hint: (document.querySelector('#sheet #nkindHint') || {}).textContent || '',
      kind: (document.querySelector('#sheet #noteOrderList .nord-row.active') || {}).getAttribute('data-kind'),
      checked: [...document.querySelectorAll('#sheet #nkPanel .nk-card.active')].map(c => c.getAttribute('data-kind'))})""")
    check("글이 있는 메모에서 다른 속지를 누르면 「이미 작성된 내용이 있어 속지를 바꿀 수 없어요」",
          blocked["shown"] and "이미 작성된 내용이 있어 속지를 바꿀 수 없어요" in blocked["toast"], blocked)
    check("기존 속지 선택이 그대로 유지됨 (data-kind · 카드 체크)",
          blocked["kind"] == "" and blocked["checked"] == [""], blocked)
    check("아코디언 안내에도 같은 문구가 보임", "이미 작성된 내용이 있어" in blocked["hint"], blocked["hint"])
    page3.locator("#sheet button.btn-primary").click()
    page3.wait_for_timeout(760)
    after_save = page3.evaluate("() => ({kinds: window.__app.state.noteKinds || {}, toast: (document.querySelector('#toast') || {}).textContent || ''})")
    check("그대로 저장해도 메모의 속지는 안 바뀜", "todo" not in after_save["kinds"], after_save)
    check("브라우저 콘솔/페이지 오류 없음 (+ 시트)", len(errs3) == 0, errs3[:4])
    ctx3.close()

    # ==================================================================
    # 8. 모눈 캔버스 다이어리 — 위 끝까지 모눈 · 눌러서 글 · 사진 끌기·자르기 · 저장 누락 없음
    # ==================================================================
    import base64 as _b64

    ctx4 = new_ctx(browser)
    ctx4.add_init_script("window.__TWOLOG_MODE = 'local';")
    page4 = ctx4.new_page()
    errs4 = []
    watch(page4, errs4)
    page4.goto(URL + "?demo=1", wait_until="networkidle")
    page4.wait_for_timeout(700)
    page4.evaluate("""() => {
      const s = JSON.parse(JSON.stringify(window.__app.state));
      s.lists = (s.lists || []).concat([{id: 'Lcanvas', title: '그림판 다이어리', emoji: '', kind: 'memo', items: []}]);
      s.groups = s.groups || {}; s.groups['list:Lcanvas'] = [];
      localStorage.setItem('twolog:v1:state', JSON.stringify(s));
    }""")
    page4.goto(URL, wait_until="networkidle")
    page4.wait_for_timeout(900)
    tab(page4, 2, 660)
    page4.locator("#s-diary .lchip", has_text="그림판 다이어리").first.click()
    page4.wait_for_timeout(600)
    page4.locator("#s-diary .d41-new").click()
    page4.wait_for_timeout(760)

    geo4 = page4.evaluate("""() => {
      const top = document.querySelector('#sheet .d41-top').getBoundingClientRect();
      const tools = document.querySelector('#sheet .d41-tools').getBoundingClientRect();
      const paper = document.getElementById('d41Paper').getBoundingClientRect();
      const back = document.querySelector('#sheet .d41-back').getBoundingClientRect();
      const date = document.querySelector('#sheet .d41-date');
      const cs = getComputedStyle(document.getElementById('d41Paper'));
      return {topTop: Math.round(back.top), topBottom: Math.round(top.bottom), toolsTop: Math.round(tools.top),
        toolsBottom: Math.round(tools.bottom), paperTop: Math.round(paper.top),
              dateInPaper: !!date && date.parentElement.id === 'd41Paper',
              grid: cs.backgroundImage.indexOf('linear-gradient') >= 0,
              paperH: Math.round(paper.height),
              canvasH: Math.round(document.getElementById('d41Canvas').clientHeight)};}""")
    # v49: 도구 줄이 위 줄(‹ 뒤로)과 «같은 줄»로 올라가 한 줄이 됐어요 (예전엔 위 줄 아래였습니다)
    check("모눈종이가 화면 맨 위(0)까지 깔리고 위 줄·도구 줄은 그 위에 떠 있음 (v49)",
          geo4["paperTop"] == 0 and geo4["grid"]
          and abs(geo4["toolsTop"] - geo4["topTop"]) <= 1
          and geo4["toolsBottom"] <= geo4["topBottom"] + 2, geo4)
    check("큰 날짜도 모눈 위에 얹혀 있음", geo4["dateInPaper"], geo4["dateInPaper"])
    check("종이는 화면 한 장을 채움", geo4["paperH"] >= geo4["canvasH"] - 6, (geo4["paperH"], geo4["canvasH"]))

    # 종이를 누르면 그 자리에 글 상자 → 바로 써요 (포커스가 남은 채 저장하는 경우까지)
    pb4 = page4.locator("#d41Paper").bounding_box()
    page4.mouse.click(pb4["x"] + 60, pb4["y"] + 240)
    page4.wait_for_timeout(420)
    page4.keyboard.type("오늘은 성수에서 파스타를 먹었다")
    page4.wait_for_timeout(240)
    focused4 = page4.evaluate("document.activeElement && document.activeElement.className")
    check("누른 자리에 글 상자가 생기고 그 자리에서 바로 입력(포커스 유지)",
          page4.evaluate("document.querySelectorAll('#sheet .d41-tx').length") == 1 and "d41-txt" in (focused4 or ""),
          focused4)
    # 저장을 누르는 순간까지 포커스가 글 상자에 남아 있어도 글이 담기는지
    page4.locator("#sheet .d41-back").click()
    page4.wait_for_timeout(900)
    saved4 = page4.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '그림판 다이어리')[0] || {};
      const it = (l.items || [])[0] || {};
      return {texts: it.texts || [], memo: it.memo || '', imgs: it.imgs || [], pen: it.pen || []}; }""")
    check("입력창에 포커스가 남은 채 저장해도 글이 그대로 담김 (사라지지 않음)",
          len(saved4["texts"]) == 1 and saved4["texts"][0]["text"] == "오늘은 성수에서 파스타를 먹었다", saved4["texts"])
    check("목록 미리보기·검색용 본문(it.memo)도 같은 글",
          "파스타" in saved4["memo"], saved4["memo"])
    card4 = page4.evaluate("(document.querySelector('#s-diary .d41-card .nmemo-b') || {}).textContent || ''")
    check("저장하면 목록 카드에 그 글이 보임", "파스타" in card4, card4)

    # 다시 열었을 때 · 새로고침 뒤에도 그대로
    page4.locator("#s-diary .d41-card").first.click()
    page4.wait_for_timeout(760)
    reopen4 = page4.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value);
      const el = document.querySelector('#sheet .d41-txt');
      return {n: t.length, text: (t[0] || {}).text || '', shown: el ? el.innerText : ''}; }""")
    check("다시 열어도 글 상자와 글이 그대로", reopen4["n"] == 1 and "파스타" in reopen4["text"] and "파스타" in reopen4["shown"], reopen4)
    page4.keyboard.press("Escape")
    page4.wait_for_timeout(300)
    page4.reload(wait_until="networkidle")
    page4.wait_for_timeout(900)
    tab(page4, 2, 660)
    page4.locator("#s-diary .lchip", has_text="그림판 다이어리").first.click()
    page4.wait_for_timeout(600)
    page4.locator("#s-diary .d41-card").first.click()
    page4.wait_for_timeout(760)
    after4 = page4.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value);
      return {n: t.length, text: (t[0] || {}).text || ''}; }""")
    check("새로고침(다시 열기) 뒤에도 글이 남음", after4["n"] == 1 and "파스타" in after4["text"], after4)

    # v44: 보기(스크롤)로 열린 다이어리 — 종이를 한 번 눌러 고치기로 전환한 뒤 도구를 써요
    page4.locator("#d41Paper").click()
    page4.wait_for_timeout(360)

    # 글씨 크기 − + 조절 — 고른 글 상자에 바로
    page4.locator("#sheet .d41-tool[aria-label='글씨']").click()
    page4.wait_for_timeout(260)
    tb4 = page4.locator("#sheet .d41-tx").first.bounding_box()
    page4.mouse.click(tb4["x"] + 14, tb4["y"] + 10)
    page4.wait_for_timeout(280)
    for _ in range(15):
        page4.locator("#sheet [data-act=d41SizeStep][data-d='1']").click()
    page4.wait_for_timeout(300)
    sz4 = page4.evaluate("""() => { const t = JSON.parse(document.getElementById('d41TextsIn').value)[0];
      return [t.size, Math.round(parseFloat(getComputedStyle(document.querySelector('#sheet .d41-tx')).fontSize))]; }""")
    check("− + 로 글씨 크기를 12~40 사이에서 조절", sz4[0] == 32 and sz4[1] == 32, sz4)

    # 사진 — 붙이면 자유 배치 · 모서리로 크기 · 자르기 · 끌어 옮기기
    durl4 = page4.evaluate("""() => { const c = document.createElement('canvas'); c.width = 400; c.height = 300;
      const x = c.getContext('2d'); x.fillStyle = '#C9A227'; x.fillRect(0, 0, 400, 300);
      x.fillStyle = '#3D6E8A'; x.fillRect(60, 60, 280, 180); return c.toDataURL('image/jpeg', 0.9); }""")
    with open("/workspace/tmp/v42-canvas.jpg", "wb") as f:
        f.write(_b64.b64decode(durl4.split(",", 1)[1]))
    h4_before = page4.evaluate("Math.round(document.getElementById('d41Paper').offsetHeight)")
    page4.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    page4.wait_for_timeout(200)
    page4.set_input_files("#d41ImgIn", ["/workspace/tmp/v42-canvas.jpg"])
    page4.wait_for_timeout(1500)
    ph4 = page4.evaluate("""() => { const im = JSON.parse(document.getElementById('d41ImgsIn').value)[0] || {};
      return {n: document.querySelectorAll('#sheet .d41-imgb').length, x: im.x, y: im.y, w: im.w,
              src: String(im.src || '').slice(0, 11)}; }""")
    check("사진을 붙이면 캔버스 위 사진 상자로 (자리·폭과 함께)", ph4["n"] == 1 and ph4["src"].startswith("data:")
          and 0 <= ph4["x"] <= 1 and 0 <= ph4["w"] <= 1, ph4)
    h4_after = page4.evaluate("Math.round(document.getElementById('d41Paper').offsetHeight)")
    check("내용이 늘면 모눈종이도 함께 길어짐", h4_after >= h4_before, (h4_before, h4_after))

    # 크기 조절 (모서리 손잡이)
    ib4 = page4.locator("#sheet .d41-imgb").first.bounding_box()
    page4.mouse.click(ib4["x"] + 30, ib4["y"] + 30)
    page4.wait_for_timeout(300)
    hb4 = page4.locator("#sheet .d41-imgb.sel .d41-rz").bounding_box()
    page4.mouse.move(hb4["x"] + hb4["width"] / 2, hb4["y"] + hb4["height"] / 2)
    page4.mouse.down()
    page4.mouse.move(hb4["x"] + hb4["width"] / 2 - 60, hb4["y"] + hb4["height"] / 2 - 40, steps=8)
    page4.mouse.up()
    page4.wait_for_timeout(400)
    w4 = page4.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].w")
    check("모서리를 끌어 사진 크기를 자유롭게 줄임", w4 < ph4["w"] - 0.05, (ph4["w"], w4))

    # 끌어서 옮기기
    ib5 = page4.locator("#sheet .d41-imgb").first.bounding_box()
    x4a = page4.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].x")
    page4.mouse.move(ib5["x"] + 24, ib5["y"] + 24)
    page4.mouse.down()
    page4.mouse.move(ib5["x"] + 90, ib5["y"] + 100, steps=8)
    page4.mouse.up()
    page4.wait_for_timeout(400)
    x4b = page4.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].x")
    check("사진을 손으로 끌어 자유롭게 옮김", x4b > x4a + 0.04, (x4a, x4b))

    # 자르기
    ib6 = page4.locator("#sheet .d41-imgb").first.bounding_box()
    page4.mouse.click(ib6["x"] + 26, ib6["y"] + 26)
    page4.wait_for_timeout(300)
    page4.locator("#d41Panel [data-act=d41ImgCrop]").first.click()
    page4.wait_for_timeout(500)
    crop4 = page4.evaluate("!!document.getElementById('d41CropWrap')")
    # v43: 자르기 창은 테두리(손잡이)를 끌어 영역을 정해요
    hb4 = page4.evaluate("""() => { const f = document.getElementById('d41CropFrame').getBoundingClientRect();
      const h = document.querySelector('#d41CropWrap .d41-ch-se').getBoundingClientRect();
      return [h.x + h.width / 2, h.y + h.height / 2, f.x, f.y, f.width, f.height]; }""")
    page4.mouse.move(hb4[0], hb4[1])
    page4.mouse.down()
    page4.mouse.move(hb4[2] + hb4[4] * 0.55, hb4[3] + hb4[5] * 0.55, steps=6)
    page4.mouse.up()
    page4.wait_for_timeout(260)
    nat4a = page4.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img'); return [i.naturalWidth, i.naturalHeight]; }""")
    page4.locator("#d41CropWrap [data-crop=apply]").click()
    page4.wait_for_timeout(700)
    nat4b = page4.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img'); return i ? [i.naturalWidth, i.naturalHeight] : null; }""")
    check("사진 선택 → 「자르기」 창에서 영역을 그려 적용하면 실제로 잘림",
          crop4 and nat4b and nat4a and nat4b[0] < nat4a[0], (nat4a, nat4b))

    # 펜 + 저장 → 사진·펜·글 모두 저장
    page4.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    page4.wait_for_timeout(260)
    pbox4 = page4.locator("#d41Paper").bounding_box()
    page4.mouse.move(pbox4["x"] + 60, pbox4["y"] + 420)
    page4.mouse.down()
    page4.mouse.move(pbox4["x"] + 200, pbox4["y"] + 470, steps=10)
    page4.mouse.up()
    page4.wait_for_timeout(360)
    page4.locator("#sheet .d41-back").click()
    page4.wait_for_timeout(900)
    all4 = page4.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '그림판 다이어리')[0] || {};
      const it = (l.items || [])[0] || {};
      return {texts: (it.texts || []).length, size: ((it.texts || [{}])[0] || {}).size,
              imgs: (it.imgs || []).map(i => [i.x, i.y, i.w, String(i.src || '').slice(0, 11)]),
              pen: (it.pen || []).length}; }""")
    check("글·사진·펜이 한 번에 저장됨 (글씨 크기·사진 자리·폭 포함)",
          all4["texts"] == 1 and all4["size"] == 32 and len(all4["imgs"]) == 1 and all4["imgs"][0][3].startswith("data:")
          and all4["pen"] == 1, all4)
    page4.locator("#s-diary .d41-card").first.click()
    page4.wait_for_timeout(760)
    page4.screenshot(path=os.path.join(SHOT, "note-v42-diary-canvas.png"))
    page4.keyboard.press("Escape")
    page4.wait_for_timeout(300)
    check("브라우저 콘솔/페이지 오류 없음 (모눈 캔버스)", len(errs4) == 0, errs4[:4])

    # ==================================================================
    # 9. 한 테마로 — 노트 선택 탭 · + 새 다이어리 · 저장 버튼이 테마 포인트 색
    # ==================================================================
    tab(page4, 4, 620)
    page4.locator('#s-set [data-act="openThemeManager"]').first.click()
    page4.wait_for_timeout(520)
    sw4 = page4.evaluate("""() => { const s = document.querySelector('#sheet .sw-grid[data-sw="homeTitleBg"] .sw');
      return s ? {n: document.querySelectorAll('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').length,
                  color: s.getAttribute('data-color')} : null; }""")
    check("테마 컬러 팔레트가 열림", sw4 and sw4["n"] >= 6, sw4)
    point4 = page4.evaluate("""() => { const s = document.querySelectorAll('#sheet .sw-grid[data-sw="homeTitleBg"] .sw')[2];
      return s.getAttribute('data-color'); }""")
    page4.evaluate("""() => document.querySelectorAll('#sheet .sw-grid[data-sw="homeTitleBg"] .sw')[2].click()""")
    page4.wait_for_timeout(420)
    page4.keyboard.press("Escape")
    page4.wait_for_timeout(320)
    applied4 = page4.evaluate("""() => {
      const r = document.documentElement;
      return {point: getComputedStyle(r).getPropertyValue('--point').trim().toUpperCase(),
              ink: getComputedStyle(r).getPropertyValue('--point-ink').trim()};}""")
    check("고른 테마 컬러가 --point 로 잡힘", applied4["point"] == point4.upper(), (point4, applied4))
    tab(page4, 2, 620)
    page4.locator("#s-diary .lchip", has_text="그림판 다이어리").first.click()
    page4.wait_for_timeout(560)
    themed4 = page4.evaluate("""() => {
      const rgb = (h) => { const n = parseInt(h.slice(1), 16); return 'rgb(' + ((n >> 16) & 255) + ', ' + ((n >> 8) & 255) + ', ' + (n & 255) + ')'; };
      const chip = document.querySelector('#s-diary .lchip.active');
      const nw = document.querySelector('#s-diary .d41-new');
      return {want: rgb(getComputedStyle(document.documentElement).getPropertyValue('--point').trim().toUpperCase()),
              chip: chip ? getComputedStyle(chip).backgroundColor : '',
              newBtn: nw ? getComputedStyle(nw).backgroundColor : ''};}""")
    check("노트에서 고른 카테고리 탭이 테마 컬러", themed4["chip"] == themed4["want"], themed4)
    check("「+ 새 다이어리」 버튼도 테마 컬러", themed4["newBtn"] == themed4["want"], themed4)
    page4.locator("#s-diary .d41-new").click()
    page4.wait_for_timeout(700)
    save4 = page4.evaluate("""() => {
      const p = getComputedStyle(document.documentElement).getPropertyValue('--point').trim().toUpperCase();
      const n = parseInt(p.slice(1), 16);
      return {noSave: !document.querySelector('#sheet .d41-save'),
              want: 'rgb(' + ((n >> 16) & 255) + ', ' + ((n >> 8) & 255) + ', ' + (n & 255) + ')'};}""")
    check("모눈 다이어리 「저장」 단추는 없음(나가면 자동 저장)", save4["noSave"], save4)
    page4.keyboard.press("Escape")
    page4.wait_for_timeout(320)

    # 노트 화면 위 「투두리스트」 되돌리기 버튼은 없음
    page4.locator('#s-diary [data-act="seg"][data-seg="bucket"]').first.click()
    page4.wait_for_timeout(520)
    check("노트 본문 위에 「투두리스트」 되돌리기 버튼이 없음",
          page4.evaluate("!document.querySelector('#s-diary .nh-back')"))

    # ==================================================================
    # 10. 투두리스트 카드 미리보기 5개 + 「+1개 더」
    # ==================================================================
    page4.evaluate("""() => {
      const s = window.__app.state;
      const l = s.lists.filter(x => x.title === '그림판 다이어리')[0];
      l.kind = 'check';
      l.items = [1, 2, 3, 4, 5, 6].map((n, i) => ({id: 'c42' + n, text: '할 일 ' + n, memo: '', done: false, gid: 'G42'}));
      s.groups['list:' + l.id] = [{id: 'G42', title: '여섯 개 카드', caption: '', who: 'me', date: '2026-11-21'}];
      window.__app.rerender();
    }""")
    page4.wait_for_timeout(500)
    page4.locator("#s-diary .lchip", has_text="그림판 다이어리").first.click()
    page4.wait_for_timeout(560)
    prev4 = page4.evaluate("""() => {
      const c = [...document.querySelectorAll('#s-diary .ncard')].filter(x => (x.textContent || '').indexOf('여섯 개 카드') >= 0)[0];
      if (!c) return null;
      return {items: c.querySelectorAll('.nc-items .cti').length,
              more: (c.querySelector('.nc-items .nc-more') || {}).textContent || ''};}""")
    check("카드에는 항목이 5개까지 보이고 「+1개 더」", prev4 and prev4["items"] == 5 and "1개 더" in prev4["more"], prev4)
    check("브라우저 콘솔/페이지 오류 없음 (테마·카드)", len(errs4) == 0, errs4[:4])
    ctx4.close()

    # ==================================================================
    # 11. Supabase 왕복 — 자유 배치 글(texts)이 서버로 갔다가 그대로 돌아옴
    # ==================================================================
    cid5, uid5, mail5 = "couple-v42", "user-v42", "v42@twolog.app"
    db5 = {
        "users": {uid5: {"id": uid5, "email": mail5, "password": "pw123456"}},
        "couples": [{"id": cid5, "invite_code": "482942", "members": [uid5],
                     "me": "소영", "you": "준영", "since": "2025-11-21", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "photos": [],
        "notes": [{"id": "L42", "couple_id": cid5, "kind": "list", "sort": 0, "deleted": False,
                   "payload": {"title": "캔버스 일기", "emoji": "", "kind": "memo", "items": []}}],
        "settings": [{"couple_id": cid5, "key": "note_meta",
                      "value": {"tabs": {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"},
                                         "log": {"e": "", "n": "영화·먹방"}},
                                "order": ["todo", "bucket", "log", "list:L42"], "kinds": {}}}],
        "uploads": [], "seq": 42,
    }
    seed5 = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({access_token: 't', refresh_token: 'r',
        user: {id: %s, email: %s}}));
    })();""" % (json.dumps(json.dumps(db5, ensure_ascii=False)), json.dumps(uid5), json.dumps(mail5))
    ctx5 = new_ctx(browser)
    ctx5.add_init_script(seed5)
    page5 = ctx5.new_page()
    errs5 = []
    watch(page5, errs5)
    stub_route(page5)
    page5.goto(URL, wait_until="domcontentloaded")
    page5.wait_for_selector("#tabbar .tab", timeout=25000)
    page5.wait_for_timeout(2800)
    tab(page5, 2, 700)
    page5.locator("#s-diary .lchip", has_text="캔버스 일기").first.click()
    page5.wait_for_timeout(640)
    page5.locator("#s-diary .d41-new").click()
    page5.wait_for_timeout(760)
    pb5 = page5.locator("#d41Paper").bounding_box()
    page5.mouse.click(pb5["x"] + 70, pb5["y"] + 160)
    page5.wait_for_timeout(320)
    page5.keyboard.type("두 폰에서 같이 보이는 글")
    page5.wait_for_timeout(240)
    page5.locator("#sheet .d41-back").click()
    page5.wait_for_timeout(2400)
    srv5 = page5.evaluate("""() => { const row = (window.__stub.notes || []).filter(x => x.kind === 'list')[0];
      const it = row ? (row.payload.items || [])[0] : null;
      return it ? {texts: (it.texts || []), memo: it.memo || ''} : null; }""")
    check("자유 배치 글(texts)이 notes payload 에 좌표와 함께 올라감",
          srv5 and len(srv5["texts"]) == 1 and "두 폰에서" in srv5["texts"][0]["text"]
          and 0 <= srv5["texts"][0]["x"] <= 1 and srv5["texts"][0]["size"] > 0, srv5)
    page5.reload(wait_until="domcontentloaded")
    page5.wait_for_selector("#tabbar .tab", timeout=25000)
    page5.wait_for_timeout(2600)
    tab(page5, 2, 700)
    page5.locator("#s-diary .lchip", has_text="캔버스 일기").first.click()
    page5.wait_for_timeout(640)
    back5 = page5.evaluate("""() => { const l = (window.__app.state.lists || []).filter(x => x.title === '캔버스 일기')[0] || {};
      const it = (l.items || [])[0] || {};
      return {texts: (it.texts || []).length, text: (((it.texts || [])[0] || {}).text || '')}; }""")
    check("서버에서 돌아온 글도 그대로 (새로고침 후)", back5["texts"] == 1 and "두 폰에서" in back5["text"], back5)
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errs5) == 0, errs5[:4])
    ctx5.close()

    browser.close()

print()
if fails:
    print("실패 %d개:" % len(fails))
    for f in fails:
        print("  -", f)
    sys.exit(1)
print("실패: 없음")
