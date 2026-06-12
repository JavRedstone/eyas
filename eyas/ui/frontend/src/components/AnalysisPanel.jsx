import { motion, AnimatePresence } from 'framer-motion'
import { Play, CheckCircle, Circle, Loader2, XCircle } from 'lucide-react'
import Box from '@mui/material/Box'
import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import LinearProgress from '@mui/material/LinearProgress'
import { t } from '../i18n.js'

const STATE_COLOR = { done: 'success.main', running: 'primary.main', error: 'error.main' }

export default function AnalysisPanel({ analyzing, statusMsg, pipelineSteps, pipelineProgress, onAnalyze, language = 'English' }) {
  return (
    <Paper>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 2, py: 1.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Box sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: 'primary.main' }} />
        <Typography variant="caption" fontWeight={600} sx={{ color: 'text.primary', letterSpacing: '0.03em' }}>{t(language, 'panel.analysis')}</Typography>
      </Box>

      <Box sx={{ p: 2, display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Button
          variant="contained" color="primary" fullWidth
          onClick={onAnalyze} disabled={analyzing}
          startIcon={analyzing ? <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} /> : <Play size={16} />}
          sx={{ py: 1.25, fontSize: '0.95rem' }}>
          {analyzing ? t(language, 'analysis.processing') : t(language, 'analysis.analyze')}
        </Button>

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
