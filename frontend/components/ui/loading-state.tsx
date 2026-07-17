export function LoadingState({ label = "資料載入中" }: Readonly<{ label?: string }>) {
  return (
    <div className="flex min-h-24 items-center justify-center rounded-md border border-line bg-panel text-muted">
      <span className="mr-3 h-4 w-4 animate-spin rounded-full border-2 border-brand border-t-transparent" />
      <span className="font-bold">{label}</span>
    </div>
  );
}
