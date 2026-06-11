import { motion, AnimatePresence } from 'framer-motion'
import { Play, CheckCircle, Circle, Loader2, XCircle } from 'lucide-react'

const STEP_LABELS = {
  load_video:    'Load Video',
  yolo:          'YOLO Tracking',
  vlm:           'VLM Captioning',
  llm_summarize: 'LLM Summary',
}

export default function AnalysisPanel({ analyzing, statusMsg, pipelineSteps, pipelineProgress, onAnalyze }) {

  return (
    <div className="card">
      <div className="panel-header">
        <div className="w-1.5 h-1.5 rounded-full bg-accent" />
        <span className="text-xs font-semibold text-text">Analysis</span>
      </div>
      <div className="p-4 space-y-4">
        <motion.button
          className={`btn btn-primary w-full justify-center py-3 text-base font-semibold
            ${analyzing ? 'opacity-60 cursor-not-allowed' : ''}`}
          onClick={onAnalyze}
          disabled={analyzing}
          whileHover={!analyzing ? { scale: 1.01 } : {}}
          whileTap={!analyzing ? { scale: 0.98 } : {}}>
          {analyzing
            ? <><Loader2 size={18} className="animate-spin" /> Processing…</>
            : <><Play size={18} /> Analyze</>}
        </motion.button>

        {statusMsg && (
          <p className="text-xs text-muted font-mono">{statusMsg}</p>
        )}

        {(analyzing || pipelineProgress > 0) && (
          <div className="space-y-1">
            <div className="h-2 w-full overflow-hidden rounded-full bg-surface border border-border">
              <div
                className="h-full rounded-full bg-accent transition-all duration-300"
                style={{ width: `${Math.max(0, Math.min(100, pipelineProgress || 0))}%` }}
              />
            </div>
            <div className="text-[10px] text-muted">Progress: {Math.round(pipelineProgress || 0)}%</div>
          </div>
        )}

        {/* Pipeline steps */}
        <AnimatePresence>
          {pipelineSteps.length > 0 && (
            <motion.div className="space-y-2"
              initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }}>
              {pipelineSteps.map((step, i) => (
                <motion.div key={step.id}
                  className="flex items-start gap-3"
                  initial={{ opacity: 0, x: -6 }} animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.05 }}>
                  <StepIcon state={step.state} />
                  <div className="min-w-0">
                    <div className={`text-xs font-medium ${
                      step.state === 'done'    ? 'text-success' :
                      step.state === 'running' ? 'text-accent'  :
                      step.state === 'error'   ? 'text-danger'  : 'text-muted'}`}>
                      {STEP_LABELS[step.id] || step.id}
                    </div>
                    {step.detail && <div className="text-[10px] text-muted truncate">{step.detail}</div>}
                  </div>
                </motion.div>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

      </div>
    </div>
  )
}

function StepIcon({ state }) {
  if (state === 'done')    return <CheckCircle size={14} className="text-success mt-0.5 shrink-0" />
  if (state === 'running') return <Loader2 size={14} className="text-accent mt-0.5 shrink-0 animate-spin" />
  if (state === 'error')   return <XCircle size={14} className="text-danger mt-0.5 shrink-0" />
  return <Circle size={14} className="text-muted/40 mt-0.5 shrink-0" />
}

