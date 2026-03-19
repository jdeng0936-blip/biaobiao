"""
LLM Provider 层单元测试
覆盖：
  1. ModelConfig / LLMResponse dataclass 校验
  2. BaseLLMProvider 接口约束
  3. GeminiProvider is_ready / 初始化行为
  4. LLMSelector 路由选择
严禁调用真实 Gemini/OpenAI API。
"""
import unittest
import asyncio
from unittest.mock import patch, MagicMock


# ============================================================
# ModelConfig dataclass 测试
# ============================================================
class TestModelConfig(unittest.TestCase):
    """ModelConfig 数据配置"""

    def test_defaults(self):
        from app.llm.providers.base import ModelConfig
        cfg = ModelConfig(provider="gemini", model_name="gemini-2.0-flash")
        self.assertEqual(cfg.temperature, 0.3)
        self.assertEqual(cfg.max_output_tokens, 4096)
        self.assertEqual(cfg.timeout_seconds, 60)
        self.assertEqual(cfg.task_type, "")

    def test_custom_values(self):
        from app.llm.providers.base import ModelConfig
        cfg = ModelConfig(
            provider="openai",
            model_name="gpt-4",
            temperature=0.7,
            max_output_tokens=8192,
            timeout_seconds=120,
            task_type="generation",
        )
        self.assertEqual(cfg.provider, "openai")
        self.assertEqual(cfg.temperature, 0.7)
        self.assertEqual(cfg.task_type, "generation")


# ============================================================
# LLMResponse dataclass 测试
# ============================================================
class TestLLMResponse(unittest.TestCase):
    """LLMResponse 统一响应"""

    def test_basic(self):
        from app.llm.providers.base import LLMResponse
        resp = LLMResponse(text="生成内容", model="gemini-2.0-flash")
        self.assertEqual(resp.text, "生成内容")
        self.assertIsNone(resp.usage)

    def test_with_usage(self):
        from app.llm.providers.base import LLMResponse
        resp = LLMResponse(
            text="输出",
            model="gpt-4",
            usage={"prompt_tokens": 100, "completion_tokens": 200},
        )
        self.assertEqual(resp.usage["prompt_tokens"], 100)


# ============================================================
# BaseLLMProvider 抽象接口测试
# ============================================================
class TestBaseLLMProvider(unittest.TestCase):
    """BaseLLMProvider 接口约束"""

    def test_cannot_instantiate_directly(self):
        from app.llm.providers.base import BaseLLMProvider
        with self.assertRaises(TypeError):
            BaseLLMProvider()

    def test_embed_not_implemented(self):
        """默认 embed 抛出 NotImplementedError"""
        from app.llm.providers.base import BaseLLMProvider

        class DummyProvider(BaseLLMProvider):
            def is_ready(self): return True
            async def generate(self, sp, up, cfg): ...
            async def generate_stream(self, sp, up, cfg): yield ""

        provider = DummyProvider()
        with self.assertRaises(NotImplementedError):
            asyncio.run(provider.embed(["test"], "model"))


# ============================================================
# GeminiProvider 测试 (Mock API)
# ============================================================
class TestGeminiProvider(unittest.TestCase):
    """GeminiProvider 初始化与 is_ready"""

    @patch.dict("os.environ", {"GEMINI_API_KEY": ""}, clear=False)
    def test_not_ready_without_key(self):
        """无 API Key 时 is_ready=False"""
        from app.llm.providers.gemini_provider import GeminiProvider
        # 强制重新创建实例
        provider = GeminiProvider.__new__(GeminiProvider)
        provider.api_key = ""
        provider.client = None
        self.assertFalse(provider.is_ready())

    def test_is_ready_with_client(self):
        """有 client 时 is_ready=True"""
        from app.llm.providers.gemini_provider import GeminiProvider
        provider = GeminiProvider.__new__(GeminiProvider)
        provider.client = MagicMock()
        self.assertTrue(provider.is_ready())

    def test_generate_raises_when_not_ready(self):
        """未就绪时 generate 抛出 RuntimeError"""
        from app.llm.providers.gemini_provider import GeminiProvider
        from app.llm.providers.base import ModelConfig
        provider = GeminiProvider.__new__(GeminiProvider)
        provider.client = None
        cfg = ModelConfig(provider="gemini", model_name="gemini-2.0-flash")
        with self.assertRaises(RuntimeError):
            asyncio.run(provider.generate("system", "user", cfg))

    def test_embed_raises_when_not_ready(self):
        """未就绪时 embed 抛出 RuntimeError"""
        from app.llm.providers.gemini_provider import GeminiProvider
        provider = GeminiProvider.__new__(GeminiProvider)
        provider.client = None
        with self.assertRaises(RuntimeError):
            asyncio.run(provider.embed(["test"]))


# ============================================================
# LLMSelector 测试
# ============================================================
class TestLLMSelector(unittest.TestCase):
    """LLMSelector 路由"""

    def test_registry_loaded(self):
        """注册表加载正确"""
        from app.llm.llm_selector import LLMSelector
        selector = LLMSelector.__new__(LLMSelector)
        # 直接读取 yaml
        import yaml
        from pathlib import Path
        yaml_path = Path(__file__).parent / "app" / "llm" / "llm_registry.yaml"
        if yaml_path.exists():
            with open(yaml_path) as f:
                registry = yaml.safe_load(f)
            self.assertIn("tasks", registry)
            self.assertIsInstance(registry["tasks"], dict)

    def test_registry_has_generation_task(self):
        """注册表包含 generation 任务"""
        import yaml
        from pathlib import Path
        yaml_path = Path(__file__).parent / "app" / "llm" / "llm_registry.yaml"
        if yaml_path.exists():
            with open(yaml_path) as f:
                registry = yaml.safe_load(f)
            tasks = registry.get("tasks", {})
            self.assertTrue(
                any("generat" in k.lower() for k in tasks.keys()),
                f"注册表缺少 generation 类任务: {list(tasks.keys())}"
            )


if __name__ == "__main__":
    unittest.main()
