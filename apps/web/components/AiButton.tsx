"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { postJSON } from "@/lib/api";

export function AiButton({ matchId, hasKey }: { matchId: string; hasKey: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!hasKey) {
    return (
      <p className="text-[11px] text-white/25">
        Añade <span className="num">LLM_API_KEY</span> en{" "}
        <span className="num">apps/api/.env</span> para reescribir el informe con IA.
      </p>
    );
  }

  async function run() {
    setBusy(true);
    setError(null);
    try {
      await postJSON(`/api/matches/${encodeURIComponent(matchId)}/report/ai`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "La IA no respondió");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <button
        type="button"
        onClick={run}
        disabled={busy}
        className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-1.5 text-[11px] font-medium text-white/70 transition hover:border-white/20 hover:text-white disabled:cursor-wait disabled:opacity-60"
      >
        {busy ? <Loader2 size={12} className="animate-spin" /> : <Sparkles size={12} />}
        {busy ? "Reescribiendo…" : "Reescribir con IA"}
      </button>
      {error && <span className="max-w-[240px] text-right text-[10px] text-brand-400">{error}</span>}
    </div>
  );
}
