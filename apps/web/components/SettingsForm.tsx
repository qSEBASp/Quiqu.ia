"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import {
  AlertTriangle,
  Bot,
  Check,
  KeyRound,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  Sparkles,
  Trash2,
} from "lucide-react";
import { postJSON, putJSON } from "@/lib/api";
import { REGIONS } from "@/lib/regions";
import type { Profile, ReanalyzeResult, SyncResult } from "@/lib/types";
import { clsx } from "./clsx";

type Feedback = { kind: "ok" | "error"; text: string } | null;

export function SettingsForm({ profile }: { profile: Profile }) {
  const router = useRouter();
  const [riotId, setRiotId] = useState(profile.riot_id);
  const [tag, setTag] = useState(profile.tag);
  const [region, setRegion] = useState(profile.region);
  const [provider, setProvider] = useState<"demo" | "henrik">(profile.provider);
  const [apiKey, setApiKey] = useState("");
  const [saving, setSaving] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [reanalyzing, setReanalyzing] = useState(false);
  const [resetting, setResetting] = useState(false);
  const [feedback, setFeedback] = useState<Feedback>(null);

  const identityChanged =
    riotId.trim().toLowerCase() !== profile.riot_id.toLowerCase() ||
    tag.trim().toLowerCase() !== profile.tag.toLowerCase() ||
    region !== profile.region ||
    provider !== profile.provider;

  const busy = saving || syncing || reanalyzing || resetting;

  async function save(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setFeedback(null);
    try {
      const body: Record<string, unknown> = {
        riot_id: riotId.trim(),
        tag: tag.trim(),
        region,
        provider,
      };
      if (apiKey.trim()) body.henrik_api_key = apiKey.trim();
      await putJSON<Profile>("/api/profile", body);
      setApiKey("");
      setFeedback({
        kind: "ok",
        text: identityChanged
          ? "Ajustes guardados. Se borró el historial de la cuenta anterior; sincroniza para cargar la nueva."
          : "Ajustes guardados.",
      });
      router.refresh();
    } catch (error) {
      setFeedback({
        kind: "error",
        text: error instanceof Error ? error.message : "No se pudo guardar.",
      });
    } finally {
      setSaving(false);
    }
  }

  async function sync() {
    setSyncing(true);
    setFeedback(null);
    try {
      const result = await postJSON<SyncResult>("/api/sync");
      setFeedback({
        kind: "ok",
        text:
          result.added > 0
            ? `${result.added} partidas nuevas añadidas.`
            : "No hay partidas nuevas.",
      });
      router.refresh();
    } catch (error) {
      setFeedback({
        kind: "error",
        text: error instanceof Error ? error.message : "No se pudo sincronizar.",
      });
    } finally {
      setSyncing(false);
    }
  }

  async function reanalyze() {
    setReanalyzing(true);
    setFeedback(null);
    try {
      const result = await postJSON<ReanalyzeResult>("/api/sync/reanalyze");
      const kept =
        result.kept_ai > 0
          ? ` Se conservaron ${result.kept_ai} informes de IA.`
          : "";
      setFeedback({
        kind: "ok",
        text:
          result.analyzed === 0
            ? "No hay partidas guardadas para reanalizar."
            : `${result.analyzed} partidas reanalizadas y ${result.insights} hallazgos actualizados.${kept}`,
      });
      router.refresh();
    } catch (error) {
      setFeedback({
        kind: "error",
        text: error instanceof Error ? error.message : "No se pudo reanalizar.",
      });
    } finally {
      setReanalyzing(false);
    }
  }

  async function reset() {
    const confirmed = window.confirm(
      "Se borrarán todas las partidas analizadas y se volverá a sincronizar con la fuente actual. ¿Continuar?",
    );
    if (!confirmed) return;
    setResetting(true);
    setFeedback(null);
    try {
      await postJSON<SyncResult>("/api/sync/reset");
      setFeedback({ kind: "ok", text: "Historial borrado y resincronizado." });
      router.refresh();
    } catch (error) {
      setFeedback({
        kind: "error",
        text: error instanceof Error ? error.message : "No se pudo reiniciar.",
      });
    } finally {
      setResetting(false);
    }
  }

  return (
    <div className="grid gap-4 xl:grid-cols-[1.5fr_1fr]">
      <form onSubmit={save} className="panel p-5 sm:p-6">
        <div className="flex items-center gap-2.5">
          <span className="grid h-9 w-9 place-items-center rounded-xl bg-white/[0.04] text-white/60">
            <KeyRound size={16} />
          </span>
          <div>
            <h2 className="text-sm font-semibold">Cuenta y fuente de datos</h2>
            <p className="text-[11px] text-white/35">Identidad de Riot y proveedor de partidas.</p>
          </div>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className="label-xs">Riot ID</span>
            <input
              value={riotId}
              onChange={(event) => setRiotId(event.target.value)}
              required
              maxLength={32}
              className="mt-2 h-10 w-full rounded-lg border border-white/8 bg-white/[0.02] px-3 text-sm text-white outline-none transition focus:border-brand-500/50"
              placeholder="TuNombre"
            />
          </label>
          <label className="block">
            <span className="label-xs">Tag</span>
            <div className="relative mt-2">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-white/25">
                #
              </span>
              <input
                value={tag}
                onChange={(event) => setTag(event.target.value)}
                required
                maxLength={10}
                className="h-10 w-full rounded-lg border border-white/8 bg-white/[0.02] pl-7 pr-3 text-sm text-white outline-none transition focus:border-brand-500/50"
                placeholder="EUW"
              />
            </div>
          </label>
          <label className="block">
            <span className="label-xs">Región</span>
            <select
              value={region}
              onChange={(event) => setRegion(event.target.value)}
              className="mt-2 h-10 w-full rounded-lg border border-white/8 bg-ink-850 px-3 text-sm text-white/80 outline-none transition focus:border-brand-500/50"
            >
              {REGIONS.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
          <div>
            <span className="label-xs">Fuente</span>
            <div className="mt-2 grid grid-cols-2 gap-2">
              {(
                [
                  ["demo", "Demo local"],
                  ["henrik", "HenrikDev"],
                ] as const
              ).map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setProvider(value)}
                  className={clsx(
                    "h-10 rounded-lg border text-xs font-medium transition",
                    provider === value
                      ? "border-brand-500/40 bg-brand-500/10 text-white"
                      : "border-white/8 bg-white/[0.02] text-white/45 hover:text-white/75",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        {provider === "henrik" && (
          <div className="mt-4 rounded-xl border border-white/5 bg-white/[0.015] p-4">
            <div className="flex items-center justify-between gap-3">
              <span className="label-xs">API key de HenrikDev</span>
              {profile.has_henrik_key && (
                <span className="flex items-center gap-1 text-[10px] text-mint-400">
                  <Check size={11} /> Guardada
                </span>
              )}
            </div>
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              className="mt-2 h-10 w-full rounded-lg border border-white/8 bg-black/20 px-3 text-sm text-white outline-none transition focus:border-brand-500/50"
              placeholder={profile.has_henrik_key ? "•••••••••••• (sin cambios)" : "HDEV-…"}
            />
            <p className="mt-2 text-[10px] leading-relaxed text-white/30">
              Se guarda solo en tu base de datos local. Consigue una key gratuita en{" "}
              <span className="text-white/50">api.henrikdev.xyz</span>. La API oficial de Riot
              requiere una production key aprobada.
            </p>
          </div>
        )}

        {identityChanged && (
          <p className="mt-4 flex items-start gap-2 rounded-xl border border-amber-400/15 bg-amber-400/[0.05] px-3 py-2.5 text-[10px] leading-relaxed text-amber-400/80">
            <AlertTriangle size={12} className="mt-0.5 shrink-0" />
            Al cambiar Riot ID, tag, región o fuente se borra el historial local de
            la cuenta anterior. Después tendrás que sincronizar para cargar la nueva.
          </p>
        )}

        <div className="mt-5 flex flex-wrap items-center gap-2.5">
          <button
            type="submit"
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-xl bg-brand-500 px-4 py-2.5 text-xs font-semibold text-white transition hover:bg-brand-400 disabled:cursor-wait disabled:opacity-70"
          >
            {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
            Guardar ajustes
          </button>
          <button
            type="button"
            onClick={sync}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-xs font-medium text-white/70 transition hover:border-white/20 hover:text-white disabled:cursor-wait disabled:opacity-60"
          >
            {syncing ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RefreshCw size={14} />
            )}
            Sincronizar ahora
          </button>
          <button
            type="button"
            onClick={reanalyze}
            disabled={busy}
            className="inline-flex items-center gap-2 rounded-xl border border-white/10 px-4 py-2.5 text-xs font-medium text-white/70 transition hover:border-white/20 hover:text-white disabled:cursor-wait disabled:opacity-60"
            title="Recalcula hallazgos e informe con el motor actual sin borrar el historial"
          >
            {reanalyzing ? (
              <Loader2 size={14} className="animate-spin" />
            ) : (
              <RotateCcw size={14} />
            )}
            Reanalizar historial
          </button>
        </div>

        <p className="mt-3 text-[10px] leading-relaxed text-white/30">
          «Reanalizar historial» recalcula los hallazgos, las métricas derivadas y el
          informe de reglas de todas las partidas guardadas. No borra nada y respeta
          los informes que ya hayas generado con IA.
        </p>

        {feedback && (
          <p
            className={clsx(
              "mt-3 text-[11px]",
              feedback.kind === "ok" ? "text-mint-400" : "text-brand-400",
            )}
          >
            {feedback.text}
          </p>
        )}
      </form>

      <div className="space-y-4">
        <section className="panel p-5">
          <div className="flex items-center gap-2.5">
            <span
              className={clsx(
                "grid h-9 w-9 place-items-center rounded-xl",
                profile.has_llm_key
                  ? "bg-mint-500/10 text-mint-400"
                  : "bg-white/[0.04] text-white/40",
              )}
            >
              <Bot size={16} />
            </span>
            <div>
              <h2 className="text-sm font-semibold">Capa de IA</h2>
              <p className="text-[11px] text-white/35">
                {profile.has_llm_key ? "Proveedor conectado" : "Opcional"}
              </p>
            </div>
          </div>
          {profile.has_llm_key ? (
            <div className="mt-4">
              <div className="flex items-center gap-2 rounded-lg border border-mint-500/15 bg-mint-500/[0.05] px-3 py-2">
                <Sparkles size={13} className="text-mint-400" />
                <span className="text-xs text-mint-400">
                  Activa · {profile.llm_model}
                </span>
              </div>
              <p className="mt-3 text-[11px] leading-relaxed text-white/35">
                En cada partida puedes pulsar “Reescribir con IA” para regenerar el informe
                con un modelo de lenguaje.
              </p>
            </div>
          ) : (
            <div className="mt-3 space-y-2 text-[11px] leading-relaxed text-white/40">
              <p>
                El informe funciona sin IA con el motor de reglas. Para usar un modelo, crea{" "}
                <span className="num text-white/60">apps/api/.env</span>:
              </p>
              <pre className="overflow-x-auto rounded-lg border border-white/5 bg-black/30 p-3 text-[10px] leading-relaxed text-mint-400">
{`LLM_API_KEY=sk-...
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o-mini`}
              </pre>
              <p>Reinicia el backend después de guardar el archivo.</p>
            </div>
          )}
        </section>

        <section className="panel border-brand-500/15 p-5">
          <div className="flex items-center gap-2.5">
            <span className="grid h-9 w-9 place-items-center rounded-xl bg-brand-500/10 text-brand-400">
              <AlertTriangle size={16} />
            </span>
            <div>
              <h2 className="text-sm font-semibold">Zona de riesgo</h2>
              <p className="text-[11px] text-white/35">Borra el historial local.</p>
            </div>
          </div>
          <p className="mt-3 text-[11px] leading-relaxed text-white/35">
            Borra todas las partidas, hallazgos e informes y vuelve a sincronizar con
            la fuente actual. No afecta a tu cuenta de Riot.
          </p>
          <button
            type="button"
            onClick={reset}
            disabled={busy}
            className="mt-4 inline-flex items-center gap-2 rounded-lg border border-brand-500/25 bg-brand-500/[0.06] px-3 py-2 text-[11px] font-medium text-brand-400 transition hover:bg-brand-500/[0.12] disabled:cursor-wait disabled:opacity-60"
          >
            {resetting ? (
              <Loader2 size={13} className="animate-spin" />
            ) : (
              <Trash2 size={13} />
            )}
            Borrar historial y resincronizar
          </button>
        </section>
      </div>
    </div>
  );
}
