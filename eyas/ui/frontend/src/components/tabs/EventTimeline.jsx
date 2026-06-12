import { useState, useMemo } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { RefreshCw, Loader2 } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Chip from '@mui/material/Chip'
import IconButton from '@mui/material/IconButton'
import MuiTooltip from '@mui/material/Tooltip'
import Table from '@mui/material/Table'
import TableBody from '@mui/material/TableBody'
import TableCell from '@mui/material/TableCell'
import TableContainer from '@mui/material/TableContainer'
import TableHead from '@mui/material/TableHead'
import TableRow from '@mui/material/TableRow'
import { t } from '../../i18n.js'

const KIND_COLORS = {
  person:      '#e87030',
  vehicle:     '#60A5FA',
  animal:      '#34D399',
  intrusion:   '#EF4444',
  loitering:   '#FBBF24',
  pickup:      '#FF2222',
  suspicious:  '#FBBF24',
  observation: '#8B93A9',
  default:     '#7a8ea8',
}

function kindColor(kind = '') {
  return KIND_COLORS[String(kind).toLowerCase()] || KIND_COLORS.default
}

function deriveKind(ev) {
  if (ev.kind) return ev.kind
  if (ev.event_type) return ev.event_type
  if (ev.pickup_confirmed) return 'pickup'
  if (ev.held_objects?.length) return 'suspicious'
  return 'observation'
}

function clipLabel(name = '') {
  const stem = name.replace(/\.[^.]+$/, '')
  const parts = stem.split('_')
  if (parts.length >= 3 && /^\d{8}$/.test(parts[0]) && /^\d{6}$/.test(parts[1]))
    return parts.slice(2).join('_')
  return stem.length > 14 ? stem.slice(-14) : stem || 'clip'
}

function ScatterDot({ cx, cy, payload }) {
  if (cx == null || cy == null) return null
  return <circle cx={cx} cy={cy} r={5} fill={kindColor(payload.kind)} fillOpacity={0.85} stroke="none" />
}

