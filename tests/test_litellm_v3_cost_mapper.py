"""Regression test for the optional LiteLLM Proxy V3 cost mapping."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

from litellm.integrations.otel.mappers.genai import GenAIMapper


_MAPPER_PATH = Path(__file__).resolve().parents[1] / "litellm-proxy" / "v3_cost_mapper.py"


def _load_mapper_module():
    spec = importlib.util.spec_from_file_location("v3_cost_mapper_test", _MAPPER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class LiteLLMV3CostMapperTests(unittest.TestCase):
    def test_installs_the_v3_cost_field_from_litellm_response_cost(self) -> None:
        if not hasattr(GenAIMapper, "_LLM_CALL_ATTRS"):
            self.skipTest("This LiteLLM version does not expose the V2 generation mapper.")

        module = _load_mapper_module()
        module.install()

        mapper = GenAIMapper._LLM_CALL_ATTRS["gen_ai.usage.cost"]
        self.assertEqual(mapper(SimpleNamespace(response_cost=0.0042)), 0.0042)
        self.assertIsNone(mapper(SimpleNamespace(response_cost=None)))
