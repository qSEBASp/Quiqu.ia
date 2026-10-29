# quiqu.ia

**Coach local de Valorant que convierte tu historial de partidas en un plan de mejora en español.**

![Backend](https://img.shields.io/badge/backend-FastAPI%20%2B%20SQLite-0f766e)
![Frontend](https://img.shields.io/badge/frontend-Next.js%2016-000000)
![Datos](https://img.shields.io/badge/datos-100%25%20locales-22c55e)
![Idioma](https://img.shields.io/badge/idioma-espa%C3%B1ol-e11d48)

quiqu.ia sincroniza tus partidas, calcula métricas por ronda y las cruza con reglas de coaching para responder a una pregunta concreta: **¿qué deberías corregir en la próxima partida?** Todo se ejecuta en tu PC, con un único usuario y sin autenticación.

- Sin nube, sin cuentas y sin telemetría: los datos viven en `apps/api/data/quiqu.db`.
- Funciona sin claves en **modo demo** (14 partidas deterministas) o con tus partidas reales vía **HenrikDev**.
- El informe principal es determinista y explicable; la IA es una capa **opcional** para reescribirlo.

## Índice

- [Qué es](#qué-es)
- [Funciones](#funciones)
- [Cómo funciona](#cómo-funciona)
- [Inicio rápido](#inicio-rápido)
- [Requisitos](#requisitos)
- [Configuración](#configuración)
- [Uso](#uso)
- [Referencia de la API](#referencia-de-la-api)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Datos y privacidad](#datos-y-privacidad)
- [Desarrollo y verificación](#desarrollo-y-verificación)
- [Lanzador de escritorio](#lanzador-de-escritorio)
- [Problemas comunes](#problemas-comunes)
- [Limitaciones conocidas](#limitaciones-conocidas)
- [Documentación interna](#documentación-interna)
- [Licencia](#licencia)

## Qué es

Las webs de estadísticas te dicen que tienes 190 de ACS; no te dicen que estás forzando compras tras perder la pistola o que mueres primero en ataque. quiqu.ia traduce los números a **hallazgos con severidad**, selecciona los más importantes y los convierte en tareas de práctica concretas.

El resultado son cuatro vistas:

| Vista | Qué muestra |
| --- | --- |
| **Resumen** (`/`) | Winrate, racha, ACS, KAST, K/D, evolución, patrones recurrentes y puntos fuertes. |
| **Partidas** (`/matches`) | Historial filtrable por modo y periodo. |
| **Detalle** (`/matches/[id]`) | Informe, puntos fuertes, métricas, timeline de rondas, otros hallazgos y marcador. |
| **Ajustes** (`/settings`) | Cuenta, proveedor, API key, sincronización, reanálisis y borrado del historial. |

## Funciones

- **Ingesta de partidas** desde `demo` (determinista, sin claves) o `henrik` (API no oficial v4).
- **Métricas por partida y ronda**: ACS, ADR, KAST, HS%, primeras sangres y primeras muertes, trades, clutches, economía, utilidad y un `form_score` agregado.
- **Diagnóstico basado en reglas**: hallazgos con categoría y severidad; el informe de reglas elige hasta 5 prioridades (máximo 2 por categoría) y 3 drills que nunca repiten un `fix`.
- **Puntos fuertes**: se calculan al vuelo desde las métricas, con un mínimo de 8 rondas; no se guardan en la base de datos.
- **Benchmarks por rango**: referencias orientativas para contextualizar ACS, ADR, KAST, HS% y primer contacto.
- **Informe IA opcional**: `POST /api/matches/{id}/report/ai` reescribe el informe con un modelo compatible con OpenAI.
- **Historial idempotente**: la sincronización no duplica partidas y `POST /api/sync/reanalyze` recalcula el análisis sin borrar nada.
- **Exportación CSV**: `GET /api/export/matches.csv` (separador `;`, BOM UTF-8, protegido contra fórmulas).
- **Todo en español**: interfaz y textos de coaching. Las etiquetas de modo se normalizan entre proveedores.

> **Estado del producto**: los endpoints de objetivos (`/api/goals`) y de coach conversacional (`/api/coach/summary`, `/api/coach/chat`) ya existen, pero todavía no tienen interfaz en la web.

## Cómo funciona

```text
Proveedor (demo | HenrikDev)
   └─▶ MatchData (Pydantic)
         └─▶ analysis/metrics.py        métricas por partida y por ronda
               └─▶ analysis/rules.py    hallazgos + severidad
                     ├─▶ analysis/messages.py   copy determinista (3 variantes)
                     └─▶ analysis/report.py     resumen + hasta 5 prioridades + 3 drills
                           └─▶ SQLite ──▶ FastAPI ──▶ Next.js (SSR)
```

Cada sincronización guarda la partida, sus insights y un informe de reglas. La página de la partida muestra solo los insights que **no** se promovieron a prioridades del informe, bajo «Otros hallazgos». Los puntos fuertes se evalúan en cada lectura desde `metrics`, así que cambiar sus umbrales no exige tocar la base de datos.

Cuatro decisiones que conviene conocer:

1. **Determinismo.** Cada texto tiene varias variantes fijas y se elige una con `sha256(match_id + rule_id)`, no con `random`. Dos análisis de la misma partida producen el mismo informe.
2. **Idempotencia.** Las partidas se identifican por su ID; una segunda sincronización omite las que ya existen. Para aplicar cambios del motor de reglas a lo guardado se usa **Reanalizar historial**.
3. **Lo desconocido no es cero.** En HenrikDev, `ability_casts` puede llegar como `null`; se mantiene como desconocido y las reglas de utilidad exigen cobertura mínima antes de activarse.
4. **La IA no sustituye al motor.** Sin `LLM_API_KEY` la app funciona igual; con clave, la IA reescribe el informe a partir de la evidencia calculada. Si no devuelve drills, se usan los del pool determinista.

## Inicio rápido

En Windows (PowerShell), desde la raíz del repo:

```powershell
git clone https://github.com/qSEBASp/Quiqu.ia.git
cd Quiqu.ia

python -m venv apps/api/.venv
apps\api\.venv\Scripts\python.exe -m pip install -r apps/api/requirements.txt

npm install
npm install --prefix apps/web

npm run dev
```

Abre **http://127.0.0.1:3000** y pulsa **Sincronizar**. Sin `.env` ni claves, el modo demo carga 14 partidas de ejemplo; el primer arranque crea el esquema y el perfil por defecto (`qSEBA#EUW`), que puedes cambiar en Ajustes.

En macOS/Linux los scripts raíz no sirven (hardcodean la ruta del venv de Windows). Arranca cada parte a mano:

```bash
python -m venv apps/api/.venv
source apps/api/.venv/bin/activate
pip install -r apps/api/requirements.txt
uvicorn app.main:app --reload --port 8000 --app-dir apps/api

# en otra terminal
npm install --prefix apps/web
npm --prefix apps/web run dev
```

## Requisitos

| Requisito | Versión / nota |
| --- | --- |
| **Windows 10/11** | Recomendado: el lanzador y los scripts raíz usan PowerShell y rutas del venv de Windows. |
| **Python** | 3.11 o superior. |
| **Node.js** | 20.9 o superior (requisito de Next.js 16). |
| **npm** | Incluido con Node. |
| **Edge** | Opcional; solo para el lanzador en modo app. Si no está, se abre el navegador por defecto. |
| **API key de HenrikDev** | Opcional; solo para partidas reales. |
| **Clave LLM** | Opcional; solo para informes y coach con IA. |

## Configuración

### Backend (`apps/api/.env`)

Copia el ejemplo y edita lo que necesites:

```powershell
Copy-Item apps/api/.env.example apps/api/.env
```

| Variable | Por defecto | Para qué |
| --- | --- | --- |
| `PROVIDER` | `demo` | Proveedor inicial (`demo` o `henrik`). Solo siembra una base de datos nueva; después manda el proveedor guardado en el perfil. |
| `DATABASE_URL` | vacío | Si está vacío usa `apps/api/data/quiqu.db`. |
| `HENRIK_API_KEY` | vacío | API key de HenrikDev. También se puede guardar desde Ajustes. |
| `HENRIK_BASE_URL` | `https://api.henrikdev.xyz` | Base de la API de HenrikDev. |
| `LLM_API_KEY` | vacío | Activa los informes con IA. Sin ella, los endpoints de IA devuelven `400`. |
| `LLM_BASE_URL` | `https://api.openai.com/v1` | Cualquier proveedor compatible con OpenAI. |
| `LLM_MODEL` | `gpt-4o-mini` | Modelo usado para reescribir informes y responder al coach. |
| `DEMO_MATCH_COUNT` | `14` | Número de partidas que genera el proveedor demo. |
| `FRONTEND_ORIGIN` | `http://localhost:3000` | Origen extra permitido por CORS (además de `localhost` y `127.0.0.1` en el puerto 3000). |
| `ENABLE_DOCS` | `true` | Expone `/docs`, `/redoc` y `/openapi.json`. Ponlo en `false` para ocultarlos. |

`apps/api/.env` se lee **desde `apps/api/`**, no desde la raíz. La configuración se cachea al importar, así que reinicia `uvicorn` después de cambiarla.

### Frontend

| Variable | Por defecto | Para qué |
| --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | `http://127.0.0.1:8000` | URL de la API. Defínela en `apps/web/.env.local` si cambias el puerto o el host. Se incrusta en el build, así que hay que reiniciar el servidor de Next. |

### Seguridad local

La API rechaza `Host` que no sean `127.0.0.1`/`localhost`, bloquea mutaciones con `Origin` no permitido y limita CORS al frontend local. No está pensada para exponerse en una red o en Internet.

## Uso

### Modo demo

No requiere configuración. El proveedor genera un historial reproducible a partir de `riot_id#tag`; las mismas entradas producen las mismas partidas, métricas e informes. Sirve para probar la app, los tests y los cambios del motor de reglas.

### Conectar tu cuenta real

1. Consigue una API key gratuita en [api.henrikdev.xyz](https://api.henrikdev.xyz).
2. Ve a **Ajustes**, elige **HenrikDev**, introduce tu **Riot ID**, **tag**, **región** y la key.
3. Guarda y pulsa **Sincronizar**.

Cambiar Riot ID, tag, región o proveedor **borra el historial local** (partidas, insights, informes y objetivos), porque los datos de cuentas distintas no son comparables. La interfaz avisa antes de hacerlo. HenrikDev devuelve como máximo las 10 partidas recientes por sincronización y solo se conservan modos con rondas.

### Sincronizar, reanalizar y borrar

| Acción | Qué hace | ¿Borra historial? |
| --- | --- | --- |
| **Sincronizar** | Trae partidas nuevas y las analiza. Omite las que ya existen por ID. | No |
| **Reanalizar historial** | Recalcula métricas derivadas, insights e informes de reglas desde los `rounds`/`metrics` guardados. Conserva los informes generados con IA. | No |
| **Borrar historial y resincronizar** | Elimina partidas, insights e informes, conserva perfil y objetivos y vuelve a sincronizar con el proveedor actual. | Sí |
| **Cambiar de cuenta o proveedor** | Borra partidas, insights, informes y objetivos, y deja el perfil listo para la nueva fuente. | Sí |
| **Borrar `apps/api/data/quiqu.db`** | Elimina todo, incluido el perfil. El esquema se recrea al arrancar. | Sí (todo) |

### Informes con IA

Añade `LLM_API_KEY` (y, si aplica, `LLM_BASE_URL`/`LLM_MODEL`) en `apps/api/.env` y reinicia el backend. En el detalle de cada partida aparecerá **Reescribir con IA**. El prompt obliga al modelo a usar solo la evidencia calculada, a mantener los `rule_id` y a no repetir los informes recientes. Al reanalizar, esos informes se conservan.

## Referencia de la API

Con `ENABLE_DOCS=true`, la documentación interactiva está en `http://127.0.0.1:8000/docs`.

| Método | Ruta | Descripción |
| --- | --- | --- |
| `GET` | `/api/health` | Estado del servicio y proveedor configurado. |
| `GET` / `PUT` | `/api/profile` | Lee o actualiza identidad, región, proveedor y key. |
| `POST` | `/api/sync` | Sincroniza partidas nuevas. |
| `POST` | `/api/sync/reanalyze` | Recalcula el análisis sin borrar datos. |
| `POST` | `/api/sync/reset` | Borra el historial (salvo perfil y objetivos) y resincroniza. |
| `GET` | `/api/overview?mode=&days=` | Agregados, tendencia, patrones, puntos fuertes, economía y objetivos. |
| `GET` | `/api/backdrop` | Rol más jugado, usado por el fondo decorativo del layout. |
| `GET` | `/api/matches?limit=&mode=&days=` | Historial resumido. |
| `GET` | `/api/matches/{id}` | Detalle: métricas, rondas, insights, informe y marcador. |
| `GET` | `/api/matches/{id}/report` | Informe guardado de una partida. |
| `POST` | `/api/matches/{id}/report/ai` | Regenera el informe con IA (requiere `LLM_API_KEY`). |
| `GET` / `POST` | `/api/goals` | Lista o crea objetivos (sin interfaz todavía). |
| `PATCH` / `DELETE` | `/api/goals/{id}` | Actualiza estado o elimina un objetivo. |
| `POST` | `/api/coach/summary` | Diagnóstico global del historial con IA (sin interfaz todavía). |
| `POST` | `/api/coach/chat` | Chat de coaching con contexto del jugador (sin interfaz todavía). |
| `GET` | `/api/export/matches.csv` | Exporta hasta 200 partidas en CSV. |

## Estructura del proyecto

```text
quiqu.ia/
├─ apps/
│  ├─ api/
│  │  ├─ app/
│  │  │  ├─ providers/     # demo.py y henrik.py -> MatchData
│  │  │  ├─ analysis/      # metrics, rules, messages, report, strengths, benchmarks, llm
│  │  │  ├─ routers/       # endpoints finos (profile, sync, matches, stats, goals, coach, export)
│  │  │  ├─ services.py    # sincronización, overview, informes, objetivos, reanálisis
│  │  │  ├─ models.py      # SQLAlchemy: Profile, Match, RankSnapshot, Goal, Insight, Report
│  │  │  └─ security.py    # TrustedHost, CORS y bloqueo de mutaciones cross-site
│  │  ├─ tests/            # pytest, sin DB real (unitarios)
│  │  └─ data/quiqu.db     # generado y gitignored
│  └─ web/
│     ├─ app/              # /, /matches, /matches/[id], /settings
│     ├─ components/       # UI (server components + islas cliente para mutaciones)
│     └─ lib/              # fetch SSR, tipos, formatos y normalización de modos
├─ scripts/                # lanzador oculto, lanzador PowerShell y acceso directo
├─ package.json            # dev/test/build de la raíz
├─ AGENTS.md               # contexto técnico para agentes y colaboradores
└─ README.md
```

El flujo del backend es siempre el mismo: `providers/` → `MatchData` → `analysis/metrics.py` → `analysis/rules.py` → `analysis/report.py` → SQLAlchemy. Los routers no contienen lógica de negocio.

## Datos y privacidad

- **Local por diseño**: no hay autenticación, multi-usuario ni envío de datos a servidores propios. El frontend habla directamente con la API en loopback.
- **SQLite**: un solo archivo en `apps/api/data/quiqu.db` (ignorado por Git). Haz copias de seguridad con el servidor parado.
- **Claves**: la key de HenrikDev se guarda en texto plano en SQLite; la de LLM solo en `apps/api/.env`. No subas `.env` ni la base de datos al repositorio.
- **IA opcional**: si configuras un LLM, el contexto de la partida (métricas, hallazgos, últimas partidas) se envía al proveedor que elijas. Sin clave, nada sale de tu PC.
- **Sin migraciones**: el esquema se crea con `create_all`. Si cambias modelos, borra `quiqu.db` (o añade una migración real).
- **Retención**: el historial se conserva hasta que pulses «Borrar historial y resincronizar», cambies de identidad o borres el archivo.

## Desarrollo y verificación

```powershell
npm run test                     # pytest (solo backend)
npm --prefix apps/web run typecheck
npm run build
```

Test individual:

```powershell
apps\api\.venv\Scripts\python.exe -m pytest apps/api/tests/test_demo.py::test_demo_is_deterministic -q
```

No hay lint ni formatter configurados: la puerta de verificación es la de arriba. Los tests actuales son unitarios (sin DB, red ni fixtures reales); si añades uno que toque la base de datos, sobrescribe `DATABASE_URL` antes de importar la app.

Convenciones que conviene respetar:

- Los textos de coaching viven en `analysis/messages.py` (3 variantes por regla) y las reglas solo construyen hallazgos en `analysis/rules.py`.
- Las etiquetas de modo se normalizan en `apps/web/lib/modes.ts`; nunca renderices el string crudo del proveedor.
- Usa el helper local `components/clsx.ts`, no el paquete `clsx`.
- Tailwind v4 no tiene `tailwind.config`: los tokens están en `app/globals.css` (`@theme`, `@utility`).
- En Next 16, `params` de rutas dinámicas es una `Promise` y las páginas con datos usan `export const dynamic = "force-dynamic"`.

## Lanzador de escritorio

Para abrir la app como ventana independiente y poder cerrarla desde la interfaz:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\crear-acceso-directo.ps1
```

Crea `Quiqu.ia.lnk` en el escritorio. El acceso directo ejecuta `scripts\iniciar-quiqu-oculto.vbs`, que arranca `scripts\iniciar-quiqu.ps1` sin ventana de consola. Al abrirlo:

1. Comprueba dependencias y que los puertos `3000`/`8000` estén libres.
2. Arranca API y web con `npm run dev`.
3. Espera a que ambos respondan y abre Edge en modo app (o el navegador por defecto).
4. Muestra **Cerrar Quiqu.ia** en la barra lateral y en la navegación móvil.

El botón escribe `.runtime/stop`; el lanzador cierra la ventana y el árbol de procesos. Los logs están en `.runtime/quiqu.log`, `.runtime/dev.out.log` y `.runtime/dev.err.log`. El lanzador es de instancia única (mutex `Global\QuiquIaLauncher`): un segundo clic reutiliza la ventana abierta en lugar de competir por el puerto 3000.

Si arrancas solo con `npm run dev`, el botón de cierre no aparece porque no hay lanzador vigilando. Para depurar el arranque con consola visible, ejecuta `scripts\iniciar-quiqu.ps1` a mano. `.runtime/` está ignorado por Git.

## Problemas comunes

| Síntoma | Causa probable | Solución |
| --- | --- | --- |
| La web muestra el aviso de API caída. | El backend no está levantado o cambió el puerto. | Comprueba `http://127.0.0.1:8000/api/health` y `NEXT_PUBLIC_API_URL`. |
| No aparecen partidas nuevas. | La sincronización es idempotente por ID. | Es lo esperado; para recalcular el análisis usa **Reanalizar historial**. |
| El botón de IA devuelve `400`. | Falta `LLM_API_KEY`. | Añádela en `apps/api/.env` y reinicia `uvicorn`. |
| El informe no cambia tras editar reglas. | Los informes guardados no se regeneran solos. | Pulsa **Reanalizar historial**. |
| La API falla tras cambiar `models.py`. | No hay migraciones. | Para el servidor, borra `apps/api/data/quiqu.db` y vuelve a sincronizar. |
| `EADDRINUSE` en 3000/8000. | Otro proceso o una instancia anterior sigue vivo. | Cierra la app o mata el proceso; el lanzador limpia sus propios procesos. |
| Henrik no encuentra la cuenta. | Riot ID, tag, región o key incorrectos. | Revísalos en Ajustes; la key se guarda en la BD local. |
| El rango aparece vacío con HenrikDev. | La consulta de rango falló (es opcional). | Vuelve a sincronizar; las partidas se cargan igualmente. |
| El lanzador no abre nada. | Fallo de arranque o puerto ocupado. | Revisa `.runtime/dev.err.log` y `.runtime/quiqu.log`. |
| El botón **Cerrar Quiqu.ia** no aparece. | Arrancaste con `npm run dev`. | Usa el acceso directo o el script del lanzador. |

## Limitaciones conocidas

- **No analiza vídeo** ni posiciones tick a tick: trabaja con los datos que expone el proveedor (sin coordenadas de kills ni radianes).
- **HenrikDev es una API no oficial** y puede cambiar o limitar el acceso. Solo se guardan modos con rondas (Competitivo, Unrated, Swiftplay, Spike Rush y Premier); Deathmatch, TDM, Escalation y Custom se descartan.
- **`ability_casts` desconocido**: si Henrik no envía el dato, la utilidad se mantiene como desconocida y las reglas correspondientes no se activan. Nunca se asume `0`.
- **Monousuario y sin autenticación**: no expongas la API fuera de tu PC.
- **Sin migraciones**: cualquier cambio de esquema implica recrear la base de datos.
- **Objetivos y coach conversacional**: existen en la API, aún sin interfaz web.
- **Benchmarks orientativos**: las referencias por rango son aproximaciones, no datos oficiales de Riot.
- **La IA es externa y opcional**: si la activas, el contexto de tus partidas viaja al proveedor del modelo.

## Documentación interna

`AGENTS.md` es la referencia técnica detallada (arquitectura, convenciones, decisiones y trampas conocidas). Este README es la puerta de entrada para usar y ejecutar el proyecto; si cambias comportamiento, actualiza ambos.

## Licencia

Proyecto privado y local-first. No hay una licencia de código abierto publicada; no se concede permiso de uso o distribución salvo autorización expresa.
