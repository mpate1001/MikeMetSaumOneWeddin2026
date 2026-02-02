import type { GuestFilters, RSVPStatus } from '../types/guest';

interface FilterBarProps {
  filters: GuestFilters;
  setFilters: React.Dispatch<React.SetStateAction<GuestFilters>>;
  uniqueSides: string[];
  totalCount: number;
  filteredCount: number;
}

const rsvpStatuses: (RSVPStatus | 'All')[] = ['All', 'Attending', 'Declined', 'No Response', 'Not Invited'];
const brideGroomOptions = ['All', 'Bride', 'Groom'] as const;

export function FilterBar({ filters, setFilters, uniqueSides, totalCount, filteredCount }: FilterBarProps) {
  const clearFilters = () => {
    setFilters({
      brideOrGroom: 'All',
      rsvpStatus: 'All',
      side: 'All',
      searchQuery: '',
    });
  };

  const hasActiveFilters =
    filters.brideOrGroom !== 'All' ||
    filters.rsvpStatus !== 'All' ||
    filters.side !== 'All' ||
    filters.searchQuery !== '';

  return (
    <div className="bg-white rounded-lg shadow p-4 mb-6">
      <div className="space-y-3">
        {/* Row 1: Search + Bride/Groom Toggle */}
        <div className="flex flex-col sm:flex-row gap-3">
          {/* Search */}
          <div className="flex-1">
            <input
              type="text"
              placeholder="Search by name..."
              value={filters.searchQuery}
              onChange={(e) => setFilters(f => ({ ...f, searchQuery: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-strawberry focus:border-transparent"
            />
          </div>

          {/* Bride/Groom Toggle */}
          <div className="flex rounded-md overflow-hidden border border-gray-300 shrink-0">
            {brideGroomOptions.map((option) => (
              <button
                key={option}
                onClick={() => setFilters(f => ({ ...f, brideOrGroom: option }))}
                className={`px-3 sm:px-4 py-2 text-sm font-medium transition-colors ${
                  filters.brideOrGroom === option
                    ? 'bg-space-indigo text-platinum'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {option}
              </button>
            ))}
          </div>
        </div>

        {/* Row 2: RSVP Status Pills */}
        <div className="flex flex-wrap gap-2">
          {rsvpStatuses.map((status) => (
            <button
              key={status}
              onClick={() => setFilters(f => ({ ...f, rsvpStatus: status }))}
              className={`px-3 py-1.5 text-xs sm:text-sm rounded-full transition-colors ${
                filters.rsvpStatus === status
                  ? status === 'Attending'
                    ? 'bg-green-600 text-white'
                    : status === 'Declined'
                    ? 'bg-crimson text-white'
                    : status === 'No Response'
                    ? 'bg-lavender-grey text-white'
                    : status === 'Not Invited'
                    ? 'bg-gray-500 text-white'
                    : 'bg-space-indigo text-platinum'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Row 3: Relationship Dropdown + Clear */}
        <div className="flex flex-wrap items-center gap-3">
          <select
            value={filters.side}
            onChange={(e) => setFilters(f => ({ ...f, side: e.target.value }))}
            className="flex-1 sm:flex-none px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-strawberry focus:border-transparent text-sm"
          >
            {uniqueSides.map((side) => (
              <option key={side} value={side}>
                {side === 'All' ? 'All Relationships' : side}
              </option>
            ))}
          </select>

          {/* Clear Filters */}
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="px-3 py-2 text-sm text-strawberry hover:text-crimson font-medium"
            >
              Clear Filters
            </button>
          )}
        </div>
      </div>

      {/* Results Count */}
      <div className="mt-3 text-sm text-gray-600">
        Showing <span className="font-semibold text-space-indigo">{filteredCount}</span> of{' '}
        <span className="font-semibold">{totalCount}</span> guests
      </div>
    </div>
  );
}
