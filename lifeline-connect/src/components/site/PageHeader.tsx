export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <section className="border-b border-border bg-secondary/50">
      <div className="mx-auto max-w-6xl px-5 py-16 md:py-20">
        {eyebrow && (
          <p className="text-xs font-bold uppercase tracking-[0.18em] text-primary">{eyebrow}</p>
        )}
        <h1 className="mt-3 text-4xl font-extrabold text-ink md:text-5xl">{title}</h1>
        {description && (
          <p className="mt-4 max-w-2xl text-base leading-relaxed text-muted-foreground md:text-lg">
            {description}
          </p>
        )}
      </div>
    </section>
  );
}