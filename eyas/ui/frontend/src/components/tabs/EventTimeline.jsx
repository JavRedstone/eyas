import { useState, useMemo, useRef, useEffect } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts'
import { RefreshCw, Loader2, Film, Video, Play, ChevronRight, ChevronDown } from 'lucide-react'
import Box from '@mui/material/Box'
import Collapse from '@mui/material/Collapse'
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
import { displayKind, displayZone, displayDescription } from '../../display.js'
import { gradioFileUrl, resolveGradioFile } from '../../backend.js'

const KIND_COLORS = {
  person:      '#e87030',
  vehicle:     '#60A5FA',
  animal:      '#34D399',
  intrusion:   '#EF4444',
  loitering:   '#FBBF24',
  pickup:      '#FF2222',
  handling:    '#FBBF24',
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
  if (ev.held_objects?.length) return 'handling'
  return 'observation'
}

function clipLabel(name = '') {
  const stem = name.replace(/\.[^.]+$/, '')
  const parts = stem.split('_')
  if (parts.length >= 3 && /^\d{8}$/.test(parts[0]) && /^\d{6}$/.test(parts[1]))
    return parts.slice(2).join('_')
  return stem.length > 14 ? stem.slice(-14) : stem || 'clip'
}

function fmtTime(ts) {
  const mins = Math.floor(ts / 60)
  const secs = (ts % 60).toFixed(1)
  return `${mins}:${String(secs).padStart(4, '0')}`
}

function ScatterDot({ cx, cy, payload }) {
  if (cx == null || cy == null) return null
  return <circle cx={cx} cy={cy} r={5} fill={kindColor(payload.kind)} fillOpacity={0.85} stroke="none" />
}

