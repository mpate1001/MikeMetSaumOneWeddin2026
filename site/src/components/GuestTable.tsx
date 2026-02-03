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

// Guest detail modal component
function GuestModal({ guest, onClose }: { guest: Guest; onClose: () => void }) {
  const name = [guest.title, guest.firstName, guest.lastName, guest.suffix]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-2xl max-w-md w-full overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`px-6 py-4 ${guest.brideOrGroom === 'Bride' ? 'bg-strawberry' : 'bg-space-indigo'}`}>
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-xl font-bold text-white">{name || '(No name)'}</h3>
              <p className="text-white/80 text-sm mt-1">{guest.side} - {guest.brideOrGroom}'s Side</p>
            </div>
            <button
              onClick={onClose}
              className="text-white/80 hover:text-white transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Contact Info */}
        <div className="p-6 space-y-4">
          {/* Email */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Email</p>
              {guest.email ? (
                <a href={`mailto:${guest.email}`} className="text-blue-600 hover:underline truncate block">
                  {guest.email}
                </a>
              ) : (
                <span className="text-gray-400">Not provided</span>
              )}
            </div>
          </div>

          {/* Phone */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Phone</p>
              {guest.phone ? (
                <a href={`tel:${guest.phone}`} className="text-green-600 hover:underline">
                  {guest.phone}
                </a>
              ) : (
                <span className="text-gray-400">Not provided</span>
              )}
            </div>
          </div>

          {/* Address */}
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-full bg-purple-100 flex items-center justify-center flex-shrink-0">
              <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs text-gray-500 uppercase tracking-wide">Address</p>
              {guest.address ? (
                <p className="text-gray-700">{guest.address}</p>
              ) : (
                <span className="text-gray-400">Not provided</span>
              )}
            </div>
          </div>
        </div>

        {/* RSVP Status */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-100">
          <p className="text-xs text-gray-500 uppercase tracking-wide mb-3">RSVP Status</p>
          <div className="grid grid-cols-4 gap-2 text-center text-xs">
            <div>
              <p className="text-gray-500 mb-1">S. V&H</p>
              <RSVPBadgeCompact status={guest.saumyaVidhiHaaldi} />
            </div>
            <div>
              <p className="text-gray-500 mb-1">M. V&H</p>
              <RSVPBadgeCompact status={guest.mahekVidhiHaaldi} />
            </div>
            <div>
              <p className="text-gray-500 mb-1">Wedding</p>
              <RSVPBadgeCompact status={guest.wedding} />
            </div>
            <div>
              <p className="text-gray-500 mb-1">Reception</p>
              <RSVPBadgeCompact status={guest.reception} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function RSVPBadgeCompact({ status }: { status: RSVPStatus }) {
  const config: Record<RSVPStatus, { bg: string; label: string }> = {
    Attending: { bg: 'bg-green-100 text-green-700', label: 'Yes' },
    Declined: { bg: 'bg-red-100 text-crimson', label: 'No' },
    'No Response': { bg: 'bg-slate-100 text-lavender-grey', label: '?' },
    'Not Invited': { bg: 'bg-gray-100 text-gray-400', label: '—' },
  };
  const { bg, label } = config[status];
  return <span className={`px-2 py-1 rounded-full font-medium ${bg}`}>{label}</span>;
}

interface GuestTableProps {
  guests: Guest[];
  title?: string;
  showSearch?: boolean;
  accentColor?: 'strawberry' | 'space-indigo';
}

function RSVPBadge({ status, compact = false }: { status: RSVPStatus; compact?: boolean }) {
  const config: Record<RSVPStatus, { bg: string; icon: React.ReactNode; label: string }> = {
    Attending: {
      bg: 'bg-green-100 text-green-700',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
        </svg>
      ),
      label: 'Yes',
    },
    Declined: {
      bg: 'bg-red-100 text-crimson',
      icon: (
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M6 18L18 6M6 6l12 12" />
        </svg>
      ),
      label: 'No',
    },
    'No Response': {
      bg: 'bg-slate-100 text-lavender-grey',
      icon: <span className="text-sm font-medium">?</span>,
      label: '?',
    },
    'Not Invited': {
      bg: 'bg-gray-100 text-gray-400',
      icon: <span className="text-xs">—</span>,
      label: '—',
    },
  };

  const { bg, icon, label } = config[status];

  // Icon-only mode for table cells
  if (!compact) {
    return (
      <span className={`inline-flex items-center justify-center w-7 h-7 rounded-full ${bg}`} title={status}>
        {icon}
      </span>
    );
  }

  // Compact text mode for mobile cards
  return (
    <span className={`px-2 py-1 text-xs rounded-full font-medium ${bg}`}>
      {label}
    </span>
  );
}

// Mobile card component for each guest
function GuestCard({ guest }: { guest: Guest }) {
  const name = [guest.title, guest.firstName, guest.lastName, guest.suffix]
    .filter(Boolean)
    .join(' ');

  return (
    <div className="bg-white border-b border-gray-200 p-4 hover:bg-platinum/30 transition-colors">
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
      <p className="text-[10px] text-gray-400 mt-2 text-center">Tap for contact info</p>
    </div>
  );
}

export function GuestTable({ guests, title, showSearch = false, accentColor }: GuestTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [grouping, setGrouping] = useState<GroupingState>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [rsvpFilter, setRsvpFilter] = useState<RSVPStatus | 'All'>('All');
  const [selectedGuest, setSelectedGuest] = useState<Guest | null>(null);

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
        header: 'S.V&H',
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
      {
        accessorKey: 'mahekVidhiHaaldi',
        header: 'M.V&H',
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
      {
        accessorKey: 'wedding',
        header: 'Wed',
        cell: ({ getValue }) => <RSVPBadge status={getValue() as RSVPStatus} />,
      },
      {
        accessorKey: 'reception',
        header: 'Rec',
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
    const headers = ['Title', 'First Name', 'Last Name', 'Suffix', 'Side', 'Relationship', "Saumya's V&H", "Mahek's V&H", 'Wedding', 'Reception', 'Email', 'Phone', 'Address'];
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
            <div
              key={`${guest.firstName}-${guest.lastName}-${idx}`}
              onClick={() => setSelectedGuest(guest)}
              className="cursor-pointer"
            >
              <GuestCard guest={guest} />
            </div>
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
                  className={`hover:bg-platinum/50 cursor-pointer ${row.getIsGrouped() ? 'bg-gray-100 font-semibold' : ''}`}
                  onClick={() => !row.getIsGrouped() && setSelectedGuest(row.original)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-sm whitespace-nowrap">
                      {cell.getIsGrouped() ? (
                        <>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              row.getToggleExpandedHandler()();
                            }}
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

      {/* Guest Detail Modal */}
      {selectedGuest && (
        <GuestModal guest={selectedGuest} onClose={() => setSelectedGuest(null)} />
      )}
    </div>
  );
}
