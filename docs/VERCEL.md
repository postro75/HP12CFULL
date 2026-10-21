# Wdrożenie na Vercel (HP12CFULL)

Projekt Vercel **`hp12cfull`** już istnieje (https://hp12cfull.vercel.app). Ten dokument opisuje jego aktualizację,
nie tworzenie nowego projektu. Nie zmieniaj produkcji z gałęzi roboczych — podgląd (Preview) powstaje automatycznie dla PR.

## Architektura

Aplikacja to **czysta strona statyczna** (`index.html`, `models.css`, `hp/*.js`, `assets/`). Nie ma serwera, workera,
crona ani trwałego procesu, więc całość działa na Vercel. Nie ma też kroku build ani zależności npm.

Poza Vercel pozostają warianty desktopowe (nie są hostowane na Vercel):
- Mac `.dmg`: `./macos/build.sh`
- Windows `.zip` (Electron): `./desktop/build-win.sh`

Są wykluczone z wdrożenia przez `.vercelignore` (`desktop`, `macos`, `tests`, `docs`, `.github`, `STATUS.md`).

## Konfiguracja

`vercel.json`: `framework: null`, brak komend install/build (statyczny hosting z katalogu głównego), `cleanUrls`,
nagłówek `Cache-Control: immutable` dla `/assets/*`.

Ustawienia projektu w panelu Vercel (do sprawdzenia ręcznie): Framework Preset = *Other*, Root Directory = `./`,
Output Directory puste (lub `.`), Production Branch = `main`, połączone repo `postro75/HP12CFULL`.

## Zmienne środowiskowe

**Aplikacja nie wymaga żadnych zmiennych środowiskowych ani sekretów na Vercel.**

Osobno, wyłącznie dla GitHub Actions z Claude (nie dla Vercel) — GitHub **Variables** (identyfikatory, nie sekrety):
`ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_SERVICE_ACCOUNT_ID`, `ANTHROPIC_WORKSPACE_ID`.
Uwierzytelnianie Claude idzie przez OIDC/WIF (bez stałych kluczy); szczegóły w `docs/CLAUDE-AUTOMATION.md`.

## Wdrożenie

1. PR do `main` → Vercel tworzy Preview (sprawdź `/` oraz `/?model=hp12c`, `/?model=ti30xa`).
2. Po scaleniu PR (robi to człowiek) Vercel wdraża produkcję automatycznie z `main`.
3. Wycofanie: Vercel → Deployments → poprzednie wdrożenie → *Promote to Production*.

## Testy lokalne (przed PR)

```bash
python3 -m http.server 8765 --bind 127.0.0.1 &
python3 tests/hp12c_engine.py      # RPN/TVM
python3 tests/hp12c_ux.py          # hotspoty, przełącznik modeli
python3 tests/e2e_liczy.py         # Casio + klawiatura
python3 tests/hp12c_78.py          # 78 operacji z indeksu Handbooka
HP12C_BASE="http://127.0.0.1:8765/?model=hp12c" python3 tests/hp12c_human.py   # klawiatura + klik w zdjęcie
```

Wymaga `playwright` (pip) z Chromium zgodnym z wersją pakietu (np. `playwright==1.56.0` przy Chromium 1194).

## Wyniki weryfikacji (2026-10-21, lokalnie)

| Zestaw | Wynik |
|---|---|
| hp12c_engine (RPN/TVM) | 127 OK, 0 błędów |
| hp12c_ux | 88 OK, 0 błędów |
| e2e_liczy (Casio, klawiatura) | 149 OK, 0 błędów |
| hp12c_78 (indeks Handbooka) | 78/78 |
| hp12c_human (klawiatura + klik) | 84/84 |

## Ograniczenia

- Nie mam dostępu do panelu Vercel ani CLI: ustawienia projektu i istnienie Preview trzeba potwierdzić w panelu.
- Brak kroku build — „build WWW” oznacza tu weryfikację, że pliki statyczne serwują się poprawnie (HTTP 200).
- Silnik to IEEE, nie BCD (patrz `STATUS.md`); to ograniczenie funkcjonalne istniejące wcześniej.
