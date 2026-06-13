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
import { resolveGradioFile } from '../../backend.js'

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
      const src = resolveGradioFile(r.data[0])
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
    <Box sx={{ flex: 1, display: 'flex', minHeight: 0, overflow: 'hidden' }}>

      {/* Left: clip list */}
      <Box sx={{ flex: '0 0 44%', display: 'flex', flexDirection: 'column', minHeight: 0, borderRight: '1px solid', borderColor: 'divider' }}>
        {/* Header */}
        <Box sx={{ flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 2, py: 1.25, borderBottom: '1px solid', borderColor: 'divider' }}>
          <Typography variant="overline" sx={{ fontSize: '0.6rem' }}>{t(language, 'library.title')}</Typography>
          <IconButton size="small" onClick={refresh} sx={{ borderRadius: 1 }}>
            <RefreshCw size={12} />
          </IconButton>
        </Box>

        {/* Search */}
        {clips.length > 0 && (
          <Box sx={{ flexShrink: 0, display: 'flex', alignItems: 'center', gap: 1, mx: 1.5, my: 1, px: 1, py: 0.5, border: '1px solid', borderColor: 'divider', borderRadius: 1.5 }}>
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

        {status && (
          <Typography variant="caption" color="text.secondary" sx={{ px: 2, pb: 0.5, flexShrink: 0 }}>{status}</Typography>
        )}

        {/* Clip list */}
        <Box sx={{ flex: 1, overflowY: 'auto', px: 1.5, pb: 1.5 }}>
          {visibleClips.length === 0 && clips.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 6, color: 'text.secondary' }}>
              <Film size={28} style={{ margin: '0 auto 12px', display: 'block', opacity: 0.3 }} />
              <Typography variant="caption">{t(language, 'library.empty')}</Typography>
            </Box>
          ) : (
            <AnimatePresence>
              {visibleClips.map((clip, i) => (
                <Paper
                  key={clip}
                  component={motion.div}
                  layout
                  initial={{ opacity: 0, scale: 0.97 }} animate={{ opacity: 1, scale: 1 }}
                  exit={{ opacity: 0, scale: 0.93 }} transition={{ delay: i * 0.03 }}
                  onClick={() => loadPreview(clip)}
                  sx={{
                    cursor: 'pointer',
                    px: 1.5, py: 1, mb: 1,
                    border: '1px solid',
                    borderColor: selected === clip ? 'rgba(247,208,70,0.5)' : 'divider',
                    bgcolor: selected === clip ? 'rgba(247,208,70,0.05)' : 'background.paper',
                    transition: 'border-color 0.15s, background-color 0.15s',
                    '&:hover': { borderColor: selected === clip ? 'rgba(247,208,70,0.5)' : 'rgba(46,64,96,0.8)' },
                  }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 1 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, minWidth: 0 }}>
                      <Film size={12} style={{ color: '#7a8ea8', flexShrink: 0 }} />
                      <Typography variant="caption" sx={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: '0.7rem' }}>
                        {clip}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', gap: 0.25, flexShrink: 0 }}>
                      <MuiTooltip title={t(language, 'library.load')}>
                        <IconButton size="small" onClick={e => { e.stopPropagation(); loadForAnalysis(clip) }}
                          sx={{ color: 'success.main', borderRadius: 1, p: 0.5 }}>
                          <ArrowUpCircle size={11} />
                        </IconButton>
                      </MuiTooltip>
                      <MuiTooltip title={t(language, 'library.delete')}>
                        <IconButton size="small" onClick={e => { e.stopPropagation(); deleteClip(clip) }}
                          sx={{ color: 'error.main', borderRadius: 1, p: 0.5 }}>
                          <Trash2 size={11} />
                        </IconButton>
                      </MuiTooltip>
                    </Box>
                  </Box>
                </Paper>
              ))}
            </AnimatePresence>
          )}
        </Box>
      </Box>

      {/* Right: preview */}
      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0, minWidth: 0, bgcolor: preview ? '#000' : 'background.default' }}>
        {preview ? (
          <video
            key={preview}
            src={preview}
            controls
            style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block' }}
          />
        ) : (
          <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 1.5 }}>
            <Film size={32} style={{ opacity: 0.2 }} />
            <Typography variant="caption" color="text.secondary">
              {t(language, 'library.select_preview')}
            </Typography>
          </Box>
        )}
      </Box>
    </Box>
  )
}
