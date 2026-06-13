import { motion } from 'framer-motion'

// Frontend-only strings for the splash screen (status badges + labels).
// Model names and labels come translated from the backend via poll_splash.
const STRINGS = {
  English: {
    tagline:      'AI Security Camera Agent',
    initializing: 'Initializing',
    ready:        'ready',
    error:        'error',
    skipped:      'skipped',
    loading:      'loading',
    pending:      'pending',
    waiting:      'waiting',
    on_demand:    'on demand',
  },
  '한국어': {
    tagline:      'AI 보안 카메라 에이전트',
    initializing: '초기화 중',
    ready:        '준비됨',
    error:        '오류',
    skipped:      '사용 불가',
    loading:      '로딩 중',
    pending:      '대기 중',
    waiting:      '대기 중',
    on_demand:    '요청 시 로드',
  },
}

function t(language, key) {
  return (STRINGS[language] || STRINGS.English)[key] || key
}

export default function Splash({ items = [], pct = 0, language = 'English', colorMode = 'dark' }) {
  const dark   = colorMode === 'dark'
  const colors = {
    bg:       dark ? '#0b1929'          : '#fef9e7',
    surface:  dark ? '#0f2338'          : '#ffffff',
    border:   dark ? 'rgba(247,208,70,0.20)' : 'rgba(21,101,192,0.20)',
    ring:     dark ? 'rgba(247,208,70,0.40)' : 'rgba(21,101,192,0.40)',
    primary:  dark ? '#f7d046'          : '#1565C0',
    text:     dark ? '#e5e1d8'          : '#0d1b2a',
    muted:    dark ? '#7a8ea8'          : '#4a5e78',
    track:    dark ? '#142d4f'          : '#e8d88a',
    skeleton: dark ? '#142d4f'          : '#e0d070',
    skeletonFaint: dark ? 'rgba(20,45,79,0.6)' : 'rgba(200,180,60,0.4)',
    shimmer:  dark ? 'rgba(247,208,70,0.07)' : 'rgba(21,101,192,0.07)',
  }

  const hasItems = items.length > 0

  return (
    <motion.div
      style={{ position: 'fixed', inset: 0, background: colors.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1300 }}
      exit={{ opacity: 0, scale: 1.01 }} transition={{ duration: 0.35 }}>
      <div style={{ width: '100%', maxWidth: 448, padding: '0 24px' }}>

        {/* Wordmark */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 40 }}>
          <div style={{ position: 'relative', flexShrink: 0 }}>
            <img src={`${import.meta.env.BASE_URL}logo.png`} alt="Eyas"
              style={{ width: 56, height: 56, objectFit: 'contain', display: 'block' }} />
            <motion.div style={{ position: 'absolute', inset: -4, borderRadius: 16, border: `1px solid ${colors.ring}`, pointerEvents: 'none' }}
              animate={{ opacity: [0.3, 0.8, 0.3] }} transition={{ duration: 2.2, repeat: Infinity }} />
          </div>
          <div>
            <div style={{ fontSize: '1.4rem', fontWeight: 700, letterSpacing: '-0.01em', color: colors.text }}>Eyas</div>
            <div style={{ fontSize: '0.75rem', color: colors.muted }}>{t(language, 'tagline')}</div>
          </div>
        </div>

        {/* Model rows */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 24 }}>
          {hasItems
            ? items.map((item, i) => <ModelRow key={item.label || i} item={item} index={i} colors={colors} language={language} />)
            : [0,1,2,3,4].map(i => <SkeletonRow key={i} index={i} colors={colors} />)
          }
        </div>

        {/* Progress bar */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '0.625rem', color: colors.muted, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.1em' }}>
              {t(language, 'initializing')}
            </span>
            <span style={{ fontSize: '0.625rem', color: colors.muted, fontFamily: 'monospace' }}>{pct}%</span>
          </div>
          <div style={{ height: 1, background: colors.track, borderRadius: 9999, overflow: 'hidden' }}>
            <motion.div style={{ height: '100%', background: colors.primary, borderRadius: 9999 }}
              animate={{ width: `${Math.max(pct, hasItems ? 4 : 12)}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }} />
          </div>
        </div>

      </div>
    </motion.div>
  )
}

function ModelRow({ item, index, colors, language }) {
  const { status, label, detail, model_name } = item

  const STATUS_META = {
    ready:     { color: '#34D399', bg: '#34D39912', ring: '#34D39933' },
    on_demand: { color: '#60A5FA', bg: '#60A5FA12', ring: '#60A5FA33' },
    error:     { color: '#F87171', bg: '#F8717112', ring: '#F8717133' },
    skipped:   { color: colors.muted, bg: `${colors.muted}12`, ring: `${colors.muted}33` },
    loading:   { color: colors.primary, bg: `${colors.primary}12`, ring: `${colors.primary}33` },
    pending:   { color: colors.muted,   bg: 'transparent',         ring: colors.muted },
  }

  const m = STATUS_META[status] || STATUS_META.pending
  const isLoading   = status === 'loading'
  const isDone      = status === 'ready' || status === 'skipped' || status === 'on_demand'
  const isError     = status === 'error'

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: index * 0.06, duration: 0.22 }}
      style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px', borderRadius: 8, overflow: 'hidden', background: status !== 'pending' ? m.bg : 'transparent' }}>

      {isLoading && (
        <motion.div style={{ position: 'absolute', inset: 0, pointerEvents: 'none', background: `linear-gradient(90deg, transparent, ${colors.shimmer}, transparent)` }}
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
        <div style={{ fontSize: '0.75rem', fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: (isDone || isLoading) ? colors.text : colors.muted }}>
          {label}
        </div>
        {(model_name || detail) && (
          <div style={{ fontSize: '0.625rem', color: colors.muted, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginTop: 2, fontFamily: 'monospace', opacity: 0.7 }}>
            {model_name || detail}
          </div>
        )}
      </div>

      {/* Status badge */}
      <div style={{ flexShrink: 0, fontSize: '0.5625rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.1em', padding: '2px 6px', borderRadius: 4, fontFamily: 'monospace', color: m.color, background: m.bg, border: `1px solid ${m.ring}` }}>
        {t(language, status) || status}
      </div>
    </motion.div>
  )
}

function SkeletonRow({ index, colors }) {
  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 0.5 }}
      transition={{ delay: index * 0.05 }}
      style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 12px' }}>
      <div style={{ width: 20, height: 20, borderRadius: '50%', background: colors.skeleton, flexShrink: 0 }} />
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ height: 10, background: colors.skeleton, borderRadius: 4, width: 112 }} />
        <div style={{ height: 8, background: colors.skeletonFaint, borderRadius: 4, width: 176 }} />
      </div>
      <div style={{ width: 48, height: 16, background: colors.skeleton, borderRadius: 4 }} />
    </motion.div>
  )
}
