export function PageHeader({
  title,
  description
}: Readonly<{ title: string; description?: string }>) {
  return (
    <header className="mb-6 border-b border-line pb-5">
      <p className="mb-2 text-sm font-bold tracking-wide text-cinnabar">長庚中醫社義診</p>
      <h2 className="font-serif text-3xl font-bold tracking-normal text-ink md:text-4xl">{title}</h2>
      {description ? <p className="mt-2 max-w-3xl text-lg leading-8 text-muted">{description}</p> : null}
    </header>
  );
}
