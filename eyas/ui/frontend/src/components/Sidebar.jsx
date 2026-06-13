import { useRef } from 'react'
import { Upload, Trash2, Download, Layers, X, CheckCircle, XCircle, Loader2, Clock } from 'lucide-react'
import { motion } from 'framer-motion'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Select from '@mui/material/Select'
import MenuItem from '@mui/material/MenuItem'
import FormControl from '@mui/material/FormControl'
import Button from '@mui/material/Button'
import Divider from '@mui/material/Divider'
import Tooltip from '@mui/material/Tooltip'
import Chip from '@mui/material/Chip'
import Checkbox from '@mui/material/Checkbox'
import { t } from '../i18n.js'

const STATUS_ICON = {
  pending: () => <Clock size={12} style={{ color: '#7a8ea8', flexShrink: 0 }} />,
  running: () => <Loader2 size={12} style={{ color: '#f7d046', flexShrink: 0, animation: 'spin 1s linear infinite' }} />,
  done:    () => <CheckCircle size={12} style={{ color: '#34D399', flexShrink: 0 }} />,
  error:   () => <XCircle size={12} style={{ color: '#F87171', flexShrink: 0 }} />,
}

export default function Sidebar({
  samples = [], queue = [], language = 'English',
  onAddFiles, onAddSample, onRemoveItem,
  onToggleSelected, onSelectAll,
  allPendingSelected = true, somePendingSelected = false,
  sessionEventCount = 0, sessionRunCount = 0,
  onClearSession, onExportZip, exportingZip = false,
}) {
  const inputRef = useRef()
  const hasSession = sessionEventCount > 0
  const hasPending = queue.some(q => q.status === 'pending')

  function handleDrop(e) {
    e.preventDefault()
    const files = [...(e.dataTransfer?.files ?? [])].filter(f => f.type.startsWith('video/'))
    if (files.length) onAddFiles(files)
  }

  function handleChange(e) {
    const files = [...(e.target.files ?? [])].filter(f => f.type.startsWith('video/'))
    if (files.length) onAddFiles(files)
    e.target.value = ''
  }

  return (
    <Paper>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main' }} />
        <Typography variant="caption" fontWeight={600} sx={{ color: 'text.primary', letterSpacing: '0.03em' }}>{t(language, 'panel.footage')}</Typography>
      </Box>

      <Box sx={{ p: 1.5, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        {samples.length > 0 && (
          <Box>
            <Typography variant="overline" sx={{ display: 'block', mb: 0.75, fontSize: '0.65rem' }}>{t(language, 'sidebar.sample_clips')}</Typography>
            <FormControl size="small" fullWidth>
              <Select
                value=""
                onChange={e => { if (e.target.value) onAddSample(e.target.value) }}
                displayEmpty
                sx={{ fontSize: '0.8rem' }}>
                <MenuItem value=""><em style={{ color: '#7a8ea8' }}>{t(language, 'sidebar.choose_sample')}</em></MenuItem>
                {samples.map(s => <MenuItem key={s} value={s}>{s}</MenuItem>)}
              </Select>
            </FormControl>
          </Box>
        )}

        <Box>
          <Typography variant="overline" sx={{ display: 'block', mb: 0.75, fontSize: '0.65rem' }}>{t(language, 'sidebar.upload_video')}</Typography>
          <Box
            component={motion.div}
            whileHover={{ scale: 1.01 }} whileTap={{ scale: 0.99 }}
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            sx={{
              border: '2px dashed', borderColor: 'divider', borderRadius: 2, p: 1.5,
              textAlign: 'center', cursor: 'pointer',
              transition: 'border-color 0.15s, background-color 0.15s',
              '&:hover': { borderColor: 'primary.dark', bgcolor: 'rgba(247,208,70,0.04)' },
            }}>
            <input ref={inputRef} type="file" accept="video/*" multiple style={{ display: 'none' }} onChange={handleChange} />
            <Upload size={16} style={{ margin: '0 auto 4px', color: '#7a8ea8', display: 'block' }} />
            <Typography variant="caption" color="text.secondary">{t(language, 'sidebar.drop_upload')}</Typography>
          </Box>
        </Box>

        {/* Queue list */}
        {queue.length > 0 && (
          <Box>
            {/* Select-all header for pending items */}
            {hasPending && (
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5, ml: -0.5 }}>
                <Checkbox
                  size="small"
                  checked={allPendingSelected && somePendingSelected}
                  indeterminate={!allPendingSelected && somePendingSelected}
                  onChange={e => onSelectAll(e.target.checked)}
                  sx={{ p: 0.5, color: 'text.disabled', '&.Mui-checked': { color: 'primary.main' }, '&.MuiCheckbox-indeterminate': { color: 'primary.main' } }}
                />
                <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                  {t(language, 'sidebar.select_all_pending')}
                </Typography>
              </Box>
            )}

            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
              {queue.map(item => {
                const isPending = item.status === 'pending'
                const isChecked = item.selected !== false
                return (
                  <Box key={item.id}
                    sx={{
                      display: 'flex', alignItems: 'center', gap: 0.5,
                      p: 0.75, borderRadius: 1.5,
                      bgcolor: item.status === 'running' ? 'rgba(247,208,70,0.06)' : 'rgba(20,45,79,0.3)',
                      border: '1px solid',
                      borderColor: item.status === 'error' ? 'rgba(248,113,113,0.3)'
                        : item.status === 'done' ? 'rgba(52,211,153,0.2)'
                        : item.status === 'running' ? 'rgba(247,208,70,0.3)'
                        : isChecked ? 'rgba(247,208,70,0.2)' : 'divider',
                      opacity: (isPending && !isChecked) ? 0.5 : 1,
                      minWidth: 0,
                    }}>
                    {/* Checkbox only for pending items */}
                    {isPending ? (
                      <Checkbox
                        size="small"
                        checked={isChecked}
                        onChange={() => onToggleSelected(item.id)}
                        sx={{ p: 0.25, mr: -0.25, flexShrink: 0, color: 'text.disabled', '&.Mui-checked': { color: 'primary.main' } }}
                      />
                    ) : (
                      <Box sx={{ width: 20, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {STATUS_ICON[item.status]?.()}
                      </Box>
                    )}

                    <Typography variant="caption" noWrap sx={{ flex: 1, fontSize: '0.7rem', minWidth: 0 }}>
                      {item.name}
                    </Typography>

                    {item.zone && (
                      <Chip label={item.zone} size="small"
                        sx={{ height: 16, fontSize: '0.6rem', flexShrink: 0,
                          bgcolor: 'rgba(247,208,70,0.1)', color: 'rgba(247,208,70,0.8)',
                          border: '1px solid rgba(247,208,70,0.2)', '& .MuiChip-label': { px: 0.75 } }} />
                    )}

                    {isPending && (
                      <Tooltip title="Remove">
                        <Box component="button" onClick={() => onRemoveItem(item.id)}
                          sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center',
                            width: 16, height: 16, p: 0, border: 'none', background: 'none',
                            cursor: 'pointer', color: '#7a8ea8', flexShrink: 0,
                            borderRadius: 0.5, '&:hover': { color: 'text.primary', bgcolor: 'divider' } }}>
                          <X size={10} />
                        </Box>
                      </Tooltip>
                    )}
                    {item.status === 'error' && item.error && (
                      <Tooltip title={item.error}>
                        <Typography variant="caption" color="error" sx={{ fontSize: '0.6rem', flexShrink: 0 }}>err</Typography>
                      </Tooltip>
                    )}
                  </Box>
                )
              })}
            </Box>
          </Box>
        )}

        {/* Session controls */}
        <Divider sx={{ my: 0.5 }} />
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Layers size={12} style={{ color: '#7a8ea8', flexShrink: 0 }} />
          <Typography variant="caption" color="text.secondary" sx={{ flex: 1, fontSize: '0.7rem' }}>
            {hasSession
              ? t(language, 'session.events', { count: sessionEventCount, runs: sessionRunCount })
              : t(language, 'session.empty')}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={t(language, 'session.export')}>
            <span style={{ flex: 1 }}>
              <Button
                size="small" variant="outlined" fullWidth
                startIcon={<Download size={12} />}
                onClick={onExportZip}
                disabled={!hasSession || exportingZip}
                sx={{ fontSize: '0.7rem', py: 0.5 }}>
                {exportingZip ? t(language, 'session.exporting') : t(language, 'session.export')}
              </Button>
            </span>
          </Tooltip>
          <Tooltip title={t(language, 'session.clear')}>
            <span>
              <Button
                size="small" variant="outlined" color="error"
                onClick={onClearSession}
                disabled={!hasSession}
                sx={{ fontSize: '0.7rem', py: 0.5, minWidth: 0, px: 1.25 }}>
                <Trash2 size={12} />
              </Button>
            </span>
          </Tooltip>
        </Box>
      </Box>
    </Paper>
  )
}
