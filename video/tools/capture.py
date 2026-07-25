"""Record the demo footage: one continuous desktop session (with per-beat
timestamps for slicing in Remotion) plus one phone session."""
import asyncio, json, re, time
from playwright.async_api import async_playwright

URL = "http://localhost:8501"
S = "/tmp/claude-0/-home-user-gemma-without-borders/0a6d217e-b4d0-50ca-bdd7-1a09f53476d2/scratchpad"
CAPS = f"{S}/caps"
BANK = json.load(open("/home/user/gemma-without-borders/data/questions.json"))


async def find_frame(page, probe):
    for f in page.frames:
        try:
            if await f.evaluate(probe):
                return f
        except Exception:
            pass
    return None


class Beats:
    def __init__(self):
        self.t0 = time.monotonic()
        self.rows = []

    def start(self, name):
        self.rows.append({"name": name, "t0": round(time.monotonic() - self.t0, 2)})
        print(f"[{self.rows[-1]['t0']:7.2f}] {name}")

    def end(self):
        self.rows[-1]["t1"] = round(time.monotonic() - self.t0, 2)


async def desktop(p):
    browser = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium",
                                      args=["--enable-unsafe-swiftshader"])
    ctx = await browser.new_context(viewport={"width": 1920, "height": 1080},
                                    record_video_dir=f"{S}/vid",
                                    record_video_size={"width": 1920, "height": 1080})
    page = await ctx.new_page()
    b = Beats()

    b.start("onboard_load")
    await page.goto(URL)
    await page.wait_for_timeout(9000)
    # the probe can miss in headless runs, leaving the provisional "Phone"
    # default - pick Computer explicitly so the citadel records full-bleed
    await page.get_by_text("Computer", exact=True).click()
    await page.wait_for_timeout(3500)
    b.end()

    b.start("name")
    name_box = page.get_by_placeholder("What should the monsters call you?")
    await name_box.click()
    await name_box.type("Maya", delay=140)
    await name_box.press("Enter")
    await page.wait_for_timeout(2500)
    b.end()

    b.start("roster")
    ob = await find_frame(page, "!!document.getElementById('next')")
    for i, pause in enumerate((4500, 3500, 3500, 3000)):
        if ob:
            try:
                await ob.click("#next", timeout=4000)
            except Exception:
                pass
        await page.wait_for_timeout(pause)
    b.end()

    b.start("enter_citadel")
    await page.get_by_role("button", name="Enter the citadel").click()
    await page.wait_for_timeout(10000)
    b.end()

    b.start("citadel_orbit")
    await page.wait_for_timeout(6000)
    b.end()

    b.start("select_equazor")
    hub = await find_frame(page, "!!document.getElementById('canvas-container')")
    fe = await hub.frame_element()
    box = await fe.bounding_box()
    got = False
    for fy in (0.55, 0.62, 0.7, 0.48, 0.78):
        for fx in (0.3, 0.5, 0.7, 0.2, 0.8, 0.4, 0.6):
            await page.mouse.click(box["x"] + box["width"] * fx,
                                   box["y"] + box["height"] * fy)
            await page.wait_for_timeout(900)
            st = await hub.evaluate(
                "({a:document.getElementById('card').classList.contains('active'),"
                " n:document.getElementById('c-name').textContent})")
            if st["a"] and st["n"] == "Equazor":
                got = True
                break
        if got:
            break
    await page.wait_for_timeout(4000)   # dwell on the card
    await page.screenshot(path=f"{CAPS}/d1-card.png")
    b.end()

    b.start("begin_challenge")
    r = await hub.evaluate("""(() => {
      const el = document.getElementById('c-fight').getBoundingClientRect();
      return {x: el.x + el.width/2, y: el.y + el.height/2};
    })()""")
    await page.mouse.click(box["x"] + r["x"], box["y"] + r["y"])
    await page.wait_for_timeout(8000)   # encounter scene + taunt
    await page.screenshot(path=f"{CAPS}/d2-encounter.png")
    b.end()

    b.start("face")
    await page.get_by_role("button", name=re.compile("^FACE ")).click()
    await page.wait_for_timeout(5000)
    b.end()

    b.start("quiz")
    # pick_quiz is deterministic: first five Algebra bank items, in order.
    # Sign-snare option (A) on items 1+2, the correct option elsewhere.
    quiz_qs = [q for q in BANK if q["strand"] == "Algebra"][:5]
    plan_idx = []
    for q in quiz_qs:
        if q["id"] in ("ALG-ITEM-1", "ALG-ITEM-2"):
            lab = next(o["label"] for o in q["options"] if o.get("trick_id") == "ALG-2")
        else:
            lab = next(o["label"] for o in q["options"] if o["is_correct"])
        plan_idx.append("ABCD".index(lab))
    groups = page.locator('[role="radiogroup"]')
    n = await groups.count()
    for i in range(min(n, len(plan_idx))):
        opt = groups.nth(i).locator("label").nth(plan_idx[i])
        await opt.scroll_into_view_if_needed()
        await opt.click()
        await page.wait_for_timeout(1300)
    await page.screenshot(path=f"{CAPS}/d3-quiz.png")
    await page.get_by_role("button", name="Submit").click()
    await page.wait_for_timeout(7000)
    b.end()

    b.start("results_banner")
    await page.wait_for_timeout(2500)
    for _ in range(6):
        await page.mouse.wheel(0, 260)
        await page.wait_for_timeout(650)
    try:
        exp = page.get_by_text("See the worked solution").first
        await exp.scroll_into_view_if_needed()
        await exp.click()
        await page.wait_for_timeout(3000)
    except Exception:
        pass
    await page.screenshot(path=f"{CAPS}/d4-results.png")
    b.end()

    b.start("mastery_enter")
    btn = page.get_by_role("button", name=re.compile("Defeat the monster|Practice until"))
    await btn.scroll_into_view_if_needed()
    await btn.click()
    await page.wait_for_timeout(6000)
    await page.screenshot(path=f"{CAPS}/d5-lesson.png")
    b.end()

    async def read_check():
        txt = await page.locator("[data-testid='stMarkdownContainer'] p strong").all_inner_texts()
        for t in txt:
            m = re.search(r"(\d+)\((\d+)x\s*-\s*(\d+)\)\s*-\s*(\d+)x", t)
            if m:
                a, bq, c, d = map(int, m.groups())
                return {"correct": f"{a*bq-d}x - {a*c}", "snare": f"{a*bq+d}x - {a*c}"}
        return None

    b.start("mastery_shallow")
    chk = await read_check()
    lab = page.locator('[role="radiogroup"] label').filter(has_text=chk["correct"]).first
    await lab.scroll_into_view_if_needed()
    await lab.click()
    await page.wait_for_timeout(900)
    reason = page.get_by_placeholder(re.compile("common denominator"))
    await reason.click()
    await reason.type("I just did it in my head", delay=95)
    await page.wait_for_timeout(700)
    await page.get_by_role("button", name="Check my answer").click()
    await page.wait_for_timeout(6000)
    await page.screenshot(path=f"{CAPS}/d6-shallow.png")
    # let the verdict + reaction sit on screen
    for _ in range(3):
        await page.mouse.wheel(0, 200)
        await page.wait_for_timeout(600)
    b.end()

    b.start("mastery_wrong")
    chk = await read_check()
    if chk:
        lab = page.locator('[role="radiogroup"] label').filter(has_text=chk["snare"]).first
        await lab.scroll_into_view_if_needed()
        await lab.click()
        await page.wait_for_timeout(900)
        reason = page.get_by_placeholder(re.compile("common denominator"))
        await reason.click()
        await reason.type("I added the 6x and the 5x together", delay=85)
        await page.wait_for_timeout(600)
        await page.get_by_role("button", name="Check my answer").click()
        await page.wait_for_timeout(6500)
        for _ in range(3):
            await page.mouse.wheel(0, 220)
            await page.wait_for_timeout(650)
    await page.screenshot(path=f"{CAPS}/d7-switch.png")
    b.end()

    b.start("letters")
    try:
        await page.locator('[class*="st-key-letters_float"] button').first.click(timeout=8000)
    except Exception:
        pass
    await page.wait_for_timeout(5000)
    for _ in range(4):
        await page.mouse.wheel(0, 240)
        await page.wait_for_timeout(700)
    await page.screenshot(path=f"{CAPS}/d8-letters.png")
    b.end()

    await ctx.close()
    path = await page.video.path()
    json.dump({"video": path, "beats": b.rows}, open(f"{S}/desktop-beats.json", "w"), indent=1)
    await browser.close()
    print("desktop video:", path)


