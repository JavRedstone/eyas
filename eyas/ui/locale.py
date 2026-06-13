"""Bilingual UI strings and display helpers (English / Korean)."""

from __future__ import annotations

from typing import Any

SUPPORTED_LOCALES = ("en", "ko")
DEFAULT_LOCALE = "en"

TTS_LANG = {"en": "English", "ko": "Korean"}
TRANSLATE_LANG = TTS_LANG

LANGUAGE_LABELS = {"en": "English", "ko": "한국어"}
LANGUAGE_KEY = {v: k for k, v in LANGUAGE_LABELS.items()}

PIPELINE_STEP_IDS = ("load_video", "yolo", "vlm", "llm_summarize")

# Canonical zone keys → localized labels
ZONES: dict[str, dict[str, str]] = {
    "en": {
        "entrance": "Entrance",
        "counter": "Counter",
        "back_door": "Back Door",
        "aisles": "Aisles",
        "review_area": "Review Area",
        "aisle_2": "Aisle 2",
        "aisle_3": "Aisle 3",
        "shelf_a": "Shelf A",
        "aisle1": "Aisle 1",
        "aisle2": "Aisle 2",
        "aisle3": "Aisle 3",
        "aisle4": "Aisle 4",
        "cam1": "Cam 1",
        "cam2": "Cam 2",
        "cam3": "Cam 3",
        "cam4": "Cam 4",
    },
    "ko": {
        "entrance": "입구",
        "counter": "계산대",
        "back_door": "뒷문",
        "aisles": "통로",
        "review_area": "검토 구역",
        "aisle_2": "통로 2",
        "aisle_3": "통로 3",
        "shelf_a": "선반 A",
        "aisle1": "통로 1",
        "aisle2": "통로 2",
        "aisle3": "통로 3",
        "aisle4": "통로 4",
        "cam1": "카메라 1",
        "cam2": "카메라 2",
        "cam3": "카메라 3",
        "cam4": "카메라 4",
    },
}

ACTIVITIES: dict[str, dict[str, str]] = {
    "en": {
        "pickup": "pickup",
        "entry": "entry",
        "dwell": "dwell",
        "exit": "exit",
        "concealment": "concealment",
    },
    "ko": {
        "pickup": "집기",
        "entry": "입장",
        "dwell": "체류",
        "exit": "퇴장",
        "concealment": "은닉",
    },
}

EVENT_TYPES: dict[str, dict[str, str]] = {
    "en": {"pickup": "pickup", "observation": "observation"},
    "ko": {"pickup": "집기", "observation": "관찰"},
}

RISK: dict[str, dict[str, str]] = {
    "en": {"none": "none", "low": "low", "medium": "medium", "high": "high"},
    "ko": {"none": "없음", "low": "낮음", "medium": "중간", "high": "높음"},
}

STORAGE_SOURCE: dict[str, dict[str, str]] = {
    "en": {"upload": "upload", "stream": "stream"},
    "ko": {"upload": "업로드", "stream": "스트림"},
}

MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "app.title": "AI Security Camera Agent",
        "header.tagline": "AI Security Camera Agent",
        "header.subtitle": (
            "Offline AI-powered CCTV analysis — structured event log, "
            "security summaries & natural-language queries."
        ),
        "header.footage": "Footage",
        "header.analysis": "Analysis",
        "badge.language": "Language: {language}",
        "tabs.event_timeline": "Event Timeline",
        "tabs.summary_alerts": "Summary & Alerts",
        "tabs.ask_footage": "Ask Footage",
        "tabs.detection_metrics": "Detection Metrics",
        "tabs.audio_report": "Audio Report",
        "tabs.live_feed": "Live Feed",
        "tabs.clip_library": "Clip Library",
        "tabs.settings": "Settings",
        "labels.sample_clips": "Sample clips",
        "labels.original_video": "Original Video",
        "labels.storage": "Storage",
        "labels.status": "Status",
        "labels.annotated_live": "Annotated (Live)",
        "labels.annotated_video": "Annotated Video",
        "labels.detected_events": "Detected Events",
        "labels.event_log": "Event Log",
        "labels.select_clip": "Select clip to preview",
        "labels.clip_preview": "Clip Preview",
        "labels.ai_summary": "AI Security Summary",
        "labels.overnight_summary": "Overnight Summary",
        "labels.translation_time": "Translation time",
        "labels.risk_level": "Risk Level",
        "labels.flagged_items": "Flagged Items",
        "labels.flags": "Flags",
        "labels.suspicious_clips": "Suspicious clips — select to preview",
        "labels.flagged_clip_preview": "Flagged Clip Preview",
        "labels.ask_question": "Ask a question about the footage",
        "labels.ask_examples": (
            "*e.g. 'Anything unusual overnight?', "
            "'Show back door activity', "
            "'What happened between 2–4 AM?'*"
        ),
        "labels.footage_qa": "Footage Q&A",
        "labels.your_question": "Your question",
        "labels.question_placeholder": "Ask about the footage...",
        "labels.zone_counts": "Per-Zone Object Counts",
        "labels.raw_counts": "Raw detection counts by zone",
        "labels.spoken_report": "Spoken Security Report",
        "labels.audio_help": (
            "Generates a spoken playback of the AI security summary using VoxCPM2 TTS. "
            "Run **Analyze** first, then click the button below."
        ),
        "labels.tts_report": "TTS Report",
        "labels.camera_stream": "Camera Stream",
        "labels.live_feed_help": (
            "*Enter an RTSP URL, a file path, or `0` for the default webcam. "
            "Click **Start** to connect.*"
        ),
        "labels.source": "Source",
        "labels.source_placeholder": "rtsp://192.168.1.x:554/stream  or  0",
        "labels.stream_status": "Stream status",
        "labels.live_feed": "Live Feed",
        "labels.recording": "Recording",
        "labels.stored_clips": "Stored Clips",
        "labels.clips": "Clips",
        "labels.preview": "Preview",
        "labels.language": "Language",
        "labels.language_help": "Pick a language, then click **Save**. Restart the server to apply.",
        "buttons.load_sample": "Load Sample",
        "buttons.analyze": "Analyze",
        "buttons.ask": "Ask",
        "buttons.clear_chat": "Clear chat",
        "buttons.generate_audio": "Generate Audio Report",
        "buttons.start": "Start",
        "buttons.stop": "Stop",
        "buttons.start_recording": "Start Recording",
        "buttons.stop_recording": "Stop Recording",
        "buttons.refresh": "Refresh",
        "buttons.load_for_analysis": "Load for Analysis",
        "buttons.delete": "Delete",
        "buttons.save_language": "Save language",
        "table.col_num": "#",
        "table.col_event": "Event",
        "table.col_activity": "Activity",
        "table.col_start": "Start",
        "table.col_end": "End",
        "table.col_zone": "Zone",
        "table.col_confidence": "Confidence",
        "table.col_clip": "Clip",
        "pipeline.load_video": "Load video",
        "pipeline.yolo": "Object detection (YOLO)",
        "pipeline.vlm": "Semantic analysis (VLM)",
        "pipeline.llm_summarize": "LLM summarization",
        "pipeline.starting": "starting…",
        "pipeline.loading_weights": "loading model weights…",
        "pipeline.frame": "frame {pct}",
        "pipeline.persons": "{count} person",
        "pipeline.persons_plural": "{count} persons",
        "pipeline.frames_tracks": "{frames} frames · {tracks} tracks",
        "pipeline.events_count": "{count} events",
        "pipeline.risk": "risk: {level}",
        "overlay.person": "person #{id}",
        "overlay.holding": "HOLDING",
        "overlay.pickup": "PICKUP",
        "splash.initializing": "Initializing Models",
        "splash.waiting": "Waiting…",
        "splash.loading": "Loading weights…",
        "splash.ready": "Ready",
        "splash.failed": "Failed",
        "splash.skipped": "Not available",
        "splash.models.yolo": "Object Detector",
        "splash.models.vlm": "Vision Analyzer",
        "splash.models.llm": "LLM Reasoner",
        "splash.models.tts": "Text-to-Speech",
        "splash.models.tinyaya": "Translator",
        "status.no_video": "No video uploaded.",
        "status.no_video_selected": "No video selected",
        "status.loading_video": "Loading video…",
        "status.running_yolo": "Running YOLO + event structuring…",
        "status.loading_models": "Loading YOLO + VLM weights…",
        "status.processing": "Processing…",
        "status.processing_frame": "Processing frame {pct}…",
        "status.pipeline_error": "Pipeline error: {error}",
        "status.running_llm": "Running LLM summarization…",
        "status.llm_unavailable": "LLM unavailable — no model loaded.",
        "status.done": "Done. {frames} frames · {tracks} tracks · {events} events.",
        "status.translation_timing": "Translation: {elapsed}s ({hits} cached, {misses} translated)",
        "status.clip_from_library": "Clip from library — already stored.",
        "status.sample_not_stored": "Sample clip — not stored.",
        "status.stored": "Stored: {filename}  ({size_mb} MB)",
        "status.storage_error": "Storage error: {error}",
        "status.no_events_qa": "No events loaded yet — please upload and analyze a video first.",
        "status.related_clips": "Related clips: {clips}",
        "status.llm_error": "LLM error: {error}",
        "status.no_source": "No source specified.",
        "status.connected": "Connected: {src}",
        "status.stream_error": "Error: {error}",
        "status.stream_stopped": "Stream stopped.",
        "status.no_active_stream": "No active stream.",
        "status.recording_to": "Recording → {path}",
        "status.no_recording": "No recording in progress.",
        "status.saved_recording": "Saved: {filename}  ({size_mb} MB)",
        "status.saved_path_error": "Saved to {path}. Storage error: {error}",
        "status.clip_not_found": "Clip not found.",
        "status.loaded_clip": "Loaded: {choice}",
        "status.nothing_selected": "Nothing selected.",
        "status.deleted": "Deleted {filename}.",
        "status.delete_failed": "Delete failed.",
        "status.no_prefs_path": "No preferences file path set.",
        "status.prefs_error": "Error saving preferences: {error}",
        "status.language_saved": "Saved **{language}**. Restart the server to apply.",
        "storage.choice_format": "{ts} — {filename}  ({size_mb} MB)  [{source}]",
    },
    "ko": {
        "app.title": "AI 보안 카메라 에이전트",
        "header.tagline": "AI 보안 카메라 에이전트",
        "header.subtitle": (
            "오프라인 AI CCTV 분석 — 구조화된 이벤트 로그, "
            "보안 요약 및 자연어 질의."
        ),
        "header.footage": "영상",
        "header.analysis": "분석",
        "badge.language": "언어: {language}",
        "tabs.event_timeline": "이벤트 타임라인",
        "tabs.summary_alerts": "요약 및 알림",
        "tabs.ask_footage": "영상 질의",
        "tabs.detection_metrics": "탐지 지표",
        "tabs.audio_report": "음성 보고서",
        "tabs.live_feed": "실시간 피드",
        "tabs.clip_library": "클립 라이브러리",
        "tabs.settings": "설정",
        "labels.sample_clips": "샘플 클립",
        "labels.original_video": "원본 영상",
        "labels.storage": "저장소",
        "labels.status": "상태",
        "labels.annotated_live": "주석 (실시간)",
        "labels.annotated_video": "주석 영상",
        "labels.detected_events": "탐지된 이벤트",
        "labels.event_log": "이벤트 로그",
        "labels.select_clip": "미리볼 클립 선택",
        "labels.clip_preview": "클립 미리보기",
        "labels.ai_summary": "AI 보안 요약",
        "labels.overnight_summary": "야간 요약",
        "labels.translation_time": "번역 시간",
        "labels.risk_level": "위험 수준",
        "labels.flagged_items": "플래그 항목",
        "labels.flags": "플래그",
        "labels.suspicious_clips": "의심 클립 — 선택하여 미리보기",
        "labels.flagged_clip_preview": "플래그 클립 미리보기",
        "labels.ask_question": "영상에 대해 질문하기",
        "labels.ask_examples": (
            "*예: '밤새 이상한 일 있었어?', "
            "'뒷문 활동 보여줘', "
            "'새벽 2–4시에 무슨 일?'*"
        ),
        "labels.footage_qa": "영상 Q&A",
        "labels.your_question": "질문",
        "labels.question_placeholder": "영상에 대해 질문하세요...",
        "labels.zone_counts": "구역별 객체 수",
        "labels.raw_counts": "구역별 원시 탐지 수",
        "labels.spoken_report": "음성 보안 보고서",
        "labels.audio_help": (
            "VoxCPM2 TTS로 AI 보안 요약을 음성으로 재생합니다. "
            "**분석**을 먼저 실행한 후 아래 버튼을 클릭하세요."
        ),
        "labels.tts_report": "TTS 보고서",
        "labels.camera_stream": "카메라 스트림",
        "labels.live_feed_help": (
            "*RTSP URL, 파일 경로, 또는 기본 웹캠 `0`을 입력하세요. "
            "**시작**을 클릭하여 연결.*"
        ),
        "labels.source": "소스",
        "labels.source_placeholder": "rtsp://192.168.1.x:554/stream  또는  0",
        "labels.stream_status": "스트림 상태",
        "labels.live_feed": "실시간 피드",
        "labels.recording": "녹화",
        "labels.stored_clips": "저장된 클립",
        "labels.clips": "클립",
        "labels.preview": "미리보기",
        "labels.language": "언어",
        "labels.language_help": "언어를 선택한 후 **저장**을 클릭하세요. 서버를 재시작해야 적용됩니다.",
        "buttons.load_sample": "샘플 불러오기",
        "buttons.analyze": "분석",
        "buttons.ask": "질문",
        "buttons.clear_chat": "대화 지우기",
        "buttons.generate_audio": "음성 보고서 생성",
        "buttons.start": "시작",
        "buttons.stop": "중지",
        "buttons.start_recording": "녹화 시작",
        "buttons.stop_recording": "녹화 중지",
        "buttons.refresh": "새로고침",
        "buttons.load_for_analysis": "분석용 불러오기",
        "buttons.delete": "삭제",
        "buttons.save_language": "언어 저장",
        "table.col_num": "#",
        "table.col_event": "이벤트",
        "table.col_activity": "활동",
        "table.col_start": "시작",
        "table.col_end": "종료",
        "table.col_zone": "구역",
        "table.col_confidence": "신뢰도",
        "table.col_clip": "클립",
        "pipeline.load_video": "영상 불러오기",
        "pipeline.yolo": "객체 탐지 (YOLO)",
        "pipeline.vlm": "의미 분석 (VLM)",
        "pipeline.llm_summarize": "LLM 요약",
        "pipeline.starting": "시작 중…",
        "pipeline.loading_weights": "모델 가중치 로딩 중…",
        "pipeline.frame": "프레임 {pct}",
        "pipeline.persons": "{count}명",
        "pipeline.persons_plural": "{count}명",
        "pipeline.frames_tracks": "{frames} 프레임 · {tracks} 트랙",
        "pipeline.events_count": "{count} 이벤트",
        "pipeline.risk": "위험: {level}",
        "overlay.person": "사람 #{id}",
        "overlay.holding": "소지",
        "overlay.pickup": "집기",
        "splash.initializing": "모델 초기화 중",
        "splash.waiting": "대기 중…",
        "splash.loading": "가중치 로딩 중…",
        "splash.ready": "준비됨",
        "splash.failed": "실패",
        "splash.skipped": "사용 불가",
        "splash.models.yolo": "객체 탐지기",
        "splash.models.vlm": "시각 분석기",
        "splash.models.llm": "LLM 추론기",
        "splash.models.tts": "음성 합성",
        "splash.models.tinyaya": "번역기",
        "status.no_video": "업로드된 영상이 없습니다.",
        "status.no_video_selected": "선택된 영상 없음",
        "status.loading_video": "영상 로딩 중…",
        "status.running_yolo": "YOLO + 이벤트 구조화 실행 중…",
        "status.loading_models": "YOLO + VLM 가중치 로딩 중…",
        "status.processing": "처리 중…",
        "status.processing_frame": "프레임 {pct} 처리 중…",
        "status.pipeline_error": "파이프라인 오류: {error}",
        "status.running_llm": "LLM 요약 실행 중…",
        "status.llm_unavailable": "LLM 사용 불가 — 모델이 로드되지 않았습니다.",
        "status.done": "완료. {frames} 프레임 · {tracks} 트랙 · {events} 이벤트.",
        "status.translation_timing": "번역: {elapsed}s ({hits} 캐시, {misses} 번역)",
        "status.clip_from_library": "라이브러리 클립 — 이미 저장됨.",
        "status.sample_not_stored": "샘플 클립 — 저장하지 않음.",
        "status.stored": "저장됨: {filename}  ({size_mb} MB)",
        "status.storage_error": "저장 오류: {error}",
        "status.no_events_qa": "이벤트가 없습니다 — 영상을 업로드하고 분석을 실행하세요.",
        "status.related_clips": "관련 클립: {clips}",
        "status.llm_error": "LLM 오류: {error}",
        "status.no_source": "소스가 지정되지 않았습니다.",
        "status.connected": "연결됨: {src}",
        "status.stream_error": "오류: {error}",
        "status.stream_stopped": "스트림 중지됨.",
        "status.no_active_stream": "활성 스트림 없음.",
        "status.recording_to": "녹화 중 → {path}",
        "status.no_recording": "진행 중인 녹화 없음.",
        "status.saved_recording": "저장됨: {filename}  ({size_mb} MB)",
        "status.saved_path_error": "{path}에 저장됨. 저장소 오류: {error}",
        "status.clip_not_found": "클립을 찾을 수 없습니다.",
        "status.loaded_clip": "불러옴: {choice}",
        "status.nothing_selected": "선택된 항목 없음.",
        "status.deleted": "{filename} 삭제됨.",
        "status.delete_failed": "삭제 실패.",
        "status.no_prefs_path": "설정 파일 경로가 설정되지 않았습니다.",
        "status.prefs_error": "설정 저장 오류: {error}",
        "status.language_saved": "**{language}** 저장됨. 서버를 재시작하세요.",
        "storage.choice_format": "{ts} — {filename}  ({size_mb} MB)  [{source}]",
    },
}

