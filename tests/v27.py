"""투로그 v27 확인 — 노트 카드 묶음(groups·gid) 동기화 · v26 기기 자동 복구 · 달력 글씨.

1) 버전: sw.js 캐시 twolog-v28 · APP_VERSION v28 · sync.js 에 repairGroups
2) 달력 아래 선택한 날 일정 글씨가 커짐(제목 16px · 이름 12.5px → v28 13.5px)
3) v26 으로 이미 한 번 이전을 마친 폰 재현
   (원격 notes 38개에 gid·memo 없음 + settings 에 groups 없음 + twolog.migrated.<cid> 있음,
    폰 localStorage 에는 groups(메모 2·버킷 3)와 항목별 gid·상세 메모가 그대로)
   → v27 로 열면 자동 복구: 메모 2개·버킷 3개 카드, 카드 색(titleBg), 항목 분배, 상세 메모,
     settings groups 행(모든 필드) · notes payload gid, 플래그 twolog.groupsRepaired.<cid>
   → 새로 열어도 다시 돌지 않고 중복 없음
4) 상대 폰에서도 같은 카드·같은 분배로 보임
5) 새 기기에서 폰 기록을 이어 올 때 groups·gid·lists·logs 가 처음부터 함께 올라감
6) remote 모드에서 카드 안에 항목을 추가·수정하면 바로 저장·표시되고,
   Realtime 다시 읽기 뒤에도 그 카드 자리에 남아 있음
7) local 모드(?sync=local)는 예전 그대로 (repair 는 local_mode)

    python3 tests/v27.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
"""
import base64, functools, http.server, json, os, re, socketserver, sys, tempfile, threading, time

from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SHOT = os.path.abspath(os.path.join(ROOT, "..", "downloads", "twolog-screens"))
os.makedirs(SHOT, exist_ok=True)

STUB = open(os.path.join(HERE, "stub-supabase.js")).read()
ESM = re.compile(r"https://esm\.sh/.*")

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

JPG = os.path.join(tempfile.mkdtemp(), "v27-photo.jpg")
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


def signup(page, email, pw):
    page.locator('#s-login [data-act="loginSwitch"]').click()
    page.wait_for_timeout(250)
    page.fill('#s-login input[name="email"]', email)
    page.fill('#s-login input[name="password"]', pw)
    page.locator("#s-login .btn-primary").click()
    page.wait_for_selector("#tabbar .tab", timeout=25000)


def go_note(page):
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(500)


def note_view(page):
    return page.evaluate("""() => {
      const cards = Array.from(document.querySelectorAll('#s-diary .ncard[data-gid]'));
      return {
        cards: cards.map(c => ({
          gid: c.getAttribute('data-gid'),
          title: (c.querySelector('.nc-t') || {}).textContent || '',
          hd: (c.querySelector('.nc-hd') || {}).style ? c.querySelector('.nc-hd').style.backgroundColor : '',
          items: Array.from(c.querySelectorAll('.nc-items .cti .cx')).map(x => x.textContent)
        })),
        newCard: document.querySelectorAll('#s-diary .ncard.new').length,
        seg: (window.TwoLogUI.state.ui || {}).seg
      };
    }""")


def state_summary(page):
    return page.evaluate("""() => {
      const S = window.TwoLogUI.state || {};
      const g = S.groups || {};
      const c = window.TwoLogStore || {};
      return {
        gTodo: (g.todo || []).map(x => x.id), gBucket: (g.bucket || []).map(x => x.id),
        gLog: (g.log || []).map(x => x.id),
        gTitles: (g.todo || []).map(x => x.title),
        todos: (S.todos || []).length, bucket: (S.bucket || []).length, logs: (S.logs || []).length,
        todoGidMissing: (S.todos || []).filter(t => !t.gid).length,
        bucketGidMissing: (S.bucket || []).filter(t => !t.gid).length,
        logGidMissing: (S.logs || []).filter(t => !t.gid).length,
        todoByGid: (S.todos || []).reduce((a, t) => { a[t.gid || 'none'] = (a[t.gid || 'none'] || 0) + 1; return a; }, {}),
        bucketByGid: (S.bucket || []).reduce((a, t) => { a[t.gid || 'none'] = (a[t.gid || 'none'] || 0) + 1; return a; }, {}),
        memoKept: (S.todos || []).filter(t => t.memo).length,
        memoBucket: (S.bucket || []).filter(t => t.memo).length,
        lists: (S.lists || []).length,
        listItems: (S.lists || []).map(l => (l.items || []).map(i => i.text + '|' + (i.memo || ''))),
        toast: ((document.getElementById('toast') || {}).textContent || ''),
        coupleId: c.coupleId || null
      };
    }""")


