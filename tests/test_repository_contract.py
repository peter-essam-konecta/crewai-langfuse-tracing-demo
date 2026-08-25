"""Regression checks that keep documentation aligned with maintained code."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
CANONICAL_DOCS = (
    REPOSITORY_ROOT / "AGENTS.md",
    REPOSITORY_ROOT / "docs" / "developer-guide.md",
    REPOSITORY_ROOT / "docs" / "trace-schema-contract.md",
    REPOSITORY_ROOT / "docs" / "trace-verification-and-evidence.md",
)


class RepositoryContractTests(unittest.TestCase):
    def test_document_set_is_focused(self) -> None:
        expected = {
            "architecture-decisions-and-faq.md",
            "developer-guide.md",
            "implementation-handoff.md",
            "trace-schema-contract.md",
            "trace-verification-and-evidence.md",
            "troubleshooting.md",
        }
        actual = {path.name for path in (REPOSITORY_ROOT / "docs").glob("*.md")}
        self.assertEqual(actual, expected)

    def test_retired_proxy_paths_stay_out_of_main(self) -> None:
        retired_paths = (
            "requirements-proxy.txt",
            "litellm-proxy/config.yaml",
            "litellm-proxy/config.v3-cloud.yaml",
            "litellm-proxy/v3_cost_mapper.py",
            "scripts/setup-litellm-proxy.ps1",
            "scripts/start-litellm-proxy.ps1",
            "scripts/start-v3-cloud-proxy.ps1",
            "scripts/inspect-v3-compliance.ps1",
            "scripts/test-litellm-proxy.ps1",
            "tests/test_litellm_v3_cost_mapper.py",
        )
        present = [path for path in retired_paths if (REPOSITORY_ROOT / path).exists()]
        self.assertEqual(present, [], "Retired paths restored to main: " + ", ".join(present))

    def test_relative_markdown_links_resolve(self) -> None:
        link_pattern = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
        missing: list[str] = []

        for markdown_file in REPOSITORY_ROOT.rglob("*.md"):
            if any(part in {".venv", ".proxy-venv"} for part in markdown_file.parts):
                continue
            for target in link_pattern.findall(markdown_file.read_text(encoding="utf-8")):
                target = target.strip().strip("<>").split("#", 1)[0]
                if not target or "://" in target or target.startswith("mailto:"):
                    continue
                if not (markdown_file.parent / target).resolve().exists():
                    missing.append(f"{markdown_file.relative_to(REPOSITORY_ROOT)} -> {target}")

        self.assertEqual(missing, [], "Broken relative Markdown links: " + ", ".join(missing))

    def test_documented_imports_use_real_interfaces(self) -> None:
        text = "\n".join(path.read_text(encoding="utf-8") for path in CANONICAL_DOCS)
        prohibited_patterns = (
            r"import\s+init_tracing",
            r"import\s+observe_crew_failures",
            r"import\s+observe_child_operation",
        )
        for pattern in prohibited_patterns:
            self.assertIsNone(re.search(pattern, text), f"Outdated documented API: {pattern}")

        self.assertIn("configure_tracing", text)
        self.assertIn("FailureAdapter", text)
        self.assertIn("CompositeToolAdapter.run_child", text)

    def test_schema_documents_exact_adapter_attributes(self) -> None:
        schema = (REPOSITORY_ROOT / "docs" / "trace-schema-contract.md").read_text(
            encoding="utf-8"
        )
        failure_source = (
            REPOSITORY_ROOT / "src" / "crewai_langfuse_demo" / "adapters" / "failure.py"
        ).read_text(encoding="utf-8")
        composite_source = (
            REPOSITORY_ROOT
            / "src"
            / "crewai_langfuse_demo"
            / "adapters"
            / "composite_tool.py"
        ).read_text(encoding="utf-8")

        expected_failure = (
            "kolibri.failure.tool.name",
            "error.type",
            "kolibri.failure.error.type",
            "kolibri.failure.retry.count",
            "kolibri.failure.final.outcome",
        )
        expected_composite = (
            "kolibri.composite.parent.tool.name",
            "kolibri.composite.child.operation.name",
            "kolibri.composite.child.final.outcome",
        )
        for attribute in expected_failure:
            self.assertIn(attribute, failure_source)
            self.assertIn(attribute, schema)
        for attribute in expected_composite:
            self.assertIn(attribute, composite_source)
            self.assertIn(attribute, schema)

    def test_historical_composite_trace_is_not_delegation_evidence(self) -> None:
        evidence = (
            REPOSITORY_ROOT / "docs" / "trace-verification-and-evidence.md"
        ).read_text(encoding="utf-8")
        for line in evidence.splitlines():
            if "0edbf7991a3fc7b45817d81b95eff248" in line:
                self.assertNotIn("| Agent Delegation |", line)

    def test_tests_use_standard_unittest_runner(self) -> None:
        runner = (REPOSITORY_ROOT / "scripts" / "run-tests.ps1").read_text(encoding="utf-8")
        requirements = (REPOSITORY_ROOT / "requirements.txt").read_text(encoding="utf-8")
        self.assertIn("-m unittest discover", runner)
        self.assertNotIn("pytest", requirements.lower())

    def test_trace_checker_delegates_to_schema_first_validator(self) -> None:
        checker = (REPOSITORY_ROOT / "scripts" / "check-trace.ps1").read_text(
            encoding="utf-8"
        )
        validator = (
            REPOSITORY_ROOT / "src" / "crewai_langfuse_demo" / "trace_validation.py"
        ).read_text(encoding="utf-8")

        self.assertIn("crewai_langfuse_demo.trace_validation", checker)
        self.assertNotIn("$_.name -eq 'Tool Usage'", checker)
        self.assertIn('operation == "execute_tool"', validator)
        self.assertIn('attributes.get("gen_ai.tool.name")', validator)
        self.assertIn('name in {"Tool Usage", "Tool Usage Error"}', validator)


if __name__ == "__main__":
    unittest.main()
