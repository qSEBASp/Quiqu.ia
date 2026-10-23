import { ChevronDown, Shield } from "lucide-react";
import type { Profile } from "@/lib/types";
import { initials } from "@/lib/format";

export function ProfileChip({
  profile,
  onClick,
  expanded = false,
}: {
  profile: Profile;
  onClick?: () => void;
  expanded?: boolean;
}) {
  const content = (
    <>
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-brand-500/80 to-brand-500/30 text-[11px] font-bold text-white">
        {initials(profile.riot_id)}
      </span>
      <div className="min-w-0 text-left leading-tight">
        <p className="truncate text-xs font-semibold text-white/90">
          {profile.riot_id}
          <span className="text-white/35">#{profile.tag}</span>
        </p>
        <p className="mt-0.5 flex items-center gap-1 text-[10px] text-white/35">
          <Shield size={10} />
          {profile.rank_name ?? profile.region.toUpperCase()}
        </p>
      </div>
      {onClick && (
        <ChevronDown
          size={13}
          className={
            expanded
              ? "ml-1 rotate-180 text-white/40 transition-transform"
              : "ml-1 text-white/40 transition-transform"
          }
        />
      )}
    </>
  );

  if (!onClick) {
    return (
      <div className="panel flex items-center gap-3 px-3 py-2">{content}</div>
    );
  }

  return (
    <button
      type="button"
      onClick={onClick}
      aria-expanded={expanded}
      aria-haspopup="dialog"
      className="panel flex items-center gap-3 px-3 py-2 transition hover:border-white/15 hover:bg-white/[0.03]"
    >
      {content}
    </button>
  );
}
