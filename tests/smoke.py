"""투로그 스모크 테스트 — 로컬 모드에서 5개 탭·사진 업로드·저장·PWA 를 확인합니다.

    pip install playwright && playwright install chromium
    python3 tests/smoke.py

실패가 하나라도 있으면 exit code 1.
"""
import base64, functools, http.server, json, os, re, socketserver, sys, tempfile, threading, time

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 테스트용 작은 JPEG (320x240)
JPEG_B64 = (
    "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAoHBwgHBgoICAgLCgoLDhgQDg0NDh0VFhEYIx8lJCIfIiEmKzcvJik0KSEiMEExNDk7Pj4+JS5ESU"
    "M8SDc9Pjv/2wBDAQoLCw4NDhwQEBw7KCIoOzs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozv/wAARCADw"
    "AUADASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhBy"
    "JxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKT"
    "lJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAA"
    "AAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRom"
    "JygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExc"
    "bHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDp6SiiuQ7QpKKKCQopKKYgopKKZIUUlFMkKKKSmIKKKSmSLSUU"
    "lAhaSikpki0lFFMkKSiimSFFJRTEFFJRTJCiikpiCiikpkhRRSUyRaSikoELSUUlMkWkoopkhSUUUxGhmiikrgPoAzRRSUyQoopKBC0lFJTJFp"
    "M0UUyQpM0UUxBRmkopkhRSUUxBRRSUEhmiikqiQzRRSUCFzSUUlMkWkopKZItJRRTEFJmiimSFGaSimSFFJRQIKKKSmSFFFJTJDNFFJTEaNJRR"
    "XAfQBRSUUyQopKKBBRRSUyQopKKYgoopKZItJRSUyRaSiimSFJRRTEFFJRTJCikopiCikooJCiikpkhRRSUxC0lFJTJFpKKSmSLSUUUxBSUUUy"
    "QopKKCQopKKYjQoopM1wH0AtJRSZpki0lFGaYgpKKKZIUlFFBIUUmaKYgopM0UyQopKKYgoopKZIUUUmaZItJRSZpiFpKKM0yQpKKKCQpKKKYg"
    "opM0UyQopM0UyQoozSUxBRRSUyRaSikpki0lFJmgRo0UlFcB9AFFJRTJCiikpiCiikpkhRRSUyRaSiigQUlFFMkKSiimIKSiimSFFJRTJCikop"
    "iCiikpkhRRSUyRaSikoELSUUUyQpKKKZIUlFFMQUlFFMkKKSimSFFFJQI0KKKSuA+gFpKKKZIUlFFMQUUlFMkKKSimIKKSimSFFFJQSFFFJTEL"
    "SUUlMkKKKSmSLSUUUxBSUUUyQopKKZIUUlFMQUUlFMkKKKSgkKKKSmIWkopKZItJRSUyRaSiimI0KKSiuA+gDNFFJQIM0UUlMkKKKSmSLSZopK"
    "YhaTNFFMkKTNFFMkKM0lFMQUUlFBIUUlFMkM0UUlMQZoopKZIUUUlMkWkopKYhaTNFFMkKTNFFMkKM0lFAgopKKZIUUUlMkKKKSmI0aSikrgPo"
    "BaSiimIKKSigkKKSimSFFFJTEFFJRTJCiikpki0lFJTELSUUUyQpKKKCQopKKYgopKKZIUUlFMkKKKSmIKKSimSFFFJTJFpKKSmIWkoooJCkoo"
    "pkhRSUUxGhRRSZrgPoAoopM0xC0lFJmmSLSUUlBItJRRTEFJRRTJCikzRTJCikzRTEFFJRTJCiikzTJCiikzQIWkopM0yRaSijNMkKSiimIKSi"
    "imSFFJmimSFFJmimIKKSimSFFFJQSFFFJmmI0aSiiuA+gCkoopiCikopkhRRSUyQoopKBBRRSUyRaSikpki0lFFMQUlFFMkKSiimSFFJRTEFFJ"
    "RQSFFFJTJCiikpiCiikpki0lFFMkKSiimIKSiimSFJRRTJCikooEaNJRSVwH0AUUUlMQtJRRTJCkoopkhSUUUxBSUUUyQopKKCQoopKYgoopKZ"
    "ItJRSUyQoopKYhaSiimSFJRRQSFFJRTEFFJRTJCikopkhRRSUxBRRSUyRaSikpki0lFJTEaNFJRXnn0AUUlFMQZoopKZIZoopKZIUUUlMQtJmi"
    "kpki0maKSmSLSZoooEFJRRTJCikopkhRSUUxBmiikpkhmiikpkhRRSUCFpM0UlMkWkzRRTJCkzRRTEFGaSimSFFJRTEFFJRTJNGkopK4D6AWko"
    "pKYhaSiigkKKSimSFFJRTEFFFJTJCikopkhRRSUCFpKKSmSLSUUlMkWkopKYhaSiimSFFJRTJCikopiCiikpkhRSUUCCiikpki0lFJTJFpKKKY"
    "gpKKKZJoUUlFcB9AFFFJmmIKKKTNMkWkopKCRaSikpiFpKKKZIUlFFMkKKTNFMQUUmaKZIUUlFBIUUUmaYgoopM0yRaSikzTELSUUlMkWkoopk"
    "hSUUUxBRSZooJCikzRTJCikopiCiikpkmjSUUVwH0AUlFFMQUlFFMkKKSimSFFJRQIKKKSmSFFFJTJFpKKSmIWkoopkhSUUUyQpKKKBBRSUUyQ"
    "opKKYgoopKZIUUUlMkKKKSmIWkoopkhSUUUEhSUUUxBSUUUyT/2Q=="
)

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

