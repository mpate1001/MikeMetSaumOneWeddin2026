import { useGuestData } from '../hooks/useGuestData';
import { Header } from './Header';
import { FilterBar } from './FilterBar';
import { SummaryCards } from './SummaryCards';
import { Charts } from './Charts';
import { GuestTable } from './GuestTable';

export function Dashboard() {
  const {
    guests,
    allGuests,
    loading,
    error,
    lastUpdated,
    filters,
    setFilters,
    uniqueSides,
    summaryStats,
    relationshipStats,
  } = useGuestData();

  if (loading) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-burgundy mx-auto"></div>
          <p className="mt-4 text-navy font-medium">Loading guest data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-cream flex items-center justify-center">
        <div className="text-center bg-white p-8 rounded-lg shadow-lg max-w-md">
          <div className="text-crimson text-4xl mb-4">⚠️</div>
          <h2 className="text-xl font-bold text-navy mb-2">Error Loading Data</h2>
          <p className="text-gray-600">{error}</p>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-burgundy text-cream rounded hover:bg-burgundy/90"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-cream">
      <Header lastUpdated={lastUpdated} />

      <main className="max-w-7xl mx-auto px-4 py-6">
        <FilterBar
          filters={filters}
          setFilters={setFilters}
          uniqueSides={uniqueSides}
          totalCount={allGuests.length}
          filteredCount={guests.length}
        />

        <SummaryCards stats={summaryStats} />

        <Charts stats={summaryStats} relationshipStats={relationshipStats} />

        <GuestTable guests={guests} />
      </main>

      <footer className="bg-navy text-cream/60 py-4 mt-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm">
          Wedding RSVP Dashboard • Data synced from Zola
        </div>
      </footer>
    </div>
  );
}
