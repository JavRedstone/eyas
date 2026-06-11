import { useState, useEffect, useCallback, useRef } from 'react'
import { Client, prepare_files } from '@gradio/client'
import { AnimatePresence, motion } from 'framer-motion'
import Splash from './components/Splash.jsx'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
import AnalysisPanel from './components/AnalysisPanel.jsx'
import TabNav from './components/TabNav.jsx'
import EventTimeline from './components/tabs/EventTimeline.jsx'
import SummaryAlerts from './components/tabs/SummaryAlerts.jsx'
import AskFootage from './components/tabs/AskFootage.jsx'
import DetectionMetrics from './components/tabs/DetectionMetrics.jsx'
import AudioReport from './components/tabs/AudioReport.jsx'
import ClipLibrary from './components/tabs/ClipLibrary.jsx'
import SettingsTab from './components/tabs/SettingsTab.jsx'

const TABS = [
  { id: 'timeline',  label: 'Event Timeline',   icon: 'Activity'      },
  { id: 'alerts',    label: 'Summary & Alerts',  icon: 'AlertTriangle' },
  { id: 'qa',        label: 'Ask Footage',        icon: 'MessageSquare' },
  { id: 'metrics',   label: 'Detection Metrics',  icon: 'BarChart2'     },
  { id: 'audio',     label: 'Audio Report',       icon: 'Volume2'       },
  { id: 'library',   label: 'Clip Library',       icon: 'Film'          },
  { id: 'settings',  label: 'Settings',           icon: 'Settings'      },
]

