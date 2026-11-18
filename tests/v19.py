"""투로그 v19 확인 — 컬러 시트에서 안내 문구·팔레트 라벨(다가오는 일정 · N월의 우리)·
헥스 코드를 지우고, 화면/12색/컬러·기본/완료만 남겼는지 봅니다.

    python3 tests/v19.py            # 스크린샷은 downloads/twolog-screens/ 에 저장
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
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
    ctx.add_init_script("window.__TWOLOG_MODE = 'local';")  # v25: 이 테스트는 로컬 모드 고정
    page = ctx.new_page()
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    # 예시 데이터로 한 번 열어 상태를 만들고, 저장되는 일반 모드로 옮겨요
    page.goto(URL + "?demo=1", wait_until="networkidle")
    page.wait_for_timeout(700)
    state = page.evaluate("JSON.stringify(window.__app.state)")
    page.goto(URL, wait_until="domcontentloaded")
    page.evaluate("(s) => localStorage.setItem('twolog:v1:state', s)", state)
    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)

    # ---------------- 컬러 시트 열기 ----------------
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(450)
    txt = page.locator("#sheet").inner_text()
    print("---- 컬러 시트 ----")
    print(txt)
    print("-------------------")

    check("제목은 컬러", "컬러" in txt)
    check("위 안내 문구 없음", "화면 밝기와 홈 제목 줄 색을 골라 주세요" not in txt and "골라 주세요" not in txt)
    check("팔레트 옛 라벨 없음", "다가오는 일정" not in txt and "월의 우리" not in txt)
    check("헥스 코드 표시 없음", "#" not in txt, [l for l in txt.split("\n") if "#" in l])
    check("헥스 코드 요소(cp-val data-val) 없음", page.locator('#sheet .cp-val[data-val="homeTitleBg"]').count() == 0)

    # 화면 → 컬러 두 섹션 제목
    caps = page.evaluate("""(() => {
      const a = Array.from(document.querySelectorAll('#sheet .cp > .cp-hd > span:first-child'))
        .filter(s => s.textContent.trim() === '화면' || s.textContent.trim() === '컬러');
      return a.map(s => { const cs = getComputedStyle(s); const r = s.getBoundingClientRect();
        return {t: s.textContent.trim(), fs: cs.fontSize, fw: cs.fontWeight, lh: cs.lineHeight,
                ls: cs.letterSpacing, col: cs.color, top: Math.round(r.top)}; });
    })()""")
    check("두 섹션 제목 「화면」·「컬러」 있음", [c["t"] for c in caps] == ["화면", "컬러"], caps)
    if len(caps) == 2:
        same = all(caps[0][k] == caps[1][k] for k in ("fs", "fw", "lh", "ls", "col"))
        check("두 제목 글씨 크기·굵기·스타일 동일", same, caps)
        check("항목 이름 글씨 15px·700", caps[0]["fs"] == "15px" and caps[0]["fw"] == "700", caps[0])
        check("화면이 맨 위 · 컬러가 그 아래", caps[0]["top"] < caps[1]["top"], caps)

    # 남아야 하는 것
    check("화면 라이트/다크 유지", page.locator('#sheet .seg-btn[data-mode="light"]').count() == 1
          and page.locator('#sheet .seg-btn[data-mode="dark"]').count() == 1)
    check("팔레트 12색 유지", page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count() == 12,
          page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count())
    check("컬러 직접 고르기 유지", page.locator('#sheet .js-color[data-target="homeTitleBg"]').count() == 1
          and page.locator('#sheet .cp-pick span', has_text="컬러").count() == 1)
    check("기본 버튼 유지", page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').count() == 1)
    # v23: 홈에서 「N월의 우리」 섹션이 사라져 설명도 「홈 제목 줄」로
    check("하단 설명 유지", "고른 색은 홈 제목 줄" in txt)
    check("완료 버튼 유지", page.locator('#sheet .btn-primary[data-close="1"]').count() == 1)

    def btn_style():
        return page.evaluate("""(() => { const b = document.querySelector('#sheet .btn-primary');
          if (!b) return null; const cs = getComputedStyle(b);
          return {color: cs.color, bg: cs.backgroundColor, text: b.textContent.trim()};
        })()""")

    def dark_text(c):
        return c is not None and c["color"].startswith("rgb(") and max(int(x) for x in c["color"][4:-1].split(",")) <= 60

    # 색을 안 고른 기본 상태에서도 확인 버튼 글씨는 검정
    b0 = btn_style()
    check("기본 상태 완료 버튼 글씨 검정(라이트)", dark_text(b0) and b0["text"] == "완료", b0)

    # 빈 여백 없이 붙었는지 — 화면 블록 → 컬러 제목 → 팔레트
    gap = page.evaluate("""(() => {
      const seg = document.querySelector('#sheet .seg');
      const sw = document.querySelector('#sheet .sw-grid[data-sw="homeTitleBg"]');
      const caps = Array.from(document.querySelectorAll('#sheet .cp > .cp-hd > span:first-child'));
      const cap = caps.find(s => s.textContent.trim() === '컬러');
      const head = document.querySelector('#sheet .sh-head') || document.querySelector('#sheet h2');
      return { segBottom: seg.getBoundingClientRect().bottom, swTop: sw.getBoundingClientRect().top,
               capTop: cap.getBoundingClientRect().top, capBottom: cap.getBoundingClientRect().bottom,
               headBottom: head ? head.getBoundingClientRect().bottom : null,
               firstCpTop: document.querySelector('#sheet .cp').getBoundingClientRect().top };
    })()""")
    check("화면 ↔ 컬러 제목 사이 빈틈 없음 (≤40px)", (gap["capTop"] - gap["segBottom"]) <= 40, gap)
    check("컬러 제목 ↔ 팔레트 10px", abs((gap["swTop"] - gap["capBottom"]) - 10) <= 2, gap)
    check("시트 머리 ↔ 화면 블록 간격 정상 (≤40px)", (gap["firstCpTop"] - gap["headBottom"]) <= 40, gap)

    # ---------------- 다크로 바꾸고 색 하나 고르기 ----------------
    page.locator('#sheet .seg-btn[data-mode="dark"]').click()
    page.wait_for_timeout(450)
    check("다크 전환", page.evaluate("document.documentElement.getAttribute('data-mode')") == "dark")
    check("다크에서도 라벨·헥스 없음", page.locator('#sheet .cp-val[data-val="homeTitleBg"]').count() == 0
          and "월의 우리" not in page.locator("#sheet").inner_text())
    page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').nth(2).click()
    page.wait_for_timeout(500)
    picked = page.evaluate("window.__app.state.theme.homeTitleBg")
    check("3번째 색 선택 저장", bool(picked), picked)
    check("고른 뒤에도 헥스 코드 안 보임", "#" not in page.locator("#sheet").inner_text(),
          [l for l in page.locator("#sheet").inner_text().split("\n") if "#" in l])
    check("고른 색이 선택 표시됨", page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw.sel').count() == 1)
    b1 = btn_style()
    check("색 고른 뒤 완료 버튼 글씨 검정(다크·테라코타)", dark_text(b1) and b1["bg"].startswith("rgb("), b1)
    check("완료 버튼 배경은 고른 색", picked and picked.upper().strip("#") != "" and b1["bg"] != "rgba(0, 0, 0, 0)", b1)
    page.screenshot(path=os.path.join(SHOT, "theme-sheet-v19.png"))

    page.locator('#sheet .btn-primary[data-close="1"]').click()
    page.wait_for_timeout(450)
    tint = page.evaluate("""(() => {
      const a = document.querySelector('#s-home .sec-tint');
      return a ? (a.getAttribute('style') || '') : null;
    })()""")
    check("홈 제목 줄에 고른 색 적용", tint is not None and picked and picked.upper() in tint.upper(), tint)

    # ---------------- 기본으로 되돌리기 ----------------
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(450)
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(450)
    check("기본 누르면 색 비움", not page.evaluate("window.__app.state.theme.homeTitleBg"),
          page.evaluate("window.__app.state.theme.homeTitleBg"))
    check("기본 상태에서도 라벨·헥스 없음", "월의 우리" not in page.locator("#sheet").inner_text()
          and page.locator('#sheet .cp-val[data-val="homeTitleBg"]').count() == 0)
    page.locator('#sheet .btn-primary[data-close="1"]').click()
    page.wait_for_timeout(400)

    # ---------------- 라이트 모드 시트 한 장 더 ----------------
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(450)
    page.locator('#sheet .seg-btn[data-mode="light"]').click()
    page.wait_for_timeout(500)
    page.screenshot(path=os.path.join(SHOT, "theme-sheet-v19-light.png"))
    dark_px = page.evaluate("getComputedStyle(document.body).backgroundColor")
    check("라이트 전환", page.evaluate("document.documentElement.getAttribute('data-mode')") != "dark", dark_px)
    page.locator('#sheet .btn-primary[data-close="1"]').click()
    page.wait_for_timeout(400)

    # ---------------- 설정 > 테마 관리의 「홈 제목 색」은 그대로 ----------------
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(400)
    page.locator("#s-set [data-act='openThemeManager']").click()
    page.wait_for_timeout(450)
    mtxt = page.locator("#sheet").inner_text()
    # v23: 「N월의 우리」 섹션이 없어져 색 이름도 「다가오는 일정」만
    check("테마 관리에는 「홈 제목 색」 항목 그대로", "홈 제목 색" in mtxt and "다가오는 일정" in mtxt, mtxt[:200])
    page.locator('#sheet .seg-btn[data-mode="dark"]').click()
    page.wait_for_timeout(450)
    page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').nth(0).click()
    page.wait_for_timeout(450)
    mb = page.evaluate("""(() => { const b = document.querySelector('#sheet .btn-primary');
      const cs = getComputedStyle(b); return {color: cs.color, bg: cs.backgroundColor}; })()""")
    check("테마 관리 완료 버튼도 글씨 검정", dark_text(mb), mb)
    page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').click()
    page.wait_for_timeout(300)
    page.locator('#sheet .seg-btn[data-mode="light"]').click()
    page.wait_for_timeout(300)
    ml = page.evaluate("getComputedStyle(document.querySelector('#sheet .btn-primary')).color")
    check("색 비운 라이트 완료 버튼도 글씨 검정", max(int(x) for x in ml[4:-1].split(",")) <= 60, ml)
    page.locator('#sheet .btn-primary[data-close="1"]').click()
    page.wait_for_timeout(300)

    # ---------------- 노트: 리스트를 누르면 그 목록으로 들어간다 ----------------
    def sheet_open():
        return page.evaluate("(() => { const w = document.getElementById('sheetWrap'); return !!(w && w.classList.contains('open')); })()")

    def close_sheet():
        if sheet_open():
            page.locator('#sheet [data-close]').first.click()
            page.wait_for_timeout(300)

    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(500)
    check("노트 화면 열림", page.locator("#s-diary .ngrid").count() == 1)

    # 메모 탭에 카드 하나 더 만들어 두기
    page.locator("#s-diary .ncard.new").click()
    page.wait_for_timeout(400)
    page.fill('#sheet #sheetForm input[name="title"]', "주말 장보기")
    page.locator('#sheet button[type="submit"]').click()
    page.wait_for_timeout(500)
    check("메모 카드 2개", page.locator("#s-diary .ngrid .ncard:not(.new)").count() == 2,
          page.locator("#s-diary .ngrid .ncard:not(.new)").count())

    seg_names = ["메모", "버킷리스트", "영화·먹방"]
    for si in range(3):
        page.locator("#s-diary .segs .seg-btn").nth(si).click()
        page.wait_for_timeout(420)
        n = page.locator("#s-diary .ngrid .ncard:not(.new)").count()
        check("%s 탭 카드 %d개" % (seg_names[si], n), n >= 1, n)
        # v22: 제목 옆 숫자·꺾쇠는 사용자 요청으로 지웠어요
        check("%s 카드에 숫자·꺾쇠 없음" % seg_names[si],
              page.locator("#s-diary .ngrid .ncard:not(.new) .nc-go").count() == 0
              and page.locator("#s-diary .ngrid .ncard:not(.new) .nc-n").count() == 0)
        for j in range(n):
            card = page.locator("#s-diary .ngrid .ncard:not(.new)").nth(j)
            title = card.locator(".nc-t").inner_text().strip()
            card.locator(".nc-t").tap()
            page.wait_for_timeout(430)
            st2 = page.evaluate("""(() => { const i = document.querySelector('#sheet #sheetForm input[name=\"title\"]');
               return {title: i ? i.value : null, items: document.querySelectorAll('#sheet .card-items .trow').length}; })()""")
            check("%s 「%s」 누르면 그 목록 열림" % (seg_names[si], title),
                  sheet_open() and (st2["title"] or "").strip() == title, st2)
            close_sheet()

    # 메모 첫 카드: 항목 추가 → 체크 → 수정 → 카드에 반영
    page.locator("#s-diary .segs .seg-btn").nth(0).click()
    page.wait_for_timeout(420)
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-t").tap()
    page.wait_for_timeout(450)
    check("카드 시트에 부가설명 없음", page.locator("#sheet .card-meta .sheet-sub").count() == 0
          and "카드 맨 윗줄에" not in page.locator("#sheet").inner_text(),
          page.locator("#sheet").inner_text()[:90])
    before = page.locator("#sheet .card-items .trow").count()
    page.fill('#sheet #listAddForm input[name="text"]', "우유 사기")
    page.locator("#sheet .todo-add-btn").click()
    page.wait_for_timeout(450)
    after = page.locator("#sheet .card-items .trow").count()
    check("카드 목록에서 항목 추가", after == before + 1, (before, after))
    check("추가한 항목이 목록에 보임", "우유 사기" in page.locator("#sheet .card-items").inner_text())
    page.locator("#sheet .card-items .trow", has_text="우유 사기").first.locator(".circ").click()
    page.wait_for_timeout(500)
    milk_cls = page.locator("#sheet .card-items .trow", has_text="우유 사기").first.get_attribute("class") or ""
    check("카드 목록에서 체크", "done" in milk_cls, milk_cls)
    order = page.evaluate("Array.from(document.querySelectorAll('#sheet .card-items .trow')).map(r => r.classList.contains('done'))")
    check("체크한 항목은 카드 목록 맨 아래로", order == sorted(order), order)
    page.locator("#sheet .card-items .trow", has_text="우유 사기").first.locator(".body").click()
    page.wait_for_timeout(450)
    ed = page.evaluate("""(() => { const i = document.querySelector('#sheet #sheetForm input[name=\"text\"]');
       return {hd: document.querySelector('#sheet .sheet-hd h2').textContent, v: i ? i.value : null}; })()""")
    check("항목 본문 누르면 수정 열림", ed["hd"].strip().endswith("수정") and ed["v"] == "우유 사기", ed)
    page.fill('#sheet #sheetForm input[name="text"]', "우유 사기 (저지방)")
    page.locator('#sheet button[type="submit"]').click()
    page.wait_for_timeout(550)
    close_sheet()
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-t").tap()
    page.wait_for_timeout(450)
    check("수정한 항목이 목록에 남음", "저지방" in page.locator("#sheet .card-items").inner_text(),
          page.locator("#sheet .card-items").inner_text()[:120])
    close_sheet()
    prev = page.locator("#s-diary .ngrid .ncard:not(.new)").first.inner_text()
    # v22: 카드 제목 옆 개수·아래 「+N개」는 사용자 요청으로 지웠어요
    check("카드 미리보기에 항목만 (개수·+N 없음)",
          page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-n").count() == 0
          and "+" not in prev and "개" not in prev, prev[:80])

    # 살짝 길게 눌러도(순서 이동과 헷갈리는 경우) 그 목록이 열려야 함
    order_before = page.evaluate("Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-t')).map(e => e.textContent)")
    box = page.locator("#s-diary .ngrid .ncard:not(.new)").first.bounding_box()
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + 28)
    page.mouse.down()
    page.wait_for_timeout(430)
    page.mouse.up()
    page.wait_for_timeout(500)
    toast_txt = page.evaluate("(() => { const t = document.querySelector('.toast'); return t ? t.textContent : ''; })()")
    check("살짝 길게 눌러도 목록 열림", sheet_open())
    check("순서 바꿈 토스트 없음", "순서를 바꿨어요" not in toast_txt, toast_txt)
    close_sheet()
    order_after = page.evaluate("Array.from(document.querySelectorAll('#s-diary .ngrid .ncard:not(.new) .nc-t')).map(e => e.textContent)")
    check("누르기만 해서는 순서 그대로", order_before == order_after, (order_before, order_after))

    # 카드 안 미리보기 항목을 눌러도 (카드 안 체크가 아니라) 목록으로 들어감
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-items .cti").first.tap()
    page.wait_for_timeout(430)
    check("미리보기 항목을 눌러도 목록 열림", sheet_open())
    close_sheet()

    # 카드 안 동그라미를 눌러도 바깥에서는 체크되지 않고 목록으로 들어감
    done_state_before = page.evaluate("window.__app.state.todos.filter(t => t.done).length")
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-items .cti .cb").first.tap()
    page.wait_for_timeout(430)
    done_state_after = page.evaluate("window.__app.state.todos.filter(t => t.done).length")
    check("카드 동그라미를 눌러도 밖에서 체크 안 됨", done_state_before == done_state_after and sheet_open(),
          {"before": done_state_before, "after": done_state_after, "open": sheet_open()})
    close_sheet()

    # 키보드 Enter 로도 열기
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(430)
    check("Enter 로도 목록 열림", sheet_open())
    close_sheet()

    # 커스텀 리스트 칩: 누르면 그 리스트의 전체 목록
    page.locator("#s-diary .lchip").first.tap()
    page.wait_for_timeout(450)
    chip_name = page.locator("#s-diary .lchip").first.locator("span:last-child").inner_text().strip()
    body = page.locator("#s-diary .dbody").inner_text()
    check("커스텀 리스트 칩 누르면 그 리스트", chip_name in body and page.locator("#s-diary .lchip.active").count() == 1, body[:60])
    check("그 리스트 항목이 보임", page.locator("#s-diary .dbody .trow").count() >= 1,
          page.locator("#s-diary .dbody .trow").count())
    page.fill("#s-diary #listAddForm input[name=text]", "칩에서 바로 추가")
    page.locator("#s-diary .todo-add-btn").click()
    page.wait_for_timeout(450)
    check("리스트에 항목 추가", "칩에서 바로 추가" in page.locator("#s-diary .dbody").inner_text())
    page.locator("#s-diary .dbody .trow", has_text="칩에서 바로 추가").first.locator(".circ").click()
    page.wait_for_timeout(500)
    o2 = page.evaluate("Array.from(document.querySelectorAll('#s-diary .dbody .trow')).map(r => r.classList.contains('done'))")
    check("리스트에서도 체크한 항목이 아래로", o2 == sorted(o2), o2)
    page.locator("#s-diary .dbody .trow", has_text="칩에서 바로 추가").first.locator(".body").tap()
    page.wait_for_timeout(450)
    ed2 = page.evaluate("""(() => { const h = document.querySelector('#sheet .sheet-hd h2'); return h ? h.textContent : null; })()""")
    check("리스트 항목 누르면 수정 열림", bool(ed2) and ed2.strip().endswith("수정"), ed2)
    close_sheet()

    # ---------------- 버킷리스트: 카테고리 태그 없이, 글씨를 눌러도 체크만 ----------------
    page.locator("#s-diary .segs .seg-btn").nth(1).click()
    page.wait_for_timeout(420)
    check("버킷 카드에 카테고리 태그 없음", page.locator("#s-diary .tagchip").count() == 0,
          page.locator("#s-diary .tagchip").count())
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-t").tap()
    page.wait_for_timeout(450)
    check("버킷 목록에도 «기타» 태그 없음", page.locator("#sheet .card-items .tagchip").count() == 0
          and "기타" not in page.locator("#sheet .card-items").inner_text(),
          page.locator("#sheet .card-items").inner_text()[:80])
    done_before = page.locator("#sheet .card-items .trow.done").count()
    if page.locator("#sheet .card-items .trow:not(.done)").count() == 0:
        page.locator("#sheet .card-items .trow .circ").first.click()
        page.wait_for_timeout(400)
        done_before = page.locator("#sheet .card-items .trow.done").count()
    page.locator("#sheet .card-items .trow:not(.done) .body").last.click()
    page.wait_for_timeout(450)
    still_card = page.evaluate("!!document.querySelector('#sheet #sheetForm input[name=\"title\"]')")
    done_after = page.locator("#sheet .card-items .trow.done").count()
    check("버킷 항목 글씨 누르면 체크만 (수정 시트 안 열림)",
          still_card and done_after == done_before + 1,
          {"still_card": still_card, "before": done_before, "after": done_after})
    page.screenshot(path=os.path.join(SHOT, "note-detail-v19.png"))
    close_sheet()

    # ---------------- 항목 이름 글씨: 앱 전체 동일하게 14.5px·700 ----------------
    def label_css(sel):
        return page.evaluate("(sel) => Array.from(document.querySelectorAll(sel)).map(e => { const cs = getComputedStyle(e); return cs.fontSize + '/' + cs.fontWeight + '/' + cs.color; })", sel)

    found = {}
    page.locator("#tabbar .tab").nth(0).click()
    page.wait_for_timeout(400)
    page.locator('#s-home [data-act="openTheme"]').click()
    page.wait_for_timeout(450)
    found["컬러 시트"] = label_css("#sheet .cp-hd > span:first-child")
    close_sheet()
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(400)
    page.locator('#s-cal [data-act="addEvent"]').click()
    page.wait_for_timeout(450)
    found["일정 추가 시트"] = label_css("#sheet .f > label")
    close_sheet()
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(400)
    page.locator("#s-diary .ngrid .ncard:not(.new)").first.locator(".nc-t").tap()
    page.wait_for_timeout(450)
    found["노트 카드 시트"] = label_css("#sheet .f > label") + label_css("#sheet .todo-label")
    close_sheet()
    page.locator("#s-diary [data-act='noteSettings']").click()
    page.wait_for_timeout(450)
    found["노트 설정"] = label_css("#sheet .set-lbl")
    close_sheet()
    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(400)
    page.locator("#s-set [data-act='openThemeManager']").click()
    page.wait_for_timeout(450)
    found["테마 관리"] = label_css("#sheet .cp-hd > span:first-child")
    close_sheet()
    for k, v in found.items():
        check("%s 항목 이름 15px·700·검정" % k,
              bool(v) and all(x == "15px/700/rgb(9, 9, 11)" for x in v), v)
    all_vals = [x for v in found.values() for x in v]
    check("시트마다 항목 이름 글씨 동일", len(set(all_vals)) == 1, all_vals)

    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(400)
    page.screenshot(path=os.path.join(SHOT, "note-v19.png"))

    # ---------------- 캘린더: 테두리·격자선 없이 여백으로만 나눈 달력 (v20 에서 주 사이 가로선도 지웠어요) ----------------
    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(600)
    cal = page.evaluate("""(() => {
      const c = document.querySelector('#s-cal .cal'); const cs = getComputedStyle(c);
      const rows = Array.from(document.querySelectorAll('#s-cal .cal-row'));
      const days = Array.from(document.querySelectorAll('#s-cal .day'));
      const sel = document.querySelector('#s-cal .day.sel');
      const dnum = sel ? sel.querySelector('.dnum') : null;
      return {border: cs.borderTopWidth + '/' + cs.borderLeftWidth, bg: cs.backgroundColor,
        rows: rows.length, row2: rows.length > 1 ? getComputedStyle(rows[1]).borderTopWidth : null,
        row1: rows.length > 0 ? getComputedStyle(rows[0]).borderTopWidth : null,
        selBg: sel ? getComputedStyle(sel).backgroundColor : null,
        numBg: sel && sel.querySelector('.dnum') ? getComputedStyle(sel.querySelector('.dnum')).backgroundColor : null,
        numColor: dnum ? getComputedStyle(dnum).color : null,
        selShadow: sel ? getComputedStyle(sel).boxShadow : null,
        dayBorders: days.filter(d => { const s = getComputedStyle(d); return s.borderTopWidth !== '0px' || s.borderLeftWidth !== '0px' || s.borderRightWidth !== '0px'; }).length,
        ebars: document.querySelectorAll('#s-cal .ebar').length,
        todayAfter: getComputedStyle(document.querySelector('#s-cal .day.today') || document.createElement('div'), '::after').content};
    })()""")
    check("달력 바깥 테두리 없음", cal["border"] == "0px/0px", cal["border"])
    check("달력 배경 투명", cal["bg"] in ("rgba(0, 0, 0, 0)", "transparent"), cal["bg"])
    check("주 행 사이 가로선 없음", cal["row1"] in ("0px", None) and cal["row2"] in ("0px", None), (cal["row1"], cal["row2"]))
    check("날짜 칸에 테두리·격자선 없음", cal["dayBorders"] == 0, cal["dayBorders"])
    # v23: 칸을 다 칠하지 않고 날짜 숫자에만 동그라미
    check("선택한 날 = 칸은 그대로 두고 숫자에만 표시",
          cal["selBg"] in ("rgba(0, 0, 0, 0)", "transparent") and cal["numBg"] == "rgb(9, 9, 11)",
          (cal["selBg"], cal["numBg"]))
    check("선택한 날 글씨 반전", cal["numColor"] == "rgb(255, 255, 255)", cal["numColor"])
    check("선택한 날 테두리 상자 없음", cal["selShadow"] == "none", cal["selShadow"])
    check("여러 날 일정 막대 유지", cal["ebars"] >= 1, cal["ebars"])

    # 상단 (v20): 왼쪽에 「11월」 · 바로 옆에 작은 화살표 · 같은 줄 오른쪽 끝에 검색 아이콘
    head = page.evaluate("""(() => {
      const cal = document.querySelector('#s-cal .cal'); const cr = cal.getBoundingClientRect();
      const mo = document.querySelector('#s-cal .cal-month'); const mr = mo.getBoundingClientRect();
      const prev = document.querySelector('#s-cal [data-act=\"calPrev\"]');
      const next = document.querySelector('#s-cal [data-act=\"calNext\"]');
      const srch = document.querySelector('#s-cal [data-act=\"calSearch\"]');
      const sr = srch.getBoundingClientRect();
      return {txt: mo.textContent.trim(), monLeft: mr.left, searchRight: window.innerWidth - sr.right,
              hasPrev: !!prev, hasNext: !!next,
              searchIcon: !!srch.querySelector('svg'), fs: getComputedStyle(mo).fontSize};
    })()""")
    check("월 표시가 왼쪽에", head["txt"] == "11월" and abs(head["monLeft"] - 20) <= 2, head)
    check("월 글씨 25px (제목과 같은 크기)", head["fs"] == "25px", head["fs"])
    check("월 옆에 이전·다음 화살표", head["hasPrev"] and head["hasNext"], head)
    check("오른쪽 끝에 검색 아이콘", head["searchIcon"] and abs(head["searchRight"] - 20) <= 2, head["searchRight"])

    # 하단 날짜: 연도 + 월·일 + 요일, 글씨 크게
    dp = page.evaluate("""(() => { const d = document.querySelector('#s-cal .daypanel-hd .d'); const cs = getComputedStyle(d);
      return {txt: d.innerText.replace(/\\n/g, ' '), fs: cs.fontSize, fw: cs.fontWeight}; })()""")
    check("하단 날짜는 연도·월·일만 (v20: 요일 없음)", "2026년" in dp["txt"] and "월" in dp["txt"] and "일" in dp["txt"] and "(" not in dp["txt"], dp["txt"])
    check("하단 날짜 글씨 확대(18.5px·800)", dp["fs"] == "18.5px" and dp["fw"] == "800", dp)

    # 공휴일 빨강 (10월로 이동 — 개천절·한글날)
    page.locator('#s-cal [data-act="calPrev"]').click()
    page.wait_for_timeout(450)
    hol = page.evaluate("""(() => { const d = document.querySelector('#s-cal .day.hol .dnum'); const n = document.querySelector('#s-cal .day.hol .dhol');
      return {month: document.querySelector('#s-cal .cal-month').textContent.trim(),
              num: d ? getComputedStyle(d).color : null, name: n ? getComputedStyle(n).color : null,
              count: document.querySelectorAll('#s-cal .day.hol').length}; })()""")
    check("공휴일 숫자 빨강", hol["num"] == "rgb(240, 20, 20)" and hol["count"] >= 1, hol)
    check("공휴일 이름도 빨강", hol["name"] == "rgb(240, 20, 20)", hol)
    page.screenshot(path=os.path.join(SHOT, "calendar-holiday-v19.png"))

    # 일정 검색 → 결과 누르면 그 달·날짜로
    page.locator('#s-cal [data-act="calSearch"]').click()
    page.wait_for_timeout(450)
    check("검색 시트 열림", "일정 검색" in page.locator("#sheet").inner_text())
    page.fill("#calSearchIn", "성수")
    page.wait_for_timeout(450)
    nres = page.locator("#sheet .sres").count()
    check("검색 결과 있음", nres >= 1, page.locator("#sheet").inner_text()[:120])
    rt = page.locator("#sheet .sres").first.inner_text()
    check("결과에 제목·날짜·종류", "성수" in rt and "2026" in rt, rt)
    page.locator("#sheet .sres").first.click()
    page.wait_for_timeout(700)
    jumped = page.evaluate("""(() => ({month: document.querySelector('#s-cal .cal-month').textContent.trim(),
      sel: document.querySelector('#s-cal .day.sel') ? document.querySelector('#s-cal .day.sel .dnum').textContent : null,
      dp: document.querySelector('#s-cal .daypanel-hd .d') ? document.querySelector('#s-cal .daypanel-hd .d').innerText.replace(/\\n/g,' ') : null,
      open: document.getElementById('sheetWrap').classList.contains('open')}))()""")
    check("결과 누르면 그 달로 이동", jumped["month"] == "11월", jumped)
    # 예시 일정은 «오늘»에 있으므로 날짜가 바뀌어도 맞게 (실행한 날 기준)
    _td = str(int(time.strftime("%d")))
    check("그 날짜가 선택됨", jumped["sel"] == _td, jumped)
    check("하단 날짜도 그 날", jumped["dp"] and ("%d월 %d일" % (int(time.strftime("%m")), int(_td))) in jumped["dp"], jumped["dp"])
    check("검색 시트는 닫힘", not jumped["open"])
    page.wait_for_timeout(2400)   # 이동 안내(toast)가 사라진 뒤 깔끔한 화면으로 저장
    page.screenshot(path=os.path.join(SHOT, "calendar-day-v19.png"))
    # 다크 모드에서도 같은 모양(밝은 바탕 + 반전)
    page.evaluate("document.documentElement.setAttribute('data-mode','dark'); 0")
    page.wait_for_timeout(300)
    cdk = page.evaluate("""(() => { const sel = document.querySelector('#s-cal .day.sel');
      const n = sel ? sel.querySelector('.dnum') : null;
      return {bg: sel ? getComputedStyle(sel).backgroundColor : null,
              numBg: n ? getComputedStyle(n).backgroundColor : null,
              num: n ? getComputedStyle(n).color : null}; })()""")
    # v23: 다크에서도 칸은 그대로, 숫자 동그라미만 밝은 바탕 + 반전
    check("다크에서도 선택한 날 = 숫자 동그라미만 반전",
          cdk["bg"] in ("rgba(0, 0, 0, 0)", "transparent")
          and cdk["numBg"] == "rgb(245, 245, 245)" and cdk["num"] == "rgb(17, 17, 17)", cdk)
    page.screenshot(path=os.path.join(SHOT, "calendar-day-v19-dark.png"))
    page.evaluate("document.documentElement.setAttribute('data-mode','light'); 0")
    page.wait_for_timeout(300)

    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
