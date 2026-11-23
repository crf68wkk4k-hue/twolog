"""투로그 v21 확인 — 노트·캘린더 다듬기.

1) 노트 위 탭(메모·버킷리스트·영화·먹방)과 내 리스트 칩의 끝을 둥글게(12px).
2) 노트 카드(새 리스트 카드 포함) 모서리를 둥글게(16px) + 바깥 테두리선 삭제.
3) 카드 상세 시트에서 제목 입력칸 «바로 위»에 제목 바탕색 컬러판(12색 뮤트 + 기본).
   고른 색은 카드 데이터(titleBg)에 저장돼 다시 열어도 남고, 카드 제목에 둥근 블록으로 깔림.
4) 캘린더에서 날짜를 누르면 «그날 일정만» — 메모·기록·사진 묶음 없음.

    python3 tests/v21.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def abs_(a):
    return abs(a)


with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")  # v25: 이 테스트는 로컬 모드 고정
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # ---------------- 서비스워커 캐시 버전 ----------------
    sw = page.request.get(URL + "sw.js").text()
    # v24: 캐시 버전은 배포마다 올라가므로 v24 으로 (앱 버전 상수와 같은 값)
    check("sw.js 캐시 버전 twolog-v49", 'const VERSION = "twolog-v49"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:2])

    # 예시 데이터로 한 번 열어 상태를 만들고, 저장되는 일반 모드로 옮겨요
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)

    # ---------------- 1. 노트 상단 탭·칩 둥근 끝 ----------------
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(600)
    check("노트 화면 열림", page.locator("#s-diary .ngrid").count() == 1)

    tabs = page.evaluate("""(() => {
      const b = document.querySelector('#s-diary .segs .seg-btn');
      const cs = getComputedStyle(b);
      const all = Array.from(document.querySelectorAll('#s-diary .segs .seg-btn')).map(x => getComputedStyle(x).borderTopLeftRadius);
      return {tl: cs.borderTopLeftRadius, tr: cs.borderTopRightRadius, all, h: b.getBoundingClientRect().height};
    })()""")
    check("노트 위 탭 끝이 둥글게(12px)", tabs["tl"] == "12px" and tabs["tr"] == "12px", tabs)
    check("노트 탭 세 칸 모두 둥글게", set(tabs["all"]) == {"12px"}, tabs["all"])
    # v29: 알약 탭을 조금 줄여 44px → 40px
    check("노트 탭 높이 40px", abs(tabs["h"] - 40) <= 0.5, tabs["h"])

    chip = page.evaluate("""(() => {
      const c = document.querySelector('#s-diary .lchip');
      return c ? getComputedStyle(c).borderTopLeftRadius : null;
    })()""")
    check("내 리스트 칩도 둥글게(12px)", chip in (None, "12px"), chip)

    # ---------------- 2. 노트 카드 둥근 모서리 + 테두리선 삭제 ----------------
    card_style = page.evaluate("""(() => {
      const cards = Array.from(document.querySelectorAll('#s-diary .ngrid .ncard'));
      const one = cards.filter(c => !c.classList.contains('new'))[0];
      const nw = document.querySelector('#s-diary .ncard.new');
      const g = (e) => { const s = getComputedStyle(e);
        return {r: s.borderTopLeftRadius, r2: s.borderBottomRightRadius,
                bt: s.borderTopWidth, bl: s.borderLeftWidth, br: s.borderRightWidth, bb: s.borderBottomWidth,
                bg: s.backgroundColor, sh: s.boxShadow};
      };
      return {card: one ? g(one) : null, new: nw ? g(nw) : null,
              count: cards.length};
    })()""")
    c1 = card_style["card"] or {}
    check("노트 카드 끝이 둥글게(16px)", c1.get("r") == "16px" and c1.get("r2") == "16px", c1)
    check("노트 카드 바깥 테두리선 삭제", all(c1.get(k) == "0px" for k in ("bt", "bl", "br", "bb")), c1)
    check("테두리 없이도 카드가 배경·그림자로 구분됨", c1.get("sh") not in (None, "none", ""), c1.get("sh"))
    n1 = card_style["new"] or {}
    check("새 리스트 카드도 둥글게(16px)", n1.get("r") == "16px", n1)
    check("새 리스트 카드도 테두리선 없음", all(n1.get(k) == "0px" for k in ("bt", "bl", "br", "bb")), n1)
    page.wait_for_timeout(200)
    page.screenshot(path=os.path.join(SHOT, "note-v21.png"))

    # ---------------- 3. 카드 시트의 제목 색 컬러판 ----------------
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-t").tap()
    page.wait_for_timeout(500)
    check("카드 시트 열림", page.evaluate("document.getElementById('sheetWrap').classList.contains('open')"))

    pal = page.evaluate("""(() => {
      const cp = document.querySelector('#sheet .cp.ccp');
      const grid = document.querySelector('#sheet .sw-grid[data-sw="cardTitleBg"]');
      const lab = document.querySelector('#sheet #sheetForm label');
      const inp = document.querySelector('#sheet #sheetForm input[name="title"]');
      const reset = document.querySelector('#sheet .cp-reset[data-act="pickCardColor"]');
      if (!cp || !grid || !lab || !inp) return {ok: false};
      const cr = cp.getBoundingClientRect(), lr = lab.getBoundingClientRect(), ir = inp.getBoundingClientRect();
      return {ok: true,
              sw: grid.querySelectorAll('.sw').length,
              colors: Array.from(grid.querySelectorAll('.sw')).map(b => b.getAttribute('data-color')),
              hd: cp.querySelector('.cp-hd').innerText.replace(/\\n/g, ' ').trim(),
              val: (cp.querySelector('.cp-val') || {}).textContent,
              reset: reset ? reset.textContent.trim() : null,
              resetOn: reset ? reset.classList.contains('on') : null,
              paletteAbove: cr.bottom <= lr.top + 1,
              paletteAboveInput: cr.bottom <= ir.top + 1,
              gapTopal: lr.top - cr.bottom,
              gapInputToPal: cr.top - ir.bottom,
              titleFont: getComputedStyle(inp).fontSize};
    })()""")
    check("카드 시트에 제목 색 컬러판", pal.get("ok"), pal)
    check("제목 색 = 12색 팔레트", pal.get("sw") == 12, pal.get("sw"))
    check("기존 12색 뮤트 팔레트 그대로", pal.get("colors") == [
        "#F2CFC9", "#DEA2A6", "#DD785B", "#EA994D", "#EFD353", "#C4C66A",
        "#B8CAA5", "#B4D8D4", "#80A4AA", "#D2CBE3", "#A299B8", "#C4B28E"], pal.get("colors"))
    # v40: 「제목」이 맨 위로 올라가고, 한 칸(18~20px) 띄워 그 아래에 「제목 색」 컬러판
    check("제목 입력칸 아래 한 칸 띄워 제목 색 컬러판",
          (not pal.get("paletteAbove")) and (not pal.get("paletteAboveInput"))
          and 16 <= pal.get("gapInputToPal", -1) <= 26, (pal.get("gapInputToPal"), pal.get("titleFont")))
    # v22: 「기본」이 제목 줄 오른쪽으로 올라가고 색 값(헥스)은 그대로 적지 않아요
    check("컬러판 제목 줄은 「제목 색」 (헥스 코드 없음)", "제목 색" in str(pal.get("hd"))
          and "#" not in str(pal.get("hd")) and pal.get("val") is None, pal)
    check("처음엔 「기본」 선택", pal.get("resetOn") is True, pal.get("resetOn"))

    # 노란색(레몬 #EFD353) 고르기
    page.locator('#sheet .sw-grid[data-sw="cardTitleBg"] .sw[data-color="#EFD353"]').click()
    page.wait_for_timeout(500)
    after = page.evaluate("""(() => {
      const g = window.__app.state.groups.todo[0];
      const card = document.querySelector('#s-diary .ngrid .ncard:not(.new)');
      const hd = card.querySelector('.nc-hd'), t = card.querySelector('.nc-t');
      const cr = card.getBoundingClientRect(), hr = hd.getBoundingClientRect();
      const cs = getComputedStyle(hd), ts = getComputedStyle(t);
      const cp = document.querySelector('#sheet .cp.ccp');
      const sel = cp ? cp.querySelector('.sw.sel') : null;
      const item = card.querySelector('.cti .cx');
      const ics = item ? getComputedStyle(item) : null;
      return {titleBg: g ? g.titleBg : null,
              val: cp.querySelector('.cp-val') ? cp.querySelector('.cp-val').textContent.trim() : null,
              sel: sel ? sel.getAttribute('data-color') : null,
              cls: hd.className, bg: cs.backgroundColor, col: ts.color,
              full: Math.abs(hr.width - cr.width) < 0.6 && Math.abs(hr.left - cr.left) < 0.6
                    && Math.abs(hr.top - cr.top) < 0.6,
              cardPad: getComputedStyle(card).paddingTop,
              itemFs: ics ? ics.fontSize : null, itemFw: ics ? ics.fontWeight : null,
              sheetStillOpen: document.getElementById('sheetWrap').classList.contains('open')};
    })()""")
    check("고른 색이 카드 데이터에 저장(titleBg)", after["titleBg"] == "#EFD353", after["titleBg"])
    check("고른 칸에 선택 테두리", after["sel"] == "#EFD353", after["sel"])
    check("카드 위쪽 띠가 고른 색으로", after["bg"] == "rgb(239, 211, 83)", after["bg"])
    check("색 띠가 카드 위·좌우 끝까지 꽉 참", after["cls"] and "tint" in after["cls"] and after["full"] and after["cardPad"] == "0px",
          (after["cls"], after["full"], after["cardPad"]))
    check("색 위 글씨는 선명한 어두운 색", after["col"] == "rgb(17, 17, 17)", after["col"])
    check("카드 안 항목 글씨 14px·가볍게(400)", after["itemFs"] == "14px" and after["itemFw"] == "400",
          (after["itemFs"], after["itemFw"]))
    check("색을 골라도 시트가 닫히지 않음", after["sheetStillOpen"])
    page.wait_for_timeout(1700)   # 안내(toast)가 사라진 뒤
    page.screenshot(path=os.path.join(SHOT, "note-detail-v21.png"))

    # ---------------- 4. 다시 열어도 유지 ----------------
    page.locator("#sheet [data-close]").first.click()
    page.wait_for_timeout(400)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(600)
    keep = page.evaluate("""(() => {
      const g = window.__app.state.groups.todo[0];
      const cards = Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)'));
      const tinted = cards.filter(c => c.querySelector('.nc-hd.tint'));
      const hd = tinted[0] ? tinted[0].querySelector('.nc-hd') : null;
      const t = tinted[0] ? tinted[0].querySelector('.nc-t') : null;
      return {titleBg: g ? g.titleBg : null, n: tinted.length,
              bg: hd ? getComputedStyle(hd).backgroundColor : null,
              txt: t ? t.textContent : null};
    })()""")
    check("앱을 다시 열어도 카드 색 유지", keep["titleBg"] == "#EFD353" and keep["n"] == 1
          and keep["bg"] == "rgb(239, 211, 83)", keep)
    page.screenshot(path=os.path.join(SHOT, "note-v21-tint.png"))

    # 카드마다 다른 색을 따로 저장하는지 (다른 카드 하나 더 만들어 확인)
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(450)
    page.fill('#sheet #sheetForm input[name="title"]', "주말 장보기")
    page.locator('#sheet button[type="submit"]').click()
    page.wait_for_timeout(600)
    # v42: 카드 미리보기가 5개까지 보여 「주말 장보기」가 메모 카드 항목으로도 보여요 —
    #      제목(.nc-t)이 정확히 그 카드인 것을 골라요
    page.locator("#s-diary .ngrid .ncard:not(.new)").filter(
        has=page.locator(".nc-t", has_text="주말 장보기")).first.locator(".nc-t").tap()
    page.wait_for_timeout(500)
    page.locator('#sheet .sw-grid[data-sw="cardTitleBg"] .sw[data-color="#B4D8D4"]').click()
    page.wait_for_timeout(500)
    two = page.evaluate("""(() => window.__app.state.groups.todo.map(g => [g.title, g.titleBg || null]))()""")
    check("카드별로 색이 따로 저장", ["메모", "#EFD353"] in two and ["주말 장보기", "#B4D8D4"] in two, two)

    # ---------------- 5. 「기본」으로 되돌리기 ----------------
    page.locator('#sheet .cp-reset[data-act="pickCardColor"]').click()
    page.wait_for_timeout(500)
    back = page.evaluate("""(() => {
      const g = window.__app.state.groups.todo.filter(x => x.title === '주말 장보기')[0];
      const c = Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new)'))
        .filter(n => { const t = n.querySelector('.nc-t'); return t && t.textContent.trim() === '주말 장보기'; })[0];
      const hd = c ? c.querySelector('.nc-hd') : null;
      return {titleBg: g ? (g.titleBg || null) : 'none', cls: hd ? hd.className : null,
              bg: hd ? getComputedStyle(hd).backgroundColor : null};
    })()""")
    check("「기본」이면 은은한 기본 띠로", back["titleBg"] in ("", None) and back["cls"] == "nc-hd"
          and back["bg"] == "rgb(245, 245, 247)", back)

    # ---------------- 6. 다크 모드에서도 그대로 ----------------
    page.evaluate("document.documentElement.setAttribute('data-mode','dark'); 0")
    page.wait_for_timeout(400)
    dk = page.evaluate("""(() => {
      const hd = document.querySelector('#s-diary .ncard .nc-hd.tint');
      const t = hd ? hd.querySelector('.nc-t') : null;
      const c = document.querySelector('#s-diary .ncard');
      const cs = getComputedStyle(c);
      return {bg: hd ? getComputedStyle(hd).backgroundColor : null, col: t ? getComputedStyle(t).color : null,
              cardBorder: cs.borderTopWidth, cardR: cs.borderTopLeftRadius, cardBg: cs.backgroundColor};
    })()""")
    check("다크에서도 제목 색 유지", dk["bg"] == "rgb(239, 211, 83)" and dk["col"] == "rgb(17, 17, 17)", dk)
    check("다크 카드도 둥글고 테두리 없음", dk["cardBorder"] == "0px" and dk["cardR"] == "16px", dk)
    page.screenshot(path=os.path.join(SHOT, "note-v21-dark.png"))
    page.evaluate("document.documentElement.setAttribute('data-mode','light'); 0")
    page.wait_for_timeout(350)

    # ---------------- 7. 캘린더: 그날 일정만 ----------------
    if page.evaluate("document.getElementById('sheetWrap').classList.contains('open')"):
        page.locator("#sheet [data-close]").first.click()
        page.wait_for_timeout(400)
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(700)
    today_str = time.strftime("%Y-%m-%d")
    page.locator("#s-cal .day[data-date='%s']" % today_str).click()
    page.wait_for_timeout(500)
    cal = page.evaluate("""(() => {
      const p = document.querySelector('#s-cal .daypanel');
      return {ev: p.querySelectorAll('.daylist .ev').length,
              sec: p.querySelectorAll('.dp-sec').length,
              ph: p.querySelectorAll('.dp-ph, .dp-photos').length,
              memo: p.querySelectorAll('.dp-memo').length,
              log: p.querySelectorAll('.dp-log').length,
              txt: p.innerText.replace(/\\n/g, ' | ').trim(),
              add: p.querySelectorAll('[data-act="addEvent"]').length};
    })()""")
    check("그날 일정은 보임", cal["ev"] >= 1, cal["ev"])
    check("메모·기록·사진 묶음 없음", cal["sec"] == 0 and cal["ph"] == 0 and cal["memo"] == 0 and cal["log"] == 0, cal)
    check("일정 외 잡다한 글씨 없음", all(k not in cal["txt"] for k in ("📝", "🖼️", "🎬", "개 ›", "장")), cal["txt"][:160])
    check("「일정 추가」 버튼은 그대로", cal["add"] >= 1, cal["add"])
    page.wait_for_timeout(1600)
    page.screenshot(path=os.path.join(SHOT, "calendar-v21.png"))

    # 일정이 없는 날(사진만 있는 날)은 안내 문구만
    day = page.evaluate("(() => { const p = window.__app.state.photos[0]; return p ? p.date.slice(0,10) : null; })()")
    page.locator("#s-cal .day[data-date='%s']" % day).click()
    page.wait_for_timeout(450)
    empty = page.evaluate("""(() => { const p = document.querySelector('#s-cal .daypanel');
      const e = p.querySelector('.daylist .empty');
      return {ev: p.querySelectorAll('.daylist .ev').length, empty: e ? e.textContent.trim() : null,
              sec: p.querySelectorAll('.dp-sec, .dp-ph, .dp-memo').length}; })()""")
    check("일정 없는 날은 안내만", empty["ev"] == 0 and empty["ev"] == 0 and empty["sec"] == 0
          and (empty["empty"] or "").endswith("일정이 없어요."), empty)
    page.wait_for_timeout(1400)
    page.screenshot(path=os.path.join(SHOT, "calendar-empty-v21.png"))

    # ---------------- 7-2. 오늘 옆 점 삭제 · 진한 검정 · 선명한 공휴일 빨강 ----------------
    dot = page.evaluate("""(() => {
      const d = document.querySelector('#s-cal .day.today .dnum');
      if (!d) return {today: false};
      const af = getComputedStyle(d, '::after');
      return {today: true, content: af.content, w: af.width, h: af.height};
    })()""")
    check("오늘 날짜 옆 점 표시 없음", dot.get("today") and dot.get("content") in ("none", "normal", '""'), dot)

    ink = page.evaluate("""(() => {
      const root = getComputedStyle(document.documentElement);
      const dn = document.querySelector('#s-cal .day:not(.sel):not(.hol):not(.sun):not(.sat) .dnum');
      const title = document.querySelector('#s-cal .daypanel-hd .d') || document.body;
      return {v: root.getPropertyValue('--ink').trim(),
              num: dn ? getComputedStyle(dn).color : null,
              title: getComputedStyle(title).color};
    })()""")
    check("라이트 검정이 더 진해짐(#09090B)", ink["v"].upper() == "#09090B"
          and ink["num"] == "rgb(9, 9, 11)" and ink["title"] == "rgb(9, 9, 11)", ink)

    gap = page.evaluate("""(() => {
      const cs = getComputedStyle(document.querySelector('#s-cal .daypanel'));
      const rows = Array.from(document.querySelectorAll('#s-cal .cal-row'));
      const nums = rows.length ? Array.from(rows[rows.length - 1].querySelectorAll('.dnum')) : [];
      const lastNumBottom = nums.length ? Math.max.apply(null, nums.map(n => n.getBoundingClientRect().bottom)) : null;
      const t = document.querySelector('#s-cal .daypanel-hd .d');
      const titleTop = t ? t.getBoundingClientRect().top : null;
      return {mt: cs.marginTop, pt: cs.paddingTop, lastNumBottom, titleTop,
              lastRowH: rows.length ? rows[rows.length - 1].getBoundingClientRect().height : null};
    })()""")
    check("달력–일정 사이 한 줄 띄움(14+12)", gap["mt"] == "14px" and gap["pt"] == "12px", gap)
    # 마지막 주에 일정이 없을 때만 그 빈 줄을 줄이므로, 그 경우에만 확인
    if gap["lastRowH"] is not None and gap["lastRowH"] <= 40:
        check("마지막 날짜 숫자와 일정 제목 사이 60px 이내",
              gap["titleTop"] - gap["lastNumBottom"] <= 60, (gap["lastNumBottom"], gap["titleTop"]))

    # 달력 숫자 전용 폰트 + 양끝 폭
    calw = page.evaluate("""(async () => {
      await document.fonts.ready;
      const cal = document.querySelector('#s-cal .cal');
      const r = cal.getBoundingClientRect();
      const dn = document.querySelector('#s-cal .day:not(.blank) .dnum');
      const cells = Array.from(document.querySelectorAll('#s-cal .cal-daygrid .day:not(.blank)'));
      return {w: r.width, left: r.left, right: window.innerWidth - r.right,
              family: getComputedStyle(dn).fontFamily, weight: getComputedStyle(dn).fontWeight,
              tnum: getComputedStyle(dn).fontVariantNumeric,
              loaded: document.fonts.check("600 15px 'Nixgon'"),
              monthFamily: getComputedStyle(document.querySelector('#s-cal .cal-month')).fontFamily,
              weekFamily: getComputedStyle(document.querySelector('#s-cal .cal-week span')).fontFamily,
              bodyFamily: getComputedStyle(document.body).fontFamily,
              titleFamily: getComputedStyle(document.querySelector('#s-cal .daypanel-hd .d')).fontFamily,
              cellW: cells[0] ? cells[0].getBoundingClientRect().width : null};
    })()""")
    check("달력이 화면 양끝 가까이 넓어짐(좌우 9px)", calw["left"] <= 10.5 and calw["right"] <= 10.5, calw)
    check("캘린더 숫자도 닉스곤체", "Nixgon" in calw["family"] and calw["loaded"], (calw["family"], calw["loaded"]))
    check("캘린더 한글은 설정한 앱 폰트 그대로", calw["monthFamily"] == calw["bodyFamily"]
          and calw["weekFamily"] == calw["bodyFamily"] and calw["titleFamily"] == calw["bodyFamily"]
          and "Nixgon" not in calw["monthFamily"],
          (calw["monthFamily"], calw["bodyFamily"]))
    check("숫자 굵기·자릿수 고정", calw["weight"] == "600" and calw["tnum"] == "tabular-nums", (calw["weight"], calw["tnum"]))

    # 「일」 요일 헤더와 모든 일요일 숫자도 공휴일과 같은 진한 빨강
    # (고른 날은 숫자가 흰색이 되는 원형 표시, 오늘은 강조색 — 둘 다 비교에서 뺍니다)
    sun = page.evaluate("""(() => {
      const wd = document.querySelector('#s-cal .cal-week span');
      const days = Array.from(document.querySelectorAll('#s-cal .day.sun:not(.sel):not(.today) .dnum'));
      return {wd: getComputedStyle(wd).color, wdTxt: wd.textContent.trim(),
              n: days.length, cols: Array.from(new Set(days.map(d => getComputedStyle(d).color)))};
    })()""")
    check("「일」 요일 헤더도 진한 빨강", sun["wdTxt"] == "일" and sun["wd"] == "rgb(240, 20, 20)", sun)
    check("일요일 날짜 숫자 모두 진한 빨강", sun["n"] >= 4 and sun["cols"] == ["rgb(240, 20, 20)"], sun)

    # My 에서 고른 폰트를 바꾸면 캘린더 한글도 같이 따라오는지
    page.evaluate("document.documentElement.style.setProperty('--font', \"'BM Jua', Pretendard, sans-serif\"); 0")
    page.wait_for_timeout(250)
    inh = page.evaluate("""(() => ({m: getComputedStyle(document.querySelector('#s-cal .cal-month')).fontFamily,
      d: getComputedStyle(document.querySelector('#s-cal .day .dnum')).fontFamily}))()""")
    check("설정 폰트를 바꾸면 캘린더 한글도 따라감", "BM Jua" in inh["m"], inh["m"])
    check("숫자는 그대로 닉스곤체", inh["d"].startswith("Nixgon"), inh["d"])
    page.evaluate("document.documentElement.style.removeProperty('--font'); 0")
    page.wait_for_timeout(200)

    page.locator('#s-cal [data-act="calPrev"]').click()
    page.wait_for_timeout(650)
    hol = page.evaluate("""(() => { const d = document.querySelector('#s-cal .day.hol .dnum');
      const n = document.querySelector('#s-cal .day.hol .dhol');
      return {month: document.querySelector('#s-cal .cal-month').textContent.trim(),
              num: d ? getComputedStyle(d).color : null,
              name: n ? getComputedStyle(n).color : null,
              var: getComputedStyle(document.documentElement).getPropertyValue('--hol').trim(),
              count: document.querySelectorAll('#s-cal .day.hol').length}; })()""")
    check("공휴일은 채도 높은 빨강(#F01414)", hol["var"].upper() == "#F01414" and hol["num"] == "rgb(240, 20, 20)", hol)
    check("공휴일 이름도 같은 빨강", hol["name"] == "rgb(240, 20, 20)", hol["name"])
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(SHOT, "calendar-holiday-v21.png"))

    page.evaluate("document.documentElement.setAttribute('data-mode','dark'); 0")
    page.wait_for_timeout(400)
    dkhol = page.evaluate("""(() => { const d = document.querySelector('#s-cal .day.hol .dnum');
      return {c: d ? getComputedStyle(d).color : null,
              v: getComputedStyle(document.documentElement).getPropertyValue('--hol').trim()}; })()""")
    check("다크 공휴일도 뚜렷한 빨강(#FF3B3B)", dkhol["v"].upper() == "#FF3B3B" and dkhol["c"] == "rgb(255, 59, 59)", dkhol)
    page.evaluate("document.documentElement.setAttribute('data-mode','light'); 0")
    page.wait_for_timeout(400)
    page.locator('#s-cal [data-act="calNext"]').click()
    page.wait_for_timeout(600)
    page.locator("#s-cal .day[data-date='%s']" % today_str).click()
    page.wait_for_timeout(600)
    page.wait_for_timeout(1300)
    page.screenshot(path=os.path.join(SHOT, "calendar-v21.png"))

    # ---------------- 7-4. 일정 검색은 «검색만» ----------------
    page.locator('#s-cal [data-act="calSearch"]').click()
    page.wait_for_timeout(500)
    sr = page.evaluate("""(() => {
      const sh = document.querySelector('#sheet');
      const inp = document.querySelector('#calSearchIn');
      const out = document.querySelector('#calSearchOut');
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
              rows: sh.querySelectorAll('.sres').length,
              empty: sh.querySelectorAll('.sres-empty').length,
              outVisible: out ? getComputedStyle(out).display !== 'none' : null,
              focus: document.activeElement === inp,
              labels: sh.querySelectorAll('.f > label').length,
              text: sh.innerText.split(String.fromCharCode(10)).join(' | ').trim(),
              ph: inp ? inp.getAttribute('placeholder') : null};
    })()""")
    check("검색 시트 처음엔 입력칸만", sr["open"] and sr["rows"] == 0 and sr["empty"] == 0
          and sr["outVisible"] is False, sr)
    pos = page.evaluate("""(() => {
      const sh = document.querySelector('#sheet'); const r = sh.getBoundingClientRect();
      const w = document.getElementById('sheetWrap');
      return {center: r.top + r.height / 2, vh: window.innerHeight, top: r.top,
              bottom: window.innerHeight - r.bottom, radius: getComputedStyle(sh).borderTopLeftRadius,
              cls: w.className, width: Math.round(r.width)};
    })()""")
    # v22: 아이폰 키보드에 가려지지 않도록 «화면 위쪽» 고정으로 바뀌었어요 (v21 의 «가운데» 기준을 현행에 맞춤)
    check("검색창이 화면 위쪽에 떠 있음", pos["top"] <= 90, pos)
    check("아래 절반은 비워 둠(키보드 자리)", pos["bottom"] >= pos["vh"] * 0.35, pos)
    check("검색 모달은 둥글고 좁게", "sheet-center" in pos["cls"] and pos["radius"] != "0px" and pos["width"] <= 350, pos)
    check("처음부터 결과 목록·안내 문구 없음", "일정이 없어요" not in sr["text"] and sr["labels"] == 0, sr["text"][:120])
    check("검색칸은 안내를 플레이스홀더로", sr["ph"] and "검색" in sr["ph"], sr["ph"])

    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(SHOT, "calendar-search-v21.png"))
    page.fill("#calSearchIn", "성")
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "calendar-search-result-v21.png"))
    r1 = page.evaluate("""(() => ({rows: document.querySelectorAll('#sheet .sres').length,
      empty: document.querySelectorAll('#sheet .sres-empty').length,
      out: getComputedStyle(document.querySelector('#calSearchOut')).display,
      titles: Array.from(document.querySelectorAll('#sheet .sres .st')).map(x => x.textContent)}))()""")
    check("글자를 치면 바로 결과가 아래에", r1["rows"] >= 1 and r1["out"] != "none", r1)
    check("친 글자에 맞는 일정만", all("성" in t for t in r1["titles"]), r1["titles"])

    page.fill("#calSearchIn", "없는일정이름")
    page.wait_for_timeout(400)
    r2 = page.evaluate("""(() => ({rows: document.querySelectorAll('#sheet .sres').length,
      empty: document.querySelectorAll('#sheet .sres-empty').length}))()""")
    check("맞는 게 없으면 안내만", r2["rows"] == 0 and r2["empty"] == 1, r2)

    page.fill("#calSearchIn", "성수")
    page.wait_for_timeout(400)
    page.locator('#sheet .sres').first.click()
    page.wait_for_timeout(600)
    jm = page.evaluate("""(() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      month: document.querySelector('#s-cal .cal-month').textContent.trim(),
      sel: window.__app.state.ui.selDate,
      ev: document.querySelectorAll('#s-cal .daylist .ev').length}))()""")
    check("결과를 누르면 그 날짜로 이동", (not jm["open"]) and jm["sel"] == today_str and jm["ev"] >= 1, jm)

    # ---------------- 7-5. 달력에서 좌우로 밀면 달 이동 ----------------
    cdp = ctx.new_cdp_session(page)

    def swipe(x1, y1, x2, y2, steps=8):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x1, "y": y1}]})
        for i in range(1, steps + 1):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [
                {"x": x1 + (x2 - x1) * i / steps, "y": y1 + (y2 - y1) * i / steps}]})
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(600)

    month0 = page.evaluate("document.querySelector('#s-cal .cal-month').textContent.trim()")
    sel0 = page.evaluate("window.__app.state.ui.selDate")
    swipe(330, 260, 60, 268)          # 왼쪽으로 밀기 → 다음 달
    month1 = page.evaluate("document.querySelector('#s-cal .cal-month').textContent.trim()")
    check("달력을 왼쪽으로 밀면 다음 달", month0 == "11월" and month1 == "12월", (month0, month1))
    swipe(60, 260, 330, 268)          # 오른쪽으로 밀기 → 이전 달
    month2 = page.evaluate("document.querySelector('#s-cal .cal-month').textContent.trim()")
    check("달력을 오른쪽으로 밀면 이전 달", month2 == "11월", month2)
    check("밀어도 날짜 선택은 그대로", page.evaluate("window.__app.state.ui.selDate") == sel0, sel0)

    # 세로로 미는 것(스크롤)은 달을 넘기지 않음
    swipe(200, 260, 210, 400)
    check("세로로 밀면 달 그대로", page.evaluate("document.querySelector('#s-cal .cal-month').textContent.trim()") == "11월")
    # 짧게 눌러 날짜를 고르는 건 그대로
    page.locator("#s-cal .day[data-date='2026-11-20']").click()
    page.wait_for_timeout(450)
    check("짧게 누르면 날짜 선택 그대로", page.evaluate("window.__app.state.ui.selDate") == "2026-11-20",
          page.evaluate("window.__app.state.ui.selDate"))

    # ---------------- 7-6. 일정 추가 시트 (컬러 → 제목 → 큰 날짜 ~ 큰 날짜 → 함께/나/준영) ----------------
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(550)
    ef = page.evaluate("""(() => {
      const sh = document.querySelector('#sheet');
      const hv = sh.querySelector('.sheet-hd');
      const chk = sh.querySelector('#evSave');
      const cs = chk ? getComputedStyle(chk) : null;
      const g = s => { const e = sh.querySelector(s); return e ? e.getBoundingClientRect() : null; };
      const cp = g('[data-sw="evColor"]'), ti = g('#sheetForm input[name="title"]');
      const when = g('.ev-when'), who = g('.wsel'), sub = g('#sheetForm .btn-primary');
      const bigs = Array.from(sh.querySelectorAll('.ev-dbig')).map(e => ({t: e.textContent.trim(), fs: getComputedStyle(e).fontSize, fw: getComputedStyle(e).fontWeight}));
      const tilde = sh.querySelector('.ev-tilde');
      return {open: document.getElementById('sheetWrap').classList.contains('open'),
              chk: !!chk, chkColor: cs ? cs.color : null, chkSvg: !!(chk && chk.querySelector('svg')),
              types: sh.querySelectorAll('select[name="type"]').length,
              typeLabel: Array.from(sh.querySelectorAll('.f > label')).map(l => l.textContent.trim()),
              order2: (() => { const t = sh.querySelector('.ev-title'), c = sh.querySelector('.sw-row');
                return !!(t && c) && t.getBoundingClientRect().bottom <= c.getBoundingClientRect().top + 1; })(),
              titleStyle: (() => { const cs = getComputedStyle(sh.querySelector('.ev-title'));
                return {bt: cs.borderTopWidth, bl: cs.borderLeftWidth, bb: cs.borderBottomWidth, r: cs.borderTopLeftRadius,
                        fs: cs.fontSize}; })(),
              swSize: (() => { const b = sh.querySelector('.sw-row .sw');
                const r = b.getBoundingClientRect(); const cs = getComputedStyle(b);
                return {w: Math.round(r.width), h: Math.round(r.height), radius: cs.borderTopLeftRadius}; })(),
              timeLabels: Array.from(sh.querySelectorAll('.ev-time-btn')).map(b => b.textContent.trim()),
              hasStartEnd: Array.from(sh.querySelectorAll('label')).map(l => l.textContent.trim()).join('|'),
              note: sh.innerText.indexOf('여러 날') >= 0,
              whoLabel: Array.from(sh.querySelectorAll('.f > label, .set-lbl')).map(l => l.textContent.trim()).indexOf('담당') >= 0,
              sw: sh.querySelectorAll('[data-sw="evColor"] .sw').length,
              reset: !!sh.querySelector('.cp-reset[data-act="pickEvColor"]'),
              bottomBtn: !!(sh.querySelector('#sheetForm .btn-primary')
                            && sh.querySelector('#sheetForm .btn-primary').textContent.trim() === '추가하기'),
              hdText: hv ? hv.innerText.replace(/\s+/g, ' ').trim() : null,
              bigs, tildeFs: tilde ? getComputedStyle(tilde).fontSize : null, tildeTxt: tilde ? tilde.textContent.trim() : null,
              who3: sh.querySelectorAll('.wsel .wopt').length,
              times: sh.querySelectorAll('.ev-time-btn').length,
              order: [cp, ti, when, who, sub].every(Boolean) && ti.top < cp.top && cp.top < when.top
                     && when.bottom <= who.top + 1 && who.top < sub.top};
    })()""")
    check("일정 시트 열림", ef["open"], ef)
    check("헤더에 검정 ✓ 저장 아이콘", ef["chk"] and ef["chkSvg"] and ef["chkColor"] == "rgb(9, 9, 11)", (ef["chk"], ef["chkColor"]))
    check("아래 「추가하기」 버튼도 유지", ef["bottomBtn"])
    check("종류(여행·데이트) 삭제", ef["types"] == 0 and "종류" not in "".join(ef["typeLabel"]), ef["typeLabel"])
    check("시작일·종료일·담당 라벨 삭제", all(k not in ef["hasStartEnd"] for k in ("시작일", "종료일"))
          and not ef["whoLabel"], (ef["hasStartEnd"], ef["whoLabel"]))
    check("여러 날 설명 문구 삭제", not ef["note"], ef["note"])
    check("컬러 12색 + 기본", ef["sw"] == 12 and ef["reset"], (ef["sw"], ef["reset"]))
    check("순서: 제목 → 컬러 → 날짜 → 함께/나/준영 → 추가하기", ef["order"] and ef["order2"] and ef["who3"] == 3,
          (ef["order"], ef["order2"], ef["who3"]))
    check("제목 칸은 밑줄만 (네모 테두리 없음)", ef["titleStyle"]["bt"] == "0px" and ef["titleStyle"]["bl"] == "0px"
          and ef["titleStyle"]["bb"] != "0px" and ef["titleStyle"]["r"] == "0px", ef["titleStyle"])
    # v22: 스와치를 20px 로 한 단계 더 줄였어요 (모양은 그대로 동그라미)
    check("컬러는 작은 동그라미(20px·둥글게)", ef["swSize"]["w"] <= 22 and ef["swSize"]["h"] <= 22
          and ("50%" in ef["swSize"]["radius"] or "999px" in ef["swSize"]["radius"]), ef["swSize"])
    # v28: 시간 설정 칸을 없애고 날짜 아래에 요일을 크게 — 시간 버튼은 하나도 없어요
    check("v28: 시간 설정 버튼 없음", ef["timeLabels"] == [] and ef["times"] == 0, (ef["timeLabels"], ef["times"]))
    check("큰 날짜 두 개 + 가운데 ~", len(ef["bigs"]) == 2 and ef["tildeTxt"] == "~", (ef["bigs"], ef["tildeTxt"]))
    import re as _re
    # v28: 날짜는 «26.11.17», 요일은 그 아래 «화요일» — 날짜 글씨도 19px 로 커짐
    check("날짜는 26.11.17 형식·더 큰 글씨(19px)", all(_re.match(r"^\d{2}\.\d{2}\.\d{2}$", b["t"]) for b in ef["bigs"])
          and all(b["fs"] == "19px" and b["fw"] == "800" for b in ef["bigs"]), ef["bigs"])
    dw = page.evaluate("""(() => {
      const in0 = document.querySelector('#sheet .js-evdate[data-side="start"]');
      const names = ['일요일','월요일','화요일','수요일','목요일','금요일','토요일'];
      const d = new Date(in0.value + 'T00:00:00');
      return {want: names[d.getDay()], txt: Array.from(document.querySelectorAll('#sheet .ev-dow')).map(e => e.textContent.trim())};
    })()""")
    check("날짜 아래에 요일 전체 이름", dw["txt"] == [dw["want"], dw["want"]], dw)
    check("~ 도 큼직하게", ef["tildeFs"] and float(ef["tildeFs"].replace("px", "")) >= 20, ef["tildeFs"])
    til = page.evaluate("""(() => { const t = document.querySelector('#sheet .ev-tilde').getBoundingClientRect();
      const l = document.querySelector('#sheet .ev-side').getBoundingClientRect();
      return {tMid: t.top + t.height / 2, lMid: l.top + l.height / 2}; })()""")
    check("물결이 두 날짜 사이 세로 가운데", abs(til["tMid"] - til["lMid"]) <= 2, til)
    check("시간 버튼·시간 칸이 사라짐", ef["times"] == 0, ef["times"])

    # 색·제목·날짜·시간을 넣고 헤더 ✓ 로 저장
    page.locator('#sheet [data-sw="evColor"] .sw[data-color="#80A4AA"]').click()
    page.wait_for_timeout(250)
    page.fill('#sheetForm input[name="title"]', "치과 예약 (저녁)")
    page.locator('#sheet .js-evdate[data-side="start"]').fill("2026-11-22")
    page.wait_for_timeout(250)
    dbig = page.evaluate("document.querySelector('#sheet .ev-dbig[data-dbig=\"start\"]').textContent.trim()")
    check("날짜를 고르면 큰 글씨도 바뀜", dbig == "26.11.22", dbig)
    ddow = page.evaluate("document.querySelector('#sheet .ev-dow[data-dow=\"start\"]').textContent.trim()")
    check("날짜를 고르면 요일도 함께 바뀜", ddow == "일요일", ddow)
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(SHOT, "event-sheet-v21.png"))
    page.locator("#evSave").click()
    page.wait_for_timeout(700)
    ev = page.evaluate("""(() => {
      const list = window.__app.state.events.filter(e => e.title === '치과 예약 (저녁)');
      const e0 = list[0] || {};
      const rows = Array.from(document.querySelectorAll('#s-cal .daylist .ev'));
      const row = rows.filter(r => r.innerText.indexOf('치과 예약 (저녁)') >= 0)[0];
      return {n: list.length, date: e0.date, time: e0.time, color: e0.color, who: e0.who,
              bar: row ? getComputedStyle(row.querySelector('.bar')).backgroundColor : null,
              meta: row && row.querySelector('.m') ? row.querySelector('.m').textContent.trim() : null,
              mCount: document.querySelectorAll('#s-cal .daylist .ev .m').length,
              open: document.getElementById('sheetWrap').classList.contains('open'),
              sel: window.__app.state.ui.selDate};
    })()""")
    check("헤더 ✓ 로 일정 저장", ev["n"] == 1 and not ev["open"], ev)
    check("고른 색이 그대로 저장 (시간 없이)", ev["color"] == "#80A4AA" and ev["time"] == "", ev)
    check("일정 띠가 고른 컬러", ev["bar"] == "rgb(128, 164, 170)", ev["bar"])
    check("일정 줄에 작은 날짜·종일 표시 없음", ev["meta"] is None and ev["mCount"] == 0, (ev["meta"], ev["mCount"]))

    # 색을 안 고르면 담당자 색으로 (아래 「추가하기」로 저장)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(500)
    page.fill('#sheetForm input[name="title"]', "색 없이 저장")
    page.wait_for_timeout(150)
    page.locator("#sheetForm .btn-primary").click()
    page.wait_for_timeout(700)
    ev2 = page.evaluate("""(() => {
      const e0 = (window.__app.state.events.filter(e => e.title === '색 없이 저장')[0]) || {};
      const rows = Array.from(document.querySelectorAll('#s-cal .daylist .ev'));
      const row = rows.filter(r => r.innerText.indexOf('색 없이 저장') >= 0)[0];
      return {color: e0.color, who: e0.who, time: e0.time, endTime: e0.endTime,
              bar: row ? getComputedStyle(row.querySelector('.bar')).backgroundColor : null,
              meta: row && row.querySelector('.m') ? row.querySelector('.m').textContent.trim() : null};
    })()""")
    check("색을 안 고르면 담당자 색", ev2["color"] == "" and ev2["bar"] not in (None, ""), ev2)
    check("일정 줄엔 작은 표시 없음", ev2["meta"] is None, ev2["meta"])
    check("v28: 새 일정은 시간 없이 저장", (ev2.get("time") or "") == "", (ev2.get("time"), ev2.get("endTime")))
    page.wait_for_timeout(1200)
    page.screenshot(path=os.path.join(SHOT, "calendar-event-v21.png"))

    # ---------------- 7-7. 사진첩 상단은 제목 없이 + 버튼만 ----------------
    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(700)
    ph = page.evaluate("""(() => {
      const hd = document.querySelector('#s-photo .hdr');
      const add = document.querySelector('#s-photo [data-act="addPhoto"]');
      const r = hd.getBoundingClientRect();
      return {h1: document.querySelectorAll('#s-photo .hdr h1').length,
              sub: document.querySelectorAll('#s-photo .hdr .sub').length,
              txt: hd.innerText.replace(/\s+/g, ' ').trim(),
              add: !!add, addRight: window.innerWidth - add.getBoundingClientRect().right,
              h: r.height, firstPola: !!document.querySelector('#s-photo .pola')};
    })()""")
    check("사진첩 제목·「N장의 순간」 삭제", ph["h1"] == 0 and ph["sub"] == 0 and "순간" not in ph["txt"], ph)
    check("사진 추가 + 버튼만 남음", ph["add"] and ph["addRight"] <= 22 and ph["firstPola"], ph)
    check("머리줄 높이 적당(60px 이하)", ph["h"] <= 60, ph["h"])
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "photo-v21.png"))

    # ---------------- 7-8. 라이트 모드는 완전한 순백 ----------------
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(700)
    wh = page.evaluate("""(() => {
      const cs = getComputedStyle(document.body);
      const root = getComputedStyle(document.documentElement);
      const phone = getComputedStyle(document.querySelector('.phone'));
      const screen = getComputedStyle(document.querySelector('#s-home'));
      const tb = getComputedStyle(document.querySelector('.tabbar'));
      return {body: cs.backgroundColor, phone: phone.backgroundColor, screen: screen.backgroundColor,
              tabbar: tb.backgroundColor, bg: root.getPropertyValue('--bg').trim(),
              surface: root.getPropertyValue('--surface').trim(), surface2: root.getPropertyValue('--surface-2').trim(),
              line: root.getPropertyValue('--line').trim()};
    })()""")
    check("바탕이 완전한 순백(#FFFFFF)", wh["bg"].upper() == "#FFFFFF" and wh["body"] == "rgb(255, 255, 255)"
          and wh["phone"] == "rgb(255, 255, 255)"
          and wh["screen"] in ("rgb(255, 255, 255)", "rgba(0, 0, 0, 0)"), wh)
    check("탭바도 순백 계열", wh["tabbar"].startswith("rgba(255, 255, 255"), wh["tabbar"])
    check("카드 회색은 쿨한 뉴트럴(#F5F5F7)", wh["surface2"].upper() == "#F5F5F7", wh["surface2"])
    page.screenshot(path=os.path.join(SHOT, "home-v21.png"))

    # ---------------- 8. 다른 화면은 그대로 ----------------
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(450)
    check("홈 브랜드 이름 그대로", page.locator("#s-home .brand b").inner_text().strip() == "투로그")
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(450)
    check("노트 제목 줄 그대로", "노트" in page.locator("#s-diary .hdr h1").inner_text())

    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
