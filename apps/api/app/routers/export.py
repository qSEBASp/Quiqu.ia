import csv
import io

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from ..db import get_db
from ..services import list_matches

router = APIRouter(prefix="/api/export", tags=["export"])

COLUMNS = [
    ("Fecha", "started_at"),
    ("Mapa", "map"),
    ("Modo", "mode"),
    ("Agente", "agent"),
    ("Resultado", "result"),
    ("Marcador", None),
    ("Kills", "kills"),
    ("Muertes", "deaths"),
    ("Asistencias", "assists"),
    ("ACS", "acs"),
    ("ADR", "adr"),
    ("HS%", "hs_pct"),
    ("KAST", "kast"),
    ("Forma", "form_score"),
    ("A corregir", "top_insight"),
    ("Recomendacion", "top_fix"),
]


def _value(row: dict, key: str | None):
    if key is None:
        return f"{row.get('score_us', 0)}-{row.get('score_them', 0)}"
    return row.get(key, "")


def _csv_safe(value):
    """Evita que una celda se interprete como fórmula al abrir el CSV."""
    if isinstance(value, str) and value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + value
    return value


@router.get("/matches.csv")
def export_matches(db: Session = Depends(get_db)):
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow([label for label, _ in COLUMNS])
    for row in list_matches(db, limit=200):
        writer.writerow([_csv_safe(_value(row, key)) for _, key in COLUMNS])

    content = "\ufeff" + output.getvalue()
    return Response(
        content=content,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": 'attachment; filename="quiquia-partidas.csv"',
            "X-Content-Type-Options": "nosniff",
            "Cache-Control": "no-store",
        },
    )