export default function EventTimeline({ client, events, outputDir, onSeekVideo, setClipSrc, language = 'English' }) {
  const [loadingClip, setLoading] = useState(false)
  const [loadingIdx, setLoadingIdx] = useState(null)

  const sourceVideos = useMemo(() => {
    const names = new Set(events.map(e => e.source_video).filter(Boolean))
    return [...names]
  }, [events])
  const multiSource = sourceVideos.length > 1
  const numBands = Math.max(sourceVideos.length, 1)

  // Compute scatter points: each source video gets an integer y-band (1-based).
  // Events sharing the same band + same 0.5-second bucket stack vertically.
  const scatterData = useMemo(() => {
    const videoToIdx = {}
    sourceVideos.forEach((name, i) => { videoToIdx[name] = i + 1 })
    const bucketCounts = {}
    return events.map((ev, i) => {
      const ts = Number(ev.timestamp ?? ev.time ?? 0)
      const vidIdx = videoToIdx[ev.source_video] ?? 1
      const bucket = `${vidIdx}_${Math.round(ts * 2)}`
      const stackPos = (bucketCounts[bucket] = (bucketCounts[bucket] ?? -1) + 1)
      return {
        x: ts,
        y: vidIdx + stackPos * 0.22,
        kind: deriveKind(ev),
        label: ev.label ?? ev.description ?? ev.summary ?? '',
        videoName: ev.source_video ?? '',
        originalIndex: i,
      }
    })
  }, [events, sourceVideos])

  const yTicks = useMemo(() => Array.from({ length: numBands }, (_, i) => i + 1), [numBands])
  const chartHeight = Math.max(140, numBands * 70)

  async function loadClip(idx) {
    if (!client || !outputDir) return
    setLoading(true)
    setLoadingIdx(idx)
    try {
      const r = await client.predict('/load_event_clip', { clip_index: idx, output_dir: outputDir })
      const src = resolveVideoSrc(r.data[0])
      if (src) setClipSrc?.(src)
    } catch {} finally { setLoading(false); setLoadingIdx(null) }
  }

  const CustomTooltip = ({ payload }) => {
    if (!payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={{ background: '#1f2833', border: '1px solid #2e4060', borderRadius: 8, padding: '8px 12px', fontSize: '0.75rem', color: '#e5e1d8', maxWidth: 220 }}>
        <div style={{ fontWeight: 600, marginBottom: 2, color: kindColor(d.kind) }}>{d.kind}</div>
        <div style={{ color: '#7a8ea8' }}>t = {Number(d.x).toFixed(1)}s</div>
        {d.videoName && multiSource && <div style={{ color: '#7a8ea8', marginTop: 2 }}>{clipLabel(d.videoName)}</div>}
        {d.label && <div style={{ color: '#7a8ea8', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>{d.label}</div>}
      </div>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Band timeline chart */}
      {scatterData.length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>{t(language, 'timeline.title')}</Typography>
          <ResponsiveContainer width="100%" height={chartHeight}>
            <ScatterChart margin={{ top: 10, right: 16, bottom: 16, left: 80 }}>
              <CartesianGrid stroke="#2e4060" strokeDasharray="3 3" horizontal={false} />

              {/* Alternating band fills */}
              {yTicks.map((band, i) => (
                <ReferenceLine key={band} y={band}
                  stroke={i % 2 === 0 ? 'rgba(30,55,90,0.35)' : 'transparent'}
                  strokeWidth={42}
                  ifOverflow="extendDomain"
                />
              ))}

              <XAxis
                dataKey="x" name="Time (s)" type="number" domain={['auto', 'auto']}
                tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false}
                label={{ value: t(language, 'timeline.x_label'), position: 'insideBottomRight', offset: -4, fill: '#7a8ea8', fontSize: 10 }}
              />
              <YAxis
                dataKey="y" type="number"
                domain={[0.5, numBands + 0.5]}
                ticks={yTicks}
                tickFormatter={(val) => clipLabel(sourceVideos[val - 1] ?? `Clip ${val}`)}
                tick={{ fill: '#7a8ea8', fontSize: 10 }}
                width={75}
                tickLine={false} axisLine={false}
              />
              <Tooltip cursor={{ stroke: '#2e4060' }} content={<CustomTooltip />} />
              <Scatter
                data={scatterData}
                shape={<ScatterDot />}
                onClick={(d) => onSeekVideo?.(d.x)}
                cursor="pointer"
              />
            </ScatterChart>
          </ResponsiveContainer>
        </Box>
      )}

      {/* Events table */}
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1.5 }}>
          <Typography variant="overline">{t(language, 'timeline.detected')}</Typography>
          <Typography variant="caption" color="text.secondary">{t(language, 'timeline.count', { count: events.length })}</Typography>
        </Box>
        {events.length === 0 ? (
          <Typography variant="caption" color="text.secondary">{t(language, 'timeline.empty')}</Typography>
        ) : (
          <TableContainer sx={{ borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>{t(language, 'timeline.col_num')}</TableCell>
                  <TableCell>{t(language, 'timeline.col_time')}</TableCell>
                  <TableCell>{t(language, 'timeline.col_kind')}</TableCell>
                  <TableCell>{t(language, 'timeline.col_zone')}</TableCell>
                  <TableCell>{t(language, 'timeline.col_desc')}</TableCell>
                  {multiSource && <TableCell>Video</TableCell>}
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {events.map((ev, i) => {
                  const kind = deriveKind(ev)
                  const color = kindColor(kind)
                  const srcName = ev.source_video ? ev.source_video.replace(/\.[^.]+$/, '') : null
                  return (
                    <TableRow key={i} hover sx={{ cursor: 'pointer' }}
                      onClick={() => onSeekVideo?.(Number(ev.timestamp ?? ev.time ?? 0))}>
                      <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>{i + 1}</TableCell>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{Number(ev.timestamp ?? ev.time ?? 0).toFixed(1)}s</TableCell>
                      <TableCell>
                        <Chip label={kind} size="small"
                          sx={{ background: color + '22', color, border: `1px solid ${color}44`, fontSize: '0.65rem' }} />
                      </TableCell>
                      <TableCell sx={{ color: 'text.secondary' }}>{ev.zone ?? '—'}</TableCell>
                      <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ev.label ?? ev.description ?? '—'}
                      </TableCell>
                      {multiSource && (
                        <TableCell>
                          {srcName && (
                            <Chip label={clipLabel(srcName)} size="small"
                              sx={{ fontSize: '0.6rem', height: 18, bgcolor: 'rgba(247,208,70,0.1)', color: 'text.secondary', border: '1px solid', borderColor: 'divider', maxWidth: 90 }} />
                          )}
                        </TableCell>
                      )}
                      <TableCell>
                        <MuiTooltip title={t(language, 'timeline.load_clip')}>
                          <span>
                            <IconButton size="small" disabled={loadingClip}
                              onClick={e => { e.stopPropagation(); loadClip(i) }}
                              sx={{ fontSize: '0.65rem', gap: 0.5, borderRadius: 1, px: 0.75, py: 0.25 }}>
                              {loadingIdx === i
                                ? <Loader2 size={10} style={{ animation: 'spin 1s linear infinite' }} />
                                : <RefreshCw size={10} />}
                              <span style={{ fontSize: '0.65rem' }}>{t(language, 'timeline.clip_btn')}</span>
                            </IconButton>
                          </span>
                        </MuiTooltip>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Box>
    </Box>
  )
}

function resolveVideoSrc(value) {
  if (!value) return ''
  if (typeof value === 'string') {
    if (value.startsWith('/gradio_api/file=')) return value
    if (value.startsWith('http')) {
      try { return new URL(value).pathname } catch {}
    }
    return `/gradio_api/file=${value}`
  }
  if (value.video) return resolveVideoSrc(value.video)
  if (Array.isArray(value) && value.length > 0) return resolveVideoSrc(value[0])
  if (value.path) return `/gradio_api/file=${value.path}`
  if (value.url) {
    try { return new URL(value.url).pathname } catch {}
    return value.url
  }
  return ''
}
