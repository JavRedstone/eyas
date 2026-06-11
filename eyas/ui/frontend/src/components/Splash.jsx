import { motion } from 'framer-motion'

const STATUS_META = {
  ready:   { label: 'ready',   color: '#34D399', bg: '#34D39912', ring: '#34D39933' },
  error:   { label: 'error',   color: '#F87171', bg: '#F8717112', ring: '#F8717133' },
  skipped: { label: 'skipped', color: '#7a8ea8', bg: '#7a8ea812', ring: '#7a8ea833' },
  loading: { label: 'loading', color: '#f7d046', bg: '#f7d04612', ring: '#f7d04633' },
  pending: { label: 'pending', color: '#2e4060', bg: 'transparent', ring: '#2e4060' },
}

function meta(s) { return STATUS_META[s] || STATUS_META.pending }

export default function Splash({ items = [], pct = 0 }) {
  const hasItems = items.length > 0

  return (
    <motion.div
      style={{ position: 'fixed', inset: 0, background: '#0e2946', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1300 }}
      exit={{ opacity: 0, scale: 1.01 }} transition={{ duration: 0.35 }}>
      <div style={{ width: '100%', maxWidth: 448, padding: '0 24px' }}>

        {/* Wordmark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 40 }}>
          <div style={{ position: 'relative', width: 36, height: 36 }}>
            <div style={{ position: 'absolute', inset: 0, borderRadius: 12, background: 'rgba(247,208,70,0.10)', border: '1px solid rgba(247,208,70,0.20)' }} />
            <motion.div style={{ position: 'absolute', inset: 0, borderRadius: 12, border: '1px solid rgba(247,208,70,0.40)' }}
              animate={{ opacity: [0.4, 1, 0.4] }} transition={{ duration: 2, repeat: Infinity }} />
            <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <div style={{ width: 10, height: 10, borderRadius: '50%', background: '#f7d046' }} />
            </div>
          </div>
          <div>
            <div style={{ fontSize: '1.25rem', fontWeight: 600, letterSpacing: '-0.01em', color: '#e5e1d8' }}>Eyas</div>
            <div style={{ fontSize: '0.75rem', color: '#7a8ea8' }}>AI Security Camera Agent</div>
          </div>
        </div>

        {/* Model rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 24 }}>
          {hasItems
            ? items.map((item, i) => <ModelRow key={item.label || i} item={item} index={i} />)
            : [0,1,2,3,4].map(i => <SkeletonRow key={i} index={i} />)
          }
        </div>

        {/* Progress bar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.625rem', color: '#7a8ea8', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Initializing</span>
            <span style={{ fontSize: '0.625rem', color: '#7a8ea8', fontFamily: 'monospace' }}>{pct}%</span>
          </div>
          <div style={{ height: 1, background: '#142d4f', borderRadius: 9999, overflow: 'hidden' }}>
            <motion.div style={{ height: '100%', background: '#f7d046', borderRadius: 9999 }}
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
      style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 8, overflow: 'hidden', background: status !== 'pending' ? m.bg : 'transparent' }}>

      {/* Shimmer for loading row */}
      {isLoading && (
        <motion.div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: 'linear-gradient(90deg, transparent, rgba(232,104,42,0.07), transparent)' }}
          animate={{ x: ['-100%', '200%'] }}
          transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }} />
      )}

      {/* Icon */}
      <div style={{ position: 'relative', flexShrink: 0, width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {isLoading ? (
          <>
            <motion.div style={{ position: 'absolute', width: 20, height: 20, borderRadius: '50%', border: '2px solid', borderColor: m.ring, borderTopColor: m.color }}
              animate={{ rotate: 360 }}
              transition={{ duration: 0.9, repeat: Infinity, ease: 'linear' }} />
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: m.color }} />
          </>
        ) : isDone ? (
          <motion.svg initial={{ scale: 0 }} animate={{ scale: 1 }}
            transition={{ type: 'spring', stiffness: 500, damping: 22 }}
            viewBox="0 0 16 16" fill="none" width={18} height={18}>
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
          <div style={{ width: 16, height: 16, borderRadius: '50%', border: `2px solid ${m.ring}` }} />
        )}
      </div>

      {/* Label + model name */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: (isDone || isLoading) ? '#e5e1d8' : '#7a8ea8' }}>
          {label}
        </div>
        {(model_name || detail) && (
          <div style={{ fontSize: '0.625rem', color: '#7a8ea8', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2, fontFamily: 'monospace', opacity: 0.7 }}>
            {model_name || detail}
          </div>
        )}
      </div>

      {/* Badge */}
      <div style={{ flexShrink: 0, fontSize: '0.5625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', color: m.color, background: m.bg, border: `1px solid ${m.ring}` }}>
        {m.label}
      </div>
    </motion.div>
  )
}

function SkeletonRow({ index }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.5 }}
      transition={{ delay: index * 0.05 }}
      style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px' }}>
      <div style={{ width: 20, height: 20, borderRadius: '50%', background: '#142d4f', flexShrink: 0 }} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ height: 10, background: '#142d4f', borderRadius: 4, width: 112 }} />
        <div style={{ height: 8, background: 'rgba(20,45,79,0.6)', borderRadius: 4, width: 176 }} />
      </div>
      <div style={{ width: 48, height: 16, background: '#142d4f', borderRadius: 4 }} />
    </motion.div>
  )
}
