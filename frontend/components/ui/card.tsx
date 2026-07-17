import type { HTMLAttributes, ReactNode } from "react";

import { cn } from "@/components/ui/utils";

export function Card({ className, ...props }: HTMLAttributes<HTMLElement>) {
  return (
    <section
      className={cn("paper-surface rounded-md border border-line bg-panel p-5 shadow-soft", className)}
      {...props}
    />
  );
}

export function CardHeader({
  title,
  description,
  action
}: Readonly<{ title: string; description?: string; action?: ReactNode }>) {
  return (
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3 border-b border-line pb-3">
      <div>
        <h3 className="font-serif text-xl font-bold text-ink">{title}</h3>
        {description ? <p className="mt-1 text-sm leading-6 text-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
