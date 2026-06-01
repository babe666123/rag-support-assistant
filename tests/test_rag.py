import tempfile
import unittest
from pathlib import Path

from rag import (
    build_knowledge_base,
    chunk_text,
    retrieve_relevant_chunks,
    tokenize,
)


class RagTests(unittest.TestCase):
    def test_tokenize_keeps_chinese_terms_and_ascii_words(self):
        tokens = tokenize("API Key 无效，返回 401 Unauthorized")

        self.assertIn("api", tokens)
        self.assertIn("key", tokens)
        self.assertIn("401", tokens)
        self.assertIn("无效", tokens)

    def test_tokenize_adds_chinese_bigrams_for_recall(self):
        tokens = tokenize("本地部署后无法调用模型")

        self.assertIn("本地", tokens)
        self.assertIn("部署", tokens)
        self.assertIn("调用", tokens)
        self.assertIn("模型", tokens)

    def test_chunk_text_splits_long_content_with_overlap(self):
        text = "第一段内容。" * 80

        chunks = chunk_text(text, max_chars=120, overlap=20)

        self.assertGreater(len(chunks), 1)
        self.assertLessEqual(len(chunks[0]), 120)
        self.assertEqual(chunks[0][-20:], chunks[1][:20])

    def test_retrieve_relevant_chunks_returns_best_matching_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "api-key.md").write_text(
                "# API Key 问题\n\n如果接口返回 401，请检查 API Key 是否正确配置。",
                encoding="utf-8",
            )
            (root / "billing.md").write_text(
                "# 计费问题\n\n套餐额度用完后，需要升级套餐或等待下个计费周期。",
                encoding="utf-8",
            )

            chunks = build_knowledge_base(root, max_chars=160, overlap=20)
            results = retrieve_relevant_chunks("接口 401 是什么原因？", chunks, limit=1)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["source"], "api-key.md")
        self.assertIn("401", results[0]["text"])


if __name__ == "__main__":
    unittest.main()
