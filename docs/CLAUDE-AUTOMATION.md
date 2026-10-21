# Automatyzacja @claude (GitHub Actions + WIF)

Workflow: `.github/workflows/claude-comments.yml` („Claude — wykonaj zadanie”).
Używa oficjalnej akcji `anthropics/claude-code-action` (przypięta do SHA `a5a423f`, tag `v1.0.256`, zgodnie z `v1`)
i natywnego Workload Identity Federation: token OIDC GitHub jest wymieniany na krótkotrwały token Anthropic.
**Nie ma stałego klucza API** (`ANTHROPIC_API_KEY` / `claude_code_oauth_token` nie mogą być ustawione — statyczny
poświadczenie wyłączyłoby federację). Sekrety aplikacji i uwierzytelnianie Claude są rozdzielone: workflow nie czyta żadnych sekretów.

## Wyzwalacze

| Wyzwalacz | Kiedy działa |
|---|---|
| `issue_comment` `[created]` | komentarz w issue lub w rozmowie PR zawiera `@claude` |
| `workflow_dispatch` | ręcznie, z pola `task` (wymagane); tylko `refs/heads/main` |

Brak `pull_request_target`, zdarzeń review i `pull_request_review_comment`. Workflow jest zawsze czytany z `main`.

## Warunki (wszystkie muszą być spełnione)

- `comment.user.id == 52690111` **i** `github.actor_id == 52690111` (właściciel repo),
- autor i nadawca nie są botami (`type != 'Bot'`),
- komentarz zawiera `@claude` (tryb ręczny: `ref == refs/heads/main`),
- dodatkowo oficjalna akcja sprawdza prawa zapisu (write/admin) aktora.

Inni aktorzy, boty i komentarze bez wzmianki: job jest pomijany (skipped), nic się nie uruchamia.

## Limity jednego uruchomienia

`timeout-minutes: 20`, `--max-turns 30`, `--max-budget-usd 2` (flagi CLI Claude Code, przekazane w `claude_args`;
`--max-budget-usd` to szacunek po stronie klienta, wydatek może go nieznacznie przekroczyć).

## Uprawnienia

Poziom workflow: `permissions: {}`. Job: `contents: write`, `pull-requests: write`, `issues: write`, `id-token: write`.
Zmiany i odpowiedzi trafiają do osobnej gałęzi / PR. Claude ma w promptcie zakaz scalania, deployu na produkcję,
pushu do `main` i zmian w `.github/workflows`. Checkout robi domyślną gałąź (zaufany kod z `main`);
gałąź PR pobiera dopiero akcja po weryfikacji uprawnień.

## Użycie

1. Komentarz: w issue lub PR napisz `@claude <polecenie>`.
2. Ręcznie: Actions → „Claude — wykonaj zadanie” → Run workflow (branch `main`) → pole `task`.
3. Preflight bez generacji: zaznacz `dry_run` — sprawdza warunki, zmienne oraz wymianę WIF + `GET /v1/models`; akcja Claude nie jest uruchamiana.

Treść `task` i komentarza nie jest interpolowana w shellu; trafia do akcji jako wejście.

## Wymagana konfiguracja

GitHub Variables (identyfikatory, nie sekrety): `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`,
`ANTHROPIC_SERVICE_ACCOUNT_ID`, `ANTHROPIC_WORKSPACE_ID`.

Reguła federacji w Console (poza repo): `repository_owner=postro75`, `ref=refs/heads/main`, audience `https://api.anthropic.com`,
`event_name` ∈ {push, workflow_dispatch, issue_comment}, a dla `issue_comment` tylko `actor_id=52690111`.

Domyślna ścieżka akcji wymaga zainstalowanej aplikacji Claude GitHub App w repozytorium
(https://github.com/apps/claude) — to ona wystawia token GitHub do komentowania i pushu.

## Ograniczenia

- Nie testowano płatnej generacji (z założenia). Komentarz/zadanie „na żywo” może wymagać dostrojenia `--allowedTools`.
- Tryb ręczny pracuje w trybie automatyzacji akcji; PR otwiera przez `gh pr create` (draft), jeśli token na to pozwala.
- Na komentarzach w PR z forka działa tylko właściciel; nie komentuj `@claude` w PR z forka, którego kodu nie znasz.
