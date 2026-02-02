import { useMemo } from 'react';

export type TabId = 'metrics' | 'all-guests' | 'bride-side' | 'groom-side' | 'follow-up';

interface Tab {
  id: TabId;
  label: string;
  shortLabel: string;
  color?: string;
}

interface TabNavigationProps {
  activeTab: TabId;
  onTabChange: (tab: TabId) => void;
  guestCounts: {
    total: number;
    bride: number;
    groom: number;
    noResponse: number;
  };
}

export function TabNavigation({ activeTab, onTabChange, guestCounts }: TabNavigationProps) {
  const tabs: Tab[] = useMemo(() => [
    {
      id: 'metrics',
      label: 'Metrics',
      shortLabel: 'Metrics',
    },
    {
      id: 'all-guests',
      label: `All Guests (${guestCounts.total})`,
      shortLabel: `All (${guestCounts.total})`,
    },
    {
      id: 'bride-side',
      label: `Bride's Side (${guestCounts.bride})`,
      shortLabel: `Bride (${guestCounts.bride})`,
      color: 'strawberry'
    },
    {
      id: 'groom-side',
      label: `Groom's Side (${guestCounts.groom})`,
      shortLabel: `Groom (${guestCounts.groom})`,
      color: 'space-indigo'
    },
    {
      id: 'follow-up',
      label: `Follow-Up (${guestCounts.noResponse})`,
      shortLabel: `Follow-Up (${guestCounts.noResponse})`,
      color: 'amber'
    },
  ], [guestCounts]);

  return (
    <div className="bg-white rounded-lg shadow mb-6">
      <nav className="flex overflow-x-auto" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;

          // Base styles
          let baseStyles = 'flex-1 min-w-0 px-3 py-4 text-center font-medium transition-all border-b-2 whitespace-nowrap';

          // Active/inactive styles based on tab color
          if (isActive) {
            if (tab.color === 'strawberry') {
              baseStyles += ' border-strawberry text-strawberry bg-strawberry/5';
            } else if (tab.color === 'space-indigo') {
              baseStyles += ' border-space-indigo text-space-indigo bg-space-indigo/5';
            } else if (tab.color === 'amber') {
              baseStyles += ' border-amber-500 text-amber-600 bg-amber-50';
            } else {
              baseStyles += ' border-space-indigo text-space-indigo bg-space-indigo/5';
            }
          } else {
            baseStyles += ' border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 hover:bg-gray-50';
          }

          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={baseStyles}
              aria-current={isActive ? 'page' : undefined}
            >
              {/* Show full label on md+, short label on mobile */}
              <span className="hidden sm:inline">{tab.label}</span>
              <span className="sm:hidden">{tab.shortLabel}</span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