export default function App() {
  const [client, setClient]                 = useState(null)
  const [splashItems, setSplashItems]       = useState([])
  const [splashPct, setSplashPct]           = useState(0)
  const [splashDone, setSplashDone]         = useState(false)
  const [activeTab, setActiveTab]           = useState('timeline')
  const [videoFile, setVideoFile]           = useState(null)
  const [videoRef, setVideoRef]             = useState(null)
  const [uploadStatus, setUploadStatus]     = useState('')
  const [analyzing, setAnalyzing]           = useState(false)
  const [statusMsg, setStatusMsg]           = useState('')
  const [pipelineSteps, setPipelineSteps]   = useState([])
  const [pipelineProgress, setPipelineProgress] = useState(0)
  const [annotatedVideo, setAnnotatedVideo] = useState(null)
  const [events, setEvents]                 = useState([])
  const [outputDir, setOutputDir]           = useState('')
  const [summary, setSummary]               = useState(null)
  const [chatHistory, setChatHistory]       = useState([])
  const [language, setLanguage]             = useState('English')
  const [samples, setSamples]               = useState([])
  const [videoPreviewSrc, setVideoPreviewSrc] = useState('')
  const previewUrlRef = useRef('')
  const annotatedVideoElRef = useRef(null)
  const splitContainerRef   = useRef(null)
  const isDragging          = useRef(false)
  const [splitPct, setSplitPct] = useState(50)

  const seekAnnotatedVideo = useCallback((t) => {
    const el = annotatedVideoElRef.current
    if (!el) return
    el.currentTime = t
    if (el.paused) el.play().catch(() => {})
  }, [])

  const onDragHandleMouseDown = useCallback((e) => {
    e.preventDefault()
    isDragging.current = true
    document.body.style.cursor = 'col-resize'
    document.body.style.userSelect = 'none'

    function onMove(e) {
      if (!isDragging.current || !splitContainerRef.current) return
      const rect = splitContainerRef.current.getBoundingClientRect()
      const pct  = ((e.clientX - rect.left) / rect.width) * 100
      setSplitPct(Math.max(25, Math.min(75, pct)))
    }
    function onUp() {
      isDragging.current = false
      document.body.style.cursor = ''
      document.body.style.userSelect = ''
      window.removeEventListener('mousemove', onMove)
      window.removeEventListener('mouseup', onUp)
    }
    window.addEventListener('mousemove', onMove)
    window.addEventListener('mouseup', onUp)
  }, [])

  function getVideoPath(fileRef) {
    if (!fileRef) return null
    if (typeof fileRef === 'string') {
      const prefix = '/gradio_api/file='
      return fileRef.startsWith(prefix) ? decodeURIComponent(fileRef.slice(prefix.length)) : fileRef
    }
    if (fileRef.path) return fileRef.path
    if (fileRef.url) {
      const prefix = '/gradio_api/file='
      return fileRef.url.startsWith(prefix) ? decodeURIComponent(fileRef.url.slice(prefix.length)) : null
    }
    return null
  }

  function getPreviewSrc(fileRef) {
    if (!fileRef) return null
    if (typeof fileRef === 'string') {
      if (fileRef.startsWith('http') || fileRef.startsWith('/gradio_api/file=')) return fileRef
      return `/gradio_api/file=${fileRef}`
    }
    if (fileRef.url) return fileRef.url
    if (fileRef.path) return `/gradio_api/file=${fileRef.path}`
    return null
  }

  function setPreviewSource(nextSrc) {
    if (previewUrlRef.current && previewUrlRef.current.startsWith('blob:')) {
      URL.revokeObjectURL(previewUrlRef.current)
    }
    previewUrlRef.current = nextSrc || ''
    setVideoPreviewSrc(nextSrc || '')
  }

  const pollSplash = useCallback(async (c) => {
    for (let i = 0; i < 60; i++) {
      try {
        const r = await c.predict('/poll_splash', {})
        const { states, done, progress_pct } = r.data[0]
        setSplashItems(states || [])
        setSplashPct(progress_pct ?? 0)
        if (done) { setSplashDone(true); return }
      } catch {
        return
      }
      await new Promise(res => setTimeout(res, 800))
    }
    setSplashDone(true)
  }, [])

  const loadSamples = useCallback(async (c) => {
    try {
      const r = await c.predict('/get_samples', {})
      setSamples(r.data[0] || [])
    } catch {
      return
    }
  }, [])

  useEffect(() => {
    Client.connect(window.location.origin)
      .then(c => {
        setClient(c)
        pollSplash(c)
        loadSamples(c)
      })
      .catch(() => null)

    return () => {
      if (previewUrlRef.current && previewUrlRef.current.startsWith('blob:')) {
        URL.revokeObjectURL(previewUrlRef.current)
      }
    }
  }, [loadSamples, pollSplash])

  const handleFileSelect = useCallback((file) => {
    setVideoFile(file)
    setVideoRef(null)
    setPreviewSource(URL.createObjectURL(file))
    setUploadStatus(`Ready: ${file.name}`)
  }, [])

  const handleLoadSample = useCallback(async (sampleName) => {
    if (!client || !sampleName) return
    try {
      setUploadStatus('Loading sample…')
      const r = await client.predict('/load_sample', { name: sampleName })
      setVideoRef(r.data[0])
      setVideoFile(null)
      setPreviewSource(getPreviewSrc(r.data[0]))
      setUploadStatus(`Sample: ${sampleName}`)
    } catch (e) { setUploadStatus(`Error: ${e.message}`) }
  }, [client])

  const handleAnalyze = useCallback(async () => {
    if (!client) return
    let gradioFile = getVideoPath(videoRef)

    if (!gradioFile && videoFile) {
      setStatusMsg('Uploading video…')
      try {
        const up = await client.upload(await prepare_files([videoFile]))
        gradioFile = getVideoPath(up[0])
        setVideoRef(up[0])
        setPreviewSource(getPreviewSrc(up[0]))
      } catch (e) { setStatusMsg(`Upload failed: ${e.message}`); return }
    }
    if (!gradioFile) { setStatusMsg('No video selected.'); return }

    setAnalyzing(true)
    setStatusMsg('Starting pipeline…')
    setPipelineSteps([])
    setPipelineProgress(0)
    setAnnotatedVideo(null)
    setEvents([])
    setSummary(null)

    try {
      const sub = client.submit('/run_pipeline', { video_path: gradioFile })
      for await (const msg of sub) {
        if (msg.type !== 'data') continue
        const u = msg.data[0]
        if (!u) continue
        if (u.status_msg || u.status) setStatusMsg(u.status_msg || u.status)
        if (u.pipeline_steps || u.steps) setPipelineSteps(u.pipeline_steps || u.steps)
        if (typeof u.progress_pct === 'number') setPipelineProgress(u.progress_pct)
        if (u.events?.length)        setEvents(u.events)
        if (u.output_dir)            setOutputDir(u.output_dir)
        if (u.annotated_video_path)  setAnnotatedVideo(u.annotated_video_path)
        if (u.type === 'final')    { setSummary(u); setPipelineProgress(100) }
      }
    } catch (e) { setStatusMsg(`Error: ${e.message}`) }
    finally      { setAnalyzing(false) }
  }, [client, videoFile, videoRef])

  const tabProps = { client, events, outputDir, summary, chatHistory, setChatHistory, language, setLanguage, onSeekVideo: seekAnnotatedVideo }

  return (
    <AnimatePresence mode="wait">
      {!splashDone ? (
        <Splash key="splash" items={splashItems} pct={splashPct} />
      ) : (
        <motion.div key="app" className="min-h-screen flex flex-col"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5 }}>

          <Header language={language} />

          {/* Resizable two-panel layout */}
          <div ref={splitContainerRef} className="flex p-4 flex-1 min-h-0 overflow-hidden">

            {/* Left: footage controls + video */}
            <div style={{ width: `${splitPct}%` }} className="flex flex-col gap-3 min-h-0 min-w-0">
              <Sidebar
                samples={samples} videoFile={videoFile} videoRef={videoRef}
                uploadStatus={uploadStatus}
                onFileSelect={handleFileSelect} onLoadSample={handleLoadSample}
              />
              <div className="card flex-1 flex flex-col min-h-0">
                <div className="panel-header">
                  <div className="w-1.5 h-1.5 rounded-full bg-accent" />
                  <span className="text-xs font-semibold text-text">
                    {annotatedVideo ? 'Annotated Video' : 'Preview'}
                  </span>
                </div>
                <div className="flex-1 flex items-center justify-center bg-black rounded-b-xl overflow-hidden min-h-0">
                  {annotatedVideo ? (
                    <video
                      ref={annotatedVideoElRef}
                      src={annotatedVideo.startsWith('/gradio_api/file=') ? annotatedVideo : `/gradio_api/file=${annotatedVideo}`}
                      controls
                      className="w-full h-full object-contain"
                    />
                  ) : videoPreviewSrc ? (
                    <video
                      src={videoPreviewSrc}
                      controls muted
                      className="w-full h-full object-contain"
                    />
                  ) : (
                    <div className="text-center text-muted p-8">
                      <div className="text-3xl mb-2 opacity-20">▶</div>
                      <p className="text-xs">Load a sample or upload a video</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Drag handle */}
            <div
              className="w-2 shrink-0 mx-1.5 flex items-center justify-center cursor-col-resize group"
              onMouseDown={onDragHandleMouseDown}>
              <div className="w-0.5 h-full rounded-full bg-border group-hover:bg-accent/60 transition-colors" />
            </div>

            {/* Right: analysis + tabs */}
            <div style={{ width: `${100 - splitPct}%` }} className="flex flex-col gap-3 min-h-0 min-w-0">
              <AnalysisPanel
                analyzing={analyzing} statusMsg={statusMsg}
                pipelineSteps={pipelineSteps} pipelineProgress={pipelineProgress}
                onAnalyze={handleAnalyze}
              />
              <div className="card flex-1 flex flex-col min-h-0">
                <TabNav tabs={TABS} activeTab={activeTab} setActiveTab={setActiveTab} />
                <div className="flex-1 overflow-y-auto p-5 min-h-0">
                  <AnimatePresence mode="wait">
                    <motion.div key={activeTab}
                      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.15 }}>
                      {activeTab === 'timeline' && <EventTimeline  {...tabProps} />}
                      {activeTab === 'alerts'   && <SummaryAlerts  {...tabProps} />}
                      {activeTab === 'qa'       && <AskFootage     {...tabProps} />}
                      {activeTab === 'metrics'  && <DetectionMetrics {...tabProps} />}
                      {activeTab === 'audio'    && <AudioReport    {...tabProps} />}
                      {activeTab === 'library'  && <ClipLibrary    {...tabProps} />}
                      {activeTab === 'settings' && <SettingsTab    {...tabProps} />}
                    </motion.div>
                  </AnimatePresence>
                </div>
              </div>
            </div>

          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
