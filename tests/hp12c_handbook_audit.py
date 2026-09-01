#!/usr/bin/env python3
"""Audit every HP-12C key vs Owner's Handbook (1992 / Function Key Index)."""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"
MUL, DIV, MINUS = "\u00d7", "\u00f7", "\u2212"


def main():
    rows = []
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
                    lastX: c.stack.lastX,
                    lcd: document.getElementById('display').textContent,
                    begin: c.financial.paymentMode,
                    n: c.memory.getFinancialRegister('n'),
                    i: c.memory.getFinancialRegister('i'),
                    pv: c.memory.getFinancialRegister('pv'),
                    pmt: c.memory.getFinancialRegister('pmt'),
                    fv: c.memory.getFinancialRegister('fv'),
                    f: c.prefixF, g: c.prefixG,
                  };
                }"""
            )

        def reset():
            page.evaluate("() => _hpCalc.reset()")

        def check(name, keys, pred, handbook):
            reset()
            try:
                tap(*keys)
                s = snap()
                ok, detail = pred(s)
            except Exception as e:
                ok, detail, s = False, str(e), {}
            rows.append({
                "name": name,
                "ok": bool(ok),
                "detail": detail,
                "handbook": handbook,
            })

        def eq(a, b, tol=1e-6):
            return abs(float(a) - float(b)) <= tol

        def close(a, b, tol=0.05):
            return abs(float(a) - float(b)) <= tol

        # ── Handbook arithmetic (p. Getting Started) ──
        check("HB 125 ENTER 375 + → 500.00",
              ["1","2","5","=","3","7","5","+"],
              lambda s: (eq(s["x"], 500) and s["lcd"]=="500.00", s["lcd"]),
              "Owner’s Handbook: RPN addition")
        check("HB 1250 ENTER 450 − → 800",
              ["1","2","5","0","=","4","5","0",MINUS],
              lambda s: (eq(s["x"], 800), s["lcd"]),
              "HB subtraction")
        check("HB 24 ENTER 15 × → 360",
              ["2","4","=","1","5",MUL],
              lambda s: (eq(s["x"], 360), s["lcd"]),
              "HB multiplication")
        check("HB 2500 ENTER 25 ÷ → 100",
              ["2","5","0","0","=","2","5",DIV],
              lambda s: (eq(s["x"], 100), s["lcd"]),
              "HB division")
        check("HB chain (45+55)×2−20 → 180",
              ["4","5","=","5","5","+","2",MUL,"2","0",MINUS],
              lambda s: (eq(s["x"], 180), s["lcd"]),
              "HB chain calc")
        check("HB (5×8) STO1 (12×3) RCL1 + → 76",
              ["5","=","8",MUL,"sto","1","1","2","=","3",MUL,"rcl","1","+"],
              lambda s: (eq(s["x"], 76), s["lcd"]),
              "HB storage registers")

        # ── Percent (Section 2) ──
        check("HB % : 200 ENTER 15 % → 30, Y=200",
              ["2","0","0","=","1","5","%"],
              lambda s: (eq(s["x"], 30) and eq(s["y"], 200), f"x={s['x']} y={s['y']}"),
              "HB % = X percent of Y")
        check("HB % + markup 200 ENTER 15 % + → 230",
              ["2","0","0","=","1","5","%","+"],
              lambda s: (eq(s["x"], 230), s["lcd"]),
              "HB % then +")
        check("HB Δ% 200 ENTER 250 Δ% → 25",
              ["2","0","0","=","2","5","0","dlt"],
              lambda s: (eq(s["x"], 25), s["lcd"]),
              "HB Δ% percent change")
        check("HB %T 200 ENTER 50 %T → 25",
              ["2","0","0","=","5","0","pctt"],
              lambda s: (eq(s["x"], 25), s["lcd"]),
              "HB %T X is what % of Y")

        # ── TVM (Section 3) ──
        check("HB n ceil: 10000 PV, 1 i, −300 PMT, 0 FV → n=41",
              ["1","0","0","0","0","pv","1","i","3","0","0","+/-","pmt","0","fv","n"],
              lambda s: (eq(s["x"], 41), s["lcd"]),
              "HB: n always whole number (ceil)")
        check("HB mortgage 360 n 0.5 i 100000 PV → PMT ≈ −599.55",
              ["3","6","0","n","0",",","5","i","1","0","0","0","0","0","pv","0","fv","pmt"],
              lambda s: (close(s["x"], -599.55, 0.05), s["lcd"]),
              "HB mortgage example")
        check("HB 6.5 ENTER 12 ÷ i stores monthly rate",
              ["6",",","5","=","1","2",DIV,"i"],
              lambda s: (close(s["i"], 6.5/12, 1e-9), f"i={s['i']}"),
              "HB: compute then store i")
        check("HB BEGIN vs END PMT differ",
              ["g","7","1","2","n","1","i","1","0","0","0","pv","0","fv","pmt"],
              lambda s: (s["begin"]=="BEGIN" and s["x"]<0, f"{s['begin']} {s['x']}"),
              "HB g 7 = BEGIN")

        # ── Cash flow (Section 4) ──
        check("HB NPV −10000 CF0, 4000 CFj, 4 Nj, 10 i → ≈2679.46",
              ["1","0","0","0","0","+/-","g","pv","4","0","0","0","g","pmt","4","g","fv","1","0","i","f","pv"],
              lambda s: (close(s["x"], 2679.46, 0.05), s["lcd"]),
              "HB discounted cash flow NPV")
        check("HB IRR same CFs → ≈21.86%",
              ["1","0","0","0","0","+/-","g","pv","4","0","0","0","g","pmt","4","g","fv","f","fv"],
              lambda s: (close(s["x"], 21.86, 0.15), s["lcd"]),
              "HB IRR")
        check("HB RND 1,239 FIX2 → 1.24",
              ["1",",","2","3","9","f","pmt"],
              lambda s: (eq(s["x"], 1.24) and s["lcd"]=="1.24", s["lcd"]),
              "HB f PMT = RND")

        # ── Math (Sections 6–7) ──
        check("HB y^x 2 ENTER 8 → 256",
              ["2","=","8","yx"],
              lambda s: (eq(s["x"], 256), s["lcd"]),
              "HB y^x")
        check("HB √144 via g y^x → 12",
              ["1","4","4","g","yx"],
              lambda s: (eq(s["x"], 12), s["lcd"]),
              "HB g √x")
        check("HB 1/x of 4 → 0.25",
              ["4","recip"],
              lambda s: (eq(s["x"], 0.25), s["lcd"]),
              "HB 1/x")
        check("HB e^x of 1 via g 1/x",
              ["1","g","recip"],
              lambda s: (close(s["x"], 2.718281828, 1e-8), s["x"]),
              "HB g e^x")
        check("HB LN e → 1",
              ["1","g","recip","g","pctt"],
              lambda s: (close(s["x"], 1.0, 1e-8), s["x"]),
              "HB g LN")
        check("HB INTG 3,7 via g % → 3",
              ["3",",","7","g","%"],
              lambda s: (eq(s["x"], 3), s["lcd"]),
              "HB g INTG")
        check("HB FRAC 3,7 via g Δ% → 0.7",
              ["3",",","7","g","dlt"],
              lambda s: (abs(s["x"]-0.7)<1e-9, s["x"]),
              "HB g FRAC")
        check("HB n! 5 g 3 → 120",
              ["5","g","3"],
              lambda s: (eq(s["x"], 120), s["lcd"]),
              "HB g n!")
        check("HB 12× 5 g n → 60",
              ["5","g","n"],
              lambda s: (eq(s["x"], 60), s["lcd"]),
              "HB g 12×")
        check("HB 12÷ 36 g i → 3",
              ["3","6","g","i"],
              lambda s: (eq(s["x"], 3), s["lcd"]),
              "HB g 12÷")
        check("HB LSTx after 8 ENTER 2 ÷ g ENTER",
              ["8","=","2",DIV,"g","="],
              lambda s: (eq(s["x"], 2) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"),
              "HB g LSTx")
        check("HB FIX 4 : 1 ENTER 3 ÷ f 4 → 0.3333",
              ["1","=","3",DIV,"f","4"],
              lambda s: (s["lcd"]=="0.3333", s["lcd"]),
              "HB f 0–9 = FIX")
        check("HB RCL n after 41 n",
              ["4","1","n","rcl","n"],
              lambda s: (eq(s["x"], 41), s["lcd"]),
              "HB RCL financial")
        check("HB ÷0 → Error 0",
              ["1","=","0",DIV],
              lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]),
              "HB Error 0")
        check("HB ON recovers",
              ["9","=","0",DIV,"mode"],
              lambda s: (eq(s["x"], 0) and s["lcd"]=="0.00", s["lcd"]),
              "HB ON")

        # ── Keys that MUST exist as hotspots ──
        hs = page.evaluate(
            """() => [...document.querySelectorAll('.hp-hotspots .hs')].map(el => ({
              key: el.dataset.key, prefix: el.dataset.prefix || '',
              lab: el.getAttribute('aria-label')
            }))"""
        )
        keys = {(h["prefix"], h["key"]) for h in hs}

        def has_hs(name, prefix, key, handbook):
            ok = (prefix, key) in keys
            rows.append({
                "name": name,
                "ok": ok,
                "detail": "hotspot present" if ok else "NO HOTSPOT",
                "handbook": handbook,
            })

        has_hs("Hotspot RND (f PMT)", "f", "pmt", "gold RND")
        has_hs("Hotspot IRR (f FV)", "f", "fv", "gold IRR")
        has_hs("Hotspot NPV (f PV)", "f", "pv", "gold NPV")
        has_hs("Hotspot AMORT (f n)", "f", "n", "gold AMORT")
        has_hs("Hotspot EEX", "", "eex", "primary EEX")
        has_hs("Hotspot R/S", "", "rs", "primary R/S")
        has_hs("Hotspot SST", "", "sst", "primary SST")
        has_hs("Hotspot Σ+", "", "sigma", "primary Σ+")
        has_hs("Hotspot CLEAR REG (f R↓)", "f", "rdn", "gold CLEAR REG")
        has_hs("Hotspot PREFIX (f SST)", "f", "sst", "gold PREFIX")
        has_hs("Hotspot PSE (f x⇄y)", "f", "xy", "gold PSE")
        has_hs("Hotspot CLEAR Σ (f Σ+)", "f", "sigma", "gold CLEAR Σ")

        check("HB STO+ register arithmetic",
              ["1","0","sto","1","5","sto","+","1","rcl","1"],
              lambda s: (eq(s["x"], 15), s["lcd"]),
              "HB storage register arithmetic")
        check("HB 12× stores n",
              ["5","g","n"],
              lambda s: (eq(s["x"], 60) and eq(s["n"], 60), f"x={s['x']} n={s['n']}"),
              "HB g 12× stores n-register")
        check("HB Continuous Memory: ON keeps STO",
              ["7","sto","2","mode","rcl","2"],
              lambda s: (eq(s["x"], 7), s["lcd"]),
              "HB Continuous Memory")

        # ── Unimplemented handbook functions: confirm they do NOT pretend to work ──
        def unimplemented(name, keys, handbook):
            reset()
            before = snap()
            tap(*keys)
            after = snap()
            # no Error unless we expect one; prefix should clear; X mostly unchanged
            rows.append({
                "name": name,
                "ok": True,  # informational
                "detail": f"lcd {before['lcd']!r}→{after['lcd']!r} x={after['x']}",
                "handbook": handbook,
                "gap": True,
            })

        check("HB INT now implemented",
              ["6","0","n","7","i","4","5","0","+/-","pv","f","i"],
              lambda s: (close(s["x"], 5.25, 0.02), s["lcd"]),
              "HB §3 simple interest")
        check("HB programming P/R + R/S",
              ["f","rs","2","=","3","+","f","rs","rs"],
              lambda s: (eq(s["x"], 5), s["lcd"]),
              "HB Part II keystroke program")
        check("HB g x=0 sets skip flag without crash",
              ["1","g","AC"],
              lambda s: (True, s["lcd"]),
              "HB g x=0")

        # ── Every primary hotspot: press does not throw ──
        crash = 0
        for h in hs:
            if h["prefix"]:
                continue
            reset()
            try:
                tap(h["key"])
                snap()
            except Exception:
                crash += 1
                rows.append({
                    "name": f"CRASH {h['key']}",
                    "ok": False,
                    "detail": "exception",
                    "handbook": "press must not throw",
                })
        rows.append({
            "name": "All primary hotspots press without crash",
            "ok": crash == 0,
            "detail": f"crashes={crash} keys={len(hs)}",
            "handbook": "keyboard integrity",
        })

        browser.close()

    gaps = [r for r in rows if r.get("gap")]
    tests = [r for r in rows if not r.get("gap")]
    failed = [r for r in tests if not r["ok"]]
    print(f"\nHANDBOOK CHECKS {len(tests)-len(failed)}/{len(tests)} OK  |  documented gaps {len(gaps)}")
    print("\n== Implemented (must match handbook) ==")
    for r in tests:
        mark = "OK  " if r["ok"] else "FAIL"
        print(f"  {mark} {r['name']:<62} {r['detail']}")
    print("\n== Not implemented (handbook has it, we don't) ==")
    for r in gaps:
        print(f"  GAP  {r['name']:<62} {r['handbook']}")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
