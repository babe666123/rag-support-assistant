import unittest

from eval_retrieval import evaluate_cases


class EvalRetrievalTests(unittest.TestCase):
    def test_evaluate_cases_counts_passed_and_failed_cases(self):
        chunks = [
            {
                "id": "api-key-and-auth.md#1",
                "source": "api-key-and-auth.md",
                "text": "接口返回 401 时，请检查 API Key。",
                "tokens": ["401", "api", "key"],
                "vector": {"401": 1, "api": 1, "key": 1},
            },
            {
                "id": "rate-limit-and-timeout.md#1",
                "source": "rate-limit-and-timeout.md",
                "text": "429 表示请求触发了平台限流。",
                "tokens": ["429"],
                "vector": {"429": 1},
            },
        ]
        cases = [
            {"question": "接口返回 401 怎么办？", "expected_source": "api-key-and-auth.md"},
            {"question": "Webhook 没有收到回调怎么办？", "expected_source": "webhook-and-sync.md"},
        ]

        report = evaluate_cases(cases, chunks)

        self.assertEqual(report["total"], 2)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 1)
        self.assertTrue(report["results"][0]["passed"])
        self.assertFalse(report["results"][1]["passed"])


if __name__ == "__main__":
    unittest.main()
