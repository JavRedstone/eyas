import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts'

const ZONE_COLORS = {
  entrance:   '#f7d046',
  counter:    '#60A5FA',
  'back door': '#34D399',
  'back_door': '#34D399',
  aisles:     '#FBBF24',
}

function zoneColor(z) { return ZONE_COLORS[z?.toLowerCase()] ?? '#7a8ea8' }

export default function DetectionMetrics({ summary, events }) {
  const zoneCounts = summary?.zone_counts ?? {}
  const zoneData = Object.entries(zoneCounts).map(([zone, count]) => ({
    zone: zone.replace(/_/g, ' '),
    count: Number(count),
    fill: zoneColor(zone),
  }))

  // Events over time — group by 10-second buckets
  const bucketSize = 10
  const buckets = {}
  events.forEach(ev => {
    const t = Math.floor(Number(ev.time ?? 0) / bucketSize) * bucketSize
    buckets[t] = (buckets[t] || 0) + 1
  })
  const timelineData = Object.entries(buckets)
    .sort((a, b) => +a[0] - +b[0])
    .map(([t, count]) => ({ t: `${t}s`, count }))

  const totalDetections = Object.values(zoneCounts).reduce((s, v) => s + Number(v), 0)

  return (
    <div className="space-y-6">
      {/* Stat cards */}
      <div className="grid grid-cols-4 gap-3">
        <StatCard label="Total Detections" value={totalDetections} color="text-accent" />
        <StatCard label="Events" value={events.length} color="text-blue-400" />
        <StatCard label="Zones Active" value={zoneData.filter(z => z.count > 0).length} color="text-success" />
        <StatCard label="Avg / Zone" value={zoneData.length ? (totalDetections / zoneData.length).toFixed(1) : '—'} color="text-warning" />
      </div>

      {/* Zone bar chart */}
      {zoneData.length > 0 ? (
        <div>
          <p className="section-label mb-3">Zone Counts</p>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={zoneData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid stroke="#2e4060" strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="zone" tick={{ fill: '#7a8ea8', fontSize: 11 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#7a8ea8', fontSize: 11 }} tickLine={false} axisLine={false} />
              <Tooltip
                cursor={{ fill: 'rgba(255,255,255,0.03)' }}
                content={({ payload, label }) => {
                  if (!payload?.length) return null
                  return (
                    <div className="bg-panel border border-border rounded-lg px-3 py-2 text-xs">
                      <div className="font-medium text-text capitalize">{label}</div>
                      <div className="text-muted">{payload[0].value} detections</div>
                    </div>
                  )
                }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {zoneData.map((d, i) => (
                  <rect key={i} fill={d.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <p className="text-xs text-muted">No zone data yet. Run the pipeline first.</p>
      )}

      {/* Event frequency timeline */}
      {timelineData.length > 0 && (
        <div>
          <p className="section-label mb-3">Event Frequency Over Time</p>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={timelineData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid stroke="#2e4060" strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={({ payload }) => {
                if (!payload?.length) return null
                return (
                  <div className="bg-panel border border-border rounded px-2 py-1 text-xs">
                    {payload[0].payload.t}: {payload[0].value} events
                  </div>
                )
              }} />
              <Line type="monotone" dataKey="count" stroke="#f7d046" strokeWidth={2}
                dot={{ r: 3, fill: '#f7d046', strokeWidth: 0 }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, color }) {
  return (
    <div className="bg-surface rounded-xl border border-border p-3">
      <div className={`text-2xl font-bold font-mono ${color}`}>{value}</div>
      <div className="text-[10px] text-muted mt-1 uppercase tracking-wide">{label}</div>
    </div>
  )
}
