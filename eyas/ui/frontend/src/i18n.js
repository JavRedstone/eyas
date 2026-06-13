const STRINGS = {
  English: {
    // App / layout
    'app.no_video':          'Load a sample or upload a video',
    'app.no_annotated':      'Annotated output will appear here after analysis',
    'app.uploading':         'Uploading video…',
    'app.upload_failed':     'Upload failed: {msg}',
    'app.ready':             'Ready: {name}',
    'app.loading_sample':    'Loading sample…',
    'app.sample':            'Sample: {name}',
    'app.no_video_selected': 'No video selected.',
    'app.starting_pipeline': 'Starting pipeline…',
    'app.close_clip':        '✕ close clip',
    'header.subtitle':       'AI Security Camera Agent',
    'panel.footage':         'Footage',
    'panel.event_clip':      'Event Clip',
    'panel.annotated':       'Annotated Video',
    'panel.preview':         'Preview',
    'panel.analysis':        'Analysis',
    'panel.all_cams':        'All Cameras',

    // Tabs
    'tabs.timeline': 'Event Timeline',
    'tabs.alerts':   'Summary & Alerts',
    'tabs.qa':       'Ask Footage',
    'tabs.metrics':  'Detection Metrics',
    'tabs.audio':    'Audio Report',
    'tabs.settings': 'Settings',

    // Sidebar
    'sidebar.sample_clips':  'Sample Clips',
    'sidebar.choose_sample': '— Choose a sample —',
    'sidebar.upload_video':  'Upload Video',
    'sidebar.drop_upload':   'Drop video or click to upload',
    'sidebar.no_samples':    'No sample clips found.',
    'sidebar.select_all_pending': 'Select all pending',

    // ClipViewSelector
    'clip_view.all': 'All',

    // Kind labels (event table chips)
    'kind.person':      'person',
    'kind.vehicle':     'vehicle',
    'kind.animal':      'animal',
    'kind.intrusion':   'intrusion',
    'kind.loitering':   'loitering',
    'kind.pickup':      'pickup',
    'kind.suspicious':  'suspicious',
    'kind.observation': 'observation',

    // Zone labels (mirror locale.py ZONES)
    'zone.entrance':    'Entrance',
    'zone.counter':     'Counter',
    'zone.back_door':   'Back Door',
    'zone.aisles':      'Aisles',
    'zone.review_area': 'Review Area',
    'zone.aisle_2':     'Aisle 2',
    'zone.aisle_3':     'Aisle 3',
    'zone.shelf_a':     'Shelf A',
    'zone.aisle1':      'Aisle 1',
    'zone.aisle2':      'Aisle 2',
    'zone.aisle3':      'Aisle 3',
    'zone.aisle4':      'Aisle 4',

    // AnalysisPanel
    'analysis.analyze':      'Analyze',
    'analysis.analyze_all':  'Analyze All ({count})',
    'analysis.processing':   'Processing…',
    'analysis.progress':     'Progress: {pct}%',
    'step.load_video':     'Load Video',
    'step.yolo':           'YOLO Tracking',
    'step.vlm':            'VLM Captioning',
    'step.llm_summarize':  'LLM Summary',

    // EventTimeline
    'timeline.title':        'Event Timeline',
    'timeline.x_label':      'seconds',
    'timeline.detected':     'Detected Events',
    'timeline.count':        '{count} events',
    'timeline.empty':        'No events yet. Run the pipeline first.',
    'timeline.col_num':      '#',
    'timeline.col_time':     'Time',
    'timeline.col_kind':     'Kind',
    'timeline.col_zone':     'Zone',
    'timeline.col_desc':     'Description',
    'timeline.load_clip':    'Load clip',
    'timeline.clip_btn':     'clip',
    'timeline.no_video':     'No video yet',
    'event.timestamp':       'Timestamp',
    'event.confidence':      'Confidence',
    'event.source':          'Source',
    'event.items':           'Items',

    // SummaryAlerts
    'summary.empty':        'No analysis yet. Run the pipeline first.',
    'summary.risk_level':   'Risk Level',
    'summary.translation':  'Translation: {ms}ms',
    'summary.flag_types':   'Flag Types',
    'summary.overnight':    'Overnight Summary',
    'summary.total':        'Total Summary',
    'summary.per_cam':      'Per Camera',
    'summary.no_summary':   'No summary available.',
    'summary.concerns':     'Potential Concerns ({count})',
    'summary.suspicious':   'Suspicious Clips ({count})',
    'risk.high':   'High Risk',
    'risk.medium': 'Medium Risk',
    'risk.low':    'Low Risk',
    'risk.none':   'No Risk',
    'flag.theft':        'Theft-related',
    'flag.entry_exit':   'Entry / Exit',
    'flag.loitering':    'Loitering / Stationary',
    'flag.interaction':  'Interaction',
    'flag.other':        'Other',

    // AskFootage
    'ask.title':       'Ask a Question About the Footage',
    'ask.hint':        'Try: "Were there any unusual events?" · "Which zone had the most activity?"',
    'ask.placeholder': 'Ask a question about the footage…',
    'ask.empty':       'No conversation yet. Run a pipeline first, then ask questions.',
    'ask.no_response': 'No response.',
    'ask.s1': 'What activity was detected?',
    'ask.s2': 'Were any suspicious events found?',
    'ask.s3': 'Which zones had the most activity?',
    'ask.s4': 'Summarize the key events',

    // AudioReport
    'audio.title':       'Spoken Security Report',
    'audio.help':        'Generates a spoken audio summary of the event log using the TTS model.',
    'audio.summarizing': 'Summarizing events…',
    'audio.synthesizing':'Synthesizing speech…',
    'audio.finishing':   'Finishing up…',
    'audio.no_audio':    'No audio returned.',
    'audio.generating':  'Generating…',
    'audio.generate':    'Generate Audio Report',

    // DetectionMetrics
    'metrics.total':     'Total Detections',
    'metrics.events':    'Events',
    'metrics.taken':     'Taken / Held',
    'metrics.zones':     'Zones Active',
    'metrics.avg':       'Avg / Zone',
    'metrics.zone_chart':'Zone Counts',
    'metrics.detections':'detections',
    'metrics.empty':     'No zone data yet. Run the pipeline first.',
    'metrics.frequency': 'Event Frequency Over Time',
    'metrics.events_tip':'events',

    // Session
    'session.event':         '1 event · {runs} video(s)',
    'session.events':        '{count} events · {runs} video(s)',
    'session.clear':         'Clear Session',
    'session.clear_confirm': 'Clear all session data?',
    'session.export':        'Export ZIP',
    'session.exporting':     'Exporting…',
    'session.empty':         'No session',

    // SettingsTab
    'settings.language':      'Language',
    'settings.language_help': 'Applies to pipeline output labels, summaries, and audio reports.',
    'settings.save':          'Save Language',
    'settings.saved':         'Language switched.',
  },

  '한국어': {
    // App / layout
    'app.no_video':          '샘플을 불러오거나 영상을 업로드하세요',
    'app.no_annotated':      '분석 후 주석 영상이 여기에 표시됩니다',
    'app.uploading':         '영상 업로드 중…',
    'app.upload_failed':     '업로드 실패: {msg}',
    'app.ready':             '준비됨: {name}',
    'app.loading_sample':    '샘플 불러오는 중…',
    'app.sample':            '샘플: {name}',
    'app.no_video_selected': '선택된 영상이 없습니다.',
    'app.starting_pipeline': '파이프라인 시작 중…',
    'app.close_clip':        '✕ 클립 닫기',
    'header.subtitle':       'AI 보안 카메라 에이전트',
    'panel.footage':         '영상',
    'panel.event_clip':      '이벤트 클립',
    'panel.annotated':       '주석 영상',
    'panel.preview':         '미리보기',
    'panel.analysis':        '분석',
    'panel.all_cams':        '전체 카메라',

    // Tabs
    'tabs.timeline': '이벤트 타임라인',
    'tabs.alerts':   '요약 및 알림',
    'tabs.qa':       '영상 질의',
    'tabs.metrics':  '탐지 지표',
    'tabs.audio':    '음성 보고서',
    'tabs.settings': '설정',

    // Sidebar
    'sidebar.sample_clips':  '샘플 클립',
    'sidebar.choose_sample': '— 샘플 선택 —',
    'sidebar.upload_video':  '영상 업로드',
    'sidebar.drop_upload':   '영상을 드래그하거나 클릭하여 업로드',
    'sidebar.no_samples':    '샘플 클립이 없습니다.',
    'sidebar.select_all_pending': '대기 중 전체 선택',

    // ClipViewSelector
    'clip_view.all': '전체',

    // Kind labels (event table chips)
    'kind.person':      '사람',
    'kind.vehicle':     '차량',
    'kind.animal':      '동물',
    'kind.intrusion':   '침입',
    'kind.loitering':   '배회',
    'kind.pickup':      '집기',
    'kind.suspicious':  '의심',
    'kind.observation': '관찰',

    // Zone labels (mirror locale.py ZONES)
    'zone.entrance':    '입구',
    'zone.counter':     '계산대',
    'zone.back_door':   '뒷문',
    'zone.aisles':      '통로',
    'zone.review_area': '검토 구역',
    'zone.aisle_2':     '통로 2',
    'zone.aisle_3':     '통로 3',
    'zone.shelf_a':     '선반 A',
    'zone.aisle1':      '통로 1',
    'zone.aisle2':      '통로 2',
    'zone.aisle3':      '통로 3',
    'zone.aisle4':      '통로 4',

    // AnalysisPanel
    'analysis.analyze':      '분석',
    'analysis.analyze_all':  '전체 분석 ({count})',
    'analysis.processing':   '처리 중…',
    'analysis.progress':     '진행률: {pct}%',
    'step.load_video':     '영상 불러오기',
    'step.yolo':           'YOLO 추적',
    'step.vlm':            'VLM 캡션',
    'step.llm_summarize':  'LLM 요약',

    // EventTimeline
    'timeline.title':     '이벤트 타임라인',
    'timeline.x_label':   '초',
    'timeline.detected':  '탐지된 이벤트',
    'timeline.count':     '{count} 이벤트',
    'timeline.empty':     '이벤트가 없습니다. 파이프라인을 먼저 실행하세요.',
    'timeline.col_num':   '#',
    'timeline.col_time':  '시간',
    'timeline.col_kind':  '종류',
    'timeline.col_zone':  '구역',
    'timeline.col_desc':  '설명',
    'timeline.load_clip': '클립 불러오기',
    'timeline.clip_btn':  '클립',
    'event.timestamp':    '타임스탬프',
    'event.confidence':   '신뢰도',
    'event.source':       '소스',
    'event.items':        '물품',
    'timeline.no_video':  '아직 영상 없음',

    // SummaryAlerts
    'summary.empty':      '분석 결과가 없습니다. 파이프라인을 먼저 실행하세요.',
    'summary.risk_level': '위험 수준',
    'summary.translation':'번역: {ms}ms',
    'summary.flag_types': '플래그 유형',
    'summary.overnight':  '야간 요약',
    'summary.total':      '전체 요약',
    'summary.per_cam':    '카메라별',
    'summary.no_summary': '요약이 없습니다.',
    'summary.concerns':   '잠재적 우려 사항 ({count})',
    'summary.suspicious': '의심 클립 ({count})',
    'risk.high':   '높은 위험',
    'risk.medium': '중간 위험',
    'risk.low':    '낮은 위험',
    'risk.none':   '위험 없음',
    'flag.theft':       '절도 관련',
    'flag.entry_exit':  '출입',
    'flag.loitering':   '배회 / 정체',
    'flag.interaction': '상호작용',
    'flag.other':       '기타',

    // AskFootage
    'ask.title':       '영상에 대해 질문하기',
    'ask.hint':        '예: "이상한 이벤트가 있었나요?" · "어느 구역에서 활동이 가장 많았나요?"',
    'ask.placeholder': '영상에 대해 질문하세요…',
    'ask.empty':       '대화가 없습니다. 파이프라인을 실행한 후 질문하세요.',
    'ask.no_response': '응답이 없습니다.',
    'ask.s1': '어떤 활동이 탐지되었나요?',
    'ask.s2': '의심스러운 이벤트가 발견되었나요?',
    'ask.s3': '어느 구역에서 활동이 가장 많았나요?',
    'ask.s4': '주요 이벤트를 요약해 주세요',

    // AudioReport
    'audio.title':        '음성 보안 보고서',
    'audio.help':         'TTS 모델을 사용하여 이벤트 로그의 음성 요약을 생성합니다.',
    'audio.summarizing':  '이벤트 요약 중…',
    'audio.synthesizing': '음성 합성 중…',
    'audio.finishing':    '마무리 중…',
    'audio.no_audio':     '오디오가 반환되지 않았습니다.',
    'audio.generating':   '생성 중…',
    'audio.generate':     '음성 보고서 생성',

    // DetectionMetrics
    'metrics.total':     '전체 탐지',
    'metrics.events':    '이벤트',
    'metrics.taken':     '탈취 / 소지',
    'metrics.zones':     '활성 구역',
    'metrics.avg':       '구역 평균',
    'metrics.zone_chart':'구역별 탐지 수',
    'metrics.detections':'탐지',
    'metrics.empty':     '구역 데이터가 없습니다. 파이프라인을 먼저 실행하세요.',
    'metrics.frequency': '시간대별 이벤트 빈도',
    'metrics.events_tip':'이벤트',

    // Session
    'session.event':         '{count}개 이벤트 · {runs}개 영상',
    'session.events':        '{count}개 이벤트 · {runs}개 영상',
    'session.clear':         '세션 초기화',
    'session.clear_confirm': '모든 세션 데이터를 초기화하시겠습니까?',
    'session.export':        'ZIP 내보내기',
    'session.exporting':     '내보내는 중…',
    'session.empty':         '세션 없음',

    // SettingsTab
    'settings.language':      '언어',
    'settings.language_help': '파이프라인 출력 레이블, 요약 및 음성 보고서에 적용됩니다.',
    'settings.save':          '언어 저장',
    'settings.saved':         '언어가 변경되었습니다.',
  },
}

export function t(language, key, vars = {}) {
  const map = STRINGS[language] || STRINGS.English
  let text = map[key] ?? STRINGS.English[key] ?? key
  for (const [k, v] of Object.entries(vars)) {
    text = text.replace(`{${k}}`, v)
  }
  return text
}
