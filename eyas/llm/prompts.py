"""Prompt templates, few-shot examples, and GBNF grammars for the reasoning module."""

SYSTEM_PROMPT = (
    "You are a security analyst assistant for a convenience store. "
    "You receive structured CCTV event logs and produce concise, factual security reports. "
    "Respond only with the requested JSON — no extra prose, no markdown fences."
)

# ---------------------------------------------------------------------------
# Event summarization
# ---------------------------------------------------------------------------

SUMMARIZE_PROMPT = """\
Below is a CCTV event log. Summarize what happened, flag anything suspicious, and assess the overall risk level.

--- EXAMPLE ---
Event log (period: 01:00:00–01:30:00):
Event 1: [entry] 01:02:11–01:02:20 | Zone: back_door | Conf: 0.94 | clip: cam2_01h02.mp4
Event 2: [dwell] 01:02:25–01:07:44 | Zone: aisle_3  | Conf: 0.88 | clip: cam1_01h02.mp4
Event 3: [exit]  01:07:50–01:07:58 | Zone: back_door | Conf: 0.95 | clip: cam2_01h07.mp4

Response:
{{"summary": "1 after-hours entry via back door at 01:02. Occupant lingered in aisle 3 for ~5 min then exited. No counter or register interaction. Review cam2_01h02.mp4.", "flags": ["after-hours entry", "prolonged dwell"], "suspicious_clips": ["cam2_01h02.mp4", "cam1_01h02.mp4"], "risk_level": "medium"}}
--- END EXAMPLE ---

Event log (period: {period}):
{event_log}

Response:
"""

# ---------------------------------------------------------------------------
# Question-answering over the event log
# ---------------------------------------------------------------------------

QA_PROMPT = """\
Below is a CCTV event log. Answer the user's question accurately and cite relevant event indices (0-based) and clip filenames.

--- EXAMPLE ---
Event log:
Event 0: [entry] 01:02:11–01:02:20 | Zone: back_door | Conf: 0.94 | clip: cam2_01h02.mp4
Event 1: [dwell] 01:02:25–01:07:44 | Zone: aisle_3  | Conf: 0.88 | clip: cam1_01h02.mp4
Event 2: [exit]  01:07:50–01:07:58 | Zone: back_door | Conf: 0.95 | clip: cam2_01h07.mp4

Question: Was there any unusual activity?

Response:
{{"answer": "Yes — 1 unscheduled after-hours entry at the back door at 01:02. The person lingered in aisle 3 for approximately 5 minutes before leaving.", "relevant_event_indices": [0, 1], "clips": ["cam2_01h02.mp4", "cam1_01h02.mp4"]}}
--- END EXAMPLE ---

Event log:
{event_log}

Question: {query}

Response:
"""

# ---------------------------------------------------------------------------
# Single-event alert
# ---------------------------------------------------------------------------

ALERT_PROMPT = """\
Generate a short security alert for the following CCTV event. Be concise and factual.

--- EXAMPLE ---
Event: [concealment] 14:32:05–14:32:41 | Zone: aisle_2 | Conf: 0.82 | clip: cam3_14h32.mp4

Response:
{{"alert": "Possible concealment detected in aisle 2 at 14:32. Confidence 82%. Review cam3_14h32.mp4.", "severity": "high", "clip": "cam3_14h32.mp4"}}
--- END EXAMPLE ---

Event: {event}

Response:
"""

# ---------------------------------------------------------------------------
# GBNF grammars — force valid JSON from the LLM
# ---------------------------------------------------------------------------

# Shared building blocks
_GBNF_COMMON = r"""
ws        ::= ([ \t\n\r])*
string    ::= "\"" ([^"\\] | "\\" (["\\/bfnrt] | "u" [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F] [0-9a-fA-F]))* "\""
number    ::= ("-")? ("0" | [1-9] [0-9]*) ("." [0-9]+)? (([eE] [+-]? [0-9]+))?
str-array ::= "[" ws (string (ws "," ws string)*)? ws "]"
int-array ::= "[" ws (number (ws "," ws number)*)? ws "]"
risk-val  ::= "\"none\"" | "\"low\"" | "\"medium\"" | "\"high\""
sev-val   ::= "\"low\"" | "\"medium\"" | "\"high\""
"""

SUMMARIZE_GRAMMAR = (
    _GBNF_COMMON
    + r"""
root ::= "{" ws
         "\"summary\""         ws ":" ws string ws "," ws
         "\"flags\""           ws ":" ws str-array ws "," ws
         "\"suspicious_clips\"" ws ":" ws str-array ws "," ws
         "\"risk_level\""      ws ":" ws risk-val ws
         "}"
"""
)

QA_GRAMMAR = (
    _GBNF_COMMON
    + r"""
root ::= "{" ws
         "\"answer\""                ws ":" ws string ws "," ws
         "\"relevant_event_indices\"" ws ":" ws int-array ws "," ws
         "\"clips\""                 ws ":" ws str-array ws
         "}"
"""
)

ALERT_GRAMMAR = (
    _GBNF_COMMON
    + r"""
root ::= "{" ws
         "\"alert\""    ws ":" ws string ws "," ws
         "\"severity\"" ws ":" ws sev-val ws "," ws
         "\"clip\""     ws ":" ws string ws
         "}"
"""
)
