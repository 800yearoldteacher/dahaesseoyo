import re
from playwright.sync_api import sync_playwright
exec(open("/home/claude/fb/test_fb.py", encoding="utf-8").read().split("with sync_playwright() as p:")[0])

def titles(pg): return [t.inner_text() for t in pg.locator(".col-title").all()]
def col(pg, title): return pg.locator(".col", has=pg.locator(".col-title", has_text=title))
names = ['민준','서연','도윤','서윤','시우','지우','하준','하윤','주원','지유']

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1280, "height": 900}); setup(ctx)
    ctx.add_init_script("window.__DHS_TODAY = '2026-09-22'")
    T = ctx.new_page(); watch(T, "교사")
    T.goto(BASE + "?teacher"); T.wait_for_selector("#login"); T.click("#login"); T.wait_for_selector("#teacher .tabs")
    T.locator("#teacher details.bulk summary").click()
    T.fill("#tv-bulk", "\n".join(f"{i+1} {n}" for i, n in enumerate(names)))
    T.click('#teacher [data-act="bulk-add"]'); T.wait_for_timeout(200)
    T.click('#teacher [data-tab="boards"]')
    for title in ["알림장 쓰기", "우유 급식"]:
        T.fill("#tv-new-title", title); T.press("#tv-new-title", "Enter"); T.wait_for_timeout(200)
    B = ctx.new_page(); B.set_viewport_size({"width": 1180, "height": 820}); watch(B, "태블릿")
    B.goto(BASE); B.wait_for_selector(".wait-code")
    T.click('#teacher [data-tab="settings"]'); T.click('#tv-devices [data-act="approve"]'); B.wait_for_selector("#app .col-title")
    T.click('#teacher [data-tab="boards"]')
    check("준비: 태블릿에 두 판, 각 10명", titles(B) == ["우유 급식", "알림장 쓰기"] and col(B, "우유 급식").locator(".card").count() == 10)

    # 1) 판별 명단: 골라서 → 모두 넣은 채 시작
    T.locator('#tv-detail [data-act="dtab"][data-v="members"]').click()
    T.locator('#tv-detail [data-act="roster-mode"][data-v="pick"]').click(); B.wait_for_timeout(300)
    check("골라서: 처음엔 반 학생 모두", T.locator("#tv-detail .m-chips .chip.d").count() == 10 and col(B, "우유 급식").locator(".card").count() == 10)
    T.click('#tv-detail [data-act="pick-none"]'); B.wait_for_timeout(300)
    check("모두 빼기 → 태블릿에 '이 판에 학생이 없어요'", col(B, "우유 급식").locator(".col-empty").count() == 1 and col(B, "우유 급식").locator(".card").count() == 0)
    check("교사: 학생 없음 안내", "이 판에 학생이 없어요" in T.locator("#tv-detail .dt-meta").inner_text())
    # 붙여넣어 고르기 (성이 붙은 이름, 번호만, 없는 학생)
    T.locator("#tv-detail details.bulk summary").click()
    T.fill("#tv-pick-text", "김민준\n3\n5 시우\n외부학생\n99")
    T.click('#tv-detail [data-act="pick-paste"]'); B.wait_for_timeout(300)
    check("붙여넣기: 3명 고름 (성 붙은 이름·번호만도 찾음)", "3명을 골랐어요" in T.locator("#tv-pick-msg").inner_text() and col(B, "우유 급식").locator(".card").count() == 3)
    miss = T.locator("#tv-pick-miss").inner_text()
    check("찾지 못한 학생과 번호를 알려 줌", "외부학생" in miss and "99번" in miss, miss)
    T.click('#tv-detail [data-act="extra-from-miss"]'); B.wait_for_timeout(300)
    labels = [c.get_attribute("aria-label").split(",")[0] for c in col(B, "우유 급식").locator(".card").all()]
    check("이 판에만 추가 → 반 번호 뒤 번호(11번)로", labels == ["1번 민준", "3번 도윤", "5번 시우", "11번 외부학생"], labels)
    T.fill("#tv-extra-name", "다른반"); T.press("#tv-extra-name", "Enter"); B.wait_for_timeout(300)
    check("이 판에만 있는 학생 직접 추가(12번)", col(B, "우유 급식").locator('.card[aria-label^="12번 다른반"]').count() == 1)
    T.locator('#tv-detail .m-extra [data-act="extra-del"]').nth(1).click(); B.wait_for_timeout(300)
    check("이 판에만 있는 학생 빼기", col(B, "우유 급식").locator(".card").count() == 4)
    check("다른 판(반 전체)은 그대로 10명", col(B, "알림장 쓰기").locator(".card").count() == 10)
    check("반 명단은 그대로 10명", T.locator("#tv-rcount").inner_text() == "10명")
    T.screenshot(path="/home/claude/shots/v4-01-members.png")

    # 2) 매일 반복
    col(B, "우유 급식").locator('.card[aria-label^="1번 "]').click(); T.wait_for_timeout(300)
    check("누른 뒤에도 태블릿 아래 문구 그대로", B.locator(".tray-msg").inner_text().startswith("다 했으면 내 번호를 눌러요"))
    check("판 목록 1/4", "1/4" in T.locator("#tv-blist .bitem.sel .c").inner_text())
    T.locator('#tv-detail [data-act="daily"][data-v="1"]').click(); B.wait_for_timeout(400)
    bid = T.evaluate("Object.keys(window.__MOCK.docs).filter(p => /^boards\\/[^/]+$/.test(p)).find(p => window.__MOCK.docs[p].title === '우유 급식').split('/')[1]")
    day = T.evaluate("(bid) => window.__MOCK.docs['boards/' + bid + '/days/2026-09-22']", bid)
    check("매일 반복 켜기 → 오늘 기록이 날짜별 기록으로 옮겨짐", day is not None and len(day["done"]) == 1)
    check("태블릿: 켠 뒤에도 민준 완료 그대로", "done" in col(B, "우유 급식").locator('.card[aria-label^="1번 "]').get_attribute("class"))
    check("판 목록에 '매일' 표시", T.locator("#tv-blist .bitem.sel .tag").inner_text() == "매일")
    col(B, "우유 급식").locator('.card[aria-label^="3번 "]').click(); T.wait_for_timeout(300)
    day = T.evaluate("(bid) => window.__MOCK.docs['boards/' + bid + '/days/2026-09-22']", bid)
    check("태블릿 누르기 → 오늘 날짜 기록에 저장", len(day["done"]) == 2)
    T.locator('#tv-detail [data-act="dtab"][data-v="now"]').click()
    check("교사: '오늘 2명 다 했어요'", "오늘 2명 다 했어요" in T.locator("#tv-detail .dt-meta").inner_text(), T.locator("#tv-detail .dt-meta").inner_text())

    # 3) 기록 달력: 한눈에 보기
    T.locator('#tv-detail [data-act="dtab"][data-v="history"]').click(); T.wait_for_timeout(300)
    check("기록 달력: 학생 4줄", T.locator("#tv-hist tbody tr").count() == 4)
    check("오늘(22일) 칸 2개 칠해짐", T.locator('#tv-hist .hc.on[data-day="2026-09-22"]').count() == 2)
    check("내일 칸은 누를 수 없음", T.locator('#tv-hist .hc[data-day="2026-09-23"]').first.is_disabled())
    T.screenshot(path="/home/claude/shots/v4-02-history-table.png")

    # 4) 다음 날
    for pg in (T, B): pg.evaluate("window.__DHS_TODAY = '2026-09-23'; window.__dhs.checkDay()")
    B.wait_for_timeout(400); T.wait_for_timeout(300)
    check("다음 날 → 태블릿 매일 판이 비워짐", col(B, "우유 급식").locator(".card.done").count() == 0)
    check("다음 날에도 다른 판은 그대로", col(B, "알림장 쓰기").locator(".card").count() == 10)
    check("기록 달력: 22일 기록은 남아 있음", T.locator('#tv-hist .hc.on[data-day="2026-09-22"]').count() == 2)
    T.locator('#tv-hist .hc[data-day="2026-09-22"]').nth(2).click(); T.wait_for_timeout(300)
    check("지난 날 칸을 눌러 기록 고치기", T.locator('#tv-hist .hc.on[data-day="2026-09-22"]').count() == 3)
    col(B, "우유 급식").locator('.card[aria-label^="5번 "]').click(); T.wait_for_timeout(400)
    check("오늘(23일) 누른 기록도 달력에 바로", T.locator('#tv-hist .hc.on[data-day="2026-09-23"]').count() == 1)
    check("판을 연 날 2일", "2일" in T.locator("#tv-hist .hist-note").inner_text())
    # 학생별 달력
    T.click('#tv-hist [data-act="hist-view"][data-v="cal"]'); T.wait_for_timeout(200)
    T.locator('#tv-hist [data-act="hist-student"]', has_text="민준").click(); T.wait_for_timeout(200)
    check("학생별 달력: 민준 22일 칠함, 오늘(23일)은 아직 '안 함' 아님", T.locator('#tv-hist .cd.on').count() == 1 and T.locator('#tv-hist .cd.miss').count() == 0 and T.locator('#tv-hist .cd.today').count() == 1)
    check("학생별 달력 요약", "판을 연 2일 중 1일" in T.locator("#tv-hist .cal-sum").inner_text(), T.locator("#tv-hist .cal-sum").inner_text())
    T.screenshot(path="/home/claude/shots/v4-03-history-cal.png")
    for pg in (T, B): pg.evaluate("window.__DHS_TODAY = '2026-09-24'; window.__dhs.checkDay()")
    T.wait_for_timeout(300); T.click('#tv-hist [data-act="hist-view"][data-v="cal"]'); T.wait_for_timeout(200)
    check("하루 지나면 23일이 '안 함'으로", T.locator('#tv-hist .cd.miss').count() == 1 and T.locator('#tv-hist .cd.miss').get_attribute("data-day") == "2026-09-23")
    T.screenshot(path="/home/claude/shots/v4-03-history-cal.png")
    T.click('#tv-hist [data-act="hist-prev"]'); T.wait_for_timeout(300)
    check("지난달로 넘기기", "8월" in T.locator("#tv-hist .hist-head strong").inner_text() and T.locator('#tv-hist .cd.on').count() == 0)
    T.click('#tv-hist [data-act="hist-next"]'); T.wait_for_timeout(300)

    # 5) 규칙(연습용): 태블릿은 날짜 기록을 한 명씩만
    FS = "https://www.gstatic.com/firebasejs/12.19.0/firebase-firestore.js"
    r2 = B.evaluate("(a) => import(a[0]).then(m => m.setDoc(m.doc({}, 'boards', a[1], 'days', '2026-09-24'), {done: {x1: 1, x2: 2}}).then(() => 'ok', e => e.code))", [FS, bid])
    r1 = B.evaluate("(a) => import(a[0]).then(m => m.setDoc(m.doc({}, 'boards', a[1], 'days', '2026-09-25'), {done: {x1: 1}}).then(() => 'ok', e => e.code))", [FS, bid])
    check("규칙: 태블릿이 두 명을 한꺼번에 쓰면 거절, 한 명은 허용", r2 == "permission-denied" and r1 == "ok", (r2, r1))

    # 6) 매일 반복 끄기
    T.locator('#tv-detail [data-act="daily"][data-v="0"]').click(); T.click('#dlg [data-dlg="ok"]'); B.wait_for_timeout(400)
    check("끄기 → 날짜별 기록 탭이 사라지고 오늘(24일) 기록이 판으로", T.locator('#tv-detail [data-v="history"]').count() == 0 and col(B, "우유 급식").locator(".card.done").count() == 0)
    check("끄면 '매일' 표시 사라짐", T.locator("#tv-blist .bitem.sel .tag").count() == 0)

    # 7) 명단 새로 바꾸기: 이름이 같으면 판 명단이 이어짐
    T.click('#teacher [data-tab="roster"]')
    T.fill("#tv-bulk", "\n".join(f"{i+1} {n}" for i, n in enumerate(reversed(names))))
    T.click('#teacher [data-act="bulk-replace"]'); T.click('#dlg [data-dlg="ok"]'); B.wait_for_timeout(400)
    labels = [c.get_attribute("aria-label").split(",")[0] for c in col(B, "우유 급식").locator(".card").all()]
    check("명단을 새로 붙여넣어도 이름이 같으면 판 명단 유지", sorted(l.split(" ")[1] for l in labels) == sorted(["민준", "도윤", "시우", "외부학생"]), labels)

    # 8) 판 지우기 → 날짜별 기록도 지움
    T.click('#teacher [data-tab="boards"]')
    T.locator("#tv-blist .bsel", has_text="우유 급식").click()
    T.click('#tv-detail [data-act="archive"]'); T.wait_for_timeout(200)
    T.locator("#teacher details.archive summary").click()
    T.locator('#tv-alist .arow', has_text="우유 급식").locator('[data-act="delete"]').click(); T.click('#dlg [data-dlg="ok"]'); T.wait_for_timeout(500)
    left = T.evaluate("(bid) => Object.keys(window.__MOCK.docs).filter(p => p.startsWith('boards/' + bid)).length", bid)
    check("판을 지우면 날짜별 기록도 함께 지워짐", left == 0, left)
    B.screenshot(path="/home/claude/shots/v4-04-tablet.png")
    b.close()
print("\n".join(res)); print("통과 %d / 실패 %d" % (sum(r.startswith("OK") for r in res), sum(r.startswith("FAIL") for r in res)))
print("--- errors ---"); print("\n".join(errs) if errs else "(none)")
