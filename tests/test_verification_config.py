"""Tests for the configurable verification pipeline."""

from pathlib import Path

import pytest

from refactron.core.config import RefactronConfig, VerificationConfig
from refactron.verification.checks.test_gate import TestSuiteGate
from refactron.verification.engine import VerificationEngine


class TestVerificationConfigDefaults:
    def test_defaults_match_historical_behaviour(self):
        cfg = VerificationConfig()
        assert cfg.enabled_checks == ["syntax", "import_integrity", "test_gate"]
        assert cfg.short_circuit is True
        assert cfg.test_gate_timeout_sec == 45
        assert cfg.pytest_extra_args == []

    def test_refactron_config_has_verification_section(self):
        cfg = RefactronConfig.default()
        assert isinstance(cfg.verification, VerificationConfig)
        assert cfg.verification.enabled_checks == [
            "syntax",
            "import_integrity",
            "test_gate",
        ]


class TestEngineHonoursConfig:
    def test_enabled_checks_subset(self):
        cfg = VerificationConfig(enabled_checks=["syntax", "import_integrity"])
        engine = VerificationEngine(config=cfg)
        assert [c.name for c in engine.checks] == ["syntax", "import_integrity"]

    def test_enabled_checks_ordering_respected(self):
        cfg = VerificationConfig(enabled_checks=["test_gate", "syntax"])
        engine = VerificationEngine(config=cfg)
        assert [c.name for c in engine.checks] == ["test_gate", "syntax"]

    def test_unknown_check_raises(self):
        cfg = VerificationConfig(enabled_checks=["syntax", "bogus_check"])
        with pytest.raises(ValueError, match="Unknown verification check"):
            VerificationEngine(config=cfg)

    def test_test_gate_timeout_threaded_from_config(self):
        cfg = VerificationConfig(test_gate_timeout_sec=120, pytest_extra_args=["-p", "no:randomly"])
        engine = VerificationEngine(config=cfg)
        gate = next(c for c in engine.checks if c.name == "test_gate")
        assert gate.timeout_sec == 120
        assert gate.pytest_extra_args == ["-p", "no:randomly"]

    def test_short_circuit_default_taken_from_config(self):
        cfg = VerificationConfig(short_circuit=False, enabled_checks=["syntax"])
        engine = VerificationEngine(config=cfg)
        # verify() with short_circuit=None must fall back to the config value.
        result = engine.verify("x = (", "y = (", Path("/tmp/t.py"))
        assert result.safe_to_apply is False  # syntax fails on both

    def test_explicit_checks_bypass_config(self):
        cfg = VerificationConfig(enabled_checks=["syntax"])
        engine = VerificationEngine(checks=[], config=cfg)
        assert engine.checks == []


class TestTestSuiteGateConfig:
    def test_defaults_preserved(self):
        gate = TestSuiteGate()
        assert gate.timeout_sec == 45
        assert gate.pytest_extra_args == []

    def test_custom_values_stored(self):
        gate = TestSuiteGate(timeout_sec=10, pytest_extra_args=["-k", "fast"])
        assert gate.timeout_sec == 10
        assert gate.pytest_extra_args == ["-k", "fast"]


class TestConfigFileRoundTrip:
    def test_verification_section_loaded_from_yaml(self, tmp_path):
        config_file = tmp_path / "refactron.yaml"
        config_file.write_text(
            "verification:\n"
            "  enabled_checks: [syntax, import_integrity]\n"
            "  short_circuit: false\n"
            "  test_gate_timeout_sec: 90\n"
            "  pytest_extra_args: ['-p', 'no:cacheprovider']\n",
            encoding="utf-8",
        )
        cfg = RefactronConfig.from_file(config_file)
        assert isinstance(cfg.verification, VerificationConfig)
        assert cfg.verification.enabled_checks == ["syntax", "import_integrity"]
        assert cfg.verification.short_circuit is False
        assert cfg.verification.test_gate_timeout_sec == 90
        assert cfg.verification.pytest_extra_args == ["-p", "no:cacheprovider"]

    def test_missing_section_uses_defaults(self, tmp_path):
        """Existing configs with no `verification:` section need no migration."""
        config_file = tmp_path / "refactron.yaml"
        config_file.write_text("max_parameters: 7\n", encoding="utf-8")
        cfg = RefactronConfig.from_file(config_file)
        assert cfg.verification.enabled_checks == [
            "syntax",
            "import_integrity",
            "test_gate",
        ]
        assert cfg.verification.test_gate_timeout_sec == 45

    def test_to_file_then_from_file_preserves_verification(self, tmp_path):
        config_file = tmp_path / "out.yaml"
        cfg = RefactronConfig.default()
        cfg.verification.test_gate_timeout_sec = 75
        cfg.verification.enabled_checks = ["syntax"]
        cfg.to_file(config_file)

        reloaded = RefactronConfig.from_file(config_file)
        assert reloaded.verification.test_gate_timeout_sec == 75
        assert reloaded.verification.enabled_checks == ["syntax"]
