import { RadialBarChart, RadialBar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'

const RISK_CONFIG = {
  high:   { color: '#F87171', label: 'High Risk',   pct: 90 },
  medium: { color: '#FBBF24', label: 'Medium Risk',  pct: 55 },
  low:    { color: '#34D399', label: 'Low Risk',     pct: 25 },
  none:   { color: '#7a8ea8', label: 'No Risk',      pct: 5  },
}

export default function SummaryAlerts({ summary }) {
  if (!summary) {
    return <Typography variant="caption" color="text.secondary">No analysis yet. Run the pipeline first.</Typography>
  }

  const risk   = (summary.risk_level ?? 'none').toLowerCase()
  const rc     = RISK_CONFIG[risk] || RISK_CONFIG.none
  const flags  = normalizeFlags(summary.flags ?? [])
  const suspiciousClips = Array.isArray(summary.suspicious_clips) ? summary.suspicious_clips : []
  const text   = summary.summary ?? summary.overnight_summary ?? ''
  const transT = summary.translation_time_ms

  const gaugeData = [
    { name: 'Risk', value: rc.pct, fill: rc.color },
    { name: 'bg',   value: 100 - rc.pct, fill: '#1f2833' },
  ]

  const flagTypes = {}
  flags.forEach(f => {
    const t = inferFlagType(f)
    flagTypes[t] = (flagTypes[t] || 0) + 1
  })
  const pieData = Object.entries(flagTypes).map(([name, value]) => ({ name, value }))
  const PIE_COLORS = ['#f7d046', '#F87171', '#FBBF24', '#60A5FA', '#34D399']

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Risk gauge + flag types */}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2.5 }}>
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>Risk Level</Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <ResponsiveContainer width={100} height={100}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="65%" outerRadius="100%"
                startAngle={210} endAngle={-30} data={gaugeData} barSize={10}>
                <RadialBar dataKey="value" cornerRadius={5} />
              </RadialBarChart>
            </ResponsiveContainer>
            <Box>
              <Typography variant="h5" fontWeight={700} style={{ color: rc.color }}>{rc.pct}%</Typography>
              <Typography variant="body2" fontWeight={500} style={{ color: rc.color }}>{rc.label}</Typography>
              {transT && <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>Translation: {transT}ms</Typography>}
            </Box>
          </Box>
        </Box>

        {pieData.length > 0 && (
          <Box>
            <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>Flag Types</Typography>
            <ResponsiveContainer width="100%" height={100}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={28} outerRadius={45}
                  dataKey="value" paddingAngle={3}>
                  {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip content={({ payload }) => {
                  if (!payload?.length) return null
                  const { name, value } = payload[0].payload
                  return (
                    <div style={{ background: '#1f2833', border: '1px solid #2e4060', borderRadius: 8, padding: '4px 8px', fontSize: '0.75rem', color: '#e5e1d8' }}>
                      {name}: {value}
                    </div>
                  )
                }} />
              </PieChart>
            </ResponsiveContainer>
          </Box>
        )}
      </Box>

      {/* Summary text */}
      <Box>
        <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>Overnight Summary</Typography>
        <Paper sx={{ p: 1.5, bgcolor: 'rgba(20,45,79,0.5)' }}>
          <Typography variant="body2" sx={{ lineHeight: 1.7, color: 'text.primary' }}>
            {text || <span style={{ color: '#7a8ea8' }}>No summary available.</span>}
          </Typography>
        </Paper>
      </Box>

      {/* Flagged items */}
      {flags.length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>Potential Concerns ({flags.length})</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
            {flags.map((f, i) => (
              <Box key={i} sx={{ display: 'flex', alignItems: 'flex-start', gap: 1, px: 1.5, py: 1, borderRadius: 1.5, bgcolor: 'rgba(248,113,113,0.05)', border: '1px solid rgba(248,113,113,0.2)' }}>
                <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'error.main', mt: 0.75, flexShrink: 0 }} />
                <Box sx={{ minWidth: 0 }}>
                  <Typography variant="caption" fontWeight={500} sx={{ display: 'block', color: 'text.primary' }}>{f.label}</Typography>
                  <Typography variant="caption" color="text.secondary">{f.detail}</Typography>
                </Box>
              </Box>
            ))}
          </Box>
        </Box>
      )}

      {/* Suspicious clips */}
      {suspiciousClips.length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>Suspicious Clips ({suspiciousClips.length})</Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
            {suspiciousClips.map((clip, i) => (
              <Chip
                key={i}
                label={String(clip)}
                variant="outlined"
                size="small"
                sx={{ borderColor: 'rgba(247,208,70,0.3)', bgcolor: 'rgba(247,208,70,0.05)', color: 'text.primary' }}
              />
            ))}
          </Box>
        </Box>
      )}
    </Box>
  )
}

function normalizeFlags(flags) {
  return flags.map(flag => {
    if (typeof flag === 'string') {
      return { label: inferFlagLabel(flag), detail: flag, text: flag }
    }
    const detail = flag.description ?? flag.detail ?? flag.text ?? JSON.stringify(flag)
    return {
      label: flag.type ? inferFlagLabel(flag.type) : inferFlagLabel(detail),
      detail,
      text: `${flag.type ?? ''} ${detail}`.trim(),
    }
  })
}

function inferFlagLabel(value) {
  const text = String(value).toLowerCase()
  if (text.includes('pickup') || text.includes('taken') || text.includes('take') || text.includes('conceal') || text.includes('held')) return 'Theft-related'
  if (text.includes('door') || text.includes('entrance') || text.includes('exit')) return 'Entry / Exit'
  if (text.includes('stationary') || text.includes('loiter') || text.includes('idle') || text.includes('wait')) return 'Loitering / Stationary'
  if (text.includes('interaction') || text.includes('interact')) return 'Interaction'
  return 'Other'
}

function inferFlagType(flag) {
  return inferFlagLabel(flag.text || flag.label || flag.detail).toLowerCase().replace(/\s+/g, '_')
}
