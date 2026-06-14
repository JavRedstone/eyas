import { RadialBarChart, RadialBar, PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import { t } from '../../i18n.js'
import { displaySummaryText } from '../../display.js'

function riskConfig(risk, language) {
  const configs = {
    high:   { color: '#F87171', pct: 90 },
    medium: { color: '#FBBF24', pct: 55 },
    low:    { color: '#34D399', pct: 25 },
    none:   { color: '#7a8ea8', pct: 5  },
  }
  const c = configs[risk] || configs.none
  return { ...c, label: t(language, `risk.${risk === 'none' ? 'none' : risk}`) }
}

export default function SummaryAlerts({ summary, language = 'English' }) {
  if (!summary) {
    return <Typography variant="caption" color="text.secondary">{t(language, 'summary.empty')}</Typography>
  }

  const risk   = (summary.risk_level ?? 'none').toLowerCase()
  const rc     = riskConfig(risk, language)
  const flags  = normalizeFlags(summary, language)
  const suspiciousClips = Array.isArray(summary.suspicious_clips) ? summary.suspicious_clips : []
  const text   = displaySummaryText(summary, language)
  const transT = summary.translation_time_ms
  const perCam = Array.isArray(summary.per_cam) ? summary.per_cam : []

  const gaugeData = [
    { name: 'Risk', value: rc.pct, fill: rc.color },
    { name: 'bg',   value: 100 - rc.pct, fill: '#1f2833' },
  ]

  const flagTypes = {}
  flags.forEach(f => {
    const ft = f.flagType
    flagTypes[ft] = (flagTypes[ft] || 0) + 1
  })
  const pieData = Object.entries(flagTypes).map(([name, value]) => ({ name, value }))
  const PIE_COLORS = ['#f7d046', '#F87171', '#FBBF24', '#60A5FA', '#34D399']

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      {/* Risk gauge + flag types */}
      <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2.5 }}>
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>{t(language, 'summary.risk_level')}</Typography>
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
              {transT && <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>{t(language, 'summary.translation', { ms: transT })}</Typography>}
            </Box>
          </Box>
        </Box>

        {pieData.length > 0 && (
          <Box>
            <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>{t(language, 'summary.flag_types')}</Typography>
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
        <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>
          {perCam.length > 0 ? t(language, 'summary.total') : t(language, 'summary.overnight')}
        </Typography>
        <Paper sx={{ p: 1.5, bgcolor: 'rgba(20,45,79,0.5)' }}>
          <Typography variant="body2" sx={{ lineHeight: 1.7, color: 'text.primary', whiteSpace: 'pre-line' }}>
            {text || <span style={{ color: '#7a8ea8' }}>{t(language, 'summary.no_summary')}</span>}
          </Typography>
        </Paper>
      </Box>

      {/* Per-camera breakdown — full SummaryAlerts output copied for each clip */}
      {perCam.length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>{t(language, 'summary.per_cam')}</Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            {perCam.map((cam, i) => (
              <Paper key={i} sx={{ p: 2, bgcolor: 'rgba(14,30,54,0.6)', border: '1px solid', borderColor: 'divider' }}>
                <Typography variant="caption" fontWeight={700} sx={{ display: 'block', mb: 1.5, color: 'primary.main', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                  — {cam.name} —
                </Typography>
                <SummaryAlerts summary={cam} language={language} />
              </Paper>
            ))}
          </Box>
        </Box>
      )}

      {/* Flagged items — hide at top level when per-cam breakdown is shown (each cam has its own) */}
      {flags.length > 0 && perCam.length === 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>{t(language, 'summary.concerns', { count: flags.length })}</Typography>
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

      {/* Suspicious clips — hide at top level when per-cam breakdown is shown */}
      {suspiciousClips.length > 0 && perCam.length === 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>{t(language, 'summary.suspicious', { count: suspiciousClips.length })}</Typography>
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

function inferFlagKey(value) {
  const text = String(value).toLowerCase()
  if (text.includes('pickup') || text.includes('taken') || text.includes('take') || text.includes('conceal') || text.includes('held')) return 'flag.theft'
  if (text.includes('door') || text.includes('entrance') || text.includes('exit')) return 'flag.entry_exit'
  if (text.includes('stationary') || text.includes('loiter') || text.includes('idle') || text.includes('wait')) return 'flag.loitering'
  if (text.includes('interaction') || text.includes('interact')) return 'flag.interaction'
  return 'flag.other'
}

function normalizeFlags(summary, language) {
  const english = summary.flags ?? []
  const korean = summary.flags_ko
  const source = (language === '한국어' && korean?.length) ? korean : english
  return source.map((flag, i) => {
    const englishFlag = english[i]
    if (typeof flag === 'string') {
      const key = inferFlagKey(typeof englishFlag === 'string' ? englishFlag : flag)
      return { label: t(language, key), detail: flag, text: flag, flagType: t('English', key) }
    }
    const detail = flag.description ?? flag.detail ?? flag.text ?? JSON.stringify(flag)
    const rawText = `${flag.type ?? ''} ${detail}`.trim()
    const key = flag.type ? inferFlagKey(flag.type) : inferFlagKey(detail)
    return { label: t(language, key), detail, text: rawText, flagType: t('English', key) }
  })
}
