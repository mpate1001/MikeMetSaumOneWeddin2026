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
  declined: '#C1121F',   // crimson
  noResponse: '#f59e0b', // amber-500
  notInvited: '#6b7280', // gray-500
  bride: '#780000',      // burgundy
  groom: '#003049',      // navy
};

export function Charts({ stats, relationshipStats }: ChartsProps) {
  const pieData = [
    { name: 'Bride', value: stats.brideGuests, color: COLORS.bride },
    { name: 'Groom', value: stats.groomGuests, color: COLORS.groom },
  ];

  const eventData = stats.eventStats.map(e => ({
    name: e.event.replace("'s Vidhi & Haaldi", "'s V&H"),
    Attending: e.attending,
    Declined: e.declined,
    'No Response': e.noResponse,
  }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      {/* Bride vs Groom Pie Chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold text-navy mb-4">Guests by Side</h3>
        <ResponsiveContainer width="100%" height={250}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={90}
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {pieData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>

      {/* Event Attendance Bar Chart */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold text-navy mb-4">RSVP by Event</h3>
        <ResponsiveContainer width="100%" height={250}>
          <BarChart data={eventData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" />
            <YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 12 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="Attending" stackId="a" fill={COLORS.attending} />
            <Bar dataKey="Declined" stackId="a" fill={COLORS.declined} />
            <Bar dataKey="No Response" stackId="a" fill={COLORS.noResponse} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Relationship Breakdown */}
      <div className="bg-white rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold text-navy mb-4">By Relationship</h3>
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
  );
}
