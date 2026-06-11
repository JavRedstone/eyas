import { useState, useRef, useEffect } from 'react'
import { Send, Trash2 } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

export default function AskFootage({ client, events, chatHistory, setChatHistory }) {
  const [query, setQuery]   = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef()
  const suggestions = [
    'What activity was detected?',
    'Were any suspicious events found?',
    'Which zones had the most activity?',
    'Summarize the key events',
  ]

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatHistory])

  async function ask() {
    const q = query.trim()
    if (!q || !client || loading) return
    setQuery('')
    const newHistory = [...chatHistory, { role: 'user', text: q }]
    setChatHistory(newHistory)
    setLoading(true)
    try {
      const r = await client.predict('/ask_footage', {
        message: q,
        history: newHistory.map(h => [h.role === 'user' ? h.text : null, h.role === 'assistant' ? h.text : null]),
        events,
      })
      const replyHistory = r.data[0] || []
      const answer = extractAssistantReply(replyHistory)
      setChatHistory(h => [...h, { role: 'assistant', text: answer || 'No response.' }])
    } catch (e) {
      setChatHistory(h => [...h, { role: 'assistant', text: `Error: ${e.message}` }])
    } finally { setLoading(false) }
  }

  function handleKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask() } }

  return (
    <div className="flex flex-col" style={{ height: 420 }}>
      <p className="section-label mb-3">Ask a Question About the Footage</p>
      <p className="text-xs text-muted mb-3">
        Try: "Were there any unusual events?" · "Which zone had the most activity?"
      </p>

      <div className="mb-3 flex flex-wrap gap-2">
        {suggestions.map(suggestion => (
          <button
            key={suggestion}
            type="button"
            onClick={() => setQuery(suggestion)}
            className="rounded-full border border-border bg-surface px-3 py-1 text-xs text-text transition-colors hover:border-accent/50 hover:bg-accent/5"
            disabled={loading}
          >
            {suggestion}
          </button>
        ))}
      </div>

      {/* Chat area */}
      <div className="flex-1 overflow-y-auto space-y-3 mb-3 min-h-0">
        {chatHistory.length === 0 && (
          <div className="text-xs text-muted text-center mt-8">
            No conversation yet. Run a pipeline first, then ask questions.
          </div>
        )}
        <AnimatePresence initial={false}>
          {chatHistory.map((msg, i) => (
            <motion.div key={i}
              initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-xs px-3 py-2 rounded-xl text-xs leading-relaxed
                ${msg.role === 'user'
                  ? 'bg-accent text-white rounded-br-sm'
                  : 'bg-surface border border-border text-text rounded-bl-sm'}`}>
                {msg.text}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        {loading && (
          <div className="flex justify-start">
            <div className="bg-surface border border-border rounded-xl rounded-bl-sm px-3 py-2">
              <div className="flex gap-1">
                {[0, 1, 2].map(i => (
                  <motion.div key={i} className="w-1.5 h-1.5 rounded-full bg-muted"
                    animate={{ y: [0, -4, 0] }} transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.15 }} />
                ))}
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input row */}
      <div className="flex gap-2 shrink-0">
        <input className="input text-xs" value={query}
          onChange={e => setQuery(e.target.value)} onKeyDown={handleKey}
          placeholder="Ask a question about the footage…" />
        <button onClick={ask} disabled={!query.trim() || loading}
          className="btn btn-primary px-3 shrink-0 disabled:opacity-40">
          <Send size={14} />
        </button>
        {chatHistory.length > 0 && (
          <button onClick={() => setChatHistory([])} className="btn btn-ghost px-2 shrink-0">
            <Trash2 size={14} />
          </button>
        )}
      </div>
    </div>
  )
}

function extractAssistantReply(replyHistory) {
  if (!Array.isArray(replyHistory) || replyHistory.length === 0) return ''
  for (let i = replyHistory.length - 1; i >= 0; i--) {
    const msg = replyHistory[i]
    if (!msg || msg.role !== 'assistant') continue
    return msg.text ?? msg.content ?? ''
  }
  const last = replyHistory[replyHistory.length - 1]
  return last?.text ?? last?.content ?? ''
}
