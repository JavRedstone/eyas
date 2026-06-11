import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line, Legend
} from 'recharts'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

const ZONE_COLORS = {
  entrance:    '#f7d046',
  counter:     '#60A5FA',
  'back door': '#34D399',
  'back_door': '#34D399',
  aisles:      '#FBBF24',
}

function zoneColor(z) { return ZONE_COLORS[z?.toLowerCase()] ?? '#7a8ea8' }

export default function DetectionMetrics({ summary, events }) {
  const zoneCounts = summary?.zone_counts ?? {}
  const zoneData = Object.entries(zoneCounts).map(([zone, count]) => ({
    zone: zone.replace(/_/g, ' '),
    count: Number(count),
    fill: zoneColor(zone),
  }))

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

  const STAT_COLORS = {
    'Total Detections': '#f7d046',
    'Events':           '#60A5FA',
    'Zones Active':     '#34D399',
    'Avg / Zone':       '#f7d046',
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Stat cards */}
      <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 1.5 }}>
        <StatCard label="Total Detections" value={totalDetections} color={STAT_COLORS['Total Detections']} />
        <StatCard label="Events" value={events.length} color={STAT_COLORS['Events']} />
        <StatCard label="Zones Active" value={zoneData.filter(z => z.count > 0).length} color={STAT_COLORS['Zones Active']} />
        <StatCard label="Avg / Zone" value={zoneData.length ? (totalDetections / zoneData.length).toFixed(1) : '—'} color={STAT_COLORS['Avg / Zone']} />
      </Box>

      {/* Zone bar chart */}
      {zoneData.length > 0 ? (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>Zone Counts</Typography>
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
                    <div style={{ background: '#1f2833', border: '1px solid #2e4060', borderRadius: 8, padding: '8px 12px', fontSize: '0.75rem', color: '#e5e1d8' }}>
                      <div style={{ fontWeight: 500, textTransform: 'capitalize' }}>{label}</div>
                      <div style={{ color: '#7a8ea8' }}>{payload[0].value} detections</div>
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
        </Box>
      ) : (
        <Typography variant="caption" color="text.secondary">No zone data yet. Run the pipeline first.</Typography>
      )}

      {/* Event frequency timeline */}
      {timelineData.length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>Event Frequency Over Time</Typography>
          <ResponsiveContainer width="100%" height={140}>
            <LineChart data={timelineData} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
              <CartesianGrid stroke="#2e4060" strokeDasharray="3 3" />
              <XAxis dataKey="t" tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false} />
              <YAxis tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false} />
              <Tooltip content={({ payload }) => {
                if (!payload?.length) return null
                return (
                  <div style={{ background: '#1f2833', border: '1px solid #2e4060', borderRadius: 8, padding: '8px 12px', fontSize: '0.75rem', color: '#e5e1d8' }}>
                    {payload[0].payload.t}: {payload[0].value} events
                  </div>
                )
              }} />
              <Line type="monotone" dataKey="count" stroke="#f7d046" strokeWidth={2}
                dot={{ r: 3, fill: '#f7d046', strokeWidth: 0 }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </Box>
      )}
    </Box>
  )
}

function StatCard({ label, value, color }) {
  return (
    <Paper sx={{ p: 1.5, bgcolor: 'rgba(20,45,79,0.5)' }}>
      <Typography variant="h5" fontWeight={700} sx={{ fontFamily: 'monospace', color }}>
        {value}
      </Typography>
      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
        {label}
      </Typography>
    </Paper>
  )
}
