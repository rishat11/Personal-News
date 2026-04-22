from src.digest.summarize import extractive_summary


def test_extractive_summary_prefers_text() -> None:
    assert extractive_summary("hello world", "fallback") == "hello world"


def test_extractive_summary_fallback() -> None:
    assert extractive_summary("", "fallback") == "fallback"


def test_extractive_summary_empty() -> None:
    assert extractive_summary("", "") == "Краткого описания пока нет."

