"""투로그 v28 확인 — 캘린더는 열 때 이번 달 · 일정 시트 날짜+요일 · 하단 일정 수정 · 노트 + 탭 추가.

1) 버전: sw.js 캐시 twolog-v42 · APP_VERSION v42
2) 앱을 새로 켜면(새로고침) 저장해 둔 지난달 대신 이번 달로
3) 탭에서 캘린더로 들어오면 이번 달 + 오늘 날짜 (다른 달 → 다른 탭 → 돌아오면 이번 달)
4) 달 안에서 화살표·손가락 밀기로 넘기는 이동은 그대로 (그 달에 머무는 동안 유지)
5) 해가 다른 달(2027년)에서 돌아오면 연도 표시도 사라지고 이번 달
6) 일정 검색 결과로 다른 달에 갈 때는 그 달을 지킴(keepCal)
7) 사진첩 달력 보기를 새로 열면 이번 달
8) 일정 시트: 시간 설정 없음 · 날짜(19px) 위/요일(13px) 아래 · 물결 간격 좁게 ·
   함께/소영/준영 글씨 12.5px
9) 하단 상세 일정: 이름 13.5px, 줄을 누르면 수정 시트(컬러·제목·날짜·누구와 채워짐) → 저장 반영
10) 한 날 일정 3개 이상: 막대 2줄 + 「+1」
11) 노트: 알약 탭 줄 오른쪽의 동그란 + 로 새 카테고리 탭 추가 · 그 안에 항목 추가
12) 원격(Supabase 스텁) 동기화: 새 탭과 항목이 상대 폰에도 뜨고, 상대가 넣은 항목도 이 폰에
13) 페이지 오류 없음

    python3 tests/v28.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import base64, functools, http.server, json, os, re, socketserver, sys, tempfile, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

STUB = open(os.path.join(HERE, "stub-supabase.js")).read()
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
TODAY = time.strftime("%Y-%m-%d")
THIS_MONTH = time.strftime("%Y-%m")
THIS_LABEL = time.strftime("%-m월")
THIS_YEAR = time.strftime("%Y")
TODAY_LONG = time.strftime("%Y년 %-m월 %-d일")
DOW_NAMES = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]


def new_ctx(browser, **kw):
    args = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                device_scale_factor=2)
    args.update(kw)
    return browser.new_context(**args)


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def stub(page, table):
    return page.evaluate("(t) => (window.__stub && window.__stub[t]) ? window.__stub[t] : []", table)


def signup(page, email, pw):
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', email)
    page.fill('#s-login input[name="password"]', pw)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)


def cal_state(page):
    return page.evaluate("""() => {
      const S = window.__app.state || {};
      const ui = S.ui || {};
      const mon = document.querySelector('#s-cal .cal-month');
      const yr = document.querySelector('#s-cal .cal-year');
      const hd = document.querySelector('#s-cal .daypanel-hd .d');
      return {calMonth: ui.calMonth || null, selDate: ui.selDate || null,
              label: mon ? mon.textContent.trim() : null,
              year: yr ? yr.textContent.trim() : null,
              day: hd ? hd.textContent.trim() : null,
              stored: (() => { try { const r = localStorage.getItem('twolog:v1:ui');
                return r ? (JSON.parse(r).calMonth || null) : null; } catch (e) { return null; } })()};
    }""")


def open_app(page):
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(700)
    page.wait_for_selector("#tabbar .tab", timeout=20000)


def tab(page, idx, wait=500):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def note_state(page):
    return page.evaluate("""() => {
      const S = window.__app.state;
      const seg = (S.ui || {}).seg;
      const cur = String(seg || '').indexOf('list:') === 0 ? (S.lists || []).filter(l => l.id === seg.slice(5))[0] : null;
      return {seg, lists: (S.lists || []).map(l => ({id: l.id, title: l.title, emoji: l.emoji, kind: l.kind,
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
    check("sw.js 캐시 버전 twolog-v42", 'const VERSION = "twolog-v42"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v42", 'var APP_VERSION = "v42"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v42", 'const SHELL = "shell-" + VERSION' in sw)

    # ==================================================================
    # 2. 앱을 새로 켜면 이번 달 (저장된 지난달은 무시)
    # ==================================================================
    open_app(page)
    st0 = cal_state(page)
    check("처음 켤 때 화면 상태가 이번 달", st0["calMonth"] == THIS_MONTH, st0)

    page.evaluate("""() => {
      const S = window.__app.state;
      S.ui.calMonth = '2027-03'; S.ui.selDate = '2027-03-05';
      window.TwoLogStore.persist(S);
    }""")
    page.wait_for_timeout(350)
    stale = page.evaluate("""() => { try { const r = localStorage.getItem('twolog:v1:ui');
      return r ? {calMonth: JSON.parse(r).calMonth, selDate: JSON.parse(r).selDate} : null; }
      catch (e) { return null; } }""")
    check("지난달(2027-03)이 폰에 저장된 상태를 만듦", bool(stale) and stale["calMonth"] == "2027-03", stale)

    open_app(page)
    st1 = cal_state(page)
    check("앱을 다시 켜면 이번 달로 (지난달 무시)", st1["calMonth"] == THIS_MONTH, st1)
    check("다시 켤 때 선택 날짜도 오늘", st1["selDate"] == TODAY, st1)

    tab(page, 1)
    st2 = cal_state(page)
    check("캘린더 탭을 열면 이번 달 제목", st2["label"] == THIS_LABEL, st2)
    check("이번 해는 연도 표시 없음", st2["year"] is None, st2)
    check("아래 선택한 날은 오늘", st2["day"] == TODAY_LONG, st2)
    page.screenshot(path=os.path.join(SHOT, "cal-v28-open.png"))

    # ==================================================================
    # 3. 다른 달 → 다른 탭 → 캘린더 다시: 이번 달
    # ==================================================================
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(450)
    hov = page.evaluate("""() => {
      const s = window.__app.state;
      return {y: Number(s.ui.calMonth.slice(0, 4)), m: Number(s.ui.calMonth.slice(5, 7))};
    }""")
    check("화살표로 넘어간 달이 이번 달과 다름", "%04d-%02d" % (hov["y"], hov["m"]) != THIS_MONTH, hov)

    tab(page, 0)                      # 홈
    tab(page, 3)                      # 사진첩
    tab(page, 1)                      # 다시 캘린더
    st4 = cal_state(page)
    check("다른 탭에 갔다 돌아오면 다시 이번 달", st4["calMonth"] == THIS_MONTH, st4)
    check("돌아오면 «이번 달» 제목", st4["label"] == THIS_LABEL, st4)
    check("돌아오면 선택 날짜도 오늘", st4["day"] == TODAY_LONG, st4)

    # ==================================================================
    # 4. 달 안에서의 이동은 그대로 (화살표 · 손가락 밀기)
    # ==================================================================
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(400)
    a1 = cal_state(page)
    check("달 안에서 화살표로 넘긴 달은 그대로 유지", a1["calMonth"] != THIS_MONTH, a1)

    cdp = ctx.new_cdp_session(page)

    def swipe(x1, y1, x2, y2, steps=8):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x1, "y": y1}]})
        for i in range(1, steps + 1):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [
                {"x": x1 + (x2 - x1) * i / steps, "y": y1 + (y2 - y1) * i / steps}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(600)

    before = cal_state(page)["calMonth"]
    swipe(330, 260, 60, 268)          # 왼쪽으로 밀기 → 다음 달
    after = cal_state(page)["calMonth"]
    check("손가락으로 밀어도 다음 달로 (그 달에 머무름)", after != before, (before, after))
    swipe(60, 260, 330, 268)          # 오른쪽으로 밀기 → 이전 달
    back = cal_state(page)["calMonth"]
    check("반대로 밀면 이전 달로 되돌아옴", back == before, (before, back))
    check("밀어서 넘긴 뒤에도 캘린더 탭에 그대로", page.evaluate(
        "() => document.querySelector('#tabbar .tab.active').textContent.trim()") == "캘린더")

    # ==================================================================
    # 5. 해가 다른 달에서 돌아오면 연도 표시도 사라지고 이번 달
    # ==================================================================
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(400)
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(500)
    far = cal_state(page)
    check("해가 바뀐 달(2027년)로 이동", far["calMonth"][:4] != THIS_YEAR and far["year"] == far["calMonth"][:4], far)
    tab(page, 4)                      # My
    tab(page, 1)                      # 캘린더
    ret = cal_state(page)
    check("해가 다른 달에서 돌아오면 이번 달", ret["calMonth"] == THIS_MONTH and ret["label"] == THIS_LABEL, ret)
    check("연도 표시도 사라짐", ret["year"] is None, ret)

    # ==================================================================
    # 6. 일정 검색 결과로 다른 달에 갈 때는 그 달을 지킴
    # ==================================================================
    nx = page.evaluate("""() => {
      const S = window.__app.state;
      const d = new Date(); const y = d.getFullYear(), m = d.getMonth() + 1;
      const t = new Date(y, m + 1, 25);
      const pad = (n) => (n < 10 ? '0' + n : '' + n);
      const ds = t.getFullYear() + '-' + pad(t.getMonth() + 1) + '-25';
      S.events.push({id: 'v28x', date: ds, endDate: ds, time: '', title: 'v28 다음 달 약속',
        type: 'etc', memo: '', who: 'both', color: ''});
      window.__app.rerender();
      window.TwoLogStore.flush();
      return {ds: ds, y: t.getFullYear(), m: t.getMonth() + 1};
    }""")
    page.wait_for_timeout(500)
    page.locator('#s-cal [data-act="calSearch"]').click()
    page.wait_for_timeout(400)
    page.fill("#calSearchIn", "v28 다음 달")
    page.wait_for_timeout(500)
    page.locator("#sheet .sres").first.click()
    page.wait_for_timeout(700)
    jump = cal_state(page)
    check("검색 결과를 누르면 그 일정이 있는 달로 이동", jump["calMonth"] == nx["ds"][:7], (jump, nx))
    check("그 달 제목이 보임", jump["label"] == str(nx["m"]) + "월", (jump["label"], nx))
    check("그 날짜가 선택됨", jump["selDate"] == nx["ds"], (jump["selDate"], nx["ds"]))
    check("검색 시트는 닫힘", not page.evaluate(
        "() => document.getElementById('sheetWrap').classList.contains('open')"))
    page.screenshot(path=os.path.join(SHOT, "cal-v28-search-jump.png"))

    tab(page, 0)
    tab(page, 1)
    again = cal_state(page)
    check("검색으로 간 달도 탭을 나갔다 오면 이번 달", again["calMonth"] == THIS_MONTH, again)

    # ==================================================================
    # 7. 사진첩 달력 보기도 새로 열면 이번 달
    # ==================================================================
    tab(page, 3, 600)
    if page.evaluate("() => !!(window.__app.state.ui || {}).photoCal"):
        page.locator('#s-photo [data-act="togglePhotoCal"]').click()
        page.wait_for_timeout(400)
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(600)
    pcal = page.evaluate("""() => {
      /* v39: 앞뒤 12개월이 이어져 첫 달이 이번 달이 아니므로 «이번 달 블록»을 봅니다 */
      const d = new Date();
      const ym = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      const el = document.querySelector('#s-photo .pcal-m[data-ym="' + ym + '"] .pcal-ym');
      return {ym: el ? el.textContent.trim() : null,
              month: (window.__app.state.ui || {}).photoMonth || null,
              grid: !!document.querySelector('#s-photo .pcal-grid')};
    }""")
    check("사진첩 달력 보기를 열면 이번 달",
          pcal["grid"] and pcal["ym"] == time.strftime("%Y년 ") + str(int(time.strftime("%m"))) + "월", pcal)
    # v38: 달력은 세로로 이어진 달력 — 이번 달이 가운데쯤 오도록 스크롤돼 열림
    stacked = page.evaluate("""() => { const ms = [...document.querySelectorAll('#s-photo .pcal-m')];
      const box = document.getElementById('screens');
      const cur = document.querySelector('#s-photo .pcal-m[data-ym="%s"]');
      const r = cur ? cur.getBoundingClientRect() : null, b = box.getBoundingClientRect();
      return {months: ms.length, above: ms.filter(m => m.getAttribute('data-ym') < '%s').length,
              top: r ? Math.round(r.top - b.top) : null, h: Math.round(b.height),
              nav: document.querySelectorAll('#s-photo .pcal-nav').length}; }""" % (time.strftime("%Y-%m"), time.strftime("%Y-%m")))
    check("사진첩 달력도 여러 달이 이어지고 이번 달이 가운데쯤",
          stacked["months"] >= 2 and stacked["nav"] == 0 and stacked["top"] is not None
          and stacked["top"] <= stacked["h"] * 0.62
          and (stacked["above"] == 0 or stacked["top"] >= stacked["h"] * 0.18), stacked)
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(400)
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(600)
    reopen = page.evaluate("""() => { const d = new Date();
      const ym = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0');
      const el = document.querySelector('#s-photo .pcal-m[data-ym="' + ym + '"] .pcal-ym');
      return el ? el.textContent.trim() : null; }""")
    check("사진첩 달력을 다시 열면 이번 달", reopen == pcal["ym"], (pcal["ym"], reopen))
    page.screenshot(path=os.path.join(SHOT, "photo-cal-v28.png"))

    # ==================================================================
    # 8. 일정 추가 시트 — 시간 없음 · 날짜/요일 크게 · 물결 간격 · 누구와 글씨
    # ==================================================================
    tab(page, 1)
    page.wait_for_timeout(400)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(700)
    ef = page.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const g = s => sh.querySelector(s);
      const box = e => { const r = e.getBoundingClientRect(); return {x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}; };
      const big0 = g('.ev-dbig[data-dbig="start"]'), big1 = g('.ev-dbig[data-dbig="end"]');
      const dow0 = g('.ev-dow[data-dow="start"]'), dow1 = g('.ev-dow[data-dow="end"]');
      const til = g('.ev-tilde');
      const i0 = g('.js-evdate[data-side="start"]');
      const names = ['일요일','월요일','화요일','수요일','목요일','금요일','토요일'];
      const d0 = new Date(i0.value + 'T00:00:00');
      return {head: g('.sheet-hd h2').textContent.trim(),
              times: sh.querySelectorAll('.ev-time-btn, .ev-time-in, input[name="startTime"]').length,
              big0: box(big0), big1: box(big1), bigFs: getComputedStyle(big0).fontSize,
              bigTxt: big0.textContent.trim(),
              dow0: box(dow0), dow1: box(dow1), dowFs: getComputedStyle(dow0).fontSize,
              dowTxt: dow0.textContent.trim(), want: names[d0.getDay()],
              tilde: box(til), tildeFs: getComputedStyle(til).fontSize,
              when: box(g('.ev-when')),
              gapL: Math.round(big0.getBoundingClientRect().right ? til.getBoundingClientRect().left - big0.getBoundingClientRect().right : -1),
              gapR: Math.round(big1.getBoundingClientRect().left - til.getBoundingClientRect().right),
              wopt: Array.from(sh.querySelectorAll('.wopt')).map(e => ({t: e.textContent.trim(),
                fs: getComputedStyle(e).fontSize})),
              dateIn: !!g('.js-evdate[data-side="start"]')};
    }""")
    check("일정 시트 열림 (제목 일정 추가)", ef["head"] == "일정 추가", ef["head"])
    check("시간 설정 칸·버튼이 사라짐", ef["times"] == 0, ef["times"])
    check("날짜 글씨 19px", ef["bigFs"] == "19px", ef["bigFs"])
    check("요일 글씨 13px", ef["dowFs"] == "13px", ef["dowFs"])
    check("요일이 날짜 아래 (전체 이름)", ef["dowTxt"] == ef["want"] and ef["dow0"]["y"] > ef["big0"]["y"],
          (ef["dowTxt"], ef["want"], ef["big0"]["y"], ef["dow0"]["y"]))
    check("날짜는 26.11.17 형식", re.match(r"^\d{2}\.\d{2}\.\d{2}$", ef["bigTxt"]) is not None, ef["bigTxt"])
    check("물결(~)이 날짜 사이 가로 가운데",
          abs((ef["tilde"]["x"] + ef["tilde"]["w"] / 2) - ((ef["big0"]["x"] + ef["big0"]["w"] + ef["big1"]["x"]) / 2)) <= 3,
          (ef["tilde"]["x"], ef["big0"]["x"], ef["big0"]["w"], ef["big1"]["x"]))
    check("물결과 날짜 사이 간격이 좁음(6px 이하)", ef["gapL"] <= 6 and ef["gapR"] <= 6, (ef["gapL"], ef["gapR"]))
    check("함께·소영·준영 글씨 12.5px",
          [w["fs"] for w in ef["wopt"]] == ["12.5px", "12.5px", "12.5px"], ef["wopt"])
    check("날짜 고르는 입력칸은 그대로", ef["dateIn"])
    page.screenshot(path=os.path.join(SHOT, "event-sheet-v28.png"))

    # 저장 → 하단 상세 일정에 나오기
    page.fill('#sheet .ev-title', "친구 만나기")
    page.locator('#sheet .wopt[data-who="me"]').click()
    page.wait_for_timeout(200)
    page.locator('#sheet .sw-row .sw').nth(2).click()
    page.wait_for_timeout(200)
    page.locator("#evSave").click()
    page.wait_for_timeout(900)
    saved = page.evaluate("""() => {
      const e = (window.__app.state.events || []).filter(x => x.title === '친구 만나기')[0] || {};
      return {n: (window.__app.state.events || []).filter(x => x.title === '친구 만나기').length,
              time: e.time || '', who: e.who, color: e.color || '', date: e.date};
    }""")
    check("일정이 시간 없이 저장됨", saved["n"] == 1 and saved["time"] == "" and saved["date"] == TODAY, saved)

    # ==================================================================
    # 9. 하단 상세 일정 — 이름 13.5px · 줄을 누르면 수정 시트
    # ==================================================================
    dp = page.evaluate("""() => {
      const rows = Array.from(document.querySelectorAll('#s-cal .daylist .ev'));
      const row = rows.filter(r => r.innerText.indexOf('친구 만나기') >= 0)[0];
      const w = row ? row.querySelector('.wname') : null;
      const t = row ? row.querySelector('.t') : null;
      return {n: rows.length, act: row ? row.getAttribute('data-act') : null,
              wname: w ? w.textContent.trim() : null, wnameFs: w ? getComputedStyle(w).fontSize : null,
              titleFs: t ? getComputedStyle(t).fontSize : null,
              xInside: row ? !!row.querySelector('button.x[data-act="delEvent"]') : false};
    }""")
    check("하단 일정 줄 이름 글씨 13.5px", dp["wname"] == "소영" and dp["wnameFs"] == "13.5px",
          (dp["wname"], dp["wnameFs"]))
    check("하단 일정 줄이 누를 수 있는 줄(editEvent)", dp["act"] == "editEvent", dp["act"])
    check("줄 안에 삭제 × 는 그대로", dp["xInside"])

    page.locator("#s-cal .daylist .ev .t", has_text="친구 만나기").first.click()
    page.wait_for_timeout(700)
    ed = page.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const g = s => sh.querySelector(s);
      const color = g('input[name="color"]');
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
              head: g('.sheet-hd h2').textContent.trim(),
              title: g('.ev-title').value,
              bigs: Array.from(sh.querySelectorAll('.ev-dbig')).map(e => e.textContent.trim()),
              dows: Array.from(sh.querySelectorAll('.ev-dow')).map(e => e.textContent.trim()),
              who: (g('.wopt.active') || {}).textContent,
              color: color ? color.value : null,
              swSel: Array.from(sh.querySelectorAll('.sw-row .sw')).filter(x => x.classList.contains('sel')).length,
              times: sh.querySelectorAll('.ev-time-btn, .ev-time-in').length,
              evId: g('input[name="evId"]').value};
    }""")
    check("일정 줄을 누르면 수정 시트가 열림", ed["open"] and ed["head"] == "일정 저장", (ed["open"], ed["head"]))
    check("수정 시트에 제목이 채워짐", ed["title"] == "친구 만나기", ed["title"])
    want_dow = DOW_NAMES[(time.strptime(TODAY, "%Y-%m-%d").tm_wday + 1) % 7]
    check("수정 시트에 날짜·요일이 채워짐",
          ed["bigs"] == [TODAY.replace("-", ".")[2:]] * 2 and ed["dows"] == [want_dow] * 2,
          (ed["bigs"], ed["dows"], want_dow))
    check("수정 시트에 고른 컬러·누구와가 채워짐", ed["who"] == "소영" and ed["swSel"] == 1, (ed["who"], ed["swSel"]))
    check("수정 시트에도 시간 설정 없음", ed["times"] == 0, ed["times"])
    page.screenshot(path=os.path.join(SHOT, "event-edit-v28.png"))

    page.fill('#sheet .ev-title', "친구 만나기 (저녁 7시)")
    page.locator('#sheet .sw-row .sw').nth(5).click()
    page.wait_for_timeout(200)
    page.locator('#sheet .btn-primary').click()
    page.wait_for_timeout(900)
    ed2 = page.evaluate("""() => {
      const e = (window.__app.state.events || []).filter(x => x.id === %s)[0] || {};
      const rows = Array.from(document.querySelectorAll('#s-cal .daylist .ev'));
      return {n: (window.__app.state.events || []).length, title: e.title, color: e.color || '',
              who: e.who, time: e.time || '',
              shown: rows.some(r => r.innerText.indexOf('친구 만나기 (저녁 7시)') >= 0),
              toast: (document.getElementById('toast') || {}).textContent || ''};
    }""" % json.dumps(ed["evId"]))
    check("수정한 제목이 저장됨", ed2["title"] == "친구 만나기 (저녁 7시)" and ed2["n"] == 2, ed2)
    check("수정한 컬러가 저장됨", ed2["color"] != "", ed2)
    check("고친 일정이 하단 목록에 보임", ed2["shown"], ed2["shown"])
    check("저장 안내 토스트", "저장" in ed2["toast"], ed2["toast"])

    # ==================================================================
    # 10. 한 날 일정 3개 이상 → 막대 2줄 + 「+1」
    # ==================================================================
    page.evaluate("""() => {
      const S = window.__app.state; const t = S.ui.selDate;
      ['덤 하나', '덤 둘'].forEach((n, i) => S.events.push({id: 'v28d' + i, date: t, endDate: t,
        time: '', title: n, type: 'etc', memo: '', who: 'me', color: ''}));
      window.__app.rerender(); window.TwoLogStore.flush();
    }""")
    page.wait_for_timeout(800)
    ov = page.evaluate("""() => {
      const cell = document.querySelector('#s-cal .day[data-date="%s"]');
      const row = cell.closest('.cal-row');
      const cr = cell.getBoundingClientRect();
      const bars = Array.from(row.querySelectorAll('.ebar')).filter(b => {
        const r = b.getBoundingClientRect(); return r.left < cr.right - 1 && r.right > cr.left + 1; });
      const o = cell.querySelector('.dovf');
      const orr = o ? o.getBoundingClientRect() : null;
      const lastBar = bars.length ? Math.max.apply(null, bars.map(b => b.getBoundingClientRect().bottom)) : 0;
      const rr = row.getBoundingClientRect();
      return {bars: bars.map(b => b.textContent.trim()), ovf: o ? o.textContent.trim() : null,
              gap: orr ? Math.round(orr.top - lastBar) : null,
              inRow: orr ? orr.bottom <= rr.bottom + 0.5 : null,
              rowH: Math.round(rr.height)};
    }""" % TODAY)
    check("일정 3개인 날은 막대가 두 줄만", len(ov["bars"]) == 2, ov["bars"])
    check("넘치는 일정은 「+1」로 표기", ov["ovf"] == "+1", ov["ovf"])
    check("「+1」이 막대 아래에 붙지 않고 보임(6px 이상)", ov["gap"] is not None and ov["gap"] >= 6, ov["gap"])
    check("「+1」이 주 칸 안에 들어옴", ov["inRow"] is True, ov)
    page.screenshot(path=os.path.join(SHOT, "cal-v28-plus1.png"))

    # ==================================================================
    # 11. 노트 — 알약 탭 줄 오른쪽의 동그란 + 로 새 카테고리 탭 추가
    # ==================================================================
    tab(page, 2, 600)
    nb = page.evaluate("""() => {
      const segs = document.querySelector('#s-diary .segs').getBoundingClientRect();
      const btn = document.querySelector('#s-diary .note-add');
      if (!btn) return {ok: false};
      const r = btn.getBoundingClientRect();
      const cs = getComputedStyle(btn);
      const h1 = document.querySelector('#s-diary .note-h1').getBoundingClientRect();
      return {ok: true, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height),
              radius: cs.borderTopLeftRadius, border: cs.borderTopStyle,
              right: Math.round(window.innerWidth - r.right),
              abovePills: r.bottom <= segs.top + 1,
              sameRow: Math.abs((r.top + r.height / 2) - (h1.top + h1.height / 2)) <= 12,
              gear: !!document.querySelector("#s-diary [data-act='noteSettings']"),
              svg: !!btn.querySelector('svg'),
              act: btn.getAttribute('data-act'),
              label: btn.getAttribute('aria-label'),
              pillsTrunc: Array.from(document.querySelectorAll('#s-diary .segs .seg-btn'))
                .some(e => e.scrollWidth > e.clientWidth + 1)};
    }""")
    check("노트에 + 버튼이 있음", nb["ok"] and nb["act"] == "newList", nb)
    # v37: 동그란 점선 테두리를 걷어내고 ＋ 아이콘만
    check("+ 버튼은 테두리·동그라미 없이 (v37)", nb["radius"] in ("0px", "0") and nb["border"] in ("none", ""),
          (nb["radius"], nb["border"]))
    # v29: + 는 알약 탭 아래가 아니라 맨 윗줄(📖 노트) 오른쪽 — 예전 네모 설정 버튼 자리
    # v37: 터치 영역을 44px로 넓히며 바깥 상자 오른쪽 끝이 17px (＋ 아이콘은 28px)
    check("+ 버튼은 알약 탭 위 맨 윗줄 오른쪽", nb["abovePills"] and nb["sameRow"] and abs(nb["right"] - 17) <= 1,
          (nb["abovePills"], nb["sameRow"], nb["right"]))
    check("네모 설정 버튼은 사라짐", nb["gear"] is False, nb["gear"])
    check("+ 버튼 아이콘은 목록+ 모양", nb["svg"])
    check("알약 탭 글씨는 잘리지 않음", not nb["pillsTrunc"])

    page.locator("#s-diary .note-add").click()
    page.wait_for_timeout(600)
    sheet = page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      head: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent})""")
    # v33: + 시트는 「새 카테고리」 — 이모지 고르는 줄이 없어졌어요
    check("+ 를 누르면 새 카테고리 시트가 열림", sheet["open"] and sheet["head"] == "새 카테고리", sheet)

    page.fill('#sheet input[name="title"]', "장보기")
    page.locator('#sheet .btn-primary').click()
    page.wait_for_timeout(800)
    ns = note_state(page)
    check("새 카테고리 탭이 만들어짐", [l["title"] for l in ns["lists"]] == ["장보기"], ns["lists"])
    check("새 탭 칩이 바로 열림", ns["chips"] == ["장보기"] and ns["cur"] == "장보기", (ns["chips"], ns["cur"]))
    # v40: 새 카테고리의 「투두리스트」는 2열 카드 묶음 — 카드를 만들고 그 안에 항목을 넣어요
    check("새 탭 화면은 2열 카드 묶음 (v40)", "새 리스트" in ns["body"], ns["body"][:80])
    page.locator("#s-diary .ngrid .ncard.new").click()
    page.wait_for_timeout(480)
    page.fill("#sheet input[name=title]", "장보기 목록")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(620)
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
    page.screenshot(path=os.path.join(SHOT, "note-v28-newtab.png"))

    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:4])
    ctx.close()

    # ==================================================================
    # 12. 원격 동기화 — 새 카테고리 탭·항목이 상대 폰에도
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs_a = []
    page.on("pageerror", lambda e: errs_a.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs_a.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "cat.a@twolog.app", "twolog1234")
    page.wait_for_timeout(2000)

    tab(page, 2, 600)
    page.locator("#s-diary .note-add").click()
    page.wait_for_timeout(500)
    page.fill('#sheet input[name="title"]', "여행 준비")
    page.locator('#sheet .btn-primary').click()
    page.wait_for_timeout(800)
    # v40: 카드를 하나 만들고 그 안에 항목을 넣어요
    page.locator("#s-diary .ngrid .ncard.new").click()
    page.wait_for_timeout(460)
    page.fill("#sheet input[name=title]", "준비물")
    page.locator("#sheet button.btn-primary").click()
    page.wait_for_timeout(600)
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.click()
    page.wait_for_timeout(500)
    page.fill('#sheet #listAddForm input[name="text"]', "여권 챙기기")
    page.locator('#sheet #listAddForm button').click()
    page.wait_for_timeout(600)
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)
    page.wait_for_timeout(600)
    page.evaluate("() => window.TwoLogStore.flush()")
    page.wait_for_timeout(1200)

    cid = page.evaluate("() => window.TwoLogStore.coupleId")
    rows = stub(page, "notes")
    list_rows = [r for r in rows if r.get("kind") == "list"]
    check("서버(notes)에 새 카테고리 행이 올라감",
          len(list_rows) == 1 and list_rows[0]["payload"].get("title") == "여행 준비", list_rows)
    check("그 행에 항목도 함께 저장됨",
          [i.get("text") for i in (list_rows[0]["payload"].get("items") or [])] == ["여권 챙기기"],
          list_rows[0]["payload"].get("items") if list_rows else None)

    db = page.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")
    a_user = db["couples"][0]["members"][0]
    db["users"]["user-b"] = {"id": "user-b", "email": "partner.cat@twolog.app", "password": "twolog1234"}
    db["couples"][0]["members"] = [a_user, "user-b"]
    seed_b = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-b', email: 'partner.cat@twolog.app' } }));
    })();""" % json.dumps(json.dumps(db, ensure_ascii=False))

    ctx_b = new_ctx(browser)
    ctx_b.add_init_script(seed_b)
    page_b = ctx_b.new_page()
    errs_b = []
    page_b.on("pageerror", lambda e: errs_b.append("pageerror: " + str(e)))
    page_b.on("console", lambda m: errs_b.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page_b)
    page_b.goto(URL, wait_until="domcontentloaded")
    page_b.wait_for_selector("#tabbar .tab", timeout=25000)
    page_b.wait_for_timeout(2500)

    tab(page_b, 2, 700)
    nb_b = note_state(page_b)
    check("상대 폰에 새 카테고리 탭이 함께 뜸", [l["title"] for l in nb_b["lists"]] == ["여행 준비"], nb_b["lists"])
    check("상대 폰 칩에도 보임", nb_b["chips"] == ["여행 준비"], nb_b["chips"])
    page_b.locator("#s-diary .lchip").first.click()
    page_b.wait_for_timeout(600)
    nb_b2 = note_state(page_b)
    check("상대 폰에서 탭을 열면 항목이 보임",
          nb_b2["cur"] == "여행 준비" and "여권 챙기기" in nb_b2["body"], (nb_b2["cur"], nb_b2["body"][:60]))

    page_b.locator("#s-diary .ngrid .ncard:not(.new)").first.click()
    page_b.wait_for_timeout(500)
    page_b.fill('#sheet #listAddForm input[name="text"]', "충전기 챙기기")
    page_b.locator('#sheet #listAddForm button').click()
    page_b.wait_for_timeout(1000)
    page_b.keyboard.press("Escape")
    page_b.wait_for_timeout(400)
    page_b.evaluate("() => window.TwoLogStore.flush()")
    page_b.wait_for_timeout(1200)
    b_items = note_state(page_b)["lists"][0]["items"]
    check("상대 폰에서 그 탭에 항목을 더 넣을 수 있음", b_items == ["여권 챙기기", "충전기 챙기기"], b_items)

    # 상대가 저장한 서버 상태를 이 폰에도 반영(같은 서버를 보는 상황) 뒤 Realtime 다시 읽기
    b_db = page_b.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")
    # 이 폰이 보는 «서버» 상태를 상대가 저장한 상태로 맞춘 뒤 Realtime 신호
    page.evaluate("""(db) => {
      const st = window.__stub;
      ['users', 'couples', 'events', 'notes', 'photos', 'settings', 'uploads'].forEach(k => {
        if (k in db) st[k] = db[k];
      });
      try { localStorage.setItem('stub-sb-db', JSON.stringify(st)); } catch (e) {}
    }""", b_db)
    page.evaluate("(c) => window.__stubEmit('notes', c)", cid)
    page.wait_for_timeout(2500)
    a_items = note_state(page)["lists"][0]["items"] if note_state(page)["lists"] else []
    check("상대가 넣은 항목이 이 폰에도 (Realtime)", a_items == ["여권 챙기기", "충전기 챙기기"], a_items)
    page.screenshot(path=os.path.join(SHOT, "note-v28-sync-partner.png"))
    check("동기화 중 오류 없음", len(errs_a) == 0 and len(errs_b) == 0, (errs_a[:3], errs_b[:3]))
    ctx_b.close()
    ctx.close()
    browser.close()

print()
if fails:
    print("FAILED %d: %s" % (len(fails), ", ".join(fails)))
    sys.exit(1)
print("ALL PASS")
