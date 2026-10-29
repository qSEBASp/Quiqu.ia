# AGENTS.md

Local-first, single-user Valorant match coach. FastAPI + SQLite backend, Next.js 16 App Router frontend. All user-facing copy and coaching text is Spanish.

## Setup

```powershell
python -m venv apps/api/.venv
apps\api\.venv\Scripts\python.exe -m pip install -r apps/api/requirements.txt
npm install                    # root: only concurrently
npm install --prefix apps/web  # web deps are NOT installed by root npm install
Copy-Item apps/api/.env.example apps/api/.env   # optional; demo mode needs no keys
```

Run both servers (Windows-specific venv path):

```powershell
npm run dev
# or: npm run dev:api  /  npm run dev:web
```

- API: `http://127.0.0.1:8000`; web: `http://localhost:3000`.
- Frontend uses `NEXT_PUBLIC_API_URL` (default `http://127.0.0.1:8000`).
- `apps/api/.env` is read relative to `apps/api`, not the repo root. Settings are cached at import: restart uvicorn after editing it.
- No lint/formatter. The verification gate is:

```powershell
npm run test                                                  # pytest, backend only
npm --prefix apps/web run typecheck
npm run build
```

Single test: `apps\api\.venv\Scripts\python.exe -m pytest apps/api/tests/test_demo.py::test_demo_is_deterministic -q`

## Architecture

- Backend flow: `providers/` → Pydantic `MatchData` → `analysis/metrics.py` → `analysis/rules.py` → `analysis/report.py` → SQLAlchemy JSON columns. Routers in `app/routers/` are thin; business logic lives in `app/services.py`.
- Every sync persists matches, insights and a deterministic rules report. `POST /api/matches/{id}/report/ai` regenerates the stored report with an OpenAI-compatible model; without `LLM_API_KEY` it returns 400.
- `POST /api/sync/reanalyze` recalculates insights, derived metrics and rule reports from the stored `rounds`/`metrics` without deleting anything. It keeps reports whose `model != "rules"` (AI reports) and returns `{analyzed, insights, reports, kept_ai}`. Needed because a normal sync skips matches that already exist by ID.
- Rule copy lives in `analysis/messages.py`: 3 deterministic variants per `rule_id`, picked with `sha256(match_id + rule_id)` (no `random`). `rules.py` only builds findings and `report.py` selects up to 5 priorities (max 2 per category); drills come from a separate pool so they never repeat a `fix`. The match page shows only insights that were not already promoted to report priorities ("Otros hallazgos").
- Sync is idempotent by match ID. Demo provider (`demo-01`…) is seeded/deterministic; do not introduce `random` without a fixed seed.
- HenrikDev is the only real-data provider (unofficial v4). Requires an API key, has no tick-by-tick positions, and kill locations/radians are currently ignored. There is no video analysis module yet.
- HenrikDev v4 `ability_casts` are `null` in current payloads. Keep `abilities_used` as `None` in that case and skip the no-utility rule; never coerce unknown casts to `0`.
- Unknown `ability_casts` stay `None` end to end: `util_usage` averages only attack rounds with data, `util_rounds_known` reports coverage, and `attack_no_utility` needs at least 4 known bought attack rounds (3 of them with zero casts) before firing.
- Round side comes from `winning_team_role` (fallback: plant/defuse team). Only keep round-based modes (competitive, unrated, swiftplay, spike rush, premier); DM/TDM/custom matches have no useful rounds.
- HenrikDev sync clears demo `rank_name`/`rank_tier`; rank stays `null` until a real rank lookup is added.
- Strengths ("puntos fuertes") are computed on the fly from stored `metrics` by `analysis/strengths.py`; they are never persisted. Minimum 8 rounds, capped at 3, tier-sorted. `build_overview` aggregates them per `rule_id` (top 5, with `count`/`match_ids`).
- `match_summary` exposes `top_insight`, `top_fix`, `top_insight_category` and `top_insight_severity` picked by `max(severity, metric)`; do not rely on ORM insight order.
- Single `Profile` row with `id=1`; no auth, no multi-user. `provider` in the DB is the runtime source of truth; `PROVIDER` in `.env` only seeds a fresh DB.
- `PUT /api/profile` treats a change to `riot_id`/`tag`/`region`/`provider` as an identity change and wipes matches, insights, reports and goals (`reset_data`), because metrics from different accounts are not comparable. The UI warns before doing it.
- Schema is created with `create_all` on startup; there are no migrations. Changing models requires deleting `apps/api/data/quiqu.db` (or adding a migration).
- `POST /api/sync/reset` deletes all matches/insights/reports, keeps the profile and goals, then re-syncs using the current provider (not necessarily demo). The settings UI labels this as "Borrar historial y resincronizar".
- The API rejects non-loopback `Host` headers and cross-origin mutations, and CORS only allows the local frontend (`FRONTEND_ORIGIN` plus `localhost:3000`/`127.0.0.1:3000`). The web scripts bind Next to `127.0.0.1`; `apps/web/next.config.ts` sets the CSP and security headers. `ENABLE_DOCS=false` hides `/docs`, `/redoc` and `/openapi.json`.
- Frontend server components fetch through `apps/web/lib/server.ts`; it returns `null` on any API failure, which pages render as `OfflineNotice`. Client components are only used for mutations (`SyncButton`, `AccountSwitcher`, `SettingsForm`, `AiButton`).
- The root layout fetches `/api/backdrop` to render the decorative role/agent watermark (`AccountBackdrop`), so the whole route tree is dynamic, including `_not-found`. The fetch is best-effort: if the API is down, the layout renders without the watermark.
- Next 16: dynamic route `params` is a Promise (`app/matches/[id]/page.tsx`), and data pages set `export const dynamic = "force-dynamic"`.

