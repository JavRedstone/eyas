"""LLM reasoning wrapper using llama-cpp-python or similar runtime."""

from typing import List, Dict


def summarize_events(events: List[Dict]) -> str:
    """Return a short natural-language summary for a list of events."""
    # TODO: implement prompt templates and local llama.cpp inference
    return ""


def answer_query(events: List[Dict], query: str) -> str:
    """Answer a natural-language question about the event log."""
    # TODO: implement retrieval + LLM prompt
    return ""
