import { useMemo } from 'react';

export type TabId = 'metrics' | 'all-guests' | 'bride-side' | 'groom-side' | 'follow-up';

interface Tab {
  id: TabId;
  label: string;
  mobileLabel: string;
  count?: number;
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
      mobileLabel: 'Metrics',
    },
    {
      id: 'all-guests',
      label: `All Guests (${guestCounts.total})`,
      mobileLabel: 'All',
      count: guestCounts.total,
    },
    {
      id: 'bride-side',
      label: `Bride's Side (${guestCounts.bride})`,
      mobileLabel: 'Bride',
      count: guestCounts.bride,
      color: 'strawberry'
    },
    {
      id: 'groom-side',
      label: `Groom's Side (${guestCounts.groom})`,
      mobileLabel: 'Groom',
      count: guestCounts.groom,
      color: 'space-indigo'
    },
    {
      id: 'follow-up',
      label: `Follow-Up (${guestCounts.noResponse})`,
      mobileLabel: 'Follow-Up',
      count: guestCounts.noResponse,
      color: 'amber'
    },
  ], [guestCounts]);

  return (
    <div className="bg-white rounded-lg shadow mb-6">
      <nav className="flex" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;

          // Base styles - equal width on all screens
          let baseStyles = 'flex-1 min-w-0 px-1 sm:px-3 py-3 sm:py-4 text-center font-medium transition-all border-b-2';

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
              {/* Desktop: full label inline */}
              <span className="hidden sm:inline">{tab.label}</span>
              {/* Mobile: short label with count below */}
              <span className="sm:hidden flex flex-col items-center gap-0.5">
                <span className="text-xs leading-tight">{tab.mobileLabel}</span>
                {tab.count !== undefined && (
                  <span className="text-[10px] leading-tight opacity-75">{tab.count}</span>
                )}
              </span>
            </button>
          );
        })}
      </nav>
    </div>
  );
}
