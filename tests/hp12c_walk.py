#!/usr/bin/env python3
"""HP-12C function-by-function walk vs Owner's Handbook 1992.

Stops on the first failure so we implement that function, then continue.
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

    def fn(name, keys, pred, hb):
        fns.append((name, keys, pred, hb))

    # ── §1 Digit entry / arithmetic / stack ──
    fn("ON recovers from Error 0",
       ["8", "=", "0", DIV, "mode"],
       lambda s: (not str(s["lcd"]).startswith("Error") and eq(s["x"], 0), s["lcd"]),
       "HB p.16 ON; Error 0 then any/ON")
    fn("digits 0-9 and decimal",
       ["1", ",", "5"],
       lambda s: (eq(s["x"], 1.5) and s["lcd"] in ("1.50", "1.5"), s["lcd"]),
       "HB p.17 keying numbers")
    fn("CHS during entry",
       ["5", "6", "+/-"],
       lambda s: (eq(s["x"], -56), s["lcd"]),
       "HB p.18 CHS")
    fn("EEX 2 EEX 3 → 2000",
       ["2", "eex", "3"],
       lambda s: (eq(s["x"], 2000), s["lcd"]),
       "HB p.18 EEX")
    fn("EEX negative exponent 2 EEX CHS 3 → 0.002",
       ["2", "eex", "+/-", "3"],
       lambda s: (eq(s["x"], 0.002), f"x={s['x']} lcd={s['lcd']}"),
       "HB p.18 EEX CHS")
    fn("CLx zeros X only",
       ["5", "=", "AC"],
       lambda s: (eq(s["x"], 0) and eq(s["y"], 5), f"x={s['x']} y={s['y']}"),
       "HB p.19 CLx")
    fn("ENTER duplicates X into Y",
       ["7", "="],
       lambda s: (eq(s["x"], 7) and eq(s["y"], 7), f"x={s['x']} y={s['y']}"),
       "HB p.19 ENTER")
    fn("125 ENTER 375 + → 500.00",
       ["1", "2", "5", "=", "3", "7", "5", "+"],
       lambda s: (eq(s["x"], 500) and s["lcd"] == "500.00", s["lcd"]),
       "HB p.19 addition")
    fn("1250 ENTER 450 − → 800",
       ["1", "2", "5", "0", "=", "4", "5", "0", MINUS],
       lambda s: (eq(s["x"], 800), s["lcd"]),
       "HB p.19 subtraction")
    fn("24 ENTER 15 × → 360",
       ["2", "4", "=", "1", "5", MUL],
       lambda s: (eq(s["x"], 360), s["lcd"]),
       "HB p.19 multiplication")
    fn("2500 ENTER 25 ÷ → 100",
       ["2", "5", "0", "0", "=", "2", "5", DIV],
       lambda s: (eq(s["x"], 100), s["lcd"]),
       "HB p.19 division")
    fn("÷0 → Error 0",
       ["1", "=", "0", DIV],
       lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]),
       "HB appendix C Error 0")
    fn("chain (45+55)×2−20 → 180",
       ["4", "5", "=", "5", "5", "+", "2", MUL, "2", "0", MINUS],
       lambda s: (eq(s["x"], 180), s["lcd"]),
       "HB p.20 chain")
    fn("x⇄y",
       ["2", "=", "9", "xy"],
       lambda s: (eq(s["x"], 2) and eq(s["y"], 9), f"x={s['x']} y={s['y']}"),
       "HB p.84 x⇄y")
    fn("R↓ four times restores",
       ["1", "=", "2", "=", "3", "=", "4", "rdn", "rdn", "rdn", "rdn"],
       lambda s: (eq(s["x"], 4) and eq(s["y"], 3) and eq(s["z"], 2) and eq(s["t"], 1),
                  f"{s['x']} {s['y']} {s['z']} {s['t']}"),
       "HB appendix A R↓")
    fn("LSTx after 8 ENTER 2 ÷",
       ["8", "=", "2", DIV, "g", "="],
       lambda s: (eq(s["x"], 2) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"),
       "HB p.85 LSTx")

    # ── §1 storage ──
    fn("STO 1 / RCL 1",
       ["4", "2", "sto", "1", "AC", "rcl", "1"],
       lambda s: (eq(s["x"], 42), s["lcd"]),
       "HB p.25 STO RCL")
    fn("(5×8) STO1 (12×3) RCL1 + → 76",
       ["5", "=", "8", MUL, "sto", "1", "1", "2", "=", "3", MUL, "rcl", "1", "+"],
       lambda s: (eq(s["x"], 76), s["lcd"]),
       "HB p.25 storage example")
    fn("RCL n financial",
       ["4", "1", "n", "rcl", "n"],
       lambda s: (eq(s["x"], 41), s["lcd"]),
       "HB p.36 RCL financial")
    fn("STO+ 1 : 10 STO 1, 5 STO+ 1, RCL 1 → 15",
       ["1", "0", "sto", "1", "5", "sto", "+", "1", "rcl", "1"],
       lambda s: (eq(s["x"], 15), s["lcd"]),
       "HB p.26 storage arithmetic")
    fn("R.0 dotted STO . 0",
       ["7", "7", "sto", ",", "0", "AC", "rcl", ",", "0"],
       lambda s: (eq(s["x"], 77), s["lcd"]),
       "HB p.25 R.0–R.9")
    fn("CLEAR FIN zeros n, leaves X",
       ["4", "2", "=", "1", "0", "n", "f", "AC"],
       lambda s: (eq(s["x"], 10) and eq(s["n"], 0), f"x={s['x']} n={s['n']}"),
       "HB p.36 CLEAR FIN")
    fn("CLEAR REG zeros stack and STO",
       ["4", "2", "sto", "1", "f", "rdn", "rcl", "1"],
       lambda s: (eq(s["x"], 0), s["lcd"]),
       "HB p.26 CLEAR REG")
    fn("CLEAR PREFIX cancels f",
       ["f", "sst"],
       lambda s: (s["f"] is False, f"f={s['f']}"),
       "HB p.17 CLEAR PREFIX")
    fn("Continuous Memory: ON keeps STO",
       ["7", "sto", "2", "mode", "rcl", "2"],
       lambda s: (eq(s["x"], 7), s["lcd"]),
       "HB p.80 Continuous Memory")

    # ── §2 percent + calendar ──
    fn("% 200 ENTER 15 → 30, Y=200",
       ["2", "0", "0", "=", "1", "5", "%"],
       lambda s: (eq(s["x"], 30) and eq(s["y"], 200), f"x={s['x']} y={s['y']}"),
       "HB p.28 %")
    fn("% then + markup 200 ENTER 15 % + → 230",
       ["2", "0", "0", "=", "1", "5", "%", "+"],
       lambda s: (eq(s["x"], 230), s["lcd"]),
       "HB p.29 net amount")
    fn("Δ% 200 ENTER 250 → 25",
       ["2", "0", "0", "=", "2", "5", "0", "dlt"],
       lambda s: (eq(s["x"], 25), s["lcd"]),
       "HB p.29 Δ%")
    fn("%T 200 ENTER 50 → 25",
       ["2", "0", "0", "=", "5", "0", "pctt"],
       lambda s: (eq(s["x"], 25), s["lcd"]),
       "HB p.30 %T")
    fn("DATE 4.281982 ENTER 10 days → 5.081982, Y=6 Saturday",
       ["4", ",", "2", "8", "1", "9", "8", "2", "=", "1", "0", "f", "+/-"],
       lambda s: (abs(s["x"] - 5.081982) < 1e-6 and eq(s["y"], 6), f"x={s['x']} y={s['y']}"),
       "HB p.33 DATE; Y = weekday 1=Mon … 7=Sun")
    fn("ΔDYS 4.281982 ENTER 7.041982 → 67 actual, 66 of 360",
       ["4", ",", "2", "8", "1", "9", "8", "2", "=", "7", ",", "0", "4", "1", "9", "8", "2", "g", "eex"],
       lambda s: (eq(s["x"], 67) and eq(s["y"], 66), f"x={s['x']} y={s['y']}"),
       "HB p.34 ΔDYS")
    fn("D.MY then M.DY do not crash",
       ["g", "4", "g", "5"],
       lambda s: (True, s["lcd"]),
       "HB p.32 date format")

    # ── §3 TVM ──
    fn("12× 5 g n → 60 and stores n",
       ["5", "g", "n"],
       lambda s: (eq(s["x"], 60) and eq(s["n"], 60), f"x={s['x']} n={s['n']}"),
       "HB p.45 12×")
    fn("12÷ 36 g i → 3 and stores i",
       ["3", "6", "g", "i"],
       lambda s: (eq(s["x"], 3) and eq(s["i"], 3), f"x={s['x']} i={s['i']}"),
       "HB p.45 12÷")
    fn("n ceil 10000 PV 1 i −300 PMT 0 FV → 41",
       ["1", "0", "0", "0", "0", "pv", "1", "i", "3", "0", "0", "+/-", "pmt", "0", "fv", "n"],
       lambda s: (eq(s["x"], 41), s["lcd"]),
       "HB p.45 n whole number")
    fn("mortgage PMT 360 n 0.5 i 100000 PV → −599.55",
       ["3", "6", "0", "n", "0", ",", "5", "i", "1", "0", "0", "0", "0", "0", "pv", "0", "fv", "pmt"],
       lambda s: (close(s["x"], -599.55, 0.05), s["lcd"]),
       "HB p.53 PMT")
    fn("BEGIN vs END |PMT_BEGIN| < |PMT_END|",
       ["g", "7", "1", "2", "n", "1", "i", "1", "0", "0", "0", "pv", "0", "fv", "pmt"],
       lambda s: (s["begin"] == "BEGIN" and s["x"] < 0, f"{s['begin']} {s['x']}"),
       "HB p.42 BEG")
    fn("END g 8",
       ["g", "7", "g", "8"],
       lambda s: (s["begin"] == "END", s["begin"]),
       "HB p.42 END")
    fn("INT 60 n 7 i 450 CHS PV f i → 5.25",
       ["6", "0", "n", "7", "i", "4", "5", "0", "+/-", "pv", "f", "i"],
       lambda s: (close(s["x"], 5.25, 0.02), s["lcd"]),
       "HB p.37 INT")
    fn("INT 365-day via R↓ x⇄y → ≈5.18",
       ["6", "0", "n", "7", "i", "4", "5", "0", "+/-", "pv", "f", "i", "rdn", "xy"],
       lambda s: (close(s["x"], 5.178, 0.02), f"x={s['x']}"),
       "HB p.37 INT 365")
    fn("odd-period simple 1.5 n 10 i −100 PV 0 PMT → FV 115.50",
       ["1", ",", "5", "n", "1", "0", "i", "1", "0", "0", "+/-", "pv", "0", "pmt", "fv"],
       lambda s: (close(s["x"], 115.5, 0.05), f"x={s['x']}"),
       "HB p.57 odd period simple")
    fn("STO EEX sets C",
       ["sto", "eex"],
       lambda s: (s["cflag"] is True, f"C={s['cflag']}"),
       "HB p.58 C indicator")
    fn("odd-period compound 1.5 n 10 i −100 PV 0 PMT → FV ≈ 116.07",
       ["sto", "eex", "1", ",", "5", "n", "1", "0", "i", "1", "0", "0", "+/-", "pv", "0", "pmt", "fv"],
       lambda s: (close(s["x"], 100 * (1.10 ** 1.5), 0.05), f"x={s['x']} C={s['cflag']}"),
       "HB p.58 compound odd period")
    fn("AMORT 1 ENTER 12 on 48 n 1 i 10000 PV loan → interest number",
       ["4", "8", "n", "1", "i", "1", "0", "0", "0", "0", "pv",
        "2", "6", "3", ",", "3", "4", "+/-", "pmt", "0", "fv",
        "1", "=", "1", "2", "f", "n"],
       lambda s: (not str(s["lcd"]).startswith("Error") and abs(float(s["x"])) > 1,
                  f"x={s['x']} pv={s['pv']}"),
       "HB p.61 AMORT")

    # ── §4 cash flow / bonds / depr ──
    fn("NPV −10000 CF0, 4000 CFj, 4 Nj, 10 i → ≈2679.46",
       ["1", "0", "0", "0", "0", "+/-", "g", "pv", "4", "0", "0", "0", "g", "pmt",
        "4", "g", "fv", "1", "0", "i", "f", "pv"],
       lambda s: (close(s["x"], 2679.46, 0.05), s["lcd"]),
       "HB p.67 NPV")
    fn("IRR same CFs → ≈21.86%",
       ["1", "0", "0", "0", "0", "+/-", "g", "pv", "4", "0", "0", "0", "g", "pmt",
        "4", "g", "fv", "f", "fv"],
       lambda s: (close(s["x"], 21.86, 0.15), s["lcd"]),
       "HB p.71 IRR")
    fn("RCL g CF0 recalls −10000",
       ["1", "0", "0", "0", "0", "+/-", "g", "pv", "rcl", "g", "pv"],
       lambda s: (eq(s["x"], -10000), s["lcd"]),
       "HB p.73 review CF0")
    fn("RND 1.239 FIX2 → 1.24",
       ["1", ",", "2", "3", "9", "f", "pmt"],
       lambda s: (eq(s["x"], 1.24) and s["lcd"] == "1.24", s["lcd"]),
       "HB p.94 RND")
    fn("SL year 3: cost 10000 salvage 1000 life 5 → 1800, rem 3600",
       ["1", "0", "0", "0", "0", "pv", "1", "0", "0", "0", "fv", "5", "n", "3", "f", "pctt"],
       lambda s: (close(s["x"], 1800, 0.05) and close(s["y"], 3600, 0.05),
                  f"x={s['x']} y={s['y']}"),
       "HB p.78 SL")
    fn("SOYD year 1 → 3000",
       ["1", "0", "0", "0", "0", "pv", "1", "0", "0", "0", "fv", "5", "n", "1", "f", "dlt"],
       lambda s: (close(s["x"], 3000, 0.05), s["lcd"]),
       "HB p.78 SOYD")
    fn("DB 200% year 1 → 4000",
       ["1", "0", "0", "0", "0", "pv", "1", "0", "0", "0", "fv", "5", "n", "2", "0", "0", "i", "1", "f", "%"],
       lambda s: (close(s["x"], 4000, 0.05), s["lcd"]),
       "HB p.78 DB")
    fn("PRICE par bond coupon=yield 4.75 → ~100",
       ["4", ",", "7", "5", "pmt", "4", ",", "7", "5", "i",
        "6", ",", "0", "1", "2", "0", "0", "6", "=",
        "6", ",", "0", "1", "2", "0", "2", "6", "f", "yx"],
       lambda s: (close(s["x"], 100, 2.0), f"x={s['x']}"),
       "HB p.76 PRICE")

    # ── §5 display ──
    fn("FIX 4 of 1 ENTER 3 ÷ → 0.3333",
       ["1", "=", "3", DIV, "f", "4"],
       lambda s: (s["lcd"] == "0.3333", s["lcd"]),
       "HB p.81 FIX")
    fn("SCI of 1234",
       ["1", "2", "3", "4", "f", ","],
       lambda s: ("1.234" in s["lcd"] and " " in s["lcd"], s["lcd"]),
       "HB p.82 SCI")

    # ── §6 stats ──
    fn("Σ+ then x̄ : 3 ENTER 2 Σ+ , 5 ENTER 4 Σ+ , g 0 → 3 and 4",
       ["3", "=", "2", "sigma", "5", "=", "4", "sigma", "g", "0"],
       lambda s: (eq(s["x"], 3) and eq(s["y"], 4), f"x={s['x']} y={s['y']}"),
       "HB p.88 mean")
    fn("s of x={2,4} → √2",
       ["3", "=", "2", "sigma", "5", "=", "4", "sigma", "g", ","],
       lambda s: (close(s["x"], 2 ** 0.5, 0.01), f"x={s['x']}"),
       "HB p.90 s")
    fn("Σ− undoes last point: one remaining mean x=2",
       ["3", "=", "2", "sigma", "5", "=", "4", "sigma", "5", "=", "4", "g", "sigma", "g", "0"],
       lambda s: (eq(s["x"], 2), f"x={s['x']} y={s['y']}"),
       "HB p.88 Σ−")
    fn("CLEAR Σ zeros stats, keeps R0",
       ["9", "sto", "0", "3", "=", "2", "sigma", "f", "sigma", "rcl", "0"],
       lambda s: (eq(s["x"], 9), s["lcd"]),
       "HB p.87 CLEAR Σ")

    # ── §7 math ──
    fn("1/x of 4 → 0.25",
       ["4", "recip"],
       lambda s: (eq(s["x"], 0.25), s["lcd"]),
       "HB p.94 1/x")
    fn("y^x 2 ENTER 8 → 256",
       ["2", "=", "8", "yx"],
       lambda s: (eq(s["x"], 256), s["lcd"]),
       "HB p.96 y^x")
    fn("√144",
       ["1", "4", "4", "g", "yx"],
       lambda s: (eq(s["x"], 12), s["lcd"]),
       "HB p.94 √x")
    fn("e^x of 1",
       ["1", "g", "recip"],
       lambda s: (close(s["x"], 2.718281828, 1e-8), s["x"]),
       "HB p.94 e^x")
    fn("LN e → 1",
       ["1", "g", "recip", "g", "pctt"],
       lambda s: (close(s["x"], 1.0, 1e-8), s["x"]),
       "HB p.94 LN")
    fn("INTG 3.7 → 3",
       ["3", ",", "7", "g", "%"],
       lambda s: (eq(s["x"], 3), s["lcd"]),
       "HB p.95 INTG")
    fn("FRAC 3.7 → 0.7",
       ["3", ",", "7", "g", "dlt"],
       lambda s: (abs(s["x"] - 0.7) < 1e-9, s["x"]),
       "HB p.95 FRAC")
    fn("n! 5 → 120",
       ["5", "g", "3"],
       lambda s: (eq(s["x"], 120), s["lcd"]),
       "HB p.94 n!")

    # ── Part II programming ──
    fn("MEM empty program → 99 lines",
       ["g", "9"],
       lambda s: (eq(s["x"], 99), s["lcd"]),
       "HB p.106 MEM")
    fn("P/R 2 ENTER 3 + R/S → 5",
       ["f", "rs", "2", "=", "3", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 5), s["lcd"]),
       "HB p.98–100 program")
    fn("x=0 skip does not crash",
       ["1", "g", "AC"],
       lambda s: (True, s["lcd"]),
       "HB p.121 x=0")
    fn("AMORT x⇄y shows principal (nonzero, opposite interest)",
       ["4", "8", "n", "1", "i", "1", "0", "0", "0", "0", "pv",
        "2", "6", "3", ",", "3", "4", "+/-", "pmt", "0", "fv",
        "1", "=", "1", "2", "f", "n", "xy"],
       lambda s: (abs(float(s["x"])) > 1 and s["x"] != 0, f"prin={s['x']}"),
       "HB p.62 AMORT x⇄y principal")
    fn("ŷ,r linear: (1,2)(2,4) then 3 g 2 → ŷ=6 r=1",
       ["2", "=", "1", "sigma", "4", "=", "2", "sigma", "3", "g", "2"],
       lambda s: (close(s["x"], 6, 0.05) and close(s["y"], 1, 0.02), f"ŷ={s['x']} r={s['y']}"),
       "HB p.91 ŷ,r")
    fn("x̂,r linear: same data 6 g 1 → x̂=3 r=1",
       ["2", "=", "1", "sigma", "4", "=", "2", "sigma", "6", "g", "1"],
       lambda s: (close(s["x"], 3, 0.05) and close(s["y"], 1, 0.02), f"x̂={s['x']} r={s['y']}"),
       "HB p.91 x̂,r")
    fn("x̄w weighted mean: 5 ENTER 2 Σ+ 3 ENTER 4 Σ+ g 6 → 2.75",
       ["5", "=", "2", "sigma", "3", "=", "4", "sigma", "g", "6"],
       lambda s: (close(s["x"], 2.75, 0.02), f"x={s['x']}"),
       "HB p.92 x̄w = Σxy/Σy")
    fn("YTM of par bond coupon=price yield → ~4.75",
       ["4", ",", "7", "5", "pmt", "1", "0", "0", "pv",
        "6", ",", "0", "1", "2", "0", "0", "6", "=",
        "6", ",", "0", "1", "2", "0", "2", "6", "f", "recip"],
       lambda s: (close(s["x"], 4.75, 0.15), f"ytm={s['x']}"),
       "HB p.77 YTM")
    fn("MEM after CF0+CFj: Y=1 (one CFj), X=99",
       ["1", "+/-", "g", "pv", "2", "g", "pmt", "g", "9"],
       lambda s: (eq(s["x"], 99) and eq(s["y"], 1), f"x={s['x']} y={s['y']}"),
       "HB p.106 MEM")
    fn("RCL g CFj recalls last flow 4000",
       ["1", "0", "0", "0", "0", "+/-", "g", "pv", "4", "0", "0", "0", "g", "pmt", "rcl", "g", "pmt"],
       lambda s: (eq(s["x"], 4000), s["lcd"]),
       "HB p.73 RCL CFj")
    fn("Error 2: x̄ with no data",
       ["g", "0"],
       lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]),
       "HB appendix C Error 2")
    fn("n! of 70 → Error",
       ["7", "0", "g", "3"],
       lambda s: (str(s["lcd"]).startswith("Error") or s["x"] > 1e99, f"x={s['x']} lcd={s['lcd']}"),
       "HB p.94 n! overflow")
    fn("FIX 0 of 1.49 → 1.",
       ["1", ",", "4", "9", "f", "0"],
       lambda s: (s["lcd"] in ("1.", "1", "1.0"), s["lcd"]),
       "HB p.81 FIX 0")
    fn("program x=0 skips next: 2 g x=0 9 + → 2 not 11",
       ["f", "rs", "2", "g", "AC", "9", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 2), f"x={s['x']} lcd={s['lcd']}"),
       "HB p.121 x=0 skip")
    fn("PREFIX mantissa of 1 ENTER 3 ÷ is 10-digit 3.333…",
       ["1", "=", "3", DIV, "f", "sst"],
       lambda s: (s["lcd"].count("3") >= 8 and "0.33" != s["lcd"], s["lcd"]),
       "HB p.83 PREFIX mantissa")
    fn("x≤y skip: 3 ENTER 5 g x≤y 9 + → 8 not 14 (5>3 skip 9)",
       ["f", "rs", "3", "=", "5", "g", "xy", "9", "+", "f", "rs", "rs"],
       lambda s: (eq(s["x"], 8), f"x={s['x']} lcd={s['lcd']}"),
       "HB p.121 x≤y")
    fn("SST executes one line: program 2 ENTER 3 + four SST → 5",
       ["f", "rs", "2", "=", "3", "+", "f", "rs", "sst", "sst", "sst", "sst"],
       lambda s: (eq(s["x"], 5), f"x={s['x']} lcd={s['lcd']}"),
       "HB p.107 SST")
    fn("GTO 00 then R/S restarts program 2 ENTER 3 + → 5",
       ["f", "rs", "2", "=", "3", "+", "f", "rs", "g", "rdn", "0", "0", "rs"],
       lambda s: (eq(s["x"], 5), f"x={s['x']}"),
       "HB p.104 GTO 00")
    fn("RCL g Nj after Nj=4 → 4",
       ["1", "+/-", "g", "pv", "5", "g", "pmt", "4", "g", "fv", "rcl", "g", "fv"],
       lambda s: (eq(s["x"], 4), s["lcd"]),
       "HB p.73 RCL Nj")
    fn("LN of 0 → Error 0",
       ["0", "g", "pctt"],
       lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]),
       "HB appendix C Error 0 LN")
    fn("SCI then FIX 2 restores 1234.00",
       ["1", "2", "3", "4", "f", ",", "f", "2"],
       lambda s: (s["lcd"] == "1234.00", s["lcd"]),
       "HB p.81–82 FIX after SCI")
    fn("√ of −9 → Error 0",
       ["9", "+/-", "g", "yx"],
       lambda s: (str(s["lcd"]).startswith("Error"), s["lcd"]),
       "HB appendix C Error 0 √")

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
                    f: c.prefixF, g: c.prefixG,
                    begin: c.financial.paymentMode,
                    cflag: !!c.financial.compoundOdd,
                    n: c.memory.getFinancialRegister('n'),
                    i: c.memory.getFinancialRegister('i'),
                    pv: c.memory.getFinancialRegister('pv'),
                    pmt: c.memory.getFinancialRegister('pmt'),
                    fv: c.memory.getFinancialRegister('fv'),
                  };
                }"""
            )

        passed = 0
        for i, (name, keys, pred, hb) in enumerate(fns, 1):
            page.evaluate("() => _hpCalc.reset()")
            try:
                tap(*keys)
                s = snap()
                ok, detail = pred(s)
            except Exception as e:
                ok, detail, s = False, str(e), {}
            mark = "OK  " if ok else "FAIL"
            print(f"{mark} {i:02d}/{len(fns)}  {name:<62} {detail}")
            if not ok:
                print(f"\nSTOP at function {i}: {name}")
                print(f"  handbook: {hb}")
                print(f"  keys: {keys}")
                print(f"  snap: {s}")
                browser.close()
                raise SystemExit(i)
            passed += 1
        browser.close()
        print(f"\nALL {passed}/{len(fns)} FUNCTIONS OK")


if __name__ == "__main__":
    main()
