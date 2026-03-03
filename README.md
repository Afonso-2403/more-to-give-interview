Preparation for the technical interview with More To Give.

## Structure

### Design Interview
- A markdown document addressing the points asked for the interview.
- An excalidraw file, which can be loaded and opened on the browser [with excalidraw](https://excalidraw.com/)
- A screenshot of the latest iteration of the architecture

### Coding Challenge
A CLI agent that assesses whether a project is eligible for funding from a list of foundations/grants.

Given a project description (`.docx`) and a list of foundation websites (`.xlsx`), the agent:
1. Extracts structured project info using Claude and asks the user to validate it
2. Scrapes each foundation's website to understand their requirements
3. Uses Claude with tool use to determine eligibility per foundation
4. Outputs a structured report with eligibility status, confidence, and reasoning

**Usage:**
```bash
uv run python coding_challenge/src/main.py \
  --project "coding_challenge/Project Plastic_Project description.docx" \
  --foundations "coding_challenge/Project Plastic_Foundations.xlsx" \
  --output report.json
```

Requires an `ANTHROPIC_API_KEY` in a `.env` file at the project root.
