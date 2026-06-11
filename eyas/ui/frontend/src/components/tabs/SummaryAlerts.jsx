import { RadialBarChart, RadialBar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'

const RISK_CONFIG = {
  high:   { color: '#F87171', label: 'High Risk',   pct: 90 },
  medium: { color: '#FBBF24', label: 'Medium Risk',  pct: 55 },
  low:    { color: '#34D399', label: 'Low Risk',     pct: 25 },
  none:   { color: '#6B728E', label: 'No Risk',      pct: 5  },
}

export default function SummaryAlerts({ summary }) {
  if (!summary) {
    return <p className="text-xs text-muted">No analysis yet. Run the pipeline first.</p>
  }

  const risk   = (summary.risk_level ?? 'none').toLowerCase()
  const rc     = RISK_CONFIG[risk] || RISK_CONFIG.none
  const flags  = normalizeFlags(summary.flags ?? [])
  const suspiciousClips = Array.isArray(summary.suspicious_clips) ? summary.suspicious_clips : []
  const text   = summary.summary ?? summary.overnight_summary ?? ''
  const transT = summary.translation_time_ms

  const gaugeData = [
    { name: 'Risk', value: rc.pct, fill: rc.color },
    { name: 'bg',   value: 100 - rc.pct, fill: '#1E2436' },
  ]

  // Flags by inferred type for mini pie
  const flagTypes = {}
  flags.forEach(f => {
    const t = inferFlagType(f)
    flagTypes[t] = (flagTypes[t] || 0) + 1
  })
  const pieData = Object.entries(flagTypes).map(([name, value]) => ({ name, value }))
  const PIE_COLORS = ['#E8682A', '#F87171', '#FBBF24', '#60A5FA', '#34D399']

  return (
    <div className="space-y-6">
      {/* Risk gauge + summary */}
      <div className="grid grid-cols-2 gap-5">
        <div>
          <p className="section-label mb-3">Risk Level</p>
          <div className="flex items-center gap-4">
            <ResponsiveContainer width={100} height={100}>
              <RadialBarChart cx="50%" cy="50%" innerRadius="65%" outerRadius="100%"
                startAngle={210} endAngle={-30} data={gaugeData} barSize={10}>
                <RadialBar dataKey="value" cornerRadius={5} />
              </RadialBarChart>
            </ResponsiveContainer>
            <div>
              <div className="text-2xl font-bold" style={{ color: rc.color }}>{rc.pct}%</div>
              <div className="text-sm font-medium" style={{ color: rc.color }}>{rc.label}</div>
              {transT && <div className="text-[10px] text-muted mt-1">Translation: {transT}ms</div>}
            </div>
          </div>
        </div>

        {pieData.length > 0 && (
          <div>
            <p className="section-label mb-3">Flag Types</p>
            <ResponsiveContainer width="100%" height={100}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={28} outerRadius={45}
                  dataKey="value" paddingAngle={3}>
                  {pieData.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
                </Pie>
                <Tooltip content={({ payload }) => {
                  if (!payload?.length) return null
                  const { name, value } = payload[0].payload
                  return <div className="bg-panel border border-border rounded px-2 py-1 text-xs">{name}: {value}</div>
                }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Summary text */}
      <div>
        <p className="section-label mb-2">Overnight Summary</p>
        <div className="bg-surface rounded-lg p-3 text-sm text-text/90 leading-relaxed border border-border">
          {text || <span className="text-muted">No summary available.</span>}
        </div>
      </div>

      {/* Flagged items */}
      {flags.length > 0 && (
        <div>
          <p className="section-label mb-2">Potential Concerns ({flags.length})</p>
          <div className="space-y-2">
            {flags.map((f, i) => (
              <div key={i} className="flex items-start gap-2 px-3 py-2 rounded-lg bg-danger/5 border border-danger/20">
                <div className="w-1.5 h-1.5 rounded-full bg-danger mt-1.5 shrink-0" />
                <div className="min-w-0">
                  <div className="text-xs font-medium text-text">{f.label}</div>
                  <div className="text-xs text-muted">{f.detail}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Suspicious clips */}
      {suspiciousClips.length > 0 && (
        <div>
          <p className="section-label mb-2">Suspicious Clips ({suspiciousClips.length})</p>
          <div className="flex flex-wrap gap-2">
            {suspiciousClips.map((clip, i) => (
              <span key={i} className="inline-flex items-center rounded-full border border-accent/30 bg-accent/5 px-3 py-1 text-xs text-text">
                {String(clip)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function normalizeFlags(flags) {
  return flags
    .map(flag => {
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
