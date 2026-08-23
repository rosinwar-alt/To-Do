import sys
from playwright.sync_api import sync_playwright

errors = []

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 390, "height": 844})
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.on("pageerror", lambda exc: errors.append(str(exc)))

    page.goto("http://localhost:8765/index.html", wait_until="networkidle")
    page.wait_for_timeout(800)

    print("== Initial load errors ==", errors)

    # Check nav: routines page exists and switches
    page.click("button.bottom-nav >> text=กิจวัตร") if page.query_selector("button.bottom-nav") else None
    routines_btn = page.query_selector('.bottom-nav button[data-page="routines"]')
    assert routines_btn, "routines bottom nav button missing"
    routines_btn.click()
    page.wait_for_timeout(300)
    visible = page.is_visible("#page-routines")
    print("routines page visible:", visible)
    assert visible

    # add a routine (quick chip)
    page.fill("#tplText", "ทดสอบกิจวัตร")
    page.fill("#tplMoney", "-20")
    page.click("#addTplBtn")
    page.wait_for_timeout(300)
    tpl_items = page.query_selector_all("#tplList .tpl-item")
    print("tpl items after add:", len(tpl_items))
    assert len(tpl_items) >= 1

    # add a second routine to test drag reorder
    page.fill("#tplText", "กิจวัตรที่สอง")
    page.click("#addTplBtn")
    page.wait_for_timeout(300)
    tpl_items = page.query_selector_all("#tplList .tpl-item")
    print("tpl items now:", len(tpl_items))
    ids_before = [el.get_attribute("data-id") for el in tpl_items]
    print("order before:", ids_before)

    # drag reorder: drag handle of second item above first
    handles = page.query_selector_all(".tpl-drag-handle")
    box2 = handles[1].bounding_box()
    box1 = handles[0].bounding_box()
    page.mouse.move(box2["x"]+4, box2["y"]+8)
    page.mouse.down()
    page.wait_for_timeout(50)
    for i in range(1, 9):
        frac = i/8
        x = box2["x"]+4 + (box1["x"]+4 - (box2["x"]+4)) * frac
        y = box2["y"]+8 + (box1["y"]+4 - (box2["y"]+8)) * frac
        page.mouse.move(x, y)
        page.wait_for_timeout(20)
    page.wait_for_timeout(50)
    page.mouse.up()
    page.wait_for_timeout(300)
    tpl_items_after = page.query_selector_all("#tplList .tpl-item")
    ids_after = [el.get_attribute("data-id") for el in tpl_items_after]
    print("order after drag:", ids_after)

    # go to today page
    today_btn = page.query_selector('.bottom-nav button[data-page="today"]')
    today_btn.click()
    page.wait_for_timeout(300)

    # quick summary widget present
    qs = page.query_selector("#quickSummary")
    print("quick summary html snippet:", qs.inner_html()[:200])

    # add a task with money
    page.fill("#taskText", "ทดสอบงาน")
    page.fill("#taskMoney", "-50")
    page.click("#addTaskBtn")
    page.wait_for_timeout(300)

    task_rows = page.query_selector_all("#taskList .task-swipe-wrap")
    print("task rows:", len(task_rows))
    assert len(task_rows) >= 1

    # test search filter
    page.fill("#taskSearch", "ไม่มีทางเจอ")
    page.wait_for_timeout(200)
    empty = page.query_selector("#taskList .empty")
    print("search empty state shown:", empty is not None)
    page.fill("#taskSearch", "")
    page.wait_for_timeout(200)

    # test swipe right (toggle done) via mouse drag simulation on first task row
    row = page.query_selector("#taskList .task")
    row.scroll_into_view_if_needed()
    box = row.bounding_box()
    page.mouse.move(box["x"]+20, box["y"]+box["height"]/2)
    page.mouse.down()
    page.mouse.move(box["x"]+120, box["y"]+box["height"]/2, steps=8)
    page.mouse.up()
    page.wait_for_timeout(300)
    row = page.query_selector("#taskList .task")  # re-query: full re-render happened
    done_class = row.get_attribute("class")
    print("task class after swipe-right:", done_class)

    # test swipe left (reveal delete) on the row again
    row2 = page.query_selector("#taskList .task")
    row2.scroll_into_view_if_needed()
    box2b = row2.bounding_box()
    page.mouse.move(box2b["x"]+box2b["width"]-20, box2b["y"]+box2b["height"]/2)
    page.mouse.down()
    page.mouse.move(box2b["x"]-100, box2b["y"]+box2b["height"]/2, steps=8)
    page.mouse.up()
    page.wait_for_timeout(300)
    row2 = page.query_selector("#taskList .task")
    swiped_class = row2.get_attribute("class")
    print("task class after swipe-left:", swiped_class)
    del_btn = page.query_selector(".swipe-del-btn")
    print("delete button exists:", del_btn is not None)

    # settings: savings goal
    settings_btn = page.query_selector('.bottom-nav button[data-page="settings"]')
    settings_btn.click()
    page.wait_for_timeout(300)
    page.fill("#goalName", "เก็บเงินเที่ยว")
    page.fill("#goalTarget", "5000")
    page.click("#saveGoalBtn")
    page.wait_for_timeout(300)
    status = page.inner_text("#goalSettingsStatus")
    print("goal status:", status)

    # summary page goal card
    summary_btn = page.query_selector('.bottom-nav button[data-page="summary"]')
    summary_btn.click()
    page.wait_for_timeout(300)
    goal_visible = page.is_visible("#goalCardWrap")
    print("goal card visible on summary:", goal_visible)

    print("== Final console errors ==", errors)
    browser.close()

if errors:
    print("ERRORS FOUND")
    sys.exit(1)
else:
    print("NO CONSOLE ERRORS")
