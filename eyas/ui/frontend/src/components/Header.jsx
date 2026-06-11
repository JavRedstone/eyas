export default function Header({ language }) {
  return (
    <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface/60 backdrop-blur-sm sticky top-0 z-10">
      <div className="flex items-center gap-3">
        <div className="w-7 h-7 rounded-lg bg-accent/10 border border-accent/30 flex items-center justify-center">
          <div className="w-2 h-2 rounded-full bg-accent" />
        </div>
        <span className="font-semibold text-text tracking-tight">Eyas</span>
        <span className="text-muted text-xs hidden sm:block">AI Security Camera Agent</span>
      </div>

      <div className="flex items-center gap-3">
        <div className="text-xs text-muted font-mono">{language}</div>
      </div>
    </header>
  )
}
