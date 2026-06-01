import json
import unittest

from server import (
    AppError,
    build_augmented_messages,
    error_payload,
    retrieve_sources_for_question,
)


class ServerTests(unittest.TestCase):
    def test_build_augmented_messages_includes_sources_and_latest_question(self):
        messages = [{"role": "user", "content": "接口返回 401 怎么办？"}]
        sources = [
            {
                "source": "api-key-and-auth.md",
                "text": "接口返回 401 时，请检查 Authorization 请求头和 API Key。",
            }
        ]

        augmented = build_augmented_messages(messages, sources)

        payload = json.dumps(augmented, ensure_ascii=False)
        self.assertIn("api-key-and-auth.md", payload)
        self.assertIn("接口返回 401", payload)
        self.assertIn("请基于参考资料回答这个问题", payload)

    def test_retrieve_sources_for_question_returns_source_payload(self):
        chunks = [
            {
                "id": "api-key-and-auth.md#1",
                "source": "api-key-and-auth.md",
                "text": "接口返回 401 时，请检查 Authorization 请求头和 API Key。",
                "tokens": ["接口返回", "401", "authorization", "api", "key"],
                "vector": {"401": 1, "api": 1, "key": 1},
            }
        ]

        payload = retrieve_sources_for_question("401 怎么排查？", chunks)

        self.assertEqual(payload["question"], "401 怎么排查？")
        self.assertEqual(payload["sources"][0]["source"], "api-key-and-auth.md")

    def test_error_payload_returns_safe_structured_message(self):
        payload = error_payload(AppError("MODEL_AUTH_MISSING", "请配置 API Key。", 400))

        self.assertEqual(payload["code"], "MODEL_AUTH_MISSING")
        self.assertEqual(payload["message"], "请配置 API Key。")
        self.assertNotIn("DEEPSEEK_API_KEY=", json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
