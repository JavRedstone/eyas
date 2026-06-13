import { t } from './i18n.js'

export function displayKind(kind, language) {
  const key = `kind.${String(kind).toLowerCase()}`
  const v = t(language, key)
  const result = v === key ? kind : v
  // #region agent log
  fetch('http://127.0.0.1:7326/ingest/2fd361a8-d87f-4a82-9c25-56b1d25d3900',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'cf95a6'},body:JSON.stringify({sessionId:'cf95a6',location:'display.js:displayKind',message:'kind display',data:{kind,key,language,result,usedI18n:v!==key},timestamp:Date.now(),hypothesisId:'C'})}).catch(()=>{});
  // #endregion
  return result
}

export function displayZone(zone, language, koCache = {}, ev = null) {
  if (!zone) return '—'
  if (language === '한국어' && ev?.zone_ko) {
    // #region agent log
    fetch('http://127.0.0.1:7326/ingest/2fd361a8-d87f-4a82-9c25-56b1d25d3900',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'cf95a6'},body:JSON.stringify({sessionId:'cf95a6',location:'display.js:displayZone',message:'zone from event zone_ko',data:{zone,result:ev.zone_ko,source:'zone_ko'},timestamp:Date.now(),hypothesisId:'B'})}).catch(()=>{});
    // #endregion
    return ev.zone_ko
  }
  const norm = zone.toLowerCase().replace(/-/g, '_')
  const key = `zone.${norm}`
  const v = t(language, key)
  if (v !== key) {
    // #region agent log
    fetch('http://127.0.0.1:7326/ingest/2fd361a8-d87f-4a82-9c25-56b1d25d3900',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'cf95a6'},body:JSON.stringify({sessionId:'cf95a6',location:'display.js:displayZone',message:'zone from i18n catalog',data:{zone,key,result:v,source:'i18n'},timestamp:Date.now(),hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    return v
  }
  if (language === '한국어' && koCache[zone]) {
    // #region agent log
    fetch('http://127.0.0.1:7326/ingest/2fd361a8-d87f-4a82-9c25-56b1d25d3900',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'cf95a6'},body:JSON.stringify({sessionId:'cf95a6',location:'display.js:displayZone',message:'zone from koCache',data:{zone,result:koCache[zone],source:'zoneKoCache'},timestamp:Date.now(),hypothesisId:'A'})}).catch(()=>{});
    // #endregion
    return koCache[zone]
  }
  // #region agent log
  fetch('http://127.0.0.1:7326/ingest/2fd361a8-d87f-4a82-9c25-56b1d25d3900',{method:'POST',headers:{'Content-Type':'application/json','X-Debug-Session-Id':'cf95a6'},body:JSON.stringify({sessionId:'cf95a6',location:'display.js:displayZone',message:'zone passthrough',data:{zone,result:zone,source:'raw'},timestamp:Date.now(),hypothesisId:'B'})}).catch(()=>{});
  // #endregion
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
