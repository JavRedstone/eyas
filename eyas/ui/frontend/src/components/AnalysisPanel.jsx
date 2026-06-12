import { motion, AnimatePresence } from 'framer-motion'
import { Play, CheckCircle, Circle, Loader2, XCircle, StopCircle } from 'lucide-react'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import LinearProgress from '@mui/material/LinearProgress'
import { t } from '../i18n.js'

const STATE_COLOR = { done: 'success.main', running: 'primary.main', error: 'error.main' }

export default function AnalysisPanel({
  analyzing, stopping = false, statusMsg, pipelineSteps, pipelineProgress,
  onAnalyzeAll, onStop, queuePending = 0, queueDone = 0, queueTotal = 0,
  processingItem, language = 'English',
}) {
  const btnLabel = stopping
    ? 'Stopping…'
    : analyzing
      ? t(language, 'analysis.processing')
      : t(language, 'analysis.analyze_all', { count: queuePending })

  return (
    <Paper>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main' }} />
        <Typography variant="caption" fontWeight={600} sx={{ color: 'text.primary', letterSpacing: '0.03em' }}>
          {t(language, 'panel.analysis')}
        </Typography>
        {queueTotal > 0 && (
          <Typography variant="caption" color="text.secondary" sx={{ ml: 'auto', fontFamily: 'monospace', fontSize: '0.7rem' }}>
            {queueDone}/{queueTotal}
          </Typography>
        )}
      </Box>

      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained" color="primary" sx={{ flex: 1, py: 1.25, fontSize: '0.95rem' }}
            onClick={onAnalyzeAll} disabled={analyzing || queuePending === 0}
            startIcon={analyzing ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={16} />}>
            {btnLabel}
          </Button>
          {analyzing && (
            <Button
              variant="outlined" color="error" onClick={onStop} disabled={stopping}
              sx={{
                py: 1.25, minWidth: 0, px: 1.5,
                borderColor: stopping ? 'divider' : 'rgba(248,113,113,0.5)',
                '&:hover': { borderColor: '#F87171', bgcolor: 'rgba(248,113,113,0.06)' },
                '&.Mui-disabled': { opacity: 0.5 },
              }}>
              {stopping
                ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
                : <StopCircle size={16} />}
            </Button>
          )}
        </Box>

        {analyzing && processingItem && (
          <Typography variant="caption" color="text.secondary" noWrap sx={{ fontFamily: 'monospace' }}>
            {processingItem.zone ? `[${processingItem.zone}] ` : ''}{processingItem.name}
          </Typography>
        )}

        {statusMsg && (
          <Typography variant="caption" color="text.secondary" sx={{ fontFamily: 'monospace' }}>
            {statusMsg}
          </Typography>
        )}

        {(analyzing || pipelineProgress > 0) && (
          <Box>
            <LinearProgress
              variant="determinate"
              value={Math.max(0, Math.min(100, pipelineProgress || 0))}
              sx={{ mb: 0.5 }}
            />
            <Typography variant="caption" color="text.secondary">
              {t(language, 'analysis.progress', { pct: Math.round(pipelineProgress || 0) })}
            </Typography>
          </Box>
        )}

        <AnimatePresence>
          {pipelineSteps.length > 0 && (
            <Box component={motion.div}
              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}
              sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
              {pipelineSteps.map((step, i) => (
                <Box key={step.id} component={motion.div}
                  initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}
                  sx={{ display: 'flex', alignItems: 'flex-start', gap: 1 }}>
                  <StepIcon state={step.state} />
                  <Box sx={{ minWidth: 0 }}>
                    <Typography variant="caption" fontWeight={500}
                      sx={{ color: STATE_COLOR[step.state] || 'text.secondary', display: 'block' }}>
                      {t(language, `step.${step.id}`) || step.id}
                    </Typography>
                    {step.detail && (
                      <Typography variant="caption" color="text.secondary" noWrap sx={{ fontSize: '0.65rem' }}>
                        {step.detail}
                      </Typography>
                    )}
                  </Box>
                </Box>
              ))}
            </Box>
          )}
        </AnimatePresence>
      </Box>
    </Paper>
  )
}

function StepIcon({ state }) {
  const style = { flexShrink: 0, marginTop: 1 }
  if (state === 'done')    return <CheckCircle size={14} style={{ ...style, color: '#34D399' }} />
  if (state === 'running') return <Loader2 size={14} style={{ ...style, color: '#f7d046', animation: 'spin 1s linear infinite' }} />
  if (state === 'error')   return <XCircle size={14} style={{ ...style, color: '#F87171' }} />
  return <Circle size={14} style={{ ...style, color: 'rgba(122,142,168,0.4)' }} />
}
