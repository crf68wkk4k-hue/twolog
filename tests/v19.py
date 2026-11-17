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
        check("화면이 맨 위 · 컬러가 그 아래", caps[0]["top"] < caps[1]["top"], caps)

    # 남아야 하는 것
    check("화면 라이트/다크 유지", page.locator('#sheet .seg-btn[data-mode="light"]').count() == 1
          and page.locator('#sheet .seg-btn[data-mode="dark"]').count() == 1)
    check("팔레트 12색 유지", page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count() == 12,
          page.locator('#sheet .sw-grid[data-sw="homeTitleBg"] .sw').count())
    check("컬러 직접 고르기 유지", page.locator('#sheet .js-color[data-target="homeTitleBg"]').count() == 1
          and page.locator('#sheet .cp-pick span', has_text="컬러").count() == 1)
    check("기본 버튼 유지", page.locator('#sheet .cp-reset[data-target="homeTitleBg"]').count() == 1)
    check("하단 설명 유지", "고른 색은 두 섹션의 제목 줄" in txt)
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
    check("테마 관리에는 「홈 제목 색」 항목 그대로", "홈 제목 색" in mtxt and "다가오는 일정 · " in mtxt, mtxt[:200])
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

    check("콘솔 오류 없음", len(errors) == 0, errors[:5])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
