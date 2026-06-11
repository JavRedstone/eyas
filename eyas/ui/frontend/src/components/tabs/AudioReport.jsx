import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import { Volume2, Loader2 } from 'lucide-react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import LinearProgress from '@mui/material/LinearProgress'

const PHASES = [
  { until: 4,        msg: 'Summarizing events…'  },
  { until: 12,       msg: 'Synthesizing speech…' },
  { until: Infinity, msg: 'Finishing up…'         },
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
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2.5 }}>
      <Typography variant="overline" sx={{ display: 'block' }}>Spoken Security Report</Typography>
      <Typography variant="caption" color="text.secondary">
        Generates a spoken audio summary of the event log using the TTS model.
      </Typography>

      {/* Waveform visualization */}
      <Box sx={{
        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 0.5,
        height: 64, bgcolor: 'rgba(20,45,79,0.5)', borderRadius: 2,
        border: '1px solid', borderColor: 'divider', px: 2,
      }}>
        {bars.map((b, i) => (
          <motion.div key={i}
            style={{ width: 4, borderRadius: 9999, background: 'rgba(247,208,70,0.6)', height: `${b.h * 100}%` }}
            animate={audioSrc ? { scaleY: [1, b.h + 0.4, 1], opacity: [0.6, 1, 0.6] } : { scaleY: 1 }}
            transition={{ duration: 0.8 + i * 0.02, repeat: Infinity, delay: i * 0.02 }} />
        ))}
      </Box>

      {audioSrc && (
        <audio src={audioSrc} controls style={{ width: '100%', borderRadius: 8, colorScheme: 'dark' }} />
      )}

      {/* Status / progress */}
      {loading && (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Loader2 size={12} style={{ flexShrink: 0, animation: 'spin 1s linear infinite' }} />
            <Typography variant="caption" color="text.secondary">{phaseMsg(elapsed)}</Typography>
            <Typography variant="caption" sx={{ color: 'text.secondary', opacity: 0.6, fontFamily: 'monospace' }}>{elapsed}s</Typography>
          </Box>
          <Box sx={{ position: 'relative', overflow: 'hidden', height: 4, borderRadius: 2, bgcolor: 'rgba(20,45,79,0.5)', border: '1px solid', borderColor: 'divider' }}>
            <Box component={motion.div}
              sx={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, borderRadius: 2, bgcolor: 'rgba(247,208,70,0.7)' }}
              animate={{ x: ['-100%', '100%'] }}
              transition={{ duration: 1.4, repeat: Infinity, ease: 'easeInOut' }} />
          </Box>
        </Box>
      )}
      {!loading && statusMsg && (
        <Typography variant="caption" color="text.secondary">{statusMsg}</Typography>
      )}

      <Button
        variant="outlined"
        onClick={generate}
        disabled={loading}
        startIcon={loading ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Volume2 size={14} />}
        sx={{
          alignSelf: 'flex-start',
          borderColor: 'divider',
          color: 'text.primary',
          bgcolor: 'rgba(20,45,79,0.5)',
          '&:hover': { borderColor: 'rgba(247,208,70,0.4)', bgcolor: 'rgba(247,208,70,0.04)' },
          '&.Mui-disabled': { opacity: 0.4 },
        }}>
        {loading ? 'Generating…' : 'Generate Audio Report'}
      </Button>
    </Box>
  )
}
