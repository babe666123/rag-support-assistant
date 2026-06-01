from pathlib import Path

from rag import build_knowledge_base, retrieve_relevant_chunks


ROOT = Path(__file__).parent
KNOWLEDGE_BASE_DIR = ROOT / "knowledge_base"

DEFAULT_CASES = [
    {"question": "接口返回 401 怎么办？", "expected_source": "api-key-and-auth.md"},
    {"question": "403 和 401 有什么区别？", "expected_source": "api-key-and-auth.md"},
    {"question": "请求太多返回 429 怎么处理？", "expected_source": "rate-limit-and-timeout.md"},
    {"question": "Webhook 没有收到回调怎么办？", "expected_source": "webhook-and-sync.md"},
    {"question": "本地部署后无法调用模型怎么排查？", "expected_source": "billing-and-deployment.md"},
]


def evaluate_cases(cases, chunks):
    results = []
    for case in cases:
        sources = retrieve_relevant_chunks(case["question"], chunks, limit=3)
        matched_sources = [source["source"] for source in sources]
        passed = case["expected_source"] in matched_sources
        results.append(
            {
                "question": case["question"],
                "expected_source": case["expected_source"],
                "matched_sources": matched_sources,
                "passed": passed,
            }
        )

    passed_count = sum(1 for result in results if result["passed"])
    return {
        "total": len(results),
        "passed": passed_count,
        "failed": len(results) - passed_count,
        "results": results,
    }


def print_report(report):
    for result in report["results"]:
        status = "PASS" if result["passed"] else "FAIL"
        matched = ", ".join(result["matched_sources"]) or "no match"
        print(f"[{status}] {result['question']} -> {matched}")

    print()
    print(f"Total: {report['total']}, Passed: {report['passed']}, Failed: {report['failed']}")


def main():
    chunks = build_knowledge_base(KNOWLEDGE_BASE_DIR)
    report = evaluate_cases(DEFAULT_CASES, chunks)
    print_report(report)
    raise SystemExit(0 if report["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
