import { AccountSwitcher } from "@/components/AccountSwitcher";
import { EmptyDashboard } from "@/components/EmptyDashboard";
import { MatchesTable } from "@/components/MatchesTable";
import { OfflineNotice } from "@/components/OfflineNotice";
import { PageHeader } from "@/components/PageHeader";
import { SyncButton } from "@/components/SyncButton";
import { fetchMatches, fetchOverview } from "@/lib/server";

export const dynamic = "force-dynamic";

export default async function MatchesPage() {
  const overview = await fetchOverview();
  if (!overview) return <OfflineNotice />;
  if (overview.totals.matches === 0) {
    return <EmptyDashboard profile={overview.profile} />;
  }
  const matches = await fetchMatches();

  return (
    <div className="rise-in">
      <PageHeader
        eyebrow="Historial"
        title="Todas tus partidas"
        description="Cada partida se analiza al sincronizar. Abre una para ver el informe, las rondas y los errores detectados."
        actions={
          <div className="flex flex-wrap items-center gap-2">
            <AccountSwitcher profile={overview.profile} />
            <SyncButton />
          </div>
        }
      />
      <MatchesTable matches={matches} />
    </div>
  );
}
