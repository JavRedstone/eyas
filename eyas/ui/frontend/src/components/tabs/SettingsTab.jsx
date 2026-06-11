import { useState } from 'react'
import { Save, Globe } from 'lucide-react'

const LANGUAGES = ['English', '한국어']

export default function SettingsTab({ client, language, setLanguage }) {
  const [local, setLocal]   = useState(language)
  const [status, setStatus] = useState('')

  async function save() {
    if (!client) return
    try {
      await client.predict('/save_language', { language: local })
      setLanguage(local)
      setStatus('Saved. Restart the app for full effect.')
    } catch (e) { setStatus(`Error: ${e.message}`) }
  }

  return (
    <div className="space-y-6 max-w-sm">
      <div>
        <p className="section-label mb-3">Language</p>
        <p className="text-xs text-muted mb-4">Changes take full effect after restarting the app.</p>
        <div className="space-y-2">
          {LANGUAGES.map(lang => (
            <button key={lang}
              onClick={() => setLocal(lang)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border text-sm transition-all
                ${local === lang
                  ? 'border-accent/60 bg-accent/10 text-text'
                  : 'border-border bg-surface text-muted hover:border-border/80 hover:text-text'}`}>
              <Globe size={14} className={local === lang ? 'text-accent' : 'text-muted'} />
              {lang}
              {local === lang && <div className="ml-auto w-2 h-2 rounded-full bg-accent" />}
            </button>
          ))}
        </div>
      </div>

      <button onClick={save} className="btn btn-primary">
        <Save size={14} /> Save Language
      </button>

      {status && <p className="text-xs text-muted">{status}</p>}
    </div>
  )
}
