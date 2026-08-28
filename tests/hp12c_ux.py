#!/usr/bin/env python3
"""HP-12C UX: photorealistic face, hotspot clicks, LCD, Casio/TI isolation."""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"
MUL = "\u00d7"


def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page(viewport={"width": 900, "height": 600})
        page.goto(BASE, wait_until="networkidle")

        def ok(name, cond, detail=""):
            results.append({"name": name, "ok": bool(cond), "detail": detail})

        page.evaluate("() => CasioCalc.setModel('hp12c')")
        page.wait_for_timeout(200)

        bg = page.evaluate(
            """() => getComputedStyle(document.querySelector('.face')).backgroundImage"""
        )
        ok("photo face uses HP12C.png", "HP12C.png" in bg, bg[:120])

        pad = page.evaluate(
            """() => getComputedStyle(document.querySelector('.pad')).display"""
        )
        ok("algebra pad hidden on HP model", pad == "none", pad)

        hs = page.locator(".hp-hotspots")
        ok("hotspot layer visible", hs.is_visible())
        n_hs = page.locator(".hp-hotspots .hs").count()
        ok("enough hotspots (>= 30)", n_hs >= 30, f"count={n_hs}")

        def click_hs(key):
            page.locator(f'.hp-hotspots .hs[data-key="{key}"]').first.click(force=True)

        page.evaluate("() => CasioCalc.press('AC')")
        click_hs("2")
        click_hs("=")
        click_hs("3")
        click_hs("+")
        lcd = page.locator("#display").inner_text()
        ok("click 2 ENTER 3 + on photo → 5.00", lcd == "5.00", lcd)

        click_hs("AC")
        click_hs("7")
        click_hs("8")
        lcd = page.locator("#display").inner_text()
        ok("click 78 on photo", lcd in ("78.00", "78"), lcd)

        click_hs("+/-")
        lcd = page.locator("#display").inner_text()
        ok("CHS hotspot → negative", lcd.startswith("-"), lcd)

        click_hs("AC")
        click_hs("4")
        click_hs("=")
        click_hs("2")
        click_hs("÷")
        lcd = page.locator("#display").inner_text()
        ok("click 4 ENTER 2 ÷ → 2.00", lcd == "2.00", lcd)

        for key in ["n", "i", "pv", "pmt", "fv", "f", "g", "sto", "rcl", "xy"]:
            vis = page.locator(f'.hp-hotspots .hs[data-key="{key}"]').count()
            ok(f"hotspot {key} present", vis >= 1, f"count={vis}")

        box = page.locator(".lcd-bezel").bounding_box()
        ok("LCD overlay has size", box and box["width"] > 80 and box["height"] > 20, str(box))

        # f prefix indicator
        click_hs("AC")
        click_hs("f")
        ind = page.locator("#indicators").inner_text()
        ok("f prefix shows on LCD", "f" in ind.lower() or "f" in ind, f"ind={ind!r}")

        # Casio isolation via UX model switch
        page.evaluate("() => CasioCalc.setModel('casio')")
        page.wait_for_timeout(100)
        bg2 = page.evaluate(
            """() => getComputedStyle(document.querySelector('.face')).backgroundImage"""
        )
        ok("Casio model drops HP photo", "HP12C.png" not in bg2, bg2[:80])
        page.locator('button.key[data-key="2"]').click()
        page.locator('button.key[data-key="+"]').click()
        page.locator('button.key[data-key="2"]').click()
        page.locator('button.key[data-key="="]').click()
        lcd = page.locator("#display").inner_text()
        ok("Casio pad still 2+2=4", lcd == "4", lcd)

        page.evaluate("() => CasioCalc.setModel('ti30xa')")
        page.wait_for_timeout(80)
        page.locator('button.key[data-key="AC"]').click()
        page.locator('button.key[data-key="9"]').click()
        page.locator('button.key[data-key="−"]').click()
        page.locator('button.key[data-key="1"]').click()
        page.locator('button.key[data-key="="]').click()
        lcd = page.locator("#display").inner_text()
        ok("TI-30Xa 9−1=8", lcd == "8", lcd)

        title = page.evaluate("() => document.title")
        ok("page title exists", bool(title), title)

        browser.close()

    failed = [r for r in results if not r["ok"]]
    print(f"\nUX {len(results) - len(failed)}/{len(results)} OK")
    for r in results:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  {mark} {r['name']:<48} {r['detail']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
