from playwright.sync_api import sync_playwright
exec(open("/home/claude/fb/test_fb.py", encoding="utf-8").read().split("with sync_playwright() as p:")[0])  # 공통 준비 코드 재사용

# 판 순서 바꾸기 점검 (2026-09-25-1)
def titles(pg): return [t.inner_text() for t in pg.locator(".col-title").all()]
def tlist(pg): return [t.inner_text() for t in pg.locator("#tv-blist .bsel .t > span:first-child").all()]
def item(pg, title): return pg.locator("#tv-blist .bitem", has=pg.locator(".bsel", has_text=title))
FS = "import('https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js')"

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900}); setup(ctx)
    T = ctx.new_page(); watch(T, "교사")
    T.goto(BASE + "?teacher"); T.wait_for_selector("#login"); T.click("#login"); T.wait_for_selector("#teacher .tabs")
    T.locator("#teacher details.bulk summary").click()
    T.fill("#tv-bulk", "\n".join(f"{i+1} 학생{i+1}" for i in range(6)))
    T.click('#teacher [data-act="bulk-add"]'); T.wait_for_timeout(200)
    T.click('#teacher [data-tab="boards"]')
    # 순서 번호가 없는 예전 판 두 개 (업데이트 전 판 흉내) → 예전처럼 새 판이 앞
    for bid, title, at in [("old1", "예전 판 가", 1000), ("old2", "예전 판 나", 2000)]:
        T.evaluate("([bid, title, at]) => " + FS + ".then(m => m.setDoc(m.doc({}, 'boards', bid), {title, createdAt: at, archived: false, shown: true, daily: false, roster: null, done: {}}))", [bid, title, at])
    T.wait_for_timeout(300)
    check("예전 판(순서 번호 없음)은 새 판이 앞", tlist(T) == ["예전 판 나", "예전 판 가"], tlist(T))
    T.fill("#tv-new-title", "새 판 다")
    T.press("#tv-new-title", "Enter"); T.wait_for_timeout(250)
    check("새로 만든 판은 맨 뒤", tlist(T) == ["예전 판 나", "예전 판 가", "새 판 다"], tlist(T))
    if not item(T, "새 판 다").locator(".showbtn.on").count():
        item(T, "새 판 다").locator('[data-act="show"]').click(); T.wait_for_timeout(200)
    check("첫 판 ▲, 끝 판 ▼는 누를 수 없음",
          item(T, "예전 판 나").locator('[data-act="up"]').is_disabled() and item(T, "새 판 다").locator('[data-act="down"]').is_disabled()
          and not item(T, "예전 판 가").locator('[data-act="up"]').is_disabled())
    # 태블릿
    B = ctx.new_page(); B.set_viewport_size({"width": 1180, "height": 820}); watch(B, "태블릿")
    B.goto(BASE); B.wait_for_selector(".wait-code")
    T.click('#teacher [data-tab="settings"]'); T.click('#tv-devices [data-act="approve"]'); B.wait_for_selector("#app .col-title")
    T.click('#teacher [data-tab="boards"]'); T.wait_for_timeout(150)
    check("태블릿도 같은 순서", titles(B) == ["예전 판 나", "예전 판 가", "새 판 다"], titles(B))
    # ▼ / ▲
    item(T, "예전 판 나").locator('[data-act="down"]').click(); B.wait_for_timeout(300)
    check("▼ 누르기 → 한 칸 뒤로", tlist(T) == ["예전 판 가", "예전 판 나", "새 판 다"], tlist(T))
    check("▼ → 태블릿에 바로 반영", titles(B) == ["예전 판 가", "예전 판 나", "새 판 다"], titles(B))
    check("▼ 누른 뒤에도 그 버튼에 초점", T.evaluate("document.activeElement && document.activeElement.dataset.act") == "down")
    item(T, "새 판 다").locator('[data-act="up"]').click(); B.wait_for_timeout(300)
    check("▲ 누르기 → 한 칸 앞으로", tlist(T) == ["예전 판 가", "새 판 다", "예전 판 나"], tlist(T))
    check("▲ → 태블릿에 바로 반영", titles(B) == ["예전 판 가", "새 판 다", "예전 판 나"], titles(B))
    orders = T.evaluate("Object.entries(window.__MOCK.docs).filter(([p]) => /^boards\\/[^/]+$/.test(p)).map(([p, d]) => d.order).sort()")
    check("순서 번호가 0, 1, 2로 저장됨", orders == [0, 1, 2], orders)
    # 끌어서 옮기기: '예전 판 나'를 맨 위 판의 윗부분에 놓기
    item(T, "예전 판 나").locator(".grip").drag_to(item(T, "예전 판 가"), target_position={"x": 40, "y": 4}); B.wait_for_timeout(300)
    check("끌어서 맨 앞에 놓기", tlist(T) == ["예전 판 나", "예전 판 가", "새 판 다"], tlist(T))
    item(T, "예전 판 나").locator(".grip").drag_to(item(T, "새 판 다"), target_position={"x": 40, "y": 60}); B.wait_for_timeout(300)
    check("끌어서 맨 뒤에 놓기", tlist(T) == ["예전 판 가", "새 판 다", "예전 판 나"], tlist(T))
    check("끌어서 옮기기 → 태블릿에 반영", titles(B) == ["예전 판 가", "새 판 다", "예전 판 나"], titles(B))
    check("끌기 표시가 남지 않음", T.locator("#tv-blist .drop-before, #tv-blist .drop-after, #tv-blist .dragging").count() == 0)
    # 순서만 바꿀 때는 태블릿 쪽이 넘어가지 않음 (세로 화면 1판씩)
    B.set_viewport_size({"width": 800, "height": 1180}); B.wait_for_timeout(300)
    first = titles(B)
    item(T, "새 판 다").locator('[data-act="down"]').click(); B.wait_for_timeout(300)
    check("순서를 바꿔도 태블릿은 보던 쪽(첫 쪽) 그대로", first == ["예전 판 가"] and titles(B) == ["예전 판 가"], (first, titles(B)))
    B.set_viewport_size({"width": 1180, "height": 820}); B.wait_for_timeout(200)
    # 보관 → 되살리기는 맨 뒤로
    item(T, "예전 판 가").locator(".bsel").click(); T.click('#tv-detail [data-act="archive"]'); T.wait_for_timeout(250)
    T.locator("#teacher details.archive summary").click()
    T.click('#tv-alist [data-act="restore"]'); T.wait_for_timeout(250)
    check("되살린 판은 맨 뒤", tlist(T) == ["예전 판 나", "새 판 다", "예전 판 가"], tlist(T))
    # 규칙: 태블릿은 순서를 못 바꿈
    r = B.evaluate("() => " + FS + ".then(m => m.updateDoc(m.doc({}, 'boards', 'old1'), {order: -5}).then(() => 'ok', e => e.code))")
    check("규칙: 태블릿은 판 순서를 못 바꿈", r == "permission-denied", r)
    # 판이 하나뿐이면 끌기 손잡이 없음
    for t in ["예전 판 나", "새 판 다"]:
        item(T, t).locator(".bsel").click(); T.click('#tv-detail [data-act="archive"]'); T.wait_for_timeout(200)
    check("판이 하나면 끌기 손잡이 없음, ▲▼ 모두 막힘",
          T.locator("#tv-blist .grip").count() == 0 and T.locator('#tv-blist [data-act="up"]').is_disabled() and T.locator('#tv-blist [data-act="down"]').is_disabled())
    T.screenshot(path="/home/claude/shots/fb5-order.png")
    b.close()

print("\n".join(res))
print(f"통과 {sum(1 for r in res if r.startswith('OK'))} / 실패 {sum(1 for r in res if r.startswith('FAIL'))}")
print("--- errors ---"); print("\n".join(errs) or "(none)")
