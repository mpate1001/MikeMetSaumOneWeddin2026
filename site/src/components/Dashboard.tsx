import { useState, useMemo } from 'react';
import { useGuestData } from '../hooks/useGuestData';
import { Header } from './Header';
import { SummaryCards } from './SummaryCards';
import { Charts } from './Charts';
import { GuestTable } from './GuestTable';
import { TabNavigation, type TabId } from './TabNavigation';
import { CountdownTimers } from './CountdownTimers';
import { FollowUpList } from './FollowUpList';

export function Dashboard() {
  const {
    allGuests,
    loading,
    error,
    lastUpdated,
    summaryStats,
    relationshipStats,
  } = useGuestData();

  const [activeTab, setActiveTab] = useState<TabId>('metrics');

  // Guest counts for tabs
  const guestCounts = useMemo(() => ({
    total: allGuests.length,
    bride: allGuests.filter(g => g.brideOrGroom === 'Bride').length,
    groom: allGuests.filter(g => g.brideOrGroom === 'Groom').length,
    noResponse: allGuests.filter(g => g.wedding === 'No Response').length,
  }), [allGuests]);

  // Filtered guests based on active tab
  const tabGuests = useMemo(() => {
    switch (activeTab) {
      case 'bride-side':
        return allGuests.filter(g => g.brideOrGroom === 'Bride');
      case 'groom-side':
        return allGuests.filter(g => g.brideOrGroom === 'Groom');
      case 'all-guests':
      default:
        return allGuests;
    }
  }, [activeTab, allGuests]);

  if (loading) {
    return (
      <div className="min-h-screen bg-platinum flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-strawberry mx-auto"></div>
          <p className="mt-4 text-space-indigo font-medium">Loading guest data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-platinum flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg max-w-md">
          <div className="text-crimson text-4xl mb-4 font-bold">!</div>
          <h2 className="text-xl font-bold text-space-indigo mb-2">Error Loading Data</h2>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-strawberry text-platinum rounded hover:bg-crimson"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-platinum">
      <Header lastUpdated={lastUpdated} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        <TabNavigation
          activeTab={activeTab}
          onTabChange={setActiveTab}
          guestCounts={guestCounts}
        />

        {/* Metrics Tab */}
        {activeTab === 'metrics' && (
          <>
            <CountdownTimers />
            <SummaryCards stats={summaryStats} />
            <Charts stats={summaryStats} relationshipStats={relationshipStats} />
          </>
        )}

        {/* All Guests Tab */}
        {activeTab === 'all-guests' && (
          <GuestTable guests={tabGuests} title="All Guests" showSearch={true} />
        )}

        {/* Bride Side Tab */}
        {activeTab === 'bride-side' && (
          <GuestTable
            guests={tabGuests}
            title="Bride's Side"
            showSearch={true}
            accentColor="strawberry"
          />
        )}

        {/* Groom Side Tab */}
        {activeTab === 'groom-side' && (
          <GuestTable
            guests={tabGuests}
            title="Groom's Side"
            showSearch={true}
            accentColor="space-indigo"
          />
        )}

        {/* Follow-Up Tab */}
        {activeTab === 'follow-up' && (
          <FollowUpList guests={allGuests} />
        )}
      </main>

      <footer className="bg-space-indigo text-platinum/60 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          Wedding RSVP Dashboard • Data synced from Zola
        </div>
      </footer>
    </div>
  );
}
