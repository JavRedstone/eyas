"""Prompt templates and GBNF grammars for the reasoning module."""

SYSTEM_PROMPT = (
    "You are a security analyst for a convenience store. "
    "You receive structured CCTV event logs. "
    "Track IDs are unique WITHIN a single camera only. "
    "When events span multiple cameras (shown with a camera label like '[cam1]'), "
    "the same person appears with different Track IDs in each camera — "
    "use the appearance description to recognise them as the same individual across cameras. "
    "When an 'Identified people' section is provided, describe each person by their "
    "appearance (e.g. 'the person in a red hoodie') rather than just 'Track N'. "
    "You may include the Track ID in parentheses for clarity: "
    "'the person in a red hoodie (Track 3 in cam1)'. "
    "Respond ONLY with valid JSON — no prose, no markdown fences, no thinking text."
)

# ---------------------------------------------------------------------------
# Event summarization
# ---------------------------------------------------------------------------

SUMMARIZE_PROMPT = """\
Analyze the CCTV event log below. Group events by Track ID to identify each person's activity.
When an 'Identified people' section is present, refer to each person by their appearance
(e.g. "the person in a red hoodie (Track 3)") rather than just their Track ID.
RULE: If ANY event in the log has "Pickup: YES", you MUST state in the summary that a pickup
occurred, name the person, and include it in flags. Do not write "no pickup occurred" when a
"Pickup: YES" event exists.

Produce a security summary that covers:
  1. How many distinct people were tracked
  2. For each person who had a pickup event (Pickup: YES): appearance, items taken or "unidentified item", zones visited
  3. Any suspicious or notable patterns, including pickup/handling of items, repeated pickups,
     unusual zones, concealment, and people lingering or standing still without obvious purpose
  4. Overall risk level:
       "none"   — no suspicious behaviour whatsoever
       "low"    — mildly suspicious (e.g. unusual movement, lingering, reaching for items) but no confirmed pickup
       "medium" — confirmed pickup OR very suspicious behaviour (e.g. bending into shelves, concealment attempt)
       "high"   — multiple confirmed pickups, clear concealment with items, or repeated theft-pattern behaviour

If someone picks up an item, mention that explicitly in the summary and include it in flags
even if the overall risk stays low.

--- EXAMPLE ---
Event log (period: 14:00:00–14:30:00):
Identified people:
  Track 3: wearing a white t-shirt and blue jeans, medium build
  Track 5: wearing a black hoodie, tall

Event 0: [Track 3 | t=0.00s] Zone: entrance | entry | Pickup: no | Conf: 0.91
Event 1: [Track 3 | t=12.50s] Zone: aisle_2 | dwell | Pickup: no | Conf: 0.87
Event 2: [Track 3 | t=28.10s] Zone: aisle_2 | pickup | Held: water x1 | Pickup: YES -> water x1 | Conf: 0.93
Event 3: [Track 5 | t=5.00s] Zone: entrance | entry | Pickup: no | Conf: 0.89
Event 4: [Track 5 | t=45.00s] Zone: counter | dwell | Pickup: no | Conf: 0.85
Event 5: [Track 3 | t=55.00s] Zone: aisle_3 | pickup | Held: chips x1 | Pickup: YES -> chips x1 | Conf: 0.90

Response:
{{"summary": "2 people tracked. The person in a white t-shirt and jeans (Track 3) took 2 items (water, chips) across aisle_2 and aisle_3 without visiting the counter — possible theft. The person in a black hoodie (Track 5) entered and went to the counter (normal behaviour).", "flags": ["Person in white t-shirt (Track 3) took multiple items without counter visit"], "suspicious_clips": [], "risk_level": "medium"}}
--- END EXAMPLE ---

Event log (period: {period}):
{event_log}

Response:
"""

# ---------------------------------------------------------------------------
# Question-answering
# ---------------------------------------------------------------------------

QA_PROMPT = """\
Answer the question about the CCTV footage.
When a security analysis summary is provided, treat it as the authoritative ground truth —
do NOT contradict it. Use the event log for specific details (timestamps, zones, indices).
When an 'Identified people' section is present, refer to each person by their appearance.
Always include the Zone field when describing where events happened.
Any event with "Pickup: YES" is a confirmed suspicious pickup — treat it as such.
Cite relevant event indices (0-based) and note zone, items, and person appearance.

--- EXAMPLE ---
Security analysis summary:
  Risk level: medium
  Summary: The person in a white t-shirt (Track 3) picked up water and chips from aisle_2 and aisle_3 without visiting the counter — possible theft.
  Flags: ["Person in white t-shirt (Track 3) took multiple items without counter visit"]

Event log:
Identified people:
  Track 3: wearing a white t-shirt and blue jeans
  Track 5: wearing a black hoodie

Event 0: [Track 3 | t=0.00s] Zone: entrance | entry | Pickup: no | Conf: 0.91
Event 1: [Track 3 | t=28.10s] Zone: aisle_2 | pickup | Held: water x1 | Pickup: YES -> water x1 | Conf: 0.93
Event 2: [Track 5 | t=5.00s] Zone: entrance | entry | Pickup: no | Conf: 0.89

Question: Who took items and how many?

Response:
{{"answer": "The person in a white t-shirt and jeans (Track 3) took 1 item (water) from aisle_2. The person in a black hoodie (Track 5) had no pickup events.", "relevant_event_indices": [1], "clips": []}}
--- END EXAMPLE ---

{summary_block}Event log:
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
Event: [Track 7 | t=840.00s] Zone: aisle_2 | concealment | Held: bottle x1 | Pickup: YES | Conf: 0.82

Response:
{{"alert": "Possible concealment by Track 7 in aisle_2 at t=840s. Item: bottle. Confidence 82%.", "severity": "high", "clip": ""}}
--- END EXAMPLE ---

Event: {event}

Response:
"""

# ---------------------------------------------------------------------------
# GBNF grammars — force valid JSON from llama-cpp models (unused by HF models)
# ---------------------------------------------------------------------------

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
