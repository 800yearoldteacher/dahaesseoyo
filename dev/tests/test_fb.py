import re, time
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8000/index.html"
MOCK = {n: open(f"/home/claude/fb/mock/served-{n}.js", encoding="utf-8").read() for n in ["app", "auth", "firestore"]}
res, errs = [], []
def check(n, c, x=""): res.append(("OK  " if c else "FAIL") + " " + n + (" | " + str(x) if x != "" else ""))

def setup(ctx):
    ctx.route("**/fonts.g*.com/**", lambda r: r.abort())
    def serve(body):
        def handler(route, request=None):
            route.fulfill(status=200, headers={"Content-Type": "application/javascript", "Access-Control-Allow-Origin": "*"}, body=body)
        return handler
    for n, body in MOCK.items():
        ctx.route(f"https://www.gstatic.com/firebasejs/12.19.0/firebase-{n}.js", serve(body))

def watch(pg, name):
    pg.on("pageerror", lambda e: errs.append(f"[{name}] pageerror: {e}"))
    pg.on("console", lambda m: errs.append(f"[{name}] console.{m.type}: {m.text}") if m.type == "error" and "ERR_FAILED" not in m.text and "net::" not in m.text else None)

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 860})
    setup(ctx)
    T = ctx.new_page(); watch(T, "교사")
    T.goto(BASE + "?teacher"); T.wait_for_selector("#login", timeout=5000)
    check("교사: 로그인 화면", T.locator("#login").is_visible())
    T.screenshot(path="/home/claude/shots/fb-01-login.png")
    T.click("#login"); T.wait_for_selector("#teacher .tabs", timeout=5000); T.wait_for_timeout(200)
    check("교사: 첫 로그인 후 명단 탭과 안내", T.locator('#teacher [data-tab="roster"]').get_attribute("aria-selected") == "true" and "먼저 학생 명단" in T.locator("#tv-flash").inner_text())
    check("교사: 계정 주소 표시", T.locator("#tv-email").inner_text() == "teacher@test.com")
    # 명단 24명 붙여넣기
    names = ['민준','서연','도윤','서윤','시우','지우','하준','하윤','주원','지유','예준','채원','지호','수아','유준','지아','준우','다은','건우','예린','현우','소율','우진','아린']
    T.locator("#teacher details.bulk summary").click()
    T.fill("#tv-bulk", "\n".join(f"{i+1}\t{n}" for i, n in enumerate(names)))
    T.click('#teacher [data-act="bulk-add"]'); T.wait_for_timeout(250)
    check("교사: 명단 24명 저장", T.locator("#tv-rcount").inner_text() == "24명", T.locator("#tv-rcount").inner_text())
    # 새 판
    T.click('#teacher [data-tab="boards"]')
    T.fill("#tv-new-title", "수학 익힘책 36쪽"); T.press("#tv-new-title", "Enter"); T.wait_for_timeout(250)
    check("교사: 새 판이 목록과 자세히 보기에", T.locator("#tv-blist .bitem").count() == 1 and T.locator("#tv-detail .dt-title").input_value() == "수학 익힘책 36쪽")

    # 태블릿 연결 요청
    B = ctx.new_page(); B.set_viewport_size({"width": 1180, "height": 820}); watch(B, "태블릿")
    B.goto(BASE); B.wait_for_selector(".wait-code", timeout=5000)
    code = B.locator(".wait-code").inner_text()
    check("태블릿: 네 자리 번호로 승인 대기", bool(re.fullmatch(r"\d{4}", code)), code)
    B.screenshot(path="/home/claude/shots/fb-02-tablet-wait.png")
    T.wait_for_timeout(300)
    check("교사: 태블릿 설정 탭에 요청 1건 표시", T.locator("#tv-badge").inner_text() == "1" and T.locator("#tv-badge").is_visible())
    check("교사: 새 요청 알림", code in T.locator("#tv-flash").inner_text(), T.locator("#tv-flash").inner_text())
    T.click('#teacher [data-tab="settings"]')
    check("교사: 같은 번호의 요청", T.locator("#tv-devices .dev.pending .dev-code").inner_text() == code)
    T.screenshot(path="/home/claude/shots/fb-03-teacher-devices.png")
    T.click('#tv-devices [data-act="approve"]')
    B.wait_for_selector("#app .col-title", timeout=5000); B.wait_for_timeout(300)
    check("태블릿: 승인 즉시 판이 열림", B.locator(".col-title").first.inner_text() == "수학 익힘책 36쪽" and B.locator(".card").count() == 24)
    check("교사: 요청 표시 사라짐", T.locator("#tv-badge").is_hidden())

    # 누르기 → 교사 화면
    T.click('#teacher [data-tab="boards"]')
    card3 = B.locator('.card[aria-label^="3번 "]')
    card3.click(); T.wait_for_timeout(300)
    check("태블릿→교사: 완료가 바로 보임", "1명 다 했어요" in T.locator("#tv-detail .dt-meta").inner_text(), T.locator("#tv-detail .dt-meta").inner_text())
    check("교사: 방금 한 학생 강조", T.locator("#tv-detail .chip.d.new").count() == 1)
    check("태블릿: 누른 뒤에도 아래 문구 그대로", B.locator(".tray-msg").inner_text().startswith("다 했으면 내 번호를 눌러요"), B.locator(".tray-msg").inner_text())
    B.wait_for_timeout(1100); card3.click(); T.wait_for_timeout(300)
    check("태블릿→교사: 다시 눌러 취소도 바로 보임", "0명 다 했어요" in T.locator("#tv-detail .dt-meta").inner_text() and T.locator("#tv-detail .chip.undo-new").count() == 1)
    T.locator('#tv-detail .chip[data-act="mark"]', has_text="시우").click(); B.wait_for_timeout(300)
    check("교사→태블릿: 교사가 표시한 완료가 바로 보임", "done" in B.locator('.card[aria-label^="5번 "]').get_attribute("class"))
    B.screenshot(path="/home/claude/shots/fb-04-tablet-board.png")
    T.screenshot(path="/home/claude/shots/fb-05-teacher-board.png")

    # 규칙 확인: 태블릿은 판 제목을 바꿀 수 없음
    bid = B.evaluate("Object.keys(window.__MOCK.docs).find(p => p.startsWith('boards/')).split('/')[1]")
    r1 = B.evaluate("(bid) => import('https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js').then(m => m.updateDoc(m.doc({}, 'boards', bid), {title: '장난'}).then(() => 'ok', e => e.code))", bid)
    check("규칙: 태블릿은 제목을 못 바꿈", r1 == "permission-denied", r1)
    r2 = B.evaluate("() => import('https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js').then(m => m.setDoc(m.doc({}, 'roster', 'main'), {items: []}).then(() => 'ok', e => e.code))")
    check("규칙: 태블릿은 명단을 못 지움", r2 == "permission-denied", r2)

    # 태블릿 새로고침 신호
    T.click('#teacher [data-tab="settings"]')
    with B.expect_navigation(timeout=5000):
        T.click('#teacher [data-act="reload-tablets"]')
    B.wait_for_selector("#app .col-title", timeout=5000)
    check("교사 '태블릿 새로고침' → 태블릿이 다시 불러오고 판이 다시 열림", B.locator(".card").count() == 24)

    # 연결 끊기 → 다시 요청
    T.click('#tv-devices [data-act="remove-device"]'); T.click('#dlg [data-dlg="ok"]')
    B.wait_for_selector(".wait-code", timeout=5000)
    code2 = B.locator(".wait-code").inner_text(); T.wait_for_timeout(300)
    check("연결 끊기 → 태블릿이 대기 화면으로", bool(re.fullmatch(r"\d{4}", code2)))
    check("교사: 다시 온 요청이 보임", T.locator("#tv-devices .dev.pending .dev-code").inner_text() == code2)
    T.click('#tv-devices [data-act="approve"]'); B.wait_for_selector("#app .col-title", timeout=5000)

    # 인터넷 끊김 표시
    ctx.set_offline(True); B.wait_for_timeout(200)
    check("태블릿: 인터넷 끊김 안내", B.locator(".net").is_visible() and "끊겼어요" in B.locator(".net").inner_text())
    check("교사: 연결 끊김 표시", "연결 끊김" in T.locator("#tv-net").inner_text())
    ctx.set_offline(False); B.wait_for_timeout(200)
    check("다시 연결되면 안내 사라짐", B.locator(".net").is_hidden() and T.locator("#tv-net").inner_text() == "실시간 연결됨")

    # 새 버전 감지 → 한가할 때 다시 불러오기
    html = re.sub(r"APP_VERSION = '[^']+'", "APP_VERSION = '2026-09-23-1'", open("/home/claude/serve/index.html", encoding="utf-8").read(), count=1)
    def newer(route, request=None):
        route.fulfill(status=200, headers={"Content-Type": "text/html"}, body=html)
    B.route("**/index.html?v=*", newer)
    found = B.evaluate("window.__dhs.checkVersion()")
    check("태블릿: 새 버전 알아챔", found is True)
    with B.expect_navigation(timeout=5000):
        B.evaluate("window.__dhs.forceIdle()")
    B.wait_for_selector("#app .col-title", timeout=5000)
    check("태블릿: 아무도 안 누를 때 새 버전으로 다시 불러옴", B.locator(".card").count() == 24)

    # 로그아웃
    T.click('#teacher [data-act="logout"]'); T.wait_for_selector("#login", timeout=5000)
    check("교사: 로그아웃 → 로그인 화면", T.locator("#login").is_visible())

    # 선생님이 아닌 계정
    X = ctx.new_page(); watch(X, "다른계정")
    X.goto(BASE + "?teacher"); X.wait_for_selector("#login")
    X.evaluate("window.__MOCK_POPUP_EMAIL = 'kid@test.com'"); X.click("#login")
    X.wait_for_selector("#relogin", timeout=5000)
    check("다른 계정: '선생님 계정이 아니에요'", "선생님 계정이 아니에요" in X.inner_text("body"))
    X.screenshot(path="/home/claude/shots/fb-06-not-teacher.png")

    # 선생님 PC에서 같은 탭으로 태블릿 화면 열기
    P = ctx.new_page(); watch(P, "교사PC판")
    P.goto(BASE + "?teacher"); P.wait_for_selector("#login"); P.click("#login"); P.wait_for_selector("#teacher .tabs")
    P.goto(BASE); P.wait_for_selector("#app .col-title", timeout=5000)
    check("선생님 계정이면 승인 없이 판이 열림", P.locator(".wait-code").count() == 0 and P.locator(".card").count() == 24)
    P.locator(".gear").click()
    for k in "1234": P.locator(f'.keys [data-key="{k}"]').click()
    check("설정 메뉴: 기기 정보와 화면 버전", "선생님 계정으로 열려 있어요" in P.locator(".sheet-box").inner_text() and "2026-09-22-2" in P.locator(".sheet-box").inner_text())

    # 로그인 오류 안내
    Y = ctx.new_page(); watch(Y, "오류")
    Y.goto(BASE + "?teacher"); Y.wait_for_selector("#login")
    Y.evaluate("window.__MOCK_POPUP_ERROR = 'auth/unauthorized-domain'"); Y.click("#login"); Y.wait_for_timeout(200)
    check("로그인 오류를 쉬운 말로", "GitHub 주소 허락하기" in Y.inner_text("body"))
    b.close()

print("\n".join(res))
print("통과 %d / 실패 %d" % (sum(r.startswith("OK") for r in res), sum(r.startswith("FAIL") for r in res)))
print("--- errors ---"); print("\n".join(errs) if errs else "(none)")
