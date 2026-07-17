import type { ReactNode } from "react";

export function PageHeader({
  title,
  description,
  action
}: Readonly<{ title: string; description?: string; action?: ReactNode }>) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-4 border-b border-line pb-5">
      <div>
        <p className="mb-2 text-sm font-bold tracking-wide text-cinnabar">長庚大學中國醫學研究社</p>
        <h2 className="font-serif text-3xl font-bold tracking-normal text-ink md:text-4xl">{title}</h2>
        {description ? <p className="mt-2 max-w-3xl text-lg leading-8 text-muted">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </header>
  );
}
