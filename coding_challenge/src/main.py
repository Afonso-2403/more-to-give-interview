#!/usr/bin/env python3
"""
Foundation Eligibility Assessment Agent

Assesses whether a project meets the requirements of specific foundations/grants
by scraping their websites and using Claude to determine eligibility.

Usage:
    uv run python coding_challenge/src/main.py \
        --project "coding_challenge/Project Plastic_Project description.docx" \
        --foundations "coding_challenge/Project Plastic_Foundations.xlsx" \
        --output report.json
"""

import argparse
import os
import sys
from pathlib import Path

import anthropic

from agent import assess_foundation, extract_project_info
from document_parser import load_project_description, parse_foundations_list
from models import EligibilityResult
from io_utils import print_project_summary, print_result_summary, print_final_report, prompt_validation, save_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess project eligibility for foundation/grant funding",
    )
    parser.add_argument(
        "--project", required=True, help="Path to project description (.docx or .txt)",
    )
    parser.add_argument(
        "--foundations", required=True, help="Path to foundations list (.xlsx)",
    )
    parser.add_argument(
        "--output", help="Optional output file (.json or .md)",
    )
    parser.add_argument(
        "--model", default="claude-sonnet-4-6", help="Claude model to use (default: claude-sonnet-4-6)",
    )
    parser.add_argument(
        "--only", type=int, nargs="+", help="Only assess specific foundation numbers (for testing)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Load API key from .env file or environment
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        env_path = Path(__file__).resolve().parents[2] / ".env"
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ[key.strip()] = value.strip()
            api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("Error: ANTHROPIC_API_KEY not found. Set it in .env or as an environment variable.")

    # Load inputs
    print("Loading project description...")
    raw_text = load_project_description(args.project)

    print("Loading foundations list...")
    try:
        foundations = parse_foundations_list(args.foundations)
    except Exception as ex:
        sys.exit(f"Error: {ex}")
        
    if args.only:
        foundations = [f for f in foundations if f.number in args.only]

    if not foundations:
        sys.exit("Error: No foundations to assess.")

    # Extract structured project info
    client = anthropic.Anthropic(api_key=api_key)

    print("Extracting project information with Claude...")
    project = extract_project_info(raw_text, client, model=args.model)

    # User validation
    print_project_summary(project)
    if not prompt_validation():
        sys.exit("Project extraction rejected. Please adjust the input file and try again.")

    # Assess each foundation
    print(f"\nAssessing {len(foundations)} foundation(s)...\n")
    results: list[EligibilityResult] = []

    for i, foundation in enumerate(foundations, 1):
        print(f"{'─' * 60}")
        result = assess_foundation(foundation, project, client, model=args.model)
        results.append(result)
        print_result_summary(result, i, len(foundations))
        print()

    # Final report
    print_final_report(results)

    # Save output
    if args.output:
        try:
            filepath = save_output(results, args.output)
            print(f"\nReport saved to: {filepath}")
        except ValueError as ex:
            print(ex)


if __name__ == "__main__":
    main()
