import { useState, useEffect } from 'react'
import { RefreshCw, Play, Trash2, ArrowUpCircle, Film } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

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
  if (value.path) return `/gradio_api/file=${value.path}`
  if (value.url) {
    try { return new URL(value.url).pathname } catch {}
    return value.url
  }
  return ''
}

export default function ClipLibrary({ client }) {
  const [clips, setClips]     = useState([])
  const [status, setStatus]   = useState('')
  const [preview, setPreview] = useState(null)
  const [selected, setSelected] = useState(null)

  useEffect(() => { refresh() }, [client])

  async function refresh() {
    if (!client) return
    try {
      const r = await client.predict('/refresh_library', {})
      setClips(r.data[0] || [])
    } catch {}
  }

  async function loadPreview(name) {
    if (!client) return
    setSelected(name)
    try {
      const r = await client.predict('/preview_clip', { choice: name })
      const src = resolveVideoSrc(r.data[0])
      if (src) setPreview(src)
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  async function deleteClip(name) {
    if (!client) return
    try {
      await client.predict('/delete_clip', { choice: name })
      setStatus(`Deleted: ${name}`)
      setPreview(null)
      setSelected(null)
      refresh()
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  async function loadForAnalysis(name) {
    if (!client) return
    try {
      await client.predict('/load_clip_for_analysis', { choice: name })
      setStatus(`Loaded for analysis: ${name}`)
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="section-label">Stored Clips</p>
        <button onClick={refresh} className="btn btn-ghost p-1.5"><RefreshCw size={13} /></button>
      </div>

      {status && <p className="text-xs text-muted">{status}</p>}

      {clips.length === 0 ? (
        <div className="text-center py-12 text-muted">
          <Film size={32} className="mx-auto mb-3 opacity-30" />
          <p className="text-xs">No clips stored yet.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <AnimatePresence>
            {clips.map((clip, i) => (
              <motion.div key={clip} layout
                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }} transition={{ delay: i * 0.04 }}
                className={`cursor-pointer rounded-xl border p-3 transition-colors
                  ${selected === clip ? 'border-accent/60 bg-accent/5' : 'border-border bg-surface hover:border-border/80'}`}
                onClick={() => loadPreview(clip)}>
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <Film size={13} className="text-muted shrink-0" />
                    <span className="text-xs truncate text-text">{clip}</span>
                  </div>
                  <div className="flex gap-1 shrink-0">
                    <button onClick={e => { e.stopPropagation(); loadForAnalysis(clip) }}
                      className="btn btn-ghost p-1 text-success hover:text-success" title="Load for analysis">
                      <ArrowUpCircle size={12} />
                    </button>
                    <button onClick={e => { e.stopPropagation(); deleteClip(clip) }}
                      className="btn btn-ghost p-1 text-danger hover:text-danger" title="Delete">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {preview && (
        <div>
          <p className="section-label mb-2">Preview: <span className="normal-case font-normal text-text">{selected}</span></p>
          <video src={preview} controls className="w-full rounded-xl border border-border bg-black max-h-48" />
        </div>
      )}
    </div>
  )
}
