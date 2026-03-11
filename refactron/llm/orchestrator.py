"""Orchestrator for LLM-based refactoring suggestions."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Union

from refactron.core.models import CodeIssue, IssueCategory, IssueLevel
from refactron.llm.backend_client import BackendLLMClient
from refactron.llm.client import GroqClient
from refactron.llm.models import RefactoringSuggestion, SuggestionStatus
from refactron.llm.prompts import (
    BATCH_TRIAGE_PROMPT,
    BATCH_TRIAGE_SYSTEM_PROMPT,
    DOCUMENTATION_PROMPT,
    SUGGESTION_PROMPT,
    SYSTEM_PROMPT,
)
from refactron.llm.safety import SafetyGate
from refactron.rag.retriever import ContextRetriever

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """Coordinates RAG context retrieval and LLM generation."""

    def __init__(
        self,
        retriever: Optional[ContextRetriever] = None,
        llm_client: Optional[Union[GroqClient, BackendLLMClient]] = None,
        safety_gate: Optional[SafetyGate] = None,
    ):
        self.retriever = retriever

        if llm_client:
            self.client = llm_client
        else:
            # Try to use GroqClient if API key is present, otherwise use BackendLLMClient
            if os.getenv("GROQ_API_KEY"):
                try:
                    self.client = GroqClient()
                except RuntimeError:
                    self.client = BackendLLMClient()
            else:
                self.client = BackendLLMClient()

        self.safety_gate = safety_gate or SafetyGate()

    def generate_suggestion(
        self, issue: CodeIssue, original_code: str, language: str = "python"
    ) -> RefactoringSuggestion:
        """Generate a refactoring suggestion for a code issue.

        Args:
            issue: The code issue to fix
            original_code: The failing code snippet
            language: The programming language of the code (default: "python")

        Returns:
            A validated refactoring suggestion
        """
        # 1. Retrieve Context
        context_snippets = []
        if self.retriever:
            try:
                # Search for similar code or relevant context
                results = self.retriever.retrieve_similar(
                    f"{issue.message} {original_code}", top_k=3
                )
                context_snippets = [r.content for r in results]
            except Exception as e:
                logger.warning(f"Context retrieval failed: {e}")

        rag_context = "\n\n".join(context_snippets) if context_snippets else "No context available."

        # 2. Construct Prompt
        prompt = SUGGESTION_PROMPT.format(
            issue_message=issue.message,
            file_path=issue.file_path,
            line_number=issue.line_number,
            severity=issue.level.value,
            original_code=original_code,
            rag_context=rag_context,
            language=language,
        )

        # 3. Call LLM
        response_text = "N/A"
        try:
            response_text = self.client.generate(
                prompt=prompt, system=SYSTEM_PROMPT, temperature=0.2  # Low temperature for code
            )

            # Parse JSON response
            # Note: Groq might return markdown code blocks, strip them
            clean_text = self._clean_json_response(response_text)

            # Using strict=False allows control characters like newlines in strings
            data = json.loads(clean_text, strict=False)

            # Extract and parse confidence score
            raw_confidence = data.get("confidence_score", 0.7)
            try:
                # Handle strings with % or range strings
                if isinstance(raw_confidence, str):
                    match = re.search(r"(\d+\.?\d*)", raw_confidence)
                    confidence = (
                        float(match.group(1)) / 100.0
                        if "%" in raw_confidence
                        else float(match.group(1))
                    )
                else:
                    confidence = float(raw_confidence)
            except (ValueError, TypeError, AttributeError):
                confidence = 0.5  # Fallback

            suggestion = RefactoringSuggestion(
                issue=issue,
                original_code=original_code,
                context_files=[r.file_path for r in results] if self.retriever else [],
                proposed_code=data.get("proposed_code", ""),
                explanation=data.get("explanation", "No explanation provided."),
                reasoning=data.get("reasoning", ""),
                model_name=self.client.model,
                confidence_score=min(max(confidence, 0.0), 1.0),
                llm_confidence=min(max(confidence, 0.0), 1.0),
            )

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            logger.debug(f"Raw response: {response_text}")
            # Return a failed suggestion
            return RefactoringSuggestion(
                issue=issue,
                original_code=original_code,
                context_files=[],
                proposed_code="",
                explanation=f"Generation failed: {str(e)}",
                reasoning="",
                model_name=self.client.model,
                confidence_score=0.0,
                status=SuggestionStatus.FAILED,
            )

        # 4. Safety Validation
        try:
            safety_result = self.safety_gate.validate(suggestion)
            suggestion.safety_result = safety_result

            # Link confidence score to safety result score
            suggestion.confidence_score = safety_result.score

            if not safety_result.passed:
                suggestion.status = SuggestionStatus.REJECTED
                logger.warning(f"Suggestion failed safety check: {safety_result.issues}")
            else:
                suggestion.status = SuggestionStatus.PENDING

        except Exception as e:
            logger.error(f"Safety validation failed: {e}")
            suggestion.status = SuggestionStatus.FAILED

        return suggestion

    def generate_documentation(
        self, code: str, file_path: str = "unknown", language: str = "python"
    ) -> RefactoringSuggestion:
        """Generate documentation for the provided code.

        Args:
            code: The code to document
            file_path: Optional file path for context
            language: The programming language of the code (default: "python")

        Returns:
            A suggestion containing the documented code
        """
        # Create a synthetic issue for tracking
        issue = CodeIssue(
            category=IssueCategory.DOCUMENTATION,
            level=IssueLevel.INFO,
            message="Add documentation",
            file_path=Path(file_path),
            line_number=1,
        )

        # 1. Retrieve Context
        context_snippets = []
        if self.retriever:
            try:
                # Search for similar code or relevant context
                results = self.retriever.retrieve_similar(code[:500], top_k=2)
                context_snippets = [r.content for r in results]
            except Exception as e:
                logger.warning(f"Context retrieval failed: {e}")

        rag_context = "\n\n".join(context_snippets) if context_snippets else "No context available."

        # 2. Construct Prompt
        prompt = DOCUMENTATION_PROMPT.format(
            original_code=code, rag_context=rag_context, language=language
        )

        # 3. Call LLM
        try:
            response_text = self.client.generate(
                prompt=prompt, system=SYSTEM_PROMPT, temperature=0.2
            )

            # Parse custom delimiter format
            explanation = "Added documentation"
            proposed_code = ""
            confidence = 0.8

            if "@@@EXPLANATION@@@" in response_text:
                parts = response_text.split("@@@")
                for i, part in enumerate(parts):
                    if part == "EXPLANATION":
                        explanation = parts[i + 1].strip()
                    elif part == "CONFIDENCE":
                        try:
                            confidence = float(parts[i + 1].strip())
                        except ValueError:
                            pass
                    elif part == "MARKDOWN":
                        proposed_code = parts[i + 1].strip()

            if not proposed_code:
                raise ValueError("Could not extract markdown content from response")

            return RefactoringSuggestion(
                issue=issue,
                original_code=code,
                context_files=[],
                explanation=explanation,
                proposed_code=proposed_code,
                reasoning="Documentation update",
                confidence_score=confidence,
                llm_confidence=confidence,
                model_name=self.client.model,
                status=SuggestionStatus.PENDING,
            )

        except Exception as e:
            logger.error(f"Documentation generation failed: {e}")
            return RefactoringSuggestion(
                issue=issue,
                original_code=code,
                context_files=[],
                explanation=f"Error: {str(e)}",
                proposed_code="",
                reasoning="",
                confidence_score=0.0,
                llm_confidence=0.0,
                model_name=self.client.model,
                status=SuggestionStatus.FAILED,
            )

    def evaluate_issues_batch(
        self,
        issues: List[CodeIssue],
        source_code: str,
        language: str = "python",
    ) -> Dict[str, float]:
        """Evaluate a batch of issues for a single file to suppress false positives.

        Args:
            issues: List of CodeIssues found in the file
            source_code: The full source code of the file
            language: The programming language of the code (default: "python")

        Returns:
            Dict mapping issue IDs (using rule_id or index) to confidence scores
        """
        if not issues:
            return {}

        # 1. Retrieve Context
        context_snippets = []
        if self.retriever:
            try:
                results = self.retriever.retrieve_similar(source_code[:1000], top_k=3)
                context_snippets = [r.content for r in results]
            except Exception as e:
                logger.warning(f"Context retrieval failed: {e}")

        rag_context = (
            "\n\n".join(context_snippets) if context_snippets else "No context available."
        )

        # 2. Construct JSON for issues
        issues_data = {}
        for i, issue in enumerate(issues):
            base_id = getattr(issue, "rule_id", None) or "issue"
            line_number = getattr(issue, "line_number", None)
            id_parts = [str(base_id)]
            if line_number is not None:
                id_parts.append(str(line_number))
            id_parts.append(str(i))
            issue_id = ":".join(id_parts)

            # Ensure uniqueness in case of unexpected collisions
            unique_id = issue_id
            suffix = 1
            while unique_id in issues_data:
                suffix += 1
                unique_id = f"{issue_id}_{suffix}"
                logger.warning(
                    f"Issue ID collision detected for '{issue_id}', using '{unique_id}'"
                )

            issues_data[unique_id] = {
                "rule_id": getattr(issue, "rule_id", None),
                "message": issue.message,
                "line": issue.line_number,
                "category": (
                    issue.category.value
                    if hasattr(issue.category, "value")
                    else str(issue.category)
                ),
                "severity": (
                    issue.level.value if hasattr(issue.level, "value") else str(issue.level)
                ),
            }

        # 3. Construct Prompt
        prompt = BATCH_TRIAGE_PROMPT.format(
            source_code=source_code,
            rag_context=rag_context,
            issues_json=json.dumps(issues_data, indent=2),
            language=language,
        )

        # 4. Call LLM with dedicated batch triage system prompt
        try:
            response_text = self.client.generate(
                prompt=prompt, system=BATCH_TRIAGE_SYSTEM_PROMPT, temperature=0.1
            )
            clean_text = self._clean_json_response(response_text)
            data = json.loads(clean_text, strict=False)

            # Ensure we return a Dict[str, float]
            result = {}
            for k, v in data.items():
                try:
                    result[str(k)] = float(v)
                except (ValueError, TypeError):
                    result[str(k)] = 0.5  # Fallback for parsing errors
            return result

        except Exception as e:
            logger.error(f"Batch triage failed: {e}")
            # Fallback: return default confidence
            return {str(k): 0.5 for k in issues_data.keys()}

    def _clean_json_response(self, text: str) -> str:
        """Clean LLM response to extract JSON."""
        text = text.strip()

        # Remove markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end]
            else:
                text = text[start:]
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end]
            else:
                text = text[start:]

        return text.strip()
