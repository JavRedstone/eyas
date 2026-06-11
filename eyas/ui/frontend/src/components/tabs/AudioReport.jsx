import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Volume2, Loader2 } from 'lucide-react'

const PHASES = [
  { until: 4,  msg: 'Summarizing events…'   },
  { until: 12, msg: 'Synthesizing speech…'  },
  { until: Infinity, msg: 'Finishing up…'   },
]

function phaseMsg(elapsed) {
  for (const p of PHASES) {
    if (elapsed < p.until) return p.msg
  }
  return 'Finishing up…'
}

export default function AudioReport({ client, summary }) {
  const [audioSrc, setAudioSrc]   = useState(null)
  const [loading, setLoading]     = useState(false)
  const [statusMsg, setStatusMsg] = useState('')
  const [elapsed, setElapsed]     = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (loading) {
      setElapsed(0)
      timerRef.current = setInterval(() => setElapsed(s => s + 1), 1000)
    } else {
      clearInterval(timerRef.current)
    }
    return () => clearInterval(timerRef.current)
  }, [loading])

  async function generate() {
    if (!client) return
    setLoading(true)
    setStatusMsg('')
    setAudioSrc(null)
    try {
      const eventsArr = summary?.events ?? []
      const r = await client.predict('/generate_audio', { events: eventsArr })
      const [fd, msg] = r.data
      if (fd) {
        const src = fd.url ?? (fd.path ? `/gradio_api/file=${fd.path}` : null)
        if (src) { setAudioSrc(src); setStatusMsg(msg || '') }
        else setStatusMsg('No audio returned.')
      } else {
        setStatusMsg(msg || 'No audio returned.')
      }
    } catch (e) { setStatusMsg(`Error: ${e.message}`) }
    finally { setLoading(false) }
  }

  const bars = Array.from({ length: 40 }, (_, i) => ({
    h: Math.sin(i * 0.4) * 0.4 + Math.random() * 0.3 + 0.2,
  }))

  return (
    <div className="space-y-5">
      <p className="section-label">Spoken Security Report</p>
      <p className="text-xs text-muted">Generates a spoken audio summary of the event log using the TTS model.</p>

      {/* Waveform visualization */}
      <div className="flex items-center justify-center gap-0.5 h-16 bg-surface rounded-xl border border-border px-4">
        {bars.map((b, i) => (
          <motion.div key={i}
            className="w-1 rounded-full bg-accent/60"
            style={{ height: `${b.h * 100}%` }}
            animate={audioSrc ? { scaleY: [1, b.h + 0.4, 1], opacity: [0.6, 1, 0.6] } : { scaleY: 1 }}
            transition={{ duration: 0.8 + i * 0.02, repeat: Infinity, delay: i * 0.02 }} />
        ))}
      </div>

      {audioSrc && (
        <audio src={audioSrc} controls className="w-full rounded-lg" style={{ colorScheme: 'dark' }} />
      )}

      {/* Status / progress */}
      {loading && (
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-muted">
            <Loader2 size={12} className="animate-spin shrink-0" />
            <span>{phaseMsg(elapsed)}</span>
            <span className="font-mono text-muted/60">{elapsed}s</span>
          </div>
          <div className="h-1 w-full rounded-full bg-surface border border-border overflow-hidden">
            <motion.div
              className="h-full rounded-full bg-accent/70"
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }}
            />
          </div>
        </div>
      )}
      {!loading && statusMsg && (
        <p className="text-xs text-muted">{statusMsg}</p>
      )}

      <button onClick={generate} disabled={loading}
        className="btn btn-secondary disabled:opacity-40">
        {loading
          ? <><Loader2 size={14} className="animate-spin" /> Generating…</>
          : <><Volume2 size={14} /> Generate Audio Report</>}
      </button>
    </div>
  )
}
