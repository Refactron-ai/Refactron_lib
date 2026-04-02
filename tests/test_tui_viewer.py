"""Tests for the TUI issue viewer state machine.

Tests the pure-logic components: TuiState, _handle_key(), and render functions.
No TTY/termios required — all state transitions are pure functions.
"""

from pathlib import Path

from refactron.cli.ui import KEY_DOWN, KEY_ENTER, KEY_UP, TuiState, _build_tui_groups, _handle_key
from refactron.core.analysis_result import AnalysisResult
from refactron.core.models import CodeIssue, FileMetrics, IssueCategory, IssueLevel

# ── Helpers ──────────────────────────────────────────────────────────


def _make_issue(
    level: IssueLevel = IssueLevel.WARNING,
    message: str = "test issue",
    line: int = 10,
    suggestion: str = None,
) -> CodeIssue:
    return CodeIssue(
        category=IssueCategory.STYLE,
        level=level,
        message=message,
        file_path=Path("/tmp/test.py"),
        line_number=line,
        suggestion=suggestion,
    )


def _make_result(*issues: CodeIssue) -> AnalysisResult:
    fm = FileMetrics(
        file_path=Path("/tmp/test.py"),
        lines_of_code=100,
        comment_lines=5,
        blank_lines=10,
        complexity=1.0,
        maintainability_index=80.0,
        functions=3,
        classes=0,
        issues=list(issues),
    )
    return AnalysisResult(
        file_metrics=[fm],
        total_files=1,
        total_issues=len(issues),
    )


def _sample_result() -> AnalysisResult:
    """Result with issues in 3 severity groups: critical(1), warning(2), info(1)."""
    return _make_result(
        _make_issue(IssueLevel.CRITICAL, "critical bug", 5, "fix it now"),
        _make_issue(IssueLevel.WARNING, "unused var", 10),
        _make_issue(IssueLevel.WARNING, "magic number", 20, "use a constant"),
        _make_issue(IssueLevel.INFO, "consider docstring", 30),
    )


# ── TuiState creation ───────────────────────────────────────────────


class TestTuiState:
    def test_initial_state_is_summary_screen(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups)
        assert state.screen == "summary"
        assert state.cursor == 0

    def test_groups_only_contain_nonempty_severities(self):
        result = _make_result(
            _make_issue(IssueLevel.CRITICAL, "one"),
            _make_issue(IssueLevel.INFO, "two"),
        )
        groups = _build_tui_groups(result)
        # Only critical and info should appear (no warning, no error)
        level_names = [g[0] for g in groups]
        assert "critical" in level_names
        assert "info" in level_names
        assert "warning" not in level_names
        assert "error" not in level_names

    def test_groups_are_ordered_by_severity(self):
        groups = _build_tui_groups(_sample_result())
        level_names = [g[0] for g in groups]
        assert level_names == ["critical", "warning", "info"]

    def test_expanded_set_starts_empty(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups)
        assert state.expanded == set()


# ── Summary screen navigation ───────────────────────────────────────


class TestSummaryNavigation:
    def test_arrow_down_moves_cursor(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups)
        new = _handle_key(state, KEY_DOWN)
        assert new.cursor == 1

    def test_arrow_up_moves_cursor(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups, cursor=2)
        new = _handle_key(state, KEY_UP)
        assert new.cursor == 1

    def test_arrow_up_at_top_stays_at_zero(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups, cursor=0)
        new = _handle_key(state, KEY_UP)
        assert new.cursor == 0

    def test_arrow_down_at_bottom_stays(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups, cursor=len(groups) - 1)
        new = _handle_key(state, KEY_DOWN)
        assert new.cursor == len(groups) - 1

    def test_enter_drills_into_group(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups, cursor=0)  # cursor on "critical"
        new = _handle_key(state, KEY_ENTER)
        assert new.screen == "group"
        assert new.current_group == 0
        assert new.cursor == 0  # reset to first issue in group

    def test_q_signals_quit(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups)
        new = _handle_key(state, "q")
        assert new.quit is True


# ── Group screen navigation ─────────────────────────────────────────


class TestGroupNavigation:
    def _group_state(self) -> TuiState:
        groups = _build_tui_groups(_sample_result())
        return TuiState(groups=groups, screen="group", current_group=1, cursor=0)
        # current_group=1 is "warning" which has 2 issues

    def test_arrow_down_moves_between_issues(self):
        state = self._group_state()
        new = _handle_key(state, KEY_DOWN)
        assert new.cursor == 1

    def test_arrow_down_at_last_issue_stays(self):
        state = self._group_state()
        state = TuiState(**{**state.__dict__, "cursor": 1})
        new = _handle_key(state, KEY_DOWN)
        assert new.cursor == 1

    def test_enter_toggles_expand(self):
        state = self._group_state()
        # First Enter expands issue 0
        new = _handle_key(state, KEY_ENTER)
        assert (1, 0) in new.expanded  # (group_idx, issue_idx)

        # Second Enter collapses it
        new2 = _handle_key(new, KEY_ENTER)
        assert (1, 0) not in new2.expanded

    def test_b_goes_back_to_summary(self):
        state = self._group_state()
        new = _handle_key(state, "b")
        assert new.screen == "summary"
        # Cursor should return to the group we were viewing
        assert new.cursor == 1

    def test_n_goes_to_next_group(self):
        state = self._group_state()  # group 1 (warning)
        new = _handle_key(state, "n")
        assert new.screen == "group"
        assert new.current_group == 2  # info
        assert new.cursor == 0

    def test_n_at_last_group_stays(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(
            groups=groups,
            screen="group",
            current_group=len(groups) - 1,
            cursor=0,
        )
        new = _handle_key(state, "n")
        assert new.current_group == len(groups) - 1

    def test_p_goes_to_prev_group(self):
        state = self._group_state()  # group 1 (warning)
        new = _handle_key(state, "p")
        assert new.screen == "group"
        assert new.current_group == 0  # critical
        assert new.cursor == 0

    def test_p_at_first_group_stays(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups, screen="group", current_group=0, cursor=0)
        new = _handle_key(state, "p")
        assert new.current_group == 0

    def test_q_signals_quit_from_group(self):
        state = self._group_state()
        new = _handle_key(state, "q")
        assert new.quit is True


# ── Edge cases ───────────────────────────────────────────────────────


class TestEdgeCases:
    def test_unknown_key_is_ignored(self):
        groups = _build_tui_groups(_sample_result())
        state = TuiState(groups=groups, cursor=1)
        new = _handle_key(state, "x")
        assert new == state  # unchanged

    def test_empty_result_produces_no_groups(self):
        result = _make_result()  # no issues
        groups = _build_tui_groups(result)
        assert groups == []
