import { motion, AnimatePresence } from 'framer-motion'

const STATUS_META = {
  ready:   { label: 'ready',   color: '#34D399', bg: '#34D39912', ring: '#34D39933' },
  error:   { label: 'error',   color: '#F87171', bg: '#F8717112', ring: '#F8717133' },
  skipped: { label: 'skipped', color: '#6B728E', bg: '#6B728E12', ring: '#6B728E33' },
  loading: { label: 'loading', color: '#E8682A', bg: '#E8682A12', ring: '#E8682A33' },
  pending: { label: 'pending', color: '#2A3050', bg: 'transparent', ring: '#2A3050' },
}

function meta(s) { return STATUS_META[s] || STATUS_META.pending }

export default function Splash({ items = [], pct = 0 }) {
  const hasItems = items.length > 0

  return (
    <motion.div className="fixed inset-0 bg-bg flex items-center justify-center z-50"
      exit={{ opacity: 0, scale: 1.01 }} transition={{ duration: 0.35 }}>
      <div className="w-full max-w-md px-6">

        {/* Wordmark */}
        <div className="flex items-center gap-3 mb-10">
          <div className="relative w-9 h-9">
            <div className="absolute inset-0 rounded-xl bg-accent/10 border border-accent/20" />
            <motion.div className="absolute inset-0 rounded-xl border border-accent/40"
              animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 2, repeat: Infinity }} />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="w-2.5 h-2.5 rounded-full bg-accent" />
            </div>
          </div>
          <div>
            <div className="text-xl font-semibold tracking-tight">Eyas</div>
            <div className="text-xs text-muted">AI Security Camera Agent</div>
          </div>
        </div>

        {/* Model rows */}
        <div className="space-y-1.5 mb-6">
          {hasItems
            ? items.map((item, i) => <ModelRow key={item.label || i} item={item} index={i} />)
            : [0,1,2,3,4].map(i => <SkeletonRow key={i} index={i} />)
          }
        </div>

        {/* Progress bar */}
        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <span className="text-[10px] text-muted font-mono uppercase tracking-widest">Initializing</span>
            <span className="text-[10px] text-muted font-mono">{pct}%</span>
          </div>
          <div className="h-px bg-surface rounded-full overflow-hidden">
            <motion.div className="h-full bg-accent rounded-full"
              animate={{ width: `${Math.max(pct, hasItems ? 4 : 12)}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }} />
          </div>
        </div>

      </div>
    </motion.div>
  )
}

function ModelRow({ item, index }) {
  const { status, label, detail, model_name } = item
  const m = meta(status)
  const isLoading = status === 'loading'
  const isDone    = status === 'ready' || status === 'skipped'
  const isError   = status === 'error'

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.06, duration: 0.22 }}
      className="relative flex items-center gap-3 px-3 py-2.5 rounded-lg overflow-hidden"
      style={{ background: status !== 'pending' ? m.bg : 'transparent' }}>

      {/* Shimmer for loading row */}
      {isLoading && (
        <motion.div className="absolute inset-0 pointer-events-none"
          style={{ background: 'linear-gradient(90deg, transparent, rgba(232,104,42,0.07), transparent)' }}
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }} />
      )}

      {/* Icon */}
      <div className="relative shrink-0 w-5 h-5 flex items-center justify-center">
        {isLoading ? (
          <>
            <motion.div className="absolute w-5 h-5 rounded-full border-2"
              style={{ borderColor: m.ring, borderTopColor: m.color }}
              animate={{ rotate: 360 }}
              transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }} />
            <div className="w-1.5 h-1.5 rounded-full" style={{ background: m.color }} />
          </>
        ) : isDone ? (
          <motion.svg initial={{ scale: 0 }} animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 22 }}
            viewBox="0 0 16 16" fill="none" className="w-4.5 h-4.5" width={18} height={18}>
            <circle cx="8" cy="8" r="7" stroke={m.color} strokeWidth="1.5" fill={m.bg} />
            <motion.path d="M5 8.5l2 2 4-4" stroke={m.color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
              initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 0.25, delay: 0.05 }} />
          </motion.svg>
        ) : isError ? (
          <svg viewBox="0 0 16 16" fill="none" width={18} height={18}>
            <circle cx="8" cy="8" r="7" stroke={m.color} strokeWidth="1.5" fill={m.bg} />
            <path d="M5.5 5.5l5 5M10.5 5.5l-5 5" stroke={m.color} strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        ) : (
          <div className="w-4 h-4 rounded-full border-2" style={{ borderColor: m.ring }} />
        )}
      </div>

      {/* Label + model name */}
      <div className="flex-1 min-w-0">
        <div className={`text-xs font-medium truncate ${
          isDone ? 'text-text' : isLoading ? 'text-text' : 'text-muted'}`}>
          {label}
        </div>
        {(model_name || detail) && (
          <div className="text-[10px] text-muted truncate mt-0.5 font-mono opacity-70">
            {model_name || detail}
          </div>
        )}
      </div>

      {/* Badge */}
      <div className="shrink-0 text-[9px] font-bold uppercase tracking-widest px-1.5 py-0.5 rounded font-mono"
        style={{ color: m.color, background: m.bg, border: `1px solid ${m.ring}` }}>
        {m.label}
      </div>
    </motion.div>
  )
}

function SkeletonRow({ index }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.5 }}
      transition={{ delay: index * 0.05 }}
      className="flex items-center gap-3 px-3 py-2.5">
      <div className="w-5 h-5 rounded-full bg-surface shrink-0" />
      <div className="flex-1 space-y-1.5">
        <div className="h-2.5 bg-surface rounded w-28" />
        <div className="h-2 bg-surface/60 rounded w-44" />
      </div>
      <div className="w-12 h-4 bg-surface rounded" />
    </motion.div>
  )
}
