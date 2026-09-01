#!/usr/bin/env python3
"""Exactly the 78 named operations from HP-12C Owner's Handbook 1992:

Function Key Index pp.231–234 (68) + Programming Key Index pp.235–237 (10).
Digits 0–9 = one index entry. FIX and SCI counted (f + digits / f ·).
Stops on first failure.
"""
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/?model=hp12c"
MUL, DIV, MINUS = "\u00d7", "\u00f7", "\u2212"


def eq(a, b, tol=1e-6):
    if isinstance(b, str):
        return a == b
    return abs(float(a) - float(b)) <= tol


def close(a, b, tol=0.05):
    return abs(float(a) - float(b)) <= tol


def main():
    fns = []

    def fn(name, keys, pred):
        fns.append((name, keys, pred))

    # ══ Function Key Index 231–234 (68) ══
    # p.231 power / entry / arith / storage / percent
    fn("01 ON", ["8", "=", "0", DIV, "mode"],
       lambda s: (not str(s["lcd"]).startswith("Error"), s["lcd"]))
    fn("02 f", ["f"],
       lambda s: (s["f"] is True, f"f={s['f']}"))
    fn("03 g", ["g"],
       lambda s: (s["g"] is True, f"g={s['g']}"))
    fn("04 CLEAR PREFIX", ["f", "sst"],
       lambda s: (s["f"] is False, f"f={s['f']}"))
    fn("05 digits 0–9", ["1", "2", "3"],
       lambda s: (eq(s["x"], 123), s["lcd"]))
    fn("06 decimal ·", ["1", ",", "5"],
       lambda s: (eq(s["x"], 1.5), s["lcd"]))
    fn("07 EEX", ["2", "eex", "3"],
       lambda s: (eq(s["x"], 2000), s["lcd"]))
    fn("08 CLx", ["5", "=", "AC"],
       lambda s: (eq(s["x"], 0) and eq(s["y"], 5), f"x={s['x']} y={s['y']}"))
    fn("09 ENTER", ["7", "="],
       lambda s: (eq(s["x"], 7) and eq(s["y"], 7), f"x={s['x']} y={s['y']}"))
    fn("10 CHS", ["5", "6", "+/-"],
       lambda s: (eq(s["x"], -56), s["lcd"]))
    fn("11 +", ["1", "2", "5", "=", "3", "7", "5", "+"],
       lambda s: (eq(s["x"], 500) and s["lcd"] == "500.00", s["lcd"]))
    fn("12 −", ["1", "2", "5", "0", "=", "4", "5", "0", MINUS],
       lambda s: (eq(s["x"], 800), s["lcd"]))
    fn("13 ×", ["2", "4", "=", "1", "5", MUL],
       lambda s: (eq(s["x"], 360), s["lcd"]))
    fn("14 ÷", ["2", "5", "0", "0", "=", "2", "5", DIV],
       lambda s: (eq(s["x"], 100), s["lcd"]))
    fn("15 STO", ["4", "2", "sto", "1", "AC", "rcl", "1"],
       lambda s: (eq(s["x"], 42), s["lcd"]))
    fn("16 RCL", ["4", "2", "sto", "3", "0", "rcl", "3"],
       lambda s: (eq(s["x"], 42), s["lcd"]))
    fn("17 CLEAR REG", ["4", "2", "sto", "1", "f", "rdn", "rcl", "1"],
       lambda s: (eq(s["x"], 0), s["lcd"]))
    fn("18 %", ["2", "0", "0", "=", "1", "5", "%"],
       lambda s: (eq(s["x"], 30) and eq(s["y"], 200), f"x={s['x']} y={s['y']}"))
    fn("19 Δ%", ["2", "0", "0", "=", "2", "5", "0", "dlt"],
       lambda s: (eq(s["x"], 25), s["lcd"]))
    fn("20 %T", ["2", "0", "0", "=", "5", "0", "pctt"],
       lambda s: (eq(s["x"], 25), s["lcd"]))
    # p.232 calendar + financial
    fn("21 D.MY", ["g", "4"],
       lambda s: (s["dmy"] is True, f"dmy={s['dmy']}"))
    fn("22 M.DY", ["g", "4", "g", "5"],
       lambda s: (s["dmy"] is False, f"dmy={s['dmy']}"))
    fn("23 DATE", ["4", ",", "2", "8", "1", "9", "8", "2", "=", "1", "0", "f", "+/-"],
       lambda s: (abs(s["x"] - 5.081982) < 1e-6 and eq(s["y"], 6), f"x={s['x']} y={s['y']}"))
    fn("24 ΔDYS", ["4", ",", "2", "8", "1", "9", "8", "2", "=", "7", ",", "0", "4", "1", "9", "8", "2", "g", "eex"],
       lambda s: (eq(s["x"], 67) and eq(s["y"], 66), f"x={s['x']} y={s['y']}"))
    fn("25 CLEAR FIN", ["1", "0", "n", "f", "AC"],
       lambda s: (eq(s["n"], 0), f"n={s['n']}"))
    fn("26 BEG", ["g", "7"],
       lambda s: (s["begin"] == "BEGIN", s["begin"]))
    fn("27 END", ["g", "7", "g", "8"],
       lambda s: (s["begin"] == "END", s["begin"]))
    fn("28 INT", ["6", "0", "n", "7", "i", "4", "5", "0", "+/-", "pv", "f", "i"],
       lambda s: (close(s["x"], 5.25, 0.02), s["lcd"]))
    fn("29 n", ["1", "0", "0", "0", "0", "pv", "1", "i", "3", "0", "0", "+/-", "pmt", "0", "fv", "n"],
       lambda s: (eq(s["x"], 41), s["lcd"]))
    fn("30 12×", ["5", "g", "n"],
       lambda s: (eq(s["x"], 60) and eq(s["n"], 60), f"x={s['x']} n={s['n']}"))
    fn("31 i", ["3", "n", "1", "0", "0", "0", "0", "+/-", "pv", "0", "pmt", "1", "5", "0", "0", "0", "fv", "i"],
       lambda s: (close(s["x"], 14.47, 0.05), f"i={s['x']}"))
    fn("32 12÷", ["3", "6", "g", "i"],
       lambda s: (eq(s["x"], 3) and eq(s["i"], 3), f"x={s['x']} i={s['i']}"))
    fn("33 PV", ["4", "8", "n", "1", "i", "2", "6", "3", ",", "3", "4", "+/-", "pmt", "0", "fv", "pv"],
       lambda s: (close(s["x"], 10000, 2.0), f"pv={s['x']}"))
    fn("34 PMT", ["3", "6", "0", "n", "0", ",", "5", "i", "1", "0", "0", "0", "0", "0", "pv", "0", "fv", "pmt"],
       lambda s: (close(s["x"], -599.55, 0.05), s["lcd"]))
    fn("35 FV", ["1", "2", "n", "1", "i", "1", "0", "0", "0", "+/-", "pv", "0", "pmt", "fv"],
       lambda s: (close(s["x"], 1126.83, 0.05), f"fv={s['x']}"))
    fn("36 AMORT", ["1", "3", ",", "2", "5", "g", "i", "5", "0", "0", "0", "0", "pv",
                    "5", "7", "3", ",", "3", "5", "+/-", "pmt", "1", "2", "f", "n"],
       lambda s: (close(s["x"], -6608.89, 0.05) and close(s["pv"], 49728.69, 0.05),
                  f"x={s['x']} pv={s['pv']}"))
    fn("37 NPV", ["1", "0", "0", "0", "0", "+/-", "g", "pv", "4", "0", "0", "0", "g", "pmt",
                  "4", "g", "fv", "1", "0", "i", "f", "pv"],
       lambda s: (close(s["x"], 2679.46, 0.05), s["lcd"]))
    fn("38 IRR", ["1", "0", "0", "0", "0", "+/-", "g", "pv", "4", "0", "0", "0", "g", "pmt",
                  "4", "g", "fv", "f", "fv"],
       lambda s: (close(s["x"], 21.86, 0.15), s["lcd"]))
    fn("39 CF0", ["1", "0", "+/-", "g", "pv", "rcl", "g", "pv"],
       lambda s: (eq(s["x"], -10), s["lcd"]))
    fn("40 CFj", ["1", "+/-", "g", "pv", "4", "g", "pmt", "rcl", "g", "pmt"],
       lambda s: (eq(s["x"], 4), s["lcd"]))
    fn("41 Nj", ["1", "+/-", "g", "pv", "5", "g", "pmt", "4", "g", "fv", "rcl", "g", "fv"],
       lambda s: (eq(s["x"], 4), s["lcd"]))
    fn("42 PRICE", ["4", ",", "7", "5", "pmt", "4", ",", "7", "5", "i",
                    "6", ",", "0", "1", "2", "0", "0", "6", "=",
                    "6", ",", "0", "1", "2", "0", "2", "6", "f", "yx"],
       lambda s: (close(s["x"], 100, 2.0), f"x={s['x']}"))
    fn("43 YTM", ["4", ",", "7", "5", "pmt", "1", "0", "0", "pv",
                  "6", ",", "0", "1", "2", "0", "0", "6", "=",
                  "6", ",", "0", "1", "2", "0", "2", "6", "f", "recip"],
       lambda s: (close(s["x"], 4.75, 0.15), f"ytm={s['x']}"))
    fn("44 SL", ["1", "0", "0", "0", "0", "pv", "1", "0", "0", "0", "fv", "5", "n", "3", "f", "pctt"],
       lambda s: (close(s["x"], 1800, 0.05) and close(s["y"], 3600, 0.05), f"x={s['x']} y={s['y']}"))
    fn("45 SOYD", ["1", "0", "0", "0", "0", "pv", "1", "0", "0", "0", "fv", "5", "n", "1", "f", "dlt"],
       lambda s: (close(s["x"], 3000, 0.05), s["lcd"]))
    fn("46 DB", ["1", "0", "0", "0", "0", "pv", "1", "0", "0", "0", "fv", "5", "n", "2", "0", "0", "i", "1", "f", "%"],
       lambda s: (close(s["x"], 4000, 0.05), s["lcd"]))
    # p.233–234 stats + math + stack
    fn("47 CLEAR Σ", ["9", "sto", "0", "3", "=", "2", "sigma", "f", "sigma", "g", "0"],
       lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]))
    fn("48 Σ+", ["3", "=", "2", "sigma"],
       lambda s: (eq(s["x"], 1), f"n={s['x']}"))
    fn("49 Σ−", ["3", "=", "2", "sigma", "5", "=", "4", "sigma", "5", "=", "4", "g", "sigma"],
       lambda s: (eq(s["x"], 1), f"n={s['x']}"))
    fn("50 x̄", ["3", "=", "2", "sigma", "5", "=", "4", "sigma", "g", "0"],
       lambda s: (eq(s["x"], 3) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"))
    fn("51 x̄w", ["5", "=", "2", "sigma", "3", "=", "4", "sigma", "g", "6"],
       lambda s: (close(s["x"], 2.75, 0.02), f"x={s['x']}"))
    fn("52 s", ["3", "=", "2", "sigma", "5", "=", "4", "sigma", "g", ","],
       lambda s: (close(s["x"], 2 ** 0.5, 0.01), f"x={s['x']}"))
    fn("53 ŷ,r", ["2", "=", "1", "sigma", "4", "=", "2", "sigma", "3", "g", "2"],
       lambda s: (close(s["x"], 6, 0.05) and close(s["y"], 1, 0.02), f"ŷ={s['x']} r={s['y']}"))
    fn("54 x̂,r", ["2", "=", "1", "sigma", "4", "=", "2", "sigma", "6", "g", "1"],
       lambda s: (close(s["x"], 3, 0.05) and close(s["y"], 1, 0.02), f"x̂={s['x']} r={s['y']}"))
    fn("55 √x", ["1", "4", "4", "g", "yx"],
       lambda s: (eq(s["x"], 12), s["lcd"]))
    fn("56 y^x", ["2", "=", "8", "yx"],
       lambda s: (eq(s["x"], 256), s["lcd"]))
    fn("57 1/x", ["4", "recip"],
       lambda s: (eq(s["x"], 0.25), s["lcd"]))
    fn("58 n!", ["5", "g", "3"],
       lambda s: (eq(s["x"], 120), s["lcd"]))
    fn("59 e^x", ["1", "g", "recip"],
       lambda s: (close(s["x"], 2.718281828, 1e-8), s["x"]))
    fn("60 LN", ["1", "g", "recip", "g", "pctt"],
       lambda s: (close(s["x"], 1.0, 1e-8), s["x"]))
    fn("61 RND", ["1", ",", "2", "3", "9", "f", "pmt"],
       lambda s: (eq(s["x"], 1.24) and s["lcd"] == "1.24", s["lcd"]))
    fn("62 INTG", ["3", ",", "7", "g", "%"],
       lambda s: (eq(s["x"], 3), s["lcd"]))
    fn("63 FRAC", ["3", ",", "7", "g", "dlt"],
       lambda s: (abs(s["x"] - 0.7) < 1e-9, s["x"]))
    fn("64 x⇄y", ["2", "=", "9", "xy"],
       lambda s: (eq(s["x"], 2) and eq(s["y"], 9), f"x={s['x']} y={s['y']}"))
    fn("65 R↓", ["1", "=", "2", "=", "3", "=", "4", "rdn", "rdn", "rdn", "rdn"],
       lambda s: (eq(s["x"], 4) and eq(s["y"], 3), f"x={s['x']} y={s['y']}"))
    fn("66 LSTx", ["8", "=", "2", DIV, "g", "="],
       lambda s: (eq(s["x"], 2) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"))
    fn("67 FIX", ["1", "=", "3", DIV, "f", "4"],
       lambda s: (s["lcd"] == "0.3333", s["lcd"]))
    fn("68 SCI", ["1", "2", "3", "4", "f", ","],
       lambda s: ("1.234" in s["lcd"] and " " in s["lcd"], s["lcd"]))

    # ══ Programming Key Index 235–237 (10) ══
    fn("69 P/R", ["f", "rs"],
       lambda s: (s["prgm"] is True, f"prgm={s['prgm']} lcd={s['lcd']}"))
    fn("70 MEM", ["g", "9"],
       lambda s: (eq(s["x"], 99), s["lcd"]))
    fn("71 CLEAR PRGM",
       ["f", "rs", "2", "=", "3", "+", "f", "sigma", "f", "rs", "7", "rs"],
       lambda s: (eq(s["x"], 7), f"x={s['x']} (must not be 5)"))
    fn("72 R/S", ["f", "rs", "2", "=", "3", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 5), s["lcd"]))
    fn("73 GTO", ["f", "rs", "2", "=", "3", "+", "f", "rs", "g", "rdn", "0", "0", "rs"],
       lambda s: (eq(s["x"], 5), f"x={s['x']}"))
    fn("74 SST", ["f", "rs", "2", "=", "3", "+", "f", "rs", "sst", "sst", "sst", "sst"],
       lambda s: (eq(s["x"], 5), s["lcd"]))
    fn("75 BST", ["f", "rs", "2", "=", "3", "+", "g", "sst"],
       lambda s: (s["prgm"] is True and s["pc"] < 4, f"prgm={s['prgm']} pc={s['pc']} lcd={s['lcd']}"))
    fn("76 PSE", ["f", "rs", "5", "f", "xy", "2", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 7), f"x={s['x']} (5 PSE 2 + → 7)"))
    fn("77 x≤y", ["f", "rs", "3", "=", "5", "g", "xy", "9", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 8), f"x={s['x']}"))
    fn("78 x=0", ["f", "rs", "2", "g", "AC", "9", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 2), f"x={s['x']}"))

    assert len(fns) == 78, f"expected 78, got {len(fns)}"

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE, wait_until="networkidle")
        page.evaluate("() => CasioCalc.setModel('hp12c')")
        assert page.evaluate("() => !!window._hpCalc")

        def tap(*keys):
            for k in keys:
                page.evaluate("(k) => CasioCalc.press(k)", k)

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

        passed = 0
        for i, (name, keys, pred) in enumerate(fns, 1):
            page.evaluate("() => _hpCalc.reset()")
            try:
                tap(*keys)
                s = snap()
                ok, detail = pred(s)
            except Exception as e:
                ok, detail, s = False, str(e), {}
            mark = "OK  " if ok else "FAIL"
            print(f"{mark} {i:02d}/78  {name:<22} {detail}")
            if not ok:
                print(f"\nSTOP at {i}/78 {name}")
                print(f"  keys: {keys}")
                print(f"  snap: {s}")
                browser.close()
                raise SystemExit(i)
            passed += 1
        browser.close()
        print(f"\nHANDBOOK INDEX  {passed}/78 OK")


if __name__ == "__main__":
    main()
