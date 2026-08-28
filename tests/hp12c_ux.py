#!/usr/bin/env python3
"""HP-12C UX: photorealistic face, hotspot clicks, LCD, Casio/TI isolation."""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"
MUL = "\u00d7"
MINUS = "\u2212"
DIV = "\u00f7"


def main():
    results = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
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
        ok("exactly 35 hotspots", n_hs == 35, f"count={n_hs}")

        def click_hs(key):
            page.locator(f'.hp-hotspots .hs[data-key="{key}"]').first.click(force=True)

        def lcd():
            return page.locator("#display").inner_text()

        def ind():
            return page.locator("#indicators").inner_text()

        # ── arithmetic via photo ──
        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("2")
        click_hs("=")
        click_hs("3")
        click_hs("+")
        ok("click 2 ENTER 3 + on photo → 5.00", lcd() == "5.00", lcd())

        click_hs("AC")
        click_hs("7")
        click_hs("8")
        ok("click 78 on photo", lcd() in ("78.00", "78"), lcd())

        click_hs("+/-")
        ok("CHS hotspot → negative", lcd().startswith("-"), lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("4")
        click_hs("=")
        click_hs("2")
        click_hs("÷")
        ok("click 4 ENTER 2 ÷ → 2.00", lcd() == "2.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        for k in "125":
            click_hs(k)
        click_hs("=")
        for k in "375":
            click_hs(k)
        click_hs("+")
        ok("handbook 125 ENTER 375 + → 500.00", lcd() == "500.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("7")
        click_hs("=")
        ok("ENTER dup on photo: 7 ENTER lcd 7.00", lcd() == "7.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("9")
        click_hs("recip")
        ok("1/x hotspot of 9 → 0.11", lcd() == "0.11", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("2")
        click_hs("=")
        click_hs("8")
        click_hs("yx")
        ok("y^x hotspot 2 ENTER 8 → 256.00", lcd() == "256.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("1")
        click_hs("4")
        click_hs("4")
        click_hs("g")
        click_hs("yx")
        ok("g √x via photo 144 → 12.00", lcd() == "12.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("2")
        click_hs("0")
        click_hs("0")
        click_hs("=")
        click_hs("1")
        click_hs("5")
        click_hs("%")
        ok("% hotspot 200 ENTER 15 → 30.00", lcd() == "30.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("2")
        click_hs("0")
        click_hs("0")
        click_hs("=")
        click_hs("5")
        click_hs("0")
        click_hs("pctt")
        ok("%T hotspot 200 ENTER 50 → 25.00", lcd() == "25.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("4")
        click_hs("2")
        click_hs("sto")
        click_hs("1")
        click_hs("AC")
        click_hs("rcl")
        click_hs("1")
        ok("STO 1 / RCL 1 via photo → 42.00", lcd() == "42.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("2")
        click_hs("=")
        click_hs("9")
        click_hs("xy")
        ok("x⇄y hotspot 2 ENTER 9 → 2.00", lcd() == "2.00", lcd())

        # ── TVM via photo (loan n) ──
        page.evaluate("() => CasioCalc.press('mode')")
        for k in "10000":
            click_hs(k)
        click_hs("pv")
        click_hs("1")
        click_hs("i")
        for k in "300":
            click_hs(k)
        click_hs("+/-")
        click_hs("pmt")
        click_hs("0")
        click_hs("fv")
        click_hs("n")
        ok("TVM n via photo 10000 PV 1 i −300 PMT 0 FV → 41.00", lcd() == "41.00", lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("4")
        click_hs("8")
        click_hs("n")
        click_hs("1")
        click_hs("i")
        for k in "10000":
            click_hs(k)
        click_hs("pv")
        click_hs("0")
        click_hs("fv")
        click_hs("pmt")
        pmt_lcd = lcd()
        ok("TVM PMT via photo 48 n 1 i 10000 PV → ≈ −263.34",
           pmt_lcd.startswith("-263."), pmt_lcd)

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("6")
        click_hs(",")
        click_hs("5")
        click_hs("=")
        click_hs("1")
        click_hs("2")
        click_hs("÷")
        click_hs("i")
        i_stored = page.evaluate("() => _hpCalc.memory.getFinancialRegister('i')")
        ok("6,5 ENTER 12 ÷ i stores 6.5/12 via photo",
           abs(float(i_stored) - 6.5 / 12) < 1e-9, str(i_stored))

        page.evaluate("() => CasioCalc.press('mode')")
        for k in "10000":
            click_hs(k)
        click_hs("+/-")
        click_hs("g")
        click_hs("pv")
        for k in "4000":
            click_hs(k)
        click_hs("g")
        click_hs("pmt")
        click_hs("4")
        click_hs("g")
        click_hs("fv")
        click_hs("1")
        click_hs("0")
        click_hs("i")
        click_hs("f")
        click_hs("pv")
        npv_lcd = lcd()
        ok("NPV via photo −10000 CF0 4000 CFj 4 Nj 10 i → ≈ 2679.46",
           npv_lcd.replace(",", "").startswith("2679."), npv_lcd)

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("g")
        click_hs("7")
        ok("BEGIN via g 7 on photo", "BEGIN" in ind().upper() or "BEG" in ind().upper()
           or page.evaluate("() => _hpCalc.financial.paymentMode") == "BEGIN",
           f"ind={ind()!r}")

        # ── remaining hotspots present ──
        for key in [
            "n", "i", "pv", "pmt", "fv", "f", "g", "sto", "rcl", "xy",
            "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
            ",", "=", "AC", "+/-", "+", MINUS, MUL, DIV, "%",
            "mode", "yx", "recip", "pctt", "dlt", "rdn",
        ]:
            vis = page.locator(f'.hp-hotspots .hs[data-key="{key}"]').count()
            ok(f"hotspot {key} present", vis >= 1, f"count={vis}")

        box = page.locator(".lcd-bezel").bounding_box()
        ok("LCD overlay has size", box and box["width"] > 80 and box["height"] > 20, str(box))

        face = page.locator(".face").bounding_box()
        ok("LCD sits on the photo face",
           bool(box and face
                and box["x"] > face["x"]
                and box["y"] > face["y"]
                and box["x"] + box["width"] < face["x"] + face["width"]),
           f"lcd={box} face={face}")

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("f")
        ok("f prefix shows on LCD", "f" in ind().lower() or "f" in ind(), f"ind={ind()!r}")

        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("8")
        click_hs("=")
        click_hs("0")
        click_hs("÷")
        ok("÷0 via photo shows Error", lcd().startswith("Error"), lcd())

        page.evaluate("() => CasioCalc.press('mode')")
        ok("ON (mode) hotspot recovers to 0.00", lcd() == "0.00", lcd())

        # ── Casio isolation via UX model switch ──
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
        ok("Casio pad still 2+2=4", lcd() == "4", lcd())

        page.evaluate("() => CasioCalc.setModel('ti30xa')")
        page.wait_for_timeout(80)
        page.locator('button.key[data-key="AC"]').click()
        page.locator('button.key[data-key="9"]').click()
        page.locator('button.key[data-key="−"]').click()
        page.locator('button.key[data-key="1"]').click()
        page.locator('button.key[data-key="="]').click()
        ok("TI-30Xa 9−1=8", lcd() == "8", lcd())

        # round-trip back to HP photo
        page.evaluate("() => CasioCalc.setModel('hp12c')")
        page.wait_for_timeout(150)
        bg3 = page.evaluate(
            """() => getComputedStyle(document.querySelector('.face')).backgroundImage"""
        )
        ok("HP photo returns after Casio/TI", "HP12C.png" in bg3, bg3[:80])
        pad2 = page.evaluate(
            """() => getComputedStyle(document.querySelector('.pad')).display"""
        )
        ok("algebra pad hidden again on HP", pad2 == "none", pad2)
        page.evaluate("() => CasioCalc.press('mode')")
        click_hs("2")
        click_hs("=")
        click_hs("3")
        click_hs("+")
        ok("HP RPN still works after Casio/TI round-trip", lcd() == "5.00", lcd())

        title = page.evaluate("() => document.title")
        ok("page title exists", bool(title), title)

        browser.close()

    failed = [r for r in results if not r["ok"]]
    print(f"\nUX {len(results) - len(failed)}/{len(results)} OK")
    for r in results:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  {mark} {r['name']:<56} {r['detail']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
