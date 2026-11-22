"""투로그 v36 확인 — 노트 중복 정리 · 동기화 덮어쓰기 방지 · 카테고리 시트 UI.

1) 버전: sw.js 캐시 twolog-v46 · APP_VERSION v46 · My 탭 「버전 v46」
2) 노트 중복 정리 (이 폰)
   - 같은 카드 안에 같은 내용이 두 번 들어 있으면 하나로: 체크(done)한 쪽이 살아남고
     상세 메모가 있는 쪽이 살아남음 · 같은 내용이라도 다른 카드/다른 kind 면 그대로
   - 정리한 결과가 폰(localStorage)에도 저장됨
3) 노트 중복 정리 (서버)
   - 서버(notes)에 겹쳐 들어간 중복 행이 실제로 지워지고, 새로 열어도 다시 생기지 않음
4) 카드 복구(repairGroups) — 공백만 다른 같은 항목을 새 행으로 또 넣지 않음
5) 저장 중 Realtime — 체크한 직후 서버를 다시 읽어도 체크가 풀리지 않음
6) 카테고리 + 시트
   - 노트 상단 + 버튼이 ≡ 없는 깨끗한 + 모양
   - 이름 칸이 네모 테두리가 아닌 밑줄 스타일 · 옆에 「추가」 버튼
   - 「추가」/엔터 → 목록에 바로 한 줄로 붙고, 그 자리에서 이름 확인·순서 이동
   - 「저장하기」로 확정 · 그냥 닫으면 버려짐 · 입력칸에 적고 바로 저장해도 추가(호환)
   - 안내 문구가 「노트 카테고리」 라벨 바로 아래(목록 위)에 있음
7) ≡ 드래그 — 끌고 있는 줄은 손가락을 따라가고(transform), 다른 줄은 FLIP 으로 미끄러지고,
   놓으면 제자리로 정리됨 · touch-action:none
8) 콘솔/페이지 오류 0건

    python3 tests/v36.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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


def tab(page, idx, wait=450):
    page.locator("#tabbar .tab").nth(idx).click()
    page.wait_for_timeout(wait)


def note_tab(page):
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(900)
    tab(page, 2, 650)


def open_add_sheet(page):
    page.locator("#s-diary .hdr .note-add").click()
    page.wait_for_timeout(650)


def rows_state(page):
    return page.evaluate("""() => Array.from(document.querySelectorAll('#sheet #noteOrderList .nord-row'))
      .map(r => ({key: r.getAttribute('data-key'),
                  name: ((r.querySelector('.nord-nm') || {}).value || ''),
                  del: !!r.querySelector('.nord-del'),
                  temp: r.classList.contains('nord-temp')}))""")


def drag_row(page, key, to_key, below=False, hold=None):
    """≡ 손잡이를 끌어 다른 줄 위/아래로 옮깁니다. hold 를 주면 놓기 직전 상태를 찍어 돌려줍니다."""
    grip = page.locator("#sheet #noteOrderList .nord-row[data-key='%s'] .nord-grip" % key).first
    gb = grip.bounding_box()
    target = page.locator("#sheet #noteOrderList .nord-row[data-key='%s']" % to_key).first.bounding_box()
    sx, sy = gb["x"] + gb["width"] / 2, gb["y"] + gb["height"] / 2
    ty = target["y"] + (target["height"] * 0.8 if below else target["height"] * 0.2)
    page.mouse.move(sx, sy)
    page.mouse.down()
    page.wait_for_timeout(80)
    steps = 10
    for i in range(1, steps + 1):
        page.mouse.move(sx, sy + (ty - sy) * i / steps)
        page.wait_for_timeout(20)
    mid = None
    if hold:
        page.wait_for_timeout(40)
        mid = hold(page)
    page.mouse.up()
    page.wait_for_timeout(400)
    return mid


def notes_state(page):
    return page.evaluate("""() => {
      const S = window.__app.state;
      return {
        todo: (S.todos || []).map(t => ({id: t.id, text: t.text, done: !!t.done, memo: t.memo || '', gid: t.gid || ''})),
        bucket: (S.bucket || []).map(b => ({id: b.id, title: b.title, done: !!b.done})),
        logs: (S.logs || []).map(l => ({id: l.id, kind: l.kind, title: l.title, review: l.review || ''})),
        lists: (S.lists || []).map(l => ({id: l.id, title: l.title, items: (l.items || []).map(i => ({text: i.text, done: !!i.done}))}))
      };
    }""")


def stored_state(page):
    return page.evaluate("""() => {
      try { return JSON.parse(localStorage.getItem('twolog:v1:state') || 'null'); } catch (e) { return null; }
    }""")


def stub_notes(page):
    return page.evaluate("() => (window.__stub.notes || []).map(r => ({id: r.id, kind: r.kind, deleted: !!r.deleted, payload: r.payload}))")


# ---------------------------------------------------------------- 공통 씨앗
def base_doc():
    return {
        "couple": {"me": "소영", "you": "준영", "since": "2025-11-19", "fmt": "D", "phrase": "함께한 지",
                   "colors": {"me": "#9E636B", "you": "#3D5C82"},
                   "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}},
        "link": {"code": "371502", "connected": True, "partnerCode": ""},
        "auth": {"out": False, "email": ""},
        "theme": {"name": None, "log": None, "mode": "light"},
        "mig": {"palette": 1, "you": 1, "phrase": 1, "homeBg": 1, "noteEmo": 1},
        "events": [], "photos": [], "expenses": [],
        "notif": {"anni": True, "today": True, "dday": False},
        "groups": {
            "todo": [{"id": "g1", "title": "메모 카드", "caption": ""}],
            "bucket": [{"id": "g2", "title": "버킷 카드", "caption": ""}],
            "log": [{"id": "g3", "title": "영화 카드", "caption": ""}]
        }
    }


def dup_doc():
    d = base_doc()
    d["todos"] = [
        {"id": "t1", "text": "나무도마", "done": False, "who": "함께", "gid": "g1"},
        {"id": "t2", "text": "잠옷긴거", "done": True, "who": "함께", "gid": "g1"},
        {"id": "t3", "text": "나무도마", "done": False, "who": "함께", "gid": "g1"},
        {"id": "t4", "text": "잠옷긴거", "done": False, "who": "함께", "gid": "g1"},
        {"id": "t5", "text": "침대프레임", "done": False, "who": "함께", "gid": "g1", "memo": "상세 메모"},
        {"id": "t6", "text": "침대프레임", "done": False, "who": "함께", "gid": "g1"},
        # 같은 내용이라도 다른 카드는 그대로 둡니다
        {"id": "t7", "text": "나무도마", "done": False, "who": "함께", "gid": "g9"}
    ]
    d["groups"]["todo"].append({"id": "g9", "title": "다른 카드", "caption": ""})
    d["bucket"] = [
        {"id": "b1", "title": "제주 여행", "done": True, "cat": "여행", "gid": "g2"},
        {"id": "b2", "title": "제주 여행", "done": False, "cat": "여행", "gid": "g2"}
    ]
    d["logs"] = [
        {"id": "l1", "kind": "movie", "title": "인터스텔라", "date": "2026-11-01", "rating": 4,
         "review": "좋았다", "done": True, "gid": "g3"},
        {"id": "l2", "kind": "movie", "title": "인터스텔라", "date": "2026-11-01", "rating": 0,
         "review": "", "done": True, "gid": "g3"},
        {"id": "l3", "kind": "food", "title": "인터스텔라", "date": "2026-11-01", "rating": 5,
         "review": "", "done": True, "gid": "g3"}
    ]
    d["lists"] = [{"id": "c1", "title": "장보기", "emoji": "", "kind": "check", "items": [
        {"id": "i1", "text": "우유", "done": False},
        {"id": "i2", "text": "우유", "done": True},
        {"id": "i3", "text": "계란", "done": False}
    ]}]
    d["noteOrder"] = ["todo", "bucket", "log", "list:c1"]
    d["note"] = {"todo": {"e": "", "n": "메모"}, "bucket": {"e": "", "n": "버킷리스트"}, "log": {"e": "", "n": "영화·먹방"}}
    return d


def remote_seed(db, user_id, email):
    return """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: %s, email: %s } }));
    })();""" % (json.dumps(json.dumps(db, ensure_ascii=False)), json.dumps(user_id), json.dumps(email))


def remote_db(cid, uid_, email, notes, settings=None):
    return {
        "users": {uid_: {"id": uid_, "email": email, "password": "pw123456"}},
        "couples": [{"id": cid, "invite_code": "482913", "members": [uid_],
                     "me": "소영", "you": "준영", "since": "2025-11-19", "phrase": "함께한 지", "fmt": "D",
                     "colors": {"me": "#9E636B", "you": "#3D5C82"},
                     "sched": {"me": "#9E636B", "you": "#3D5C82", "both": "#625A7F"}}],
        "events": [], "photos": [],
        "notes": notes,
        "settings": settings or [],
        "uploads": [], "seq": 40
    }


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전 · 노트 상단 + 버튼 모양
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    watch(page, errs)

    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    check("sw.js 캐시 버전 twolog-v46", 'const VERSION = "twolog-v46"' in sw,
          re.search(r'const VERSION = "[^"]+"', sw))
    check("app.js 버전 상수 v44", 'var APP_VERSION = "v46"' in app_js,
          re.search(r'var APP_VERSION = "[^"]+"', app_js))
    check("sw.js 캐시 목록 이름이 shell-twolog-v46", 'const SHELL = "shell-" + VERSION' in sw)

    note_tab(page)
    hdr = page.evaluate("""() => {
      const b = document.querySelector('#s-diary .hdr .note-add');
      return {html: b ? b.innerHTML : '', label: b ? b.getAttribute('aria-label') : ''};
    }""")
    check("노트 상단 + 버튼이 ≡ 없는 ＋ 만", "M12 5.5v13M5.5 12h13" in hdr["html"] and "M4.6 6.4h9.2" not in hdr["html"],
          hdr["html"][:120])
    check("노트 상단 + 버튼 이름 유지", "새 카테고리" in (hdr["label"] or ""), hdr["label"])

    tab(page, 4, 500)
    ver = page.evaluate("(document.querySelector('#s-set .app-ver') || {}).textContent || ''")
    check("My 탭 맨 위에 「버전 v46」", ver.strip() == "버전 v46", ver)
    tab(page, 2, 500)

    # ==================================================================
    # 2. 카테고리 + 시트 — 안내 문구 위치·밑줄 칸·추가 버튼
    # ==================================================================
    open_add_sheet(page)
    lay = page.evaluate("""() => {
      const hint = document.querySelector('#sheet .nord-hint');
      const list = document.querySelector('#sheet #noteOrderList');
      const lbl = document.querySelector('#sheet .set-lbl');
      const inp = document.querySelector('#sheet input[name="title"]');
      const btn = document.querySelector('#sheet .nord-add-btn');
      const cs = inp ? getComputedStyle(inp) : null;
      const bb = inp && btn ? {i: inp.getBoundingClientRect(), b: btn.getBoundingClientRect()} : null;
      return {
        hintNext: hint && hint.nextElementSibling ? hint.nextElementSibling.id : '',
        hintPrev: hint && hint.previousElementSibling ? (hint.previousElementSibling.className || '') : '',
        hintPrevTxt: hint && hint.previousElementSibling ? hint.previousElementSibling.textContent.trim() : '',
        hintText: hint ? hint.textContent.trim() : '',
        hintAboveList: hint && list ? (hint.compareDocumentPosition(list) & Node.DOCUMENT_POSITION_FOLLOWING) > 0 : false,
        lblTxt: lbl ? lbl.textContent.trim() : '',
        cls: inp ? inp.className : '',
        border: cs ? [cs.borderTopWidth, cs.borderRightWidth, cs.borderLeftWidth, cs.borderBottomWidth] : [],
        radius: cs ? cs.borderRadius : '',
        btnTxt: btn ? btn.textContent.trim() : '',
        sameRow: bb ? (Math.abs(bb.i.top - bb.b.top) < 16 && bb.b.left > bb.i.left + bb.i.width - 30) : false
      };
    }""")
    check("안내 문구가 목록 바로 위에 있음", lay["hintNext"] == "noteOrderList", lay["hintNext"])
    check("안내 문구 위가 「노트 카테고리」 라벨", lay["hintPrevTxt"] == "노트 카테고리", lay["hintPrevTxt"])
    # v39: 안내에 「줄을 누르면 속지 고르기」가 더해짐 — ≡ 드래그 안내는 그대로 남아 있음
    check("안내 문구 내용 그대로", "줄을 누르면" in lay["hintText"] and "≡ 를 끌면" in lay["hintText"], lay["hintText"])
    check("이름 칸이 네모 테두리가 아닌 밑줄 스타일",
          lay["border"][:3] == ["0px", "0px", "0px"] and lay["border"][3] not in ("0px", ""), lay["border"])
    check("이름 칸 모서리가 각지고 .field 네모칸이 아님",
          lay["radius"] in ("0px", "0") and "field" not in lay["cls"], (lay["radius"], lay["cls"]))
    check("이름 칸 옆 같은 줄에 「추가」 버튼", lay["btnTxt"] == "추가" and lay["sameRow"],
          (lay["btnTxt"], lay["sameRow"]))
    page.screenshot(path=os.path.join(SHOT, "note-v36-addsheet.png"))

    # ==================================================================
    # 3. 「추가」·엔터 → 목록에 바로 붙고, 그 자리에서 순서 이동 → 저장
    # ==================================================================
    page.fill("#sheet .nord-new", "장보기")
    page.locator("#sheet .nord-add-btn").click()
    page.wait_for_timeout(350)
    r1 = rows_state(page)
    check("「추가」를 누르면 목록 맨 아래에 새 줄", r1[-1]["key"].startswith("new:") and r1[-1]["name"] == "장보기",
          [(r["key"], r["name"]) for r in r1])
    check("붙은 줄에 ≡ 손잡이와 삭제 버튼", page.evaluate(
        "() => { const r = document.querySelector('#sheet #noteOrderList .nord-row.nord-temp');"
        " return !!r && !!r.querySelector('.nord-grip') && !!r.querySelector('.nord-del'); }"))
    check("추가 뒤 입력칸은 비워짐", page.evaluate("document.querySelector('#sheet .nord-new').value") == "")
    temp_key = r1[-1]["key"]

    page.fill("#sheet .nord-new", "여행")
    page.locator("#sheet .nord-new").press("Enter")
    page.wait_for_timeout(400)
    r2 = rows_state(page)
    check("엔터로도 목록에 붙음", r2[-1]["name"] == "여행" and r2[-1]["key"].startswith("new:"),
          [(r["key"], r["name"]) for r in r2])
    check("엔터로 붙어도 시트는 닫히지 않음",
          page.evaluate("document.getElementById('sheetWrap').classList.contains('open')"))
    # 붙인 줄을 지우면 목록에서만 빠짐
    page.locator("#sheet #noteOrderList .nord-row[data-key='%s'] .nord-del" % r2[-1]["key"]).click()
    page.wait_for_timeout(300)
    check("붙인 줄의 삭제 버튼으로 목록에서 뺌",
          all(r["name"] != "여행" for r in rows_state(page)), [r["name"] for r in rows_state(page)])

    # 드래그 중 모습 — 손가락을 따라가고, 다른 줄은 FLIP 으로 미끄러짐
    def hold_state(pg):
        return pg.evaluate("""() => {
          const box = document.querySelector('#sheet #noteOrderList');
          const rows = Array.from(box.querySelectorAll('.nord-row'));
          const drag = rows.filter(r => r.classList.contains('dragging'))[0] || null;
          const others = rows.filter(r => r !== drag);
          return {
            n: rows.length,
            draggingKey: drag ? drag.getAttribute('data-key') : null,
            transform: drag ? (drag.style.transform || '') : '',
            z: drag ? drag.style.zIndex : '',
            shadow: drag ? getComputedStyle(drag).boxShadow : '',
            flip: others.map(r => ({key: r.getAttribute('data-key'),
                                    tr: r.style.transition || '',
                                    tf: r.style.transform || ''}))
          };
        }""")

    grip_ta = page.evaluate("getComputedStyle(document.querySelector('#sheet .nord-grip')).touchAction")
    check("손잡이 touch-action 이 none(스크롤과 충돌 없음)", grip_ta == "none", grip_ta)

    mid = drag_row(page, temp_key, "todo", below=False, hold=hold_state)
    check("끌고 있는 줄이 dragging 상태로 떠 있음", mid and mid["draggingKey"] == temp_key, mid)
    check("끌고 있는 줄이 손가락을 따라 translateY", mid and mid["transform"].startswith("translateY(")
          and mid["transform"] not in ("translateY(0px)", ""), mid and mid["transform"])
    check("끌고 있는 줄이 위로 떠 보임(그림자)", mid and mid["shadow"] not in ("none", ""), mid and mid["shadow"])
    check("다른 줄이 FLIP(transform 180ms)으로 자리를 비켜 줌",
          mid and any("transform 180ms" in o["tr"] for o in mid["flip"]),
          mid and mid["flip"])
    after_drag = rows_state(page)
    check("끌어 올린 줄이 맨 위로 이동", after_drag[0]["key"] == temp_key, [r["key"] for r in after_drag])
    settled = page.evaluate("""() => {
      const r = document.querySelector('#sheet #noteOrderList .nord-row');
      return {tr: r.style.transform || '', cls: r.className, tid: r.style.transition || ''};
    }""")
    check("놓으면 제자리로 정리(transform·dragging 없음)",
          settled["tr"] in ("", "translateY(0px)") and "dragging" not in settled["cls"], settled)
    page.screenshot(path=os.path.join(SHOT, "note-v36-drag.png"))

    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(900)
    saved = page.evaluate("""() => ({lists: window.__app.state.lists.map(l => l.title),
                                    order: window.__app.state.noteOrder,
                                    seg: window.__app.state.ui.seg})""")
    check("추가한 카테고리가 노트에 생김", saved["lists"] == ["장보기"], saved["lists"])
    new_key = saved["order"][0] if saved["order"] else ""
    check("끌어 올린 자리(맨 앞)에 그대로 저장", new_key.startswith("list:") and saved["seg"] == new_key,
          (saved["order"], saved["seg"]))
    first_chip = page.evaluate(
        "(document.querySelector('#s-diary .segs > button') || {}).textContent || ''").strip()
    check("노트 탭 첫 칸이 새 카테고리", first_chip == "장보기", first_chip)

    # 입력칸에 적고 바로 「저장하기」 (예전 방식 호환)
    open_add_sheet(page)
    page.fill("#sheet .nord-new", "호환")
    page.locator("#sheet .btn-primary").click()
    page.wait_for_timeout(900)
    check("입력칸에 적고 바로 저장해도 카테고리 추가(호환)",
          page.evaluate("window.__app.state.lists.map(l => l.title)") == ["장보기", "호환"],
          page.evaluate("window.__app.state.lists.map(l => l.title)"))

    # 붙였지만 저장하지 않고 닫으면 버려짐
    open_add_sheet(page)
    page.fill("#sheet .nord-new", "버림")
    page.locator("#sheet .nord-add-btn").click()
    page.wait_for_timeout(300)
    page.keyboard.press("Escape")
    page.wait_for_timeout(450)
    check("붙인 뒤 그냥 닫으면 카테고리로 남지 않음",
          page.evaluate("window.__app.state.lists.map(l => l.title)") == ["장보기", "호환"],
          page.evaluate("window.__app.state.lists.map(l => l.title)"))
    check("여기까지 페이지 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 4. 이 폰에서 노트 중복 정리
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    ctx.add_init_script("(() => { if (localStorage.getItem('twolog:v1:state')) return;"
                        " localStorage.setItem('twolog:v1:state', %s); })();"
                        % json.dumps(json.dumps(dup_doc(), ensure_ascii=False)))
    page = ctx.new_page()
    errs2 = []
    watch(page, errs2)
    note_tab(page)
    st = notes_state(page)
    check("메모: 같은 카드의 같은 줄이 하나로", [t["text"] for t in st["todo"]] ==
          ["나무도마", "잠옷긴거", "침대프레임", "나무도마"],
          [(t["text"], t["gid"]) for t in st["todo"]])
    check("메모: 체크한 쪽이 살아남음",
          [t["done"] for t in st["todo"] if t["text"] == "잠옷긴거" and t["gid"] == "g1"] == [True],
          st["todo"])
    check("메모: 상세 메모가 있는 쪽이 살아남음",
          [t["memo"] for t in st["todo"] if t["text"] == "침대프레임"] == ["상세 메모"], st["todo"])
    check("메모: 다른 카드의 같은 내용은 그대로", len([t for t in st["todo"] if t["gid"] == "g9"]) == 1,
          [t["text"] for t in st["todo"] if t["gid"] == "g9"])
    check("버킷: 중복 하나로 · 체크 유지", len(st["bucket"]) == 1 and st["bucket"][0]["done"], st["bucket"])
    check("영화·먹방: 같은 제목이라도 영화/먹방은 따로", len(st["logs"]) == 2 and set(l["kind"] for l in st["logs"]) == {"movie", "food"},
          st["logs"])
    check("내 카테고리 항목 중복 정리 · 체크 유지",
          len(st["lists"][0]["items"]) == 2 and
          [i["done"] for i in st["lists"][0]["items"] if i["text"] == "우유"] == [True],
          st["lists"][0]["items"])

    stored = stored_state(page)
    check("정리한 결과가 폰 저장본에도 반영", stored is not None and len(stored.get("todos", [])) == 4,
          stored and [t["text"] for t in stored["todos"]])

    # 카드 안에서 보면 같은 줄이 한 번만
    page.locator("#s-diary .ncard[data-gid='g1']").click()
    page.wait_for_timeout(600)
    rows = page.evaluate("""() => Array.from(document.querySelectorAll('#sheet .card-items .trow .t'))
        .map(e => e.textContent.trim())""")
    check("카드 안에 같은 줄이 한 번만", rows.count("나무도마") == 1 and rows.count("잠옷긴거") == 1, rows)
    page.screenshot(path=os.path.join(SHOT, "note-v36-dedupe.png"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(350)

    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=20000)
    page.wait_for_timeout(900)
    st2 = notes_state(page)
    check("새로 열어도 다시 늘지 않음", len(st2["todo"]) == 4 and len(st2["bucket"]) == 1, (len(st2["todo"]), len(st2["bucket"])))
    check("중복 정리 중 오류 없음", len(errs2) == 0, errs2[:3])
    ctx.close()

    # ==================================================================
    # 5. 서버(notes)의 중복 행이 실제로 지워짐
    # ==================================================================
    cid, uid_, mail = "couple-dup", "user-dup", "dup@twolog.app"
    db = remote_db(cid, uid_, mail, [
        {"id": "n1", "couple_id": cid, "kind": "todo", "sort": 0, "deleted": False,
         "payload": {"text": "나무도마", "done": False, "who": "both", "gid": "g1"}},
        {"id": "n2", "couple_id": cid, "kind": "todo", "sort": 1, "deleted": False,
         "payload": {"text": "나무도마", "done": False, "who": "both", "gid": "g1"}},
        {"id": "n3", "couple_id": cid, "kind": "todo", "sort": 2, "deleted": False,
         "payload": {"text": "잠옷긴거", "done": True, "who": "both", "gid": "g1"}},
        {"id": "n4", "couple_id": cid, "kind": "todo", "sort": 3, "deleted": False,
         "payload": {"text": "잠옷긴거", "done": False, "who": "both", "gid": "g1"}},
        {"id": "n5", "couple_id": cid, "kind": "bucket", "sort": 4, "deleted": False,
         "payload": {"title": "제주 여행", "done": True, "cat": "여행", "gid": "g2"}},
        {"id": "n6", "couple_id": cid, "kind": "bucket", "sort": 5, "deleted": False,
         "payload": {"title": "제주 여행", "done": False, "cat": "여행", "gid": "g2"}},
    ], [{"couple_id": cid, "key": "groups", "value": {
        "todo": [{"id": "g1", "title": "메모 카드", "caption": ""}],
        "bucket": [{"id": "g2", "title": "버킷 카드", "caption": ""}],
        "log": [{"id": "g3", "title": "영화 카드", "caption": ""}]}}])
    ctx = new_ctx(browser)
    ctx.add_init_script(remote_seed(db, uid_, mail))
    page = ctx.new_page()
    errs3 = []
    watch(page, errs3)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2600)
    rows5 = stub_notes(page)
    texts = sorted(r["payload"].get("text") or r["payload"].get("title") for r in rows5)
    check("서버 notes 의 중복 행이 지워짐", len(rows5) == 3, [(r["id"], r["payload"]) for r in rows5])
    check("서버에 남은 줄이 하나씩", texts == ["나무도마", "잠옷긴거", "제주 여행"], texts)
    done_map = {r["payload"].get("text") or r["payload"].get("title"): r["payload"].get("done") for r in rows5}
    check("서버에도 체크한 쪽이 남음", done_map.get("잠옷긴거") is True and done_map.get("제주 여행") is True, done_map)
    page.reload(wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2200)
    check("다시 열어도 서버에 중복이 다시 생기지 않음", len(stub_notes(page)) == 3, len(stub_notes(page)))
    live = notes_state(page)
    check("화면에도 줄이 하나씩", [t["text"] for t in live["todo"]] == ["나무도마", "잠옷긴거"], live["todo"])
    check("서버 중복 정리 중 오류 없음", len(errs3) == 0, errs3[:3])
    ctx.close()

    # ==================================================================
    # 6. 카드 복구(repairGroups) — 공백만 다른 항목을 또 넣지 않음
    # ==================================================================
    cid2, uid2, mail2 = "couple-rep", "user-rep", "rep@twolog.app"
    db2 = remote_db(cid2, uid2, mail2, [
        {"id": "r1", "couple_id": cid2, "kind": "todo", "sort": 0, "deleted": False,
         "payload": {"text": "나무도마 ", "done": False, "who": "both"}}          # gid 없음 + 뒤 공백
    ])
    local = base_doc()
    local["todos"] = [{"id": "loc1", "text": "나무도마", "done": False, "who": "함께", "gid": "g1"}]
    ctx = new_ctx(browser)
    ctx.add_init_script(remote_seed(db2, uid2, mail2))
    ctx.add_init_script("(() => { if (localStorage.getItem('twolog:v1:state')) return;"
                        " localStorage.setItem('twolog:v1:state', %s); })();"
                        % json.dumps(json.dumps(local, ensure_ascii=False)))
    page = ctx.new_page()
    errs4 = []
    watch(page, errs4)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2800)
    rows6 = stub_notes(page)
    check("공백만 다른 항목을 새 행으로 또 넣지 않음", len(rows6) == 1,
          [(r["id"], r["payload"]) for r in rows6])
    check("복구가 그 행에 카드(gid)를 채워 넣음", rows6 and rows6[0]["payload"].get("gid") == "g1",
          rows6[0]["payload"] if rows6 else None)
    check("화면에도 항목 하나", len([t for t in notes_state(page)["todo"]]) == 1, notes_state(page)["todo"])
    check("카드 복구 중 오류 없음", len(errs4) == 0, errs4[:3])
    ctx.close()

    # ==================================================================
    # 7. 저장 중 Realtime — 체크가 풀리지 않음
    # ==================================================================
    cid3, uid3, mail3 = "couple-rt", "user-rt", "rt@twolog.app"
    db3 = remote_db(cid3, uid3, mail3, [
        {"id": "x1", "couple_id": cid3, "kind": "todo", "sort": 0, "deleted": False,
         "payload": {"text": "체크할 일", "done": False, "who": "both", "gid": "g1"}}
    ], [{"couple_id": cid3, "key": "groups", "value": {
        "todo": [{"id": "g1", "title": "메모 카드", "caption": ""}],
        "bucket": [{"id": "g2", "title": "버킷 카드", "caption": ""}],
        "log": [{"id": "g3", "title": "영화 카드", "caption": ""}]}}])
    ctx = new_ctx(browser)
    ctx.add_init_script(remote_seed(db3, uid3, mail3))
    page = ctx.new_page()
    errs5 = []
    watch(page, errs5)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2600)
    tab(page, 2, 650)
    page.locator("#s-diary .ncard[data-gid='g1']").click()
    page.wait_for_timeout(600)
    check("카드 안에 체크할 줄이 있음", page.evaluate("document.querySelectorAll('#sheet .card-items .trow').length") == 1)

    # 서버 쓰기만 늦게 끝나게 해서 «저장이 끝나기 전에 Realtime 이 오는» 상황을 만듭니다
    page.evaluate("() => { window.__STUB_WRITE_DELAY = 1200; }")
    page.locator("#sheet .card-items .trow .circ").click()
    page.wait_for_timeout(420)
    busy = page.evaluate("() => !!window.TwoLogStore.backend.saving")
    check("체크하면 서버 저장이 진행 중", busy is True, busy)
    # 아직 서버에는 체크가 닿지 않은 상태 — 상대가 준 것처럼 예전 값을 되돌려 두고 Realtime 을 보냅니다
    page.evaluate("""(cid) => {
      const st = window.__stub;
      const r = (st.notes || []).filter(x => x.id === 'x1')[0];
      r.payload.done = false;
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      return window.__stubEmit('notes', cid);
    }""", cid3)
    page.wait_for_timeout(2400)
    rt = page.evaluate("""() => ({
      done: (window.__app.state.todos || [])[0].done,
      rowDone: !!document.querySelector('#sheet .card-items .trow.done'),
      saved: ((window.__stub.notes || []).filter(x => x.id === 'x1')[0] || {payload: {}}).payload.done
    })""")
    check("저장 중 Realtime 이 와도 방금 체크가 풀리지 않음", rt["done"] is True, rt)
    check("화면의 체크 표시도 그대로", rt["rowDone"] is True, rt)
    check("서버에도 체크가 남음", rt["saved"] is True, rt)
    check("동기화 보호 중 오류 없음", len(errs5) == 0, errs5[:3])
    page.screenshot(path=os.path.join(SHOT, "note-v36-realtime.png"))
    ctx.close()

    browser.close()

print()
if fails:
    print("FAILED %d" % len(fails))
    for f in fails:
        print("  - " + f)
    sys.exit(1)
print("ALL PASS")
