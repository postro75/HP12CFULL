# CASIO SL-300

Działający kalkulator biurkowy w stylu Casio: srebrne klawisze 3D, złote operatory, przecinek polski.

**Live:** https://casio-kalkulator.vercel.app

## Uruchomienie

Otwórz `index.html` albo:

```bash
python3 -m http.server 8765
```

E2E:

```bash
python3 tests/e2e_liczy.py
```

Klawiatura laptopa działa (`Enter`, `Escape`, `*`, `/`, `.`).

## Aplikacja na Maca

```bash
./macos/build.sh
open ~/Applications/CASIO\ SL-300.app
```

Apka ląduje w `~/Applications/CASIO SL-300.app` (natywne okno WebKit, bez przeglądarki).
