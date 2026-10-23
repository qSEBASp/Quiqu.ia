import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="panel mx-auto mt-10 max-w-md p-8 text-center">
      <p className="num text-[11px] uppercase tracking-[0.2em] text-brand-400">404</p>
      <h1 className="mt-2 text-lg font-semibold">Página no encontrada</h1>
      <p className="mt-1 text-xs text-white/40">
        La ruta que buscas no existe o ha cambiado.
      </p>
      <Link
        href="/"
        className="mt-5 inline-flex items-center gap-1.5 text-xs font-medium text-brand-400 hover:text-brand-500"
      >
        <ArrowLeft size={13} /> Volver al resumen
      </Link>
    </div>
  );
}