function EventDetail({ ev, language, zoneKoCache, multiSource }) {
  const ts = Number(ev.timestamp ?? ev.time ?? 0)
  const zone = displayZone(ev.zone, language, zoneKoCache, ev)
  const desc = displayDescription(ev, language)
  const items = ev.picked_up_items ?? ev.held_objects ?? []
  const conf = ev.confidence != null ? `${Math.round(Number(ev.confidence) * 100)}%` : null
  const srcName = ev.source_video ? ev.source_video.replace(/\.[^.]+$/, '') : null

  return (
    <Box sx={{
      px: 2, py: 1.5,
      bgcolor: 'rgba(0,0,0,0.18)',
      borderBottom: '1px solid',
      borderColor: 'divider',
      display: 'flex', flexDirection: 'column', gap: 1,
    }}>
      {/* Metadata row */}
      <Box sx={{ display: 'flex', gap: 3, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
            {t(language, 'event.timestamp')}
          </Typography>
          <Typography sx={{ fontSize: '0.78rem', fontFamily: 'monospace' }}>
            {fmtTime(ts)} <span style={{ opacity: 0.5, fontSize: '0.7rem' }}>({ts.toFixed(1)}s)</span>
          </Typography>
        </Box>
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
            {t(language, 'timeline.col_zone')}
          </Typography>
          <Typography sx={{ fontSize: '0.78rem' }}>{zone}</Typography>
        </Box>
        {conf && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
              {t(language, 'event.confidence')}
            </Typography>
            <Typography sx={{ fontSize: '0.78rem' }}>{conf}</Typography>
          </Box>
        )}
        {multiSource && srcName && (
          <Box>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
              {t(language, 'event.source')}
            </Typography>
            <Typography sx={{ fontSize: '0.72rem', fontFamily: 'monospace', color: 'text.secondary' }}>{srcName}</Typography>
          </Box>
        )}
      </Box>

      {/* Activity (VLM reason) */}
      {ev.activity && (
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
            {t(language, 'event.activity')}
          </Typography>
          <Typography sx={{ fontSize: '0.78rem', lineHeight: 1.6, color: 'text.primary', fontStyle: 'italic' }}>{(language === '한국어' && ev.activity_ko) || ev.activity}</Typography>
        </Box>
      )}

      {/* Full description */}
      <Box>
        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
          {t(language, 'timeline.col_desc')}
        </Typography>
        <Typography sx={{ fontSize: '0.78rem', lineHeight: 1.6, color: 'text.primary' }}>{desc}</Typography>
      </Box>

      {/* Items */}
      {items.length > 0 && (
        <Box>
          <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.58rem', letterSpacing: '0.05em', textTransform: 'uppercase', display: 'block', mb: 0.3 }}>
            {t(language, 'event.items')}
          </Typography>
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
            {items.map((item, idx) => {
              const name = typeof item === 'string' ? item : (item.name ?? String(item))
              const count = typeof item === 'object' && item.count ? ` ×${item.count}` : ''
              return (
                <Chip key={idx} label={`${name}${count}`} size="small"
                  sx={{ fontSize: '0.62rem', height: 18, bgcolor: 'rgba(255,34,34,0.12)', color: '#FF8888', border: '1px solid rgba(255,34,34,0.25)' }} />
              )
            })}
          </Box>
        </Box>
      )}
    </Box>
  )
}

export default function EventTimeline({
  client, events, outputDir, onSeekVideo,
  annotatedVideo, annotatedVideoRef,
  language = 'English',
  zoneKoCache = {},
  viewClipId = null,
  onSwitchToClip,
  onHighlightGridClip = null,
  doneClips = [],
  latestEventKey = null,
  previewFrame = null,
}) {
  const [loadingClip, setLoading] = useState(false)
  const [loadingIdx, setLoadingIdx] = useState(null)
  const [localClipSrc, setLocalClipSrc] = useState(null)
  const [showingClip, setShowingClip] = useState(false)
  const [expandedKey, setExpandedKey] = useState(null)

  // Auto-expand and scroll to the latest event row when events stream in during processing
  const latestRowRef = useRef(null)
  useEffect(() => {
    if (!latestEventKey) return
    setExpandedKey(latestEventKey)
    // Give the DOM a tick to render the expanded row, then scroll it into view
    setTimeout(() => { latestRowRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, 50)
  }, [latestEventKey])
  const [tableSplitPct, setTableSplitPct] = useState(50)
  const [highlightedAnnotatedClipId, setHighlightedAnnotatedClipId] = useState(null)
  const splitRowRef = useRef(null)
  const pendingSeekRef = useRef(null)
  const annotatedGridRefs = useRef([])
  const annotatedSyncLockRef = useRef(false)
  const annotatedSyncLockTimerRef = useRef(null)

  const sourceVideos = useMemo(() => {
    const names = new Set(events.map(e => e.source_video).filter(Boolean))
    return [...names]
  }, [events])
  const multiSource = sourceVideos.length > 1
  const numBands = Math.max(sourceVideos.length, 1)

  // Map source_video name → source_clip_id for the video panel switcher
  const videoToClipId = useMemo(() => {
    const map = {}
    events.forEach(ev => {
      if (ev.source_clip_id && ev.source_video) map[ev.source_video] = ev.source_clip_id
    })
    return map
  }, [events])

  const tableEvents = useMemo(() => {
    if (!multiSource) return events
    return [...events].sort(
      (a, b) => Number(a.timestamp ?? a.time ?? 0) - Number(b.timestamp ?? b.time ?? 0)
    )
  }, [events, multiSource])

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
        kindLabel: displayKind(deriveKind(ev), language),
        label: displayDescription(ev, language),
        videoName: ev.source_video ?? '',
      }
    })
  }, [events, sourceVideos, language])

  const yTicks = useMemo(() => Array.from({ length: numBands }, (_, i) => i + 1), [numBands])
  const chartHeight = Math.max(90, numBands * 56)

  async function loadClip(idx, dir, displayIdx = idx) {
    const clipDir = dir || outputDir
    if (!client || !clipDir) return
    setLoading(true)
    setLoadingIdx(displayIdx)
    try {
      const r = await client.predict('/load_event_clip', { clip_index: idx, output_dir: clipDir })
      const src = resolveGradioFile(r.data[0])
      if (src) {
        setLocalClipSrc(src)
        setShowingClip(true)
      }
    } catch {} finally { setLoading(false); setLoadingIdx(null) }
  }

  function handleViewOnVideo(e, ev, ts) {
    e.stopPropagation()
    setShowingClip(false)
    const clipId = ev.source_clip_id
    // In All-view with a grid, highlight the clip's tile and seek all grid videos
    // without switching away from All view.
    if (!viewClipId && onHighlightGridClip) {
      onHighlightGridClip(clipId, ts)  // seek + highlight top raw-feed grid
      // Also seek + highlight the annotated grid in this panel
      if (doneClips.length >= 2) {
        setHighlightedAnnotatedClipId(clipId)
        annotatedGridRefs.current.forEach(el => {
          if (!el) return
          el.currentTime = ts
          if (el.paused) el.play().catch(() => {})
        })
      } else {
        onSeekVideo?.(ts)
      }
      return
    }
    const needsSwitch = onSwitchToClip && clipId && clipId !== viewClipId
    if (needsSwitch) {
      pendingSeekRef.current = ts
      onSwitchToClip(clipId)
    } else {
      onSeekVideo?.(ts)
    }
  }

  function toggleExpand(key) {
    setExpandedKey(prev => prev === key ? null : key)
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

  // Show a grid of annotated videos when in All view with 2+ done clips.
  const showAnnotatedGrid = !viewClipId && !showingClip && doneClips.length >= 2

  function lockAnnotatedSync(ms = 250) {
    annotatedSyncLockRef.current = true
    clearTimeout(annotatedSyncLockTimerRef.current)
    annotatedSyncLockTimerRef.current = setTimeout(() => { annotatedSyncLockRef.current = false }, ms)
  }

  function handleAnnotatedGridSeeked(e, idx) {
    if (annotatedSyncLockRef.current) return
    const time = e.target.currentTime
    lockAnnotatedSync()
    annotatedGridRefs.current.forEach((el, i) => {
      if (i !== idx && el) el.currentTime = time
    })
  }

  function handleAnnotatedGridPlay(e, idx) {
    if (annotatedSyncLockRef.current) return
    const time = e.target.currentTime
    lockAnnotatedSync(100)
    annotatedGridRefs.current.forEach((el, i) => {
      if (i !== idx && el) {
        el.currentTime = time
        el.play().catch(() => {})
      }
    })
  }

  function handleAnnotatedGridPause(e, idx) {
    if (annotatedSyncLockRef.current) return
    lockAnnotatedSync(100)
    annotatedGridRefs.current.forEach((el, i) => {
      if (i !== idx && el && !el.paused) el.pause()
    })
  }

  const CustomTooltip = ({ payload }) => {
    if (!payload?.length) return null
    const d = payload[0].payload
    return (
      <div style={{ background: '#1f2833', border: '1px solid #2e4060', borderRadius: 8, padding: '8px 12px', fontSize: '0.75rem', color: '#e5e1d8', maxWidth: 220 }}>
        <div style={{ fontWeight: 600, marginBottom: 2, color: kindColor(d.kind) }}>{d.kindLabel ?? d.kind}</div>
        <div style={{ color: '#7a8ea8' }}>t = {Number(d.x).toFixed(1)}s</div>
        {d.videoName && multiSource && <div style={{ color: '#7a8ea8', marginTop: 2 }}>{clipLabel(d.videoName)}</div>}
        {d.label && <div style={{ color: '#7a8ea8', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: 200 }}>{d.label}</div>}
      </div>
    )
  }

  const annotatedVideoSrc = annotatedVideo
    ? gradioFileUrl(annotatedVideo)
    : null

  const handleChartClick = (state) => {
    const payload = state?.activePayload?.[0]?.payload
    if (payload?.x == null) return
    onSeekVideo?.(payload.x)
    annotatedGridRefs.current.forEach(el => {
      if (!el) return
      el.currentTime = payload.x
    })
  }

  const activeSrc = showingClip && localClipSrc ? localClipSrc : annotatedVideoSrc

  // Number of table columns (used for expansion row colSpan)
  const numCols = multiSource ? 7 : 6

  return (
    <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, overflow: 'hidden' }}>

      {/* ── Scatter timeline ─── */}
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
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75, width: 32 }} />
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_time')}</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_kind')}</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_zone')}</TableCell>
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>{t(language, 'timeline.col_desc')}</TableCell>
                    {multiSource && <TableCell sx={{ bgcolor: 'background.paper', py: 0.75 }}>Clip</TableCell>}
                    <TableCell sx={{ bgcolor: 'background.paper', py: 0.75, width: 56 }} />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {tableEvents.flatMap((ev, i) => {
                    const kind = deriveKind(ev)
                    const color = kindColor(kind)
                    const ts = Number(ev.timestamp ?? ev.time ?? 0)
                    const srcName = ev.source_video ? ev.source_video.replace(/\.[^.]+$/, '') : null
                    const rowKey = `${ev.source_clip_id ?? ''}-${ev.source_event_index ?? i}`
                    const isExpanded = expandedKey === rowKey

                    return [
                      <TableRow key={rowKey} hover
                        ref={rowKey === latestEventKey ? latestRowRef : null}
                        sx={{ cursor: 'pointer', bgcolor: isExpanded ? 'rgba(247,208,70,0.04)' : undefined }}
                        onClick={() => toggleExpand(rowKey)}>
                        {/* Expand chevron + index */}
                        <TableCell sx={{ py: 0.5, pr: 0.5, color: 'text.secondary' }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                            {isExpanded
                              ? <ChevronDown size={10} style={{ flexShrink: 0, color: '#f7d046' }} />
                              : <ChevronRight size={10} style={{ flexShrink: 0 }} />}
                            <span style={{ fontFamily: 'monospace', fontSize: '0.7rem' }}>{i + 1}</span>
                          </Box>
                        </TableCell>
                        <TableCell sx={{ fontFamily: 'monospace', py: 0.5 }}>{ts.toFixed(1)}s</TableCell>
                        <TableCell sx={{ py: 0.5 }}>
                          <Chip label={displayKind(kind, language)} size="small"
                            sx={{ background: color + '22', color, border: `1px solid ${color}44`, fontSize: '0.62rem', height: 18 }} />
                        </TableCell>
                        <TableCell sx={{ color: 'text.secondary', py: 0.5, fontSize: '0.72rem' }}>
                          {displayZone(ev.zone, language, zoneKoCache, ev)}
                        </TableCell>
                        <TableCell sx={{ maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', py: 0.5, fontSize: '0.72rem' }}>
                          {displayDescription(ev, language)}
                        </TableCell>
                        {multiSource && (
                          <TableCell sx={{ py: 0.5 }}>
                            {srcName && (
                              <Chip label={clipLabel(srcName)} size="small"
                                sx={{ fontSize: '0.58rem', height: 16, bgcolor: 'rgba(247,208,70,0.08)', color: 'text.secondary', border: '1px solid', borderColor: 'divider', maxWidth: 80 }} />
                            )}
                          </TableCell>
                        )}
                        {/* Action buttons */}
                        <TableCell sx={{ py: 0.5 }}>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.25 }}>
                            <MuiTooltip title="View on video">
                              <IconButton size="small"
                                onClick={e => handleViewOnVideo(e, ev, ts)}
                                sx={{ borderRadius: 1, px: 0.5, py: 0.25 }}>
                                <Play size={9} />
                              </IconButton>
                            </MuiTooltip>
                            <MuiTooltip title={t(language, 'timeline.load_clip')}>
                              <span>
                                <IconButton size="small" disabled={loadingClip}
                                  onClick={e => { e.stopPropagation(); loadClip(ev.source_event_index ?? i, ev.source_output_dir ?? outputDir, i) }}
                                  sx={{ borderRadius: 1, px: 0.5, py: 0.25 }}>
                                  {loadingIdx === i
                                    ? <Loader2 size={9} style={{ animation: 'spin 1s linear infinite' }} />
                                    : <RefreshCw size={9} />}
                                </IconButton>
                              </span>
                            </MuiTooltip>
                          </Box>
                        </TableCell>
                      </TableRow>,

                      // Expansion row
                      <TableRow key={`${rowKey}-expand`} sx={{ '& > td': { border: 0 } }}>
                        <TableCell colSpan={numCols} sx={{ py: 0 }}>
                          <Collapse in={isExpanded} timeout="auto" unmountOnExit>
                            <EventDetail ev={ev} language={language} zoneKoCache={zoneKoCache} multiSource={multiSource} />
                          </Collapse>
                        </TableCell>
                      </TableRow>,
                    ]
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

        {/* Right: video panel */}
        <Box style={{ flex: 100 - tableSplitPct }}
          sx={{ display: 'flex', flexDirection: 'column', minHeight: 0, minWidth: 0, overflow: 'hidden' }}>

          {/* Video panel header */}
          <Box sx={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 0.75, px: 1.5, py: 0.75, borderBottom: '1px solid', borderColor: 'divider', flexWrap: 'wrap', minHeight: 36 }}>
            {/* Annotated / Clip toggle */}
            <MuiTooltip title={t(language, 'panel.annotated')}>
              <IconButton size="small"
                onClick={() => setShowingClip(false)}
                sx={{ borderRadius: 1, p: 0.5, bgcolor: !showingClip ? 'rgba(247,208,70,0.12)' : 'transparent', color: !showingClip ? 'primary.main' : 'text.secondary' }}>
                <Video size={13} />
              </IconButton>
            </MuiTooltip>
            <MuiTooltip title={t(language, 'panel.event_clip')}>
              <span>
                <IconButton size="small"
                  onClick={() => setShowingClip(true)}
                  disabled={!localClipSrc}
                  sx={{ borderRadius: 1, p: 0.5, bgcolor: showingClip ? 'rgba(247,208,70,0.12)' : 'transparent', color: showingClip ? 'primary.main' : 'text.secondary', '&.Mui-disabled': { opacity: 0.3 } }}>
                  <Film size={13} />
                </IconButton>
              </span>
            </MuiTooltip>

            {/* Divider + multi-source switcher — hidden in annotated grid mode */}
            {!showAnnotatedGrid && multiSource && !showingClip && onSwitchToClip && (
              <>
                <Box sx={{ width: 1, height: 14, bgcolor: 'divider', mx: 0.25, flexShrink: 0 }} />
                {sourceVideos.map(name => {
                  const cid = videoToClipId[name]
                  const isActive = cid === viewClipId || (!viewClipId && name === sourceVideos[sourceVideos.length - 1])
                  return (
                    <Box key={name} component="button"
                      onClick={() => onSwitchToClip(cid)}
                      sx={{
                        px: 0.75, py: 0.25,
                        border: '1px solid',
                        borderColor: isActive ? 'primary.main' : 'divider',
                        borderRadius: 1,
                        fontSize: '0.6rem', fontFamily: 'monospace',
                        bgcolor: isActive ? 'rgba(247,208,70,0.1)' : 'transparent',
                        color: isActive ? 'primary.main' : 'text.secondary',
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                        lineHeight: 1.4,
                        '&:hover': { borderColor: 'primary.main', color: 'text.primary', bgcolor: 'rgba(247,208,70,0.05)' },
                      }}>
                      {clipLabel(name)}
                    </Box>
                  )
                })}
              </>
            )}

            {/* Label for single-source or clip mode */}
            {(showingClip || (!multiSource && !showAnnotatedGrid)) && (
              <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.62rem', ml: 0.25 }}>
                {showingClip && localClipSrc ? t(language, 'panel.event_clip') : annotatedVideoSrc ? t(language, 'panel.annotated') : t(language, 'timeline.no_video')}
              </Typography>
            )}
          </Box>

          {showAnnotatedGrid ? (
            /* ── Annotated video grid (All view, 2+ done clips) ── */
            <Box sx={{
              flex: 1, minHeight: 0, bgcolor: '#000', p: 0.5,
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gridAutoRows: '1fr',
              gap: 0.5,
              overflow: 'hidden',
            }}>
              {doneClips.map((item, idx) => {
                const av = item.results?.annotatedVideo
                const src = av ? gradioFileUrl(av) : null
                const label = item.zone || item.name.replace(/\.[^.]+$/, '')
                const isHighlighted = highlightedAnnotatedClipId === item.id
                return (
                  <Box key={item.id} sx={{
                    position: 'relative', borderRadius: 1, overflow: 'hidden',
                    outline: '2px solid',
                    outlineColor: isHighlighted ? 'primary.main' : 'transparent',
                    transition: 'outline-color 0.2s',
                  }}>
                    <Typography variant="caption" sx={{
                      position: 'absolute', top: 4, left: 5, zIndex: 1,
                      color: '#fff', bgcolor: 'rgba(0,0,0,0.6)',
                      px: 0.75, py: 0.15, borderRadius: 0.5,
                      fontFamily: 'monospace', fontSize: '0.55rem',
                      lineHeight: 1.5, pointerEvents: 'none',
                    }}>
                      {label}
                    </Typography>
                    {src ? (
                      <video
                        ref={el => { annotatedGridRefs.current[idx] = el }}
                        src={src}
                        preload="metadata"
                        controls
                        style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                        onSeeked={e => handleAnnotatedGridSeeked(e, idx)}
                        onPlay={e => handleAnnotatedGridPlay(e, idx)}
                        onPause={e => handleAnnotatedGridPause(e, idx)}
                        onLoadedMetadata={(e) => {
                          if (pendingSeekRef.current !== null) {
                            e.currentTarget.currentTime = pendingSeekRef.current
                            e.currentTarget.play().catch(() => {})
                          }
                        }}
                      />
                    ) : (
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', bgcolor: 'background.default' }}>
                        <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.6rem' }}>No annotated video</Typography>
                      </Box>
                    )}
                  </Box>
                )
              })}
            </Box>
          ) : (
            /* ── Single annotated video ── */
            <Box sx={{ flex: 1, bgcolor: (activeSrc || previewFrame) ? '#000' : 'background.default', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden', minHeight: 0 }}>
              {activeSrc ? (
                <video
                  ref={showingClip ? undefined : annotatedVideoRef}
                  key={activeSrc}
                  src={activeSrc}
                  preload="metadata"
                  controls
                  onLoadedMetadata={(e) => {
                    if (pendingSeekRef.current !== null && !showingClip) {
                      e.currentTarget.currentTime = pendingSeekRef.current
                      pendingSeekRef.current = null
                      e.currentTarget.play().catch(() => {})
                    }
                  }}
                  style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
                />
              ) : previewFrame ? (
                <img src={previewFrame} alt="Processing preview"
                  style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }} />
              ) : (
                <Box sx={{ textAlign: 'center', p: 3 }}>
                  <Typography sx={{ fontSize: '1.5rem', opacity: 0.2, mb: 0.5 }}>▶</Typography>
                  <Typography variant="caption" color="text.secondary">{t(language, 'app.no_annotated')}</Typography>
                </Box>
              )}
            </Box>
          )}
        </Box>
      </Box>
    </Box>
  )
}
