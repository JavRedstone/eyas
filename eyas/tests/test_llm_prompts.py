"""Tests for eyas/llm/prompts.py — template structure and required placeholders."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import pytest

from eyas.llm.prompts import (
    ALERT_GRAMMAR,
    ALERT_PROMPT,
    QA_GRAMMAR,
    QA_PROMPT,
    SUMMARIZE_GRAMMAR,
    SUMMARIZE_PROMPT,
    SYSTEM_PROMPT,
)


class TestSystemPrompt:
    def test_mentions_security_analyst(self):
        assert "security" in SYSTEM_PROMPT.lower()

    def test_instructs_json_only(self):
        assert "JSON" in SYSTEM_PROMPT


class TestSummarizePrompt:
    def test_has_period_placeholder(self):
        assert "{period}" in SUMMARIZE_PROMPT

    def test_has_event_log_placeholder(self):
        assert "{event_log}" in SUMMARIZE_PROMPT

    def test_has_few_shot_example(self):
        assert "EXAMPLE" in SUMMARIZE_PROMPT

    def test_example_includes_risk_level(self):
        assert "risk_level" in SUMMARIZE_PROMPT

    def test_example_includes_flags(self):
        assert "flags" in SUMMARIZE_PROMPT


class TestQaPrompt:
    def test_has_event_log_placeholder(self):
        assert "{event_log}" in QA_PROMPT

    def test_has_query_placeholder(self):
        assert "{query}" in QA_PROMPT

    def test_has_few_shot_example(self):
        assert "EXAMPLE" in QA_PROMPT

    def test_example_includes_relevant_indices(self):
        assert "relevant_event_indices" in QA_PROMPT


class TestAlertPrompt:
    def test_has_event_placeholder(self):
        assert "{event}" in ALERT_PROMPT

    def test_has_few_shot_example(self):
        assert "EXAMPLE" in ALERT_PROMPT

    def test_example_includes_severity(self):
        assert "severity" in ALERT_PROMPT


class TestGrammarStrings:
    def test_summarize_grammar_is_nonempty(self):
        assert len(SUMMARIZE_GRAMMAR.strip()) > 0

    def test_summarize_grammar_has_risk_level(self):
        assert "risk_level" in SUMMARIZE_GRAMMAR

    def test_qa_grammar_has_answer(self):
        assert "answer" in QA_GRAMMAR

    def test_qa_grammar_has_relevant_event_indices(self):
        assert "relevant_event_indices" in QA_GRAMMAR

    def test_alert_grammar_has_severity(self):
        assert "severity" in ALERT_GRAMMAR

    def test_alert_grammar_has_clip(self):
        assert "clip" in ALERT_GRAMMAR


if __name__ == "__main__":
    sys.exit(pytest.main([__file__] + sys.argv[1:]))
