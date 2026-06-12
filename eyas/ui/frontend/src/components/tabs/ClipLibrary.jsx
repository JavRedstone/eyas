import { useState, useEffect, useMemo } from 'react'
import { RefreshCw, Trash2, ArrowUpCircle, Film, Search } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import Box from '@mui/material/Box'
import InputBase from '@mui/material/InputBase'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import IconButton from '@mui/material/IconButton'
import MuiTooltip from '@mui/material/Tooltip'
import { t } from '../../i18n.js'

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

export default function ClipLibrary({ client, language = 'English' }) {
  const [clips, setClips]       = useState([])
  const [filter, setFilter]     = useState('')
  const [status, setStatus]     = useState('')
  const [preview, setPreview]   = useState(null)
  const [selected, setSelected] = useState(null)

  const visibleClips = useMemo(() => {
    const q = filter.trim().toLowerCase()
    return q ? clips.filter(c => c.toLowerCase().includes(q)) : clips
  }, [clips, filter])

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
      setStatus(t(language, 'library.deleted', { name }))
      setPreview(null)
      setSelected(null)
      refresh()
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  async function loadForAnalysis(name) {
    if (!client) return
    try {
      await client.predict('/load_clip_for_analysis', { choice: name })
      setStatus(t(language, 'library.loaded', { name }))
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography variant="overline">{t(language, 'library.title')}</Typography>
        <IconButton size="small" onClick={refresh} sx={{ borderRadius: 1 }}>
          <RefreshCw size={13} />
        </IconButton>
      </Box>

      {clips.length > 0 && (
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 1, py: 0.5, border: '1px solid', borderColor: 'divider', borderRadius: 1.5 }}>
          <Search size={12} style={{ color: '#7a8ea8', flexShrink: 0 }} />
          <InputBase
            size="small"
            placeholder={t(language, 'library.filter')}
            value={filter}
            onChange={e => setFilter(e.target.value)}
            sx={{ fontSize: '0.75rem', flex: 1 }}
          />
        </Box>
      )}

      {status && <Typography variant="caption" color="text.secondary">{status}</Typography>}

      {visibleClips.length === 0 && clips.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
          <Film size={32} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
          <Typography variant="caption">{t(language, 'library.empty')}</Typography>
        </Box>
      ) : (
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 1.5 }}>
          <AnimatePresence>
            {visibleClips.map((clip, i) => (
              <Paper
                key={clip}
                component={motion.div}
                layout
                initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9 }} transition={{ delay: i * 0.04 }}
                onClick={() => loadPreview(clip)}
                sx={{
                  cursor: 'pointer',
                  p: 1.5,
                  border: '1px solid',
                  borderColor: selected === clip ? 'rgba(247,208,70,0.5)' : 'divider',
                  bgcolor: selected === clip ? 'rgba(247,208,70,0.05)' : 'background.paper',
                  transition: 'border-color 0.15s, background-color 0.15s',
                  '&:hover': { borderColor: selected === clip ? 'rgba(247,208,70,0.5)' : 'rgba(46,64,96,0.8)' },
                }}>
                <Box sx={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: 1 }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                    <Film size={13} style={{ color: '#7a8ea8', flexShrink: 0 }} />
                    <Typography variant="caption" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{clip}</Typography>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 0.5, flexShrink: 0 }}>
                    <MuiTooltip title={t(language, 'library.load')}>
                      <IconButton size="small" onClick={e => { e.stopPropagation(); loadForAnalysis(clip) }}
                        sx={{ color: 'success.main', borderRadius: 1, p: 0.5 }}>
                        <ArrowUpCircle size={12} />
                      </IconButton>
                    </MuiTooltip>
                    <MuiTooltip title={t(language, 'library.delete')}>
                      <IconButton size="small" onClick={e => { e.stopPropagation(); deleteClip(clip) }}
                        sx={{ color: 'error.main', borderRadius: 1, p: 0.5 }}>
                        <Trash2 size={12} />
                      </IconButton>
                    </MuiTooltip>
                  </Box>
                </Box>
              </Paper>
            ))}
          </AnimatePresence>
        </Box>
      )}

      {preview && (
        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 1 }}>
            {t(language, 'library.preview_hdr')}<Typography component="span" variant="caption" sx={{ textTransform: 'none', color: 'text.primary', fontWeight: 400 }}>{selected}</Typography>
          </Typography>
          <video src={preview} controls style={{ width: '100%', borderRadius: 12, border: '1px solid #2e4060', background: '#000', maxHeight: 192, display: 'block' }} />
        </Box>
      )}
    </Box>
  )
}
