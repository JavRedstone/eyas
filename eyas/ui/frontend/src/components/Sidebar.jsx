import { useRef } from 'react'
import { Upload } from 'lucide-react'
import { motion } from 'framer-motion'

export default function Sidebar({ samples, videoFile, videoRef, uploadStatus, onFileSelect, onLoadSample }) {
  const inputRef   = useRef()
  const hasVideo   = videoFile || videoRef

  function handleDrop(e) {
    e.preventDefault()
    const f = e.dataTransfer?.files?.[0]
    if (f && f.type.startsWith('video/')) onFileSelect(f)
  }

  function handleChange(e) {
    if (e.target.files[0]) onFileSelect(e.target.files[0])
  }

  return (
    <div className="flex flex-col gap-3">
      {/* Sample clips */}
      <div className="card">
        <div className="panel-header">
          <div className="w-1.5 h-1.5 rounded-full bg-accent" />
          <span className="text-xs font-semibold text-text">Footage</span>
        </div>
        <div className="p-3 space-y-3">
          {samples.length > 0 ? (
            <>
              <div>
                <div className="section-label mb-2 text-[10px]">Sample Clips</div>
                <select className="input text-xs"
                  onChange={e => onLoadSample(e.target.value)}
                  defaultValue="">
                  <option value="">— Choose a sample —</option>
                  {samples.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
            </>
          ) : (
            <p className="text-xs text-muted">No sample clips found.</p>
          )}

          {/* Upload zone */}
          <div>
            <div className="section-label mb-2 text-[10px]">Upload Video</div>
            <motion.div
              className={`relative border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors
                ${hasVideo ? 'border-accent/40 bg-accent/5' : 'border-border hover:border-accent/40 hover:bg-surface/60'}`}
              onDragOver={e => e.preventDefault()}
              onDrop={handleDrop}
              onClick={() => inputRef.current?.click()}
              whileHover={{ scale: 1.01 }}
              whileTap={{ scale: 0.99 }}>
              <input ref={inputRef} type="file" accept="video/*" className="hidden" onChange={handleChange} />
              <Upload className="mx-auto text-muted mb-2" size={20} />
              <p className="text-xs text-muted">
                {videoFile ? videoFile.name : 'Drop video or click to upload'}
              </p>
            </motion.div>
          </div>

          {uploadStatus && (
            <p className="text-xs text-muted truncate">{uploadStatus}</p>
          )}
        </div>
      </div>
    </div>
  )
}
