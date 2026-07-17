import type { ReactNode } from "react";

export function SectionHeader({
  eyebrow,
  title,
  description,
  action
}: Readonly<{ eyebrow?: string; title: string; description?: string; action?: ReactNode }>) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        {eyebrow ? <p className="text-sm font-bold tracking-wide text-cinnabar">{eyebrow}</p> : null}
        <h2 className="font-serif text-2xl font-bold text-ink">{title}</h2>
        {description ? <p className="mt-1 max-w-3xl text-base leading-7 text-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}