async def phone(p):
    browser = await p.chromium.launch(executable_path="/opt/pw-browsers/chromium",
                                      args=["--enable-unsafe-swiftshader"])
    ctx = await browser.new_context(viewport={"width": 430, "height": 932},
                                    has_touch=True, is_mobile=True,
                                    record_video_dir=f"{S}/vid",
                                    record_video_size={"width": 430, "height": 932})
    page = await ctx.new_page()
    b = Beats()

    b.start("p_load")
    await page.goto(URL)
    await page.wait_for_timeout(8000)
    b.end()

    b.start("p_enter")
    skip = page.get_by_text("Skip the introduction")
    await skip.scroll_into_view_if_needed()
    await skip.tap()
    await page.wait_for_timeout(9000)
    b.end()

    b.start("p_tap_monster")
    hub = await find_frame(page, "!!document.getElementById('canvas-container')")
    fe = await hub.frame_element()
    box = await fe.bounding_box()
    for fy in (0.6, 0.7, 0.5, 0.78):
        done = False
        for fx in (0.5, 0.3, 0.7):
            await page.touchscreen.tap(box["x"] + box["width"] * fx,
                                       box["y"] + box["height"] * fy)
            await page.wait_for_timeout(800)
            if await hub.evaluate("document.getElementById('card').classList.contains('active')"):
                done = True
                break
        if done:
            break
    await page.wait_for_timeout(3500)
    await page.screenshot(path=f"{CAPS}/p1-card.png")
    b.end()

    b.start("p_list")
    await page.mouse.wheel(0, 500)
    await page.wait_for_timeout(2500)
    await page.screenshot(path=f"{CAPS}/p2-list.png")
    b.end()

    b.start("p_begin")
    await page.mouse.wheel(0, -500)
    await page.wait_for_timeout(1200)
    r = await hub.evaluate("""(() => {
      const el = document.getElementById('c-fight').getBoundingClientRect();
      return {x: el.x + el.width/2, y: el.y + el.height/2};
    })()""")
    fb = await (await hub.frame_element()).bounding_box()
    await page.touchscreen.tap(fb["x"] + r["x"], fb["y"] + r["y"])
    await page.wait_for_timeout(7000)
    await page.screenshot(path=f"{CAPS}/p3-encounter.png")
    b.end()

    await ctx.close()
    path = await page.video.path()
    json.dump({"video": path, "beats": b.rows}, open(f"{S}/phone-beats.json", "w"), indent=1)
    await browser.close()
    print("phone video:", path)


async def main():
    import os
    os.makedirs(CAPS, exist_ok=True)
    os.makedirs(f"{S}/vid", exist_ok=True)
    async with async_playwright() as p:
        await desktop(p)
        await phone(p)

asyncio.run(main())
