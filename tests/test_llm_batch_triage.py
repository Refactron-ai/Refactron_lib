"""Tests for the Batched Triage & RAG Context in LLMOrchestrator."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
from refactron.llm.orchestrator import LLMOrchestrator
from refactron.llm.prompts import BATCH_TRIAGE_SYSTEM_PROMPT
from refactron.rag.retriever import ContextRetriever


@pytest.fixture
def mock_retriever():
    retriever = MagicMock(spec=ContextRetriever)
    mock_result = MagicMock()
    mock_result.content = "Some context snippet"
    retriever.retrieve_similar.return_value = [mock_result]
    return retriever


@pytest.fixture
def mock_llm_client():
    client = MagicMock()
    client.model = "mock-model"
    # Provide a mock JSON response for evaluate_issues_batch
    client.generate.return_value = """```json
{
  "issue:10:0": 0.85,
  "issue:20:1": 0.12,
  "E101:30:2": 0.95
}
```"""
    return client


def test_evaluate_issues_batch(mock_llm_client, mock_retriever):
    """Test that batch evaluation correctly parses JSON map from the LLM."""
    orchestrator = LLMOrchestrator(retriever=mock_retriever, llm_client=mock_llm_client)

    issues = [
        CodeIssue(
            category=IssueCategory.COMPLEXITY,
            level=IssueLevel.WARNING,
            message="Too complex",
            file_path=Path("test.py"),
            line_number=10,
        ),
        CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.INFO,
            message="Line too long",
            file_path=Path("test.py"),
            line_number=20,
        ),
        CodeIssue(
            category=IssueCategory.CODE_SMELL,
            level=IssueLevel.WARNING,
            message="Bad smell",
            file_path=Path("test.py"),
            line_number=30,
            rule_id="E101",
        ),
    ]

    source_code = "def complex_function():\n    pass\n" * 10

    result = orchestrator.evaluate_issues_batch(issues, source_code)

    # Check that ContextRetriever was called for RAG Context
    mock_retriever.retrieve_similar.assert_called_once()
    assert "def complex_function" in mock_retriever.retrieve_similar.call_args[0][0]

    # Check JSON map parsing
    assert isinstance(result, dict)
    assert result.get("issue:10:0") == 0.85
    assert result.get("issue:20:1") == 0.12
    assert result.get("E101:30:2") == 0.95

    # Ensure there's exactly 3 keys corresponding to the 3 returned mapping
    assert len(result) == 3


def test_evaluate_issues_batch_uses_dedicated_system_prompt(mock_llm_client, mock_retriever):
    """Test that batch evaluation uses BATCH_TRIAGE_SYSTEM_PROMPT, not SYSTEM_PROMPT."""
    orchestrator = LLMOrchestrator(retriever=mock_retriever, llm_client=mock_llm_client)

    issues = [
        CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.INFO,
            message="Style issue",
            file_path=Path("test.py"),
            line_number=1,
        ),
    ]

    orchestrator.evaluate_issues_batch(issues, "x = 1")

    # Verify that the system prompt used is BATCH_TRIAGE_SYSTEM_PROMPT
    call_kwargs = mock_llm_client.generate.call_args.kwargs
    assert call_kwargs["system"] == BATCH_TRIAGE_SYSTEM_PROMPT
    assert "code triage expert" in call_kwargs["system"]
    # Ensure it does NOT contain the refactoring system prompt instructions
    assert "proposed_code" not in call_kwargs["system"]


def test_evaluate_issues_batch_language_parameter(mock_llm_client, mock_retriever):
    """Test that the language parameter is passed through to the prompt."""
    orchestrator = LLMOrchestrator(retriever=mock_retriever, llm_client=mock_llm_client)

    issues = [
        CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.INFO,
            message="Style issue",
            file_path=Path("test.js"),
            line_number=1,
        ),
    ]

    orchestrator.evaluate_issues_batch(issues, "const x = 1;", language="javascript")

    # Verify the prompt contains the language
    call_kwargs = mock_llm_client.generate.call_args.kwargs
    assert "```javascript" in call_kwargs["prompt"]


def test_evaluate_issues_batch_empty_issues(mock_llm_client, mock_retriever):
    """Test batch evaluation handles empty issues correctly."""
    orchestrator = LLMOrchestrator(retriever=mock_retriever, llm_client=mock_llm_client)

    result = orchestrator.evaluate_issues_batch([], "source")
    assert result == {}
    mock_llm_client.generate.assert_not_called()


def test_evaluate_issues_batch_fallback_on_error(mock_llm_client, mock_retriever):
    """Test batch evaluation handles LLM errors using a fallback mechanism."""
    mock_llm_client.generate.side_effect = Exception("LLM Error")

    orchestrator = LLMOrchestrator(retriever=mock_retriever, llm_client=mock_llm_client)

    issues = [
        CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.INFO,
            message="Line too long",
            file_path=Path("test.py"),
            line_number=20,
        )
    ]

    result = orchestrator.evaluate_issues_batch(issues, "source")

    # It should fallback to 0.5 confidence
    assert len(result) == 1
    assert all(v == 0.5 for v in result.values())


def test_evaluate_issues_batch_fallback_on_bad_json(mock_llm_client, mock_retriever):
    """Test batch evaluation handles invalid JSON appropriately."""
    mock_llm_client.generate.return_value = "not a json string at all"
    orchestrator = LLMOrchestrator(retriever=mock_retriever, llm_client=mock_llm_client)

    issues = [
        CodeIssue(
            category=IssueCategory.STYLE,
            level=IssueLevel.INFO,
            message="Line too long",
            file_path=Path("test.py"),
            line_number=20,
        )
    ]

    result = orchestrator.evaluate_issues_batch(issues, "source")

    assert len(result) == 1
    assert all(v == 0.5 for v in result.values())
