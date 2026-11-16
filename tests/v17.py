"""투로그 v17 확인 — 노트 카드·시트에서 「주제」 줄/칸 삭제, sw 자동 갱신(controllerchange 새로고침),
12색 컬러 팔레트(IMG_4508, 4열 3줄)와 기본 버튼 색 일치.

    python3 tests/v17.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


SW_OVERRIDE = {"body": None}


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        # sw.js 는 테스트 중 바꿔치기할 수 있게 메모리 본문을 내려 줘요 (새 버전 배포 흉내)
        if SW_OVERRIDE["body"] is not None and self.path.split("?")[0].endswith("/sw.js"):
            body = SW_OVERRIDE["body"].encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/javascript; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()


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


CSS_OF = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
  const s = getComputedStyle(el); const r = el.getBoundingClientRect();
  return {br: s.borderTopLeftRadius, pl: s.paddingLeft, pt: s.paddingTop,
  bt: s.borderTopWidth, bs: s.borderTopStyle, bc: s.borderTopColor,
  bg: s.backgroundColor, col: s.color, fs: s.fontSize, fw: s.fontWeight,
  mt: s.marginTop, sh: s.boxShadow, h: r.height, w: r.width, x: r.x, y: r.y, txt: el.innerText}; }"""
BOX = """(sel) => { const el = document.querySelector(sel); if (!el) return null;
  const r = el.getBoundingClientRect(); return {y: r.y, b: r.bottom, h: r.height}; }"""
LABELS = "() => Array.from(document.querySelectorAll('#sheetForm label')).map(l => l.innerText.trim())"
INK = """(hex) => { const h = String(hex).replace('#',''); const n = parseInt(h.slice(0,2),16),
  g = parseInt(h.slice(2,4),16), b = parseInt(h.slice(4,6),16);
  const lin = c => (c/255) <= 0.03928 ? (c/255)/12.92 : Math.pow((c/255 + 0.055)/1.055, 2.4);
  const L = 0.2126*lin(n) + 0.7152*lin(g) + 0.0722*lin(b);
  return L > 0.5 ? 'rgb(17, 17, 17)' : 'rgb(255, 255, 255)'; }"""
RGB = """(hex) => { const h = String(hex).replace('#','');
  return 'rgb(' + parseInt(h.slice(0,2),16) + ', ' + parseInt(h.slice(2,4),16) + ', ' + parseInt(h.slice(4,6),16) + ')'; }"""

PALETTE = ["#F2CFC9", "#DEA2A6", "#DD785B", "#EA994D",
           "#EFD353", "#C4C66A", "#B8CAA5", "#B4D8D4",
           "#80A4AA", "#D2CBE3", "#A299B8", "#C4B28E"]
PICK = "#80A4AA"


def shot(page, name, settle=1900):
    page.wait_for_timeout(settle)
    page.screenshot(path=os.path.join(SHOT, name))


def px(v):
    try:
        return float(str(v).replace("px", ""))
    except Exception:  # noqa: BLE001
        return -1


def goto_note(page):
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(600)