# 이 환경은 시스템 라이브러리(libatk 등)가 없어 LD_LIBRARY_PATH 로 넘겨 줍니다.
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

jpg_path = os.path.join(tempfile.mkdtemp(), "test-photo.jpg")
with open(jpg_path, "wb") as f:
    f.write(base64.b64decode(JPEG_B64))

with sync_playwright() as p:
    browser = launch(p)
    ctx = browser.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

    page.goto("http://127.0.0.1:%d/" % PORT, wait_until="networkidle")
    page.wait_for_timeout(500)

    check("5개 탭", page.locator("#tabbar .tab").count() == 5, page.locator("#tabbar .tab").count())
    check("홈 브랜드", page.locator("#s-home .brand b").inner_text().strip() == "투로그")

    page.locator("#tabbar .tab").nth(1).click()
    page.wait_for_timeout(250)
    check("캘린더 날짜", page.locator("#s-cal .day").count() >= 28, page.locator("#s-cal .day").count())
    page.locator('#s-cal [data-act="addEvent"]').first.click()
    page.wait_for_timeout(200)
    page.fill('#sheetForm input[name="title"]', "스모크 일정")
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(300)
    check("일정 추가", page.locator("#s-cal .ev .t", has_text="스모크 일정").count() == 1)

    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(350)
    check("노트 카드", page.locator("#s-diary .ngrid .ncard").count() >= 1, page.locator("#s-diary .ncard").count())
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(350)
    page.fill('#sheet #listAddForm input[name="text"]', "스모크 할일")
    page.click("#sheet .todo-add-btn")
    page.wait_for_timeout(350)
    check("할 일 추가", page.locator("#sheet .card-items .trow .t", has_text="스모크 할일").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(250)

    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(250)
    page.set_input_files("#photoInput", [jpg_path])
    page.wait_for_timeout(400)
    check("사진 추가 시트", page.locator("#upBar").count() == 1)
    page.click('#sheetForm button[type="submit"]')
    page.wait_for_timeout(1500)
    check("사진 타일", page.locator("#s-photo .pola").count() == 1, page.locator("#s-photo .pola").count())
    src = page.locator("#s-photo .pola-pic img").first.get_attribute("src") if page.locator("#s-photo .pola-pic img").count() else ""
    check("사진 파일 렌더", str(src).startswith("blob:"), src)

    page.locator("#s-photo .pola").first.click()
    page.wait_for_timeout(250)
    check("사진 상세", page.locator(".pview").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    page.locator("#tabbar .tab").nth(4).click()
    page.wait_for_timeout(250)
    page.locator('#s-set [data-act="linkSheet"]').first.click()
    page.wait_for_timeout(300)
    check("설정 초대 코드", len(page.locator("#sheet .set-code").inner_text().replace(" ", "")) == 6)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    man = page.evaluate("fetch('manifest.json').then(r => r.json())")
    check("manifest standalone", man.get("display") == "standalone", man.get("display"))
    check("아이콘 192", page.evaluate("fetch('icons/icon-192.png').then(r => r.status)") == 200)
    check("애플 터치 아이콘", page.evaluate("fetch('icons/apple-touch-icon.png').then(r => r.status)") == 200)
    sw = page.evaluate("navigator.serviceWorker.ready.then(r => r.active ? r.active.scriptURL : 'none')")
    check("서비스 워커", str(sw).endswith("/sw.js"), sw)

    page.reload(wait_until="networkidle")
    page.wait_for_timeout(700)
    page.locator("#tabbar .tab").nth(3).click()
    page.wait_for_timeout(400)
    check("새로 열어도 사진 유지", page.locator("#s-photo .pola").count() == 1)
    page.locator("#tabbar .tab").nth(2).click()
    page.wait_for_timeout(400)
    page.locator("#s-diary .ncard").first.click()
    page.wait_for_timeout(350)
    check("새로 열어도 할 일 유지", page.locator("#sheet .card-items .trow .t", has_text="스모크 할일").count() == 1)
    page.keyboard.press("Escape")
    page.wait_for_timeout(200)

    check("콘솔 오류 없음", len(errors) == 0, errors[:3])
    browser.close()

print()
print("실패:", fails if fails else "없음")
sys.exit(1 if fails else 0)
