import { useState } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
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
  const k = String(kind).toLowerCase()
  return KIND_COLORS[k] || KIND_COLORS.default
}

function deriveKind(ev) {
  if (ev.kind) return ev.kind
  if (ev.event_type) return ev.event_type
  if (ev.pickup_confirmed) return 'pickup'
  if (ev.held_objects?.length) return 'suspicious'
  return 'observation'
}

function ScatterDot({ cx, cy, payload }) {
  if (cx == null || cy == null) return null
  return <circle cx={cx} cy={cy} r={5} fill={kindColor(payload.kind)} fillOpacity={0.85} />
}

export default function EventTimeline({ client, events, outputDir, onSeekVideo, setClipSrc }) {
  const [loadingClip, setLoading] = useState(false)
  const [loadingIdx, setLoadingIdx] = useState(null)

  const scatterData = events.map((ev, i) => ({
    x: Number(ev.timestamp ?? ev.time ?? 0),
    y: i + 1,
    kind: deriveKind(ev),
    label: ev.label ?? ev.description ?? ev.summary ?? '',
  }))

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

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      {/* Scatter timeline */}
      {scatterData.length > 0 && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1.5 }}>Event Timeline</Typography>
          <ResponsiveContainer width="100%" height={160}>
            <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid stroke="#2e4060" strokeDasharray="3 3" />
              <XAxis dataKey="x" name="Time (s)" type="number" domain={['auto', 'auto']}
                tick={{ fill: '#7a8ea8', fontSize: 10 }} tickLine={false} axisLine={false}
                label={{ value: 'seconds', position: 'insideBottomRight', offset: -4, fill: '#7a8ea8', fontSize: 10 }} />
              <YAxis dataKey="y" type="number" hide domain={[0, scatterData.length + 1]} />
              <Tooltip
                cursor={{ stroke: '#2e4060' }}
                content={({ payload }) => {
                  if (!payload?.length) return null
                  const d = payload[0].payload
                  return (
                    <div style={{ background: '#1f2833', border: '1px solid #2e4060', borderRadius: 8, padding: '8px 12px', fontSize: '0.75rem', color: '#e5e1d8', maxWidth: 200 }}>
                      <div style={{ fontWeight: 600, marginBottom: 2, color: kindColor(d.kind) }}>{d.kind}</div>
                      <div style={{ color: '#7a8ea8' }}>t = {Number(d.x).toFixed(1)}s</div>
                      {d.label && <div style={{ color: '#7a8ea8', marginTop: 4, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{d.label}</div>}
                    </div>
                  )
                }} />
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
          <Typography variant="overline">Detected Events</Typography>
          <Typography variant="caption" color="text.secondary">{events.length} events</Typography>
        </Box>
        {events.length === 0 ? (
          <Typography variant="caption" color="text.secondary">No events yet. Run the pipeline first.</Typography>
        ) : (
          <TableContainer sx={{ borderRadius: 1, border: '1px solid', borderColor: 'divider' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>#</TableCell>
                  <TableCell>Time</TableCell>
                  <TableCell>Kind</TableCell>
                  <TableCell>Zone</TableCell>
                  <TableCell>Description</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {events.map((ev, i) => {
                  const kind = deriveKind(ev)
                  const color = kindColor(kind)
                  return (
                    <TableRow key={i}
                      hover
                      sx={{ cursor: 'pointer' }}
                      onClick={() => onSeekVideo?.(Number(ev.timestamp ?? ev.time ?? 0))}>
                      <TableCell sx={{ fontFamily: 'monospace', color: 'text.secondary' }}>{i + 1}</TableCell>
                      <TableCell sx={{ fontFamily: 'monospace' }}>{Number(ev.timestamp ?? ev.time ?? 0).toFixed(1)}s</TableCell>
                      <TableCell>
                        <Chip
                          label={kind}
                          size="small"
                          sx={{ background: color + '22', color, border: `1px solid ${color}44`, fontSize: '0.65rem' }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: 'text.secondary' }}>{ev.zone ?? '—'}</TableCell>
                      <TableCell sx={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {ev.label ?? ev.description ?? '—'}
                      </TableCell>
                      <TableCell>
                        <MuiTooltip title="Load clip">
                          <span>
                            <IconButton
                              size="small"
                              disabled={loadingClip}
                              onClick={e => { e.stopPropagation(); loadClip(i) }}
                              sx={{ fontSize: '0.65rem', gap: 0.5, borderRadius: 1, px: 0.75, py: 0.25 }}>
                              {loadingIdx === i
                                ? <Loader2 size={10} style={{ animation: 'spin 1s linear infinite' }} />
                                : <RefreshCw size={10} />}
                              <span style={{ fontSize: '0.65rem' }}>clip</span>
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