# Keys that must exist in every locale (for tests)
REQUIRED_MESSAGE_KEYS = sorted(MESSAGES["en"].keys())

SPLASH_MODEL_KEYS = {"yolo": "splash.models.yolo", "vlm": "splash.models.vlm", "llm": "splash.models.llm", "tts": "splash.models.tts", "tinyaya": "splash.models.tinyaya"}


def normalize_key(value: str) -> str:
    return value.lower().replace(" ", "_").replace("-", "_")


class Strings:
    """Locale-aware string lookup."""

    def __init__(self, locale: str = DEFAULT_LOCALE) -> None:
        if locale not in SUPPORTED_LOCALES:
            locale = DEFAULT_LOCALE
        self.locale = locale
        self._messages = MESSAGES[locale]

    def t(self, key: str, **kwargs: Any) -> str:
        text = self._messages.get(key, MESSAGES["en"].get(key, key))
        if kwargs:
            return text.format(**kwargs)
        return text

    @property
    def tts_lang(self) -> str:
        return TTS_LANG[self.locale]

    @property
    def translate_lang(self) -> str:
        return TRANSLATE_LANG[self.locale]

    def pipeline_step_label(self, step_id: str) -> str:
        return self.t(f"pipeline.{step_id}")

    def table_headers(self) -> list[str]:
        return [
            self.t("table.col_num"),
            self.t("table.col_event"),
            self.t("table.col_activity"),
            self.t("table.col_start"),
            self.t("table.col_end"),
            self.t("table.col_zone"),
            self.t("table.col_confidence"),
            self.t("table.col_clip"),
        ]

    def zone_label(self, zone_key: str) -> str:
        return display_zone(zone_key, self.locale)

    def activity_label(self, activity: str) -> str:
        return display_activity(activity, self.locale)

    def event_type_label(self, event_type: str) -> str:
        return display_event_type(event_type, self.locale)

    def risk_label(self, risk: str) -> str:
        return display_risk(risk, self.locale)

    def storage_source_label(self, source: str) -> str:
        return STORAGE_SOURCE.get(self.locale, STORAGE_SOURCE["en"]).get(source, source)


