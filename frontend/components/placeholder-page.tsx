import { AppShell } from "@/components/app-shell";
import { PageHeader } from "@/components/page-header";
import { Card, EmptyState } from "@/components/ui";

export function PlaceholderPage({
  title,
  description
}: Readonly<{ title: string; description: string }>) {
  return (
    <AppShell>
      <PageHeader title={title} description={description} />
      <Card>
        <EmptyState title="此功能已排入後續開發" description="目前先保留入口，避免影響既有義診流程操作。" />
      </Card>
    </AppShell>
  );
}
