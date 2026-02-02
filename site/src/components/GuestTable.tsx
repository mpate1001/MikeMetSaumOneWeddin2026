import { useMemo, useState } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  getGroupedRowModel,
  flexRender,
  type ColumnDef,
  type SortingState,
  type GroupingState,
} from '@tanstack/react-table';
import type { Guest, RSVPStatus } from '../types/guest';

interface GuestTableProps {
  guests: Guest[];
  title?: string;
  showSearch?: boolean;
  accentColor?: 'strawberry' | 'space-indigo';
}

function RSVPBadge({ status, compact = false }: { status: RSVPStatus; compact?: boolean }) {
  const colors: Record<RSVPStatus, string> = {
    Attending: 'bg-green-100 text-green-800',
    Declined: 'bg-red-100 text-crimson',
    'No Response': 'bg-slate-100 text-lavender-grey',
    'Not Invited': 'bg-gray-100 text-gray-500',
  };

  const shortLabels: Record<RSVPStatus, string> = {
    Attending: 'Yes',
    Declined: 'No',
    'No Response': '—',
    'Not Invited': 'N/A',
  };

  return (
    <span className={`px-2 py-1 text-xs rounded-full font-medium ${colors[status]}`}>
      {compact ? shortLabels[status] : status}
    </span>
  );
}

// Mobile card component for each guest
function GuestCard({ guest }: { guest: Guest }) {
  const name = [guest.title, guest.firstName, guest.lastName, guest.suffix]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <div className="flex justify-between items-start mb-2">
        <div>
          <p className="font-medium text-space-indigo">{name || '(No name)'}</p>
          <p className="text-xs text-gray-500">{guest.side}</p>
        </div>
        <span className={`text-xs font-medium px-2 py-1 rounded ${
          guest.brideOrGroom === 'Bride' ? 'bg-strawberry/10 text-strawberry' : 'bg-space-indigo/10 text-space-indigo'
        }`}>
          {guest.brideOrGroom}
        </span>
      </div>
      <div className="grid grid-cols-4 gap-2 mt-3">
        <div className="text-center">
          <p className="text-[10px] text-gray-400 mb-1">S. V&H</p>
          <RSVPBadge status={guest.saumyaVidhiHaaldi} compact />
        </div>
        <div className="text-center">
          <p className="text-[10px] text-gray-400 mb-1">M. V&H</p>
          <RSVPBadge status={guest.mahekVidhiHaaldi} compact />
        </div>
        <div className="text-center">
          <p className="text-[10px] text-gray-400 mb-1">Wedding</p>
          <RSVPBadge status={guest.wedding} compact />
        </div>
        <div className="text-center">
          <p className="text-[10px] text-gray-400 mb-1">Reception</p>
          <RSVPBadge status={guest.reception} compact />
        </div>
      </div>
    </div>
  );
}

