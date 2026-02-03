import { useMemo, useState } from 'react';
import type { Guest } from '../types/guest';

interface FollowUpListProps {
  guests: Guest[];
}

type SortField = 'name' | 'relationship' | 'side';
type SortDirection = 'asc' | 'desc';

export function FollowUpList({ guests }: FollowUpListProps) {
  const [sortField, setSortField] = useState<SortField>('side');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSide, setFilterSide] = useState<'All' | 'Bride' | 'Groom'>('All');
  const [filterRelationship, setFilterRelationship] = useState<string>('All');

  // Get guests who haven't responded to the wedding
  const noResponseGuests = useMemo(() => {
    return guests.filter(g => g.wedding === 'No Response');
  }, [guests]);

  // Get unique relationships for filter dropdown
  const uniqueRelationships = useMemo(() => {
    const relationships = new Set(noResponseGuests.map(g => g.side));
    return ['All', ...Array.from(relationships).sort()];
  }, [noResponseGuests]);

  // Filter and sort
  const filteredGuests = useMemo(() => {
    let result = noResponseGuests;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(g => {
        const fullName = `${g.firstName} ${g.lastName}`.toLowerCase();
        const relationship = g.side.toLowerCase();
        return fullName.includes(query) || relationship.includes(query);
      });
    }

    // Side filter
    if (filterSide !== 'All') {
      result = result.filter(g => g.brideOrGroom === filterSide);
    }

    // Relationship filter
    if (filterRelationship !== 'All') {
      result = result.filter(g => g.side === filterRelationship);
    }

    // Sort
    result = [...result].sort((a, b) => {
      let aVal: string, bVal: string;

      switch (sortField) {
        case 'name':
          aVal = `${a.firstName} ${a.lastName}`.toLowerCase();
          bVal = `${b.firstName} ${b.lastName}`.toLowerCase();
          break;
        case 'relationship':
          aVal = a.side.toLowerCase();
          bVal = b.side.toLowerCase();
          break;
        case 'side':
          aVal = a.brideOrGroom;
          bVal = b.brideOrGroom;
          break;
        default:
          aVal = '';
          bVal = '';
      }

      const comparison = aVal.localeCompare(bVal);
      return sortDirection === 'asc' ? comparison : -comparison;
    });

    return result;
  }, [noResponseGuests, searchQuery, filterSide, filterRelationship, sortField, sortDirection]);

  // Group by relationship for summary
  const groupedByRelationship = useMemo(() => {
    const groups: Record<string, { count: number; brideOrGroom: 'Bride' | 'Groom' | 'Unknown' }> = {};
    noResponseGuests.forEach(g => {
      if (!groups[g.side]) {
        groups[g.side] = { count: 0, brideOrGroom: g.brideOrGroom };
      }
      groups[g.side].count++;
    });
    return Object.entries(groups)
      .map(([relationship, data]) => ({ relationship, ...data }))
      .sort((a, b) => b.count - a.count);
  }, [noResponseGuests]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const brideNoResponse = noResponseGuests.filter(g => g.brideOrGroom === 'Bride').length;
  const groomNoResponse = noResponseGuests.filter(g => g.brideOrGroom === 'Groom').length;

  const exportToCSV = () => {
    const headers = ['First Name', 'Last Name', 'Side', 'Relationship', 'Email', 'Phone', 'Address'];
    const rows = filteredGuests.map(g => [
      g.firstName,
      g.lastName,
      g.brideOrGroom,
      g.side,
      g.email,
      g.phone,
      g.address,
    ]);

    // Escape double quotes in CSV cells by doubling them
    const escapeCSV = (cell: string) => `"${(cell || '').replace(/"/g, '""')}"`;

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(escapeCSV).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `follow-up-list-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow p-5 border-l-4 border-amber-500">
          <p className="text-sm text-gray-500">Total Awaiting Response</p>
          <p className="text-3xl font-bold text-amber-600">{noResponseGuests.length}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-5 border-l-4 border-strawberry">
          <p className="text-sm text-gray-500">Bride's Side</p>
          <p className="text-3xl font-bold text-strawberry">{brideNoResponse}</p>
        </div>

        <div className="bg-white rounded-lg shadow p-5 border-l-4 border-space-indigo">
          <p className="text-sm text-gray-500">Groom's Side</p>
          <p className="text-3xl font-bold text-space-indigo">{groomNoResponse}</p>
        </div>
      </div>

      {/* By Relationship Summary */}
      <div className="bg-white rounded-lg shadow p-5">
        <h3 className="text-lg font-semibold text-space-indigo mb-4">By Relationship</h3>
        <div className="flex flex-wrap gap-2">
          {groupedByRelationship.map(({ relationship, count, brideOrGroom }) => (
            <span
              key={relationship}
              className={`px-3 py-1 rounded-full text-sm font-medium ${
                brideOrGroom === 'Bride'
                  ? 'bg-strawberry/10 text-strawberry'
                  : 'bg-space-indigo/10 text-space-indigo'
              }`}
            >
              {relationship}: {count}
            </span>
          ))}
        </div>
      </div>

      {/* Guest List */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-4 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-bold text-space-indigo">
              Follow-Up List
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({filteredGuests.length} guests)
              </span>
            </h2>
            <button
              onClick={exportToCSV}
              className="px-3 py-1 text-sm bg-space-indigo text-platinum rounded hover:opacity-90 transition-colors"
            >
              Export CSV
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <input
                  type="text"
                  placeholder="Search by name or relationship..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-space-indigo/20 focus:border-space-indigo outline-none"
                />
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </div>
            </div>

            {/* Side Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Side:</label>
              <select
                value={filterSide}
                onChange={(e) => setFilterSide(e.target.value as 'All' | 'Bride' | 'Groom')}
                className="px-2 py-2 text-sm border border-gray-300 rounded-lg"
              >
                <option value="All">All</option>
                <option value="Bride">Bride</option>
                <option value="Groom">Groom</option>
              </select>
            </div>

            {/* Relationship Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Relationship:</label>
              <select
                value={filterRelationship}
                onChange={(e) => setFilterRelationship(e.target.value)}
                className="px-2 py-2 text-sm border border-gray-300 rounded-lg max-w-[180px]"
              >
                {uniqueRelationships.map(rel => (
                  <option key={rel} value={rel}>{rel}</option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* Mobile Card View */}
        <div className="md:hidden">
          {filteredGuests.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {noResponseGuests.length === 0
                ? "Everyone has responded!"
                : "No guests match your search."}
            </div>
          ) : (
            filteredGuests.map((guest, idx) => {
              const name = [guest.title, guest.firstName, guest.lastName, guest.suffix]
                .filter(Boolean)
                .join(' ');
              return (
                <div key={`${guest.firstName}-${guest.lastName}-${idx}`} className="p-4 border-b border-gray-200">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-space-indigo">{name || '(No name)'}</p>
                      <p className="text-sm text-gray-500">{guest.side}</p>
                    </div>
                    <span className={`text-xs font-medium px-2 py-1 rounded ${
                      guest.brideOrGroom === 'Bride'
                        ? 'bg-strawberry/10 text-strawberry'
                        : 'bg-space-indigo/10 text-space-indigo'
                    }`}>
                      {guest.brideOrGroom}
                    </span>
                  </div>
                  {(guest.email || guest.phone) && (
                    <div className="mt-2 text-xs text-gray-600">
                      {guest.email && (
                        <a href={`mailto:${guest.email}`} className="text-blue-600 block truncate">{guest.email}</a>
                      )}
                      {guest.phone && (
                        <a href={`tel:${guest.phone}`} className="text-blue-600">{guest.phone}</a>
                      )}
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>

        {/* Desktop Table View */}
        <div className="hidden md:block overflow-x-auto">
          {filteredGuests.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              {noResponseGuests.length === 0
                ? "Everyone has responded!"
                : "No guests match your search."}
            </div>
          ) : (
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('name')}
                  >
                    Name {sortField === 'name' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('side')}
                  >
                    Side {sortField === 'side' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th
                    className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('relationship')}
                  >
                    Relationship {sortField === 'relationship' && (sortDirection === 'asc' ? '↑' : '↓')}
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Email
                  </th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">
                    Phone
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredGuests.map((guest, idx) => {
                  const name = [guest.title, guest.firstName, guest.lastName, guest.suffix]
                    .filter(Boolean)
                    .join(' ');
                  return (
                    <tr key={`${guest.firstName}-${guest.lastName}-${idx}`} className="hover:bg-platinum/50">
                      <td className="px-4 py-3 text-sm font-medium">{name || '(No name)'}</td>
                      <td className="px-4 py-3 text-sm">
                        <span className={guest.brideOrGroom === 'Bride' ? 'text-strawberry' : 'text-space-indigo'}>
                          {guest.brideOrGroom}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-600">{guest.side}</td>
                      <td className="px-4 py-3 text-sm">
                        {guest.email ? (
                          <a href={`mailto:${guest.email}`} className="text-blue-600 hover:underline text-xs">
                            {guest.email}
                          </a>
                        ) : <span className="text-gray-400">—</span>}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {guest.phone ? (
                          <a href={`tel:${guest.phone}`} className="text-blue-600 hover:underline text-xs">
                            {guest.phone}
                          </a>
                        ) : <span className="text-gray-400">—</span>}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
