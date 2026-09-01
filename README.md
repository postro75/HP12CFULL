# CASIO SL-300

Działający kalkulator biurkowy w stylu Casio: srebrne klawisze 3D, złote operatory, przecinek polski.

**Live:** https://casio-kalkulator.vercel.app  
**HP-12C:** https://casio-kalkulator.vercel.app/?model=hp12c  
**TI-30Xa:** https://casio-kalkulator.vercel.app/?model=ti30xa

**Test (HP12CFULL):** https://hp12cfull.vercel.app  
**Test HP-12C:** https://hp12cfull.vercel.app/?model=hp12c  
**Test TI-30Xa:** https://hp12cfull.vercel.app/?model=ti30xa

## Uruchomienie

Otwórz `index.html` albo:

```bash
python3 -m http.server 8765
```

E2E:

```bash
python3 tests/hp12c_78.py       # 78 operacji z indeksów Owner's Handbook 1992
python3 tests/hp12c_engine.py   # HP-12C RPN/TVM silnik
python3 tests/hp12c_ux.py       # hotspoty na zdjęciu HP12C.png
python3 tests/e2e_liczy.py      # Casio algebra L→P
```

Klawiatura laptopa działa (`Enter`, `Escape`, `*`, `/`, `.`). Na modelu HP-12C dodatkowo `n` `i` `f` `g` `p` (PV) `m` (PMT) `v` (FV) `s` (STO) `r` (RCL).

## Aplikacja na Maca

```bash
./macos/build.sh
open ~/Applications/CASIO\ SL-300.app
```

Apka ląduje w `~/Applications/CASIO SL-300.app` (natywne okno WebKit, bez przeglądarki).
