import { ServerCrash } from "lucide-react";

export function OfflineNotice() {
  return (
    <div className="mx-auto mt-10 max-w-xl">
      <div className="panel p-6 sm:p-8">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-xl bg-brand-500/10 text-brand-400">
            <ServerCrash size={19} />
          </span>
          <div>
            <h1 className="text-lg font-semibold">El backend no está respondiendo</h1>
            <p className="text-xs text-white/40">La interfaz está viva, pero no encuentra la API.</p>
          </div>
        </div>
        <p className="mt-5 text-sm leading-relaxed text-white/55">
          Arranca el backend desde la raíz del proyecto:
        </p>
        <pre className="mt-3 overflow-x-auto rounded-xl border border-white/5 bg-black/40 p-4 text-xs leading-relaxed text-mint-400">
          <code>npm run dev</code>
        </pre>
        <p className="mt-3 text-xs text-white/35">
          Si ya está corriendo, comprueba que responde en{" "}
          <span className="num text-white/60">http://127.0.0.1:8000/api/health</span>.
        </p>
      </div>
    </div>
  );
}
