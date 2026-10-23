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

## Acceso directo de escritorio

Para abrir Quiqu.ia como una aplicación y poder cerrarla desde la propia interfaz:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\crear-acceso-directo.ps1
```

Crea `Quiqu.ia.lnk` en el escritorio. El acceso directo usa `scripts\iniciar-quiqu-oculto.vbs`, que arranca el lanzador de PowerShell sin mostrar ninguna terminal. Al abrirlo, `scripts\iniciar-quiqu.ps1`:

1. Comprueba dependencias y que los puertos `3000`/`8000` estén libres.
2. Arranca API y web con `npm run dev`.
3. Espera a que respondan y abre la página en una ventana de Edge en modo app.
4. Muestra el botón **Cerrar Quiqu.ia** en la barra lateral y en la navegación móvil.

El acceso directo usa el icono de la app (`apps/web/app/favicon.ico`). El botón escribe una señal en `.runtime/stop`; el lanzador cierra la ventana del navegador y el árbol de procesos de la app. `.runtime/` está ignorado por Git y contiene los logs (`quiqu.log`, `dev.out.log`, `dev.err.log`). Si arrancas manualmente solo con `npm run dev`, el botón de cierre no aparece porque no hay lanzador vigilando. Para depurar el arranque con consola visible puedes ejecutar `scripts\iniciar-quiqu.ps1` a mano.

Variables relevantes (ver `apps/api/.env.example`):

| Variable | Descripción | Por defecto |
| --- | --- | --- |
| `PROVIDER` | Proveedor inicial para BD nueva (`demo` o `henrikdev`) | `demo` |
| `FRONTEND_ORIGIN` | Origen permitido por CORS | `http://localhost:3000` |
| `ENABLE_DOCS` | Expone `/docs`, `/redoc` y `/openapi.json` | `true` |
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
- Cambiar `riot_id`/`tag`/`region`/`provider` desde Ajustes borra partidas, insights, informes y objetivos (datos de cuentas distintas no son comparables).
- `POST /api/sync/reset` borra el historial (conserva los objetivos) y resincroniza con el proveedor actual.
- `ability_casts` null en HenrikDev se tratan como desconocidos (no se fuerzan a 0). Las reglas relacionadas con utilidad requieren cobertura mínima antes de activarse.
- Los modos solo se analizan si son competitivos/unrated/swiftplay/spike rush/premier.

## Licencia

Proyecto privado/local-first.