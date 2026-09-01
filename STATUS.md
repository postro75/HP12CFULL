# Stan końcowy HP12CFULL (2026-09-01)

Test na żywo: https://hp12cfull.vercel.app/?model=hp12c  
Repo: https://github.com/postro75/HP12CFULL · `main`

Owner’s Handbook 1992: Function Key Index (68) + Programming Key Index (10) = **78** nazwanych operacji.

| Sprawdzenie | Wynik na Vercelu |
|---|---|
| 78/78 indeks instrukcji | OK |
| 39/39 klawiszy na zdjęciu | klik OK |
| 18/18 złotych `f` | klik OK |
| 84/84 jak człowiek (klawiatura laptopa + palec w zdjęcie) | OK |
| PMT hipoteki 360 n / 0,5 i / 100000 PV | −599.55 |
| AMORT 12 f n (przykład 50 000 / 13,25%) | −6608.89 / −271.31 / PV 49728.69 |

Klawiatura laptopa: `0–9` `.` `,` `Enter` `+` `-` `*` `/` `%` `Escape` `n` `i` `f` `g` `p` `m` `v` `s` `r`. CHS, EEX, yˣ, złote nakładki — klik w zdjęcie.

To nie jest cyfrowa kopia BCD 12C. PSE bez pauzy 1 s, BST bez przytrzymania, MEM bez mapy P-xx, brak GTO., IEEE zamiast BCD (350k/6,5%/360: −2212.24 vs −2212.75).
