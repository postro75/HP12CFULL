#!/usr/bin/env python3
"""Human-style HP-12C: laptop keyboard where mapped, otherwise click the photo.

Does not call CasioCalc.press. Uses page.keyboard and hotspot clicks.
Stops on first failure. Target: live Vercel unless BASE is set.
"""
import os
from playwright.sync_api import sync_playwright

BASE = os.environ.get("HP12C_BASE", "https://hp12cfull.vercel.app/?model=hp12c")
PAUSE = 35


def eq(a, b, tol=1e-6):
    if isinstance(b, str):
        return a == b
    return abs(float(a) - float(b)) <= tol


def close(a, b, tol=0.05):
    return abs(float(a) - float(b)) <= tol


def main():
    cases = []

    def add(name, drive, pred):
        cases.append((name, drive, pred))

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 980, "height": 760})
        page.goto(BASE, wait_until="networkidle")
        # human: land on page, click HP-12C if needed
        if "hp12c" not in page.url:
            page.locator('.models [data-model="hp12c"]').click()
            page.wait_for_timeout(200)
        page.wait_for_timeout(250)

        def lcd():
            return page.locator("#display").inner_text()

        def snap():
            return page.evaluate(
                """() => {
                  const c = _hpCalc;
                  return {
                    x: c.stack.x, y: c.stack.y, z: c.stack.z, t: c.stack.t,
                    lcd: document.getElementById('display').textContent,
                    f: c.prefixF, g: c.prefixG,
                    begin: c.financial.paymentMode,
                    dmy: !!c.dmyMode,
                    prgm: !!c.prgmMode,
                    pc: c.pc,
                    n: c.memory.getFinancialRegister('n'),
                    i: c.memory.getFinancialRegister('i'),
                    pv: c.memory.getFinancialRegister('pv'),
                    pmt: c.memory.getFinancialRegister('pmt'),
                    fv: c.memory.getFinancialRegister('fv'),
                  };
                }"""
            )

        def reset():
            page.evaluate("() => _hpCalc.reset()")
            page.wait_for_timeout(20)

        def kb(*chars):
            """Laptop keys. Special names: Enter, Escape, Backspace."""
            for ch in chars:
                if ch in ("Enter", "Escape", "Backspace", "Tab"):
                    page.keyboard.press(ch)
                else:
                    page.keyboard.type(ch, delay=PAUSE)
                page.wait_for_timeout(PAUSE)

        def tap(key, gold=False):
            """Click the calculator face like a finger."""
            if gold:
                loc = page.locator(
                    f'.hp-hotspots .hs[data-prefix="f"][data-key="{key}"]'
                )
                if loc.count() == 0:
                    tap("f")
                    loc = page.locator(
                        f'.hp-hotspots .hs[data-key="{key}"]:not([data-prefix])'
                    )
            else:
                loc = page.locator(
                    f'.hp-hotspots .hs[data-key="{key}"]:not([data-prefix])'
                )
            loc.first.click(force=True, timeout=5000)
            page.wait_for_timeout(PAUSE)

        # ── 78 handbook ops, human path ──
        # laptop: 0-9 . , + - * / Enter Escape % n i f g p m v s r
        # face click: everything else (CHS, EEX, yx, recip, gold labels, …)

        add("01 ON", lambda: (kb("8", "Enter", "0", "/"), tap("mode")),
            lambda s: (not str(s["lcd"]).startswith("Error"), s["lcd"]))
        add("02 f", lambda: kb("f"),
            lambda s: (s["f"] is True, f"f={s['f']}"))
        add("03 g", lambda: kb("g"),
            lambda s: (s["g"] is True, f"g={s['g']}"))
        add("04 CLEAR PREFIX", lambda: (kb("f"), tap("sst")),
            lambda s: (s["f"] is False, f"f={s['f']}"))
        add("05 digits 0–9 laptop", lambda: kb("123"),
            lambda s: (eq(s["x"], 123), s["lcd"]))
        add("06 decimal laptop .", lambda: kb("1", ".", "5"),
            lambda s: (eq(s["x"], 1.5), s["lcd"]))
        add("06b decimal laptop ,", lambda: kb("1", ",", "5"),
            lambda s: (eq(s["x"], 1.5), s["lcd"]))
        add("07 EEX click", lambda: (kb("2"), tap("eex"), kb("3")),
            lambda s: (eq(s["x"], 2000), s["lcd"]))
        add("08 CLx Escape", lambda: kb("5", "Enter", "Escape"),
            lambda s: (eq(s["x"], 0) and eq(s["y"], 5), f"x={s['x']} y={s['y']}"))
        add("09 ENTER laptop", lambda: kb("7", "Enter"),
            lambda s: (eq(s["x"], 7) and eq(s["y"], 7), f"x={s['x']} y={s['y']}"))
        add("10 CHS click", lambda: (kb("56"), tap("+/-")),
            lambda s: (eq(s["x"], -56), s["lcd"]))
        add("11 + laptop", lambda: kb("125", "Enter", "375", "+"),
            lambda s: (eq(s["x"], 500), s["lcd"]))
        add("12 − laptop", lambda: kb("1250", "Enter", "450", "-"),
            lambda s: (eq(s["x"], 800), s["lcd"]))
        add("13 × laptop", lambda: kb("24", "Enter", "15", "*"),
            lambda s: (eq(s["x"], 360), s["lcd"]))
        add("14 ÷ laptop", lambda: kb("2500", "Enter", "25", "/"),
            lambda s: (eq(s["x"], 100), s["lcd"]))
        add("15 STO s+digit", lambda: kb("42", "s", "1", "Escape", "r", "1"),
            lambda s: (eq(s["x"], 42), s["lcd"]))
        add("16 RCL r+digit", lambda: kb("42", "s", "3", "0", "r", "3"),
            lambda s: (eq(s["x"], 42), s["lcd"]))
        add("17 CLEAR REG f+click R↓", lambda: (kb("42", "s", "1", "f"), tap("rdn"), kb("r", "1")),
            lambda s: (eq(s["x"], 0), s["lcd"]))
        add("18 % laptop", lambda: kb("200", "Enter", "15", "%"),
            lambda s: (eq(s["x"], 30) and eq(s["y"], 200), f"x={s['x']} y={s['y']}"))
        add("19 Δ% click", lambda: (kb("200", "Enter", "250"), tap("dlt")),
            lambda s: (eq(s["x"], 25), s["lcd"]))
        add("20 %T click", lambda: (kb("200", "Enter", "50"), tap("pctt")),
            lambda s: (eq(s["x"], 25), s["lcd"]))
        add("21 D.MY g4 laptop", lambda: kb("g", "4"),
            lambda s: (s["dmy"] is True, f"dmy={s['dmy']}"))
        add("22 M.DY g5 laptop", lambda: kb("g", "4", "g", "5"),
            lambda s: (s["dmy"] is False, f"dmy={s['dmy']}"))
        add("23 DATE click CHS gold", lambda: (kb("4.281982", "Enter", "10"), tap("+/-", gold=True)),
            lambda s: (abs(s["x"] - 5.081982) < 1e-6 and eq(s["y"], 6), f"x={s['x']} y={s['y']}"))
        add("24 ΔDYS g+EEX click", lambda: (kb("4.281982", "Enter", "7.041982", "g"), tap("eex")),
            lambda s: (eq(s["x"], 67) and eq(s["y"], 66), f"x={s['x']} y={s['y']}"))
        add("25 CLEAR FIN gold CLx", lambda: (kb("10", "n"), tap("AC", gold=True)),
            lambda s: (eq(s["n"], 0), f"n={s['n']}"))
        add("26 BEG g7", lambda: kb("g", "7"),
            lambda s: (s["begin"] == "BEGIN", s["begin"]))
        add("27 END g8", lambda: kb("g", "7", "g", "8"),
            lambda s: (s["begin"] == "END", s["begin"]))
        add("28 INT gold i", lambda: (kb("60", "n", "7", "i", "450"), tap("+/-"), kb("p"), tap("i", gold=True)),
            lambda s: (close(s["x"], 5.25, 0.02), s["lcd"]))
        add("29 n solve laptop", lambda: (kb("10000", "p", "1", "i", "300"), tap("+/-"), kb("m", "0", "v", "n")),
            lambda s: (eq(s["x"], 41), s["lcd"]))
        add("30 12× gn", lambda: kb("5", "g", "n"),
            lambda s: (eq(s["x"], 60) and eq(s["n"], 60), f"x={s['x']} n={s['n']}"))
        add("31 i solve", lambda: (kb("3", "n", "10000"), tap("+/-"), kb("p", "0", "m", "15000", "v", "i")),
            lambda s: (close(s["x"], 14.47, 0.05), f"i={s['x']}"))
        add("32 12÷ gi", lambda: kb("36", "g", "i"),
            lambda s: (eq(s["x"], 3) and eq(s["i"], 3), f"x={s['x']} i={s['i']}"))
        add("33 PV solve", lambda: (kb("48", "n", "1", "i", "263.34"), tap("+/-"), kb("m", "0", "v", "p")),
            lambda s: (close(s["x"], 10000, 2.0), f"pv={s['x']}"))
        add("34 PMT laptop n i p v m", lambda: kb("360", "n", "0.5", "i", "100000", "p", "0", "v", "m"),
            lambda s: (close(s["x"], -599.55, 0.05), s["lcd"]))
        add("35 FV", lambda: (kb("12", "n", "1", "i", "1000"), tap("+/-"), kb("p", "0", "m", "v")),
            lambda s: (close(s["x"], 1126.83, 0.05), f"fv={s['x']}"))
        add("36 AMORT gold n", lambda: (kb("13.25", "g", "i", "50000", "p", "573.35"), tap("+/-"), kb("m", "12"), tap("n", gold=True)),
            lambda s: (close(s["x"], -6608.89, 0.05), f"x={s['x']}"))
        add("37 NPV gold PV", lambda: (kb("10000"), tap("+/-"), kb("g", "p", "4000", "g", "m", "4", "g", "v", "10", "i"), tap("pv", gold=True)),
            lambda s: (close(s["x"], 2679.46, 0.05), s["lcd"]))
        add("38 IRR gold FV", lambda: (kb("10000"), tap("+/-"), kb("g", "p", "4000", "g", "m", "4", "g", "v"), tap("fv", gold=True)),
            lambda s: (close(s["x"], 21.86, 0.15), s["lcd"]))
        add("39 CF0 g p", lambda: (kb("10"), tap("+/-"), kb("g", "p", "r", "g", "p")),
            lambda s: (eq(s["x"], -10), s["lcd"]))
        add("40 CFj g m", lambda: (kb("1"), tap("+/-"), kb("g", "p", "4", "g", "m", "r", "g", "m")),
            lambda s: (eq(s["x"], 4), s["lcd"]))
        add("41 Nj g v", lambda: (kb("1"), tap("+/-"), kb("g", "p", "5", "g", "m", "4", "g", "v", "r", "g", "v")),
            lambda s: (eq(s["x"], 4), s["lcd"]))
        add("42 PRICE gold yx", lambda: (kb("4.75", "m", "4.75", "i", "6.012006", "Enter", "6.012026"), tap("yx", gold=True)),
            lambda s: (close(s["x"], 100, 2.0), f"x={s['x']}"))
        add("43 YTM gold 1/x", lambda: (kb("4.75", "m", "100", "p", "6.012006", "Enter", "6.012026"), tap("recip", gold=True)),
            lambda s: (close(s["x"], 4.75, 0.15), f"ytm={s['x']}"))
        add("44 SL gold %T", lambda: (kb("10000", "p", "1000", "v", "5", "n", "3"), tap("pctt", gold=True)),
            lambda s: (close(s["x"], 1800, 0.05), s["lcd"]))
        add("45 SOYD gold Δ%", lambda: (kb("10000", "p", "1000", "v", "5", "n", "1"), tap("dlt", gold=True)),
            lambda s: (close(s["x"], 3000, 0.05), s["lcd"]))
        add("46 DB gold %", lambda: (kb("10000", "p", "1000", "v", "5", "n", "200", "i", "1"), tap("%", gold=True)),
            lambda s: (close(s["x"], 4000, 0.05), s["lcd"]))
        add("47 CLEAR Σ gold sigma", lambda: (kb("9", "s", "0", "3", "Enter", "2"), tap("sigma"), tap("sigma", gold=True), kb("g", "0")),
            lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]))
        add("48 Σ+ click", lambda: (kb("3", "Enter", "2"), tap("sigma")),
            lambda s: (eq(s["x"], 1), f"n={s['x']}"))
        add("49 Σ− g+sigma", lambda: (kb("3", "Enter", "2"), tap("sigma"), kb("5", "Enter", "4"), tap("sigma"), kb("5", "Enter", "4", "g"), tap("sigma")),
            lambda s: (eq(s["x"], 1), f"n={s['x']}"))
        add("50 x̄ g0", lambda: (kb("3", "Enter", "2"), tap("sigma"), kb("5", "Enter", "4"), tap("sigma"), kb("g", "0")),
            lambda s: (eq(s["x"], 3) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"))
        add("51 x̄w g6", lambda: (kb("5", "Enter", "2"), tap("sigma"), kb("3", "Enter", "4"), tap("sigma"), kb("g", "6")),
            lambda s: (close(s["x"], 2.75, 0.02), f"x={s['x']}"))
        add("52 s g.", lambda: (kb("3", "Enter", "2"), tap("sigma"), kb("5", "Enter", "4"), tap("sigma"), kb("g", ".")),
            lambda s: (close(s["x"], 2 ** 0.5, 0.01), f"x={s['x']}"))
        add("53 ŷ,r g2", lambda: (kb("2", "Enter", "1"), tap("sigma"), kb("4", "Enter", "2"), tap("sigma"), kb("3", "g", "2")),
            lambda s: (close(s["x"], 6, 0.05) and close(s["y"], 1, 0.02), f"ŷ={s['x']} r={s['y']}"))
        add("54 x̂,r g1", lambda: (kb("2", "Enter", "1"), tap("sigma"), kb("4", "Enter", "2"), tap("sigma"), kb("6", "g", "1")),
            lambda s: (close(s["x"], 3, 0.05) and close(s["y"], 1, 0.02), f"x̂={s['x']} r={s['y']}"))
        add("55 √x g yx", lambda: (kb("144", "g"), tap("yx")),
            lambda s: (eq(s["x"], 12), s["lcd"]))
        add("56 y^x click", lambda: (kb("2", "Enter", "8"), tap("yx")),
            lambda s: (eq(s["x"], 256), s["lcd"]))
        add("57 1/x click", lambda: (kb("4"), tap("recip")),
            lambda s: (eq(s["x"], 0.25), s["lcd"]))
        add("58 n! g3", lambda: kb("5", "g", "3"),
            lambda s: (eq(s["x"], 120), s["lcd"]))
        add("59 e^x g recip", lambda: (kb("1", "g"), tap("recip")),
            lambda s: (close(s["x"], 2.718281828, 1e-8), s["x"]))
        add("60 LN g %T", lambda: (kb("1", "g"), tap("recip"), kb("g"), tap("pctt")),
            lambda s: (close(s["x"], 1.0, 1e-8), s["x"]))
        add("61 RND gold PMT", lambda: (kb("1.239"), tap("pmt", gold=True)),
            lambda s: (eq(s["x"], 1.24), s["lcd"]))
        add("62 INTG g%", lambda: kb("3.7", "g", "%"),
            lambda s: (eq(s["x"], 3), s["lcd"]))
        add("63 FRAC g dlt", lambda: (kb("3.7", "g"), tap("dlt")),
            lambda s: (abs(s["x"] - 0.7) < 1e-9, s["x"]))
        add("64 x⇄y click", lambda: (kb("2", "Enter", "9"), tap("xy")),
            lambda s: (eq(s["x"], 2) and eq(s["y"], 9), f"x={s['x']} y={s['y']}"))
        add("65 R↓ click", lambda: (kb("1", "Enter", "2", "Enter", "3", "Enter", "4"), tap("rdn"), tap("rdn"), tap("rdn"), tap("rdn")),
            lambda s: (eq(s["x"], 4) and eq(s["y"], 3), f"x={s['x']} y={s['y']}"))
        add("66 LSTx g Enter", lambda: kb("8", "Enter", "2", "/", "g", "Enter"),
            lambda s: (eq(s["x"], 2) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"))
        add("67 FIX f4", lambda: kb("1", "Enter", "3", "/", "f", "4"),
            lambda s: (s["lcd"] == "0.3333", s["lcd"]))
        add("68 SCI f.", lambda: kb("1234", "f", "."),
            lambda s: ("1.234" in s["lcd"] and " " in s["lcd"], s["lcd"]))
        add("69 P/R gold R/S", lambda: tap("rs", gold=True),
            lambda s: (s["prgm"] is True, f"prgm={s['prgm']} lcd={s['lcd']}"))
        add("70 MEM g9", lambda: kb("g", "9"),
            lambda s: (eq(s["x"], 99), s["lcd"]))
        add("71 CLEAR PRGM", lambda: (tap("rs", gold=True), kb("2", "Enter", "3", "+"), tap("sigma", gold=True), tap("rs", gold=True), kb("7"), tap("rs")),
            lambda s: (eq(s["x"], 7), f"x={s['x']}"))
        add("72 R/S run 2 ENTER 3 +", lambda: (tap("rs", gold=True), kb("2", "Enter", "3", "+"), tap("rs", gold=True), tap("rs")),
            lambda s: (eq(s["x"], 5), s["lcd"]))
        add("73 GTO g R↓ 00", lambda: (tap("rs", gold=True), kb("2", "Enter", "3", "+"), tap("rs", gold=True), kb("g"), tap("rdn"), kb("00"), tap("rs")),
            lambda s: (eq(s["x"], 5), f"x={s['x']}"))
        add("74 SST four times", lambda: (tap("rs", gold=True), kb("2", "Enter", "3", "+"), tap("rs", gold=True), tap("sst"), tap("sst"), tap("sst"), tap("sst")),
            lambda s: (eq(s["x"], 5), s["lcd"]))
        add("75 BST g SST", lambda: (tap("rs", gold=True), kb("2", "Enter", "3", "+"), kb("g"), tap("sst")),
            lambda s: (s["prgm"] is True and s["pc"] < 4, f"prgm={s['prgm']} pc={s['pc']}"))
        add("76 PSE gold xy", lambda: (tap("rs", gold=True), kb("5"), tap("xy", gold=True), kb("2", "+"), tap("rs", gold=True), tap("rs")),
            lambda s: (eq(s["x"], 7), f"x={s['x']}"))
        add("77 x≤y g xy", lambda: (tap("rs", gold=True), kb("3", "Enter", "5", "g"), tap("xy"), kb("9", "+"), tap("rs", gold=True), tap("rs")),
            lambda s: (eq(s["x"], 8), f"x={s['x']}"))
        add("78 x=0 g Escape", lambda: (tap("rs", gold=True), kb("2", "g", "Escape"), kb("9", "+"), tap("rs", gold=True), tap("rs")),
            lambda s: (eq(s["x"], 2), f"x={s['x']}"))

        # extra: click digits on the photo, not laptop
        add("photo digits 125 ENTER 375 +", lambda: (
            tap("1"), tap("2"), tap("5"), tap("="), tap("3"), tap("7"), tap("5"), tap("+")
        ), lambda s: (eq(s["x"], 500) and s["lcd"] == "500.00", s["lcd"]))
        add("photo 2 ENTER 3 +", lambda: (tap("2"), tap("="), tap("3"), tap("+")),
            lambda s: (s["lcd"] == "5.00", s["lcd"]))
        add("photo CHS of 78", lambda: (tap("7"), tap("8"), tap("+/-")),
            lambda s: (s["lcd"].startswith("-"), s["lcd"]))
        add("photo 4 ENTER 2 ÷", lambda: (tap("4"), tap("="), tap("2"), tap("÷")),
            lambda s: (s["lcd"] == "2.00", s["lcd"]))
        add("switcher click Casio then HP", lambda: (
            page.locator('.models [data-model="casio"]').click(),
            page.wait_for_timeout(150),
            page.locator('.models [data-model="hp12c"]').click(),
            page.wait_for_timeout(200),
            kb("2", "Enter", "3", "+"),
        ), lambda s: (s["lcd"] == "5.00", s["lcd"]))

        n = len(cases)
        passed = 0
        for i, (name, drive, pred) in enumerate(cases, 1):
            reset()
            try:
                drive()
                s = snap()
                ok, detail = pred(s)
            except Exception as e:
                ok, detail, s = False, str(e), {}
            mark = "OK  " if ok else "FAIL"
            print(f"{mark} {i:02d}/{n}  {name:<42} {detail}")
            if not ok:
                print(f"\nSTOP at {i}/{n} {name}")
                print(f"  snap: {s}")
                browser.close()
                raise SystemExit(i)
            passed += 1
        browser.close()
        print(f"\nHUMAN  {passed}/{n} OK  ({BASE})")


if __name__ == "__main__":
    main()
