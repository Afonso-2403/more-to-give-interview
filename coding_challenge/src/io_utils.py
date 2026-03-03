import json
from pathlib import Path

from models import EligibilityResult, Project

def print_project_summary(project: Project) -> None:
    """Print the extracted project summary for user validation."""
    focus = ", ".join(project.focus_areas) if project.focus_areas else "N/A"
    print("\n=== Extracted Project Summary ===")
    print(f"  Name:            {project.name}")
    print(f"  Country:         {project.country}")
    print(f"  Target location: {project.target_location}")
    print(f"  Budget total:    {project.budget_total:,.0f} {project.currency}")
    print(f"  Self-financing:  {project.self_financing:,.0f} {project.currency}")
    print(f"  Funding sought:  {project.funding_sought:,.0f} {project.currency}")
    print(f"  Duration:        {project.duration_months} months (start: {project.start_date})")
    print(f"  Target group:    {project.target_group}")
    print(f"  Focus areas:     {focus}")
    print("=================================\n")


def prompt_validation() -> bool:
    """Ask the user to validate the extracted project summary."""
    while True:
        answer = input("Does this look correct? [Y/n]: ").strip().lower()
        if answer in ("", "y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please enter Y or N.")


def print_result_summary(result: EligibilityResult, index: int, total: int) -> None:
    """Print a single foundation's assessment result."""
    status_map = {
        True: "ELIGIBLE",
        False: "NOT ELIGIBLE",
        None: "UNDETERMINED",
    }
    status = status_map.get(result.eligible, "UNDETERMINED")
    confidence = result.confidence.upper()

    print(f"[{index}/{total}] {result.foundation.name}")
    print(f"  Status:     {status} ({confidence} confidence)")
    print(f"  Reasoning:  {result.reasoning}")

    if result.key_criteria_matched:
        print(f"  Matched:    {', '.join(result.key_criteria_matched)}")
    if result.key_criteria_missed:
        print(f"  Missed:     {', '.join(result.key_criteria_missed)}")
    if result.scrape_errors:
        print(f"  Warnings:   {'; '.join(result.scrape_errors)}")


def print_final_report(results: list[EligibilityResult]) -> None:
    """Print a summary table of all results."""
    eligible = [r for r in results if r.eligible is True]
    not_eligible = [r for r in results if r.eligible is False]
    undetermined = [r for r in results if r.eligible is None]

    print("\n" + "=" * 60)
    print("ELIGIBILITY SUMMARY")
    print("=" * 60)

    if eligible:
        names = [f"{r.foundation.name} ({r.confidence})" for r in eligible]
        print(f"\n  ELIGIBLE ({len(eligible)}):")
        for name in names:
            print(f"    - {name}")

    if not_eligible:
        names = [f"{r.foundation.name} ({r.confidence})" for r in not_eligible]
        print(f"\n  NOT ELIGIBLE ({len(not_eligible)}):")
        for name in names:
            print(f"    - {name}")

    if undetermined:
        names = [f"{r.foundation.name} ({r.confidence})" for r in undetermined]
        print(f"\n  UNDETERMINED ({len(undetermined)}):")
        for name in names:
            print(f"    - {name}")

    print("=" * 60)


def save_output(results: list[EligibilityResult], filename: str) -> Path:
    """Save results to coding_challenge/outputs/<filename>. Supports .json and .md."""
    output_dir = Path(__file__).resolve().parents[1] / "outputs"
    output_dir.mkdir(exist_ok=True)
    filepath = output_dir / filename

    if filename.endswith(".json"):
        data = []
        for r in results:
            data.append({
                "foundation_number": r.foundation.number,
                "foundation_name": r.foundation.name,
                "foundation_url": r.foundation.url,
                "eligible": r.eligible,
                "confidence": r.confidence,
                "reasoning": r.reasoning,
                "key_criteria_matched": r.key_criteria_matched,
                "key_criteria_missed": r.key_criteria_missed,
                "scraped_urls": r.scraped_urls,
                "scrape_errors": r.scrape_errors,
            })
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    elif filename.endswith(".md"):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# Foundation Eligibility Report\n\n")
            f.write("| # | Foundation | Eligible | Confidence |\n")
            f.write("|---|-----------|----------|------------|\n")
            for r in results:
                status = {True: "Yes", False: "No", None: "?"}[r.eligible]
                f.write(f"| {r.foundation.number} | {r.foundation.name} | {status} | {r.confidence} |\n")

            f.write("\n---\n\n## Detailed Assessments\n\n")
            for r in results:
                f.write(f"### {r.foundation.number}. {r.foundation.name}\n\n")
                f.write(f"**URL:** {r.foundation.url}\n\n")
                status = {True: "ELIGIBLE", False: "NOT ELIGIBLE", None: "UNDETERMINED"}[r.eligible]
                f.write(f"**Status:** {status} ({r.confidence} confidence)\n\n")
                f.write(f"**Reasoning:** {r.reasoning}\n\n")
                if r.key_criteria_matched:
                    f.write(f"**Matched:** {', '.join(r.key_criteria_matched)}\n\n")
                if r.key_criteria_missed:
                    f.write(f"**Missed:** {', '.join(r.key_criteria_missed)}\n\n")
    else:
        raise ValueError(f"Unsupported output format '{filename}'. Use .json or .md")

    return filepath
