"""투로그 v26 확인 — 폰에 남아 있던 로컬 기록(localStorage·IndexedDB)을 새 커플 공간으로
자동 1회 이전(merge)하고, 다시 로그인해도 중복되지 않는지 확인합니다.

1) 버전: sw.js 캐시 twolog-v31 · APP_VERSION v31
2) 로컬 모드에서 일정·메모·사진을 만들고 → 원격(remote)에 처음 로그인
   → 자동으로 그 기록들이 살아나고(일정·노트·사진·커플 정보) 플래그가 남음
   → 새로 열기/다시 로그인해도 중복 없음, 폰의 원본 데이터는 그대로
3) 원격에 이미 기록이 있으면 자동 이전은 하지 않고, My 탭 「폰에 있던 예전 기록 가져오기」로
   겹치지 않게 더함 (상대가 정한 커플 정보는 건드리지 않음)
4) 새 기기(로컬 기록 없음)에서는 아무 일도 일어나지 않음 · 예전 프로토타입 키도 읽음
5) local 모드(?sync=local)는 예전 그대로

    python3 tests/v26.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import base64, functools, http.server, json, os, re, socketserver, sys, tempfile, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

STUB = open(os.path.join(HERE, "stub-supabase.js")).read()
ESM = re.compile(r"https://esm\.sh/.*")

# smoke.py 의 테스트 사진을 그대로 씁니다 (중복 정의 피하기)
_smoke = open(os.path.join(HERE, "smoke.py")).read()
_blob = re.search(r"JPEG_B64 = \((.*?)\)\n", _smoke, re.S).group(1)
JPEG_B64 = "".join(re.findall(r'"([^"]*)"', _blob))

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

JPG = os.path.join(tempfile.mkdtemp(), "v26-photo.jpg")
with open(JPG, "wb") as f:
    f.write(base64.b64decode(JPEG_B64))


def new_ctx(browser, **kw):
    args = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True,
                device_scale_factor=2)
    args.update(kw)
    return browser.new_context(**args)


def stub_route(page):
    page.route(ESM, lambda route: route.fulfill(status=200, content_type="application/javascript", body=STUB))


def stub(page, table):
    return page.evaluate("(t) => (window.__stub && window.__stub[t]) ? window.__stub[t] : []", table)


def body_text(page):
    return page.evaluate("document.body.innerText.replace(/\\s+/g, ' ').trim()")


def migrated_keys(page):
    return page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('twolog.migrated.') === 0)")


def local_state_raw(page):
    return page.evaluate("localStorage.getItem('twolog:v1:state')")


def signup(page, email, pw):
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', email)
    page.fill('#s-login input[name="password"]', pw)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    check("sw.js 캐시 버전 twolog-v31", 'const VERSION = "twolog-v31"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:1])
    check("app.js 버전 상수 v31", 'var APP_VERSION = "v31"' in app_js)
    check("sync.js 에 이전 로직(Store.migrate) 있음",
          "migrateLocal" in page.request.get(URL + "sync.js").text())
    ctx.close()

    # ==================================================================
    # 2. 로컬 기록 → 처음 로그인할 때 자동 이전
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)

    # --- 2-1. 로컬 모드에서 진짜로 기록을 만듭니다 (일정 · 메모 · 사진)
    page.goto(URL + "?sync=local", wait_until="networkidle")
    page.wait_for_timeout(600)
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(400)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(350)
    page.fill('#sheetForm input[name="title"]', "폰에 있던 크리스마스")
    page.locator("#evSave").click()
    page.wait_for_timeout(600)

    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(450)
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(400)
    page.fill('#sheet #listAddForm input[name="text"]', "폰에 있던 장보기")
    page.click("#sheet .todo-add-btn")
    page.wait_for_timeout(450)
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)

    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(300)
    page.set_input_files("#photoInput", [JPG])
    page.wait_for_timeout(600)
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(1800)
    local_made = page.evaluate("""(() => {
      const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      return {events: (s.events || []).length, todos: (s.todos || []).length,
              photos: (s.photos || []).length,
              pathes: (s.photos || []).map(p => p.path || ''),
              pola: document.querySelectorAll('#s-photo .pola').length};
    })()""")
    check("로컬 모드에서 일정·메모·사진을 만듦",
          local_made["events"] >= 1 and local_made["todos"] >= 1 and local_made["photos"] == 1,
          local_made)
    check("로컬 사진은 IndexedDB 경로(idb:)로 저장", str(local_made["pathes"][0]).startswith("idb:"),
          local_made["pathes"])

    # 프로필 사진도 로컬에만 있던 상태 (v26 이전)
    page.set_input_files("#avatarInput", JPG)
    page.wait_for_timeout(900)
    page.locator("#avcApply").click()          # v27: 동그라미 가이드에서 잘라 적용
    page.wait_for_timeout(1600)
    local_pic = page.evaluate("""(() => {
      const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      const pics = (s.couple || {}).pics || {};
      return {me: (pics.me || '').slice(0, 22), len: (pics.me || '').length};
    })()""")
    check("로컬 모드: 프로필 사진이 이 기기에만 저장됨", local_pic["me"] == "data:image/jpeg;base64" and local_pic["len"] > 500, local_pic)

    # --- 2-2. 커플 정보(만난 날·이름)를 앱 API 로 바꿔 둡니다 (화면에서 바꾼 것과 같은 상태)
    page.evaluate("""() => {
      const S = window.TwoLogUI.state;
      S.couple.since = '2024-05-01';
      S.couple.me = '박소영';
      S.couple.you = '이준영';
      return window.TwoLogStore.flush();
    }""")
    page.wait_for_timeout(400)
    before_raw = local_state_raw(page)
    before = page.evaluate("JSON.parse(localStorage.getItem('twolog:v1:state'))")
    check("이전 전 로컬 상태에 사용자가 만든 기록·설정이 있음",
          len(before["events"]) >= 1 and before["couple"]["since"] == "2024-05-01", before["couple"])

    # --- 2-3. 원격 모드로 열어 처음 가입 → 자동 이전
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    EMAIL = "migrate.first@twolog.app"
    signup(page, EMAIL, "twolog1234")
    page.wait_for_timeout(2500)

    after = page.evaluate("""(() => {
      const S = (window.TwoLogUI || {}).state || {};
      return {me: (S.couple || {}).me, you: (S.couple || {}).you, since: (S.couple || {}).since,
              events: (S.events || []).length, todos: (S.todos || []).length,
              photos: (S.photos || []).length,
              titles: (S.events || []).map(e => e.title),
              texts: (S.todos || []).map(t => t.text),
              toast: (document.getElementById('toast') || {}).textContent || '',
              coupleId: (window.TwoLogStore || {}).coupleId};
    })()""")
    check("자동 이전: 일정이 새 커플 공간에 살아남", "폰에 있던 크리스마스" in after["titles"], after["titles"])
    check("자동 이전: 메모(할일)도 살아남", "폰에 있던 장보기" in after["texts"], after["texts"])
    check("자동 이전: 사진도 살아남", after["photos"] == 1, after["photos"])
    check("자동 이전: 커플 정보(이름·만난 날)도 살아남",
          after["me"] == "박소영" and after["you"] == "이준영" and after["since"] == "2024-05-01",
          {k: after[k] for k in ("me", "you", "since")})
    check("이전 안내를 토스트로 알려 줌", "이어 왔어요" in after["toast"], after["toast"])

    dday = page.evaluate("""() => {
      const num = document.querySelector('#s-home .dday-num');
      const iso = (d) => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
      const now = new Date();
      const since = new Date(2024, 4, 1);
      return {text: num ? num.textContent.trim() : '',
              want: 'D+' + Math.max(0, Math.round((new Date(iso(now)) - since) / 86400000))};
    }""")
    check("홈 D-day 이 옮겨 온 만난 날 기준", dday["text"] == dday["want"], dday)

    ev_rows = stub(page, "events")
    note_rows = stub(page, "notes")
    photo_rows = stub(page, "photos")
    uploads = stub(page, "uploads")
    check("원격 events 행이 만들어짐", len(ev_rows) == 1 and ev_rows[0]["title"] == "폰에 있던 크리스마스", ev_rows)
    check("원격 notes 행이 만들어짐(할일)", len(note_rows) == 1 and note_rows[0]["payload"]["text"] == "폰에 있던 장보기", note_rows)
    check("원격 photos 행 + Storage 업로드",
          len(photo_rows) == 1 and str(photo_rows[0]["storage_path"]).endswith(".jpg") and len(uploads) == 1,
          (photo_rows, uploads))
    check("사진 원본이 실제로 업로드됨(빈 파일 아님)", uploads and uploads[0]["size"] > 500, uploads)
    check("사진 Storage 경로가 <coupleId>/<id>.jpg 규칙",
          photo_rows and str(photo_rows[0]["storage_path"]).startswith(str(after["coupleId"]) + "/"),
          (photo_rows[0]["storage_path"] if photo_rows else "", after["coupleId"]))
    couple_row = stub(page, "couples")[0]
    check("커플 행에 옮긴 이름·만난 날이 저장됨",
          couple_row["me"] == "박소영" and couple_row["you"] == "이준영" and couple_row["since"] == "2024-05-01", couple_row)

    av_rows = [r for r in stub(page, "settings") if str(r.get("key", "")).startswith("avatar:")]
    check("이전: 폰에 있던 프로필 사진도 내 몫(avatar:0)으로 올라감",
          len(av_rows) == 1 and av_rows[0]["key"] == "avatar:0" and
          str(av_rows[0].get("value", {}).get("src", "")).startswith("data:image/jpeg;base64"),
          [(r["key"], len(str(r.get("value", {}).get("src", "")))) for r in av_rows])
    pics_now = page.evaluate("(((window.TwoLogUI.state||{}).couple||{}).pics) || {}")
    check("이전 뒤 화면 상태에도 내 프로필 사진이 들어 있음",
          str((pics_now or {}).get("me", "")).startswith("data:image/"), list((pics_now or {}).keys()))

    keys = migrated_keys(page)
    check("이 기기 플래그 twolog.migrated.<coupleId> 저장", len(keys) == 1 and after["coupleId"] in keys[0], keys)
    flag = page.evaluate("(k) => JSON.parse(localStorage.getItem(k))", keys[0]) if keys else {}
    check("플래그에 옮긴 개수가 남음",
          flag.get("events") == 1 and flag.get("notes") == 1 and flag.get("photos") == 1, flag)

    same_local = local_state_raw(page) == before_raw
    still_idb = page.evaluate("""() => new Promise((resolve) => {
      const req = indexedDB.open('twolog', 1);
      req.onsuccess = () => {
        const db = req.result;
        const tx = db.transaction('photos', 'readonly');
        const all = tx.objectStore('photos').getAll();
        all.onsuccess = () => resolve({count: (all.result || []).length,
                                        size: (all.result || []).map(b => b.size).reduce((a, b) => a + b, 0)});
        all.onerror = () => resolve({count: -1});
      };
      req.onerror = () => resolve({count: -2});
    })""")
    check("폰의 원본 기록(localStorage)은 지우지 않고 그대로", same_local, same_local)
    check("폰의 사진 원본(IndexedDB)도 그대로", still_idb.get("count") == 1 and still_idb.get("size", 0) > 500, still_idb)

    # 화면에서도 보이는지 (캘린더 · 사진첩 · My)
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(500)
    check("캘린더에 옮겨 온 일정이 보임",
          page.locator("#s-cal .ev .t", has_text="폰에 있던 크리스마스").count() >= 1)
    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(800)
    pola = page.evaluate("""() => {
      const imgs = Array.from(document.querySelectorAll('#s-photo .pola-pic img')).map(i => i.getAttribute('src') || '');
      return {pola: document.querySelectorAll('#s-photo .pola').length, imgs: imgs};
    }""")
    check("사진첩에 옮겨 온 사진이 보임(원격 서명 주소)", pola["pola"] == 1 and pola["imgs"] and pola["imgs"][0].startswith("data:image/gif"), pola)
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(600)
    my = page.evaluate("document.querySelector('#s-set').innerText.replace(/\\s+/g,' ')")
    check("My 탭에 「폰에 있던 기록」 카드 · 「이어 옴」", "폰에 있던 기록" in my and "이어 옴" in my, my[:200])
    check("My 탭 카드에 옮긴 개수 표시", "일정 1개" in my and "사진 1장" in my, my[:200])
    check("My 탭에 「폰에 있던 예전 기록 가져오기」 버튼", "폰에 있던 예전 기록 가져오기" in my)
    page.screenshot(path=os.path.join(SHOT, "my-v26-migrated.png"))

    # --- 2-4. 새로 열어도, 다시 로그인해도 중복되지 않음
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2000)
    again = {"events": len(stub(page, "events")), "notes": len(stub(page, "notes")), "photos": len(stub(page, "photos"))}
    check("새로 열어도 중복 생성 없음", again["events"] == 1 and again["notes"] == 1 and again["photos"] == 1, again)

    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    page.locator('#s-set [data-act="logout"]').first.click()
    page.wait_for_timeout(450)
    page.locator("#sheetForm button[type=submit]").click()
    page.wait_for_selector("#s-login .login", timeout=10000)
    kept_after_logout = local_state_raw(page)
    check("로그아웃해도 폰의 예전 로컬 기록은 남아 있음", kept_after_logout == before_raw,
          "None" if kept_after_logout is None else "ok")

    page.fill('#s-login input[name="email"]', EMAIL)
    page.fill('#s-login input[name="password"]', "twolog1234")
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2000)
    relog = {"events": len(stub(page, "events")), "notes": len(stub(page, "notes")), "photos": len(stub(page, "photos")),
             "keys": len(migrated_keys(page))}
    check("다시 로그인해도 중복 생성 없음", relog["events"] == 1 and relog["notes"] == 1 and relog["photos"] == 1, relog)
    check("플래그도 하나만 유지", relog["keys"] == 1, relog["keys"])
    check("자동 이전 흐름에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 3. 원격에 이미 기록이 있으면 → 자동은 건너뛰고, 버튼으로 겹치지 않게 더하기
    # ==================================================================
    ctx = new_ctx(browser)
    seed = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;      // 새로 열 때 다시 심지 않음
      const CID = '11111111-1111-4111-8111-111111111111';
      const today = (() => { const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); })();
      localStorage.setItem('stub-sb-db', JSON.stringify({
        users: { 'user-me': { id: 'user-me', email: 'partner.side@twolog.app', password: 'twolog1234' } },
        couples: [{ id: CID, invite_code: '112233', members: ['user-me'], me: '준영', you: '소영',
                    since: '2025-03-14', phrase: '함께한 지', fmt: 'D',
                    colors: { me: '#BCE0F7', you: '#F7C6D4' }, sched: { me: '#BCE0F7', you: '#F7C6D4', both: '#D6C5F7' } }],
        events: [{ id: 'remote-e1', couple_id: CID, title: '상대가 넣은 일정', date: today, time: '',
                   type: 'date', memo: '', who: 'both' }],
        notes: [], photos: [], settings: [], uploads: [], seq: 0
      }));
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-me', email: 'partner.side@twolog.app' } }));
      localStorage.setItem('twolog:v1:state', JSON.stringify({
        couple: { me: '소영', you: '준영', since: '2023-01-20', fmt: 'D', phrase: '함께한 지',
                  colors: { me: '#9E636B', you: '#3D5C82' }, sched: { me: '#9E636B', you: '#3D5C82', both: '#625A7F' } },
        link: { code: '999999', connected: false, partnerCode: '' },
        auth: { out: false, email: '' },
        theme: { name: null, log: null, mode: 'light' },
        events: [
          { id: 'le1', date: today, endDate: today, time: '19:00', title: '폰 일정 A', type: 'date', memo: '', who: 'both' },
          { id: 'le2', date: today, endDate: today, time: '', title: '폰 일정 B', type: 'etc', memo: '', who: 'me' }
        ],
        todos: [{ id: 'lt1', text: '폰 할일', done: false, who: '나' }],
        bucket: [], logs: [], expenses: [], lists: [],
        photos: [
          { id: 'lp1', date: today, album: '폰 앨범', title: '폰 사진', place: '', memo: '',
            art: 0, capBg: null, src: 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7' },
          { id: 'lp2', date: today, album: '폰 앨범', title: '원본이 없는 사진', place: '', memo: '',
            art: 0, capBg: null, path: 'idb:nothing-here' }
        ],
        ui: { seg: 'todo', expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today }
      }));
    })();"""
    ctx.add_init_script(seed)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(1500)

    auto = page.evaluate("""(() => {
      const S = window.TwoLogUI.state || {};
      return {titles: (S.events || []).map(e => e.title), me: (S.couple || {}).me,
              since: (S.couple || {}).since,
              toast: (document.getElementById('toast') || {}).textContent || ''};
    })()""")
    check("원격에 기록이 있으면 자동 이전은 하지 않음",
          auto["titles"] == ["상대가 넣은 일정"], auto["titles"])
    check("원격 커플 정보는 그대로 (자동 이전이 덮어쓰지 않음)",
          auto["me"] == "준영" and auto["since"] == "2025-03-14", {k: auto[k] for k in ("me", "since")})
    check("자동 이전을 하지 않았을 때는 플래그도 없음", len(migrated_keys(page)) == 0, migrated_keys(page))

    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(600)
    my = page.evaluate("document.querySelector('#s-set').innerText.replace(/\\s+/g,' ')")
    check("My 탭에 가져오기 카드 · 「대기」 표시", "폰에 있던 기록" in my and "대기" in my, my[:200])
    check("가져올 개수 안내(일정 2개 · 노트 1개 · 사진 2장)",
          "일정 2개" in my and "노트 1개" in my and "사진 2장" in my, my[:200])
    page.screenshot(path=os.path.join(SHOT, "my-v26-pending.png"))

    page.locator('#s-set [data-act="importLocal"]').first.click()
    page.wait_for_timeout(500)
    sheet = page.evaluate("document.querySelector('#sheet').innerText.replace(/\\s+/g,' ')")
    check("가져오기 확인 시트", "폰에 있던 기록 가져오기" in sheet and "가져오기" in sheet, sheet[:160])
    page.screenshot(path=os.path.join(SHOT, "import-v26-sheet.png"))
    page.locator("#importForm button[type=submit]").click()
    page.wait_for_timeout(3000)

    merged = {"events": len(stub(page, "events")), "notes": len(stub(page, "notes")),
              "photos": len(stub(page, "photos")), "uploads": len(stub(page, "uploads"))}
    check("가져오기: 일정 2개가 더해져 3개", merged["events"] == 3, merged)
    check("가져오기: 노트 1개 추가", merged["notes"] == 1, merged)
    check("가져오기: 사진 2장 행 + data URL 사진은 Storage 업로드", merged["photos"] == 2 and merged["uploads"] == 1, merged)
    photos_now = stub(page, "photos")
    with_file = [r for r in photos_now if r.get("storage_path")]
    without = [r for r in photos_now if not r.get("storage_path")]
    check("원본이 없는 사진도 날짜·제목은 남김",
          len(with_file) == 1 and len(without) == 1 and without[0]["title"] == "원본이 없는 사진", photos_now)
    couple_now = stub(page, "couples")[0]
    check("상대가 정한 커플 정보는 그대로 유지",
          couple_now["me"] == "준영" and couple_now["since"] == "2025-03-14", couple_now)
    state_now = page.evaluate("""(() => {
      const S = window.TwoLogUI.state || {};
      return {titles: (S.events || []).sort((a, b) => (a.title < b.title ? -1 : 1)).map(e => e.title),
              texts: (S.todos || []).map(t => t.text),
              photos: (S.photos || []).length,
              toast: (document.getElementById('toast') || {}).textContent || ''};
    })()""")
    check("가져온 기록이 화면 상태에도 반영", "폰 일정 A" in state_now["titles"] and "폰 할일" in state_now["texts"], state_now)
    check("가져오기 안내 토스트", "이어 왔어요" in state_now["toast"], state_now["toast"])
    check("가져온 뒤 플래그 저장", len(migrated_keys(page)) == 1, migrated_keys(page))
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(500)
    check("캘린더에 가져온 일정 A·B 와 상대 일정이 함께 보임",
          page.locator("#s-cal .ev .t", has_text="폰 일정 A").count() >= 1 and
          page.locator("#s-cal .ev .t", has_text="상대가 넣은 일정").count() >= 1)
    page.screenshot(path=os.path.join(SHOT, "cal-v26-imported.png"))

    # 한 번 더 눌러도 겹치지 않음
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    page.locator('#s-set [data-act="importLocal"]').first.click()
    page.wait_for_timeout(400)
    page.locator("#importForm button[type=submit]").click()
    page.wait_for_timeout(2500)
    twice = {"events": len(stub(page, "events")), "notes": len(stub(page, "notes")),
             "photos": len(stub(page, "photos")), "uploads": len(stub(page, "uploads"))}
    check("같은 버튼을 다시 눌러도 겹치지 않음", twice == merged, twice)

    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(1500)
    reload_counts = {"events": len(stub(page, "events")), "notes": len(stub(page, "notes")),
                     "photos": len(stub(page, "photos"))}
    check("새로 열어도 그대로 (자동 이전이 다시 돌지 않음)",
          reload_counts["events"] == 3 and reload_counts["notes"] == 1 and reload_counts["photos"] == 2, reload_counts)
    check("가져오기 흐름에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 4. 새 기기(로컬 기록 없음) — 아무 일도 일어나지 않음
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "fresh.device@twolog.app", "twolog1234")
    page.wait_for_timeout(1500)
    fresh = page.evaluate("""(() => {
      const S = window.TwoLogUI.state || {};
      return {events: (S.events || []).length, photos: (S.photos || []).length,
              toast: (document.getElementById('toast') || {}).textContent || ''};
    })()""")
    check("새 기기: 빈 기록으로 시작", fresh["events"] == 0 and fresh["photos"] == 0, fresh)
    check("새 기기: 이전 토스트 없음", "이어 왔어요" not in fresh["toast"], fresh["toast"])
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    my_fresh = page.evaluate("document.querySelector('#s-set').innerText.replace(/\\s+/g,' ')")
    check("새 기기: 「폰에 있던 기록」 카드가 없음", "폰에 있던 기록" not in my_fresh, my_fresh[:160])
    check("새 기기: 플래그도 만들지 않음", len(migrated_keys(page)) == 0, migrated_keys(page))
    check("새 기기: 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 5. 예전 프로토타입 키(couple-app-v1)만 있는 기기
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("""(() => {
      const today = (() => { const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); })();
      localStorage.setItem('couple-app-v1', JSON.stringify({
        couple: { me: '소영', you: '준영', since: '2022-11-11', fmt: 'D', phrase: '함께한 지',
                  colors: { me: '#9E636B', you: '#3D5C82' }, sched: { me: '#9E636B', you: '#3D5C82', both: '#625A7F' } },
        auth: { out: false },
        events: [{ id: 'old1', date: today, endDate: today, time: '', title: '옛 프로토타입 일정', type: 'date', memo: '', who: 'both' }],
        todos: [], bucket: [], logs: [], expenses: [], photos: [], lists: [],
        ui: { seg: 'todo', expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today }
      }));
    })();""")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "legacy.key@twolog.app", "twolog1234")
    page.wait_for_timeout(2000)
    legacy = page.evaluate("(() => ((window.TwoLogUI.state || {}).events || []).map(e => e.title))()")
    check("예전 프로토타입 키도 이어 옴", legacy == ["옛 프로토타입 일정"], legacy)
    check("옛 키를 읽어도 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 6. 프로필 사진 — 각자 자기 사진만 바꾸고, 두 폰에 함께 보임
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "avatar.a@twolog.app", "twolog1234")
    page.wait_for_timeout(1200)

    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    before_pic = page.evaluate("""() => ({
      pickYou: document.querySelectorAll('#s-set [data-act="pickPic"][data-who="you"]').length,
      pickMe: document.querySelectorAll('#s-set [data-act="pickPic"][data-who="me"]').length,
      members: window.TwoLogStore.couple.memberCount(), slot: window.TwoLogStore.couple.mySlot()
    })""")
    check("연결 전(혼자)에는 두 사람 사진을 모두 설정할 수 있음",
          before_pic["pickYou"] >= 1 and before_pic["pickMe"] >= 1 and before_pic["members"] == 1, before_pic)

    page.set_input_files("#avatarInput", JPG)
    page.wait_for_timeout(900)
    page.locator("#avcApply").click()          # v27: 동그라미 가이드에서 잘라 적용
    page.wait_for_timeout(1500)
    pic_a = page.evaluate("""() => {
      const st = window.__stub;
      const rows = (st.settings || []).filter(r => String(r.key).indexOf('avatar:') === 0);
      const img = document.querySelector('#s-set [data-who="me"] .av-img');
      return {rows: rows.map(r => ({key: r.key, len: (r.value && r.value.src || '').length,
                                    head: (r.value && r.value.src || '').slice(0, 22)})),
              mine: ((window.TwoLogUI.state || {}).couple.pics || {}).me ? 'yes' : 'no',
              shown: img ? img.getAttribute('src').slice(0, 22) : ''};
    }""")
    check("내 사진을 바꾸면 서버(settings)에 내 몫(avatar:0)으로 올라감",
          len(pic_a["rows"]) == 1 and pic_a["rows"][0]["key"] == "avatar:0" and pic_a["rows"][0]["len"] > 500
          and pic_a["rows"][0]["head"] == "data:image/jpeg;base64", pic_a)
    check("내 아바타가 화면에 보임", pic_a["mine"] == "yes" and pic_a["shown"].startswith("data:image/"), pic_a)
    page.screenshot(path=os.path.join(SHOT, "avatar-v26-a.png"))
    a_avatar = page.evaluate("(window.__stub.settings||[]).filter(r=>r.key==='avatar:0')[0].value.src")
    a_db = page.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")

    # --- 상대 기기(준영) 만들기: 같은 서버 상태 + 두 번째 구성원
    a_user = a_db["couples"][0]["members"][0]
    a_db["users"]["user-b"] = {"id": "user-b", "email": "avatar.b@twolog.app", "password": "twolog1234"}
    a_db["couples"][0]["members"] = [a_user, "user-b"]
    seed_b = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-b', email: 'avatar.b@twolog.app' } }));
    })();""" % json.dumps(json.dumps(a_db, ensure_ascii=False))

    ctx_b = new_ctx(browser)
    ctx_b.add_init_script(seed_b)
    page_b = ctx_b.new_page()
    errs_b = []
    page_b.on("pageerror", lambda e: errs_b.append("pageerror: " + str(e)))
    page_b.on("console", lambda m: errs_b.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page_b)
    page_b.goto(URL, wait_until="domcontentloaded")
    page_b.wait_for_selector("#tabbar .tab", timeout=25000)
    page_b.wait_for_timeout(1800)

    on_b = page_b.evaluate("""() => {
      const home = document.querySelector('#s-home .av.you img');
      const mine = document.querySelector('#s-home .av.me img');
      return {member: window.TwoLogStore.couple.mySlot(),
              youSrc: home ? home.getAttribute('src') : '',
              meSrc: mine ? mine.getAttribute('src') : '',
              names: [(window.TwoLogUI.state.couple.me), (window.TwoLogUI.state.couple.you)]};
    }""")
    check("상대 기기(준영)는 내가 정한 사진을 자기 '상대' 자리에서 봄",
          on_b["youSrc"] == a_avatar and on_b["meSrc"] == "", (on_b["youSrc"][:24], on_b["meSrc"][:24]))
    check("상대 기기는 members[1] 로 인식(자기 자리가 뒤집힘)", on_b["member"] == 1, on_b)

    page_b.locator("#tabbar .tab").nth(4).click()
    page_b.wait_for_timeout(600)
    perm_b = page_b.evaluate("""() => ({
      pickYou: document.querySelectorAll('#s-set [data-act="pickPic"][data-who="you"]').length,
      pickMe: document.querySelectorAll('#s-set [data-act="pickPic"][data-who="me"]').length,
      hint: (document.querySelector('#s-set .row[data-who="you"]') || {}).innerText || ''
    })""")
    check("상대 기기 My 탭: 내 사진만 고를 수 있고 상대(소영) 사진에는 버튼이 없음",
          perm_b["pickMe"] >= 1 and perm_b["pickYou"] == 0, perm_b)
    check("상대 사진 줄에 「상대 폰에서 바꿔요」 안내", "폰에서 바꿔요" in perm_b["hint"], perm_b["hint"])

    page_b.locator('#s-set [data-act="personSheet"][data-who="you"]').click()
    page_b.wait_for_timeout(500)
    sheet_b = page_b.evaluate("""() => ({
      text: document.querySelector('#sheet').innerText.replace(/\\s+/g,' '),
      pick: document.querySelectorAll('#sheet [data-act="pickPic"]').length
    })""")
    check("상대 프로필 시트에는 사진 선택 버튼 대신 안내", "본인 폰에서 바꿀 수 있어요" in sheet_b["text"] and sheet_b["pick"] == 0, sheet_b)
    page_b.keyboard.press("Escape")
    page_b.wait_for_timeout(300)

    guard = page_b.evaluate("""() => {
      const b = document.createElement('button');
      b.setAttribute('data-act', 'pickPic'); b.setAttribute('data-who', 'you');
      document.body.appendChild(b); b.click(); b.remove();
      return (document.getElementById('toast') || {}).textContent || '';
    }""")
    check("상대 사진 선택을 억지로 눌러도 막힘", "폰에서 바꿀 수 있어요" in guard, guard)

    # 준영이 자기 사진을 바꾸기
    page_b.locator("#tabbar .tab").nth(4).click()
    page_b.wait_for_timeout(400)
    page_b.set_input_files("#avatarInput", JPG)
    page_b.wait_for_timeout(900)
    page_b.locator("#avcApply").click()        # v27: 동그라미 가이드에서 잘라 적용
    page_b.wait_for_timeout(1500)
    b_rows = page_b.evaluate("""() => (window.__stub.settings||[]).filter(r=>String(r.key).indexOf('avatar:')===0)
      .map(r => ({key: r.key, src: (r.value && r.value.src) || ''}))""")
    keys = [r["key"] for r in b_rows]
    b_avatar = [r["src"] for r in b_rows if r["key"] == "avatar:1"]
    a_still = [r["src"] for r in b_rows if r["key"] == "avatar:0"]
    check("상대 기기에서 바꾼 사진은 자기 몫(avatar:1)으로 저장", "avatar:1" in keys and b_avatar and b_avatar[0].startswith("data:image/"), keys)
    check("내가 정한 사진(avatar:0)은 덮어쓰지 않음", a_still and a_still[0] == a_avatar, [len(x) for x in a_still])
    b_db = page_b.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")

    # --- 다시 소영 기기: 새로 열면 준영 사진도 보임
    page.evaluate("(db) => { localStorage.setItem('stub-sb-db', db); }", json.dumps(b_db, ensure_ascii=False))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(1800)
    on_a = page.evaluate("""() => {
      const me = document.querySelector('#s-home .av.me img');
      const you = document.querySelector('#s-home .av.you img');
      return {meSrc: me ? me.getAttribute('src') : '', youSrc: you ? you.getAttribute('src') : ''};
    }""")
    check("소영 기기: 내 사진과 준영 사진이 각자 자리에 보임",
          on_a["meSrc"] == a_avatar and on_a["youSrc"] == b_avatar[0] if b_avatar else False,
          (on_a["meSrc"][:24], on_a["youSrc"][:24]))
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    perm_a = page.evaluate("""() => ({
      pickYou: document.querySelectorAll('#s-set [data-act="pickPic"][data-who="you"]').length,
      pickMe: document.querySelectorAll('#s-set [data-act="pickPic"][data-who="me"]').length,
      hint: (document.querySelector('#s-set .row[data-who="you"]') || {}).innerText || ''
    })""")
    check("소영 기기도 상대(준영) 사진은 바꿀 수 없음", perm_a["pickMe"] >= 1 and perm_a["pickYou"] == 0, perm_a)
    check("연결된 뒤 상대 줄 안내 문구", "폰에서 바꿔요" in perm_a["hint"], perm_a["hint"])
    page.screenshot(path=os.path.join(SHOT, "avatar-v26-synced.png"))

    # --- 진짜 Realtime 경로: 상대가 바꾼 것을 구독으로 받아 다시 그리는지
    cid_a = page.evaluate("(window.TwoLogStore||{}).coupleId")
    newer = a_avatar[:-8] + "AAAAAAA=" if a_avatar.endswith("=") else a_avatar
    page.evaluate("""(args) => {
      const st = window.__stub;
      const row = (st.settings || []).filter(r => r.key === 'avatar:1')[0];
      row.value = { src: args.src, at: Date.now() };
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      return window.__stubEmit('settings', args.cid);
    }""", {"src": a_avatar, "cid": cid_a})
    page.wait_for_timeout(2200)
    rt = page.evaluate("""() => {
      const you = document.querySelector('#s-home .av.you img');
      return {src: you ? you.getAttribute('src') : '',
              state: (((window.TwoLogUI.state || {}).couple.pics) || {}).you ? 'yes' : 'no'};
    }""")
    check("Realtime: 상대가 바꾸면 새로 열지 않아도 바로 반영", rt["src"] == a_avatar and rt["state"] == "yes", (rt["src"][:24], rt["state"]))
    check("프로필 사진 흐름에서 콘솔/스크립트 오류 없음(소영 기기)", len(errs) == 0, errs[:3])
    check("프로필 사진 흐름에서 콘솔/스크립트 오류 없음(준영 기기)", len(errs_b) == 0, errs_b[:3])
    ctx_b.close()
    ctx.close()

    # ==================================================================
    # 7. local 모드 — 예전 그대로 (이전 카드 없음, migrate 는 local_mode)
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(700)
    loc = page.evaluate("""async () => {
      const st = window.TwoLogStore;
      const res = await st.migrate.run({});
      return {mode: st.mode, reason: res && res.reason, tabs: document.querySelectorAll('#tabbar .tab').length,
              summary: st.local.summary(), done: st.migrate.done()};
    }""")
    check("local 모드: migrate 는 local_mode 로만 답함", loc["mode"] == "local" and loc["reason"] == "local_mode", loc)
    check("local 모드: 플래그 없음 · 요약은 읽을 수 있음",
          loc["done"] is None and isinstance(loc["summary"], dict), (loc["done"], loc["summary"]))
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    my_loc = page.evaluate("document.querySelector('#s-set').innerText.replace(/\\s+/g,' ')")
    check("local 모드: My 탭에 이전 카드가 없고 「로컬」 표시", "폰에 있던 기록" not in my_loc and "로컬" in my_loc, my_loc[:160])
    check("local 모드: 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
