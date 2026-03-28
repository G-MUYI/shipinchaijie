#!/usr/bin/env python3
"""
Generate benchmark report from test results
"""
import json
import os
from pathlib import Path
from datetime import datetime

def load_json(file_path):
    """Load JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {file_path}: {e}")
        return None

def generate_benchmark(workspace_dir):
    """Generate benchmark.json from all test results"""
    workspace = Path(workspace_dir)

    # Find all eval directories
    eval_dirs = [d for d in workspace.iterdir() if d.is_dir() and (d / "eval_metadata.json").exists()]

    benchmark = {
        "metadata": {
            "skill_name": "video-breakdown",
            "skill_path": str(Path(workspace).parent / "shipinchaijie"),
            "timestamp": datetime.now().isoformat(),
            "evals_run": [],
            "runs_per_configuration": 1
        },
        "runs": [],
        "run_summary": {
            "with_skill": {
                "pass_rate": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
                "time_seconds": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            },
            "without_skill": {
                "pass_rate": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
                "time_seconds": {"mean": 0, "stddev": 0, "min": 0, "max": 0},
                "tokens": {"mean": 0, "stddev": 0, "min": 0, "max": 0}
            },
            "delta": {
                "pass_rate": "",
                "time_seconds": "",
                "tokens": ""
            }
        },
        "notes": []
    }

    # Collect all runs
    with_skill_stats = {"pass_rates": [], "times": [], "tokens": []}
    without_skill_stats = {"pass_rates": [], "times": [], "tokens": []}

    for eval_dir in sorted(eval_dirs):
        metadata = load_json(eval_dir / "eval_metadata.json")
        if not metadata:
            continue

        eval_name = metadata.get("eval_name", eval_dir.name)
        eval_id = metadata.get("eval_id", 0)
        benchmark["metadata"]["evals_run"].append(eval_name)

        # Process both configurations
        for config in ["with_skill", "without_skill"]:
            grading_file = eval_dir / config / "grading.json"
            timing_file = eval_dir / config / "timing.json"

            grading = load_json(grading_file)
            timing = load_json(timing_file)

            if not grading or not timing:
                continue

            run_data = {
                "eval_id": eval_id,
                "eval_name": eval_name,
                "configuration": config,
                "run_number": 1,
                "result": {
                    "pass_rate": grading["summary"]["pass_rate"],
                    "passed": grading["summary"]["passed"],
                    "failed": grading["summary"]["failed"],
                    "total": grading["summary"]["total"],
                    "time_seconds": timing["total_duration_seconds"],
                    "tokens": timing["total_tokens"],
                    "tool_calls": 0,
                    "errors": 0
                },
                "expectations": grading["expectations"],
                "notes": []
            }

            benchmark["runs"].append(run_data)

            # Collect stats
            stats = with_skill_stats if config == "with_skill" else without_skill_stats
            stats["pass_rates"].append(grading["summary"]["pass_rate"])
            stats["times"].append(timing["total_duration_seconds"])
            stats["tokens"].append(timing["total_tokens"])

    # Calculate summary statistics
    def calc_stats(values):
        if not values:
            return {"mean": 0, "stddev": 0, "min": 0, "max": 0}
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values) if len(values) > 1 else 0
        stddev = variance ** 0.5
        return {
            "mean": round(mean, 2),
            "stddev": round(stddev, 2),
            "min": round(min(values), 2),
            "max": round(max(values), 2)
        }

    benchmark["run_summary"]["with_skill"]["pass_rate"] = calc_stats(with_skill_stats["pass_rates"])
    benchmark["run_summary"]["with_skill"]["time_seconds"] = calc_stats(with_skill_stats["times"])
    benchmark["run_summary"]["with_skill"]["tokens"] = calc_stats(with_skill_stats["tokens"])

    benchmark["run_summary"]["without_skill"]["pass_rate"] = calc_stats(without_skill_stats["pass_rates"])
    benchmark["run_summary"]["without_skill"]["time_seconds"] = calc_stats(without_skill_stats["times"])
    benchmark["run_summary"]["without_skill"]["tokens"] = calc_stats(without_skill_stats["tokens"])

    # Calculate deltas
    ws_pr = benchmark["run_summary"]["with_skill"]["pass_rate"]["mean"]
    wo_pr = benchmark["run_summary"]["without_skill"]["pass_rate"]["mean"]
    ws_time = benchmark["run_summary"]["with_skill"]["time_seconds"]["mean"]
    wo_time = benchmark["run_summary"]["without_skill"]["time_seconds"]["mean"]
    ws_tokens = benchmark["run_summary"]["with_skill"]["tokens"]["mean"]
    wo_tokens = benchmark["run_summary"]["without_skill"]["tokens"]["mean"]

    benchmark["run_summary"]["delta"]["pass_rate"] = f"+{ws_pr - wo_pr:.2f}" if ws_pr >= wo_pr else f"{ws_pr - wo_pr:.2f}"
    benchmark["run_summary"]["delta"]["time_seconds"] = f"+{ws_time - wo_time:.1f}" if ws_time >= wo_time else f"{ws_time - wo_time:.1f}"
    benchmark["run_summary"]["delta"]["tokens"] = f"+{int(ws_tokens - wo_tokens)}"

    # Add analysis notes
    benchmark["notes"].append(f"With-skill average pass rate: {ws_pr:.1%} vs without-skill: {wo_pr:.1%} (delta: {ws_pr - wo_pr:+.1%})")
    benchmark["notes"].append(f"With-skill average time: {ws_time:.1f}s vs without-skill: {wo_time:.1f}s (delta: {ws_time - wo_time:+.1f}s)")
    benchmark["notes"].append(f"With-skill average tokens: {int(ws_tokens)} vs without-skill: {int(wo_tokens)} (delta: {int(ws_tokens - wo_tokens):+d})")

    if ws_pr > wo_pr:
        benchmark["notes"].append(f"✅ Skill improves pass rate by {(ws_pr - wo_pr):.1%}")
    else:
        benchmark["notes"].append(f"⚠️ Skill does not improve pass rate (delta: {(ws_pr - wo_pr):.1%})")

    return benchmark

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generate_benchmark.py <workspace_dir>")
        sys.exit(1)

    workspace_dir = sys.argv[1]
    benchmark = generate_benchmark(workspace_dir)

    # Save benchmark.json
    output_file = Path(workspace_dir) / "benchmark.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(benchmark, f, indent=2, ensure_ascii=False)

    print(f"Benchmark report generated: {output_file}")
    print(f"\nSummary:")
    print(f"  With-skill pass rate: {benchmark['run_summary']['with_skill']['pass_rate']['mean']:.1%}")
    print(f"  Without-skill pass rate: {benchmark['run_summary']['without_skill']['pass_rate']['mean']:.1%}")
    print(f"  Delta: {benchmark['run_summary']['delta']['pass_rate']}")

if __name__ == "__main__":
    main()
