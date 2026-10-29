import json
import logging

import httpx

from ..config import settings
from ..providers.base import MatchData
from .rules import Finding
from .strengths import evaluate_strengths

logger = logging.getLogger(__name__)


class LLMUnavailable(Exception):
    pass


SYSTEM_PROMPT = """Eres un coach profesional de Valorant. Analizas datos objetivos de una partida
y escribes un informe breve, directo y accionable en espanol. Reglas:
- Usa SOLO la evidencia proporcionada. No inventes rondas, posiciones ni estadisticas.
- Nada de relleno ni motivacion generica.
- Prioriza los errores con mayor impacto en el resultado.
- Cada prioridad debe explicar el problema y dar una accion concreta.
- No repitas frases, titulos ni acciones de los informes recientes que se te dan.
- Cada prioridad debe reutilizar el campo `regla` de uno de los hallazgos.
- Los drills son habitos de practica distintos del `fix`: no copies la accion.
Devuelve exclusivamente un JSON valido con esta forma:
{"summary": "2-3 frases", "priorities": [{"rule_id": "...", "title": "...", "why": "...", "fix": "..."}], "drills": ["..."]}
Maximo 5 prioridades y 3 drills."""

HISTORY_PROMPT = """Eres un coach profesional de Valorant. Recibes un resumen del historial
de un jugador (ultimas partidas, patrones, puntos fuertes y objetivos). Escribe en espanol,
sin relleno y usando solo los datos proporcionados. No repitas el mismo diagnostico que
los informes de partida: busca la tendencia que solo se ve mirando el historial.
Devuelve exclusivamente un JSON valido:
{"summary": "2-4 frases con el diagnostico global",
 "trends": [{"title": "patron", "detail": "explicacion breve con datos"}],
 "plan": ["accion concreta 1", "accion concreta 2", "accion concreta 3"]}
Maximo 3 tendencias y 3 acciones."""

CHAT_PROMPT = """Eres un coach profesional de Valorant integrado en una app local.
Respondes en espanol, en 2-5 frases, con tono directo y sin motivacion generica.
Usa SOLO el contexto del jugador que se te entrega y el historial de la conversacion.
Si el contexto no alcanza para responder, dilo y pide el dato exacto que falta.
No inventes estadisticas, rondas ni posiciones. Puedes proponer ejercicios concretos."""


def _post(
    messages: list[dict],
    max_tokens: int,
    json_mode: bool,
    temperature: float = 0.3,
) -> str:
    if not settings.llm_api_key:
        raise LLMUnavailable(
            "No hay proveedor de IA configurado. Añade LLM_API_KEY en apps/api/.env."
        )
    body = {
        "model": settings.llm_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "messages": messages,
    }
    if json_mode:
        body["response_format"] = {"type": "json_object"}
    try:
        response = httpx.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.llm_api_key}",
                "Content-Type": "application/json",
            },
            json=body,
            timeout=60,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.warning("Fallo llamando al proveedor de IA: %s", exc)
        raise LLMUnavailable(
            "No se pudo contactar con el proveedor de IA. Inténtalo más tarde."
        ) from exc


def _json(content: str) -> dict:
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        raise LLMUnavailable("La respuesta de la IA no es JSON válido.") from exc
    if not isinstance(parsed, dict):
        raise LLMUnavailable("La respuesta de la IA no tiene el formato esperado.")
    return parsed


def _payload(
    match: MatchData,
    metrics: dict,
    findings: list[Finding],
    previous_reports: list[dict] | None = None,
) -> dict:
    strengths = [
        {"titulo": strength.title, "detalle": strength.detail}
        for strength in evaluate_strengths(metrics, match.match_id)
    ]
    return {
        "partida": {
            "mapa": match.map_name,
            "agente": match.agent,
            "resultado": match.result,
            "marcador": f"{match.score_us}-{match.score_them}",
            "kda": f"{match.overall.kills}/{match.overall.deaths}/{match.overall.assists}",
        },
        "metricas": metrics,
        "puntos_fuertes": strengths,
        "rondas_clave": metrics.get("key_rounds", []),
        "hallazgos": [
            {
                "regla": f.rule_id,
                "etiqueta": f.label,
                "titulo": f.title,
                "categoria": f.category,
                "severidad": f.severity,
                "detalle": f.detail,
                "accion": f.recommendation,
                "rondas": f.evidence.get("rounds", []),
            }
            for f in findings[:8]
        ],
        "informes_recientes": previous_reports or [],
    }


