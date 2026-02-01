import type { SummaryStats } from '../types/guest';

interface SummaryCardsProps {
  stats: SummaryStats;
}

export function SummaryCards({ stats }: SummaryCardsProps) {
  // Overview cards
  const overviewCards = [
    {
      title: 'Total Guests',
      value: stats.totalGuests,
      subtitle: `${stats.brideGuests} Bride • ${stats.groomGuests} Groom`,
      color: 'bg-space-indigo',
    },
    {
      title: 'Response Rate',
      value: `${stats.responseRate.toFixed(0)}%`,
      subtitle: `${stats.totalNoResponse} awaiting response`,
      color: 'bg-lavender-grey',
    },
  ];

  // Short names for events
  const eventShortNames: Record<string, string> = {
    "Saumya's Vidhi & Haaldi": "Saumya's V&H",
    "Mahek's Vidhi & Haaldi": "Mahek's V&H",
    "Wedding": "Wedding",
    "Reception": "Reception",
  };

  return (
    <div className="space-y-4 mb-6">
      {/* Overview Row */}
      <div className="grid grid-cols-2 gap-4">
        {overviewCards.map((card) => (
          <div
            key={card.title}
            className={`${card.color} rounded-lg shadow-lg p-4 text-white`}
          >
            <p className="text-sm font-medium opacity-90">{card.title}</p>
            <p className="text-3xl md:text-4xl font-bold mt-1">{card.value}</p>
            <p className="text-xs mt-2 opacity-75">{card.subtitle}</p>
          </div>
        ))}
      </div>

      {/* Per-Event Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.eventStats.map((event) => {
          const total = event.attending + event.declined + event.noResponse;
          const responseRate = total > 0 ? ((event.attending + event.declined) / total * 100) : 0;
          const shortName = eventShortNames[event.event] || event.event;

          return (
            <div
              key={event.event}
              className="bg-white rounded-lg shadow-lg p-4 border-l-4 border-space-indigo"
            >
              <p className="text-sm font-semibold text-space-indigo truncate">{shortName}</p>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Attending</span>
                  <span className="text-lg font-bold text-green-600">{event.attending}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Declined</span>
                  <span className="text-lg font-bold text-crimson">{event.declined}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Awaiting</span>
                  <span className="text-lg font-bold text-lavender-grey">{event.noResponse}</span>
                </div>
              </div>
              <div className="mt-2 pt-2 border-t border-gray-100">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-400">Response</span>
                  <span className="text-sm font-semibold text-space-indigo">{responseRate.toFixed(0)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
