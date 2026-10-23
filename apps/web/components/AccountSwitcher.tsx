"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check, Loader2, LogOut, TriangleAlert, X } from "lucide-react";
import { postJSON, putJSON } from "@/lib/api";
import { REGIONS } from "@/lib/regions";
import type { Profile, SyncResult } from "@/lib/types";
import { ProfileChip } from "./ProfileChip";

export function AccountSwitcher({ profile }: { profile: Profile }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [riotId, setRiotId] = useState(profile.riot_id);
  const [tag, setTag] = useState(profile.tag);
  const [region, setRegion] = useState(profile.region);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const changed =
    riotId.trim().toLowerCase() !== profile.riot_id.toLowerCase() ||
    tag.trim().toLowerCase() !== profile.tag.toLowerCase() ||
    region !== profile.region;

  function toggle() {
    setOpen((value) => !value);
    setError(null);
    setDone(null);
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setDone(null);
    try {
      await putJSON<Profile>("/api/profile", {
        riot_id: riotId.trim(),
        tag: tag.trim(),
        region,
        provider: profile.provider,
      });
      const result = await postJSON<SyncResult>("/api/sync");
      setDone(
        result.added > 0
          ? `Cuenta actualizada · ${result.added} partida${result.added === 1 ? "" : "s"} nueva${result.added === 1 ? "" : "s"}.`
          : "Cuenta actualizada. No hay partidas nuevas.",
      );
    } catch (cause) {
      setError(
        cause instanceof Error ? cause.message : "No se pudo cambiar de cuenta.",
      );
    } finally {
      setBusy(false);
      router.refresh();
    }
  }

  return (
    <div className="relative">
      <ProfileChip profile={profile} onClick={toggle} expanded={open} />

      {open && (
        <>
          <div
            className="fixed inset-0 z-40 cursor-default"
            onClick={() => setOpen(false)}
            aria-hidden
          />
          <div
            role="dialog"
            aria-label="Cambiar de cuenta"
            className="absolute right-0 z-50 mt-2 w-[min(21rem,calc(100vw-2rem))] rounded-2xl border border-white/10 bg-ink-900 p-4 shadow-2xl shadow-black/60"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-xs font-semibold text-white/90">
                  Cambiar de cuenta
                </p>
                <p className="mt-0.5 text-[10px] leading-relaxed text-white/35">
                  Buscamos el historial de la cuenta que escribas.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Cerrar"
                className="grid h-6 w-6 shrink-0 place-items-center rounded-md text-white/35 transition hover:bg-white/5 hover:text-white"
              >
                <X size={13} />
              </button>
            </div>

            <form onSubmit={submit} className="mt-3.5 space-y-2.5">
              <div className="grid grid-cols-[1.6fr_1fr] gap-2">
                <label className="block">
                  <span className="text-[9px] uppercase tracking-[0.14em] text-white/30">
                    Riot ID
                  </span>
                  <input
                    value={riotId}
                    onChange={(event) => setRiotId(event.target.value)}
                    required
                    maxLength={32}
                    className="mt-1 h-9 w-full rounded-lg border border-white/8 bg-white/[0.02] px-2.5 text-xs text-white outline-none transition focus:border-brand-500/50"
                    placeholder="TuNombre"
                  />
                </label>
                <label className="block">
                  <span className="text-[9px] uppercase tracking-[0.14em] text-white/30">
                    Tag
                  </span>
                  <div className="relative mt-1">
                    <span className="pointer-events-none absolute left-2.5 top-1/2 -translate-y-1/2 text-xs text-white/25">
                      #
                    </span>
                    <input
                      value={tag}
                      onChange={(event) => setTag(event.target.value)}
                      required
                      maxLength={10}
                      className="h-9 w-full rounded-lg border border-white/8 bg-white/[0.02] pl-6 pr-2 text-xs text-white outline-none transition focus:border-brand-500/50"
                      placeholder="EUW"
                    />
                  </div>
                </label>
              </div>

              <label className="block">
                <span className="text-[9px] uppercase tracking-[0.14em] text-white/30">
                  Región
                </span>
                <select
                  value={region}
                  onChange={(event) => setRegion(event.target.value)}
                  className="mt-1 h-9 w-full rounded-lg border border-white/8 bg-ink-850 px-2.5 text-xs text-white/80 outline-none transition focus:border-brand-500/50"
                >
                  {REGIONS.map((item) => (
                    <option key={item.value} value={item.value}>
                      {item.label}
                    </option>
                  ))}
                </select>
              </label>

              {changed && (
                <p className="flex items-start gap-1.5 rounded-lg border border-amber-400/15 bg-amber-400/[0.05] px-2.5 py-2 text-[10px] leading-relaxed text-amber-400/80">
                  <TriangleAlert size={12} className="mt-0.5 shrink-0" />
                  Al cambiar de cuenta se borra el historial local de la cuenta
                  anterior antes de sincronizar la nueva.
                </p>
              )}

              <button
                type="submit"
                disabled={busy}
                className="inline-flex h-9 w-full items-center justify-center gap-2 rounded-lg bg-brand-500 text-xs font-semibold text-white transition hover:bg-brand-400 disabled:cursor-wait disabled:opacity-70"
              >
                {busy ? (
                  <Loader2 size={13} className="animate-spin" />
                ) : (
                  <LogOut size={13} />
                )}
                {busy ? "Cambiando de cuenta…" : "Cambiar y sincronizar"}
              </button>
            </form>

            {error && (
              <p className="mt-2.5 text-[10px] leading-relaxed text-brand-400">
                {error}
              </p>
            )}
            {done && (
              <p className="mt-2.5 flex items-center gap-1.5 text-[10px] leading-relaxed text-mint-400">
                <Check size={11} className="shrink-0" />
                {done}
              </p>
            )}

            <p className="mt-3 border-t border-white/5 pt-2.5 text-[10px] leading-relaxed text-white/25">
              Fuente actual:{" "}
              {profile.provider === "demo" ? "demo local" : "HenrikDev"} ·{" "}
              {profile.region.toUpperCase()}
            </p>
          </div>
        </>
      )}
    </div>
  );
}
