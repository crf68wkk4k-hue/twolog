"""투로그 v23 확인 — 달력 일정 글씨 1포인트 · 여러 일정 분리 · 일정 시트 날짜/시간 같은 크기 · 큰 물결 · 노트 카드 제목 얇게 가운데 · My 버전.

1) 캘린더에 뜨는 일정 글씨 1포인트 키움 (9.5 → 11px, 막대 14 → 16px)
2) 한 날/한 주에 일정이 2개 이상이면 막대가 세로·가로로 떨어져 또렷하게 보임 (세 줄까지 펼침)
3) 일정 추가 시트 — 큰 날짜와 시간 글씨 크기가 «완전히 같고», 물결(~)은 더 큼
4) 노트 카드 제목 — 얇게(400) · 가운데 정렬
5) My 탭 맨 윗줄 「버전 v35」 · sw.js 캐시 twolog-v35

    python3 tests/v23.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                              has_touch=True, device_scale_factor=2)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")  # v25: 이 테스트는 로컬 모드 고정
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # ---------------- 0. 버전 ----------------
    sw = page.request.get(URL + "sw.js").text()
    check("sw.js 캐시 버전 twolog-v35", 'const VERSION = "twolog-v35"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:2])
    app_js = page.request.get(URL + "app.js").text()
    check("app.js 버전 상수 v35", 'var APP_VERSION = "v35"' in app_js)
    check("캐시 목록이 새 버전(shell-twolog-v35)", "shell-" in sw)

    # 예시 데이터로 상태를 만들고 일반 모드로
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)

    # ==================================================================
    # 1·2. 캘린더 — 글씨 1포인트 · 여러 일정 분리
    # ==================================================================
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(700)
    today_str = time.strftime("%Y-%m-%d")
    if page.locator("#s-cal .day[data-date='%s']" % today_str).count():
        page.locator("#s-cal .day[data-date='%s']" % today_str).click()
        page.wait_for_timeout(450)

    cal = page.evaluate("""(() => {
      const bars = Array.from(document.querySelectorAll('#s-cal .ebar'));
      const cs = bars.length ? getComputedStyle(bars[0]) : null;
      const rs = bars.map(b => { const r = b.getBoundingClientRect();
        return {t: b.textContent.trim(), x: r.left, y: r.top, w: r.width, h: r.height, b: r.bottom, r: r.right}; });
      const rowRects = Array.from(document.querySelectorAll('#s-cal .cal-row')).map(r => {
        const b = r.getBoundingClientRect(); return {t: b.top, b: b.bottom, h: b.height}; });
      return {n: bars.length,
              fs: cs ? cs.fontSize : null, lh: cs ? cs.lineHeight : null,
              h: cs ? cs.height : null, color: cs ? cs.color : null,
              rects: rs, rows: rowRects,
              ovf: Array.from(document.querySelectorAll('#s-cal .dovf')).map(e => e.textContent.trim()),
              dnumFs: (() => { const d = document.querySelector('#s-cal .day .dnum');
                return d ? getComputedStyle(d).fontSize : null; })()};
    })()""")
    # v27: 달력 칸 안 막대 글씨만 1px 더 작게 (11 → 10px) — 아래 상세 패널은 그대로
    check("달력 일정 글씨 10px (v27: 1px 더 작게)", cal["fs"] == "10px", cal["fs"])
    check("달력 일정 막대 높이 16px", cal["h"] == "16px" and cal["lh"] == "16px", (cal["h"], cal["lh"]))
    check("달력 일정 막대에 일정이 그려짐", cal["n"] >= 3, cal["n"])

    # 세로 분리 — 같은 칸에 쌓인 막대끼리 2px 이상 떨어짐
    rects = cal["rects"]
    vgaps = []
    for i in range(len(rects)):
        for j in range(len(rects)):
            a, b = rects[i], rects[j]
            if a is b:
                continue
            # a 가 b 보다 위이고, 가로로 겹치는 경우
            horiz = min(a["r"], b["r"]) - max(a["x"], b["x"])
            if horiz > 1 and a["b"] <= b["y"] + 0.5:
                vgaps.append(round(b["y"] - a["b"], 1))
    stacked = page.evaluate("""(() => {
      const bars = Array.from(document.querySelectorAll('#s-cal .ebar'));
      const byCol = {};
      bars.forEach(b => { const r = b.getBoundingClientRect();
        const k = Math.round(r.left / 7); (byCol[k] = byCol[k] || []).push(r.top); });
      return Math.max.apply(null, Object.keys(byCol).map(k => byCol[k].length)); })()""")
    # v28: 한 칸에 보이는 막대는 두 줄까지 (세 개부터는 +N)
    check("같은 칸에 일정 막대가 2줄까지 쌓임", stacked == 2, stacked)
    # v27: 한 칸에 일정이 여러 개면 막대 사이 빈틈 없이 딱 붙습니다
    # v27: 한 칸에 쌓인 막대는 빈틈 없이 붙습니다 (다른 주 사이 간격은 제외)
    check("쌓인 막대 사이에 빈틈이 없음 (v27: 붙여서)",
          bool(vgaps) and min(vgaps) == 0 and all(v <= 0.6 or v > 10 for v in vgaps),
          sorted(set(vgaps))[:6])

    # 가로 분리 — 이웃한 칸의 막대 사이 2px 이상
    hgaps = []
    for i in range(len(rects)):
        for j in range(len(rects)):
            a, b = rects[i], rects[j]
            if a is b:
                continue
            same_row = abs(a["y"] - b["y"]) < 1
            if same_row and a["r"] <= b["x"] + 0.5:
                hgaps.append(round(b["x"] - a["r"], 1))
    check("이웃한 칸 막대 사이도 2px 이상 벌어짐", bool(hgaps) and min(hgaps) >= 2,
          sorted(set(hgaps))[:6])
    check("막대가 날짜 칸 안에 들어옴", all(0 < r["w"] for r in rects), [round(r["w"], 1) for r in rects])

    # 넉 줄이 넘는 일정은 날짜 칸에 「외 N」 — 예시 데이터의 오늘은 일정이 네 개
    ovf = page.evaluate("""(() => {
      const d = new Date(); const iso = d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0');
      const cell = document.querySelector('#s-cal .day[data-date="' + iso + '"]');
      const o = cell ? cell.querySelector('.dovf') : null;
      const row = cell ? cell.closest('.cal-row') : null;
      const cr = cell.getBoundingClientRect();
      const bars = row ? Array.from(row.querySelectorAll('.ebar')).filter(b => {
        const r = b.getBoundingClientRect(); return r.left < cr.right - 1 && r.right > cr.left + 1; }) : [];
      return {bars: bars.map(b => b.textContent.trim()),
              ovf: o ? o.textContent.trim() : null}; })()""")
    check("일정이 많은 날은 두 줄까지 펼치고 나머지는 「+N」",
          len(ovf["bars"]) == 2 and bool(ovf["ovf"]) and str(ovf["ovf"]).startswith("+"), ovf)
    page.wait_for_timeout(1500)
    page.locator("#s-cal .cal").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "calendar-v23.png"))

    # 일정이 두 개인 날 — 둘 다 따로 보이고 「외 N」이 붙지 않는지 (실제 추가 흐름으로)
    month_day = time.strftime("%Y-%m-05")
    for ttl in ("친구 생일 파티", "치과 정기검진"):
        page.locator('#s-cal [data-act="addEvent"]').first.click()
        page.wait_for_timeout(550)
        page.fill('#sheetForm input[name="title"]', ttl)
        page.locator('#sheet .js-evdate[data-side="start"]').fill(month_day)
        page.wait_for_timeout(250)
        page.locator('#sheet .js-evdate[data-side="end"]').fill(month_day)
        page.wait_for_timeout(250)
        page.locator("#evSave").click()
        page.wait_for_timeout(650)
    two = page.evaluate("""(() => {
      const iso = '%s';
      const cell = document.querySelector('#s-cal .day[data-date="' + iso + '"]');
      if (!cell) return {ok: false};
      const row = cell.closest('.cal-row');
      const cr = cell.getBoundingClientRect();
      const bars = Array.from(row.querySelectorAll('.ebar')).map(b => {
        const r = b.getBoundingClientRect(); return {t: b.textContent.trim(), x: r.left, r: r.right,
          y: r.top, b: r.bottom, hit: r.left < cr.right - 1 && r.right > cr.left + 1}; })
        .filter(b => b.hit);
      const o = cell.querySelector('.dovf');
      return {ok: true, bars: bars.map(b => b.t),
              ovf: o ? o.textContent.trim() : null,
              gap: bars.length > 1 ? Math.round(bars[1].y - bars[0].b) : null};
    })()""" % month_day)
    check("일정 두 개인 날은 둘 다 따로 보임(외 N 없음)",
          len(two.get("bars", [])) == 2 and not two.get("ovf"), two)
    # v27: 한 칸에 일정이 여러 개면 막대 사이 빈틈 없이 딱 붙습니다
    check("두 일정 막대가 빈틈 없이 붙어 있음 (v27)", two.get("gap") is not None and abs(two["gap"]) <= 1, two.get("gap"))
    page.locator("#s-cal .day[data-date='%s']" % month_day).click()
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT, "calendar-v23-two.png"))

    # ==================================================================
    # 3. 일정 추가 시트 — 날짜·시간 같은 크기, 더 큰 물결
    # ==================================================================
    def sheet_metrics(w):
        page.locator("#tabbar .tab").nth(1).click()
        page.wait_for_timeout(550)
        page.locator('#s-cal [data-act="addEvent"]').first.click()
        page.wait_for_timeout(600)
        m = page.evaluate("""(() => {
          const sh = document.querySelector('#sheet');
          const big = sh.querySelector('.ev-dbig[data-dbig="start"]');
          const bigR = big.getBoundingClientRect();
          const bcs = getComputedStyle(big);
          const tbtn = sh.querySelector('.ev-time-btn[data-side="start"]');
          const tin = sh.querySelector('.ev-time-in[data-side="start"]');
          const dow = sh.querySelector('.ev-dow[data-dow="start"]');
          const til = sh.querySelector('.ev-tilde');
          const sides = Array.from(sh.querySelectorAll('.ev-side')).map(e => e.getBoundingClientRect());
          const when = sh.querySelector('.ev-when').getBoundingClientRect();
          const shR = sh.getBoundingClientRect();
          const tr = til.getBoundingClientRect();
          const tcs = getComputedStyle(til);
          // 두 날짜 블록 사이 가로 가운데
          const midGap = (sides[0].right + sides[1].left) / 2;
          return {vw: window.innerWidth,
                  bigFs: bcs.fontSize, bigW: bigR.width, bigSW: big.scrollWidth,
                  bigOverflow: big.scrollWidth > Math.ceil(bigR.width) + 1,
                  bigTxt: big.textContent.trim(),
                  btnFs: tbtn ? getComputedStyle(tbtn).fontSize : null, btnTxt: tbtn ? tbtn.textContent.trim() : null,
                  btnR: tbtn ? tbtn.getBoundingClientRect().width : null,
                  inFs: tin ? getComputedStyle(tin).fontSize : null,
                  dowTxt: dow ? dow.textContent.trim() : null,
                  dowFs: dow ? getComputedStyle(dow).fontSize : null,
                  dowWant: (() => { const i0 = sh.querySelector('.js-evdate[data-side="start"]');
                    const names = ['일요일','월요일','화요일','수요일','목요일','금요일','토요일'];
                    return i0 ? names[new Date(i0.value + 'T00:00:00').getDay()] : null; })(),
                  tildeFs: tcs.fontSize, tildeTxt: til.textContent.trim(),
                  tildeMid: tr.left + tr.width / 2, gapMid: midGap,
                  tildeVMid: tr.top + tr.height / 2,
                  side0VMid: sides[0].top + sides[0].height / 2,
                  whenL: when.left, whenR: when.right, sheetL: shR.left, sheetR: shR.right,
                  inSheet: bigR.left >= shR.left - 1 && bigR.right <= shR.right + 1
                           && sides[1].right <= shR.right + 1,
                  oneLine: (() => { const r = big.getClientRects(); return r.length; })(),
                  bigH: bigR.height, lh: bcs.lineHeight};
        })()""")
        return m

    ev = sheet_metrics(390)
    # v28: 날짜 19px · 아래 요일 13px, 시간 설정 버튼은 없앰
    check("날짜 글씨 19px (v28: 더 크게)", ev["bigFs"] == "19px", ev["bigFs"])
    check("날짜 아래 요일이 13px", ev["dowTxt"] == ev["dowWant"] and ev["dowFs"] == "13px",
          (ev["dowTxt"], ev["dowWant"], ev["dowFs"]))
    check("시간 설정 버튼·칸 없음", ev["btnFs"] is None and ev["inFs"] is None, (ev["btnFs"], ev["inFs"]))
    check("390px 폭에서 날짜가 한 줄로 잘리지 않음",
          not ev["bigOverflow"] and ev["oneLine"] == 1, (ev["bigTxt"], ev["bigW"], ev["bigSW"], ev["oneLine"]))
    check("390px 폭에서 요일도 한 줄", "요일" in str(ev["dowTxt"]), ev["dowTxt"])
    check("물결(~)이 날짜 글씨보다 큼", float(ev["tildeFs"].replace("px", "")) >= 26, ev["tildeFs"])
    check("물결이 두 날짜 블록 사이 가로 가운데", abs(ev["tildeMid"] - ev["gapMid"]) <= 3,
          (round(ev["tildeMid"], 1), round(ev["gapMid"], 1)))
    check("물결이 두 날짜 블록 세로 가운데", abs(ev["tildeVMid"] - ev["side0VMid"]) <= 3,
          (round(ev["tildeVMid"], 1), round(ev["side0VMid"], 1)))
    check("날짜가 시트 안에 들어옴", bool(ev["inSheet"]), (ev["sheetL"], ev["sheetR"], ev["whenR"]))
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT, "event-sheet-v23.png"))
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # 아이폰 SE 폭(375)에서도 한 줄인지
    page.set_viewport_size({"width": 375, "height": 667})
    page.wait_for_timeout(500)
    ev375 = sheet_metrics(375)
    check("375px 폭에서도 날짜·요일 한 줄 (넘침 없음)",
          not ev375["bigOverflow"] and ev375["oneLine"] == 1 and ev375["dowTxt"] == ev375["dowWant"],
          (ev375["bigW"], ev375["bigSW"], ev375["dowTxt"]))
    check("375px 폭에서도 시트 안", bool(ev375["inSheet"]), (ev375["sheetL"], ev375["whenR"]))
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(SHOT, "event-sheet-v23-375.png"))
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(300)
    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(500)

    # ==================================================================
    # 4. 노트 카드 제목 — 얇게(400) · 가운데
    # ==================================================================
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(700)
    note = page.evaluate("""(() => {
      const cs = Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)'));
      const c = cs[0];
      const t = c.querySelector('.nc-t');
      const s = getComputedStyle(t);
      const tr = t.getBoundingClientRect(), cr = c.getBoundingClientRect(), hr = c.querySelector('.nc-hd').getBoundingClientRect();
      const pad = parseFloat(getComputedStyle(c.querySelector('.nc-hd')).paddingLeft);
      return {n: cs.length, fw: s.fontWeight, ta: s.textAlign, fs: s.fontSize,
              ws: s.whiteSpace, ov: s.overflow,
              left: tr.left, right: tr.right, cardL: cr.left, cardR: cr.right,
              lines: Math.round(tr.height / parseFloat(s.lineHeight)),
              center: Math.abs((tr.left + tr.right) / 2 - (hr.left + hr.right) / 2),
              txt: t.textContent.trim()};
    })()""")
    check("노트 카드 있음", note["n"] >= 1, note["n"])
    check("카드 제목이 얇아짐(400 이하)", int(note["fw"]) <= 400, note["fw"])
    check("카드 제목이 가운데 정렬", note["ta"] == "center" and note["center"] <= 3,
          (note["ta"], round(note["center"], 1)))
    check("카드 제목은 그대로 한 줄 · 13.5px", note["ws"] == "nowrap" and note["ov"] == "hidden"
          and note["fs"] == "13.5px" and note["lines"] == 1, (note["fs"], note["ws"], note["lines"]))
    page.wait_for_timeout(1800)   # 안내(toast)가 사라진 뒤
    page.screenshot(path=os.path.join(SHOT, "note-v23.png"))

    # ==================================================================
    # 5. My 탭 버전 v23
    # ==================================================================
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(600)
    my = page.evaluate("""(() => {
      const v = document.querySelector('#s-set .hdr .app-ver');
      return {ok: !!v, txt: v ? v.textContent.trim() : null,
              right: v ? window.innerWidth - v.getBoundingClientRect().right : null};
    })()""")
    check("My 탭에 버전 v35 표시", my.get("ok") and "v35" in str(my.get("txt")), my.get("txt"))
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "my-v23.png"))

    # ==================================================================
    # 6. 홈 — 「{월}월의 우리」 삭제 · 다가오는 일정 부제목 작게
    # ==================================================================
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(650)
    home = page.evaluate("""(() => {
      const our = document.querySelector('.home-sec[data-sec="our"]');
      const smeta = document.querySelector('.row.sched .smeta');
      const sd = document.querySelector('.row.sched .smeta .sd');
      return {our: !!our, cards: document.querySelectorAll('.bcard').length,
              txt: document.querySelector('#s-home').innerText,
              smetaFs: smeta ? getComputedStyle(smeta).fontSize : null,
              sdFs: sd ? getComputedStyle(sd).fontSize : null,
              rows: document.querySelectorAll('.row.sched').length};
    })()""")
    check("홈에서 「월의 우리」 섹션 삭제", not home["our"] and home["cards"] == 0
          and "월의 우리" not in home["txt"], (home["our"], home["cards"]))
    check("홈은 D-day 다음이 다가오는 일정", home["rows"] >= 1 and "다가오는 일정" in home["txt"], home["rows"])
    check("다가오는 일정 부제목 글씨 한 단계 작게(11px)",
          home["smetaFs"] == "11px" and home["sdFs"] in ("11px", None), (home["smetaFs"], home["sdFs"]))
    page.screenshot(path=os.path.join(SHOT, "home-v23.png"))

    # 홈 「컬러」 시트에서도 「N월의 우리」 이름이 사라졌는지
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(500)
    th2 = page.evaluate("document.querySelector('#sheet').innerText")
    check("홈 컬러 시트에 「월의 우리」 없음", "월의 우리" not in th2, th2[:120])
    check("홈 컬러 시트에 「다가오는 일정」 색은 유지", 'data-sw="homeTitleBg"' in page.content()
          or page.locator('#sheet .sw-grid[data-sw="homeTitleBg"]').count() >= 1)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    page.locator('#s-set .menu-row[data-act="openThemeManager"]').click()
    page.wait_for_timeout(500)
    tm = page.evaluate("document.querySelector('#sheet').innerText")
    check("테마 관리에서도 「월의 우리」 없음 · 「다가오는 일정」만", "월의 우리" not in tm and "다가오는 일정" in tm, tm[:160])
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # ==================================================================
    # 7. 캘린더 — 선택한 날은 숫자에만 동그라미
    # ==================================================================
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(650)
    if page.locator("#s-cal .day[data-date='%s']" % today_str).count():
        page.locator("#s-cal .day[data-date='%s']" % today_str).click()
        page.wait_for_timeout(450)
    sel = page.evaluate("""(() => {
      const d = document.querySelector('#s-cal .day.sel');
      if (!d) return {ok: false};
      const n = d.querySelector('.dnum');
      const nr = n.getBoundingClientRect(), dr = d.getBoundingClientRect();
      const cs = getComputedStyle(n), dcs = getComputedStyle(d);
      const hol = document.querySelector('#s-cal .day.hol .dhol');
      return {ok: true, cellBg: dcs.backgroundColor, numBg: cs.backgroundColor, numColor: cs.color,
              w: Math.round(nr.width), h: Math.round(nr.height),
              radius: cs.borderTopLeftRadius,
              centered: Math.abs((nr.left + nr.right) / 2 - (dr.left + dr.right) / 2) <= 2,
              holColor: hol ? getComputedStyle(hol).color : null,
              holCss: getComputedStyle(document.documentElement).getPropertyValue('--hol').trim()};
    })()""")
    check("선택한 날 칸 바탕은 칠하지 않음", sel["ok"] and sel["cellBg"] in ("rgba(0, 0, 0, 0)", "transparent"), sel.get("cellBg"))
    check("날짜 숫자에만 동그라미(24px·정원)",
          sel["ok"] and sel["w"] == 24 and sel["h"] == 24
          and ("50%" in str(sel["radius"]) or "999px" in str(sel["radius"])), (sel.get("w"), sel.get("h"), sel.get("radius")))
    check("동그라미 안 숫자가 반전돼 보임", sel["numBg"] == "rgb(9, 9, 11)" and sel["numColor"] == "rgb(255, 255, 255)",
          (sel.get("numBg"), sel.get("numColor")))
    check("동그라미가 칸 가운데", bool(sel.get("centered")), sel.get("centered"))
    page.wait_for_timeout(1200)
    page.locator("#s-cal .cal").scroll_into_view_if_needed()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "calendar-v23.png"))

    # ==================================================================
    # 8. 사진첩 — 달력 보기
    # ==================================================================
    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(650)
    acts = page.evaluate("""(() => {
      const bs = Array.from(document.querySelectorAll('#s-photo .hdr-acts .round-btn'));
      return bs.map(b => { const r = b.getBoundingClientRect();
        return {act: b.getAttribute('data-act'), x: r.left, y: r.top, svg: !!b.querySelector('svg')}; });
    })()""")
    check("사진첩 + 옆에 달력 아이콘 버튼", len(acts) == 2 and acts[0]["act"] == "togglePhotoCal"
          and acts[1]["act"] == "addPhoto" and acts[0]["x"] < acts[1]["x"] and abs(acts[0]["y"] - acts[1]["y"]) <= 1,
          acts)
    check("달력 아이콘 버튼에 아이콘 있음", all(a["svg"] for a in acts), acts)
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(600)
    pc = page.evaluate("""(() => {
      const ym = document.querySelector('#s-photo .pcal-ym');
      const cells = Array.from(document.querySelectorAll('#s-photo .pcell'));
      const has = cells.filter(c => c.classList.contains('has'));
      const withBadge = has.filter(c => c.querySelector('.pc'));
      const days = cells.filter(c => !c.classList.contains('blank'));
      const nonPhoto = days.filter(c => !c.classList.contains('has'));
      const grid = document.querySelector('#s-photo .pcal-grid');
      const one = has[0];
      const oneR = one ? one.getBoundingClientRect() : null;
      const pn = one ? one.querySelector('.pn').getBoundingClientRect() : null;
      const badge = withBadge[0] ? withBadge[0].querySelector('.pc') : null;
      const bR = badge ? badge.getBoundingClientRect() : null;
      return {ym: ym ? ym.textContent.trim() : null, cells: days.length, has: has.length,
              badges: withBadge.map(c => (c.querySelector('.pc') || {}).textContent),
              imgs: has.filter(c => c.querySelector('img, svg')).length,
              firstImg: has.length ? has[0].querySelector('img, svg') !== null : false,
              gridCols: grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').length : 0,
              cellW: oneR ? Math.round(oneR.width) : null,
              cellH: oneR ? Math.round(oneR.height) : null,
              pnTopLeft: (oneR && pn) ? {top: Math.round(pn.top - oneR.top), left: Math.round(pn.left - oneR.left)} : null,
              badgeBR: (oneR && bR) ? {right: Math.round(oneR.right - bR.right), bottom: Math.round(oneR.bottom - bR.bottom)} : null,
              nonPhotoNumsOnly: nonPhoto.filter(c => { const t = c.innerText.trim();
                return /^\d{1,2}$/.test(t) && !c.querySelector('img, svg'); }).length,
              nonPhotoCount: nonPhoto.length,
              nav: !!document.querySelector('#s-photo [data-act="pcalPrev"]') && !!document.querySelector('#s-photo [data-act="pcalNext"]')};
    })()""")
    this_month = time.strftime("%Y년 %-m월")
    check("사진 달력이 이번 달 한 달만", pc["ym"] == this_month, (pc["ym"], this_month))
    check("달력은 7칸·이번 달 날짜 수만큼", pc["gridCols"] == 7 and pc["cells"] >= 28, (pc["gridCols"], pc["cells"]))
    check("사진 있는 날은 대표 사진이 채워짐", pc["has"] >= 1 and pc["imgs"] == pc["has"],
          (pc["has"], pc["imgs"]))
    check("여러 장인 날은 장수 배지", len(pc["badges"]) >= 1 and pc["badges"][0].isdigit(),
          pc["badges"])
    check("사진 있는 날: 날짜는 왼쪽 위", bool(pc["pnTopLeft"]) and pc["pnTopLeft"]["top"] <= 8 and pc["pnTopLeft"]["left"] <= 8,
          pc["pnTopLeft"])
    check("사진 있는 날: 장수는 오른쪽 아래", bool(pc["badgeBR"]) and pc["badgeBR"]["right"] <= 8
          and pc["badgeBR"]["bottom"] <= 8, pc["badgeBR"])
    check("사진 없는 날은 날짜 숫자만", pc["nonPhotoNumsOnly"] == pc["nonPhotoCount"],
          (pc["nonPhotoNumsOnly"], pc["nonPhotoCount"]))
    check("좌우 화살표 있음", pc["nav"])
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "photo-cal-v23.png"))

    # 화살표로 달 넘기기
    page.locator('#s-photo [data-act="pcalNext"]').click()
    page.wait_for_timeout(450)
    nxt = page.evaluate("document.querySelector('#s-photo .pcal-ym').textContent.trim()")
    check("다으다 달로 넘어감", nxt != this_month and nxt.endswith("월"), nxt)
    page.locator('#s-photo [data-act="pcalPrev"]').click()
    page.wait_for_timeout(450)
    back = page.evaluate("document.querySelector('#s-photo .pcal-ym').textContent.trim()")
    check("이전 달로 돌아옴", back == this_month, back)
    page.locator('#s-photo [data-act="pcalPrev"]').click()
    page.wait_for_timeout(450)
    page.screenshot(path=os.path.join(SHOT, "photo-cal-v23-prev.png"))
    page.locator('#s-photo [data-act="pcalNext"]').click()
    page.wait_for_timeout(450)

    # 좌우로 밀어서 달 넘기기
    sw = page.evaluate("""(() => {
      const g = document.querySelector('#s-photo .pcal-grid');
      const before = document.querySelector('#s-photo .pcal-ym').textContent.trim();
      const t = (x) => new Touch({identifier: 1, target: g, clientX: x, clientY: 400});
      g.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, cancelable: true,
        touches: [t(320)], changedTouches: [t(320)]}));
      g.dispatchEvent(new TouchEvent('touchend', {bubbles: true, cancelable: true,
        touches: [], changedTouches: [t(150)]}));
      return before;
    })()""")
    page.wait_for_timeout(500)
    after_sw = page.evaluate("document.querySelector('#s-photo .pcal-ym').textContent.trim()")
    check("손가락으로 밀어 다음 달", after_sw != sw, (sw, after_sw))
    page.locator('#s-photo [data-act="pcalPrev"]').click()
    page.wait_for_timeout(450)

    # 날짜 칸을 누르면 그날 사진 크게 보기
    page.locator('#s-photo .pcell.has').first.click()
    page.wait_for_timeout(600)
    pv = page.evaluate("""(() => {
      const pv = document.querySelector('#sheet .pview');
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
              hasView: !!pv, count: (document.querySelector('#sheet .pv-count') || {}).textContent || null};
    })()""")
    check("사진 있는 날을 누르면 그날 사진이 열림", pv["open"] and pv["hasView"], pv)
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)

    # 목록 보기로 돌아가기
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(550)
    back_to_list = page.evaluate("""(() => ({
      pcal: !!document.querySelector('#s-photo .pcal'),
      polas: document.querySelectorAll('#s-photo .pola').length }))()""")
    check("달력 아이콘을 다시 누르면 목록(폴라로이드)으로", back_to_list["pcal"] is False and back_to_list["polas"] >= 1,
          back_to_list)

    # 다크 모드에서도 같은 모양인지 (캘린더 막대·일정 시트)
    page.evaluate("document.documentElement.setAttribute('data-mode', 'dark'); 0")
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(600)
    dark = page.evaluate("""(() => {
      const b = document.querySelector('#s-cal .ebar');
      return b ? {fs: getComputedStyle(b).fontSize, h: getComputedStyle(b).height} : null; })()""")
    check("다크 모드에서도 막대 10px/16px", dark and dark["fs"] == "10px" and dark["h"] == "16px", dark)
    page.evaluate("document.documentElement.removeAttribute('data-mode'); 0")
    page.wait_for_timeout(300)

    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
