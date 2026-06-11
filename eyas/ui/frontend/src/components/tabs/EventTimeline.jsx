import { useState } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { RefreshCw, Loader2 } from 'lucide-react'

const KIND_COLORS = {
  person:      '#E8682A',
  vehicle:     '#60A5FA',
  animal:      '#34D399',
  intrusion:   '#EF4444',
  loitering:   '#FBBF24',
  pickup:      '#FF2222',
  suspicious:  '#FBBF24',
  observation: '#8B93A9',
  default:     '#6B728E',
}

function kindColor(kind = '') {
  const k = String(kind).toLowerCase()
  return KIND_COLORS[k] || KIND_COLORS.default
}

// Derive a display kind from the raw event object
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
    <div className="space-y-5">
      {/* Scatter timeline */}
      {scatterData.length > 0 && (
        <div>
          <p className="section-label mb-3">Event Timeline</p>
          <ResponsiveContainer width="100%" height={160}>
            <ScatterChart margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <CartesianGrid stroke="#2A3050" strokeDasharray="3 3" />
              <XAxis dataKey="x" name="Time (s)" type="number" domain={['auto', 'auto']}
                tick={{ fill: '#6B728E', fontSize: 10 }} tickLine={false} axisLine={false}
                label={{ value: 'seconds', position: 'insideBottomRight', offset: -4, fill: '#6B728E', fontSize: 10 }} />
              <YAxis dataKey="y" type="number" hide domain={[0, scatterData.length + 1]} />
              <Tooltip
                cursor={{ stroke: '#2A3050' }}
                content={({ payload }) => {
                  if (!payload?.length) return null
                  const d = payload[0].payload
                  return (
                    <div className="bg-panel border border-border rounded-lg px-3 py-2 text-xs shadow-lg max-w-xs">
                      <div className="font-semibold mb-0.5" style={{ color: kindColor(d.kind) }}>{d.kind}</div>
                      <div className="text-muted">t = {Number(d.x).toFixed(1)}s</div>
                      {d.label && <div className="text-muted mt-1 truncate">{d.label}</div>}
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
        </div>
      )}

      {/* Events table */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <p className="section-label">Detected Events</p>
          <span className="text-xs text-muted">{events.length} events</span>
        </div>
        {events.length === 0 ? (
          <p className="text-xs text-muted">No events yet. Run the pipeline first.</p>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-border bg-surface/60">
                  <th className="text-left px-3 py-2 text-muted font-medium">#</th>
                  <th className="text-left px-3 py-2 text-muted font-medium">Time</th>
                  <th className="text-left px-3 py-2 text-muted font-medium">Kind</th>
                  <th className="text-left px-3 py-2 text-muted font-medium">Zone</th>
                  <th className="text-left px-3 py-2 text-muted font-medium">Description</th>
                  <th className="px-3 py-2" />
                </tr>
              </thead>
              <tbody>
                {events.map((ev, i) => {
                  const kind = deriveKind(ev)
                  const color = kindColor(kind)
                  return (
                    <tr key={i}
                      className="border-b border-border/50 hover:bg-surface/40 transition-colors cursor-pointer"
                      onClick={() => onSeekVideo?.(Number(ev.timestamp ?? ev.time ?? 0))}>
                      <td className="px-3 py-2 text-muted font-mono">{i + 1}</td>
                      <td className="px-3 py-2 font-mono">{Number(ev.timestamp ?? ev.time ?? 0).toFixed(1)}s</td>
                      <td className="px-3 py-2">
                        <span className="badge text-[10px]"
                          style={{ background: color + '22', color, border: `1px solid ${color}44` }}>
                          {kind}
                        </span>
                      </td>
                      <td className="px-3 py-2 text-muted">{ev.zone ?? '—'}</td>
                      <td className="px-3 py-2 text-text/80 max-w-xs truncate">{ev.label ?? ev.description ?? '—'}</td>
                      <td className="px-3 py-2">
                        <button onClick={e => { e.stopPropagation(); loadClip(i) }}
                          disabled={loadingClip}
                          className="btn btn-ghost p-1 text-[10px] gap-1 disabled:opacity-40">
                          {loadingIdx === i
                            ? <Loader2 size={10} className="animate-spin" />
                            : <RefreshCw size={10} />}
                          clip
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

    </div>
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