with sync_playwright() as p:
    browser = launch(p)

    # ==================================================================
    # 1. 버전 · 문구
    # ==================================================================
    ctx = new_ctx(browser)
    page = ctx.new_page()
    sw = page.request.get(URL + "sw.js").text()
    app_js = page.request.get(URL + "app.js").text()
    sync_js = page.request.get(URL + "sync.js").text()
    check("sw.js 캐시 버전 twolog-v28", 'const VERSION = "twolog-v28"' in sw,
          [l for l in sw.splitlines() if "VERSION" in l][:1])
    check("app.js 버전 상수 v28", 'var APP_VERSION = "v28"' in app_js)
    check("sync.js 에 gid·groups 동기화가 있음",
          "notePayload" in sync_js and 'K_GROUPS = "groups"' in sync_js and "repairGroups" in sync_js)
    ctx.close()

    # ==================================================================
    # 2. 달력 아래 선택한 날 일정 글씨 (v27: 더 크게)
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(700)
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(500)
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(400)
    page.fill('#sheetForm input[name="title"]', "글씨 크기 확인 일정")
    page.locator("#evSave").click()
    page.wait_for_timeout(700)
    # 이름(누구)이 붙도록 담당자를 나로 바꿔 저장합니다 — whoRow 가 .wname 을 그립니다
    page.evaluate("""() => {
      const S = window.TwoLogUI.state;
      const e = (S.events || []).filter(x => x.title === '글씨 크기 확인 일정')[0];
      if (e) e.who = 'me';
      return window.TwoLogStore.flush();
    }""")
    page.wait_for_timeout(400)
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(600)
    fs = page.evaluate("""() => {
      const t = document.querySelector('#s-cal .daylist .ev .t');
      const w = document.querySelector('#s-cal .daylist .ev .wname');
      const d = document.querySelector('#s-cal .daypanel-hd .d');
      return {t: t ? getComputedStyle(t).fontSize : null,
              w: w ? getComputedStyle(w).fontSize : null,
              who: w ? w.textContent.trim() : '',
              d: d ? getComputedStyle(d).fontSize : null,
              txt: t ? t.textContent.trim() : ''};
    }""")
    check("달력 아래 일정 제목 글씨가 16px (v26 14px 보다 큼)", fs["t"] == "16px", fs)
    # v28: 이름 글씨를 1px 더 크게 (12.5 → 13.5px)
    check("일정 줄 이름 글씨 13.5px", fs["w"] == "13.5px", fs)
    check("일정 제목이 그대로 보임", fs["txt"] == "글씨 크기 확인 일정", fs)
    # ---- 달력 격자 칸 안의 일정 막대: 빈틈 없이 쌓기 · 글씨 1px 작게
    page.evaluate("""() => {
      const S = window.TwoLogUI.state;
      const t = S.ui.selDate;
      ['일정 둘', '일정 셋'].forEach((n, i) => S.events.push({ id: 'v27e' + i, date: t, endDate: t,
        time: '', title: n, type: 'etc', memo: '', who: 'me', color: '' }));
      window.__app.rerender();
      return window.TwoLogStore.flush();
    }""")
    page.wait_for_timeout(600)
    bars = page.evaluate("""() => {
      const bs = Array.from(document.querySelectorAll('#s-cal .ebar'));
      const cs = bs.length ? getComputedStyle(bs[0]) : null;
      const rs = bs.map(b => { const r = b.getBoundingClientRect();
        return {t: b.textContent.trim(), y: r.top, b: r.bottom, h: r.height, x: r.left}; });
      const byCol = {};
      rs.forEach(r => { const k = Math.round(r.x / 7); (byCol[k] = byCol[k] || []).push(r); });
      const col = Object.keys(byCol).map(k => byCol[k].sort((a, b) => a.y - b.y))
        .sort((a, b) => b.length - a.length)[0] || [];
      return {n: bs.length, fs: cs ? cs.fontSize : null, h: cs ? cs.height : null,
              gaps: col.slice(1).map((b, i) => Math.round((b.y - col[i].b) * 10) / 10),
              pitch: col.slice(1).map((b, i) => Math.round((b.y - col[i].y) * 10) / 10)};
    }""")
    check("달력 칸 일정 막대 글씨가 10px (v27: 1px 작게)", bars["fs"] == "10px", bars)
    check("달력 칸 막대 높이는 16px 그대로", bars["h"] == "16px", bars)
    check("한 칸에 쌓인 막대 사이가 빈틈 없이 붙어 있음",
          len(bars["gaps"]) >= 1 and max(abs(g) for g in bars["gaps"]) <= 0.6 and
          all(abs(p - 16) <= 0.6 for p in bars["pitch"]), bars)
    page.screenshot(path=os.path.join(SHOT, "cal-v27-daypanel.png"))
    check("달력 글씨 확인 중 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 3. v26 으로 이미 이전을 마친 폰 → 자동 복구
    # ==================================================================
    seed = r"""(() => {
      if (localStorage.getItem('stub-sb-db')) return;      // 새로 열 때 다시 심지 않음
      const today = (() => { const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); })();
      const CID = '22222222-2222-4222-8222-222222222222';
      const groups = {
        todo: [
          { id: 'g-t1', title: '메모 카드 하나', caption: '', who: 'me', date: today, titleBg: '#F2CFC9' },
          { id: 'g-t2', title: '메모 카드 둘', caption: '', who: 'me', date: today, titleBg: '#B8CAA5' }
        ],
        bucket: [
          { id: 'g-b1', title: '버킷 하나', caption: '여름에 갈 곳', who: 'you', date: today, titleBg: '#EA994D' },
          { id: 'g-b2', title: '버킷 둘', caption: '', who: 'me', date: today, titleBg: '' },
          { id: 'g-b3', title: '버킷 셋', caption: '', who: 'me', date: today, titleBg: '#80A4AA' }
        ],
        log: [{ id: 'g-l1', title: '영화·먹방', caption: '', who: 'me', date: today }]
      };
      const todos = [];
      for (let i = 1; i <= 16; i++) todos.push({ id: 'lt' + i, text: '메모 항목 ' + i,
        memo: (i % 3 === 0 ? '상세 메모 ' + i : ''), done: (i % 4 === 0), who: '나',
        gid: (i <= 8 ? 'g-t1' : 'g-t2') });
      const bucket = [];
      for (let i = 1; i <= 18; i++) bucket.push({ id: 'lb' + i, title: '버킷 항목 ' + i, cat: '여행',
        memo: (i % 5 === 0 ? '버킷 메모 ' + i : ''), done: (i % 6 === 0),
        gid: (i <= 6 ? 'g-b1' : (i <= 12 ? 'g-b2' : 'g-b3')) });
      const logs = [];
      for (let i = 1; i <= 4; i++) logs.push({ id: 'lg' + i, kind: (i % 2 ? 'movie' : 'food'),
        title: '영화·먹방 ' + i, rating: 4, date: today, review: '한 줄 평 ' + i, place: '', done: true, gid: 'g-l1' });
      /* 커스텀 리스트도 폰에만 상세 메모가 남아 있는 상태 (v26 은 항목 memo 를 올리지 않았어요) */
      const lists = [{ id: 'ls1', title: '여행 준비물', emoji: '🧳', kind: 'check', items: [
        { id: 'li1', text: '여권', memo: '유효기간 확인', done: false },
        { id: 'li2', text: '충전기', memo: '', done: false } ] }];

      localStorage.setItem('twolog:v1:state', JSON.stringify({
        couple: { me: '박소영', you: '이준영', since: '2024-05-01', fmt: 'D', phrase: '함께한 지',
                  colors: { me: '#9E636B', you: '#3D5C82' }, sched: { me: '#9E636B', you: '#3D5C82', both: '#625A7F' } },
        link: { code: '224466', connected: true, partnerCode: '' },
        auth: { out: false, email: '' },
        theme: { name: null, log: null, mode: 'light' },
        groups: groups, todos: todos, bucket: bucket, logs: logs,
        lists: lists, expenses: [], photos: [],
        ui: { seg: 'todo', expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today }
      }));

      /* v26 이 올렸던 모습 그대로 — payload 에 gid·memo·done 이 없습니다 */
      const notes = [];
      let s = 0;
      todos.forEach(t => notes.push({ id: t.id, couple_id: CID, kind: 'todo', sort: s++, deleted: false,
        payload: { text: t.text, done: !!t.done, who: 'me' } }));
      bucket.forEach(b => notes.push({ id: b.id, couple_id: CID, kind: 'bucket', sort: s++, deleted: false,
        payload: { title: b.title, cat: b.cat, done: !!b.done, status: '' } }));
      logs.forEach(l => notes.push({ id: l.id, couple_id: CID, kind: 'log', sort: s++, deleted: false,
        payload: { kind: l.kind, title: l.title, rating: l.rating, date: l.date, review: l.review, place: '' } }));
      lists.forEach(l => notes.push({ id: l.id, couple_id: CID, kind: 'list', sort: s++, deleted: false,
        payload: { title: l.title, emoji: l.emoji, kind: l.kind,
                   items: l.items.map(i => ({ id: i.id, text: i.text, done: !!i.done })) } }));

      localStorage.setItem('stub-sb-db', JSON.stringify({
        users: { 'user-me': { id: 'user-me', email: 'repair@twolog.app', password: 'twolog1234' } },
        couples: [{ id: CID, invite_code: '224466', members: ['user-me'], me: '박소영', you: '이준영',
                    since: '2024-05-01', phrase: '함께한 지', fmt: 'D',
                    colors: { me: '#9E636B', you: '#3D5C82' }, sched: { me: '#9E636B', you: '#3D5C82', both: '#625A7F' } }],
        events: [], notes: notes, photos: [], settings: [], uploads: [], seq: 0
      }));
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-me', email: 'repair@twolog.app' } }));
      localStorage.setItem('twolog.migrated.' + CID, JSON.stringify({ at: Date.now(), events: 0, notes: 38, photos: 0, meta: true }));
    })();"""
    ctx = new_ctx(browser)
    ctx.add_init_script(seed)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(3500)

    before = state_summary(page)
    check("v26 으로 이미 이전을 마친 기기(시나리오) — twolog.migrated 플래그가 있음",
          len(page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('twolog.migrated.') === 0)")) == 1,
          page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('twolog.migrated.') === 0)"))

    after = state_summary(page)
    check("자동 복구: 메모 카드 2개 · 버킷 3개 · 영화·먹방 1개",
          len(after["gTodo"]) == 2 and len(after["gBucket"]) == 3 and len(after["gLog"]) == 1,
          (after["gTodo"], after["gBucket"], after["gLog"]))
    check("복구: 항목 38개가 모두 살아 있음",
          after["todos"] == 16 and after["bucket"] == 18 and after["logs"] == 4,
          (after["todos"], after["bucket"], after["logs"]))
    check("복구: 모든 항목이 카드(gid)를 가짐",
          after["todoGidMissing"] == 0 and after["bucketGidMissing"] == 0 and after["logGidMissing"] == 0,
          (after["todoGidMissing"], after["bucketGidMissing"], after["logGidMissing"]))
    check("복구: 항목이 원래 카드로 나뉨 (8/8 · 6/6/6)",
          after["todoByGid"].get("g-t1") == 8 and after["todoByGid"].get("g-t2") == 8 and
          after["bucketByGid"].get("g-b1") == 6 and after["bucketByGid"].get("g-b2") == 6 and
          after["bucketByGid"].get("g-b3") == 6, (after["todoByGid"], after["bucketByGid"]))
    check("복구: 상세 메모(메모내용)도 되살아남",
          after["memoKept"] == 5 and after["memoBucket"] == 3, (after["memoKept"], after["memoBucket"]))
    check("복구 안내 토스트", "노트 카드를 되살렸어요" in after["toast"], after["toast"])

    keys = page.evaluate("Object.keys(localStorage).filter(k => k.indexOf('twolog.groupsRepaired.') === 0)")
    check("이 기기 플래그 twolog.groupsRepaired.<coupleId>", len(keys) == 1 and after["coupleId"] in keys[0], keys)
    flag = page.evaluate("(k) => JSON.parse(localStorage.getItem(k))", keys[0]) if keys else {}
    check("플래그에 카드 개수·고친 항목 수",
          (flag.get("groups") or {}).get("todo") == 2 and (flag.get("groups") or {}).get("bucket") == 3 and
          flag.get("fixed") == 39 and flag.get("added") == 0, flag)

    g_rows = [r for r in stub(page, "settings") if r.get("key") == "groups"]
    check("settings 에 groups 행 하나", len(g_rows) == 1, [r.get("key") for r in stub(page, "settings")])
    gv = (g_rows[0]["value"] if g_rows else {})
    check("groups 행: 메모 2 · 버킷 3 · 영화·먹방 1",
          len(gv.get("todo") or []) == 2 and len(gv.get("bucket") or []) == 3 and len(gv.get("log") or []) == 1,
          {k: len(gv.get(k) or []) for k in ("todo", "bucket", "log")})
    g1 = (gv.get("todo") or [{}])[0]
    check("groups 행: 카드의 모든 필드(id·title·titleBg·caption·who·date) 보존",
          g1.get("id") == "g-t1" and g1.get("title") == "메모 카드 하나" and g1.get("titleBg") == "#F2CFC9" and
          g1.get("caption") == "" and g1.get("who") == "me" and bool(g1.get("date")), g1)
    gb1 = (gv.get("bucket") or [{}])[0]
    check("groups 행: 버킷 카드 caption·who·titleBg 도 보존",
          gb1.get("caption") == "여름에 갈 곳" and gb1.get("who") == "you" and gb1.get("titleBg") == "#EA994D", gb1)

    rows_now = stub(page, "notes")
    note_kinds = [r for r in rows_now if r["kind"] in ("todo", "bucket", "log")]
    bad_gid = [r["id"] for r in note_kinds if not (r.get("payload") or {}).get("gid")]
    check("원격 notes 38개 모두 payload.gid 를 가짐", len(note_kinds) == 38 and not bad_gid, bad_gid[:5])
    lt3 = [r for r in rows_now if r["id"] == "lt3"]
    check("원격 notes 에 상세 메모도 채워짐", lt3 and lt3[0]["payload"].get("memo") == "상세 메모 3",
          (lt3[0]["payload"] if lt3 else None))
    lg1 = [r for r in rows_now if r["id"] == "lg1"]
    check("원격 notes(영화·먹방)에 done 도 채워짐", lg1 and lg1[0]["payload"].get("done") is True,
          (lg1[0]["payload"] if lg1 else None))

    ls1 = [r for r in rows_now if r["kind"] == "list"]
    ls_memo = (ls1[0]["payload"]["items"][0].get("memo") if ls1 else None)
    check("복구: 커스텀 리스트 항목의 상세 메모도 서버에 채워짐", ls1 and ls_memo == "유효기간 확인",
          (ls1[0]["payload"] if ls1 else None))
    ls_state = page.evaluate("""() => {
      const L = (window.TwoLogUI.state.lists || [])[0];
      return L ? {title: L.title, items: L.items.map(i => i.text + '|' + (i.memo || ''))} : null;
    }""")
    check("복구: 리스트가 화면 상태에도 살아 있음",
          ls_state and ls_state["title"] == "여행 준비물" and ls_state["items"][0] == "여권|유효기간 확인", ls_state)

    # 화면 — 메모 탭 카드 2개
    go_note(page)
    todo_view = note_view(page)
    check("노트 화면: 메모 카드 2개 + 새 리스트 버튼",
          len(todo_view["cards"]) == 2 and todo_view["newCard"] == 1, todo_view["cards"])
    check("카드 제목이 원래대로", [c["title"] for c in todo_view["cards"]] == ["메모 카드 하나", "메모 카드 둘"],
          [c["title"] for c in todo_view["cards"]])
    check("카드 제목 색(titleBg)이 살아 있음",
          todo_view["cards"][0]["hd"] == "rgb(242, 207, 201)" and todo_view["cards"][1]["hd"] == "rgb(184, 202, 165)",
          [c["hd"] for c in todo_view["cards"]])
    check("카드 미리보기 항목도 갈라져 보임",
          all(len(c["items"]) > 0 for c in todo_view["cards"]) and
          todo_view["cards"][0]["items"][0] != todo_view["cards"][1]["items"][0],
          [c["items"] for c in todo_view["cards"]])
    page.screenshot(path=os.path.join(SHOT, "note-v27-repaired.png"))

    # 버킷 탭 카드 3개
    page.locator('#s-diary .segs [data-seg="bucket"]').click()
    page.wait_for_timeout(500)
    buck_view = note_view(page)
    check("노트 화면: 버킷 카드 3개", len(buck_view["cards"]) == 3, [c["title"] for c in buck_view["cards"]])
    check("버킷 카드 제목·색이 원래대로",
          [c["title"] for c in buck_view["cards"]] == ["버킷 하나", "버킷 둘", "버킷 셋"] and
          buck_view["cards"][0]["hd"] == "rgb(234, 153, 77)" and buck_view["cards"][2]["hd"] == "rgb(128, 164, 170)",
          [(c["title"], c["hd"]) for c in buck_view["cards"]])
    page.screenshot(path=os.path.join(SHOT, "note-v27-repaired-bucket.png"))

    # 카드 안으로 들어가면 상세 메모가 보임
    page.locator('#s-diary .segs [data-seg="todo"]').click()
    page.wait_for_timeout(400)
    page.locator("#s-diary .ncard[data-gid='g-t1']").click()
    page.wait_for_timeout(500)
    sheet = page.evaluate("""() => ({
      title: (document.querySelector('#sheet #sheetForm input[name="title"]') || {}).value || '',
      rows: Array.from(document.querySelectorAll('#sheet .card-items .trow')).length,
      subs: Array.from(document.querySelectorAll('#sheet .card-items .sub')).map(e => e.textContent.trim()),
      addForm: !!document.querySelector('#sheet #listAddForm')
    })""")
    check("카드 상세 시트: 제목·항목 8개", sheet["title"] == "메모 카드 하나" and sheet["rows"] == 8, sheet)
    check("카드 상세 시트: 상세 메모(메모내용)가 보임", "상세 메모 3" in sheet["subs"], sheet["subs"])
    check("카드 상세 시트: 항목 추가 칸이 있음", sheet["addForm"])
    page.screenshot(path=os.path.join(SHOT, "card-v27-repaired-memo.png"))

    # ---- 3-1. remote 모드에서 카드 안에 항목 추가 → 바로 저장·표시
    page.fill('#sheet #listAddForm input[name="text"]', "v27 새로 적은 메모")
    page.click("#sheet .todo-add-btn")
    page.wait_for_timeout(900)
    added = page.evaluate("""() => {
      const S = window.TwoLogUI.state;
      const row = (S.todos || []).filter(t => t.text === 'v27 새로 적은 메모')[0] || {};
      return {gid: row.gid || null, id: row.id || null,
              sheetRows: Array.from(document.querySelectorAll('#sheet .card-items .trow')).length,
              shown: document.querySelector('#sheet .card-items').innerText.indexOf('v27 새로 적은 메모') >= 0};
    }""")
    check("카드 안에서 만든 항목이 그 카드(g-t1·시트)에 바로 보임",
          added["gid"] == "g-t1" and added["shown"] and added["sheetRows"] == 9, added)
    saved = page.evaluate("""(id) => {
      const st = window.__stub;
      const r = (st.notes || []).filter(x => x.id === id)[0];
      return r ? {kind: r.kind, text: r.payload.text, gid: r.payload.gid} : null;
    }""", added["id"])
    check("카드 안에서 만든 항목이 서버(notes)에 gid 와 함께 바로 저장됨",
          saved and saved["text"] == "v27 새로 적은 메모" and saved["gid"] == "g-t1", saved)

    # ---- 3-2. 그 항목의 상세 메모를 고치면 바로 저장
    page.locator("#sheet .card-items .trow .body", has_text="v27 새로 적은 메모").click()
    page.wait_for_timeout(500)
    page.fill('#sheetForm textarea[name="memo"]', "v27 상세 메모 입력")
    page.locator("#sheetForm button[type=submit]").click()
    page.wait_for_timeout(900)
    edited = page.evaluate("""(id) => {
      const S = window.TwoLogUI.state;
      const row = (S.todos || []).filter(t => t.id === id)[0] || {};
      const st = window.__stub;
      const r = (st.notes || []).filter(x => x.id === id)[0];
      return {memo: row.memo || '', server: r ? (r.payload.memo || '') : null};
    }""", added["id"])
    check("항목 상세 메모를 고치면 바로 저장됨",
          edited["memo"] == "v27 상세 메모 입력" and edited["server"] == "v27 상세 메모 입력", edited)

    # ---- 3-3. Realtime 다시 읽기 뒤에도 그 카드 자리에 남아 있음
    page.keyboard.press("Escape")
    page.wait_for_timeout(300)
    cid = after["coupleId"]
    page.evaluate("(c) => window.__stubEmit('notes', c)", cid)
    page.wait_for_timeout(2200)
    rt = state_summary(page)
    rt_item = page.evaluate("""(id) => {
      const t = (window.TwoLogUI.state.todos || []).filter(x => x.id === id)[0] || {};
      return {gid: t.gid || null, memo: t.memo || ''};
    }""", added["id"])
    check("Realtime 다시 읽기 뒤에도 새 항목이 그 카드에 남음",
          rt_item["gid"] == "g-t1" and len(rt["gTodo"]) == 2, (rt_item, rt["gTodo"]))
    check("Realtime 뒤에도 카드 2개 · 버킷 3개 그대로",
          len(rt["gTodo"]) == 2 and len(rt["gBucket"]) == 3, (rt["gTodo"], rt["gBucket"]))

    # ---- 3-4. 새로 열어도 다시 복구하지 않고, 카드·항목이 그대로
    n_before = len(stub(page, "notes"))
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(3000)
    reload_sum = state_summary(page)
    check("새로 열어도 카드 2/3 유지 · 항목 중복 없음",
          len(reload_sum["gTodo"]) == 2 and len(reload_sum["gBucket"]) == 3 and
          len(stub(page, "notes")) == n_before and reload_sum["todos"] == 17,
          (reload_sum["gTodo"], reload_sum["gBucket"], len(stub(page, "notes")), reload_sum["todos"]))
    check("새로 열면 복구 토스트가 다시 뜨지 않음", "노트 카드를 되살렸어요" not in reload_sum["toast"],
          reload_sum["toast"])

    # ---- 3-5. 앱이 다시 저장해도 gid·groups 가 지워지지 않음
    page.evaluate("() => window.TwoLogStore.flush()")
    page.wait_for_timeout(1200)
    keep = page.evaluate("""() => {
      const st = window.__stub;
      const notes = st.notes || [];
      const g = (st.settings || []).filter(r => r.key === 'groups')[0];
      return {notes: notes.length,
              noGid: notes.filter(r => r.kind !== 'list' && !(r.payload || {}).gid).length,
              groups: g ? {todo: (g.value.todo || []).length, bucket: (g.value.bucket || []).length,
                           log: (g.value.log || []).length, bg: (g.value.todo[0] || {}).titleBg} : null};
    }""")
    check("앱이 다시 저장해도 notes 의 gid·settings 의 groups 가 그대로",
          keep["noGid"] == 0 and keep["groups"] and keep["groups"]["todo"] == 2 and
          keep["groups"]["bucket"] == 3 and keep["groups"]["bg"] == "#F2CFC9", keep)
    check("복구 흐름에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    page.screenshot(path=os.path.join(SHOT, "note-v27-after-reload.png"))

    # ---- 3-6. 상대가 바꾸면 조용하게 바로 반영 (Realtime) · 깨었을 때 당겨오기
    go_note(page)
    page.wait_for_timeout(400)
    page.evaluate("""(cid) => {
      const st = window.__stub;
      const r = (st.notes || []).filter(x => x.id === 'lt1')[0];
      r.payload.text = '상대가 고친 메모 1';
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      return window.__stubEmit('notes', cid);
    }""", cid)
    page.wait_for_timeout(2200)
    rt2 = page.evaluate("""() => ({
      text: document.querySelector('#s-diary').innerText,
      toast: (document.getElementById('toast') || {}).textContent || '',
      state: ((window.TwoLogUI.state.todos || []).filter(t => t.id === 'lt1')[0] || {}).text
    })""")
    check("Realtime: 상대가 고친 메모가 새로 열지 않아도 바로 보임",
          "상대가 고친 메모 1" in rt2["text"] and rt2["state"] == "상대가 고친 메모 1", rt2)
    check("Realtime: 「상대와 맞췄어요」 토스트가 뜨지 않음", "상대와 맞췄어요" not in rt2["toast"], rt2["toast"])

    page.evaluate("""(cid) => {
      const st = window.__stub;
      const g = (st.settings || []).filter(x => x.key === 'groups')[0];
      g.value.todo[1].title = '상대가 바꾼 카드';
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      return window.__stubEmit('settings', cid);
    }""", cid)
    page.wait_for_timeout(2200)
    g_rt = note_view(page)
    check("Realtime: 상대가 바꾼 카드 이름(settings groups)도 바로 반영",
          len(g_rt["cards"]) == 2 and g_rt["cards"][1]["title"] == "상대가 바꾼 카드",
          [c["title"] for c in g_rt["cards"]])
    check("Realtime: 카드 이름을 바꿔도 토스트는 없음",
          "상대와 맞췄어요" not in page.evaluate("(document.getElementById('toast')||{}).textContent||''"))

    page.evaluate("""(cid) => {
      const st = window.__stub;
      st.couples[0].you = '이준영님';
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      return window.__stubEmit('couples', cid);
    }""", cid)
    page.wait_for_timeout(2200)
    c_rt = page.evaluate("() => (window.TwoLogUI.state.couple || {}).you")
    check("Realtime: 상대가 바꾼 커플 정보(이름)도 바로 반영", c_rt == "이준영님", c_rt)

    # 앱으로 돌아왔을 때(focus) 서버 상태를 당겨오는지 — Realtime 이 끊겼던 상황
    page.evaluate("""() => {
      const st = window.__stub;
      const r = (st.notes || []).filter(x => x.id === 'lt2')[0];
      r.payload.text = '깨어날 때 당겨온 메모';
      localStorage.setItem('stub-sb-db', JSON.stringify(st));
      window.dispatchEvent(new Event('focus'));
    }""")
    page.wait_for_timeout(2200)
    pull_txt = page.evaluate("() => ((window.TwoLogUI.state.todos || []).filter(t => t.id === 'lt2')[0] || {}).text")
    check("앱으로 돌아오면(focus) 서버의 최신 상태를 조용히 당겨옴", pull_txt == "깨어날 때 당겨온 메모", pull_txt)

    # ==================================================================
    # 4. 상대 폰에서도 같은 카드·같은 분배
    # ==================================================================
    db = page.evaluate("JSON.parse(localStorage.getItem('stub-sb-db'))")
    a_user = db["couples"][0]["members"][0]
    db["users"]["user-b"] = {"id": "user-b", "email": "partner@twolog.app", "password": "twolog1234"}
    db["couples"][0]["members"] = [a_user, "user-b"]
    seed_b = """(() => {
      if (localStorage.getItem('stub-sb-db')) return;
      localStorage.setItem('stub-sb-db', %s);
      localStorage.setItem('stub-sb-session', JSON.stringify({
        access_token: 't', refresh_token: 'r', user: { id: 'user-b', email: 'partner@twolog.app' } }));
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
    page_b.wait_for_timeout(3000)

    pb = state_summary(page_b)
    check("상대 폰: 메모 카드 2개 · 버킷 3개", len(pb["gTodo"]) == 2 and len(pb["gBucket"]) == 3,
          (pb["gTodo"], pb["gBucket"]))
    check("상대 폰: 항목이 같은 카드로 갈라짐",
          pb["todoByGid"].get("g-t1") == 9 and pb["todoByGid"].get("g-t2") == 8 and
          pb["bucketByGid"].get("g-b3") == 6, (pb["todoByGid"], pb["bucketByGid"]))
    check("상대 폰: 상세 메모도 그대로", pb["memoKept"] == 6, pb["memoKept"])
    go_note(page_b)
    vb = note_view(page_b)
    check("상대 폰 화면: 카드 제목·색 동일",
          [c["title"] for c in vb["cards"]] == ["메모 카드 하나", "상대가 바꾼 카드"] and
          vb["cards"][0]["hd"] == "rgb(242, 207, 201)", [(c["title"], c["hd"]) for c in vb["cards"]])
    page_b.locator('#s-diary .segs [data-seg="bucket"]').click()
    page_b.wait_for_timeout(500)
    vb2 = note_view(page_b)
    check("상대 폰 화면: 버킷 카드 3개", len(vb2["cards"]) == 3, [c["title"] for c in vb2["cards"]])
    page_b.screenshot(path=os.path.join(SHOT, "note-v27-partner.png"))

    # ---- 상대 프로필 시트: 프사 변경이 잠겨도 프사 옆에 「닉네임」 · 동그란 컬러
    page_b.locator("#tabbar .tab").nth(4).click()
    page_b.wait_for_timeout(500)
    page_b.locator('#s-set [data-act="personSheet"][data-who="you"]').click()
    page_b.wait_for_timeout(500)
    ps_b = page_b.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const avb = sh.querySelector('.pr-avbtn');
      const sws = Array.from(sh.querySelectorAll('.pr-sws .sw'));
      return {text: sh.innerText.replace(/\\s+/g, ' '),
              plus: sh.querySelectorAll('.pr-plus').length,
              avAct: avb ? avb.getAttribute('data-act') : 'none',
              lbls: Array.from(sh.querySelectorAll('.pr-lbl')).map(e => e.textContent.trim()),
              sws: sws.length,
              round: sws.length ? Math.round(parseFloat(getComputedStyle(sws[0]).borderRadius) /
                                  parseFloat(getComputedStyle(sws[0]).width) * 100) : 0};
    }""")
    check("상대 프로필 시트: 프사 변경이 잠겨 + 배지·사진 버튼이 없음",
          ps_b["plus"] == 0 and ps_b["avAct"] in (None, "none"), ps_b)
    check("상대 프로필 시트: 프사 옆에 「닉네임」 한 칸", ps_b["lbls"] == ["닉네임"], ps_b["lbls"])
    check("상대 프로필 시트: 「컬러」 라벨 + 동그란 12색",
          "컬러" in ps_b["text"] and ps_b["sws"] == 12 and ps_b["round"] >= 49, ps_b)
    check("상대 폰에서 콘솔/스크립트 오류 없음", len(errs_b) == 0, errs_b[:3])
    ctx_b.close()
    ctx.close()

    # ==================================================================
    # 5. 새 기기 — 폰 기록을 이어 올 때 groups·gid·lists·logs 가 함께
    # ==================================================================
    ctx = new_ctx(browser)
    seed2 = r"""(() => {
      const today = (() => { const d = new Date();
        return d.getFullYear() + '-' + String(d.getMonth()+1).padStart(2,'0') + '-' + String(d.getDate()).padStart(2,'0'); })();
      localStorage.setItem('twolog:v1:state', JSON.stringify({
        couple: { me: '박소영', you: '이준영', since: '2024-05-01', fmt: 'D', phrase: '함께한 지',
                  colors: { me: '#9E636B', you: '#3D5C82' }, sched: { me: '#9E636B', you: '#3D5C82', both: '#625A7F' } },
        link: { code: '999999', connected: false, partnerCode: '' },
        auth: { out: false, email: '' },
        theme: { name: null, log: null, mode: 'light' },
        groups: {
          todo: [ { id: 'n-t1', title: '메모 A', caption: '', who: 'me', date: today, titleBg: '#F2CFC9' },
                  { id: 'n-t2', title: '메모 B', caption: '', who: 'me', date: today, titleBg: '#D2CBE3' } ],
          bucket: [ { id: 'n-b1', title: '버킷 A', caption: '', who: 'me', date: today, titleBg: '#EA994D' },
                    { id: 'n-b2', title: '버킷 B', caption: '', who: 'me', date: today, titleBg: '#80A4AA' },
                    { id: 'n-b3', title: '버킷 C', caption: '', who: 'me', date: today, titleBg: '' } ],
          log: [ { id: 'n-l1', title: '영화·먹방', caption: '', who: 'me', date: today } ]
        },
        todos: [ { id: 'n1', text: '새 기기 메모 1', memo: '메모 상세 1', done: false, who: '나', gid: 'n-t1' },
                 { id: 'n2', text: '새 기기 메모 2', memo: '', done: true, who: '함께', gid: 'n-t1' },
                 { id: 'n3', text: '새 기기 메모 3', memo: '', done: false, who: '나', gid: 'n-t2' } ],
        bucket: [ { id: 'nb1', title: '새 버킷 1', cat: '여행', memo: '버킷 상세', done: false, gid: 'n-b1' },
                  { id: 'nb2', title: '새 버킷 2', cat: '맛집', memo: '', done: true, gid: 'n-b2' },
                  { id: 'nb3', title: '새 버킷 3', cat: '취미', memo: '', done: false, gid: 'n-b3' } ],
        logs: [ { id: 'nl1', kind: 'movie', title: '새 영화', rating: 5, date: today, review: '좋았음', place: '', done: true, gid: 'n-l1' } ],
        lists: [ { id: 'nlst1', title: '여행 준비물', emoji: '🧳', kind: 'check', items: [
                    { id: 'li1', text: '여권', memo: '유효기간 확인', done: false },
                    { id: 'li2', text: '충전기', memo: '', done: true } ] },
                  { id: 'nlst2', title: '선물 아이디어', emoji: '🎁', kind: 'memo', items: [
                    { id: 'li3', text: '향초 세트', memo: '겨울 한정', done: false } ] } ],
        expenses: [], photos: [],
        ui: { seg: 'todo', expMonth: today.slice(0, 7), calMonth: today.slice(0, 7), selDate: today }
      }));
    })();"""
    ctx.add_init_script(seed2)
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    stub_route(page)
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#s-login .login", timeout=20000)
    signup(page, "v27.fresh@twolog.app", "twolog1234")
    page.wait_for_timeout(3000)

    mig = state_summary(page)
    check("새 기기 이전: 카드가 처음부터 함께 올라감 (2/3/1)",
          len(mig["gTodo"]) == 2 and len(mig["gBucket"]) == 3 and len(mig["gLog"]) == 1,
          (mig["gTodo"], mig["gBucket"], mig["gLog"]))
    check("새 기기 이전: 항목마다 gid", mig["todoGidMissing"] == 0 and mig["bucketGidMissing"] == 0,
          (mig["todoGidMissing"], mig["bucketGidMissing"]))
    check("새 기기 이전: lists(2개)와 항목·상세 메모까지",
          mig["lists"] == 2 and mig["listItems"][0] == ["여권|유효기간 확인", "충전기|"], mig["listItems"])
    remote_notes = stub(page, "notes")
    kinds = {}
    for r in remote_notes:
        kinds[r["kind"]] = kinds.get(r["kind"], 0) + 1
    check("새 기기 이전: 원격 notes 에 todo·bucket·log·list 넷 다 있음",
          kinds.get("todo") == 3 and kinds.get("bucket") == 3 and kinds.get("log") == 1 and kinds.get("list") == 2, kinds)
    check("새 기기 이전: 원격에도 gid·memo 가 들어감",
          all((r.get("payload") or {}).get("gid") for r in remote_notes if r["kind"] in ("todo", "bucket", "log")) and
          [r for r in remote_notes if r["id"] == "n1"][0]["payload"].get("memo") == "메모 상세 1",
          [(r["id"], (r.get("payload") or {}).get("gid")) for r in remote_notes][:5])
    list_row = [r for r in remote_notes if r["kind"] == "list" and r["payload"].get("title") == "여행 준비물"]
    check("새 기기 이전: 원격 list 항목의 상세 메모도 저장",
          list_row and list_row[0]["payload"]["items"][0]["memo"] == "유효기간 확인",
          list_row[0]["payload"] if list_row else None)
    gset = [r for r in stub(page, "settings") if r.get("key") == "groups"]
    check("새 기기 이전: settings groups 행도 함께", len(gset) == 1 and len(gset[0]["value"]["bucket"]) == 3,
          gset[0]["value"] if gset else None)

    go_note(page)
    v = note_view(page)
    check("새 기기 화면: 메모 카드 2개(제목·색)", len(v["cards"]) == 2 and
          [c["title"] for c in v["cards"]] == ["메모 A", "메모 B"] and
          v["cards"][0]["hd"] == "rgb(242, 207, 201)", v["cards"])
    page.locator('#s-diary .segs [data-seg="bucket"]').click()
    page.wait_for_timeout(450)
    check("새 기기 화면: 버킷 카드 3개", len(note_view(page)["cards"]) == 3)
    page.locator('#s-diary .segs [data-seg="log"]').click()
    page.wait_for_timeout(450)
    check("새 기기 화면: 영화·먹방 카드 1개", len(note_view(page)["cards"]) == 1)
    page.screenshot(path=os.path.join(SHOT, "note-v27-fresh-migrated.png"))

    # 새로 열어도 카드 구성이 그대로
    page.goto(URL, wait_until="domcontentloaded")
    page.wait_for_selector("#tabbar .tab", timeout=25000)
    page.wait_for_timeout(2500)
    again = state_summary(page)
    check("새 기기: 새로 열어도 카드 2/3/1 그대로 · 항목 중복 없음",
          len(again["gTodo"]) == 2 and len(again["gBucket"]) == 3 and len(again["gLog"]) == 1 and
          again["todos"] == 3 and again["lists"] == 2,
          (again["gTodo"], again["gBucket"], again["gLog"], again["todos"], again["lists"]))
    check("새 기기 흐름에서 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 6. local 모드 — 그대로
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
      const res = await st.repairGroups();
      return {mode: st.mode, reason: res && res.reason, flag: st.groupsRepaired()};
    }""")
    check("local 모드: repairGroups 는 local_mode 로만 답함",
          loc["mode"] == "local" and loc["reason"] == "local_mode" and loc["flag"] is None, loc)
    go_note(page)
    card = page.evaluate("""() => {
      const S = window.TwoLogUI.state;
      return {todo: S.groups.todo.length, bucket: S.groups.bucket.length,
              cards: document.querySelectorAll('#s-diary .ncard[data-gid]').length,
              stored: (JSON.parse(localStorage.getItem('twolog:v1:state') || '{}').groups || {}).todo || null};
    }""")
    check("local 모드: 카드 기본값 유지·저장", card["todo"] == 1 and card["bucket"] == 1 and card["cards"] == 1,
          card)
    check("local 모드: 콘솔/스크립트 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    # ==================================================================
    # 7. My 탭 프로필 시트 — 프사 ＋ 배지·닉네임·동그란 컬러 / 동그라미 크롭
    # ==================================================================
    ctx = new_ctx(browser)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")
    page = ctx.new_page()
    errs = []
    page.on("pageerror", lambda e: errs.append("pageerror: " + str(e)))
    page.on("console", lambda m: errs.append("console: " + m.text) if m.type == "error" else None)
    page.goto(URL, wait_until="networkidle")
    page.wait_for_timeout(700)
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(500)
    page.locator('#s-set [data-act="personSheet"][data-who="me"]').click()
    page.wait_for_timeout(500)
    ps = page.evaluate("""() => {
      const sh = document.querySelector('#sheet');
      const avb = sh.querySelector('.pr-avbtn');
      const sws = Array.from(sh.querySelectorAll('.pr-sws .sw'));
      const first = sws[0];
      return {text: sh.innerText.replace(/\\s+/g, ' '),
              plus: !!sh.querySelector('.pr-plus'),
              avAct: avb ? avb.getAttribute('data-act') : null,
              lbls: Array.from(sh.querySelectorAll('.pr-lbl')).map(e => e.textContent.trim()),
              colorLbl: Array.from(sh.querySelectorAll('.pr-color .set-lbl')).map(e => e.textContent.trim()),
              sws: sws.length,
              cols: sws.map(b => getComputedStyle(b).backgroundColor),
              round: first ? Math.round(parseFloat(getComputedStyle(first).borderRadius) /
                                parseFloat(getComputedStyle(first).width) * 100) : 0,
              ownNm: sh.querySelectorAll('.own-nm').length,
              ownChip: sh.querySelectorAll('.own-chip').length,
              nameField: !!sh.querySelector('#personForm input[name="name"]')};
    }""")
    check("프로필 시트: 프사에 ＋ 배지 · 누르면 사진첩", ps["plus"] and ps["avAct"] == "pickPic", ps)
    check("프로필 시트: 글씨 버튼 삭제(사진첩 선택·사진 지우기)",
          "사진첩에서 선택" not in ps["text"] and "사진 지우기" not in ps["text"], ps["text"])
    check("프로필 시트: 프사 옆 「닉네임」 한 칸", ps["lbls"] == ["닉네임"] and ps["nameField"], ps["lbls"])
    check("프로필 시트: 「닉네임 바꾸기」 표현이 없음", "닉네임 바꾸기" not in ps["text"], ps["text"])
    check("프로필 시트: 「컬러」 라벨", ps["colorLbl"] == ["컬러"], ps["colorLbl"])
    check("프로필 시트: 이름+컬러 표기·네모 컬러 미리보기가 없음",
          ps["ownNm"] == 0 and ps["ownChip"] == 0 and "컬러 #" not in ps["text"], (ps["ownNm"], ps["ownChip"]))
    MUTED_RGB = ["rgb(242, 207, 201)", "rgb(222, 162, 166)", "rgb(221, 120, 91)", "rgb(234, 153, 77)",
                 "rgb(239, 211, 83)", "rgb(196, 198, 106)", "rgb(184, 202, 165)", "rgb(180, 216, 212)",
                 "rgb(128, 164, 170)", "rgb(210, 203, 227)", "rgb(162, 153, 184)", "rgb(196, 178, 142)"]
    check("프로필 시트: 컬러판 12색이 MUTED 팔레트", ps["sws"] == 12 and ps["cols"] == MUTED_RGB, ps["cols"])
    check("프로필 시트: 컬러 칩이 동그라미", ps["round"] >= 49, ps["round"])
    page.screenshot(path=os.path.join(SHOT, "my-v27-person-sheet.png"))

    # ---- 7-1. 프사 누르면 사진첩이 열리고, 고르면 동그라미 가이드 크롭 화면
    with page.expect_file_chooser() as fc:
        page.locator("#sheet .pr-avbtn").click()
    fc.value.set_files(JPG)
    page.wait_for_timeout(1000)
    crop = page.evaluate("""() => {
      const o = document.querySelector('#avCrop');
      const st = document.querySelector('.avcrop-stage');
      const cs = st ? getComputedStyle(st) : null;
      const z = document.querySelector('#avcZoom');
      return {open: !!o, r: st ? Math.round(st.getBoundingClientRect().width) : 0,
              radius: cs ? cs.borderRadius : "",
              bg: o ? getComputedStyle(o).backgroundColor : '',
              apply: !!document.querySelector('#avcApply'), cancel: !!document.querySelector('#avcCancel'),
              slider: z ? [z.min, z.max] : null, img: !!document.querySelector('#avcImg')};
    }""")
    round_ok = (crop["radius"] == "50%" or
                (str(crop["radius"]).endswith("px") and float(str(crop["radius"])[:-2]) >= crop["r"] / 2 - 1))
    check("사진을 고르면 크롭 화면이 뜸(어두운 배경 + 동그라미 가이드)",
          crop["open"] and crop["img"] and round_ok and
          crop["bg"] in ("rgb(8, 8, 10)", "rgba(8, 8, 10, 0.985)"), crop)
    check("크롭 화면: 취소·적용 버튼과 확대 슬라이더",
          crop["apply"] and crop["cancel"] and crop["slider"] == ["1", "3"], crop["slider"])
    page.screenshot(path=os.path.join(SHOT, "my-v27-avatar-crop.png"))

    # 드래그로 위치 옮기기 · 슬라이더로 확대
    box = page.locator(".avcrop-stage").bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] / 2 + 18, box["y"] + box["height"] / 2 + 12, steps=6)
    page.mouse.up()
    page.wait_for_timeout(250)
    moved = page.evaluate("() => document.getElementById('avcImg').style.transform")
    mx = re.search(r"calc\(-50% \+ (-?[\d.]+)px\)", moved or "")
    check("크롭 화면: 끌어서 사진 위치를 옮길 수 있음", bool(mx) and abs(float(mx.group(1))) >= 10, moved)
    page.evaluate("""() => { const z = document.getElementById('avcZoom');
      z.value = '2'; z.dispatchEvent(new Event('input', { bubbles: true })); }""")
    page.wait_for_timeout(250)
    zoomed = page.evaluate("() => document.getElementById('avcImg').style.transform")
    check("크롭 화면: 슬라이더로 확대", "scale(2)" in zoomed, zoomed)

    # 적용 → 256×256 JPEG 로 저장
    page.locator("#avcApply").click()
    page.wait_for_timeout(1400)
    saved = page.evaluate("""() => new Promise((res) => {
      const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      const src = ((s.couple || {}).pics || {}).me || '';
      const im = new Image();
      const out = (w, h) => res({head: src.slice(0, 22), len: src.length, w: w, h: h,
        overlay: !!document.querySelector('#avCrop'),
        shown: !!document.querySelector('#sheet .pr-av img.av-img')});
      im.onload = () => out(im.naturalWidth, im.naturalHeight);
      im.onerror = () => out(0, 0);
      im.src = src;
    })""")
    check("적용하면 256×256 JPEG 로 저장됨",
          saved["head"] == "data:image/jpeg;base64" and saved["w"] == 256 and saved["h"] == 256, saved)
    check("적용 뒤 크롭 화면이 닫히고 시트에 사진이 보임", not saved["overlay"] and saved["shown"], saved)
    page.screenshot(path=os.path.join(SHOT, "my-v27-avatar-applied.png"))

    # ---- 7-2. 취소하면 저장되지 않음
    before_len = saved["len"]
    with page.expect_file_chooser() as fc2:
        page.locator("#sheet .pr-avbtn").click()
    fc2.value.set_files(JPG)
    page.wait_for_timeout(900)
    page.locator("#avcCancel").click()
    page.wait_for_timeout(500)
    cancelled = page.evaluate("""() => {
      const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      return {overlay: !!document.querySelector('#avCrop'),
              len: (((s.couple || {}).pics || {}).me || '').length};
    }""")
    check("취소를 누르면 저장하지 않고 닫힘", (not cancelled["overlay"]) and cancelled["len"] == before_len, cancelled)

    # ---- 7-3. 컬러를 고르면 그 색으로 저장
    page.evaluate("""() => { const b = document.querySelectorAll('#sheet .pr-sws .sw')[3]; b.click(); }""")
    page.wait_for_timeout(600)
    col = page.evaluate("""() => ({
      colors: (window.TwoLogUI.state.couple.colors || {}).me,
      sched: (window.TwoLogUI.state.couple.sched || {}).me,
      sel: document.querySelectorAll('#sheet .pr-sws .sw.sel').length}) """)
    check("컬러를 고르면 프로필·일정 색으로 저장되고 하나만 선택 표시",
          col["colors"] == "#EA994D" and col["sched"] == "#EA994D" and col["sel"] == 1, col)

    # ---- 7-4. 닉네임은 프사 옆 칸에서 그대로 저장
    page.fill('#personForm input[name="name"]', "소영이")
    page.locator('#personForm button[type="submit"]').click()
    page.wait_for_timeout(700)
    nick = page.evaluate("""() => {
      const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      return {me: (window.TwoLogUI.state.couple || {}).me, stored: (s.couple || {}).me,
              sheet: document.getElementById('sheetWrap').classList.contains('open')};
    }""")
    check("닉네임을 프사 옆 칸에서 바꾸면 저장됨",
          nick["me"] == "소영이" and nick["stored"] == "소영이" and not nick["sheet"], nick)

    # ---- 7-5. 사진 지우기는 프사 위 작은 × 로 (글씨 버튼 없이)
    page.locator('#s-set [data-act="personSheet"][data-who="me"]').click()
    page.wait_for_timeout(450)
    page.locator("#sheet .pr-del").click()
    page.wait_for_timeout(700)
    cleared = page.evaluate("""() => {
      const s = JSON.parse(localStorage.getItem('twolog:v1:state') || '{}');
      return {pics: Object.keys(((s.couple || {}).pics) || {}),
              img: !!document.querySelector('#sheet .pr-av img'),
              del: !!document.querySelector('#sheet .pr-del')};
    }""")
    check("프사 위 × 를 누르면 사진이 지워지고 × 도 사라짐",
          cleared["pics"] == [] and not cleared["img"] and not cleared["del"], cleared)
    check("프로필 시트 확인 중 오류 없음", len(errs) == 0, errs[:3])
    ctx.close()

    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
