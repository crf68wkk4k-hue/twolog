"""투로그 v37 확인 — 노트 상단 ＋ 테두리 제거 · 사진첩 정사각형 3열 · 사진 달력 정사각 칸·상하 넘김.

1) 버전: sw.js 캐시 twolog-v48 · APP_VERSION v37 · My 탭 「버전 v48」
2) 노트 맨 윗줄 ＋
   - 동그란 테두리·바탕 없이 ＋ 아이콘만 (border 0 · background 투명 · 모서리 각짐)
   - 터치 영역은 44x44, 아이콘 22px, 오른쪽·높이는 예전 ＋ 자리 그대로
   - 누르면 「새 카테고리」 시트가 열림
   - 다른 화면의 둥근 버튼(사진첩 +·달력)은 테두리·38px 그대로 — 영향 없음
3) 사진첩 기본 화면 — 날짜마다 정사각형 사진 3열
   - 폴라로이드 틀(흰 프레임·기울기·그림자·턱) 없음: padding 0 · transform none · shadow none
   - 사진 칸은 정사각(aspect-ratio 1/1)이고 칸을 꽉 채움(object-fit cover)
   - 한 줄 3장 · 카드끼리 겹치지 않고 8px 간격 · 가로 넘침 없음
   - 캡션이 있으면 사진 아래 한 줄 · 캡션 색을 고른 사진은 그 색 그대로
   - 하루 3장까지·넘치면 +N · 눌러서 크게 보기 그대로
   - 이번 달 사진만 · 가장 최근 날짜부터 3일치만 · 「{월}월의 순간」 같은 제목 없음
   - 날짜 옆에는 3장을 넘길 때만 「+N장」（3장 이하는 비움）
4) 사진 달력 — 정사각 칸 + 위아래로 달 넘기기
   - 7칸 달력의 날짜 칸이 정사각형(폭=높이)이고 그날 사진이 칸을 꽉 채움
   - 화살표는 위/아래(⌄ 아래=지난 달 · ⌃ 위=다음 달)
   - 위로 밀면 다음 달, 아래로 밀면 지난 달 · 좌우로 밀면 그대로
   - 날짜를 누르면 그날 사진 크게 보기
5) 사진첩에 들어올 때는 늘 기본 사진 화면
   - 달력 보기를 열어 둔 채 다른 탭에 갔다 돌아오면 목록으로
   - 달력 보기를 열어 둔 채 새로고침해도 사진첩은 목록으로
6) 다크 모드에서도 ＋ 보임 · 사진 칸 정사각 그대로
7) 콘솔/페이지 오류 0건

    python3 tests/v37.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import functools, http.server, os, re, socketserver, sys, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
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


def new_ctx(browser):
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True,
                              has_touch=True, device_scale_factor=2)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    return ctx


def watch(page, bucket):
    page.on("pageerror", lambda e: bucket.append("pageerror: " + str(e)))
    page.on("console", lambda m: bucket.append("console: " + m.text) if m.type == "error" else None)


def tab(page, idx, wait=520):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def swipe(page, sel, from_y, to_y, x=200):
    """세로로 미는 제스처 한 번 (터치 이벤트)."""
    page.evaluate("""([sel, y1, y2, x]) => {
      const el = document.querySelector(sel);
      const t = (y) => new Touch({identifier: 1, target: el, clientX: x, clientY: y});
      el.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, cancelable: true,
        touches: [t(y1)], changedTouches: [t(y1)]}));
      el.dispatchEvent(new TouchEvent('touchend', {bubbles: true, cancelable: true,
        touches: [], changedTouches: [t(y2)]}));
    }""", [sel, from_y, to_y, x])
    page.wait_for_timeout(520)


def swipe_h(page, sel, from_x, to_x, y=400):
    page.evaluate("""([sel, x1, x2, y]) => {
      const el = document.querySelector(sel);
      const t = (x) => new Touch({identifier: 1, target: el, clientX: x, clientY: y});
      el.dispatchEvent(new TouchEvent('touchstart', {bubbles: true, cancelable: true,
        touches: [t(x1)], changedTouches: [t(x1)]}));
      el.dispatchEvent(new TouchEvent('touchend', {bubbles: true, cancelable: true,
        touches: [], changedTouches: [t(x2)]}));
    }""", [sel, from_x, to_x, y])
    page.wait_for_timeout(520)


def month_text(page):
    return page.evaluate("document.querySelector('#s-photo .pcal-ym').textContent.trim()")


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 0. 로컬 모드 + 예시 데이터로 시작
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs = []
    watch(page, errs)

    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    seed_state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", seed_state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)

    # ==================================================================
    # 1. 버전
    # ==================================================================
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    css = page.request.get(URL + "styles.css").text()
    check("sw.js 캐시 버전 twolog-v48", 'const VERSION = "twolog-v48"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v37", 'var APP_VERSION = "v48"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v48", 'const SHELL = "shell-" + VERSION' in sw)

    tab(page, 4, 600)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v48」", ver.strip() == "버전 v48", ver)

    # ==================================================================
    # 2. 노트 맨 윗줄 ＋ — 테두리 없이 아이콘만
    # ==================================================================
    tab(page, 2, 650)
    nb = page.evaluate("""() => {
      const b = document.querySelector('#s-diary .hdr .note-add');
      if (!b) return {ok: false};
      const r = b.getBoundingClientRect(), cs = getComputedStyle(b);
      const s = b.querySelector('svg');
      const sr = s ? s.getBoundingClientRect() : null;
      const h1 = document.querySelector('#s-diary .note-h1').getBoundingClientRect();
      return {ok: true, act: b.getAttribute('data-act'), label: b.getAttribute('aria-label'),
              w: Math.round(r.width), h: Math.round(r.height),
              right: Math.round(window.innerWidth - r.right),
              bw: cs.borderTopWidth, bs: cs.borderTopStyle, radius: cs.borderTopLeftRadius,
              bg: cs.backgroundColor, shadow: cs.boxShadow,
              svg: !!s, svgD: s ? (s.querySelector('path') || {}).getAttribute && s.querySelector('path').getAttribute('d') : '',
              svgW: sr ? Math.round(sr.width) : 0,
              svgRight: sr ? Math.round(window.innerWidth - sr.right) : 0,
              svgCY: sr ? Math.round(sr.top + sr.height / 2) : 0,
              svgCX: sr ? Math.round(sr.left + sr.width / 2) : 0,
              boxCY: Math.round(r.top + r.height / 2), boxCX: Math.round(r.left + r.width / 2),
              h1CY: Math.round(h1.top + h1.height / 2),
              headerBtns: document.querySelectorAll('#s-diary .hdr-acts button').length,
              hasRound: b.classList.contains('round-btn')};
    }""")
    check("노트 맨 윗줄 ＋ 버튼이 있음", nb.get("ok") and nb.get("act") == "newList", nb)
    check("＋ 버튼에 테두리 없음", nb.get("bw") in ("0px", "0") or nb.get("bs") == "none",
          (nb.get("bw"), nb.get("bs")))
    check("＋ 버튼에 바탕색 없음(투명)", nb.get("bg") in ("rgba(0, 0, 0, 0)", "transparent"), nb.get("bg"))
    check("＋ 버튼에 점선·원형 없음(모서리 각짐)", nb.get("radius") in ("0px", "0"), nb.get("radius"))
    check("＋ 버튼에 그림자 없음", nb.get("shadow") in ("none", ""), nb.get("shadow"))
    check("＋ 아이콘만 (＋ 모양 path)", nb.get("svg") and "M12 5.5v13" in str(nb.get("svgD")), nb.get("svgD"))
    check("터치 영역 44x44", nb.get("w") == 44 and nb.get("h") == 44, (nb.get("w"), nb.get("h")))
    check("＋ 아이콘 22px · 버튼 가운데", nb.get("svgW") == 22
          and abs(nb.get("svgCX") - nb.get("boxCX")) <= 1 and abs(nb.get("svgCY") - nb.get("boxCY")) <= 1,
          (nb.get("svgW"), nb.get("svgCX"), nb.get("boxCX"), nb.get("svgCY"), nb.get("boxCY")))
    check("＋ 는 제목(📖 노트)과 같은 줄", abs(nb.get("svgCY") - nb.get("h1CY")) <= 12,
          (nb.get("svgCY"), nb.get("h1CY")))
    check("＋ 아이콘 오른쪽 여백 26~30px", 26 <= nb.get("svgRight") <= 30, nb.get("svgRight"))
    check("맨 윗줄 오른쪽 버튼은 ＋ 하나뿐", nb.get("headerBtns") == 1, nb.get("headerBtns"))

    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(600)
    sheet = page.evaluate("""() => ({
      open: document.getElementById('sheetWrap').classList.contains('open'),
      title: (document.querySelector('#sheet .sheet-hd h2') || {}).textContent || '',
      name: !!document.querySelector('#sheet input[name="title"]')})""")
    check("＋ 를 누르면 「새 카테고리」 시트", sheet["open"] and "새 카테고리" in sheet["title"] and sheet["name"], sheet)
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)
    page.screenshot(path=os.path.join(SHOT, "note-v37.png"))

    # 다른 화면 버튼은 그대로 — 사진첩 +·달력은 테두리 있는 38px
    tab(page, 3, 700)
    others = page.evaluate("""() => Array.from(document.querySelectorAll('#s-photo .hdr-acts .round-btn')).map(b => {
      const cs = getComputedStyle(b), r = b.getBoundingClientRect();
      return {act: b.getAttribute('data-act'), bw: cs.borderTopWidth, radius: cs.borderTopLeftRadius,
              w: Math.round(r.width), h: Math.round(r.height)};
    })""")
    check("사진첩 검색·달력·＋ 버튼은 예전 그대로(테두리 1px·38px)",
          len(others) == 3 and all(o["bw"] == "1px" and o["w"] == 38 and o["h"] == 38 for o in others), others)

    # ==================================================================
    # 3. 사진첩 기본 화면 — 날짜마다 정사각형 사진 3열
    # ==================================================================
    ph = page.evaluate("""() => {
      const els = Array.from(document.querySelectorAll('#s-photo .pola'));
      if (!els.length) return {ok: false};
      const p = els[0], pic = p.querySelector('.pola-pic'), chin = p.querySelector('.pola-chin');
      const r = e => e.getBoundingClientRect();
      const cs = getComputedStyle(p), pcs = getComputedStyle(pic);
      const grid = document.querySelector('#s-photo .polas');
      const gs = getComputedStyle(grid);
      const imgs = els.map(e => e.querySelector('.pola-pic img, .pola-pic svg'));
      return {ok: true, pcal: !!document.querySelector('#s-photo .pcal'),
        n: els.length, cols: gs.gridTemplateColumns.split(' ').length, colGap: parseFloat(gs.columnGap),
        rowGap: parseFloat(gs.rowGap),
        pad: [cs.paddingTop, cs.paddingLeft, cs.paddingBottom],
        shadow: cs.boxShadow, transform: cs.transform, bg: cs.backgroundColor,
        radius: cs.borderTopLeftRadius,
        cardW: r(p).width, picW: r(pic).width, picH: r(pic).height,
        picRight: r(pic).right, cardRight: r(p).right,
        picTop: r(pic).top, cardTop: r(p).top,
        fit: pcs.objectFit || getComputedStyle(imgs[0]).objectFit,
        imgW: imgs[0] ? r(imgs[0]).width : 0, imgH: imgs[0] ? r(imgs[0]).height : 0,
        allImg: imgs.every(Boolean),
        chinH: chin ? Math.round(r(chin).height) : 0,
        chinText: chin ? chin.textContent.trim() : null,
        chinBg: chin ? getComputedStyle(chin).backgroundColor : null,
        gaps: els.length > 1 ? Math.round(r(els[1]).left - r(els[0]).right) : null,
        rows: new Set(els.map(e => Math.round(r(e).top))).size,
        overflow: document.querySelector('#s-photo').scrollWidth - document.querySelector('#s-photo').clientWidth,
        more: (document.querySelector('#s-photo .pola-more') || {}).textContent || null,
        days: Array.from(document.querySelectorAll('#s-photo .pday')).map(d => d.querySelectorAll('.pola').length)};
    }""")
    check("사진첩에 들어오면 기본 사진 화면", ph.get("ok") and ph.get("pcal") is False, ph.get("pcal"))
    img_cover = page.evaluate("""() => {
      const i = document.querySelector('#s-photo .pola .pola-pic img');
      return i ? getComputedStyle(i).objectFit === 'cover' : true;
    }""")
    check("한 줄에 정사각형 사진 3장", ph.get("cols") == 3 and ph.get("n") >= 3, (ph.get("cols"), ph.get("n")))
    check("사진 칸이 정사각형", abs(ph.get("picW") - ph.get("picH")) <= 0.6, (ph.get("picW"), ph.get("picH")))
    check("사진이 칸을 꽉 채움 (테두리 여백 없음)",
          abs(ph.get("picW") - ph.get("cardW")) <= 0.6 and abs(ph.get("picRight") - ph.get("cardRight")) <= 0.6,
          (ph.get("cardW"), ph.get("picW"), ph.get("picRight"), ph.get("cardRight")))
    check("사진 한 칸 100px 이상 (3열)", ph.get("picW") >= 100, ph.get("picW"))
    check("이미지가 cover 로 채워짐", img_cover and "object-fit:cover" in css, (img_cover, css.count("object-fit:cover")))
    check("폴라로이드 흰 프레임·턱 없음 (padding 0)",
          all(str(x) in ("0px", "0") for x in ph.get("pad", [])), ph.get("pad"))
    check("기울기·그림자 없음", ph.get("transform") in ("none", "matrix(1, 0, 0, 1, 0, 0)")
          and ph.get("shadow") == "none", (ph.get("transform"), ph.get("shadow")))
    check("카드끼리 겹치지 않고 얇게 띄워짐(간격 3px)", ph.get("gaps") is not None and abs(ph.get("gaps") - 3) <= 1,
          ph.get("gaps"))
    check("사진첩 가로 넘침 없음", ph.get("overflow") <= 1, ph.get("overflow"))
    check("사진이 모두 그려짐", ph.get("allImg") is True and ph.get("imgW", 0) > 0, (ph.get("allImg"), ph.get("imgW")))
    # v40: 사진 아래 «캡션 줄»은 없앴어요 — 사진만 보입니다 (예전 캡션 글씨는 저장돼 있어도 안 보여요)
    check("사진 아래 캡션 줄 없음 (v40)", (ph.get("chinText") or "") == "" and not ph.get("chinH"),
          (ph.get("chinText"), ph.get("chinH")))
    check("캡션 색도 사진 아래에 칠해지지 않음", ph.get("chinBg") in (None, "", "rgba(0, 0, 0, 0)"),
          ph.get("chinBg"))
    check("하루 3장·넘치면 +N 그대로", all(d <= 3 for d in ph.get("days", [])) and ph.get("more") == "+3",
          (ph.get("days"), ph.get("more")))

    # v37: 이번 달 사진만 · 최근 3일치만 · 날짜 옆 「+N장」
    scope = page.evaluate("""() => {
      const days = Array.from(document.querySelectorAll('#s-photo .pday'));
      const heads = days.map(d => { const c = d.querySelector('.pday-hd .c');
        return {date: d.querySelector('.pday-hd').innerText.replace(/\\n/g, ' ').trim(),
                meta: c ? c.textContent.trim() : null,
                n: d.querySelectorAll('.pola').length}; });
      const sc = document.querySelector('#s-photo').innerText;
      return {todayYm: (new Date()).toISOString().slice(0, 7), days: days.length, heads: heads,
              moment: sc.indexOf('월의 순간') >= 0};
    }""")
    # v39: 3일 제한을 풀어 사진이 있는 날을 모두 보여 줍니다
    check("사진이 있는 날짜가 모두 보임", scope["days"] >= 1, scope["days"])
    # (날짜가 오늘 기준으로 밀리므로 «이번 달이 아닌 날짜» 가 있으면 통과 — 예전엔 10월 24일·8월 8일을 찾았어요)
    def _other_month(h):
        mm = re.match(r"(\d+)월", h["date"] or "")
        return bool(mm) and int(mm.group(1)) != int(time.strftime("%m"))
    check("지난 달 사진도 기본 화면에 함께 보임", any(_other_month(h) for h in scope["heads"]), scope["heads"])
    check("「{월}월의 순간」 제목 없음", scope["moment"] is False, scope["moment"])
    # v40: 장수는 날짜 줄이 아니라 «마지막 사진 오른쪽 아래» 작은 +N 배지로만
    check("3장을 넘는 날은 마지막 사진에 작은 +N", ph.get("more") == "+3" and all(h["meta"] is None for h in scope["heads"]),
          (ph.get("more"), scope["heads"]))

    # 날짜 묶음을 여러 날로 늘리고 확인 — 최근 3일치만, 3장 이하 날은 장수 표기 없음
    page.evaluate("""() => {
      const st = window.__app.state;
      const d = new Date();
      const day = (n) => { const x = new Date(d.getFullYear(), d.getMonth(), d.getDate() - n);
        return x.getFullYear() + '-' + String(x.getMonth() + 1).padStart(2, '0') + '-' + String(x.getDate()).padStart(2, '0'); };
      for (let i = 1; i <= 4; i++) {
        for (let j = 0; j < 2; j++) {
          st.photos.push({id: 'v37-' + i + '-' + j, date: day(i), album: '', title: '검사' + i + j,
                          art: j, capBg: ''});
        }
      }
      window.__app.rerender();
    }""")
    page.wait_for_timeout(700)
    lim = page.evaluate("""() => {
      const days = Array.from(document.querySelectorAll('#s-photo .pday'));
      const st = window.__app.state.photos;
      return {n: days.length, heads: days.map(d => { const c = d.querySelector('.pday-hd .c');
        const day = d.querySelector('.pday-hd').getAttribute('data-date');
        return {date: [...d.querySelector('.pday-hd').children].map(x => x.textContent.trim()).filter(Boolean).join(' '),
                meta: c ? c.textContent.trim() : null, count: d.querySelectorAll('.pola').length,
                total: st.filter(p => String(p.date || '').slice(0, 10) === day).length}; })};
    }""")
    check("날짜 묶음은 사진이 있는 날 전부 (3일 제한 없음, v39)", lim["n"] >= 7, lim["n"])
    # v39: 3일 제한이 없어져 3장을 넘는 날도 함께 보입니다 — «그날 전체 3장 이하»인 날만 표기가 비어 있어야
    check("날짜 줄에는 장수 표기가 없음 (v40: 마지막 사진 +N 만)",
          all(h["meta"] is None for h in lim["heads"]), lim["heads"])
    today_d = time.localtime()
    yday = time.strftime("%Y-%m-%d", time.localtime(time.time() - 86400))
    # v39: 목록은 예전 날짜가 위 · 가장 최근 날짜가 아래 → 마지막 줄이 어제
    check("가장 최근 날(어제)이 맨 아래", lim["heads"] and ("어제" in lim["heads"][-1]["date"]
                                                 or yday[5:7].lstrip("0") + "월" in lim["heads"][-1]["date"]),
          lim["heads"][-1:])
    page.screenshot(path=os.path.join(SHOT, "photo-v37-3days.png"))

    # 예시 데이터로 되돌림 (검사용으로 넣은 사진만 걱기)
    page.evaluate("""() => {
      const st = window.__app.state;
      st.photos = st.photos.filter(p => String(p.id).indexOf('v37-') !== 0);
      window.__app.rerender();
    }""")
    page.wait_for_timeout(700)
    page.screenshot(path=os.path.join(SHOT, "photo-v37.png"))
    page.screenshot(path=os.path.join(SHOT, "photo-v37-full.png"), full_page=True)

    # v39: 목록은 예전 → 최근 순 — 사진이 가장 많은 «최근 날짜»(맨 아래)를 봅니다
    first_title = page.evaluate("(document.querySelector('#s-photo .pday:last-child .pola .pola-chin') || {}).textContent || ''")
    page.locator("#s-photo .pola").last.click()
    page.wait_for_timeout(650)
    # v38: 날짜 모아보기가 먼저 → 사진을 누르면 크게 보기
    page.locator("#s-photo .dg-cell").first.click()
    page.wait_for_timeout(650)
    pv = page.evaluate("""() => { const v = document.querySelector('#sheet .pview');
      return {open: !!v, h: v ? Math.round(v.getBoundingClientRect().height) : 0,
              img: !!(v && v.querySelector('img, svg')),
              slides: document.querySelectorAll('#sheet .pv40-slide').length}; }""")
    check("정사각 사진을 누르면 크게 보기", pv["open"] and pv["img"] and pv["h"] > 200, pv)
    # v40: 크게 보기는 «사진만» — 넘기기는 옆으로 밀기(가로 스냅)로 해요
    check("같은 날 사진이 옆으로 이어짐 (넘기기)", pv["slides"] == 6, pv["slides"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)
    page.locator('#s-photo [data-act="photoDayBack"]').click()   # v38: 모아보기 → 목록
    page.wait_for_timeout(450)

    # ==================================================================
    # 4. 사진 달력 — 세로로 이어진 달력 + 정사각 칸 (v38)
    # ==================================================================
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(800)
    cal = page.evaluate("""() => {
      /* v39: 앞뒤 12개월이 이어져 첫 달에는 사진이 없을 수 있어 «이번 달» 격자에서 잽니다 */
      const g = document.querySelector('#s-photo .pcal-m[data-ym="' + (new Date()).getFullYear() + '-' +
        String((new Date()).getMonth() + 1).padStart(2, '0') + '"] .pcal-grid') || document.querySelector('#s-photo .pcal-grid');
      if (!g) return {ok: false};
      const cells = Array.from(g.querySelectorAll('.pcell'));
      const days = cells.filter(c => !c.classList.contains('blank'));
      const has = days.filter(c => c.classList.contains('has'));
      const one = has[0] || days[0];
      const r = one.getBoundingClientRect();
      const img = one.querySelector('img, svg');
      const ms = [...document.querySelectorAll('#s-photo .pcal-m')];
      const box = document.getElementById('screens');
      const cur = document.querySelector('#s-photo .pcal-m[data-ym="2026-11"]');
      const cr = cur ? cur.getBoundingClientRect() : null;
      const br = box.getBoundingClientRect();
      const ym = document.querySelector('#s-photo .pcal-ym');
      return {ok: true, cols: getComputedStyle(g).gridTemplateColumns.split(' ').length,
        rows: Number(g.getAttribute('data-rows')),
        cellW: r.width, cellH: r.height,
        imgW: img ? img.getBoundingClientRect().width : 0,
        imgH: img ? img.getBoundingClientRect().height : 0,
        hasN: has.length,
        months: ms.length,
        monthsAbove: ms.filter(m => m.getAttribute('data-ym') < '2026-11').length,
        monthsBelow: ms.filter(m => m.getAttribute('data-ym') > '2026-11').length,
        curTop: cr ? Math.round(cr.top - br.top) : null,
        boxH: Math.round(br.height),
        nav: document.querySelectorAll('#s-photo .pcal-nav, #s-photo .cal-arrow').length,
        ymCenter: ym ? Math.abs((ym.getBoundingClientRect().left + ym.getBoundingClientRect().right) / 2 - 195) < 6 : false,
        gridRight: Math.round(window.innerWidth - g.getBoundingClientRect().right)};
    }""")
    check("달력 보기로 전환", cal.get("ok") and cal.get("cols") == 7, cal.get("cols"))
    check("날짜 칸이 정사각형", abs(cal.get("cellW", 0) - cal.get("cellH", 0)) <= 0.6,
          (cal.get("cellW"), cal.get("cellH")))
    check("칸 안 사진도 정사각으로 꽉 참", abs(cal.get("imgW", 0) - cal.get("imgH", 0)) <= 0.6
          and abs(cal.get("imgW", 0) - cal.get("cellW", 0)) <= 0.8,
          (cal.get("imgW"), cal.get("imgH"), cal.get("cellW")))
    check("달력은 여러 달이 세로로 이어짐", cal.get("months", 0) >= 2
          and cal.get("monthsAbove", 0) >= 1 and cal.get("monthsBelow", 0) >= 1,
          (cal.get("months"), cal.get("monthsAbove"), cal.get("monthsBelow")))
    check("이번 달이 화면 가운데쯤에 맞춰 열림",
          cal.get("curTop") is not None and cal["boxH"] * 0.18 <= cal["curTop"] <= cal["boxH"] * 0.62,
          (cal.get("curTop"), cal.get("boxH")))
    check("위·아래 화살표는 없음", cal.get("nav") == 0, cal.get("nav"))
    check("달 제목은 가운데", cal.get("ymCenter") is True)
    page.screenshot(path=os.path.join(SHOT, "photo-cal-v37.png"))

    # 위로 스크롤하면 다음 달이 이어서 보임
    page.evaluate("document.getElementById('screens').scrollTop += 420")
    page.wait_for_timeout(450)
    moved = page.evaluate("""() => { const box = document.getElementById('screens');
      const cur = document.querySelector('#s-photo .pcal-m[data-ym="2026-11"]');
      return {top: Math.round(cur.getBoundingClientRect().top - box.getBoundingClientRect().top)}; }""")
    check("위로 밀면 다음 달이 이어서 보임", moved["top"] < cal["curTop"] - 200, (cal["curTop"], moved["top"]))

    page.locator("#s-photo .pcell.has").first.click()
    page.wait_for_timeout(650)
    # v38: 날짜 칸 → 그날 모아보기 → 사진 → 크게 보기
    day_open = page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      grid: !!document.querySelector('#s-photo .dgrid')})""")
    check("날짜를 누르면 그날 모아보기가 열림", day_open["grid"] and not day_open["open"], day_open)
    page.locator("#s-photo .dg-cell").first.click()
    page.wait_for_timeout(600)
    day_view = page.evaluate("""() => ({open: document.getElementById('sheetWrap').classList.contains('open'),
      view: !!document.querySelector('#sheet .pview')})""")
    check("모아보기에서 사진을 누르면 크게 보기", day_view["open"] and day_view["view"], day_view)
    page.locator("#sheet .pv40-slide").first.click()
    page.wait_for_timeout(400)
    page.locator('#s-photo [data-act="photoDayBack"]').click()
    page.wait_for_timeout(500)

    # ==================================================================
    # 5. 사진첩에 들어올 때는 늘 기본 사진 화면
    # ==================================================================
    check("아직 달력 보기 상태", page.evaluate("!!document.querySelector('#s-photo .pcal')") is True)
    tab(page, 2, 600)      # 노트로 갔다가
    tab(page, 3, 700)      # 사진첩으로 돌아오면
    back = page.evaluate("""() => ({pcal: !!document.querySelector('#s-photo .pcal'),
      polas: document.querySelectorAll('#s-photo .pola').length})""")
    check("다른 탭에 갔다 오면 달력이 아니라 기본 사진 화면",
          back["pcal"] is False and back["polas"] >= 3, back)

    # 달력을 열어 둔 채 새로고침해도 기본 화면부터
    page.locator('#s-photo [data-act="togglePhotoCal"]').click()
    page.wait_for_timeout(600)
    page.wait_for_timeout(400)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)
    tab(page, 3, 700)
    after_reload = page.evaluate("""() => ({pcal: !!document.querySelector('#s-photo .pcal'),
      polas: document.querySelectorAll('#s-photo .pola').length})""")
    check("새로 켜도 사진첩은 기본 사진 화면", after_reload["pcal"] is False and after_reload["polas"] >= 3,
          after_reload)

    # ==================================================================
    # 6. 다크 모드 — ＋ 보임 · 사진 칸 정사각 그대로
    # ==================================================================
    page.evaluate("document.documentElement.setAttribute('data-mode','dark')")
    page.wait_for_timeout(400)
    tab(page, 2, 600)      # 노트에서 ＋ 색과 사진첩 칸을 함께 본다
    note_dark = page.evaluate("""() => {
      const b = document.querySelector('#s-diary .hdr .note-add');
      return {color: b ? getComputedStyle(b).color : null,
              bg: b ? getComputedStyle(b).backgroundColor : null};
    }""")
    tab(page, 3, 700)
    dark = page.evaluate("""() => {
      const pic = document.querySelector('#s-photo .pola .pola-pic');
      const r = pic ? pic.getBoundingClientRect() : null;
      const p = document.querySelector('#s-photo .pola');
      return {picSquare: r ? Math.abs(r.width - r.height) <= 0.6 : false,
              borderless: p ? getComputedStyle(p).borderTopWidth === '0px' : false};
    }""")
    check("다크 모드에서도 ＋ 는 보이는 색", note_dark["color"] not in (None, "rgba(0, 0, 0, 0)")
          and note_dark["bg"] in ("rgba(0, 0, 0, 0)", "transparent", "rgb(17, 17, 17)"), note_dark)
    check("다크 모드에서도 사진 칸 정사각·테두리 없음", dark["picSquare"] is True and dark["borderless"] is True,
          dark)
    page.screenshot(path=os.path.join(SHOT, "photo-v37-dark.png"))
    page.evaluate("document.documentElement.setAttribute('data-mode','light')")
    page.wait_for_timeout(300)

    check("콘솔/페이지 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()
    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
