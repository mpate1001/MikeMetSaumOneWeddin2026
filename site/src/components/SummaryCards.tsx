import type { SummaryStats } from '../types/guest';

interface SummaryCardsProps {
  stats: SummaryStats;
}

export function SummaryCards({ stats }: SummaryCardsProps) {
  const cards = [
    {
      title: 'Total Guests',
      value: stats.totalGuests,
      subtitle: `${stats.brideGuests} Bride • ${stats.groomGuests} Groom`,
      color: 'bg-navy',
    },
    {
      title: 'Attending',
      value: stats.totalAttending,
      subtitle: 'Wedding ceremony',
      color: 'bg-green-600',
    },
    {
      title: 'Declined',
      value: stats.totalDeclined,
      subtitle: 'Wedding ceremony',
      color: 'bg-crimson',
    },
    {
      title: 'Response Rate',
      value: `${stats.responseRate.toFixed(0)}%`,
      subtitle: `${stats.totalNoResponse} awaiting response`,
      color: 'bg-steel',
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
      {cards.map((card) => (
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
  );
}
