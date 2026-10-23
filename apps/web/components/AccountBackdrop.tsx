import { Cloud, Eye, Shield, Swords, type LucideIcon } from "lucide-react";
import type { Backdrop } from "@/lib/types";

const ROLE_META: Record<string, { label: string; icon: LucideIcon }> = {
  duelista: { label: "Duelista", icon: Swords },
  controlador: { label: "Controlador", icon: Cloud },
  iniciador: { label: "Iniciador", icon: Eye },
  centinela: { label: "Centinela", icon: Shield },
};

function roleKey(value: string): keyof typeof ROLE_META {
  const normalized = value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();

  if (normalized.includes("duel")) return "duelista";
  if (normalized.includes("control")) return "controlador";
  if (normalized.includes("inic") || normalized.includes("init")) return "iniciador";
  if (normalized.includes("cent") || normalized.includes("sent")) return "centinela";
  return "duelista";
}

/**
 * Marca de agua ambiental con el rol más jugado de la cuenta.
 * Es puramente decorativa: queda detrás del contenido y no captura el puntero.
 */
export function AccountBackdrop({ data }: { data: Backdrop | null }) {
  if (!data?.role || data.matches === 0) return null;

  const key = roleKey(data.role.name);
  const meta = ROLE_META[key];
  const Icon = meta.icon;

  return (
    <div className="account-backdrop" data-role={key} aria-hidden="true">
      <span className="account-backdrop__glow" />
      <div className="account-backdrop__crest">
        <span className="account-backdrop__halo" />
        <span className="account-backdrop__orbit" />
        <span className="account-backdrop__orbit account-backdrop__orbit--inner" />
        <span className="account-backdrop__diamond" />
        <span className="account-backdrop__ticks" />
        <Icon className="account-backdrop__glyph" strokeWidth={0.7} />
      </div>
      <span className="account-backdrop__caption">
        <span>{meta.label}</span>
        <span className="account-backdrop__caption-line" />
        <span>{data.role.matches} partidas</span>
      </span>
    </div>
  );
}
