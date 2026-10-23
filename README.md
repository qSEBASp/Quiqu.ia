# quiqu.ia

Entrenador local de partidas de Valorant con análisis automático y coaching en español.

- **Backend**: FastAPI + SQLAlchemy + SQLite
- **Frontend**: Next.js 16 (App Router) + TypeScript + Tailwind CSS v4
- **Modo local**: Un solo usuario, sin autenticación. Los datos se guardan en `apps/api/data/quiqu.db`.

## Características

- **Sincronización de partidas**: Soporta proveedor `demo` (determinista, sin claves) o `henrikdev` (unofficial API v4 de Valorant).
- **Análisis automático**: Métricas por partida/ronda, reglas de coaching (`analysis/rules.py`) e insights almacenados.
- **Fortalezas**: Calculadas al vuelo desde métricas (`analysis/strengths.py`), con mínimo 8 rondas y top 3.
- **Coach IA opcional**: `POST /api/matches/{id}/report/ai` regenera el informe con un modelo compatible con OpenAI. Requiere `LLM_API_KEY` (solo en `.env`, sin UI).
- **Objetivos, stats y exportación**: Vistas de progreso, estadísticas globales y exportación de datos.
- **Modo español**: Todos los textos de coaching e interfaz están en español. Las etiquetas de modo se normalizan entre proveedor demo y HenrikDev.

## Requisitos

- Windows (los scripts usan rutas del venv de Windows). También debería funcionar en otros sistemas ajustando los scripts.
- Python 3.11+
- Node.js 18+
- npm

## Instalación

```powershell
# Crear y activar entorno virtual del backend
python -m venv apps/api/.venv
apps\api\.venv\Scripts\python.exe -m pip install -r apps/api/requirements.txt

# Dependencias
npm install                    # solo concurrently
npm install --prefix apps/web  # dependencias del frontend

# Configuración opcional
Copy-Item apps/api/.env.example apps/api/.env
```

El archivo `.env` se lee desde `apps/api/`, no desde la raíz. Las configuraciones se cachean al importar; tras cambiar `.env` hay que reiniciar `uvicorn`.

## Desarrollo

Ejecutar API y web juntos:

```powershell
npm run dev
```

O por separado:

```powershell
npm run dev:api  # http://127.0.0.1:8000
npm run dev:web  # http://localhost:3000
```

Variables relevantes (ver `apps/api/.env.example`):

| Variable | Descripción | Por defecto |
| --- | --- | --- |
| `PROVIDER` | Proveedor inicial para BD nueva (`demo` o `henrikdev`) | `demo` |
| `FRONTEND_ORIGIN` | Origen permitido por CORS | `http://localhost:3000` |
| `HENRIKDEV_API_KEY` | API key para HenrikDev (también se puede guardar desde Ajustes) | - |
| `LLM_API_KEY` | Clave para informe IA (OpenAI-compatible) | - |
| `LLM_BASE_URL` | URL base del proveedor LLM | `https://api.openai.com/v1` |
| `LLM_MODEL` | Modelo a usar para el informe IA | `gpt-4o-mini` |
| `NEXT_PUBLIC_API_URL` | URL de la API usada por el frontend | `http://127.0.0.1:8000` |

## Verificación

```powershell
npm run test                                                  # pytest (solo backend)
npm --prefix apps/web run typecheck
npm run build
```

Test individual:
```powershell
apps\api\.venv\Scripts\python.exe -m pytest apps/api/tests/test_demo.py::test_demo_is_deterministic -q
```

## Estructura

```text
apps/
  api/        # FastAPI (app/, providers/, analysis/, routers/, services.py)
  web/        # Next.js 16 App Router (app/, components/, lib/)
```

Notas importantes (ver `AGENTS.md` para detalles completos):

- Sin migraciones: usar `create_all`. Si cambian modelos, borrar `apps/api/data/quiqu.db`.
- Cambiar `riot_id`/`tag`/`region`/`provider` desde Ajustes borra partidas, insights e informes (datos de cuentas distintas no son comparables).
- `POST /api/sync/reset` borra historial y resincroniza con el proveedor actual.
- `ability_casts` null en HenrikDev se tratan como desconocidos (no se fuerzan a 0). Las reglas relacionadas con utilidad requieren cobertura mínima antes de activarse.
- Los modos solo se analizan si son competitivos/unrated/swiftplay/spike rush/premier.

## Licencia

Proyecto privado/local-first.