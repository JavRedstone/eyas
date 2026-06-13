import { t } from './i18n.js'

export function displayKind(kind, language) {
  const key = `kind.${String(kind).toLowerCase()}`
  const v = t(language, key)
  return v === key ? kind : v
}

export function displayZone(zone, language, koCache = {}, ev = null) {
  if (!zone) return '—'
  if (language === '한국어' && ev?.zone_ko) return ev.zone_ko
  const norm = zone.toLowerCase().replace(/-/g, '_')
  const key = `zone.${norm}`
  const v = t(language, key)
  if (v !== key) return v
  if (language === '한국어' && koCache[zone]) return koCache[zone]
  return zone
}

export function displayDescription(ev, language) {
  const raw = ev.label ?? ev.description ?? '—'
  if (language === '한국어' && ev.description_ko) return ev.description_ko
  return raw
}

export function displaySummaryText(summary, language) {
  if (!summary) return ''
  const raw = summary.summary ?? summary.overnight_summary ?? ''
  if (language === '한국어' && summary.summary_ko) return summary.summary_ko
  return raw
}

export function displayChatText(msg, language) {
  const raw = msg.text ?? msg.content ?? ''
  if (language === '한국어' && msg.role === 'assistant' && msg.text_ko) return msg.text_ko
  return raw
}