with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    page.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page.wait_for_timeout(800)

    # ==================================================================
    # 1. 노트 카드 — 「이번 주 / 주제」 윗줄이 사라지고 제목부터
    # ==================================================================
    goto_note(page)
    n_cards = page.locator("#s-diary .ncard:not(.new)").count()
    check("노트 카드 있음", n_cards >= 1, n_cards)
    check("카드에 「주제」 줄 없음", page.locator("#s-diary .ncard .nc-topic").count() == 0,
          page.locator("#s-diary .ncard .nc-topic").count())
    check("카드에 nc-top 없음", page.locator("#s-diary .ncard .nc-top").count() == 0)
    check("카드 글에 「주제」·「이번 주」 없음",
          "주제" not in page.locator("#s-diary").inner_text()
          and "이번 주" not in page.locator("#s-diary").inner_text(),
          page.locator("#s-diary").inner_text()[:80])
    first_cls = page.evaluate(
        "() => { const c = document.querySelector('#s-diary .ncard'); const k = c && c.firstElementChild; return k ? k.className : ''; }")
    check("카드 맨 윗줄이 제목(.nc-t)", str(first_cls).startswith("nc-t"), first_cls)
    t_css = page.evaluate(CSS_OF, "#s-diary .ncard .nc-t")
    check("제목 18px 유지", px(t_css["fs"]) >= 18, t_css["fs"])
    check("제목 800 유지", int(t_css["fw"]) >= 800, t_css["fw"])
    check("제목이 카드 위쪽", t_css["y"] - page.evaluate(BOX, "#s-diary .ncard")["y"] < 26,
          round(t_css["y"]))

    # ==================================================================
    # 2. 카드 상세 시트 — 제목만, 주제 칸 없음
    # ==================================================================
    page.locator("#s-diary .ncard .nc-t").first.click()
    page.wait_for_timeout(500)
    check("카드 상세 시트 열림", page.locator("#sheet .card-items").count() == 1)
    labels = page.evaluate(LABELS)
    check("시트 라벨은 제목만", labels == ["제목"], labels)
    check("주제 입력칸 없음", page.locator('#sheetForm input[name="topic"]').count() == 0)
    check("「주제」 안내 글씨 없음", "주제" not in page.locator("#sheet").inner_text(),
          page.locator("#sheet").inner_text()[:120].replace("\n", " / "))
    y_title = page.evaluate(BOX, '#sheetForm input[name="title"]')
    y_todo = page.evaluate(BOX, "#sheet .todo-label")
    y_add = page.evaluate(BOX, "#sheet .todo-add")
    y_items = page.evaluate(BOX, "#sheet .card-items")
    check("제목이 To-do보다 위", y_title and y_todo and y_title["y"] < y_todo["y"],
          (y_title and round(y_title["y"]), y_todo and round(y_todo["y"])))
    check("To-do 입력·목록 순서", y_add and y_items and y_add["y"] < y_items["y"],
          (y_add and round(y_add["y"]), y_items and round(y_items["y"])))
    check("To-do 안내 그대로", page.locator("#sheet .todo-add input.todo-in").count() == 1)
    check("저장하기·카드 삭제 그대로",
          page.locator('#sheet .card-acts .btn-primary').count() == 1
          and page.locator('#sheet [data-act="delCard"]').count() == 1)

    for word in ("우유 사기", "계란", "카카오페이 충전"):
        page.fill('#sheet #listAddForm input[name="text"]', word)
        page.click("#sheet .todo-add-btn")
        page.wait_for_timeout(320)
    check("시트에서 항목 추가", page.locator("#sheet .card-items .trow").count() == 3,
          page.locator("#sheet .card-items .trow").count())
    page.locator("#sheet .card-items .trow .circ").first.click()
    page.wait_for_timeout(400)
    check("시트 안에서 완료", page.locator("#sheet .card-items .trow.done").count() == 1)
    # 항목을 체크해도 적던 제목이 날아가지 않는지 (refreshCardSheet)
    page.fill('#sheetForm input[name="title"]', "생일 준비")
    page.locator("#sheet .card-items .trow .circ").nth(1).click()
    page.wait_for_timeout(400)
    check("체크해도 적던 제목 유지", page.input_value('#sheetForm input[name="title"]') == "생일 준비",
          page.input_value('#sheetForm input[name="title"]'))
    page.locator("#sheet .card-acts").scroll_into_view_if_needed()
    shot(page, "note-detail-v17.png", settle=600)
    page.click("#sheet .card-acts .btn-primary")
    page.wait_for_timeout(800)
    check("저장하면 시트 닫힘", page.locator("#sheetWrap.open").count() == 0)
    check("저장한 제목이 카드 맨 윗줄",
          page.locator("#s-diary .ncard .nc-t").first.inner_text().strip() == "생일 준비",
          page.locator("#s-diary .ncard .nc-t").first.inner_text())
    check("저장 후에도 주제 줄 없음", page.locator("#s-diary .ncard .nc-topic").count() == 0)
    check("카드에 항목 미리보기", page.locator("#s-diary .ncard .nc-items .cti").count() >= 3,
          page.locator("#s-diary .ncard .nc-items .cti").count())
    page.locator("#s-diary .ncard .nc-t").first.scroll_into_view_if_needed()
    shot(page, "note-v17.png", settle=900)

    # ==================================================================
    # 3. 새 리스트 시트 — 제목만 (주제 칸 삭제)
    # ==================================================================
    before = page.locator("#s-diary .ncard:not(.new)").count()
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(450)
    new_labels = page.evaluate(LABELS)
    check("새 리스트 라벨은 제목만", new_labels == ["제목"], new_labels)
    check("새 리스트 주제 칸 없음", page.locator('#sheetForm input[name="topic"]').count() == 0)
    check("새 리스트 안내에 「주제」 없음", "주제" not in page.locator("#sheet").inner_text())
    page.fill('#sheetForm input[name="title"]', "장보기")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(700)
    check("새 리스트 만들어짐", page.locator("#s-diary .ncard:not(.new)").count() == before + 1,
          page.locator("#s-diary .ncard:not(.new)").count())
    check("새 리스트 제목 보임", "장보기" in page.locator("#s-diary").inner_text())
    # 카드 삭제는 그대로 동작
    page.locator("#s-diary .ncard", has_text="장보기").first.click()
    page.wait_for_timeout(450)
    page.click('#sheet [data-act="delCard"]')
    page.wait_for_timeout(450)
    check("삭제 확인 시트", "카드를 지울까요" in page.locator("#sheet").inner_text())
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(700)
    check("카드 삭제됨", page.locator("#s-diary .ncard:not(.new)").count() == before,
          page.locator("#s-diary .ncard:not(.new)").count())

    # ==================================================================
    # 4. 예전에 저장된 「주제」 값(이번 주)은 화면에 안 나오고 저장 때 지워짐
    # ==================================================================
    page.evaluate("""() => {
      const k = 'twolog:v1:state';
      const d = JSON.parse(localStorage.getItem(k));
      d.groups.todo[0].topic = '이번 주';
      localStorage.setItem(k, JSON.stringify(d));
    }""")
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(900)
    goto_note(page)
    check("예전 주제 값이 화면에 안 나옴", "이번 주" not in page.locator("#s-diary").inner_text(),
          page.locator("#s-diary").inner_text()[:80].replace("\n", " / "))
    check("예전 데이터에도 주제 줄 없음", page.locator("#s-diary .ncard .nc-topic").count() == 0)
    page.locator("#s-diary .ncard .cti").first.click()   # 저장을 한 번 일으킴
    page.wait_for_timeout(600)
    left = page.evaluate("""() => {
      const d = JSON.parse(localStorage.getItem('twolog:v1:state'));
      return d.groups.todo.filter(g => 'topic' in g).length;
    }""")
    check("저장하면 예전 주제 값도 정리", left == 0, left)
    page.locator("#s-diary .ncard .cti").first.click()   # 원래대로 되돌리기
    page.wait_for_timeout(500)

    # ==================================================================
    # 5. 12색 컬러 팔레트 (IMG_4508) — 4열 3줄, 컬러·기본보다 위
    # ==================================================================
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(500)
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(500)
    pal = page.evaluate("""() => {
      const grid = document.querySelector('.sw-grid[data-sw="homeTitleBg"]');
      const els = Array.from(grid.querySelectorAll('.sw'));
      const cs = getComputedStyle(grid);
      const rows = new Set(els.map(e => Math.round(e.getBoundingClientRect().y)));
      return {n: els.length, cols: cs.gridTemplateColumns.split(' ').length, colTxt: cs.gridTemplateColumns,
              rows: rows.size, colors: els.map(e => String(e.getAttribute('data-color')).toUpperCase()),
              bg: els.map(e => getComputedStyle(e).backgroundColor),
              h: els.map(e => Math.round(e.getBoundingClientRect().height)),
              w: els.map(e => Math.round(e.getBoundingClientRect().width))};
    }""")
    check("팔레트 12색", pal["n"] == 12, pal["n"])
    check("팔레트 색 순서 일치", pal["colors"] == PALETTE, pal["colors"])
    check("팔레트 4열", pal["cols"] == 4, pal["colTxt"])
    check("팔레트 3줄", pal["rows"] == 3, pal["rows"])
    check("팔레트 칸 크기 같음", len(set(pal["w"])) == 1 and len(set(pal["h"])) == 1,
          (sorted(set(pal["w"])), sorted(set(pal["h"]))))
    check("팔레트 색이 실제로 칠해짐",
          pal["bg"] == [page.evaluate(RGB, c) for c in PALETTE], pal["bg"][:3])
    check("팔레트 칸 각진 모서리", page.evaluate(
        "() => getComputedStyle(document.querySelector('.sw-grid[data-sw=\"homeTitleBg\"] .sw')).borderTopLeftRadius") in ("0px", "0"))
    grid_box = page.evaluate(BOX, '.sw-grid[data-sw="homeTitleBg"]')
    pick_box = page.evaluate(BOX, '#sheet .cp-pick')
    reset_box = page.evaluate(BOX, '#sheet .cp-reset')
    check("팔레트가 「컬러」 위", grid_box and pick_box and grid_box["b"] <= pick_box["y"] + 1,
          (grid_box and round(grid_box["b"]), pick_box and round(pick_box["y"])))
    check("팔레트가 「기본」 위", grid_box and reset_box and grid_box["b"] <= reset_box["y"] + 1,
          (grid_box and round(grid_box["b"]), reset_box and round(reset_box["y"])))
    shot(page, "theme-sheet-v17.png", settle=500)

    # 색을 고르면 --btn-bg/--btn-ink 로 모든 기본 버튼이 같은 색
    page.locator('.sw-grid[data-sw="homeTitleBg"] .sw[data-color="%s"]' % PICK).click()
    page.wait_for_timeout(500)
    btn = page.evaluate(CSS_OF, "#sheet .btn-primary")
    check("시트 완료 버튼이 고른 색", btn and btn["bg"] == page.evaluate(RGB, PICK), (btn and btn["bg"]))
    check("시트 완료 버튼 글씨 대비", btn and btn["col"] == page.evaluate(INK, PICK), (btn and btn["col"]))
    check("--btn-bg 변수 설정", page.evaluate(
        "() => getComputedStyle(document.documentElement).getPropertyValue('--btn-bg').trim().toUpperCase()") == PICK,
        page.evaluate("() => getComputedStyle(document.documentElement).getPropertyValue('--btn-bg')"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(450)
    shot(page, "home-tinted-v17.png", settle=600)
    tint = page.evaluate(CSS_OF, ".home-sec[data-sec='sched'] .sec-tint")
    check("홈 제목 줄도 고른 색", tint and tint["bg"] == page.evaluate(RGB, PICK), (tint and tint["bg"]))

    # ==================================================================
    # 6. 시트마다 기본 버튼이 모두 같은 색 (저장하기·완료·추가하기·Add·연결하기)
    # ==================================================================
    def btns_in_sheet():
        return page.evaluate("""(pick) => {
          const out = {};
          const g = s => { const el = document.querySelector(s); return el ? getComputedStyle(el).backgroundColor : null; };
          out.primary = g('#sheet .btn-primary');
          out.add = g('#sheet .todo-add-btn');
          out.on = g('#sheet .set-btn.on');
          const stray = Array.from(document.querySelectorAll('#sheet button'))
            .filter(b => { const s = getComputedStyle(b); const r = b.getBoundingClientRect();
              return r.height >= 34 && s.backgroundColor === 'rgb(217, 107, 82)'; })
            .map(b => (b.className || '') + ':' + (b.innerText || '').trim().slice(0, 10));
          out.stray = stray;
          const ink = Array.from(document.querySelectorAll('#sheet .btn-primary, #sheet .todo-add-btn, #sheet .set-btn.on'))
            .map(b => getComputedStyle(b).color);
          out.ink = ink;
          return out;
        }""", PICK)

    want = page.evaluate(RGB, PICK)
    ink = page.evaluate(INK, PICK)

    goto_note(page)
    page.locator("#s-diary .ncard .nc-t").first.click()
    page.wait_for_timeout(500)
    b = btns_in_sheet()
    check("카드 시트 저장하기 색", b["primary"] == want, b["primary"])
    check("카드 시트 Add 색", b["add"] == want, b["add"])
    check("카드 시트 버튼 글씨 대비", all(c == ink for c in b["ink"]), b["ink"])
    check("카드 시트에 색 안 바뀐 버튼 없음", b["stray"] == [], b["stray"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(450)
    b = btns_in_sheet()
    check("새 리스트 저장 색", b["primary"] == want, b["primary"])
    check("새 리스트에 색 안 바뀐 버튼 없음", b["stray"] == [], b["stray"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # 일정 추가 시트
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(500)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(500)
    b = btns_in_sheet()
    check("일정 시트 추가하기 색", b["primary"] == want, b["primary"])
    check("일정 시트에 색 안 바뀐 버튼 없음", b["stray"] == [], b["stray"])
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # 커플 연결 시트 (연결하기 = .set-btn.on)
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    page.locator('#s-set [data-act="linkSheet"]').first.click()
    page.wait_for_timeout(500)
    b = btns_in_sheet()
    check("연결 시트 연결하기 색", b["on"] == want, b["on"])
    check("연결 시트에 색 안 바뀐 버튼 없음", b["stray"] == [], b["stray"])
    shot(page, "link-sheet-v17.png", settle=400)
    page.keyboard.press("Escape")
    page.wait_for_timeout(400)

    # ==================================================================
    # 7. 사진첩 — 날짜별 폴라로이드 (IMG_4511)
    # ==================================================================
    ctx3 = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page3 = ctx3.new_page()
    errs3 = []
    page3.on("pageerror", lambda e: errs3.append(str(e)))
    page3.on("console", lambda m: errs3.append(m.text) if m.type == "error" else None)
    page3.goto("http://127.0.0.1:%d/?demo=1" % PORT, wait_until="networkidle")
    page3.wait_for_timeout(900)
    page3.locator("#tabbar .tab").nth(3).click()
    page3.wait_for_timeout(700)

    ph = page3.evaluate("""() => {
      const days = Array.from(document.querySelectorAll('#s-photo .pday'));
      const first = days[0];
      const polas = first ? Array.from(first.querySelectorAll('.pola')) : [];
      const r = el => el.getBoundingClientRect();
      return {
        days: days.length,
        heads: days.map(d => d.querySelector('.pday-hd').innerText),
        labels: days.map(d => (d.querySelector('.pday-hd .d') || {}).innerText || ''),
        polas: polas.length,
        bg: polas.length ? getComputedStyle(polas[0]).backgroundColor : null,
        br: polas.length ? getComputedStyle(polas[0]).borderTopLeftRadius : null,
        pad: polas.length ? [getComputedStyle(polas[0]).paddingTop, getComputedStyle(polas[0]).paddingLeft,
                            getComputedStyle(polas[0]).paddingBottom] : null,
        shadow: polas.length ? getComputedStyle(polas[0]).boxShadow : null,
        tilts: polas.map(p => getComputedStyle(p).transform),
        chins: polas.map(p => { const c = p.querySelector('.pola-chin'); return c ? c.offsetHeight : 0; }),
        rows: new Set(polas.map(p => Math.round(r(p).y))).size,
        cols: getComputedStyle(first ? first.querySelector('.polas') : document.body).gridTemplateColumns,
        overlap: polas.length > 1 ? Math.round(r(polas[0]).right - r(polas[1]).left) : 0,
        sheetOver: document.querySelector('#s-photo').scrollWidth - document.querySelector('#s-photo').clientWidth,
        pics: polas.map(p => { const i = p.querySelector('.pola-pic img, .pola-pic svg'); return i ? parseFloat(getComputedStyle(i).width) : 0; }),
      };
    }""")
    check("사진첩 날짜별 묶음(3일)", ph["days"] == 3, ph["days"])
    check("가장 최근 날이 맨 위(사진 6장)", ph["polas"] == 6, ph["polas"])
    flat_heads = [" / ".join(h.split("\n")) for h in ph["heads"]]
    check("날짜 머리글 형식(오늘/어제/ M월 D일 · 요일)",
          all(any(x in h for x in ("오늘", "어제")) or ("월" in h and "일" in h and "요일" in h)
              for h in flat_heads), flat_heads)
    check("오래된 날은 날짜만(point 색 아님)", "월" in flat_heads[-1], flat_heads[-1])
    check("한 날 사진이 한 줄에", ph["polas"] == 6 and ph["cols"].count(" ") == 2, (ph["polas"], ph["cols"]))
    check("폴라로이드 흰 프레임", ph["bg"] == "rgb(255, 255, 255)", ph["bg"])
    check("폴라로이드 각진 모서리", ph["br"] in ("0px", "0"), ph["br"])
    check("위·옆 6px, 아래 18px 턱", ph["pad"] == ["6px", "6px", "18px"], ph["pad"])
    check("폴라로이드 그림자", ph["shadow"] not in (None, "none", ""), ph["shadow"])
    check("사진마다 살짝 기울어짐", len(set(ph["tilts"])) >= 2 and all(t != "none" for t in ph["tilts"]),
          ph["tilts"][:3])
    check("사진끼리 살짝 겹침", ph["overlap"] >= 6, ph["overlap"])
    check("턱(캡션) 높이 있음", all(6 <= c <= 18 for c in ph["chins"]), ph["chins"])
    check("사진첩 가로 넘침 없음", ph["sheetOver"] <= 1, ph["sheetOver"])
    check("사진 칸이 정사각", ph["pics"] and max(ph["pics"]) - min(ph["pics"]) <= 1.5 and ph["pics"][0] > 70,
          ph["pics"][:3])

    # 폴라로이드를 누르면 전체 화면 뷰어·캡션 시트
    page3.locator("#s-photo .pola").first.click()
    page3.wait_for_timeout(600)
    check("폴라로이드 누르면 사진 상세", page3.locator("#sheet .pdetail").count() == 1)
    check("상세에 캡션·캡션 색 있음", page3.locator("#sheet .pd-cap").count() == 1
          and page3.locator('#sheet .sw-grid[data-sw="cap"]').count() == 1)
    page3.keyboard.press("Escape")
    page3.wait_for_timeout(400)
    shot(page3, "photo-v17.png", settle=900)

    # + 사진 추가는 그대로 파일 선택창을 엽니다
    chooser_ok = True
    try:
        with page3.expect_file_chooser(timeout=5000) as fc:
            page3.locator('#s-photo [data-act="addPhoto"]').click()
        chooser_ok = fc.value is not None
    except Exception:  # noqa: BLE001
        chooser_ok = False
    check("+ 사진 추가가 파일 선택창을 엽니다", chooser_ok)
    # 앨범·날짜 수정은 사진 상세의 「정보 수정」에서 그대로
    page3.locator("#s-photo .pola").first.click()
    page3.wait_for_timeout(500)
    page3.locator('#sheet [data-act="photoEdit"]').click()
    page3.wait_for_timeout(500)
    check("정보 수정에 앨범 칸", page3.locator('#sheet input[name="album"]').count() == 1)
    check("정보 수정에 날짜 칸", page3.locator('#sheet input[name="date"]').count() == 1)
    page3.keyboard.press("Escape")
    page3.wait_for_timeout(300)
    page3.keyboard.press("Escape")
    page3.wait_for_timeout(400)

    # 다크 모드 프레임
    page3.evaluate("document.documentElement.setAttribute('data-mode','dark')")
    page3.wait_for_timeout(400)
    darkbg = page3.evaluate("() => getComputedStyle(document.querySelector('#s-photo .pola')).backgroundColor")
    check("다크 모드엔 짙은 프레임", darkbg == "rgb(35, 35, 38)", darkbg)
    shot(page3, "photo-dark-v17.png", settle=500)
    page3.evaluate("document.documentElement.setAttribute('data-mode','light')")
    page3.wait_for_timeout(300)
    check("사진첩 콘솔 오류 없음", len(errs3) == 0, errs3[:2])
    ctx3.close()

    # ==================================================================
    # 8. 좁은 화면(375px) — 팔레트 4열 유지·넘침 없음
    # ==================================================================
    ctx2 = browser.new_context(viewport={"width": 375, "height": 812}, is_mobile=True, has_touch=True)
    page2 = ctx2.new_page()
    errs2 = []
    page2.on("pageerror", lambda e: errs2.append(str(e)))
    page2.on("console", lambda m: errs2.append(m.text) if m.type == "error" else None)
    page2.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page2.wait_for_timeout(800)
    page2.locator('#s-home [data-act="openTheme"]').click()
    page2.wait_for_timeout(500)
    over = page2.evaluate("""() => {
      const s = document.querySelector('#sheet');
      const grid = document.querySelector('.sw-grid[data-sw="homeTitleBg"]');
      const els = Array.from(grid.querySelectorAll('.sw'));
      return {sheet: s.scrollWidth - s.clientWidth,
              cols: getComputedStyle(grid).gridTemplateColumns.split(' ').length,
              rows: new Set(els.map(e => Math.round(e.getBoundingClientRect().y))).size,
              right: Math.max.apply(null, els.map(e => e.getBoundingClientRect().right))};
    }""")
    check("375px 팔레트 4열 3줄", over["cols"] == 4 and over["rows"] == 3, over)
    check("375px 시트 넘침 없음", over["sheet"] <= 1 and over["right"] <= 375, over)
    check("375px 콘솔 오류 없음", len(errs2) == 0, errs2[:2])
    ctx2.close()

    # ==================================================================
    # 8. 서비스워커 — v17, skipWaiting/clients.claim/옛 캐시 삭제, 새 버전이면 한 번 새로고침
    # ==================================================================
    sw_src = page.evaluate("fetch('sw.js', {cache:'no-store'}).then(r => r.text())")
    check("sw 캐시 v17", "twolog-v17" in sw_src, (sw_src or "")[:60])
    check("sw install 에서 skipWaiting", "self.skipWaiting()" in sw_src)
    check("sw activate 에서 clients.claim", "self.clients.claim()" in sw_src)
    check("sw 옛 캐시 삭제", "caches.delete(k)" in sw_src)
    app_src = page.evaluate("fetch('app.js', {cache:'no-store'}).then(r => r.text())")
    check("app 이 controllerchange 를 듣고 새로고침",
          "controllerchange" in app_src and "location.reload()" in app_src)
    check("app 이 표시될 때마다 reg.update()", "reg.update()" in app_src and "visibilitychange" in app_src)
    check("app 이 pageshow·online 에서도 확인", "pageshow" in app_src and "online" in app_src)

    reg = page.evaluate("""() => navigator.serviceWorker.getRegistration().then(r => r ? {
        active: !!r.active, scope: r.scope } : null)""")
    check("서비스워커 등록·활성", bool(reg and reg["active"]), reg)
    ctrl = page.evaluate("() => !!navigator.serviceWorker.controller")
    check("현재 페이지가 서비스워커 제어 중", ctrl is True, ctrl)

    # 새 버전 배포 흉내: sw.js 본문이 바뀌면 controllerchange → 새로고침 한 번
    marker_before = page.evaluate("() => { window.__v17mark = 1; return window.__v17mark; }")
    SW_OVERRIDE["body"] = sw_src + "\n/* v17 test: 새 버전 */\n"
    page.evaluate("() => navigator.serviceWorker.getRegistration().then(r => r.update())")
    reloaded = True
    try:
        page.wait_for_function("() => window.__v17mark === undefined", timeout=15000)
    except Exception:  # noqa: BLE001
        reloaded = False
    check("새 sw.js 가 오면 스스로 새로고침", reloaded, None if reloaded else "새로고침 없음")
    page.wait_for_timeout(900)
    check("새로고침 뒤에도 화면 정상", page.locator("#tabbar .tab").count() == 5,
          page.locator("#tabbar .tab").count())
    ctrl2 = page.evaluate("() => !!navigator.serviceWorker.controller")
    check("새로고침 뒤에도 제어 중", ctrl2 is True, ctrl2)
    page.evaluate("() => { window.__v17mark2 = 1; }")
    page.wait_for_timeout(2500)
    check("새로고침은 한 번만(두 번째 없음)",
          page.evaluate("() => window.__v17mark2") == 1, marker_before)
    shot(page, "home-v17.png", settle=600)

    check("콘솔 오류 없음", len(errors) == 0, errors[:3])
    browser.close()

print()
print("실패:", fails if fails else "없음")
print("스크린샷:", SHOT)
sys.exit(1 if fails else 0)
