#!/usr/bin/env python3
"""HP-12C engine tests — RPN stack + TVM via CasioCalc.press (no photo clicks).

Scenarios from HP-12C Owner's Handbook / apezoo examples, plus stack-machine
edge cases. LCD + X/Y/Z/T/LastX/registers are asserted, not just 'did not crash'.
"""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"
MUL, DIV, MINUS = "\u00d7", "\u00f7", "\u2212"


def main():
    results = []
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(BASE, wait_until="networkidle")
        page.evaluate("() => CasioCalc.setModel('hp12c')")
        assert page.evaluate("() => !!window._hpCalc"), "hpInit failed"

        def tap(*keys):
            for k in keys:
                page.evaluate("(k) => CasioCalc.press(k)", k)

        def snap():
            return page.evaluate(
                """() => {
                  const c = _hpCalc;
                  return {
                    x: c.stack.x, y: c.stack.y, z: c.stack.z, t: c.stack.t,
                    lastX: c.stack.lastX, lift: c.stack.stackLift,
                    lcd: document.getElementById('display').textContent,
                    ind: document.getElementById('indicators').textContent,
                    f: c.prefixF, g: c.prefixG,
                    begin: c.financial.paymentMode,
                    n: c.memory.getFinancialRegister('n'),
                    i: c.memory.getFinancialRegister('i'),
                    pv: c.memory.getFinancialRegister('pv'),
                    pmt: c.memory.getFinancialRegister('pmt'),
                    fv: c.memory.getFinancialRegister('fv'),
                  };
                }"""
            )

        def case(name, keys, check):
            tap("mode")  # ON = full reset (stack + financial + prefixes)
            tap(*keys)
            s = snap()
            ok, detail = check(s)
            results.append({"name": name, "ok": bool(ok), "detail": detail, "s": s})

        def eq(got, exp, tol=1e-6):
            if isinstance(exp, str):
                return got == exp
            return abs(float(got) - float(exp)) <= tol

        def close(got, exp, tol=0.02):
            return abs(float(got) - float(exp)) <= tol

        # ── RPN four-function (handbook Bsp. 1–6) ──
        case("2 ENTER 3 +", ["2", "=", "3", "+"],
             lambda s: (eq(s["x"], 5) and eq(s["lcd"], "5.00"), f"x={s['x']} lcd={s['lcd']}"))
        case("2 ENTER 3 ×", ["2", "=", "3", MUL],
             lambda s: (eq(s["x"], 6) and eq(s["lcd"], "6.00"), f"x={s['x']}"))
        case("2 ENTER 3 −", ["2", "=", "3", MINUS],
             lambda s: (eq(s["x"], -1) and eq(s["lcd"], "-1.00"), f"x={s['x']}"))
        case("9 ENTER 3 ÷", ["9", "=", "3", DIV],
             lambda s: (eq(s["x"], 3) and eq(s["lcd"], "3.00"), f"x={s['x']}"))
        case("125 ENTER 375 + → 500", ["1", "2", "5", "=", "3", "7", "5", "+"],
             lambda s: (eq(s["x"], 500) and eq(s["lcd"], "500.00"), f"x={s['x']} lcd={s['lcd']}"))
        case("1250 ENTER 450 − → 800", ["1", "2", "5", "0", "=", "4", "5", "0", MINUS],
             lambda s: (eq(s["x"], 800), f"x={s['x']}"))
        case("24 ENTER 15 × → 360", ["2", "4", "=", "1", "5", MUL],
             lambda s: (eq(s["x"], 360), f"x={s['x']}"))
        case("2500 ENTER 25 ÷ → 100", ["2", "5", "0", "0", "=", "2", "5", DIV],
             lambda s: (eq(s["x"], 100), f"x={s['x']}"))
        case("chain 5 ENTER 3 + 2 +", ["5", "=", "3", "+", "2", "+"],
             lambda s: (eq(s["x"], 10), f"x={s['x']}"))
        case("chain (45+55)×2−20 → 180",
             ["4", "5", "=", "5", "5", "+", "2", MUL, "2", "0", MINUS],
             lambda s: (eq(s["x"], 180) and eq(s["lcd"], "180.00"), f"x={s['x']}"))
        case("nested (12+8)÷(5−1) → 5",
             ["1", "2", "=", "8", "+", "5", "=", "1", MINUS, DIV],
             lambda s: (eq(s["x"], 5) and eq(s["lcd"], "5.00"), f"x={s['x']} y={s['y']}"))
        case("Y dropped after binary op", ["5", "=", "3", "+"],
             lambda s: (eq(s["x"], 8) and eq(s["y"], 0), f"x={s['x']} y={s['y']}"))

        # ── Stack machine: ENTER / CLx / lift / T ──
        case("ENTER dup: 7 ENTER → x=y=7", ["7", "="],
             lambda s: (eq(s["x"], 7) and eq(s["y"], 7), f"x={s['x']} y={s['y']}"))
        case("double ENTER: 5 ENTER ENTER → x=y=z=5", ["5", "=", "="],
             lambda s: (eq(s["x"], 5) and eq(s["y"], 5) and eq(s["z"], 5),
                        f"x={s['x']} y={s['y']} z={s['z']}"))
        case("stack fill 1 ENTER 2 ENTER 3 ENTER 4",
             ["1", "=", "2", "=", "3", "=", "4"],
             lambda s: (eq(s["x"], 4) and eq(s["y"], 3) and eq(s["z"], 2) and eq(s["t"], 1),
                        f"x={s['x']} y={s['y']} z={s['z']} t={s['t']}"))
        case("digit after ENTER overwrites X (lift off)",
             ["9", "=", "4"],
             lambda s: (eq(s["x"], 4) and eq(s["y"], 9) and s["lift"] is False,
                        f"x={s['x']} y={s['y']} lift={s['lift']}"))
        case("digit after + lifts (new number)",
             ["2", "=", "3", "+", "9"],
             lambda s: (eq(s["x"], 9) and eq(s["y"], 5),
                        f"x={s['x']} y={s['y']} lift={s['lift']}"))
        case("CLx clears X only; Y stays; next digit overwrites X",
             ["5", "=", "AC", "3"],
             lambda s: (eq(s["x"], 3) and eq(s["y"], 5), f"x={s['x']} y={s['y']}"))
        case("CLx then ENTER still dups", ["4", "AC", "8", "="],
             lambda s: (eq(s["x"], 8) and eq(s["y"], 8), f"x={s['x']} y={s['y']}"))
        case("CLx leaves Z/T intact",
             ["1", "=", "2", "=", "3", "=", "4", "AC"],
             lambda s: (eq(s["x"], 0) and eq(s["y"], 3) and eq(s["z"], 2) and eq(s["t"], 1),
                        f"x={s['x']} y={s['y']} z={s['z']} t={s['t']}"))
        case("T duplicates down after drop (2 ENTER 3 +)",
             ["1", "=", "2", "=", "3", "+", "9", "+"],
             lambda s: (eq(s["x"], 14), f"x={s['x']} y={s['y']} z={s['z']} t={s['t']}"))

        # ── CHS / decimal / LastX / x⇄y / R↓ ──
        case("CHS during entry", ["5", "6", "+/-"],
             lambda s: (eq(s["x"], -56), f"x={s['x']} lcd={s['lcd']}"))
        case("CHS on result", ["9", "=", "+/-"],
             lambda s: (eq(s["x"], -9), f"x={s['x']}"))
        case("CHS after ENTER flips X, Y stays", ["8", "=", "+/-"],
             lambda s: (eq(s["x"], -8) and eq(s["y"], 8), f"x={s['x']} y={s['y']}"))
        case("decimal 1 , 5 ENTER 2 ×", ["1", ",", "5", "=", "2", MUL],
             lambda s: (eq(s["x"], 3), f"x={s['x']} lcd={s['lcd']}"))
        case("leading comma 0,25 × 4", [",", "2", "5", "=", "4", MUL],
             lambda s: (eq(s["x"], 1), f"x={s['x']} lcd={s['lcd']}"))
        case("LastX: 8 ENTER 2 ÷  then g ENTER", ["8", "=", "2", DIV, "g", "="],
             lambda s: (eq(s["x"], 2) and eq(s["y"], 4) and eq(s["lastX"], 2),
                        f"x={s['x']} y={s['y']} lastX={s['lastX']}"))
        case("LastX after × : 6 ENTER 7 × g ENTER",
             ["6", "=", "7", MUL, "g", "="],
             lambda s: (eq(s["x"], 7) and eq(s["y"], 42) and eq(s["lastX"], 7),
                        f"x={s['x']} y={s['y']} lastX={s['lastX']}"))
        case("x⇄y", ["2", "=", "9", "xy"],
             lambda s: (eq(s["x"], 2) and eq(s["y"], 9), f"x={s['x']} y={s['y']}"))
        case("x⇄y twice restores", ["2", "=", "9", "xy", "xy"],
             lambda s: (eq(s["x"], 9) and eq(s["y"], 2), f"x={s['x']} y={s['y']}"))
        case("R↓ after 1 ENTER 2 ENTER 3",
             ["1", "=", "2", "=", "3", "rdn"],
             lambda s: (eq(s["x"], 2) and eq(s["y"], 1) and eq(s["z"], 0) and eq(s["t"], 3),
                        f"x={s['x']} y={s['y']} z={s['z']} t={s['t']}"))
        case("R↓ four times restores stack fill",
             ["1", "=", "2", "=", "3", "=", "4", "rdn", "rdn", "rdn", "rdn"],
             lambda s: (eq(s["x"], 4) and eq(s["y"], 3) and eq(s["z"], 2) and eq(s["t"], 1),
                        f"x={s['x']} y={s['y']} z={s['z']} t={s['t']}"))

        # ── Math (√, 1/x, y^x, e^x, LN, INTG, FRAC, n!) ──
        case("1/x of 4", ["4", "recip"],
             lambda s: (eq(s["x"], 0.25), f"x={s['x']}"))
        case("1/x of 8 → 0.125", ["8", "recip"],
             lambda s: (eq(s["x"], 0.125) and eq(s["lcd"], "0.13"), f"x={s['x']} lcd={s['lcd']}"))
        case("y^x 2 ENTER 3 → 8", ["2", "=", "3", "yx"],
             lambda s: (eq(s["x"], 8), f"x={s['x']}"))
        case("y^x 2 ENTER 8 → 256 (handbook)", ["2", "=", "8", "yx"],
             lambda s: (eq(s["x"], 256) and eq(s["lcd"], "256.00"), f"x={s['x']}"))
        case("√ 9 via g y^x", ["9", "g", "yx"],
             lambda s: (eq(s["x"], 3), f"x={s['x']}"))
        case("√ 144 via g y^x", ["1", "4", "4", "g", "yx"],
             lambda s: (eq(s["x"], 12) and eq(s["lcd"], "12.00"), f"x={s['x']}"))
        case("e^x of 1 ≈ 2.71828", ["1", "g", "recip"],
             lambda s: (close(s["x"], 2.718281828, 1e-8), f"x={s['x']}"))
        case("LN(e) roundtrip ≈ 1", ["1", "g", "recip", "g", "pctt"],
             lambda s: (close(s["x"], 1.0, 1e-9), f"x={s['x']}"))
        case("LN 1.0 = 0", ["1", ",", "0", "g", "pctt"],
             lambda s: (eq(s["x"], 0), f"x={s['x']}"))
        case("INTG 3,7 via g %", ["3", ",", "7", "g", "%"],
             lambda s: (eq(s["x"], 3), f"x={s['x']}"))
        case("INTG of −3,7 via g %", ["3", ",", "7", "+/-", "g", "%"],
             lambda s: (eq(s["x"], -3), f"x={s['x']}"))
        case("FRAC 3,7 via g Δ%", ["3", ",", "7", "g", "dlt"],
             lambda s: (abs(s["x"] - 0.7) < 1e-9, f"x={s['x']}"))
        case("n!  g 3  of 5", ["5", "g", "3"],
             lambda s: (eq(s["x"], 120), f"x={s['x']}"))
        case("n! of 0 = 1", ["0", "g", "3"],
             lambda s: (eq(s["x"], 1), f"x={s['x']}"))
        case("n! of 1 = 1", ["1", "g", "3"],
             lambda s: (eq(s["x"], 1), f"x={s['x']}"))

        # ── 12× / 12÷ ──
        case("12× : 5 g n", ["5", "g", "n"],
             lambda s: (eq(s["x"], 60), f"x={s['x']}"))
        case("12÷ : 36 g i", ["3", "6", "g", "i"],
             lambda s: (eq(s["x"], 3), f"x={s['x']}"))
        case("6,5 ENTER 12 ÷ → monthly 0.5416…",
             ["6", ",", "5", "=", "1", "2", DIV],
             lambda s: (close(s["x"], 6.5 / 12, 1e-9), f"x={s['x']}"))

        # ── % / %T / Δ% (Owner's Handbook) ──
        case("%  200 ENTER 15 % → 30, Y stays 200",
             ["2", "0", "0", "=", "1", "5", "%"],
             lambda s: (eq(s["x"], 30) and eq(s["y"], 200) and eq(s["lcd"], "30.00"),
                        f"x={s['x']} y={s['y']} lcd={s['lcd']}"))
        case("% then + : 200 ENTER 15 % + → 230",
             ["2", "0", "0", "=", "1", "5", "%", "+"],
             lambda s: (eq(s["x"], 230), f"x={s['x']}"))
        case("% then − : 500 ENTER 20 % − → 400",
             ["5", "0", "0", "=", "2", "0", "%", MINUS],
             lambda s: (eq(s["x"], 400), f"x={s['x']}"))
        case("%T  200 ENTER 50 %T → 25",
             ["2", "0", "0", "=", "5", "0", "pctt"],
             lambda s: (eq(s["x"], 25) and eq(s["y"], 200), f"x={s['x']} y={s['y']}"))
        case("Δ%  50000 ENTER 65000 → 30",
             ["5", "0", "0", "0", "0", "=", "6", "5", "0", "0", "0", "dlt"],
             lambda s: (eq(s["x"], 30) and eq(s["y"], 50000), f"x={s['x']} y={s['y']}"))
        case("Δ%  200 ENTER 250 → 25",
             ["2", "0", "0", "=", "2", "5", "0", "dlt"],
             lambda s: (eq(s["x"], 25), f"x={s['x']}"))

        # ── STO / RCL ──
        case("STO 1 / RCL 1", ["4", "2", "sto", "1", "AC", "rcl", "1"],
             lambda s: (eq(s["x"], 42), f"x={s['x']}"))
        case("STO overwrite: 5 STO 1, 9 STO 1, RCL 1 → 9",
             ["5", "sto", "1", "9", "sto", "1", "AC", "rcl", "1"],
             lambda s: (eq(s["x"], 9), f"x={s['x']}"))
        case("STO 0 / RCL 0", ["1", "7", "sto", "0", "AC", "rcl", "0"],
             lambda s: (eq(s["x"], 17), f"x={s['x']}"))
        case("STO 9 / RCL 9", ["8", "8", "sto", "9", "AC", "rcl", "9"],
             lambda s: (eq(s["x"], 88), f"x={s['x']}"))
        case("RCL does not destroy other regs: STO 1 and 2, RCL 1",
             ["1", "1", "sto", "1", "2", "2", "sto", "2", "AC", "rcl", "1"],
             lambda s: (eq(s["x"], 11), f"x={s['x']}"))
        case("handbook (5×8) STO1 (12×3) RCL1 + → 76",
             ["5", "=", "8", MUL, "sto", "1", "1", "2", "=", "3", MUL, "rcl", "1", "+"],
             lambda s: (eq(s["x"], 76), f"x={s['x']}"))

        # ── Errors + ON ──
        case("÷0 Error", ["8", "=", "0", DIV],
             lambda s: (s["lcd"].startswith("Error"), f"lcd={s['lcd']}"))
        case("1/x of 0 → Error", ["0", "recip"],
             lambda s: (s["lcd"].startswith("Error"), f"lcd={s['lcd']}"))
        case("√ of −9 → Error", ["9", "+/-", "g", "yx"],
             lambda s: (s["lcd"].startswith("Error"), f"lcd={s['lcd']}"))
        case("ON resets stack", ["9", "=", "3", "+", "mode"],
             lambda s: (eq(s["x"], 0) and eq(s["y"], 0), f"x={s['x']} y={s['y']}"))
        case("ON after Error recovers to 0.00",
             ["8", "=", "0", DIV, "mode"],
             lambda s: (eq(s["x"], 0) and eq(s["lcd"], "0.00"), f"x={s['x']} lcd={s['lcd']}"))
        case("ON clears financial registers",
             ["1", "0", "n", "5", "i", "mode"],
             lambda s: (eq(s["n"], 0) and eq(s["i"], 0), f"n={s['n']} i={s['i']}"))

        # ── Display FIX 2 ──
        case("FIX 2 default lcd", ["1", "=", "3", DIV],
             lambda s: (s["lcd"] == "0.33", f"lcd={s['lcd']}"))
        case("FIX 2 of 1,005 → 1.01 or 1.00 (IEEE)",
             ["1", ",", "0", "0", "5"],
             lambda s: (s["lcd"] in ("1.01", "1.00", "1.005"), f"lcd={s['lcd']}"))
        case("negative lcd has minus", ["7", "+/-"],
             lambda s: (s["lcd"].startswith("-") and "7" in s["lcd"], f"lcd={s['lcd']}"))

        # ── Prefix f / g ──
        case("prefix f clears after next key", ["f", "xy"],
             lambda s: (s["f"] is False, f"f={s['f']}"))
        case("prefix g sets then clears after n!",
             ["5", "g", "3"],
             lambda s: (s["g"] is False and eq(s["x"], 120), f"g={s['g']} x={s['x']}"))
        case("AMORT f n on loaded loan: 1 ENTER 12 periods → interest number",
             ["4", "8", "n", "1", "i", "1", "0", "0", "0", "0", "pv",
              "2", "6", "3", ",", "3", "4", "+/-", "pmt", "0", "fv",
              "1", "=", "1", "2", "f", "n"],
             lambda s: (not str(s["lcd"]).startswith("Error") and abs(float(s["x"])) > 1,
                        f"x={s['x']} lcd={s['lcd']} pv={s['pv']}"))

        # ── BEGIN / END ──
        case("BEGIN indicator g 7", ["g", "7"],
             lambda s: (s["begin"] == "BEGIN", f"mode={s['begin']}"))
        case("END indicator g 8", ["g", "8"],
             lambda s: (s["begin"] == "END", f"mode={s['begin']}"))
        case("default payment mode is END", [],
             lambda s: (s["begin"] == "END", f"mode={s['begin']}"))

        # ── TVM store / solve ──
        case("TVM store PV i PMT FV",
             ["1", "0", "0", "0", "0", "pv", "1", "i", "3", "0", "0", "+/-", "pmt", "0", "fv"],
             lambda s: (eq(s["pv"], 10000) and eq(s["i"], 1) and eq(s["pmt"], -300) and eq(s["fv"], 0),
                        f"pv={s['pv']} i={s['i']} pmt={s['pmt']} fv={s['fv']}"))
        case("TVM solve n (ceil 40.75→41, physical 12C)",
             ["1", "0", "0", "0", "0", "pv", "1", "i", "3", "0", "0", "+/-", "pmt", "0", "fv", "n"],
             lambda s: (eq(s["x"], 41) and eq(s["lcd"], "41.00") and eq(s["n"], 41),
                        f"x={s['x']} lcd={s['lcd']} nreg={s['n']}"))
        case("TVM solve PMT 48 n 1 i 10000 PV 0 FV",
             ["4", "8", "n", "1", "i", "1", "0", "0", "0", "0", "pv", "0", "fv", "pmt"],
             lambda s: (close(s["x"], -263.3383543192775, 0.02), f"pmt x={s['x']}"))
        case("TVM solve PV 48 n 1 i −263.34 PMT 0 FV ≈ +10000 (inflow)",
             ["4", "8", "n", "1", "i", "2", "6", "3", ",", "3", "4", "+/-", "pmt", "0", "fv", "pv"],
             lambda s: (close(s["x"], 10000, 2.0), f"pv x={s['x']}"))
        case("TVM solve FV 12 n 1 i −1000 PV 0 PMT",
             ["1", "2", "n", "1", "i", "1", "0", "0", "0", "+/-", "pv", "0", "pmt", "fv"],
             lambda s: (close(s["x"], 1000 * (1.01 ** 12), 0.05), f"fv x={s['x']}"))
        case("TVM solve i : 3 n −10000 PV 0 PMT 15000 FV ≈ 14.47%",
             ["3", "n", "1", "0", "0", "0", "0", "+/-", "pv", "0", "pmt", "1", "5", "0", "0", "0", "fv", "i"],
             lambda s: (close(s["x"], 14.471443, 0.05) and close(s["i"], 14.471443, 0.05),
                        f"i x={s['x']} ireg={s['i']}"))
        case("TVM doubling at 8%: n = ceil(ln2/ln1.08) = 10",
             ["8", "i", "1", "0", "0", "0", "+/-", "pv", "2", "0", "0", "0", "fv", "0", "pmt", "n"],
             lambda s: (eq(s["x"], 10) and eq(s["n"], 10), f"x={s['x']} nreg={s['n']}"))
        case("TVM i=0 : 10 n 0 i 100 PV 0 FV → PMT = −10",
             ["1", "0", "n", "0", "i", "1", "0", "0", "pv", "0", "fv", "pmt"],
             lambda s: (eq(s["x"], -10), f"pmt x={s['x']}"))
        case("TVM mortgage 360 n 0,5 i 100000 PV 0 FV → PMT ≈ −599.55",
             ["3", "6", "0", "n", "0", ",", "5", "i", "1", "0", "0", "0", "0", "0", "pv", "0", "fv", "pmt"],
             lambda s: (close(s["x"], -599.55, 0.05), f"pmt x={s['x']} lcd={s['lcd']}"))
        case("TVM 6,5 ENTER 12 ÷ i stores 0.5416… (not solve)",
             ["6", ",", "5", "=", "1", "2", DIV, "i"],
             lambda s: (close(s["i"], 6.5 / 12, 1e-9) and close(s["x"], 6.5 / 12, 1e-9),
                        f"i={s['i']} x={s['x']} lcd={s['lcd']}"))
        case("TVM savings 60 n 4 ENTER 12 ÷ i 0 PV 50000 FV → PMT ≈ −754.16",
             ["6", "0", "n", "4", "=", "1", "2", DIV, "i", "0", "pv", "5", "0", "0", "0", "0", "fv", "pmt"],
             lambda s: (close(s["x"], -754.16, 0.05), f"pmt x={s['x']} i={s['i']}"))
        case("TVM house 360 n 6,5 ENTER 12 ÷ i 350000 PV → PMT ≈ −2212.24 (IEEE; handbook −2212.75 BCD)",
             ["3", "6", "0", "n", "6", ",", "5", "=", "1", "2", DIV, "i",
              "3", "5", "0", "0", "0", "0", "pv", "0", "fv", "pmt"],
             lambda s: (close(s["x"], -2212.24, 0.05), f"pmt x={s['x']} lcd={s['lcd']} i={s['i']}"))
        case("RCL n after TVM store",
             ["4", "1", "n", "rcl", "n"],
             lambda s: (eq(s["x"], 41) and eq(s["n"], 41), f"x={s['x']} n={s['n']}"))
        case("STO 0 independent of n (R0 ≠ n)",
             ["9", "n", "5", "sto", "0", "rcl", "n"],
             lambda s: (eq(s["x"], 9) and eq(s["n"], 9), f"x={s['x']} n={s['n']}"))
        case("FIX 4 of 1 ENTER 3 ÷ → 0.3333",
             ["1", "=", "3", DIV, "f", "4"],
             lambda s: (s["lcd"] == "0.3333", f"lcd={s['lcd']}"))
        case("RND f PMT : 1,239 → 1.24 at FIX 2",
             ["1", ",", "2", "3", "9", "f", "pmt"],
             lambda s: (eq(s["x"], 1.24) and s["lcd"] == "1.24", f"x={s['x']} lcd={s['lcd']}"))
        case("NPV: −10000 CF0, 4000 CFj, 4 Nj, 10 i → ≈ 2679.46",
             ["1", "0", "0", "0", "0", "+/-", "g", "pv",
              "4", "0", "0", "0", "g", "pmt",
              "4", "g", "fv",
              "1", "0", "i", "f", "pv"],
             lambda s: (close(s["x"], 2679.46, 0.05), f"npv x={s['x']} lcd={s['lcd']}"))
        case("IRR of same cashflows ≈ 21.86%",
             ["1", "0", "0", "0", "0", "+/-", "g", "pv",
              "4", "0", "0", "0", "g", "pmt",
              "4", "g", "fv", "f", "fv"],
             lambda s: (close(s["x"], 21.86, 0.15), f"irr x={s['x']} i={s['i']}"))

        # BEGIN vs END: annuity-due vs ordinary. Same loan, |PMT_BEGIN| < |PMT_END|.
        tap("mode")
        tap("1", "2", "n", "1", "i", "1", "0", "0", "0", "pv", "0", "fv", "pmt")
        end_pmt = snap()["x"]
        tap("mode")
        tap("g", "7", "1", "2", "n", "1", "i", "1", "0", "0", "0", "pv", "0", "fv", "pmt")
        begin_snap = snap()
        begin_pmt = begin_snap["x"]
        results.append({
            "name": "TVM BEGIN vs END: |PMT_BEGIN| < |PMT_END| and both negative",
            "ok": (end_pmt < 0 and begin_pmt < 0 and abs(begin_pmt) < abs(end_pmt)
                   and begin_snap["begin"] == "BEGIN"),
            "detail": f"END={end_pmt} BEGIN={begin_pmt} mode={begin_snap['begin']}",
            "s": begin_snap,
        })

        # ── Casio isolation (algebra L→R, not RPN) ──
        page.evaluate("() => CasioCalc.setModel('casio')")
        tap("AC", "2", "+", "3", MUL, "4", "=")
        casio = page.locator("#display").inner_text()
        results.append({
            "name": "Casio still L→R 2+3×4=20",
            "ok": casio == "20",
            "detail": f"lcd={casio}",
            "s": {},
        })

        page.evaluate("() => CasioCalc.setModel('hp12c')")
        tap("mode", "2", "=", "3", "+")
        hp_again = page.locator("#display").inner_text()
        results.append({
            "name": "HP still RPN after Casio round-trip 2 ENTER 3 + → 5.00",
            "ok": hp_again == "5.00",
            "detail": f"lcd={hp_again}",
            "s": {},
        })

        browser.close()

    failed = [r for r in results if not r["ok"]]
    print(f"\nENGINE {len(results) - len(failed)}/{len(results)} OK")
    for r in results:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  {mark} {r['name']:<62} {r['detail']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
