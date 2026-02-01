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
}

function RSVPBadge({ status }: { status: RSVPStatus }) {
  const colors: Record<RSVPStatus, string> = {
    Attending: 'bg-green-100 text-green-800',
    Declined: 'bg-red-100 text-red-800',
    'No Response': 'bg-amber-100 text-amber-800',
    'Not Invited': 'bg-gray-100 text-gray-500',
  };

  return (
    <span className={`px-2 py-1 text-xs rounded-full font-medium ${colors[status]}`}>
      {status}
    </span>
  );
}

export function GuestTable({ guests }: GuestTableProps) {
  const [sorting, setSorting] = useState<SortingState>([]);
  const [grouping, setGrouping] = useState<GroupingState>([]);

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
            <span className={value === 'Bride' ? 'text-burgundy' : 'text-navy'}>
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
    data: guests,
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
    const rows = guests.map(g => [
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
    a.download = `guest-list-export-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      {/* Table Header */}
      <div className="px-4 py-3 border-b border-gray-200 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Group by:</label>
          <select
            value={grouping[0] || ''}
            onChange={(e) => setGrouping(e.target.value ? [e.target.value] : [])}
            className="px-2 py-1 text-sm border border-gray-300 rounded"
          >
            <option value="">None</option>
            <option value="brideOrGroom">Side</option>
            <option value="side">Relationship</option>
            <option value="wedding">Wedding RSVP</option>
          </select>
        </div>
        <button
          onClick={exportToCSV}
          className="px-3 py-1 text-sm bg-navy text-cream rounded hover:bg-navy/90 transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
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
                className={`hover:bg-cream/30 ${row.getIsGrouped() ? 'bg-gray-100 font-semibold' : ''}`}
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
      </div>

      {/* Pagination */}
      <div className="px-4 py-3 border-t border-gray-200 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
            className="px-3 py-1 text-sm border rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-100"
          >
            Previous
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
              Show {size}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
