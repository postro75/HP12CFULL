#!/usr/bin/env python3
"""E2E: klika prawdziwe klawisze Casio i sprawdza LCD."""

from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8765/"


def lcd(page):
    return page.locator("#display").inner_text().strip()


def tap(page, *keys):
    for key in keys:
        page.locator(f'button.key[data-key="{key}"]').click()


def case(page, keys, expect, name):
    tap(page, "AC")
    tap(page, *keys)
    got = lcd(page)
    ok = got == expect
    return {"name": name, "seq": " ".join(keys), "expect": expect, "got": got, "ok": ok}


def engine_case(page, keys, expect, name):
    got = page.evaluate(
        """keys => {
          CasioCalc.press('AC');
          keys.forEach(k => CasioCalc.press(k));
          return document.getElementById('display').textContent;
        }""",
        keys,
    )
    return {
        "name": name,
        "seq": " ".join(keys),
        "expect": expect,
        "got": got,
        "ok": got == expect,
    }


def main():
    specs = [
        (["7", "+", "8", "="], "15", "dodawanie"),
        (["9", "−", "4", "="], "5", "odejmowanie"),
        (["6", "×", "7", "="], "42", "mnożenie"),
        (["1", "0", "0", "÷", "4", "="], "25", "dzielenie"),
        (["1", "2", ",", "5", "+", "3", "="], "15,5", "przecinek PL"),
        (["2", "+", "3", "×", "4", "="], "20", "od lewej, bez priorytetu ×"),
        (["1", "+", "2", "+", "3", "="], "6", "łańcuch +"),
        (["8", "÷", "2", "÷", "2", "="], "2", "łańcuch ÷"),
        (["5", "+", "3", "=", "="], "11", "= powtarza działanie"),
        (["5", "+", "3", "=", "=", "="], "14", "potrójne ="),
        (["5", "0", "%"], "0,5", "% unarne"),
        (["2", "0", "0", "+", "1", "0", "%", "="], "220", "200+10%"),
        (["2", "0", "0", "−", "1", "0", "%", "="], "180", "200-10%"),
        (["2", "0", "0", "×", "1", "0", "%", "="], "20", "200×10%"),
        (["2", "0", "0", "÷", "1", "0", "%", "="], "2 000", "200÷10%"),
        (["1", "2", "3", "4", "+/-"], "-1234", "zmiana znaku"),
        (["5", "+/-", "+", "3", "="], "-2", "ujemna + 3"),
        (["8", "÷", "0", "="], "Błąd", "dzielenie przez zero"),
        ([","], "0,", "przecinek na starcie"),
        (["0", ",", "1", "+", "0", ",", "2", "="], "0,3", "0,1+0,2"),
        (["1", "2", "3", "4", "×", "1", "0", "0", "0", "="], "1 234 000", "grupowanie tysięcy"),
        (["5", "+", "×", "3", "="], "15", "zamiana operatora + na ×"),
        (["5", "+", "5", "=", "2"], "2", "cyfra po = zaczyna nową liczbę"),

        # --- trudniejsze ---
        (["5", "+", "="], "10", "5+=  (operand użyty dwa razy)"),
        (["5", "×", "="], "25", "5×=  (kwadrat)"),
        (["5", "+", "=", "="], "15", "5+= =  (10+5)"),
        (["5", "×", "=", "="], "125", "5×= =  (25×5)"),
        (["2", "×", "=", "×", "="], "16", "×= potem ×= kwadratuje (2→4→16)"),
        (["3", "−", "5", "="], "-2", "wynik ujemny"),
        (["3", "−", "5", "+/-", "="], "8", "3−(−5)"),
        (["5", "+", "+/-", "="], "0", "5+(−5)"),
        (["0", "÷", "0", "="], "Błąd", "0÷0"),
        (["0", "÷", "1", "="], "0", "0÷1"),
        (["1", "÷", "0", "="], "Błąd", "1÷0"),
        (["8", "+/-", "÷", "0", "="], "Błąd", "ujemna ÷0"),
        (["0", "−", "1", "="], "-1", "0−1"),
        (["0", "×", "5", "="], "0", "0×5"),
        (["1", "÷", "3", "="], "0,333333333333", "1÷3 okres"),
        (["1", "÷", "3", "×", "3", "="], "1", "1÷3×3 wraca do 1"),
        (["2", "÷", "3", "="], "0,666666666667", "2÷3"),
        (["1", "0", "÷", "3", "="], "3,33333333333", "10÷3"),
        (["1", "÷", "7", "×", "7", "="], "1", "1÷7×7 wraca do 1"),
        (["0", ",", "1", "×", "0", ",", "1", "="], "0,01", "0,1×0,1"),
        (["9"] * 12 + ["+", "1", "="], "1,000000e+12", "12 dziewiątek +1 → sci"),
        (["1"] + ["0"] * 12 + ["×", "2", "="], "2,000000e+12", "10^12 × 2"),
        (["9"] * 15 + ["×", "2", "="], "2,000000e+15", "15 dziewiątek ×2 overflow sci"),
        ([","] + ["0"] * 8 + ["1"], "0,000000001", "wpis 1e-9"),
        ([","] + ["0"] * 8 + ["1", "×", "1", "="], "1,000000e-9", "1e-9 ×1 → sci"),
        (["9"] * 15, "999999999999999", "limit 15 cyfr"),
        (["9"] * 16, "999999999999999", "16. cyfra obcięta"),
        (["1", ",", ",", "2"], "1,2", "podwójny przecinek ignorowany"),
        (["0", "0", "5"], "5", "zera wiodące"),
        ([",", "="], "0", "sam przecinek + ="),
        (["="], "0", "samo ="),
        (["+/-"], "0", "+/− na zerze"),
        (["0", ",", "5", "+/-"], "-0,5", "znak ułamka"),
        (["0", ",", "5", "+/-", "+", "0", ",", "5", "="], "0", "−0,5+0,5"),
        (["5", "+/-", "×", "4", "+/-", "="], "20", "ujemna × ujemna"),
        (["1", "+/-", "×", "1", "+/-", "="], "1", "−1×−1"),
        (["0", "%"], "0", "0%"),
        (["1", "0", "0", "+", "1", "0", "0", "%", "="], "200", "100+100%"),
        (["2", "0", "0", "+", "5", "0", "%", "+", "1", "0", "="], "110", "% nie woła =; 100+10"),
        (["1", "0", "%", "%"], "0,001", "10% dwa razy"),
        (["1", "0", "0", "%", "%", "%"], "0,0001", "100% trzy razy"),
        (["2", "0", "0", "=", "%"], "2", "% po = (200/100)"),
        (["5", "+", "5", "=", "+", "3", "="], "13", "kontynuacja po ="),
        (["5", "+", "3", "=", "AC", "="], "0", "AC kasuje powtórzenie ="),
        (["5", "+", "AC", "2", "+", "2", "="], "4", "AC w środku działania"),
        (["1", "0", "−", "3", "×", "2", "+", "4", "÷", "2", "="], "9", "łańcuch mieszany 10-3×2+4÷2"),
        (["1", "+", "2", "−", "3", "×", "4", "÷", "5", "="], "0", "1+2-3×4÷5 od lewej =0"),
        (["7", "+", "8", "−", "9", "×", "2", "="], "12", "7+8-9×2 od lewej =12"),
        (["1", "0", "−", "1", "0", "−", "1", "0", "="], "-10", "10-10-10"),
        (["1", "2", "3", "4", "5", "6", "7", ",", "8", "9"], "1234567,89", "wpis bez spacji"),
        (["1", "2", "3", "4", "5", "6", "7", ",", "8", "9", "="], "1 234 567,89", "grupowanie po ="),
        (["9"] * 9 + ["×", "9", "="], "8 999 999 991", "999999999×9"),
        (["9", "÷", "0", "=", "+"], "Błąd", "operator po Błąd zablokowany"),
        (["5", "+", "5", "=", "mode"], "10", "ikona trybu nie psuje wyniku"),
    ]

    # Te same press() co przyciski, bez 80s klików — trudniejsze brzegi.
    engine_specs = [
        (["5", "−", "="], "0", "5−=  → 0"),
        (["5", "−", "=", "="], "-5", "5−= =  → −5"),
        (["5", "÷", "="], "1", "5÷=  → 1"),
        (["5", "÷", "=", "="], "0,2", "5÷= =  → 0,2"),
        (["1", "0", "÷", "2", "=", "=", "="], "1,25", "10÷2===  5→2,5→1,25"),
        (["1", "÷", "3", "=", "="], "0,111111111111", "1÷3= =  dzieli jeszcze raz przez 3"),
        (["5", "+", "3", "=", "+", "="], "16", "8+8 po = + ="),
        (["5", "+", "3", "=", "×", "="], "64", "8×8 po = × ="),
        (["5", "+", "−", "×", "+", "2", "="], "7", "seria operatorów, zostaje +"),
        (["5", "+", "+", "+", "2", "="], "7", "+++ nie psuje"),
        (["1", "2", ",", "="], "12", "trailing comma = 12"),
        (["1", "2", ",", "+", "3", "="], "15", "12, + 3"),
        ([",", "5", "+", ",", "5", "="], "1", ",5+,5"),
        (["0", "0", "0", ",", "5"], "0,5", "000,5"),
        (["1", ",", "0", "0", "0"], "1,000", "1,000 to 1,000 nie tysiąc"),
        (["1", ",", "0", "0", "0", "="], "1", "1,000= → 1"),
        (["2", "0", "0", "+/-", "+", "1", "0", "%", "="], "-220", "−200+10%"),
        (["2", "0", "0", "+/-", "−", "1", "0", "%", "="], "-180", "−200−10%"),
        (["2", "0", "0", "+/-", "×", "1", "0", "%", "="], "-20", "−200×10%"),
        (["5", "0", "%", "+", "5", "0", "%", "="], "0,75", "50%+50% = 0,5+0,25"),
        (["2", "0", "0", "+", "1", "0", "%"], "20", "200+10% bez = pokazuje 20"),
        (["2", "0", "0", "−", "1", "0", "%"], "20", "200−10% bez = pokazuje 20"),
        (["2", "0", "0", "+", "1", "0", "%", "5"], "5", "cyfra po % zaczyna nową liczbę"),
        (["1", "2", "3", "=", "+/-"], "-123", "+/− po ="),
        (["8", "+", "2", "=", "+/-", "×", "2", "="], "-20", "zmiana znaku wyniku ×2"),
        (["2", "2", "÷", "7", "="], "3,14285714286", "22÷7"),
        (["1", "0", "0", "÷", "5", "÷", "4", "÷", "5", "="], "1", "100÷5÷4÷5"),
        (["9", "÷", "9", "÷", "9", "="], "0,111111111111", "9÷9÷9"),
        (["1", "2", "3", "+", "0", "="], "123", "identyczność +0"),
        (["1", "2", "3", "−", "0", "="], "123", "identyczność −0"),
        (["1", "2", "3", "×", "1", "="], "123", "identyczność ×1"),
        (["1", "2", "3", "÷", "1", "="], "123", "identyczność ÷1"),
        (["9", "×", "0", "+", "5", "="], "5", "×0 potem +5"),
        (["9", "−", "9", "+", "9", "−", "9", "="], "0", "9-9+9-9"),
        (["1"] + ["+", "1"] * 9 + ["="], "10", "dziesięć jedynek dodanych"),
        (["1", "0", "0", "0", "0", "0", "0", "+", "1", "0", "0", "0", "0", "0", "0", "="], "2 000 000", "1 000 000+1 000 000"),
        (["1", "2", "3", "4", "5", "6", "7", "+/-", "="], "-1 234 567", "grupowanie ujemnej"),
        (["+", "="], "0", "+ = na zerze"),
        (["×", "="], "0", "× = na zerze"),
        (["1"] + ["0"] * 12 + ["+", "1", "="], "1,000000e+12", "1e12+1 gubi jedynkę w sci"),
        ([","] + ["0"] * 8 + ["1", "+", ","] + ["0"] * 8 + ["1", "="], "2,000000e-9", "1e-9+1e-9"),
        (["1"] * 10 + [","] + ["2"] * 5, "1111111111,22222", "15 cyfr z przecinkiem"),
        (["1"] * 10 + [","] + ["2"] * 6, "1111111111,22222", "16. cyfra po przecinku obcięta"),
        (["1", "÷", "3", "×", "3", "−", "1", "="], "0", "1÷3×3−1"),
        (["5", "0", "%", "×", "4", "="], "2", "50%×4"),
        (["2", ",", "5", "×", "2", ",", "5", "="], "6,25", "2,5²"),
        (["0", ",", "0", "0", "1", "×", "0", ",", "0", "0", "1", "="], "0,000001", "0,001²"),
        (["1", "+", "2", "+", "3", "=", "="], "9", "1+2+3= =  (6+3)"),
        (["7", "÷", "2", "="], "3,5", "7÷2"),
        (["7", "÷", "2", "=", "="], "1,75", "7÷2= ="),
        (["1", "0", "−", "3", "=", "="], "4", "10−3= ="),
        (["mode", "2", "+", "2", "="], "4", "mode na starcie"),
        (["8", "+/-", "+/-"], "8", "podwójny +/− wraca"),
        (["9", "×", "0", "÷", "0", "="], "Błąd", "9×0÷0"),
        (["1", "÷", "8", "×", "8", "="], "1", "1÷8×8"),
        (["9", "9", ",", "9", "9", "+", "0", ",", "0", "1", "="], "100", "99,99+0,01"),
        (["0", ",", "1", "+", "0", ",", "2", "+", "0", ",", "3", "="], "0,6", "0,1+0,2+0,3"),
        (["0", ",", "1", "+/-", "×", "1", "0", "="], "-1", "−0,1×10"),
        (["1", "0", "0", "0", "÷", "8", "="], "125", "1000÷8"),
        (["2"] + ["×", "2"] * 9 + ["="], "1 024", "2×2 dziewięć razy = 2^10"),
    ]

    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(channel="chrome", headless=True)
        except Exception:
            browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 430, "height": 900})
        page.goto(BASE, wait_until="domcontentloaded")
        page.locator("#display").wait_for()

        results = []
        assert lcd(page) == "0", f"start LCD={lcd(page)!r}"
        results.append({"name": "start 0", "seq": "", "expect": "0", "got": lcd(page), "ok": True})

        for keys, expect, name in specs:
            results.append(case(page, keys, expect, name))

        for keys, expect, name in engine_specs:
            results.append(engine_case(page, keys, expect, name))

        # cyfra po Błąd nie może nic zmienić
        tap(page, "AC", "8", "÷", "0", "=", "7")
        got = lcd(page)
        results.append({
            "name": "cyfra po Błąd ignorowana",
            "seq": "8 ÷ 0 = 7",
            "expect": "Błąd",
            "got": got,
            "ok": got == "Błąd",
        })
        tap(page, "AC")
        results.append({
            "name": "AC po Błąd",
            "seq": "AC",
            "expect": "0",
            "got": lcd(page),
            "ok": lcd(page) == "0",
        })

        # klawiatura laptopa
        tap(page, "AC")
        page.keyboard.type("78")
        page.keyboard.press("+")
        page.keyboard.type("9")
        page.keyboard.press("Enter")
        results.append({
            "name": "klawiatura 78+9 Enter",
            "seq": "keyboard",
            "expect": "87",
            "got": lcd(page),
            "ok": lcd(page) == "87",
        })
        page.keyboard.press("Escape")
        results.append({
            "name": "Escape = AC",
            "seq": "Esc",
            "expect": "0",
            "got": lcd(page),
            "ok": lcd(page) == "0",
        })

        tap(page, "AC")
        page.keyboard.type("12.5+3")
        page.keyboard.press("Enter")
        results.append({
            "name": "klawiatura kropka jako przecinek",
            "seq": "12.5+3 Enter",
            "expect": "15,5",
            "got": lcd(page),
            "ok": lcd(page) == "15,5",
        })
        tap(page, "AC")
        page.keyboard.type("8")
        page.keyboard.press("Minus")
        page.keyboard.type("3")
        page.keyboard.press("Enter")
        results.append({
            "name": "klawiatura minus",
            "seq": "8-3 Enter",
            "expect": "5",
            "got": lcd(page),
            "ok": lcd(page) == "5",
        })
        tap(page, "AC")
        page.keyboard.type("6*7")
        page.keyboard.press("Enter")
        results.append({
            "name": "klawiatura gwiazdka",
            "seq": "6*7 Enter",
            "expect": "42",
            "got": lcd(page),
            "ok": lcd(page) == "42",
        })
        tap(page, "AC")
        page.keyboard.type("9/3")
        page.keyboard.press("Enter")
        results.append({
            "name": "klawiatura slash",
            "seq": "9/3 Enter",
            "expect": "3",
            "got": lcd(page),
            "ok": lcd(page) == "3",
        })
        tap(page, "AC")
        page.keyboard.type("100")
        page.keyboard.press("Backspace")
        results.append({
            "name": "Backspace = AC",
            "seq": "100 Backspace",
            "expect": "0",
            "got": lcd(page),
            "ok": lcd(page) == "0",
        })
        tap(page, "AC")
        page.keyboard.type("3,5*2")
        page.keyboard.press("Enter")
        results.append({
            "name": "klawiatura przecinek PL",
            "seq": "3,5*2 Enter",
            "expect": "7",
            "got": lcd(page),
            "ok": lcd(page) == "7",
        })
        tap(page, "AC")
        page.keyboard.press("Equal")
        results.append({
            "name": "klawiatura samo Equal",
            "seq": "=",
            "expect": "0",
            "got": lcd(page),
            "ok": lcd(page) == "0",
        })

        browser.close()

    failed = [r for r in results if not r["ok"]]
    print(f"E2E {len(results) - len(failed)}/{len(results)} OK")
    for r in results:
        mark = "OK " if r["ok"] else "FAIL"
        print(f"  {mark}  {r['name']:<28}  {r['seq']:<22}  LCD={r['got']!r}  (oczekiwane {r['expect']!r})")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
