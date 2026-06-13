import { useState, useMemo, useRef } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { RefreshCw, Loader2, Film, Video } from 'lucide-react'
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

export default function EventTimeline({
  client, events, outputDir, onSeekVideo,
  annotatedVideo, annotatedVideoRef,
  language = 'English',
}) {
  const [loadingClip, setLoading] = useState(false)
  const [loadingIdx, setLoadingIdx] = useState(null)
  const [localClipSrc, setLocalClipSrc] = useState(null)
  const [showingClip, setShowingClip] = useState(false)
  // col-resize between events table (left) and video panel (right)
  const [tableSplitPct, setTableSplitPct] = useState(50)
  const splitRowRef = useRef(null)

  const sourceVideos = useMemo(() => {
    const names = new Set(events.map(e => e.source_video).filter(Boolean))
    return [...names]
  }, [events])
  const multiSource = sourceVideos.length > 1
  const numBands = Math.max(sourceVideos.length, 1)

  const scatterData = useMemo(() => {
    const videoToIdx = {}
    sourceVideos.forEach((name, i) => { videoToIdx[name] = i + 1 })
    const bucketCounts = {}
    return events.map((ev) => {
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
      }
    })
  }, [events, sourceVideos])

  const yTicks = useMemo(() => Array.from({ length: numBands }, (_, i) => i + 1), [numBands])
  const chartHeight = Math.max(90, numBands * 56)

  async function loadClip(idx) {
    if (!client || !outputDir) return
    setLoading(true)
    setLoadingIdx(idx)
    try {
      const r = await client.predict('/load_event_clip', { clip_index: idx, output_dir: outputDir })
      const src = resolveVideoSrc(r.data[0])
      if (src) {
        setLocalClipSrc(src)
        setShowingClip(true)
      }
    } catch {} finally { setLoading(false); setLoadingIdx(null) }
  }

  const onSplitDrag = (e) => {
    e.preventDefault()
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'
    const onMove = (ev) => {
      if (!splitRowRef.current) return
      const rect = splitRowRef.current.getBoundingClientRect()
      const pct = ((ev.clientX - rect.left) / rect.width) * 100
      setTableSplitPct(Math.max(25, Math.min(75, pct)))
    }
    const onUp = () => {
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
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

  const annotatedVideoSrc = annotatedVideo
    ? (annotatedVideo.startsWith('/gradio_api/file=') ? annotatedVideo : `/gradio_api/file=${annotatedVideo}`)
    : null

  // Seek via ScatterChart's onClick — this reliably provides the hovered/clicked point
  const handleChartClick = (state) => {
    const payload = state?.activePayload?.[0]?.payload
    if (payload?.x != null) onSeekVideo?.(payload.x)
  }

  const activeSrc = showingClip && localClipSrc ? localClipSrc : annotatedVideoSrc

  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>

      {/* ── Scatter timeline — full width ─── */}
      <Box sx={{ flexShrink: 0, px: 2, pt: 1.25, pb: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="overline" sx={{ display: 'block', mb: 0.5, fontSize: '0.6rem' }}>
          {t(language, 'timeline.title')}
        </Typography>
        {scatterData.length > 0 ? (
          <ResponsiveContainer width="100%" height={chartHeight}>
            <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 80 }} onClick={handleChartClick} style={{ cursor: 'crosshair' }}>
              <CartesianGrid stroke="#2e4060" strokeDasharray="3 3" horizontal={false} />
              {yTicks.map((band, i) => (
                <ReferenceLine key={band} y={band}
                  stroke={i % 2 === 0 ? 'rgba(30,55,90,0.35)' : 'transparent'}
                  strokeWidth={36} ifOverflow="extendDomain" />
              ))}
              <XAxis
                dataKey="x" name="Time (s)" type="number" domain={['auto', 'auto']}
                tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false}
                label={{ value: t(language, 'timeline.x_label'), position: 'insideBottomRight', offset: -4, fill: '#7a8ea8', fontSize: 10 }}
              />
              <YAxis
                dataKey="y" type="number"
                domain={[0.5, numBands + 0.5]} ticks={yTicks}
                tickFormatter={(val) => clipLabel(sourceVideos[val - 1] ?? `Clip ${val}`)}
                tick={{ fill: '#7a8ea8', fontSize: 10 }}
                width={75} tickLine={false} axisLine={false}
              />
              <Tooltip cursor={{ stroke: '#f7d04640', strokeWidth: 1 }} content={<CustomTooltip />} />
              <Scatter data={scatterData} shape={<ScatterDot />} />
            </ScatterChart>
          </ResponsiveContainer>
        ) : (
          <Box sx={{ height: 48, display: 'flex', alignItems: 'center' }}>
            <Typography variant="caption" color="text.secondary">{t(language, 'timeline.empty')}</Typography>
          </Box>
        )}
      </Box>

      {/* ── Bottom split: events LEFT | video RIGHT ─── */}
      <Box ref={splitRowRef} sx={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>

        {/* Left: events table */}
        <Box style={{ flex: tableSplitPct }}
          sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, minWidth: 0, overflow: 'hidden' }}>

          {/* Table header row */}
          <Box sx={{ flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 2, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="overline" sx={{ fontSize: '0.6rem' }}>{t(language, 'timeline.detected')}</Typography>
            <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace', fontSize: '0.65rem' }}>
              {events.length}
            </Typography>
          </Box>

          {events.length === 0 ? (
            <Box sx={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Typography variant="caption" color="text.secondary">{t(language, 'timeline.empty')}</Typography>
            </Box>
          ) : (
            <TableContainer sx={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
              <Table size="small" stickyHeader>
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>#</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_time')}</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_kind')}</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_zone')}</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_desc')}</TableCell>
                    {multiSource && <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>Clip</TableCell>}
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }} />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {events.map((ev, i) => {
                    const kind = deriveKind(ev)
                    const color = kindColor(kind)
                    const ts = Number(ev.timestamp ?? ev.time ?? 0)
                    const srcName = ev.source_video ? ev.source_video.replace(/\.[^.]+$/, '') : null
                    return (
                      <TableRow key={i} hover sx={{ cursor: 'pointer' }}
                        onClick={() => { onSeekVideo?.(ts); setShowingClip(false) }}>
                        <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary', py: 0.5 }}>{i + 1}</TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', py: 0.5 }}>{ts.toFixed(1)}s</TableCell>
                        <TableCell sx={{ py: 0.5 }}>
                          <Chip label={kind} size="small"
                            sx={{ background: color + '22', color, border: `1px solid ${color}44`, fontSize: '0.62rem', height: 18 }} />
                        </TableCell>
                        <TableCell sx={{ color: 'text.secondary', py: 0.5, fontSize: '0.72rem' }}>{ev.zone ?? '—'}</TableCell>
                        <TableCell sx={{ maxWidth: 160, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', py: 0.5, fontSize: '0.72rem' }}>
                          {ev.label ?? ev.description ?? '—'}
                        </TableCell>
                        {multiSource && (
                          <TableCell sx={{ py: 0.5 }}>
                            {srcName && (
                              <Chip label={clipLabel(srcName)} size="small"
                                sx={{ fontSize: '0.58rem', height: 16, bgcolor: 'rgba(247,208,70,0.08)', color: 'text.secondary', border: '1px solid', borderColor: 'divider', maxWidth: 80 }} />
                            )}
                          </TableCell>
                        )}
                        <TableCell sx={{ py: 0.5 }}>
                          <MuiTooltip title={t(language, 'timeline.load_clip')}>
                            <span>
                              <IconButton size="small" disabled={loadingClip}
                                onClick={e => { e.stopPropagation(); loadClip(i) }}
                                sx={{ fontSize: '0.62rem', gap: 0.5, borderRadius: 1, px: 0.5, py: 0.25 }}>
                                {loadingIdx === i
                                  ? <Loader2 size={9} style={{ animation: 'spin 1s linear infinite' }} />
                                  : <RefreshCw size={9} />}
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

        {/* Col-resize handle */}
        <Box sx={{ width: 12, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'col-resize', bgcolor: 'background.default' }}
          onMouseDown={onSplitDrag}>
          <Box sx={{ width: 2, height: '40%', minHeight: 32, borderRadius: 9999, bgcolor: 'divider', '&:hover': { bgcolor: 'primary.dark' } }} />
        </Box>

        {/* Right: video panel (annotated or clip, switchable) */}
        <Box style={{ flex: 100 - tableSplitPct }}
          sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, minWidth: 0, overflow: 'hidden' }}>

          {/* Video panel header with toggle */}
          <Box sx={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 1, px: 1.5, py: 0.75, borderBottom: '1px solid', borderColor: 'divider' }}>
            <MuiTooltip title="Annotated video">
              <IconButton size="small"
                onClick={() => setShowingClip(false)}
                sx={{ borderRadius: 1, p: 0.5, bgcolor: !showingClip ? 'rgba(247,208,70,0.12)' : 'transparent', color: !showingClip ? 'primary.main' : 'text.secondary' }}>
                <Video size={13} />
              </IconButton>
            </MuiTooltip>
            <MuiTooltip title="Event clip">
              <span>
                <IconButton size="small"
                  onClick={() => setShowingClip(true)}
                  disabled={!localClipSrc}
                  sx={{ borderRadius: 1, p: 0.5, bgcolor: showingClip ? 'rgba(247,208,70,0.12)' : 'transparent', color: showingClip ? 'primary.main' : 'text.secondary', '&.Mui-disabled': { opacity: 0.3 } }}>
                  <Film size={13} />
                </IconButton>
              </span>
            </MuiTooltip>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.62rem', ml: 0.5 }}>
              {showingClip && localClipSrc ? 'Event clip' : annotatedVideoSrc ? 'Annotated video' : 'No video yet'}
            </Typography>
          </Box>

          <Box sx={{ flex: 1, bgcolor: activeSrc ? '#000' : 'background.default', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', minHeight: 0 }}>
            {activeSrc ? (
              <video
                ref={showingClip ? undefined : annotatedVideoRef}
                key={activeSrc}
                src={activeSrc}
                controls
                style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
              />
            ) : (
              <Box sx={{ textAlign: 'center', p: 3 }}>
                <Typography sx={{ fontSize: '1.5rem', opacity: 0.2, mb: 0.5 }}>▶</Typography>
                <Typography variant="caption" color="text.secondary">{t(language, 'app.no_annotated')}</Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Box>
    </Box>
  )
}