export function GuestTable({ guests, title, showSearch = false, accentColor }: GuestTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [grouping, setGrouping] = useState<GroupingState>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [rsvpFilter, setRsvpFilter] = useState<RSVPStatus | 'All'>('All');

  // Filter guests based on search and RSVP filter
  const filteredGuests = useMemo(() => {
    return guests.filter((guest) => {
      // Search filter
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        const fullName = `${guest.firstName} ${guest.lastName}`.toLowerCase();
        const relationship = guest.side.toLowerCase();
        if (!fullName.includes(query) && !relationship.includes(query)) {
          return false;
        }
      }

      // RSVP filter (based on wedding event)
      if (rsvpFilter !== 'All' && guest.wedding !== rsvpFilter) {
        return false;
      }

      return true;
    });
  }, [guests, searchQuery, rsvpFilter]);

  const columns = useMemo<ColumnDef<Guest>[]>(
    () => [
      {
        accessorFn: (row) => `${row.firstName} ${row.lastName}`.trim(),
        id: 'name',
        header: 'Name',
        cell: ({ row }) => {
          const guest = row.original;
          const parts = [guest.title, guest.firstName, guest.lastName, guest.suffix]
            .filter(Boolean)
            .join(' ');
          return <span className="font-medium">{parts || '(No name)'}</span>;
        },
      },
      {
        accessorKey: 'brideOrGroom',
        header: 'Side',
        cell: ({ getValue }) => {
          const value = getValue() as string;
          return (
            <span className={value === 'Bride' ? 'text-strawberry' : 'text-space-indigo'}>
              {value}
            </span>
          );
        },
      },
      {
        accessorKey: 'side',
        header: 'Relationship',
      },
      {
        accessorKey: 'saumyaVidhiHaaldi',
        header: "Saumya's V&H",
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
      {
        accessorKey: 'mahekVidhiHaaldi',
        header: "Mahek's V&H",
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
      {
        accessorKey: 'wedding',
        header: 'Wedding',
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
      {
        accessorKey: 'reception',
        header: 'Reception',
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
    ],
    []
  );

  const table = useReactTable({
    data: filteredGuests,
    columns,
    state: {
      sorting,
      grouping,
    },
    onSortingChange: setSorting,
    onGroupingChange: setGrouping,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getGroupedRowModel: getGroupedRowModel(),
    initialState: {
      pagination: {
        pageSize: 50,
      },
    },
  });

  const exportToCSV = () => {
    const headers = ['Title', 'First Name', 'Last Name', 'Suffix', 'Side', 'Relationship', "Saumya's V&H", "Mahek's V&H", 'Wedding', 'Reception'];
    const rows = filteredGuests.map(g => [
      g.title,
      g.firstName,
      g.lastName,
      g.suffix,
      g.brideOrGroom,
      g.side,
      g.saumyaVidhiHaaldi,
      g.mahekVidhiHaaldi,
      g.wedding,
      g.reception,
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `guest-list-${title?.toLowerCase().replace(/\s+/g, '-') || 'export'}-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get paginated guests for mobile card view
  const paginatedGuests = table.getRowModel().rows.map(row => row.original);

  // Accent color classes
  const accentClasses = {
    title: accentColor === 'strawberry' ? 'text-strawberry' : 'text-space-indigo',
    border: accentColor === 'strawberry' ? 'border-strawberry' : 'border-space-indigo',
    bg: accentColor === 'strawberry' ? 'bg-strawberry' : 'bg-space-indigo',
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Table Header with Title, Search, and Controls */}
      <div className={`px-4 py-4 border-b border-gray-200 ${accentColor ? `border-l-4 ${accentClasses.border}` : ''}`}>
        {/* Title Row */}
        {title && (
          <div className="flex items-center justify-between mb-3">
            <h2 className={`text-lg font-bold ${accentClasses.title}`}>
              {title}
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({filteredGuests.length} {filteredGuests.length === 1 ? 'guest' : 'guests'})
              </span>
            </h2>
            <button
              onClick={exportToCSV}
              className={`px-3 py-1 text-sm ${accentClasses.bg} text-platinum rounded hover:opacity-90 transition-colors`}
            >
              Export CSV
            </button>
          </div>
        )}

        {/* Search and Filter Row */}
        <div className="flex flex-wrap items-center gap-3">
          {showSearch && (
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
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    ×
                  </button>
                )}
              </div>
            </div>
          )}

          {showSearch && (
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600 whitespace-nowrap">RSVP:</label>
              <select
                value={rsvpFilter}
                onChange={(e) => setRsvpFilter(e.target.value as RSVPStatus | 'All')}
                className="px-2 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-space-indigo/20 focus:border-space-indigo outline-none"
              >
                <option value="All">All</option>
                <option value="Attending">Attending</option>
                <option value="Declined">Declined</option>
                <option value="No Response">No Response</option>
              </select>
            </div>
          )}

          <div className="flex items-center gap-2">
            <label className="text-sm text-gray-600 whitespace-nowrap hidden sm:inline">Group:</label>
            <select
              value={grouping[0] || ''}
              onChange={(e) => setGrouping(e.target.value ? [e.target.value] : [])}
              className="px-2 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-space-indigo/20 focus:border-space-indigo outline-none"
            >
              <option value="">None</option>
              <option value="brideOrGroom">Side</option>
              <option value="side">Relationship</option>
              <option value="wedding">Wedding RSVP</option>
            </select>
          </div>

          {!title && (
            <button
              onClick={exportToCSV}
              className="px-3 py-2 text-sm bg-space-indigo text-platinum rounded-lg hover:bg-space-indigo/90 transition-colors"
            >
              Export CSV
            </button>
          )}
        </div>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden">
        {paginatedGuests.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No guests found matching your search.
          </div>
        ) : (
          paginatedGuests.map((guest, idx) => (
            <GuestCard key={`${guest.firstName}-${guest.lastName}-${idx}`} guest={guest} />
          ))
        )}
      </div>

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        {filteredGuests.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            No guests found matching your search.
          </div>
        ) : (
          <table className="w-full">
            <thead className="bg-gray-50">
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th
                      key={header.id}
                      className="px-4 py-3 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      <div className="flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {{
                          asc: ' ↑',
                          desc: ' ↓',
                        }[header.column.getIsSorted() as string] ?? null}
                      </div>
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody className="divide-y divide-gray-200">
              {table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className={`hover:bg-platinum/50 ${row.getIsGrouped() ? 'bg-gray-100 font-semibold' : ''}`}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-sm whitespace-nowrap">
                      {cell.getIsGrouped() ? (
                        <>
                          <button
                            onClick={row.getToggleExpandedHandler()}
                            className="mr-2"
                          >
                            {row.getIsExpanded() ? '▼' : '▶'}
                          </button>
                          {flexRender(cell.column.columnDef.cell, cell.getContext())} ({row.subRows.length})
                        </>
                      ) : cell.getIsAggregated() ? null : cell.getIsPlaceholder() ? null : (
                        flexRender(cell.column.columnDef.cell, cell.getContext())
                      )}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {filteredGuests.length > 0 && (
        <div className="px-4 py-3 border-t border-gray-200 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Prev
            </button>
            <button
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
              className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
            >
              Next
            </button>
          </div>
          <span className="text-sm text-gray-600">
            Page {table.getState().pagination.pageIndex + 1} of {table.getPageCount()}
          </span>
          <select
            value={table.getState().pagination.pageSize}
            onChange={(e) => table.setPageSize(Number(e.target.value))}
            className="px-2 py-1 text-sm border rounded"
          >
            {[25, 50, 100, 200].map((size) => (
              <option key={size} value={size}>
                {size} per page
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
