interface HeaderProps {
  lastUpdated: string | null;
}

export function Header({ lastUpdated }: HeaderProps) {
  return (
    <header className="bg-space-indigo text-platinum py-6 px-4 shadow-lg">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl md:text-4xl font-bold tracking-tight">
          Wedding RSVP Dashboard
        </h1>
        <p className="mt-2 text-platinum/80 text-sm md:text-base">
          Mike & Saumya • 2026
        </p>
        {lastUpdated && (
          <p className="mt-1 text-platinum/60 text-xs">
            Last updated: {lastUpdated}
          </p>
        )}
      </div>
    </header>
  );
}