def display_zone(key: str, locale: str = DEFAULT_LOCALE) -> str:
    if not key:
        return key
    norm = normalize_key(key)
    zones = ZONES.get(locale, ZONES["en"])
    if norm in zones:
        return zones[norm]
    # shelf_A → shelf_a
    if norm.startswith("shelf_"):
        alt = norm.replace("shelf_", "shelf_")
        if alt in zones:
            return zones[alt]
    return key.replace("_", " ").title() if locale == "en" else key


def display_activity(key: str, locale: str = DEFAULT_LOCALE) -> str:
    if not key:
        return key
    norm = normalize_key(key)
    activities = ACTIVITIES.get(locale, ACTIVITIES["en"])
    return activities.get(norm, key)


def display_event_type(key: str, locale: str = DEFAULT_LOCALE) -> str:
    if not key:
        return key
    norm = normalize_key(key)
    types = EVENT_TYPES.get(locale, EVENT_TYPES["en"])
    return types.get(norm, key)


def display_risk(key: str, locale: str = DEFAULT_LOCALE) -> str:
    if not key:
        return key
    norm = normalize_key(key)
    risks = RISK.get(locale, RISK["en"])
    return risks.get(norm, key)


def is_known_zone(key: str) -> bool:
    norm = normalize_key(key)
    return norm in ZONES["en"]


