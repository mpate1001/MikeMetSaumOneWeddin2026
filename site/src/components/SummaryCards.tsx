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

  // Event card config with proper colors
  // Saumya = Groom's side, Mahek = Bride's side
  const eventCardConfig: Record<string, { shortName: string; borderColor: string; textColor: string }> = {
    "Saumya's Vidhi & Haaldi": {
      shortName: "Saumya's V&H",
      borderColor: 'border-space-indigo',
      textColor: 'text-space-indigo',
    },
    "Mahek's Vidhi & Haaldi": {
      shortName: "Mahek's V&H",
      borderColor: 'border-strawberry',
      textColor: 'text-strawberry',
    },
    "Wedding": {
      shortName: "Wedding",
      borderColor: 'border-space-indigo',
      textColor: 'text-space-indigo',
    },
    "Reception": {
      shortName: "Reception",
      borderColor: 'border-space-indigo',
      textColor: 'text-space-indigo',
    },
  };

  // Get bride and groom stats for combined cards
  const brideWedding = stats.sideEventStats.find(s => s.side === 'Bride' && s.event === 'Wedding');
  const brideReception = stats.sideEventStats.find(s => s.side === 'Bride' && s.event === 'Reception');
  const groomWedding = stats.sideEventStats.find(s => s.side === 'Groom' && s.event === 'Wedding');
  const groomReception = stats.sideEventStats.find(s => s.side === 'Groom' && s.event === 'Reception');

  const calculateResponseRate = (attending: number, declined: number, noResponse: number) => {
    const total = attending + declined + noResponse;
    return total > 0 ? ((attending + declined) / total * 100) : 0;
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

      {/* Per-Event Stats Row - V&H cards with proper colors */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {stats.eventStats.map((event) => {
          const total = event.attending + event.declined + event.noResponse;
          const responseRate = total > 0 ? ((event.attending + event.declined) / total * 100) : 0;
          const config = eventCardConfig[event.event] || {
            shortName: event.event,
            borderColor: 'border-space-indigo',
            textColor: 'text-space-indigo',
          };

          return (
            <div
              key={event.event}
              className={`bg-white rounded-lg shadow-lg p-4 border-l-4 ${config.borderColor}`}
            >
              <p className={`text-sm font-semibold ${config.textColor} truncate`}>{config.shortName}</p>
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
                  <span className={`text-sm font-semibold ${config.textColor}`}>{responseRate.toFixed(0)}%</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Combined Bride & Groom Cards - 2x2 layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Bride's Card */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden border-l-4 border-strawberry">
          <div className="bg-strawberry/5 px-5 py-3 border-b border-strawberry/10">
            <h3 className="text-lg font-bold text-strawberry">Bride's Side</h3>
          </div>
          <div className="p-5">
            <div className="grid grid-cols-2 gap-6">
              {/* Wedding */}
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-3">Wedding</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Attending</span>
                    <span className="text-xl font-bold text-green-600">{brideWedding?.attending || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Declined</span>
                    <span className="text-xl font-bold text-crimson">{brideWedding?.declined || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Awaiting</span>
                    <span className="text-xl font-bold text-lavender-grey">{brideWedding?.noResponse || 0}</span>
                  </div>
                  <div className="pt-2 border-t border-gray-100">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-400">Response</span>
                      <span className="text-sm font-semibold text-strawberry">
                        {calculateResponseRate(brideWedding?.attending || 0, brideWedding?.declined || 0, brideWedding?.noResponse || 0).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              {/* Reception */}
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-3">Reception</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Attending</span>
                    <span className="text-xl font-bold text-green-600">{brideReception?.attending || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Declined</span>
                    <span className="text-xl font-bold text-crimson">{brideReception?.declined || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Awaiting</span>
                    <span className="text-xl font-bold text-lavender-grey">{brideReception?.noResponse || 0}</span>
                  </div>
                  <div className="pt-2 border-t border-gray-100">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-400">Response</span>
                      <span className="text-sm font-semibold text-strawberry">
                        {calculateResponseRate(brideReception?.attending || 0, brideReception?.declined || 0, brideReception?.noResponse || 0).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Groom's Card */}
        <div className="bg-white rounded-xl shadow-lg overflow-hidden border-l-4 border-space-indigo">
          <div className="bg-space-indigo/5 px-5 py-3 border-b border-space-indigo/10">
            <h3 className="text-lg font-bold text-space-indigo">Groom's Side</h3>
          </div>
          <div className="p-5">
            <div className="grid grid-cols-2 gap-6">
              {/* Wedding */}
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-3">Wedding</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Attending</span>
                    <span className="text-xl font-bold text-green-600">{groomWedding?.attending || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Declined</span>
                    <span className="text-xl font-bold text-crimson">{groomWedding?.declined || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Awaiting</span>
                    <span className="text-xl font-bold text-lavender-grey">{groomWedding?.noResponse || 0}</span>
                  </div>
                  <div className="pt-2 border-t border-gray-100">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-400">Response</span>
                      <span className="text-sm font-semibold text-space-indigo">
                        {calculateResponseRate(groomWedding?.attending || 0, groomWedding?.declined || 0, groomWedding?.noResponse || 0).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              {/* Reception */}
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-3">Reception</p>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Attending</span>
                    <span className="text-xl font-bold text-green-600">{groomReception?.attending || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Declined</span>
                    <span className="text-xl font-bold text-crimson">{groomReception?.declined || 0}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-500">Awaiting</span>
                    <span className="text-xl font-bold text-lavender-grey">{groomReception?.noResponse || 0}</span>
                  </div>
                  <div className="pt-2 border-t border-gray-100">
                    <div className="flex justify-between items-center">
                      <span className="text-xs text-gray-400">Response</span>
                      <span className="text-sm font-semibold text-space-indigo">
                        {calculateResponseRate(groomReception?.attending || 0, groomReception?.declined || 0, groomReception?.noResponse || 0).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
