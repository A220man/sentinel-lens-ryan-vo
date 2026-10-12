"""Reproducible CLI command for running the AI/ML semantic locator grounding benchmark."""

import json
import sys
from app.services.evaluation_service import run_semantic_benchmark


def main():
    print("=" * 70)
    print("Sentinel Lens — AI/ML Semantic Locator Grounding Evaluation")
    print("=" * 70)
    print("Evaluating deterministic accessibility hierarchy locator against baseline naive matcher...")
    print("Test Corpus: 8 labeled real-world UI workflows (e-commerce, settings, mobile, auth)")
    print("-" * 70)

    summary, scenarios = run_semantic_benchmark("web")

    print(f"Total Scenarios Evaluated: {summary['total_scenarios']}")
    print(f"Correct Locators Resolved: {summary['correct_count']}")
    print(f"Sentinel Lens Accuracy:    {summary['accuracy']}%")
    print(f"Baseline Matcher Accuracy: {summary['baseline_comparison']['baseline_accuracy']}%")
    print(f"Accuracy Delta:            +{summary['baseline_comparison']['accuracy_improvement']}%")
    print(f"Ambiguity Resolution:      {summary['ambiguity_resolution_rate']}%")
    print(f"Mean Resolution Latency:   {summary['mean_latency_ms']} ms")
    print(f"P95 Resolution Latency:    {summary['latency_p95_ms']} ms")
    print("-" * 70)
    print("Scenario Breakdown:")
    for s in scenarios:
        status_sym = "[PASS]" if s.passed else "[FAIL]"
        amb_sym = "(Ambiguous)" if s.ambiguity_detected else "(Clean)"
        print(f" {status_sym} {s.scenario_id}: {s.name:<32} -> {s.resolved_element:<20} {amb_sym} in {s.latency_ms:.2f}ms")

    print("=" * 70)
    print("Evaluation completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
