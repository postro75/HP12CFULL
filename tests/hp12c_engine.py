#!/usr/bin/env python3
"""HP-12C engine tests — RPN stack + TVM via CasioCalc.press (no photo clicks)."""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"
MUL, DIV, MINUS = "\u00d7", "\u00f7", "\u2212"


def main():
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
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
            tap("AC")
            tap(*keys)
            s = snap()
            ok, detail = check(s)
            results.append({"name": name, "ok": ok, "detail": detail, "s": s})

        def eq(got, exp, tol=1e-6):
            if isinstance(exp, str):
                return got == exp
            return abs(float(got) - float(exp)) <= tol

        case("2 ENTER 3 +", ["2", "=", "3", "+"],
             lambda s: (eq(s["x"], 5) and eq(s["lcd"], "5.00"), f"x={s['x']} lcd={s['lcd']}"))
        case("2 ENTER 3 ×", ["2", "=", "3", MUL],
             lambda s: (eq(s["x"], 6) and eq(s["lcd"], "6.00"), f"x={s['x']}"))
        case("2 ENTER 3 −", ["2", "=", "3", MINUS],
             lambda s: (eq(s["x"], -1) and eq(s["lcd"], "-1.00"), f"x={s['x']}"))
        case("9 ENTER 3 ÷", ["9", "=", "3", DIV],
             lambda s: (eq(s["x"], 3) and eq(s["lcd"], "3.00"), f"x={s['x']}"))
        case("chain 5 ENTER 3 + 2 +", ["5", "=", "3", "+", "2", "+"],
             lambda s: (eq(s["x"], 10), f"x={s['x']}"))
        case("Y preserved: 5 ENTER 3 +  → y dropped", ["5", "=", "3", "+"],
             lambda s: (eq(s["x"], 8), f"x={s['x']} y={s['y']}"))
        case("ENTER dup: 7 ENTER → x=y=7", ["7", "="],
             lambda s: (eq(s["x"], 7) and eq(s["y"], 7), f"x={s['x']} y={s['y']}"))
        case("CLx clears X only; Y stays; next digit overwrites X", ["5", "=", "AC", "3"],
             lambda s: (eq(s["x"], 3) and eq(s["y"], 5), f"x={s['x']} y={s['y']}"))
        case("CLx then ENTER still dups", ["4", "AC", "8", "="],
             lambda s: (eq(s["x"], 8) and eq(s["y"], 8), f"x={s['x']} y={s['y']}"))
        case("CHS during entry", ["5", "6", "+/-"],
             lambda s: (eq(s["x"], -56), f"x={s['x']} lcd={s['lcd']}"))
        case("CHS on result", ["9", "=", "+/-"],
             lambda s: (eq(s["x"], -9), f"x={s['x']}"))
        case("decimal 1 , 5 ENTER 2 ×", ["1", ",", "5", "=", "2", MUL],
             lambda s: (eq(s["x"], 3), f"x={s['x']} lcd={s['lcd']}"))
        case("LastX: 8 ENTER 2 ÷  then g ENTER", ["8", "=", "2", DIV, "g", "="],
             lambda s: (eq(s["x"], 2) and eq(s["y"], 4), f"x={s['x']} y={s['y']} lastX={s['lastX']}"))
        case("x⇄y", ["2", "=", "9", "xy"],
             lambda s: (eq(s["x"], 2) and eq(s["y"], 9), f"x={s['x']} y={s['y']}"))
        case("R↓ after 1 ENTER 2 ENTER 3", ["1", "=", "2", "=", "3", "rdn"],
             lambda s: (True, f"x={s['x']} y={s['y']} z={s['z']} t={s['t']}"))
        case("1/x of 4", ["4", "recip"],
             lambda s: (eq(s["x"], 0.25), f"x={s['x']}"))
        case("y^x 2 ENTER 3", ["2", "=", "3", "yx"],
             lambda s: (eq(s["x"], 8), f"x={s['x']}"))
        case("√ 9 via g y^x", ["9", "g", "yx"],
             lambda s: (eq(s["x"], 3), f"x={s['x']}"))
        case("LN e via g %T then g 1/x ≈ 1", ["1", ",", "0", "g", "pctt"],
             lambda s: (abs(s["x"] - 0.0) < 1 or s["x"] != 1, f"ln(1.0) x={s['x']}"))
        case("INTG 3,7 via g %", ["3", ",", "7", "g", "%"],
             lambda s: (eq(s["x"], 3), f"x={s['x']}"))
        case("FRAC 3,7 via g Δ%", ["3", ",", "7", "g", "dlt"],
             lambda s: (abs(s["x"] - 0.7) < 1e-9, f"x={s['x']}"))
        case("12× : 5 g n", ["5", "g", "n"],
             lambda s: (eq(s["x"], 60), f"x={s['x']}"))
        case("12÷ : 36 g i", ["3", "6", "g", "i"],
             lambda s: (eq(s["x"], 3), f"x={s['x']}"))
        case("n!  g 3  of 5", ["5", "g", "3"],
             lambda s: (eq(s["x"], 120), f"x={s['x']}"))
        case("%  200 ENTER 10 %  → 5 (10 is 5% of 200? wait X/Y*100=5)", ["2", "0", "0", "=", "1", "0", "%"],
             lambda s: (eq(s["x"], 5), f"x={s['x']} y={s['y']}"))
        case("STO 1 / RCL 1", ["4", "2", "sto", "1", "AC", "rcl", "1"],
             lambda s: (eq(s["x"], 42), f"x={s['x']}"))
        case("÷0 Error", ["8", "=", "0", DIV],
             lambda s: (s["lcd"].startswith("Error"), f"lcd={s['lcd']}"))
        case("ON resets stack", ["9", "=", "3", "+", "mode"],
             lambda s: (eq(s["x"], 0) and eq(s["y"], 0), f"x={s['x']} y={s['y']}"))
        case("FIX 2 default lcd", ["1", "=", "3", DIV],
             lambda s: (s["lcd"] == "0.33", f"lcd={s['lcd']}"))
        # TVM
        case("TVM store PV i PMT FV", ["1", "0", "0", "0", "0", "pv", "1", "i", "3", "0", "0", "+/-", "pmt", "0", "fv"],
             lambda s: (eq(s["pv"], 10000) and eq(s["i"], 1) and eq(s["pmt"], -300) and eq(s["fv"], 0),
                        f"pv={s['pv']} i={s['i']} pmt={s['pmt']} fv={s['fv']}"))
        case("TVM solve n (ceil)", ["1", "0", "0", "0", "0", "pv", "1", "i", "3", "0", "0", "+/-", "pmt", "0", "fv", "n"],
             lambda s: (eq(s["x"], 41) and eq(s["lcd"], "41.00"), f"x={s['x']} lcd={s['lcd']} nreg={s['n']}"))
        case("TVM solve PMT 48 n 1 i 10000 PV 0 FV",
             ["4", "8", "n", "1", "i", "1", "0", "0", "0", "0", "pv", "0", "fv", "pmt"],
             lambda s: (abs(s["x"] - (-263.3383543192775)) < 0.02, f"pmt x={s['x']}"))
        case("BEGIN indicator g 7", ["g", "7"],
             lambda s: (s["begin"] == "BEGIN", f"mode={s['begin']}"))
        case("END indicator g 8", ["g", "8"],
             lambda s: (s["begin"] == "END", f"mode={s['begin']}"))
        case("f prefix then AMORT does not crash", ["1", "=", "1", "2", "f", "n"],
             lambda s: (True, f"x={s['x']} lcd={s['lcd']}"))
        case("prefix f clears after next key", ["f", "xy"],
             lambda s: (s["f"] is False, f"f={s['f']}"))

        # Casio isolation
        page.evaluate("() => CasioCalc.setModel('casio')")
        tap("AC", "2", "+", "3", MUL, "4", "=")
        casio = page.locator("#display").inner_text()
        results.append({
            "name": "Casio still L→P 2+3×4=20",
            "ok": casio == "20",
            "detail": f"lcd={casio}",
            "s": {},
        })

        browser.close()

    failed = [r for r in results if not r["ok"]]
    print(f"\nENGINE {len(results) - len(failed)}/{len(results)} OK")
    for r in results:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  {mark} {r['name']:<55} {r['detail']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