def enhance_report(
    match: MatchData,
    metrics: dict,
    findings: list[Finding],
    previous_reports: list[dict] | None = None,
) -> dict:
    content = _post(
        [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": json.dumps(
                    _payload(match, metrics, findings, previous_reports),
                    ensure_ascii=False,
                ),
            },
        ],
        max_tokens=1100,
        json_mode=True,
        temperature=0.55,
    )
    parsed = _json(content)

    summary = parsed.get("summary")
    priorities = parsed.get("priorities")
    drills = parsed.get("drills")
    if not isinstance(summary, str) or not isinstance(priorities, list):
        raise LLMUnavailable("La respuesta de la IA no tiene el formato esperado.")

    by_rule = {finding.rule_id: finding for finding in findings}
    by_label = {
        finding.label.lower(): finding for finding in findings if finding.label
    }
    cleaned = []
    seen: set[str] = set()
    for item in priorities[:5]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        why = str(item.get("why", "")).strip()
        fix = str(item.get("fix", "")).strip()
        if not (title and why and fix):
            continue
        reference = str(item.get("rule_id") or item.get("regla") or "").strip()
        matched = by_rule.get(reference) or by_label.get(reference.lower())
        key = matched.rule_id if matched else title.lower()
        if key in seen:
            continue
        seen.add(key)
        priority: dict = {"title": title, "why": why, "fix": fix}
        if matched is not None:
            priority.update(
                {
                    "rule_id": matched.rule_id,
                    "category": matched.category,
                    "severity": matched.severity,
                    "evidence": matched.evidence,
                }
            )
        else:
            category = str(item.get("category") or "").strip()
            if category:
                priority["category"] = category
        cleaned.append(priority)

    fixes = {priority["fix"].strip().lower() for priority in cleaned}
    clean_drills: list[str] = []
    if isinstance(drills, list):
        for drill in drills:
            text = str(drill).strip()
            if not text or text.lower() in fixes or text in clean_drills:
                continue
            clean_drills.append(text)
            if len(clean_drills) == 3:
                break

    return {
        "summary": summary.strip(),
        "priorities": cleaned,
        "drills": clean_drills,
        "model": settings.llm_model,
    }


def historical_summary(context: dict) -> dict:
    content = _post(
        [
            {"role": "system", "content": HISTORY_PROMPT},
            {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
        ],
        max_tokens=800,
        json_mode=True,
        temperature=0.5,
    )
    parsed = _json(content)
    summary = parsed.get("summary")
    if not isinstance(summary, str):
        raise LLMUnavailable("La respuesta de la IA no tiene el formato esperado.")
    trends = []
    for item in parsed.get("trends") or []:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        detail = str(item.get("detail", "")).strip()
        if title and detail:
            trends.append({"title": title, "detail": detail})
    plan = [
        str(item).strip()
        for item in (parsed.get("plan") or [])
        if str(item).strip()
    ]
    return {
        "summary": summary.strip(),
        "trends": trends[:3],
        "plan": plan[:3],
        "model": settings.llm_model,
    }


def coach_chat(context: dict, messages: list[dict]) -> dict:
    cleaned = []
    for message in messages[-12:]:
        if not isinstance(message, dict):
            continue
        role = message.get("role")
        content = message.get("content")
        if role not in ("user", "assistant") or not isinstance(content, str):
            continue
        text = content.strip()[:2000]
        if text:
            cleaned.append({"role": role, "content": text})
    if not cleaned:
        raise LLMUnavailable("Escribe una pregunta para el coach.")

    system = (
        f"{CHAT_PROMPT}\n\nContexto actual del jugador (JSON):\n"
        f"{json.dumps(context, ensure_ascii=False)}"
    )
    content = _post(
        [{"role": "system", "content": system}, *cleaned],
        max_tokens=600,
        json_mode=False,
    )
    reply = (content or "").strip()
    if not reply:
        raise LLMUnavailable("La IA devolvió una respuesta vacía.")
    return {"reply": reply, "model": settings.llm_model}
