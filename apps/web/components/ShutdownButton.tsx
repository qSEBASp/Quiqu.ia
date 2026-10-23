"use client";

import { Power } from "lucide-react";
import { useState } from "react";
import { clsx } from "./clsx";

export function ShutdownButton({ compact = false }: { compact?: boolean }) {
  const [busy, setBusy] = useState(false);
  const [closing, setClosing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function shutdown() {
    if (busy || closing) return;

    setBusy(true);
    setError(null);
    try {
      const response = await fetch("/quit", {
        method: "POST",
        headers: { "X-Quiqu-Shutdown": "1" },
      });

      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(
          typeof body?.detail === "string"
            ? body.detail
            : "No se pudo cerrar Quiqu.ia",
        );
      }

      setClosing(true);
      window.setTimeout(() => window.close(), 1200);
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "No se pudo cerrar Quiqu.ia",
      );
      window.setTimeout(() => setError(null), 6000);
    } finally {
      setBusy(false);
    }
  }

  const button = compact ? (
    <button
      type="button"
      onClick={shutdown}
      disabled={busy || closing}
      aria-label="Cerrar Quiqu.ia"
      title="Cerrar Quiqu.ia"
      className="grid h-9 w-9 place-items-center rounded-lg text-white/30 transition hover:bg-white/[0.04] hover:text-white/70 disabled:opacity-40"
    >
      <Power size={16} />
    </button>
  ) : (
    <button
      type="button"
      onClick={shutdown}
      disabled={busy || closing}
      className={clsx(
        "group flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-[11px] transition",
        "text-white/30 hover:bg-white/[0.04] hover:text-white/60 disabled:opacity-40",
      )}
    >
      <Power size={13} />
      <span>{busy ? "Cerrando..." : "Cerrar Quiqu.ia"}</span>
    </button>
  );

  return (
    <>
      {button}

      {closing && (
        <div
          role="dialog"
          aria-modal="true"
          aria-live="polite"
          className="fixed inset-0 z-[100] grid place-items-center bg-ink-950/95 px-4 backdrop-blur-md"
        >
          <div className="panel w-full max-w-sm p-6 text-center">
            <span className="mx-auto grid h-12 w-12 place-items-center rounded-full border border-brand-500/30 bg-brand-500/10 text-brand-400">
              <Power size={22} />
            </span>
            <p className="mt-4 text-sm font-semibold text-white">
              Cerrando Quiqu.ia
            </p>
            <p className="mt-2 text-xs leading-relaxed text-white/45">
              Se están deteniendo la web y la API. La ventana se cerrará sola.
            </p>
            <button
              type="button"
              onClick={() => window.close()}
              className="mt-5 text-[11px] uppercase tracking-[0.18em] text-white/35 transition hover:text-white/70"
            >
              Cerrar pestaña
            </button>
          </div>
        </div>
      )}

      {error && (
        <div
          role="status"
          className="fixed bottom-5 left-1/2 z-[100] w-[min(92vw,420px)] -translate-x-1/2 rounded-xl border border-brand-500/30 bg-ink-900/95 px-4 py-3 text-xs text-brand-400 shadow-2xl backdrop-blur"
        >
          {error}
        </div>
      )}
    </>
  );
}
