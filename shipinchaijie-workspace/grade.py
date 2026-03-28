#!/usr/bin/env python3
"""
Grader script for video-breakdown skill evaluation
"""
import json
import os
import sys
from pathlib import Path

def grade_assertions(output_dir, assertions, eval_name):
    """Grade a single test case against its assertions"""
    results = {
        "expectations": [],
        "summary": {
            "passed": 0,
            "failed": 0,
            "total": len(assertions),
            "pass_rate": 0.0
        }
    }

    # Get all output files
    output_path = Path(output_dir)
    if not output_path.exists():
        print(f"Warning: Output directory does not exist: {output_dir}")
        for assertion in assertions:
            results["expectations"].append({
                "text": assertion,
                "passed": False,
                "evidence": "Output directory not found"
            })
        return results

    output_files = list(output_path.glob("*"))
    if not output_files:
        print(f"Warning: No output files found in {output_dir}")
        for assertion in assertions:
            results["expectations"].append({
                "text": assertion,
                "passed": False,
                "evidence": "No output files generated"
            })
        return results

    # Read all output content
    all_content = ""
    for file_path in output_files:
        if file_path.is_file():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    all_content += f.read() + "\n"
            except Exception as e:
                print(f"Warning: Could not read {file_path}: {e}")

    # Grade each assertion
    for assertion in assertions:
        passed, evidence = check_assertion(assertion, all_content, output_files, eval_name)
        results["expectations"].append({
            "text": assertion,
            "passed": passed,
            "evidence": evidence
        })
        if passed:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1

    results["summary"]["pass_rate"] = results["summary"]["passed"] / results["summary"]["total"] if results["summary"]["total"] > 0 else 0.0

    return results

def check_assertion(assertion, content, output_files, eval_name):
    """Check if an assertion is met"""
    assertion_lower = assertion.lower()
    content_lower = content.lower()

    # Check for file location
    if "输出文件保存在 output 目录" in assertion:
        # For with_skill runs, check if files were saved to the skill's output directory
        # For this test, we're checking if files exist in the outputs directory
        if output_files:
            return True, f"Found {len(output_files)} output file(s)"
        return False, "No output files found"

    # Check for structure elements
    if "总述区" in assertion and "时间线区" in assertion:
        has_overview = "总述区" in content or "核心主题" in content or "角色设定" in content
        has_timeline = "时间线区" in content or "0-" in content or "秒" in content
        if has_overview and has_timeline:
            return True, "Found both overview and timeline sections"
        return False, f"Missing sections - overview: {has_overview}, timeline: {has_timeline}"

    # Check for time segments
    if "时间线区至少有" in assertion and "个时间段" in assertion:
        import re
        # Extract expected number
        match = re.search(r'至少有(\d+)个时间段', assertion)
        if match:
            expected_count = int(match.group(1))
            # Count time markers like "0-2秒", "2-4秒", etc.
            time_markers = re.findall(r'\d+[-~]\d+[秒s]', content)
            actual_count = len(time_markers)
            if actual_count >= expected_count:
                return True, f"Found {actual_count} time segments (expected >= {expected_count})"
            return False, f"Found only {actual_count} time segments (expected >= {expected_count})"

    # Check for specific content keywords
    keywords_to_check = {
        "光线描述": ["阳光", "光线", "照射", "透过"],
        "角色动作描述": ["抬头", "微笑", "动作"],
        "场景描述": ["咖啡厅", "场景"],
        "禁止出现文字": ["禁止", "字幕", "logo", "水印"],
        "@引用系统": ["@图片", "@视频", "@音频", "@"],
        "参考素材清单": ["参考素材", "素材清单", "图片生成"],
        "图片生成提示词": ["图片", "生成", "提示词"],
        "赛博朋克": ["赛博朋克", "cyberpunk", "科幻"],
        "银发机械少女": ["银发", "机械", "少女"],
        "数据球": ["数据球", "能量球"],
        "能量蔓延": ["能量", "蔓延", "扩散"],
        "手部特效": ["手部", "手", "特效"],
        "渐进规则": ["渐进", "自然状态", "逐渐"],
        "竹林": ["竹林", "竹子"],
        "白衣剑客": ["白衣", "剑客", "剑士"],
        "仙剑": ["仙剑", "宝剑", "剑"],
        "古风仙侠": ["古风", "仙侠", "武侠"],
        "火系法师": ["火系", "火焰", "法师"],
        "水系法师": ["水系", "水流", "法师"],
        "雷系法师": ["雷系", "雷电", "法师"],
        "三个独立": ["三个", "独立"],
        "法杖": ["法杖", "权杖"],
        "火焰": ["火焰", "火"],
    }

    for key, keywords in keywords_to_check.items():
        if key in assertion:
            found = any(kw in content_lower for kw in keywords)
            if found:
                matched = [kw for kw in keywords if kw in content_lower]
                return True, f"Found keywords: {', '.join(matched)}"
            return False, f"Missing expected keywords related to '{key}'"

    # Check for remix/复刻 in filename
    if "remix" in assertion_lower or "复刻" in assertion:
        filenames = [f.name.lower() for f in output_files]
        has_remix = any("remix" in fn or "复刻" in fn for fn in filenames)
        if has_remix:
            return True, "Filename contains 'remix' or '复刻'"
        return False, "Filename does not contain 'remix' or '复刻'"

    # Default: check if assertion text appears in content
    if any(word in content_lower for word in assertion_lower.split()):
        return True, "Found related content in output"

    return False, "Could not verify this assertion"

def main():
    if len(sys.argv) < 4:
        print("Usage: python grade.py <workspace_dir> <eval_name> <config>")
        print("  config: 'with_skill' or 'without_skill'")
        sys.exit(1)

    workspace_dir = sys.argv[1]
    eval_name = sys.argv[2]
    config = sys.argv[3]

    # Load eval metadata
    eval_dir = Path(workspace_dir) / eval_name
    metadata_file = eval_dir / "eval_metadata.json"

    if not metadata_file.exists():
        print(f"Error: Metadata file not found: {metadata_file}")
        sys.exit(1)

    with open(metadata_file, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    assertions = metadata.get("assertions", [])

    # Grade the output
    output_dir = eval_dir / config / "outputs"
    results = grade_assertions(str(output_dir), assertions, eval_name)

    # Save grading results
    grading_file = eval_dir / config / "grading.json"
    with open(grading_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"Graded {eval_name} ({config}): {results['summary']['passed']}/{results['summary']['total']} passed ({results['summary']['pass_rate']:.1%})")
    print(f"Results saved to: {grading_file}")

if __name__ == "__main__":
    main()