def is_known_activity(key: str) -> bool:
    norm = normalize_key(key)
    return norm in ACTIVITIES["en"]


def fmt_event_time(seconds) -> str:
    if seconds is None:
        return ""
    t = float(seconds)
    m, s = divmod(int(t), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"


def _cached_localize(
    text: str,
    locale: str,
    text_cache: dict[str, str],
    stats: "TranslateStats | None",
) -> str:
    if not text or text == "—":
        return text
    if text in text_cache:
        return text_cache[text]
    if locale != "ko":
        text_cache[text] = text
        return text
    translated, row_stats = localize_text(text, locale)
    if translated != text:
        text_cache[text] = translated
    if stats is not None and row_stats is not None:
        merged = stats.merge(row_stats)
        stats.elapsed_s = merged.elapsed_s
        stats.cache_hits = merged.cache_hits
        stats.cache_misses = merged.cache_misses
    return translated if translated != text else text


def format_event_row(
    ev: dict,
    index: int,
    S: Strings,
    *,
    text_cache: dict[str, str],
    stats: "TranslateStats | None" = None,
) -> list:
    """Build one localized event-table row from a structurer event dict."""
    event_type = "pickup" if ev.get("pickup_confirmed") else "observation"
    raw_activity = "pickup" if ev.get("pickup_confirmed") else (ev.get("activity") or "")
    if is_known_activity(raw_activity):
        activity = S.activity_label(raw_activity)
    elif raw_activity.strip():
        activity = _cached_localize(raw_activity.strip(), S.locale, text_cache, stats)
    else:
        activity = "—"

    zone_raw = ev.get("zone", "")
    zone = S.zone_label(zone_raw) if zone_raw else "—"

    clip_name = "—"
    if ev.get("pickup_confirmed"):
        picked = ev.get("picked_up_items") or []
        if picked:
            clip_name = picked[0].get("name", "—") or "—"
    if clip_name != "—":
        clip_name = _cached_localize(clip_name, S.locale, text_cache, stats)

    end_time = ev.get("confirmation_timestamp")
    return [
        index,
        S.event_type_label(event_type),
        activity,
        fmt_event_time(ev.get("timestamp")),
        fmt_event_time(end_time) if end_time is not None else "—",
        zone,
        round(float(ev.get("confidence", 0)), 2),
        clip_name,
    ]


def format_translation_time(S: Strings, stats: "TranslateStats | None") -> str:
    """Format translation timing for display; empty when no translation ran."""
    if stats is None or (stats.cache_hits == 0 and stats.cache_misses == 0):
        return ""
    elapsed = f"{stats.elapsed_s:.2f}"
    return S.t(
        "status.translation_timing",
        elapsed=elapsed,
        hits=stats.cache_hits,
        misses=stats.cache_misses,
    )


def localize_text(text: str, locale: str) -> tuple[str, "TranslateStats | None"]:
    """Post-translate a single string when locale is ko."""
    if locale != "ko" or not text or not text.strip():
        return text, None
    from postprocessing.translate_tts import TranslateStats, translate_cached

    try:
        translated, stats = translate_cached(text, target_lang="Korean")
        return translated, stats
    except Exception:
        return text, None


def localize_llm_result(llm: dict, locale: str) -> tuple[dict, "TranslateStats | None"]:
    """Post-translate summary and flags; risk_level stays English."""
    if locale != "ko":
        return llm, None

    from postprocessing.translate_tts import TranslateStats, translate_many

    result = dict(llm)
    stats = TranslateStats()
    to_translate: set[str] = set()

    summary = llm.get("summary", "")
    if summary and summary.strip():
        to_translate.add(summary)

    for flag in llm.get("flags") or []:
        if flag and str(flag).strip():
            to_translate.add(str(flag))

    if not to_translate:
        return result, None

    try:
        mapping, batch_stats = translate_many(to_translate, "Korean")
        stats = stats.merge(batch_stats)
        if summary:
            result["summary"] = mapping.get(summary, summary)
        result["flags"] = [mapping.get(str(f), str(f)) for f in (llm.get("flags") or [])]
        return result, stats
    except Exception:
        return llm, None


def localize_summary_for_display(
    summary: dict,
    locale: str,
) -> tuple[dict, "TranslateStats | None"]:
    """Attach summary_ko and flags_ko without mutating English canonical fields."""
    if locale != "ko" or not summary:
        return dict(summary) if summary else {}, None

    translated, stats = localize_llm_result(summary, locale)
    out = dict(summary)
    ko_summary = translated.get("summary", "")
    if ko_summary and ko_summary != summary.get("summary", ""):
        out["summary_ko"] = ko_summary
    ko_flags = translated.get("flags")
    if ko_flags and ko_flags != summary.get("flags"):
        out["flags_ko"] = ko_flags
    return out, stats


def localize_chat_for_display(
    messages: list[dict],
    locale: str,
) -> tuple[list[dict], "TranslateStats | None"]:
    """Translate assistant message text for Korean UI; user messages unchanged."""
    if locale != "ko" or not messages:
        return [dict(m) for m in messages], None

    from postprocessing.translate_tts import TranslateStats, translate_many

    to_translate: set[str] = set()
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        text = (msg.get("text") or msg.get("content") or "").strip()
        if text:
            to_translate.add(text)

    if not to_translate:
        return [dict(m) for m in messages], None

    try:
        mapping, stats = translate_many(to_translate, "Korean")
    except Exception:
        return [dict(m) for m in messages], None

    enriched: list[dict] = []
    for msg in messages:
        out = dict(msg)
        if msg.get("role") == "assistant":
            text = (msg.get("text") or msg.get("content") or "").strip()
            ko = mapping.get(text)
            if ko and ko != text:
                out["text_ko"] = ko
        enriched.append(out)
    return enriched, stats


def batch_translate_freeform(
    texts: set[str],
    locale: str,
) -> tuple[dict[str, str], "TranslateStats | None"]:
    """Translate unknown activity/VLM strings to Korean; identity map for English."""
    identity = {t: t for t in texts if t}
    if locale != "ko" or not texts:
        return identity, None

    from postprocessing.translate_tts import TranslateStats, translate_many

    to_translate = {t for t in texts if t and not is_known_activity(t)}
    cache = dict(identity)
    if not to_translate:
        return cache, None

    try:
        mapping, stats = translate_many(to_translate, "Korean")
        cache.update(mapping)
        return cache, stats
    except Exception:
        return identity, None


def localize_zone_labels(
    zones: list[str],
    locale: str,
) -> tuple[dict[str, str], "TranslateStats | None"]:
    """Return localized labels for zone keys; unknown keys go through TinyAya."""
    unique = {z for z in zones if z and str(z).strip()}
    if locale != "ko" or not unique:
        return {z: z for z in unique}, None

    from postprocessing.translate_tts import TranslateStats, translate_many

    result: dict[str, str] = {}
    to_translate: set[str] = set()
    for z in unique:
        norm = normalize_key(z)
        if norm in ZONES.get("ko", {}):
            result[z] = display_zone(z, "ko")
        else:
            to_translate.add(z)

    stats = TranslateStats()
    if to_translate:
        try:
            mapping, batch_stats = translate_many(to_translate, "Korean")
            result.update(mapping)
            stats = stats.merge(batch_stats)
        except Exception:
            for z in to_translate:
                result.setdefault(z, z)

    if stats.cache_hits == 0 and stats.cache_misses == 0:
        return result, None
    return result, stats


def localize_events_for_display(
    events: list[dict],
    locale: str,
    *,
    text_cache: dict[str, str] | None = None,
    stats: "TranslateStats | None" = None,
) -> tuple[list[dict], "TranslateStats | None"]:
    """Attach description_ko and zone_ko for Korean UI display."""
    if locale != "ko":
        return [dict(ev) for ev in events], stats

    from postprocessing.translate_tts import TranslateStats

    cache = text_cache if text_cache is not None else {}
    accum = stats if stats is not None else TranslateStats()
    unknown_zones = {
        str(ev.get("zone", "")).strip()
        for ev in events
        if ev.get("zone") and not is_known_zone(str(ev.get("zone", "")))
    }
    zone_map, zone_stats = localize_zone_labels(list(unknown_zones), locale)
    if zone_stats is not None:
        merged = accum.merge(zone_stats)
        accum.elapsed_s = merged.elapsed_s
        accum.cache_hits = merged.cache_hits
        accum.cache_misses = merged.cache_misses

    enriched: list[dict] = []
    for ev in events:
        out = dict(ev)
        desc = (ev.get("label") or ev.get("description") or "").strip()
        if desc:
            ko = _cached_localize(desc, locale, cache, accum)
            if ko != desc:
                out["description_ko"] = ko

        zone_raw = str(ev.get("zone", "")).strip()
        if zone_raw:
            if is_known_zone(zone_raw):
                out["zone_ko"] = display_zone(zone_raw, "ko")
            else:
                out["zone_ko"] = zone_map.get(zone_raw, zone_raw)
        enriched.append(out)

    if stats is None and accum.cache_hits == 0 and accum.cache_misses == 0:
        return enriched, None
    return enriched, accum if stats is None else stats


def pipeline_steps_default() -> list[tuple[str, str, str]]:
    return [(step_id, "pending", "") for step_id in PIPELINE_STEP_IDS]
