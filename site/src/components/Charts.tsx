import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { SummaryStats } from '../types/guest';

interface ChartsProps {
  stats: SummaryStats;
  relationshipStats: { relationship: string; count: number }[];
}

const COLORS = {
  attending: '#16a34a',  // green-600
  declined: '#D80032',   // Classic Crimson
  noResponse: '#8D99AE', // Lavender Grey
  notInvited: '#6b7280', // gray-500
  bride: '#EF233C',      // Strawberry Red
  groom: '#2B2D42',      // Space Indigo
};

// Short names for events
const eventShortNames: Record<string, string> = {
  "Saumya's Vidhi & Haaldi": "Saumya's V&H",
  "Mahek's Vidhi & Haaldi": "Mahek's V&H",
  "Wedding": "Wedding",
  "Reception": "Reception",
};

interface MiniPieProps {
  title: string;
  brideCount: number;
  groomCount: number;
}

function MiniPieChart({ title, brideCount, groomCount }: MiniPieProps) {
  const data = [
    { name: 'Bride', value: brideCount, color: COLORS.bride },
    { name: 'Groom', value: groomCount, color: COLORS.groom },
  ];
  const total = brideCount + groomCount;

  return (
    <div className="bg-white rounded-lg shadow p-3 flex flex-col items-center">
      <h4 className="text-xs font-semibold text-space-indigo mb-1 text-center truncate w-full">{title}</h4>
      <ResponsiveContainer width="100%" height={120}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={25}
            outerRadius={45}
            paddingAngle={2}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value: number) => [value, '']} />
        </PieChart>
      </ResponsiveContainer>
      <div className="flex gap-3 text-xs mt-1">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-strawberry"></span>
          <span className="text-gray-600">{brideCount}</span>
        </span>
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-space-indigo"></span>
          <span className="text-gray-600">{groomCount}</span>
        </span>
      </div>
      <p className="text-xs text-gray-400 mt-1">{total} total</p>
    </div>
  );
}

export function Charts({ stats, relationshipStats }: ChartsProps) {
  const eventData = stats.eventStats.map(e => ({
    name: e.event.replace("'s Vidhi & Haaldi", "'s V&H"),
    Attending: e.attending,
    Declined: e.declined,
    'No Response': e.noResponse,
  }));

  return (
    <div className="space-y-6 mb-6">
      {/* Guests by Side - Row of pie charts */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold text-space-indigo mb-4">Attending by Side</h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
          {/* Total */}
          <MiniPieChart
            title="Total"
            brideCount={stats.brideGuests}
            groomCount={stats.groomGuests}
          />
          {/* Per-event */}
          {stats.eventStats.map((event) => (
            <MiniPieChart
              key={event.event}
              title={eventShortNames[event.event] || event.event}
              brideCount={event.brideAttending}
              groomCount={event.groomAttending}
            />
          ))}
        </div>
        {/* Legend */}
        <div className="flex justify-center gap-6 mt-4 text-sm">
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-strawberry"></span>
            <span className="text-gray-600">Bride's Side</span>
          </span>
          <span className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-space-indigo"></span>
            <span className="text-gray-600">Groom's Side</span>
          </span>
        </div>
      </div>

      {/* Other Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Event Attendance Bar Chart */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold text-space-indigo mb-4">RSVP by Event</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={eventData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" />
              <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 10 }} />
              <Tooltip />
              <Legend wrapperStyle={{ fontSize: '12px' }} />
              <Bar dataKey="Attending" stackId="a" fill={COLORS.attending} />
              <Bar dataKey="Declined" stackId="a" fill={COLORS.declined} />
              <Bar dataKey="No Response" stackId="a" fill={COLORS.noResponse} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Relationship Breakdown */}
        <div className="bg-white rounded-lg shadow p-4">
          <h3 className="text-lg font-semibold text-space-indigo mb-4">By Relationship</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={relationshipStats.slice(0, 8)}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="relationship"
                tick={{ fontSize: 10 }}
                angle={-45}
                textAnchor="end"
                height={80}
              />
              <YAxis />
              <Tooltip />
              <Bar dataKey="count" fill={COLORS.bride} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
