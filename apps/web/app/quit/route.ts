import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/**
 * Cierre local controlado por el lanzador de escritorio.
 *
 * No mata procesos directamente: deja una señal que el script de PowerShell
 * vigila para cerrar la ventana del navegador y el árbol de procesos de la app.
 */
export async function POST(request: Request) {
  const stopFile = process.env.QUIQU_STOP_FILE;
  if (!stopFile) {
    return NextResponse.json(
      {
        detail:
          "El cierre automático solo está disponible al abrir Quiqu.ia desde el acceso directo.",
      },
      { status: 503 },
    );
  }

  if (request.headers.get("x-quiqu-shutdown") !== "1") {
    return NextResponse.json({ detail: "Petición no permitida" }, { status: 403 });
  }

  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (origin && host) {
    try {
      if (new URL(origin).host !== host) {
        return NextResponse.json({ detail: "Origen no permitido" }, { status: 403 });
      }
    } catch {
      return NextResponse.json({ detail: "Origen no permitido" }, { status: 403 });
    }
  }

  if (request.headers.get("sec-fetch-site") === "cross-site") {
    return NextResponse.json({ detail: "Origen no permitido" }, { status: 403 });
  }

  try {
    await mkdir(path.dirname(stopFile), { recursive: true });
    await writeFile(stopFile, new Date().toISOString(), "utf8");
    return NextResponse.json({ ok: true }, { status: 202 });
  } catch {
    return NextResponse.json(
      { detail: "No se pudo preparar el cierre de la aplicación" },
      { status: 500 },
    );
  }
}
