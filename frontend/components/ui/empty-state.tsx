import type { ReactNode } from "react";
import { FileText } from "lucide-react";

export function EmptyState({
  title,
  description,
  action
}: Readonly<{ title: string; description?: string; action?: ReactNode }>) {
  return (
    <div className="rounded-md border border-dashed border-line bg-paper/70 p-8 text-center">
      <FileText aria-hidden="true" className="mx-auto h-9 w-9 text-brand" />
      <p className="mt-3 font-serif text-xl font-bold">{title}</p>
      {description ? <p className="mx-auto mt-2 max-w-xl text-base leading-7 text-muted">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}
