"""Reproducible CLI command for running the AI/ML semantic locator grounding benchmark."""

import argparse
import json
import sys
from app.services.evaluation_service import run_semantic_benchmark


def run_benchmark_json(target_env: str = "web") -> dict:
    """Runs benchmark and returns results as a JSON-serializable dict for CI/CD."""
    summary, scenarios = run_semantic_benchmark(target_env)
    return {
        "benchmark_name": "semantic_locator_grounding",
        "target": target_env,
        "total_scenarios": summary["total_scenarios"],
        "correct_count": summary["correct_count"],
        "accuracy": summary["accuracy"],
        "baseline_accuracy": summary["baseline_comparison"]["baseline_accuracy"],
        "accuracy_improvement": summary["baseline_comparison"]["accuracy_improvement"],
        "ambiguity_resolution_rate": summary["ambiguity_resolution_rate"],
        "mean_latency_ms": summary["mean_latency_ms"],
        "latency_p95_ms": summary["latency_p95_ms"],
        "scenarios": [
            {
                "scenario_id": s.scenario_id,
                "name": s.name,
                "passed": s.passed,
                "resolved_element": s.resolved_element,
                "expected_element": s.expected_element,
                "ambiguity_detected": s.ambiguity_detected,
                "latency_ms": s.latency_ms,
            }
            for s in scenarios
        ],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Sentinel Lens — AI/ML Semantic Locator Grounding Evaluation"
    )
    parser.add_argument(
        "--target",
        default="web",
        choices=["web", "mobile_android", "mobile_ios"],
        help="Target environment for evaluation",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON for CI/CD integration",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Write JSON output to file (requires --json)",
    )
    args = parser.parse_args()

    if args.json:
        result = run_benchmark_json(args.target)
        json_output = json.dumps(result, indent=2)
        if args.output:
            with open(args.output, "w") as f:
                f.write(json_output)
        else:
            print(json_output)
        return 0

    print("=" * 70)
    print("Sentinel Lens — AI/ML Semantic Locator Grounding Evaluation")
    print("=" * 70)
    print("Evaluating deterministic accessibility hierarchy locator against baseline naive matcher...")
    print("Test Corpus: 8 labeled real-world UI workflows (e-commerce, settings, mobile, auth)")
    print("-" * 70)

    summary, scenarios = run_semantic_benchmark(args.target)

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

