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
      <div className="flex flex-wrap items-center gap-4">
        {/* Search */}
        <div className="flex-1 min-w-[200px]">
          <input
            type="text"
            placeholder="Search by name..."
            value={filters.searchQuery}
            onChange={(e) => setFilters(f => ({ ...f, searchQuery: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-burgundy focus:border-transparent"
          />
        </div>

        {/* Bride/Groom Toggle */}
        <div className="flex rounded-md overflow-hidden border border-gray-300">
          {brideGroomOptions.map((option) => (
            <button
              key={option}
              onClick={() => setFilters(f => ({ ...f, brideOrGroom: option }))}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                filters.brideOrGroom === option
                  ? 'bg-burgundy text-cream'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              {option}
            </button>
          ))}
        </div>

        {/* RSVP Status Pills */}
        <div className="flex flex-wrap gap-2">
          {rsvpStatuses.map((status) => (
            <button
              key={status}
              onClick={() => setFilters(f => ({ ...f, rsvpStatus: status }))}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                filters.rsvpStatus === status
                  ? status === 'Attending'
                    ? 'bg-green-600 text-white'
                    : status === 'Declined'
                    ? 'bg-crimson text-white'
                    : status === 'No Response'
                    ? 'bg-amber-500 text-white'
                    : status === 'Not Invited'
                    ? 'bg-gray-500 text-white'
                    : 'bg-navy text-cream'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              {status}
            </button>
          ))}
        </div>

        {/* Relationship Dropdown */}
        <select
          value={filters.side}
          onChange={(e) => setFilters(f => ({ ...f, side: e.target.value }))}
          className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-burgundy focus:border-transparent"
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
            className="px-3 py-2 text-sm text-crimson hover:text-burgundy font-medium"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* Results Count */}
      <div className="mt-3 text-sm text-gray-600">
        Showing <span className="font-semibold text-navy">{filteredCount}</span> of{' '}
        <span className="font-semibold">{totalCount}</span> guests
      </div>
    </div>
  );
}
