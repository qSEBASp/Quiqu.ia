"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { postJSON } from "@/lib/api";
import type { SyncResult } from "@/lib/types";
import { clsx } from "./clsx";

export function SyncButton({
  label = "Sincronizar",
  size = "md",
  fullWidth = false,
}: {
  label?: string;
  size?: "md" | "lg";
  fullWidth?: boolean;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(
    null,
  );

  async function run() {
    setBusy(true);
    setMessage(null);
    try {
      const result = await postJSON<SyncResult>("/api/sync");
      setMessage({
        kind: "ok",
        text:
          result.added > 0
            ? `${result.added} partida${result.added === 1 ? "" : "s"} nueva${result.added === 1 ? "" : "s"}`
            : "Todo al día",
      });
      router.refresh();
    } catch (error) {
      setMessage({
        kind: "error",
        text: error instanceof Error ? error.message : "No se pudo sincronizar",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={clsx("flex flex-col gap-1.5", fullWidth && "w-full")}>
      <button
        type="button"
        onClick={run}
        disabled={busy}
        className={clsx(
          "inline-flex items-center justify-center gap-2 rounded-xl bg-brand-500 font-semibold text-white transition hover:bg-brand-400 disabled:cursor-wait disabled:opacity-70",
          size === "lg" ? "px-5 py-3 text-sm" : "px-3.5 py-2 text-xs",
          fullWidth && "w-full",
        )}
      >
        <RefreshCw size={size === "lg" ? 16 : 14} className={busy ? "animate-spin" : ""} />
        {busy ? "Sincronizando…" : label}
      </button>
      {message && (
        <span
          className={clsx(
            "text-[11px]",
            message.kind === "ok" ? "text-mint-400" : "text-brand-400",
            fullWidth && "text-center",
          )}
        >
          {message.text}
        </span>
      )}
    </div>
  );
}
