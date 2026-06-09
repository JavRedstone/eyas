# llm

Local LLM reasoning over the event log via llama.cpp (GGUF models).

## Key exports

| Symbol | Description |
|---|---|
| `Reasoner` | Main class — loads a GGUF model and exposes three inference methods |
| `Reasoner.summarize_events(events)` | Returns `{summary, risk_level, flags, suspicious_clips}` |
| `Reasoner.answer_query(events, query)` | Free-form Q&A over the event log |
| `Reasoner.generate_alert(event)` | Generates an operator alert for a single confirmed-pickup event |
| `SUMMARIZE_PROMPT` / `QA_PROMPT` / `ALERT_PROMPT` | Prompt templates with few-shot examples |
| `SUMMARIZE_GRAMMAR` / `QA_GRAMMAR` / `ALERT_GRAMMAR` | GBNF grammar strings that constrain JSON output |

## Model

Default: `models/nemotron-nano-4b.gguf`.  
Override with the `EYAS_MODEL_PATH` environment variable.

## Usage

```python
import json
from llm.reasoner import Reasoner

events = json.loads(open("tests/samples/events.json").read())
r = Reasoner("models/nemotron-nano-4b.gguf")
result = r.summarize_events(events)
print(result["risk_level"], result["summary"])
```
