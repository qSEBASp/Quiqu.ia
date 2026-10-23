import { OfflineNotice } from "@/components/OfflineNotice";
import { PageHeader } from "@/components/PageHeader";
import { SettingsForm } from "@/components/SettingsForm";
import { fetchProfile } from "@/lib/server";

export const dynamic = "force-dynamic";

export default async function SettingsPage() {
  const profile = await fetchProfile();
  if (!profile) return <OfflineNotice />;

  return (
    <div className="rise-in">
      <PageHeader
        eyebrow="Ajustes"
        title="Configuración"
        description="Conecta tu cuenta, elige la fuente de datos y activa la capa de IA. Todo se guarda en local."
      />
      <SettingsForm profile={profile} />
    </div>
  );
}
