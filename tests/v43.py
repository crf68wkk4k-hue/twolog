"""투로그 v43 확인 — 모눈 다이어리 손보기.

1) 버전: sw.js 캐시 twolog-v49 · APP_VERSION v49 · My 탭 「버전 v49」
2) 글 상자
   - 종이를 톡 누르면 그 자리에 상자가 생기고 바로 입력(포커스)
   - 이미 있는 상자를 한 번 톡 누르면 «고르기»만 — 입력 포커스가 풀려(blur) 아이폰 키보드가 내려가고
     아래 T 툴바(한 줄: 정렬 · B · S · U · − 크기 + · 색 동그라미)가 보임 — v45
   - 같은 상자를 두 번 톡 누르면 그때 입력(포커스)
   - 오른쪽 위 × 는 누르는 즉시(pointerdown) 그 상자만 삭제 — 새 상자가 생기지 않음 (터치 영역 30px)
   - 빈 「글을 써 보세요」 상자가 쌓이지 않음 (종이를 다시 누르거나 도구를 바꾸면 정리)
3) 사진 자르기
   - 「자르기」를 누르면 사진이 저절로 잘리지 않고, 원본 전체가 화면 안에 크게 보이는 크롭 편집 창
     (테두리 + 모서리·변 손잡이 8개, 전체·취소·적용)
   - 손잡이를 끌면 테두리 크기가 바뀌고, 「적용」을 눌렀을 때만 실제로 잘림 · 「취소」면 원본 그대로
4) 사진 두 손가락 핀치 — 벌리면 커지고 오므리면 작아짐 · 저장·다시 열어도 폭이 그대로
5) 기본 카테고리(탭 속지 「모눈 메모」)에서 쓴 다이어리 — 저장하면 카드에 글·사진이 보이고,
   다시 열어도 그대로 (예전엔 날짜만 남았어요)
6) Supabase 왕복 — 기본 카테고리·사용자 카테고리 모두 notes payload 에 texts·imgs 가 실리고,
   서버에서 다시 읽어도 글·사진이 남음
7) 날짜 모아보기 — 사진 칸마다 붙던 ⋯ 메뉴가 없음 (오른쪽 위 연필 시트에서 모두)
8) 콘솔/페이지 오류 0건

    python3 tests/v43.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def tab(page, idx, wait=520):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def open_new_diary(page):
    page.locator("#s-diary .d41-new").click()
    page.wait_for_timeout(720)


def boxes(page):
    return page.evaluate("document.querySelectorAll('#sheet .d41-tx').length")


def hidden_texts(page):
    return page.evaluate("JSON.parse(document.getElementById('d41TextsIn').value)")


def make_photo(page, name, w=600, h=800):
    durl = page.evaluate("""([w, h]) => { const c = document.createElement('canvas'); c.width = w; c.height = h;
      const x = c.getContext('2d');
      const g = x.createLinearGradient(0, 0, w, h); g.addColorStop(0, '#D69678'); g.addColorStop(1, '#5A6E82');
      x.fillStyle = g; x.fillRect(0, 0, w, h);
      x.fillStyle = '#FFFFFF'; x.font = '64px sans-serif'; x.fillText('PHOTO', w * 0.2, h * 0.5);
      return c.toDataURL('image/jpeg', 0.9); }""", [w, h])
    path = "/tmp/%s" % name
    with open(path, "wb") as f:
        f.write(base64.b64decode(durl.split(",", 1)[1]))
    return path


PINCH_JS = """([spread]) => {
  /* spread > 0 이면 벌리기, < 0 이면 오므리기 — 두 손가락을 가운데에서 바깥/안쪽으로 */
  const el = document.querySelector('#sheet .d41-imgb');
  const paper = document.getElementById('d41Paper');
  const r = el.getBoundingClientRect();
  const cx = r.x + r.width / 2, cy = r.y + r.height / 2;
  const mk = (type, id, x, y) => new PointerEvent(type, {pointerId: id, pointerType: 'touch',
    clientX: x, clientY: y, bubbles: true, cancelable: true});
  const idA = 900 + (spread > 0 ? 1 : 11), idB = idA + 5;
  const step = Math.abs(spread) / 2 / 6;
  const dir = spread > 0 ? -1 : 1;
  el.dispatchEvent(mk('pointerdown', idA, cx - 30, cy));
  el.dispatchEvent(mk('pointerdown', idB, cx + 30, cy));
  for (let i = 1; i <= 6; i++) {
    paper.dispatchEvent(mk('pointermove', idA, cx - 30 + dir * step * i, cy));
    paper.dispatchEvent(mk('pointermove', idB, cx + 30 - dir * step * i, cy));
  }
  const w = JSON.parse(document.getElementById('d41ImgsIn').value)[0].w;
  paper.dispatchEvent(mk('pointerup', idA, cx, cy));
  paper.dispatchEvent(mk('pointerup', idB, cx, cy));
  return w;
}"""


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
    check("예전 v42 문자열이 남아 있지 않음",
          "twolog-v42" not in sw and 'APP_VERSION = "v42"' not in app_js)

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
    # 2. 사용자 카테고리 「그림판」 — 글 상자 ×·빈 상자·한 줄 툴바
    # ==================================================================
    ctxA = new_ctx(browser)
    ctxA.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageA = ctxA.new_page()
    errsA = []
    watch(pageA, errsA)
    pageA.goto(URL + "?demo=1", wait_until="networkidle")
    pageA.wait_for_timeout(700)
    pageA.evaluate("""() => {
      const s = JSON.parse(JSON.stringify(window.__app.state));
      s.lists = (s.lists || []).concat([{id: 'Lc43', title: '그림판', emoji: '', kind: 'memo', items: []}]);
      s.groups = s.groups || {}; s.groups['list:Lc43'] = [];
      localStorage.setItem('twolog:v1:state', JSON.stringify(s));
    }""")
    pageA.goto(URL, wait_until="networkidle")
    pageA.wait_for_timeout(900)
    tab(pageA, 2, 660)
    pageA.locator("#s-diary .lchip", has_text="그림판").first.click()
    pageA.wait_for_timeout(600)
    open_new_diary(pageA)

    pb = pageA.locator("#d41Paper").bounding_box()
    pageA.mouse.click(pb["x"] + 60, pb["y"] + 190)
    pageA.wait_for_timeout(420)
    focusA = pageA.evaluate("document.activeElement ? document.activeElement.className : ''")
    check("종이를 톡 누르면 그 자리에 상자가 생기고 바로 입력(포커스)",
          boxes(pageA) == 1 and "d41-txt" in (focusA or ""), focusA)
    pageA.keyboard.type("첫 번째 글")
    pageA.wait_for_timeout(240)

    # 이미 있는 상자를 한 번 톡 → 고르기만 (키보드 내려감) + T 툴바
    pageA.evaluate("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
    pageA.wait_for_timeout(160)
    tb = pageA.locator("#sheet .d41-tx").first.bounding_box()
    pageA.mouse.click(tb["x"] + 18, tb["y"] + 12)
    pageA.wait_for_timeout(420)
    one = pageA.evaluate("""() => ({focused: document.activeElement ? document.activeElement.className : '',
      sel: document.querySelectorAll('#sheet .d41-tx.sel').length,
      panel: (document.getElementById('d41Panel') || {}).innerText || '',
      panelHidden: (document.getElementById('d41Panel') || {}).hidden,
      x: (() => { const b = document.querySelector('#sheet .d41-txx'); if (!b) return null;
        const r = b.getBoundingClientRect(); return [Math.round(r.width), Math.round(r.height), getComputedStyle(b).display]; })()})""")
    check("이미 있는 상자를 한 번 톡 누르면 입력 포커스가 풀림 (아이폰 키보드 내려감)",
          "d41-txt" not in (one["focused"] or ""), one["focused"])
    # v45: T 툴바는 한 줄 [정렬 B S U − 크기 + 색] · 「글 수정/키보드 내리기」 줄은 없앰
    tbar = pageA.evaluate("""() => { const p = document.getElementById('d41Panel');
      const row = p.querySelector('.d41-trow');
      const cs = e => e ? getComputedStyle(e) : null;
      const order = row ? [...row.querySelectorAll('button, .d41-pv')].map(e => e.getAttribute('data-act') || e.getAttribute('aria-label') || e.textContent.trim()) : [];
      return {hidden: p.hidden, row: !!row,
        align: !!p.querySelector('[data-act=d41Align]'), b: !!p.querySelector('[data-act=d41Bold]'),
        s: !!p.querySelector('[data-act=d41Strike]'), u: !!p.querySelector('[data-act=d41Underline]'),
        size: p.querySelectorAll('[data-act=d41SizeStep]').length, pv: !!p.querySelector('.d41-pv'),
        color: !!p.querySelector('[data-act=d41ColorPick]'),
        edit: p.querySelectorAll('[data-act=d41Edit]').length, blur: p.querySelectorAll('[data-act=d41Blur]').length,
        hint: p.querySelectorAll('.d41-phint').length, order: order,
        colorW: (() => { const c = p.querySelector('.d41-tc'); return c ? Math.round(c.getBoundingClientRect().width) : 0; })()}; }""")
    check("그 상태에서 아래 T 툴바가 한 줄로 보임 (정렬·B·S·U·크기·색)",
          tbar["hidden"] is False and tbar["row"] and tbar["align"] and tbar["b"] and tbar["s"] and tbar["u"]
          and tbar["size"] == 2 and tbar["pv"] and tbar["color"], tbar)
    check("T 툴바에서 「글 수정·키보드 내리기」 줄과 안내 글씨가 사라짐",
          tbar["edit"] == 0 and tbar["blur"] == 0 and tbar["hint"] == 0, tbar)
    check("색 동그라미는 작게 (22px)", tbar["colorW"] == 22, tbar["colorW"])
    check("× 삭제 버튼 터치 영역 30px", one["x"] and one["x"][0] == 30 and one["x"][1] == 30 and one["x"][2] == "flex", one["x"])

    # 같은 상자를 짧은 사이에 한 번 더 톡 → 입력(포커스)
    pageA.mouse.click(tb["x"] + 18, tb["y"] + 12)
    pageA.wait_for_timeout(80)
    pageA.mouse.click(tb["x"] + 18, tb["y"] + 12)
    pageA.wait_for_timeout(360)
    dbl = pageA.evaluate("document.activeElement ? document.activeElement.className : ''")
    check("고른 상자를 한 번 더 톡 누르면 그때 입력(포커스)", "d41-txt" in (dbl or ""), dbl)

    # v45: 「글 수정 / 키보드 내리기」 단추는 없앴어요 — 두 번 톡 누르면 입력, 다른 곳을 누르면 내려가요
    pageA.evaluate("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
    pageA.wait_for_timeout(150)
    gone = pageA.evaluate("""() => ({edit: document.querySelectorAll('#d41Panel [data-act=d41Edit]').length,
      blur: document.querySelectorAll('#d41Panel [data-act=d41Blur]').length,
      hint: document.querySelectorAll('#d41Panel .d41-phint').length})""")
    check("T 툴바에서 「글 수정·키보드 내리기」 단추와 안내 줄이 사라짐",
          gone["edit"] == 0 and gone["blur"] == 0 and gone["hint"] == 0, gone)
    pageA.mouse.click(tb["x"] + 18, tb["y"] + 12)
    pageA.wait_for_timeout(120)
    pageA.mouse.click(tb["x"] + 18, tb["y"] + 12)
    pageA.wait_for_timeout(340)
    againFocus = pageA.evaluate("document.activeElement ? document.activeElement.className : ''")
    check("상자를 한 번 더 톡 누르면 다시 입력(포커스)", "d41-txt" in (againFocus or ""), againFocus)
    pageA.evaluate("document.activeElement && document.activeElement.blur && document.activeElement.blur()")
    pageA.wait_for_timeout(200)

    # × — pointerdown 에서 바로 삭제 (click 이 삼켜져도 지워짐)
    pageA.mouse.click(tb["x"] + 18, tb["y"] + 12)
    pageA.wait_for_timeout(300)
    xc = pageA.evaluate("""() => { const b = document.querySelector('#sheet .d41-txx');
      const r = b.getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }""")
    pageA.mouse.move(xc[0], xc[1])
    pageA.mouse.down()
    pageA.mouse.up()
    pageA.wait_for_timeout(420)
    check("× 를 누르면 그 상자가 바로 지워짐 (새 상자가 생기지 않음)",
          boxes(pageA) == 0 and hidden_texts(pageA) == [], (boxes(pageA), hidden_texts(pageA)))

    # 빈 상자가 쌓이지 않음 — 종이를 세 번 톡 + 도구 바꾸기
    pageA.mouse.click(pb["x"] + 110, pb["y"] + 250)
    pageA.wait_for_timeout(300)
    pageA.mouse.click(pb["x"] + 150, pb["y"] + 320)
    pageA.wait_for_timeout(300)
    pageA.mouse.click(pb["x"] + 190, pb["y"] + 390)
    pageA.wait_for_timeout(300)
    afterTaps = boxes(pageA)
    pageA.locator("#sheet .d41-tool[aria-label='펜 그리기']").click()
    pageA.wait_for_timeout(300)
    afterTool = boxes(pageA)
    check("빈 「글을 써 보세요」 상자는 쌓이지 않음 (항상 하나만)", afterTaps <= 1, afterTaps)
    check("도구를 바꾸면 빈 상자는 정리됨", afterTool == 0, afterTool)
    pageA.locator("#sheet .d41-tool[aria-label='글씨']").click()
    pageA.wait_for_timeout(300)

    # 글 하나 제대로 넣어 두기 (뒤 단계 저장용)
    pageA.mouse.click(pb["x"] + 70, pb["y"] + 210)
    pageA.wait_for_timeout(360)
    pageA.keyboard.type("자르기와 핀치를 시험하는 날")
    pageA.wait_for_timeout(240)
    pageA.wait_for_timeout(150)

    # ==================================================================
    # 3. 사진 — 자르기 창 (적용해야만 잘림)
    # ==================================================================
    img = make_photo(pageA, "v43-crop.jpg")
    pageA.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    pageA.wait_for_timeout(200)
    pageA.set_input_files("#d41ImgIn", [img])
    pageA.wait_for_timeout(1800)
    ib = pageA.locator("#sheet .d41-imgb").first.bounding_box()
    pageA.mouse.click(ib["x"] + 26, ib["y"] + 26)
    pageA.wait_for_timeout(400)
    nat0 = pageA.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img');
      return [i.naturalWidth, i.naturalHeight]; }""")
    check("사진을 누르면 「자르기·삭제」 칸", "자르기" in (pageA.evaluate("(document.getElementById('d41Panel')||{}).innerText || ''")))
    pageA.locator("#d41Panel [data-act=d41ImgCrop]").first.click()
    pageA.wait_for_timeout(620)
    geo = pageA.evaluate("""() => { const w = document.getElementById('d41CropWrap'); if (!w) return null;
      const card = w.querySelector('.d41-cropcard').getBoundingClientRect();
      const stage = document.getElementById('d41CropStage').getBoundingClientRect();
      const img = document.getElementById('d41CropImg').getBoundingClientRect();
      const frame = document.getElementById('d41CropFrame').getBoundingClientRect();
      const acts = [...w.querySelectorAll('.d41-cropacts .d41-cb')].map(b => b.textContent);
      return {pos: getComputedStyle(w).position, card: [Math.round(card.top), Math.round(card.height)],
        stage: [Math.round(stage.width), Math.round(stage.height)],
        img: [Math.round(img.width), Math.round(img.height)],
        frame: [Math.round(frame.width), Math.round(frame.height)],
        handles: w.querySelectorAll('.d41-ch').length, acts: acts,
        vw: innerWidth, vh: innerHeight}; }""")
    natOpen = pageA.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img');
      return [i.naturalWidth, i.naturalHeight]; }""")
    check("「자르기」를 눌러도 사진이 저절로 잘리지 않음", nat0 == natOpen, (nat0, natOpen))
    check("자르기 창이 뜸 — 원본 전체가 화면 안에 크게 (사진 크기 = 원본 비율)",
          geo and abs(geo["img"][0] / geo["img"][1] - nat0[0] / nat0[1]) < 0.02
          and geo["img"][0] <= geo["vw"] - 40 and geo["card"][0] >= 0
          and geo["card"][0] + geo["card"][1] <= geo["vh"], geo)
    check("자르기 테두리 + 모서리·변 손잡이 8개 · 전체/취소/적용",
          geo and geo["handles"] == 8 and geo["acts"] == ["전체", "취소", "적용"]
          and abs(geo["frame"][0] - geo["img"][0]) <= 4, geo)
    check("자르기 창은 화면 기준(fixed)이라 스크롤과 상관없이 보임", geo and geo["pos"] == "fixed", geo and geo["pos"])
    pageA.screenshot(path=os.path.join(SHOT, "note-v43-crop.png"))

    # 적용 전에 취소 → 원본 그대로
    pageA.locator("#d41CropWrap .d41-cb[data-crop=cancel]").click()
    pageA.wait_for_timeout(400)
    natCancel = pageA.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img');
      return [i.naturalWidth, i.naturalHeight]; }""")
    check("「취소」면 사진이 그대로", natCancel == nat0 and not pageA.evaluate("!!document.getElementById('d41CropWrap')"), natCancel)

    # 손잡이를 끌어 테두리 줄이고 적용 → 이때만 실제로 잘림
    pageA.locator("#d41Panel [data-act=d41ImgCrop]").first.click()
    pageA.wait_for_timeout(560)
    hb = pageA.evaluate("""() => { const f = document.getElementById('d41CropFrame').getBoundingClientRect();
      const h = document.querySelector('#d41CropWrap .d41-ch-se').getBoundingClientRect();
      return [h.x + h.width / 2, h.y + h.height / 2, f.x, f.y, f.width, f.height]; }""")
    pageA.mouse.move(hb[0], hb[1])
    pageA.mouse.down()
    pageA.mouse.move(hb[2] + hb[4] * 0.6, hb[3] + hb[5] * 0.6, steps=8)
    pageA.mouse.up()
    pageA.wait_for_timeout(300)
    ratio = pageA.evaluate("""() => { const f = document.getElementById('d41CropFrame').getBoundingClientRect();
      const s = document.getElementById('d41CropStage').getBoundingClientRect(); return [f.width / s.width, f.height / s.height]; }""")
    check("모서리 손잡이를 끌면 자르기 테두리 크기가 바뀜 (적용 전 사진은 그대로)",
          ratio[0] < 0.9 and ratio[1] < 0.9 and
          pageA.evaluate("(() => { const i = document.querySelector('#sheet .d41-imgb img'); return [i.naturalWidth, i.naturalHeight]; })()") == nat0, ratio)
    pageA.locator("#d41CropWrap [data-crop=apply]").click()
    pageA.wait_for_timeout(700)
    nat1 = pageA.evaluate("""() => { const i = document.querySelector('#sheet .d41-imgb img');
      return i ? [i.naturalWidth, i.naturalHeight] : null; }""")
    check("「적용」을 눌렀을 때만 사진이 실제로 잘림", nat1 and nat1[0] < nat0[0] and nat1[1] < nat0[1], (nat0, nat1))
    check("잘린 뒤 창이 닫히고 사진이 그대로 골라져 있음",
          not pageA.evaluate("!!document.getElementById('d41CropWrap')")
          and pageA.evaluate("document.querySelectorAll('#sheet .d41-imgb.sel').length") == 1)

    # ==================================================================
    # 4. 두 손가락 핀치 — 벌리면 커지고 오므리면 작아짐
    # ==================================================================
    w_open = pageA.evaluate("JSON.parse(document.getElementById('d41ImgsIn').value)[0].w")
    w_big = pageA.evaluate(PINCH_JS, [200])
    check("두 손가락을 벌리면 사진이 커짐", w_big > w_open + 0.03, (w_open, w_big))
    w_small = pageA.evaluate(PINCH_JS, [-90])
    check("두 손가락을 오므리면 사진이 작아짐", w_small < w_big - 0.02, (w_big, w_small))
    check("핀치로 바꾼 폭이 저장 준비 값(d41ImgsIn)에 반영", 0 < w_small < 1, w_small)
    pageA.screenshot(path=os.path.join(SHOT, "_p43-test-pinch.png"))

    # ==================================================================
    # 5. 저장 → 카드 → 다시 열기 (글·사진·폭 그대로)
    # ==================================================================
    pageA.locator("#sheet .d41-back").click()
    pageA.wait_for_timeout(900)
    cardA = pageA.evaluate("""() => { const c = document.querySelector('#s-diary .d41-card');
      return c ? {date: (c.querySelector('.nmemo-date') || {}).textContent,
        title: (c.querySelector('.nmemo-t') || {}).textContent,
        body: (c.querySelector('.nmemo-b') || {}).textContent,
        thumbs: c.querySelectorAll('.d41-th').length} : null; }""")
    check("저장하면 카드에 날짜·글·사진 미리보기 (v49: 제목 칸이 없어 제목은 비어요)",
          cardA and (cardA["title"] or "") == "" and "자르기와 핀치" in (cardA["body"] or "")
          and cardA["thumbs"] == 1, cardA)
    pageA.locator("#s-diary .d41-card").first.click()
    pageA.wait_for_timeout(700)
    reA = pageA.evaluate("""() => ({texts: JSON.parse(document.getElementById('d41TextsIn').value),
      imgs: JSON.parse(document.getElementById('d41ImgsIn').value)})""")
    check("다시 열어도 글·사진이 그대로",
          len(reA["texts"]) == 1 and "자르기와 핀치" in (reA["texts"][0]["text"] or "")
          and len(reA["imgs"]) == 1, [t["text"] for t in reA["texts"]])
    check("다시 열어도 핀치로 바꾼 사진 폭이 그대로",
          abs(reA["imgs"][0]["w"] - w_small) < 0.001, (reA["imgs"][0]["w"], w_small))
    pageA.keyboard.press("Escape")
    pageA.wait_for_timeout(300)
    check("브라우저 콘솔/페이지 오류 없음 (글 상자·사진)", len(errsA) == 0, errsA[:4])
    ctxA.close()

    # ==================================================================
    # 6. 기본 카테고리(속지 「모눈 메모」) — 저장해도 글이 사라지지 않음
    # ==================================================================
    ctxB = new_ctx(browser)
    ctxB.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageB = ctxB.new_page()
    errsB = []
    watch(pageB, errsB)
    pageB.goto(URL + "?demo=1", wait_until="networkidle")
    pageB.wait_for_timeout(700)
    pageB.evaluate("""() => {
      const s = JSON.parse(JSON.stringify(window.__app.state));
      s.noteKinds = { log: 'memo' };                 /* 「영화·먹방」 탭을 「모눈 메모」 속지로 */
      s.note = s.note || {};
      s.note.log = { e: '', n: '미정' };
      s.logs = [];
      localStorage.setItem('twolog:v1:state', JSON.stringify(s));
    }""")
    pageB.goto(URL, wait_until="networkidle")
    pageB.wait_for_timeout(900)
    tab(pageB, 2, 660)
    pageB.locator("#s-diary .seg-btn", has_text="미정").first.click()
    pageB.wait_for_timeout(620)
    pageB.locator("#s-diary .d41-new").click()
    pageB.wait_for_timeout(720)
    pbB = pageB.locator("#d41Paper").bounding_box()
    pageB.mouse.click(pbB["x"] + 60, pbB["y"] + 200)
    pageB.wait_for_timeout(360)
    pageB.keyboard.type("기본 카테고리에도 글이 남아야 해요")
    pageB.wait_for_timeout(240)
    imgB = make_photo(pageB, "v43-base.jpg", 480, 360)
    pageB.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    pageB.wait_for_timeout(200)
    pageB.set_input_files("#d41ImgIn", [imgB])
    pageB.wait_for_timeout(1700)
    pageB.locator("#sheet .d41-back").click()
    pageB.wait_for_timeout(1000)
    baseCard = pageB.evaluate("""() => { const c = document.querySelector('#s-diary .d41-card');
      return c ? {title: (c.querySelector('.nmemo-t') || {}).textContent,
        body: (c.querySelector('.nmemo-b') || {}).textContent,
        thumbs: c.querySelectorAll('.d41-th').length, date: (c.querySelector('.nmemo-date') || {}).textContent} : null; }""")
    check("기본 카테고리(모눈 메모) 저장 — 카드에 글·사진이 보임",
          baseCard and (baseCard["title"] or "") == ""
          and "기본 카테고리에도" in (baseCard["body"] or "") and baseCard["thumbs"] == 1, baseCard)
    baseSaved = pageB.evaluate("""() => { const l = (window.__app.state.logs || [])[0] || {};
      return {texts: (l.texts || []).length, imgs: (l.imgs || []).length, memo: l.memo || l.review || ''}; }""")
    check("기본 카테고리 저장값(S.logs)에 texts·imgs 가 들어 있음",
          baseSaved["texts"] == 1 and baseSaved["imgs"] == 1
          and "기본 카테고리에도" in (baseSaved["memo"] or ""), baseSaved)
    pageB.reload(wait_until="networkidle")
    pageB.wait_for_timeout(900)
    tab(pageB, 2, 660)
    pageB.locator("#s-diary .seg-btn", has_text="미정").first.click()
    pageB.wait_for_timeout(620)
    baseBack = pageB.evaluate("""() => { const c = document.querySelector('#s-diary .d41-card');
      return c ? {body: (c.querySelector('.nmemo-b') || {}).textContent,
        thumbs: c.querySelectorAll('.d41-th').length} : null; }""")
    check("새로고침해도 기본 카테고리 카드에 글이 남아 있음", baseBack and "기본 카테고리에도" in (baseBack["body"] or ""), baseBack)
    pageB.locator("#s-diary .d41-card").first.click()
    pageB.wait_for_timeout(720)
    baseOpen = pageB.evaluate("""() => ({texts: JSON.parse(document.getElementById('d41TextsIn').value),
      imgs: JSON.parse(document.getElementById('d41ImgsIn').value).length})""")
    check("다시 열어도 기본 카테고리 다이어리의 글·사진이 그대로",
          len(baseOpen["texts"]) == 1 and "기본 카테고리에도" in (baseOpen["texts"][0]["text"] or "")
          and baseOpen["imgs"] == 1, baseOpen)
    pageB.keyboard.press("Escape")
    pageB.wait_for_timeout(250)
    check("브라우저 콘솔/페이지 오류 없음 (기본 카테고리)", len(errsB) == 0, errsB[:4])
    ctxB.close()

    # ==================================================================
    # 6-2. 기념일 & 생일 시트 — 프로필 편집은 맨 위, 상단 문구 + 처음 만난 날 한 줄
    # ==================================================================
    ctxE = new_ctx(browser)
    ctxE.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageE = ctxE.new_page()
    errsE = []
    watch(pageE, errsE)
    pageE.goto(URL + "?demo=1", wait_until="networkidle")
    pageE.wait_for_timeout(800)
    demoE = pageE.evaluate("JSON.stringify(window.__app.state)")
    pageE.goto(URL, wait_until="domcontentloaded")
    pageE.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", demoE)
    pageE.reload(wait_until="networkidle")
    pageE.wait_for_timeout(900)
    tab(pageE, 0, 560)
    pageE.locator("#s-home .dday").click()
    pageE.wait_for_timeout(700)
    dd = pageE.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const hd = sh.querySelector('.sheet-hd');
      const profs = sh.querySelector('.dday-profs');
      const btns = profs ? [...profs.querySelectorAll('button[data-act="personSheet"]')] : [];
      const avs = profs ? [...profs.querySelectorAll('.pr-av')] : [];
      const outside = [...sh.querySelectorAll('button.btn-line[data-act="personSheet"]')]
        .filter(b => !profs || !profs.contains(b));
      const ph = sh.querySelector('input[name=phrase]');
      const since = sh.querySelector('input[name=since]');
      const lb = [...sh.querySelectorAll('.dday-row label')].map(l => l.textContent.trim());
      const allLbl = [...sh.querySelectorAll('.f > label')].map(l => l.textContent.trim());
      const rp = ph.getBoundingClientRect(), rs = since.getBoundingClientRect();
      const rb = btns[0] ? btns[0].getBoundingClientRect() : null;
      return {n: btns.length, who: btns.map(b => b.getAttribute('data-who')),
        outside: outside.length, inTop: !!profs && btns.length == 2,
        profTop: rb ? Math.round(rb.top) : -1, phTop: Math.round(rp.top),
        hdBottom: Math.round(hd.getBoundingClientRect().bottom),
        labels: lb, allLabels: allLbl,
        maxlen: ph.getAttribute('maxlength'),
        sameRow: Math.abs(rp.top - rs.top) < 6 && rp.right <= rs.left,
        phLeft: rp.left < rs.left,
        fits: ph.scrollWidth <= ph.clientWidth + 1,
        fs: getComputedStyle(ph).fontSize,
        avs: avs.length,
        avSize: avs[0] ? Math.round(avs[0].getBoundingClientRect().width) : 0,
        avFirst: avs[0] ? Math.round(avs[0].getBoundingClientRect().left) : -1,
        btnFirst: btns[0] ? Math.round(btns[0].getBoundingClientRect().left) : -1,
        text: sh.innerText.replace(/\s+/g, ' ').trim()};
    }""")
    check("기념일 시트 — 프로필 편집 버튼 두 개가 헤더 바로 아래 맨 위에 (아래쪽 버튼은 없음)",
          dd["n"] == 2 and set(dd["who"]) == {"me", "you"} and dd["inTop"] and dd["outside"] == 0
          and dd["profTop"] < dd["phTop"] and dd["profTop"] - dd["hdBottom"] < 40, dd)
    check("프로필 편집 버튼 앞에 각자 동그라미 프사 (2개, 왼쪽)",
          dd["avs"] == 2 and 18 <= dd["avSize"] <= 30
          and dd["btnFirst"] <= dd["avFirst"] <= dd["btnFirst"] + 40, dd)
    check("「우리는」 대신 「상단 문구」 라벨", dd["labels"][0].startswith("상단 문구")
          and dd["labels"][1] == "우리의 시작"
          and "우리는" not in (dd["text"] or ""), dd["labels"])
    check("「상단 문구」(왼쪽)와 「우리의 시작」(오른쪽)이 한 줄", dd["sameRow"] and dd["phLeft"], dd)
    check("상단 문구 칸 maxlength=14", dd["maxlen"] == "14", dd["maxlen"])
    # 14자를 넣어도 칸 안에 다 보이는지 (지금 쓴 글자수가 맥스가 되도록 맞춘 레이아웃)
    pageE.fill('#sheetForm input[name="phrase"]', "준영이가 소영이 쫓아다닌지")
    pageE.wait_for_timeout(250)
    fit = pageE.evaluate("""() => { const p = document.querySelector('#sheet input[name=phrase]');
      return {len: p.value.length, fits: p.scrollWidth <= p.clientWidth + 1,
        sw: p.scrollWidth, cw: p.clientWidth, fs: getComputedStyle(p).fontSize}; }""")
    check("14자(맥스) 문구가 칸 안에 다 보임", fit["len"] == 14 and fit["fits"], fit)
    pageE.screenshot(path=os.path.join(SHOT, "dday-v43-sheet.png"))
    pageE.locator('#sheet .dday-profs button[data-act="personSheet"][data-who="me"]').click()
    pageE.wait_for_timeout(520)
    meP = pageE.evaluate("""() => { const sh = document.querySelector('#sheet');
      const sws = [...sh.querySelectorAll('.pr-sws .sw')];
      const rows = new Set(sws.map(b => Math.round(b.getBoundingClientRect().top))).size;
      return {head: (sh.querySelector('.sheet-hd h2') || {}).textContent || '',
        sws: sws.length, rows: rows, colorLbl: sh.querySelectorAll('.pr-color').length,
        note: sh.querySelectorAll('.pr-note').length}; }""")
    check("내 프로필 편집 — 컬러 동그라미가 한 줄로 (12색) · 상대 안내 문구는 없음",
          "프로필" in (meP["head"] or "") and meP["sws"] == 12 and meP["rows"] == 1
          and meP["colorLbl"] == 1 and meP["note"] == 0, meP)
    # 사진을 올린 뒤 컬러를 고르면 사진 대신 컬러 아바타로 바뀌는지
    imgE = make_photo(pageE, "v43-av.jpg", 240, 240)
    with pageE.expect_file_chooser() as fcE:
        pageE.locator("#sheet .pr-avbtn").click()
    fcE.value.set_files([imgE])
    pageE.wait_for_timeout(900)
    pageE.locator("#avcApply").click()
    pageE.wait_for_timeout(700)
    hasPic = pageE.evaluate("!!((window.__app.state.couple.pics || {}).me)")
    check("프로필 사진을 올리면 저장됨", hasPic is True, hasPic)
    swsE = pageE.locator("#sheet .pr-sws .sw")
    nSw = swsE.count()
    swsE.nth(2).click()
    pageE.wait_for_timeout(700)
    afterCol = pageE.evaluate("""() => ({pic: !!((window.__app.state.couple.pics || {}).me),
      color: ((window.__app.state.couple.colors || {}).me) || '',
      sel: document.querySelectorAll('#sheet .pr-sws .sw.sel').length,
      img: document.querySelectorAll('#sheet .pr-av .av-img').length})""")
    check("사진이 있던 프로필에서 컬러를 고르면 사진 대신 그 컬러로 바뀜",
          nSw == 12 and afterCol["pic"] is False and afterCol["color"] == "#DD785B"
          and afterCol["sel"] == 1 and afterCol["img"] == 0, afterCol)
    pageE.screenshot(path=os.path.join(SHOT, "_p43-profile-color.png"))
    check("브라우저 콘솔/페이지 오류 없음 (기념일 시트)", len(errsE) == 0, errsE[:4])
    ctxE.close()

    # ==================================================================
    # 7. 날짜 모아보기 — 사진 칸의 ⋯ 메뉴 없음
    # ==================================================================
    ctxC = new_ctx(browser)
    ctxC.add_init_script("window.__TWOLOG_MODE = 'local';")
    pageC = ctxC.new_page()
    errsC = []
    watch(pageC, errsC)
    pageC.goto(URL + "?demo=1", wait_until="networkidle")
    pageC.wait_for_timeout(800)
    demoC = pageC.evaluate("JSON.stringify(window.__app.state)")
    pageC.goto(URL, wait_until="domcontentloaded")
    pageC.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", demoC)
    pageC.reload(wait_until="networkidle")
    pageC.wait_for_timeout(900)
    tab(pageC, 3, 600)
    pageC.locator("#s-photo .pola").last.click()
    pageC.wait_for_timeout(620)
    dayC = pageC.evaluate("""() => ({cells: document.querySelectorAll('#s-photo .dg-cell').length,
      more: document.querySelectorAll('#s-photo .dg-more').length,
      menu: document.querySelectorAll('#s-photo [data-act="photoMenu"]').length,
      badge: document.querySelectorAll('#s-photo .dg-moren').length,
      pencil: document.querySelectorAll('#s-photo [data-act="editPhotoDay"]').length,
      blocks: document.querySelectorAll('#s-photo .dcmt').length})""")
    check("날짜 모아보기 사진 칸에 ⋯ 메뉴가 없음", dayC["more"] == 0 and dayC["menu"] == 0, dayC)
    check("사진 칸·+N 배지·오른쪽 위 연필·댓글 칸은 그대로",
          dayC["cells"] >= 3 and dayC["pencil"] == 1 and dayC["blocks"] == 1, dayC)
    pageC.screenshot(path=os.path.join(SHOT, "_p43-test-daygrid.png"))
    pageC.locator("#s-photo [data-act=editPhotoDay]").click()
    pageC.wait_for_timeout(620)
    dayEdit = pageC.evaluate("""() => ({cells: document.querySelectorAll('#sheet .up-cell').length,
      xs: document.querySelectorAll('#sheet .up-cell .up-x').length,
      fields: [...document.querySelectorAll('#sheet .up-row label')].map(l => l.textContent)})""")
    check("연필(사진 수정) 시트에서 사진 빼기·기록 이름·날짜를 모두 할 수 있음",
          dayEdit["cells"] >= 3 and dayEdit["xs"] == dayEdit["cells"] and
          "기록 이름" in (dayEdit["fields"] or []) and "날짜" in (dayEdit["fields"] or []), dayEdit)

    SHEET_JS = """() => {
      const cs = (e) => e ? getComputedStyle(e) : null;
      const labels = [...document.querySelectorAll('#sheet .up-row label')].map(l => l.textContent);
      const d = document.querySelector('#sheet input[name=date]');
      const t = document.querySelector('#sheet input[name=album_tag]');
      const rd = d.getBoundingClientRect(), rt = t.getBoundingClientRect();
      const lb = document.querySelector('#sheet .up-hd-lb');
      const fl = document.querySelector('#sheet .up-row label');
      const cnt = document.querySelector('#sheet .up-hd-c');
      const grid = document.querySelector('#sheet #upList');
      const guide = document.querySelector('#sheet .up-guide');
      return {labels: labels,
        /* v45: 한 줄 나란히 → 「기록 이름」 위 · 「날짜」 아래 두 줄 */
        stacked: rt.bottom <= rd.top + 2 && Math.abs(rd.left - rt.left) < 2,
        lbFs: cs(lb) ? cs(lb).fontSize : null, lbFw: cs(lb) ? cs(lb).fontWeight : null,
        flFs: cs(fl) ? cs(fl).fontSize : null, flFw: cs(fl) ? cs(fl).fontWeight : null,
        cntFs: cs(cnt) ? cs(cnt).fontSize : null, cnt: (document.getElementById('upCount') || {}).textContent,
        cols: grid ? getComputedStyle(grid).gridTemplateColumns.split(' ').length : 0,
        guide: guide ? guide.textContent : '',
        sub: (document.querySelector('#sheet .sheet-sub') || {}).textContent || ''};
    }"""
    fixE = pageC.evaluate(SHEET_JS)
    check("사진 수정 시트 — 「기록 이름」 위 · 「날짜」 아래 두 줄 (v45)",
          fixE["labels"] == ["기록 이름", "날짜"] and fixE["stacked"], fixE["labels"])
    check("「사진」 라벨 글씨가 위 라벨(날짜·기록 이름)과 같은 폰트 크기·굵기",
          fixE["lbFs"] == fixE["flFs"] and fixE["lbFw"] == fixE["flFw"], (fixE["lbFs"], fixE["flFs"], fixE["lbFw"], fixE["flFw"]))
    check("옆의 「N장」은 지금 크기(12px) 그대로", fixE["cntFs"] == "12px" and (fixE["cnt"] or "").isdigit(), (fixE["cntFs"], fixE["cnt"]))
    check("오래된 「≡ 로 순서를 바꿔요」 안내는 사라짐", "≡ 로 순서" not in (fixE["sub"] or ""), fixE["sub"])
    check("사진 N장 아래에 「사진을 눌러 끌어 옮기면 순서를 바꿀 수 있어요」 안내",
          "끌어 옮기면 순서를 바꿀 수 있어요" in (fixE["guide"] or ""), fixE["guide"])
    check("사진 네모 그리드가 한 줄에 5개", fixE["cols"] == 5, fixE["cols"])
    pageC.screenshot(path=os.path.join(SHOT, "photo-v43-editgrid.png"))
    pageC.keyboard.press("Escape")
    pageC.wait_for_timeout(400)
    pageC.locator("#s-photo .dgal-back").click()
    pageC.wait_for_timeout(600)

    # 사진 추가 시트도 같은 기준
    imgC = make_photo(pageC, "v43-add.jpg", 400, 400)
    with pageC.expect_file_chooser() as fc:
        pageC.locator('#s-photo [data-act="addPhoto"]').click()
    fc.value.set_files([imgC, imgC, imgC])
    pageC.wait_for_timeout(1000)
    addE = pageC.evaluate(SHEET_JS)
    check("사진 추가 시트 — 「기록 이름」 위 · 「날짜」 아래 두 줄 (v45)",
          addE["labels"] == ["기록 이름", "날짜"] and addE["stacked"], addE["labels"])
    check("사진 추가 시트 — 「사진」 라벨 글씨 통일 · 「N장」 그대로 · 5열 · 안내 문구",
          addE["lbFs"] == addE["flFs"] and addE["lbFw"] == addE["flFw"] and addE["cntFs"] == "12px"
          and addE["cols"] == 5 and "끌어 옮기면 순서를 바꿀 수 있어요" in (addE["guide"] or ""), addE)
    pageC.keyboard.press("Escape")
    pageC.wait_for_timeout(300)
    check("브라우저 콘솔/페이지 오류 없음 (사진첩)", len(errsC) == 0, errsC[:4])
    ctxC.close()
    errs.clear()

    # ==================================================================
    # 8. Supabase 왕복 — 기본 카테고리·사용자 카테고리 모두 글·사진이 남음
    # ==================================================================
    cid = "couple-v43"
    uid = "user-v43"
    mail = "v43@twolog.app"
    db = {
        "users": {uid: {"id": uid, "email": mail, "password": "pw123456"}},
        "couples": [{"id": cid, "invite_code": "431743", "members": [uid],
                     "me": "소영", "you": "준영", "since": "2025-11-21", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "photos": [],
        "notes": [{"id": "L43", "couple_id": cid, "kind": "list", "sort": 0, "deleted": False,
                   "payload": {"title": "세상 메모", "emoji": "", "kind": "memo", "items": []}}],
        "settings": [{"couple_id": cid, "key": "note_meta",
                      "value": {"tabs": {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"},
                                         "log": {"e": "", "n": "미정"}},
                                "order": ["todo", "bucket", "log", "list:L43"],
                                "kinds": {"log": "memo"}}}],
        "uploads": [], "seq": 43,
    }
    seed = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({access_token: 't', refresh_token: 'r',
        user: {id: %s, email: %s}}));
    })();""" % (json.dumps(json.dumps(db, ensure_ascii=False)), json.dumps(uid), json.dumps(mail))
    ctxD = new_ctx(browser)
    ctxD.add_init_script(seed)
    pageD = ctxD.new_page()
    errsD = []
    watch(pageD, errsD)
    stub_route(pageD)
    pageD.goto(URL, wait_until="domcontentloaded")
    pageD.wait_for_selector("#tabbar .tab", timeout=25000)
    pageD.wait_for_timeout(2800)
    tab(pageD, 2, 700)
    # (a) 기본 카테고리 「미정」(모눈 메모)
    pageD.locator("#s-diary .seg-btn", has_text="미정").first.click()
    pageD.wait_for_timeout(640)
    pageD.locator("#s-diary .d41-new").click()
    pageD.wait_for_timeout(760)
    pbD = pageD.locator("#d41Paper").bounding_box()
    pageD.mouse.click(pbD["x"] + 70, pbD["y"] + 170)
    pageD.wait_for_timeout(340)
    pageD.keyboard.type("서버 왕복에도 남는 글")
    pageD.wait_for_timeout(240)
    imgD = make_photo(pageD, "v43-sync.jpg", 400, 300)
    pageD.locator("#sheet .d41-tool[aria-label='사진 넣기']").click()
    pageD.wait_for_timeout(200)
    pageD.set_input_files("#d41ImgIn", [imgD])
    pageD.wait_for_timeout(1700)
    pageD.locator("#sheet .d41-back").click()
    pageD.wait_for_timeout(2600)
    srv = pageD.evaluate("""() => { const row = (window.__stub.notes || []).filter(x => x.kind === 'log')[0];
      const p = row ? (row.payload || {}) : {};
      return {texts: p.texts || [], imgs: p.imgs || [], memo: p.memo || '', title: p.title || p.text || ''}; }""")
    check("기본 카테고리 다이어리의 글·사진이 notes(log) payload 에 실림",
          len(srv["texts"]) == 1 and "서버 왕복에도" in (srv["texts"][0].get("text") or "")
          and len(srv["imgs"]) == 1 and srv["imgs"][0].get("src", "").startswith("data:image"), srv)
    check("글 상자 좌표·크기도 함께 올라감 (v49: 위 줄 제목 칸 없음)",
          0 <= srv["texts"][0].get("x", -1) <= 1 and srv["texts"][0].get("size", 0) > 0
          and (srv["title"] or "") == "", srv["texts"][0])
    # (b) 사용자 카테고리 「세상 메모」
    pageD.keyboard.press("Escape")
    pageD.wait_for_timeout(300)
    pageD.locator("#s-diary .lchip", has_text="세상 메모").first.click()
    pageD.wait_for_timeout(620)
    pageD.locator("#s-diary .d41-new").click()
    pageD.wait_for_timeout(760)
    pbD2 = pageD.locator("#d41Paper").bounding_box()
    pageD.mouse.click(pbD2["x"] + 70, pbD2["y"] + 170)
    pageD.wait_for_timeout(340)
    pageD.keyboard.type("내 카테고리 글도 남아요")
    pageD.wait_for_timeout(240)
    pageD.locator("#sheet .d41-back").click()
    pageD.wait_for_timeout(2600)
    srv2 = pageD.evaluate("""() => { const row = (window.__stub.notes || []).filter(x => x.kind === 'list')[0];
      const it = row ? ((row.payload || {}).items || [])[0] : null;
      return it ? {texts: it.texts || [], imgs: it.imgs || []} : null; }""")
    check("사용자 카테고리 다이어리도 notes(list) payload 에 texts 가 실림",
          srv2 and len(srv2["texts"]) == 1 and "내 카테고리 글도" in (srv2["texts"][0].get("text") or ""), srv2)
    # (c) 새로고침(=서버에서 다시 읽기) 뒤에도 그대로
    pageD.reload(wait_until="domcontentloaded")
    pageD.wait_for_selector("#tabbar .tab", timeout=25000)
    pageD.wait_for_timeout(2800)
    backD = pageD.evaluate("""() => {
      const log = (window.__app.state.logs || [])[0] || {};
      const l = (window.__app.state.lists || []).filter(x => x.title === '세상 메모')[0] || {};
      const it = (l.items || [])[0] || {};
      return {baseTexts: (log.texts || []).length, baseImgs: (log.imgs || []).length,
        baseText: (((log.texts || [])[0]) || {}).text || '',
        listTexts: (it.texts || []).length, listText: (((it.texts || [])[0]) || {}).text || ''}; }""")
    check("서버에서 다시 읽어도 기본 카테고리 글·사진이 남음 (날짜만 남던 문제)",
          backD["baseTexts"] == 1 and backD["baseImgs"] == 1 and "서버 왕복에도" in backD["baseText"], backD)
    check("서버에서 다시 읽어도 사용자 카테고리 글도 남음",
          backD["listTexts"] == 1 and "내 카테고리 글도" in backD["listText"], backD)
    tab(pageD, 2, 700)
    pageD.locator("#s-diary .seg-btn", has_text="미정").first.click()
    pageD.wait_for_timeout(640)
    cardD = pageD.evaluate("""() => { const c = document.querySelector('#s-diary .d41-card');
      return c ? {body: (c.querySelector('.nmemo-b') || {}).textContent,
        thumbs: c.querySelectorAll('.d41-th').length} : null; }""")
    check("새로고침 뒤 카드에도 글·사진 미리보기가 보임",
          cardD and "서버 왕복에도" in (cardD["body"] or "") and cardD["thumbs"] == 1, cardD)
    # (d) 프로필(생일)도 서버 왕복 뒤에도 남아야 해요
    tab(pageD, 4, 700)
    pageD.locator('#s-set [data-act="personSheet"][data-who="you"]').click()
    pageD.wait_for_timeout(600)
    prof0 = pageD.evaluate("""() => { const sh = document.querySelector('#sheet');
      const b = sh.querySelector('input[name=bday]');
      const n = sh.querySelector('input[name=name]');
      return {date: !!b && b.type === 'date',
        sel3: !!(sh.querySelector('select.pr-bday-y') || sh.querySelector('select.pr-bday-m')),
        note: (sh.querySelector('.pr-note') || {}).textContent || '',
        belowName: (() => { if (!b || !n) return false;
          const rn = n.getBoundingClientRect(), rb = b.getBoundingClientRect();
          return rb.top > rn.bottom - 1; })(),
        sws: sh.querySelectorAll('.pr-sws .sw').length, colorLbl: sh.querySelectorAll('.pr-color').length,
        hint: (document.getElementById('prBdayTxt') || {}).textContent || ''}; }""")
    check("상대 프로필 시트 — 컬러 동그라미 한 줄", prof0["sws"] == 12 and prof0["colorLbl"] == 1, prof0)
    check("상대 프로필 시트 — 닉네임 아래 「프로필은 상대방이 직접 설정할 수 있어요」 안내",
          "프로필은 상대방이 직접 설정할 수 있어요" in (prof0["note"] or "") and prof0["belowName"], prof0)
    # v45: 생일은 날짜칸 한 개 (v44 의 세 칸 고르기는 걷어냄)
    check("생일 칸은 날짜 입력칸 하나 (세 칸 고르기 없음)", prof0["date"] and not prof0["sel3"] and prof0["belowName"], prof0)
    pageD.fill('#sheet input[name=bday]', '1996-03-09')
    pageD.wait_for_timeout(280)
    hintNow = pageD.evaluate("(document.getElementById('prBdayTxt') || {}).textContent || ''")
    check("날짜를 고르면 연·월·일이 그 자리에 보임", "1996년 3월 9일" in hintNow, hintNow)
    pageD.locator('#sheet #personForm button[type="submit"]').click()
    pageD.wait_for_timeout(1600)
    savedP = pageD.evaluate("""() => ({b: ((window.__app.state.couple || {}).birthdays || {}).you || ''})""")
    check("저장하면 준영 생일이 1996-03-09 로 남음", savedP["b"] == "1996-03-09", savedP)
    # 기념일 & 생일 요약 줄에도 바로
    tab(pageD, 0, 600)
    pageD.locator("#s-home .dday").click()
    pageD.wait_for_timeout(700)
    mileNow = pageD.evaluate("(document.querySelector('#sheet .mile-d[data-bdtxt=\\'you\\']') || {}).textContent || ''")
    check("기념일 & 생일 요약 줄에 「3월 9일」이 바로 보임", "3월 9일" in mileNow, mileNow)
    pageD.keyboard.press("Escape")
    pageD.wait_for_timeout(400)
    pageD.reload(wait_until="domcontentloaded")
    pageD.wait_for_selector("#tabbar .tab", timeout=25000)
    pageD.wait_for_timeout(2800)
    prof1 = pageD.evaluate("""() => (((window.__app.state.couple || {}).birthdays) || {})""")
    check("새로고침(서버에서 다시 읽기)해도 두 사람 생일이 그대로",
          prof1.get("you") == "1996-03-09" and bool(prof1.get("me")), prof1)
    tab(pageD, 4, 700)
    pageD.locator('#s-set [data-act="personSheet"][data-who="you"]').click()
    pageD.wait_for_timeout(600)
    profVal = pageD.evaluate("(document.querySelector('#sheet input[name=bday]') || {}).value || ''")
    check("프로필을 다시 열면 생일 칸에 1996-03-09 가 채워져 있음", profVal == "1996-03-09", profVal)
    pageD.keyboard.press("Escape")
    pageD.wait_for_timeout(300)
    check("브라우저 콘솔/페이지 오류 없음 (동기화)", len(errsD) == 0, errsD[:4])
    ctxD.close()

    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS — v43")