## Conventions and gotchas

- Game-mode labels are normalized in `apps/web/lib/modes.ts` (`GAME_MODES`, `modeInfo()`): Henrik stores English queue names ("Competitive") while demo uses Spanish ("Competitivo"), so always render `modeInfo(match.mode).label`, never the raw string. `MatchesTable` filters by normalized mode id and only lists analyzed modes (plus unknown modes that actually have data).
- Use the local `components/clsx.ts` helper, not the npm `clsx` package.
- Tailwind v4 has no `tailwind.config`; theme tokens live in `app/globals.css` under `@theme`, and shared classes are custom `@utility` (`panel`, `label-xs`, `num`).
- `@/*` maps to `apps/web/*`.
- HenrikDev API keys can be saved through `PUT /api/profile` (stored in SQLite); the LLM key is env-only and has no UI field.
- Current tests are pure unit tests (no DB, network, or fixtures despite `conftest.py`). Do not add DB-touching tests without overriding `DATABASE_URL` before app import or they will use the real dev DB.
- The root `dev:api` script hardcodes the Windows virtualenv path.
- Desktop launcher: `scripts\iniciar-quiqu-oculto.vbs` starts `scripts\iniciar-quiqu.ps1` with a hidden PowerShell window, so the shortcut opens only the Edge app window. The launcher starts dev, opens Edge app mode with `.runtime/edge-profile`, redirects dev output to `.runtime/dev.out.log`/`dev.err.log`, and watches `.runtime/stop`. It exports `QUIQU_STOP_FILE`, which enables `ShutdownButton`; `POST /quit` requires `X-Quiqu-Shutdown: 1` and a same-origin request, then writes the stop signal. `.runtime/` is gitignored. `scripts\crear-acceso-directo.ps1` creates the desktop shortcut (targeting `wscript.exe`) and uses `apps/web/app/favicon.ico`. Manual `npm run dev` has no close button because the env var is absent.
- The launcher is single-instance (named mutex `Global\QuiquIaLauncher`): a second click waits up to 30 s for both ports and then just opens the window, so it never races the first instance for port 3000. If the previous instance does not answer in that time, it kills only this repo's processes (launcher, `uvicorn`, `next dev`/`next-server`, `concurrently`, plus `.runtime/server.pid`) and starts again instead of asking for a PC reboot. Killing `taskkill` targets must stay inside `Stop-QuiquProcessTree`/try-catch: a native stderr under `$ErrorActionPreference = "Stop"` aborts the launcher. Startup aborts with an error (it no longer opens a dead window) when the dev log shows `EADDRINUSE`, `exited with code 1`, `error while attempting to bind` or `Application startup failed`.
- `Open-Quiqu` never creates a second window: if an Edge window is already using `.runtime/edge-profile` (main window with that `--user-data-dir`) it just brings it to the front with `WScript.Shell.AppActivate`. A new window is only opened when the previous one was closed while the servers keep running (closing the Edge window does not stop dev; only the in-page "Cerrar Quiqu.ia" button does).
