import json

import httpx

from ..config import settings
from ..providers.base import MatchData
from .rules import Finding


class LLMUnavailable(Exception):
    pass


SYSTEM_PROMPT = """Eres un coach profesional de Valorant. Analizas datos objetivos de una partida
y escribes un informe breve, directo y accionable en espanol. Reglas:
- Usa SOLO la evidencia proporcionada. No inventes rondas, posiciones ni estadisticas.
- Nada de relleno ni motivacion generica.
- Prioriza los errores con mayor impacto en el resultado.
- Cada prioridad debe explicar el problema y dar una accion concreta.
Devuelve exclusivamente un JSON valido con esta forma:
{"summary": "2-3 frases", "priorities": [{"title": "...", "why": "...", "fix": "..."}], "drills": ["..."]}
Maximo 4 prioridades y 3 drills."""


def _payload(match: MatchData, metrics: dict, findings: list[Finding]) -> dict:
    return {
        "partida": {
            "mapa": match.map_name,
            "agente": match.agent,
            "resultado": match.result,
            "marcador": f"{match.score_us}-{match.score_them}",
            "kda": f"{match.overall.kills}/{match.overall.deaths}/{match.overall.assists}",
        },
        "metricas": metrics,
        "hallazgos": [
            {
                "titulo": f.title,
                "categoria": f.category,
                "severidad": f.severity,
                "detalle": f.detail,
                "accion": f.recommendation,
                "rondas": f.evidence.get("rounds", []),
            }
            for f in findings[:6]
        ],
    }


def enhance_report(
    match: MatchData, metrics: dict, findings: list[Finding]
) -> dict:
    if not settings.llm_api_key:
        raise LLMUnavailable(
            "No hay proveedor de IA configurado. Añade LLM_API_KEY en apps/api/.env."
        )

    request_body = {
        "model": settings.llm_model,
        "temperature": 0.3,
        "max_tokens": 900,
        "response_format": {"type": "json_object"},
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(_payload(match, metrics, findings), ensure_ascii=False),
            },
        ],
    }
    try:
        response = httpx.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json=request_body,
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (httpx.HTTPError, KeyError, ValueError, json.JSONDecodeError) as exc:
        raise LLMUnavailable(f"El proveedor de IA falló: {exc}") from exc

    summary = parsed.get("summary")
    priorities = parsed.get("priorities")
    drills = parsed.get("drills")
    if not isinstance(summary, str) or not isinstance(priorities, list):
        raise LLMUnavailable("La respuesta de la IA no tiene el formato esperado.")

    cleaned = []
    for item in priorities[:4]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        why = str(item.get("why", "")).strip()
        fix = str(item.get("fix", "")).strip()
        if title and why and fix:
            cleaned.append({"title": title, "why": why, "fix": fix})

    return {
        "summary": summary.strip(),
        "priorities": cleaned,
        "drills": [str(d).strip() for d in drills if str(d).strip()][:3]
        if isinstance(drills, list)
        else [],
        "model": settings.llm_model,
    }
