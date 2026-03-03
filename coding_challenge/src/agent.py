import json
import re

import anthropic
from anthropic.types import ToolParam, MessageParam

from models import EligibilityResult, Foundation, Project
from scraper import extract_links, fetch_page

FETCH_TOOL: ToolParam = {
    "name": "fetch_webpage",
    "description": (
        "Fetch the content of a webpage. Returns the page text and a list of "
        "relevant sub-page links (application criteria, about pages, etc.). "
        "Use this to read a foundation's website or follow up on sub-pages."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The full URL to fetch",
            }
        },
        "required": ["url"],
    },
}

EXTRACTION_SYSTEM_PROMPT = """\
You are a structured data extraction assistant. Given a project description text, \
extract key fields into a JSON object.

Respond ONLY with a JSON object in this exact format:
{
    "name": "Project name",
    "country": "Country where the project is based",
    "target_location": "Specific location(s) where the project operates",
    "budget_total": 0.0,
    "self_financing": 0.0,
    "funding_sought": 0.0,
    "currency": "DKK",
    "duration_months": 0,
    "start_date": "YYYY-MM-DD",
    "target_group": "Description of primary target group",
    "focus_areas": ["area1", "area2"]
}

Rules:
- budget_total is the full project budget
- self_financing is the amount the organization covers from its own resources
- funding_sought is the amount sought externally (budget_total - self_financing)
- focus_areas should be short tags (e.g. "environment", "children's health", "policy")
- If a field cannot be determined, use reasonable defaults (0 for numbers, "" for strings)
"""

ASSESSMENT_SYSTEM_PROMPT = """\
You are an expert grant researcher helping a Danish NGO assess whether their project \
is eligible for funding from a specific foundation.

You will be given:
1. A structured project summary with key facts
2. The full project description text
3. A foundation name and website URL

Your task:
1. Fetch the foundation's website to understand their purpose, focus areas, \
eligibility requirements, and any restrictions.
2. If the main page does not have enough detail, follow relevant sub-page links \
provided in the fetch results to find application criteria or about pages.
3. Make a clear eligibility determination.

Foundations are often Danish, and their websites are in Danish. Read them carefully.

When you have gathered enough information, respond with a JSON object in this exact format:
{
    "eligible": true,
    "confidence": "high",
    "reasoning": "Clear explanation in English, 2-5 sentences.",
    "key_criteria_matched": ["criterion 1", "criterion 2"],
    "key_criteria_missed": ["criterion 1", "criterion 2"]
}

- eligible: true, false, or null (null only when the website provides no useful information)
- confidence: "high", "medium", or "low"
- key_criteria_matched: aspects of the project that align with the foundation
- key_criteria_missed: requirements the project does not meet, or foundation restrictions

Common disqualifiers to look for:
- Foundation only funds individuals/persons (not organizations)
- Foundation is geographically restricted to a specific area the project doesn't operate in
- Foundation's purpose area is completely unrelated (e.g., disease research, trade association)
- Foundation explicitly requires membership or professional affiliation
- Budget or grant size mismatch
"""


def extract_project_info(raw_text: str, client: anthropic.Anthropic, model: str) -> Project:
    """Use Claude to extract structured project info from raw description text."""
    response = client.messages.create(
        model=model,
        max_tokens=1024,
        temperature=0,
        system=EXTRACTION_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Extract project information from this text:\n\n{raw_text}"}],
    )

    text = response.content[0].text
    data = _parse_json_response(text)

    return Project(
        name=data.get("name", "Unknown"),
        description=raw_text,
        country=data.get("country", "Unknown"),
        target_location=data.get("target_location", "Unknown"),
        budget_total=float(data.get("budget_total", 0)),
        self_financing=float(data.get("self_financing", 0)),
        funding_sought=float(data.get("funding_sought", 0)),
        currency=data.get("currency", "DKK"),
        duration_months=int(data.get("duration_months", 0)),
        start_date=data.get("start_date", "Unknown"),
        target_group=data.get("target_group", "Unknown"),
        focus_areas=data.get("focus_areas", []),
    )


def assess_foundation(
    foundation: Foundation,
    project: Project,
    client: anthropic.Anthropic,
    model: str,
    max_tool_calls: int = 4,
) -> EligibilityResult:
    """Run an agentic loop for one foundation and return an EligibilityResult."""
    project_summary = _format_project_summary(project)

    messages: list[MessageParam] = [
        {
            "role": "user",
            "content": (
                f"## Project Summary\n{project_summary}\n\n"
                f"## Full Project Description\n{project.description}\n\n"
                f"---\n\n"
                f"Please assess eligibility for:\n"
                f"**Foundation:** {foundation.name}\n"
                f"**Website:** {foundation.url}\n\n"
                f"Start by fetching the foundation's website."
            ),
        }
    ]

    scraped_urls: list[str] = []
    scrape_errors: list[str] = []
    tool_calls_made = 0
    limit_exceeded = False

    while True:
        # After the limit, stop offering tools so Claude must give a final text answer
        tools = [] if limit_exceeded else [FETCH_TOOL]

        try:
            response = client.messages.create(
                model=model,
                max_tokens=2048,
                temperature=0,
                system=ASSESSMENT_SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            )
        except anthropic.APIError as e:
            return _error_result(foundation, f"Claude API error: {e}", scraped_urls, scrape_errors)

        # If Claude is done (end_turn or no more tools available), parse the final response
        if response.stop_reason != "tool_use":
            final_text = ""
            for block in response.content:
                if hasattr(block, "text"):
                    final_text += block.text
            return _parse_eligibility_result(final_text, foundation, scraped_urls, scrape_errors)

        # Process all tool use blocks in the response
        assistant_content = response.content
        tool_results = []

        for block in assistant_content:
            if block.type == "tool_use" and block.name == "fetch_webpage":
                tool_calls_made += 1
                url = block.input.get("url", "")
                scraped_urls.append(url)

                if tool_calls_made > max_tool_calls:
                    limit_exceeded = True
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": (
                            "Tool call limit reached. Make your best assessment "
                            "with the information gathered so far."
                        ),
                    })
                else:
                    result_text = _execute_fetch(url)
                    if result_text.startswith("Failed to fetch"):
                        scrape_errors.append(f"{url}: {result_text}")
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

        messages.append({"role": "assistant", "content": assistant_content})
        messages.append({"role": "user", "content": tool_results})


def _execute_fetch(url: str) -> str:
    """Fetch a webpage and return formatted text with sub-page links."""
    page = fetch_page(url)

    if not page.success:
        return f"Failed to fetch {url}: {page.error}"

    result = page.text

    # Append discovered sub-page links
    if page.raw_html:
        links = extract_links(page.raw_html, url)
        if links:
            result += "\n\n---\nRelevant sub-pages found:\n"
            result += "\n".join(f"- {link}" for link in links)

    return result


def _format_project_summary(project: Project) -> str:
    """Format project as a readable summary for Claude."""
    focus = ", ".join(project.focus_areas) if project.focus_areas else "N/A"
    return (
        f"Name: {project.name}\n"
        f"Country: {project.country}\n"
        f"Target location: {project.target_location}\n"
        f"Budget total: {project.budget_total:,.0f} {project.currency}\n"
        f"Self-financing: {project.self_financing:,.0f} {project.currency}\n"
        f"Funding sought: {project.funding_sought:,.0f} {project.currency}\n"
        f"Duration: {project.duration_months} months (start: {project.start_date})\n"
        f"Target group: {project.target_group}\n"
        f"Focus areas: {focus}"
    )


def _parse_json_response(text: str) -> dict:
    """Extract JSON from Claude's response, handling code fences."""
    # Try code-fenced JSON first
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        return json.loads(match.group(1))

    # Fall back to first { ... } block (handling nested braces)
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start is not None:
                return json.loads(text[start : i + 1])

    raise ValueError("No JSON found in response")


def _parse_eligibility_result(
    text: str,
    foundation: Foundation,
    scraped_urls: list[str],
    scrape_errors: list[str],
) -> EligibilityResult:
    """Parse Claude's final JSON response into an EligibilityResult."""
    try:
        data = _parse_json_response(text)
        return EligibilityResult(
            foundation=foundation,
            eligible=data.get("eligible"),
            confidence=data.get("confidence", "low"),
            reasoning=data.get("reasoning", "No reasoning provided."),
            key_criteria_matched=data.get("key_criteria_matched", []),
            key_criteria_missed=data.get("key_criteria_missed", []),
            scraped_urls=scraped_urls,
            scrape_errors=scrape_errors,
        )
    except (ValueError, json.JSONDecodeError):
        return EligibilityResult(
            foundation=foundation,
            eligible=None,
            confidence="low",
            reasoning=f"Failed to parse structured response. Raw output: {text[:500]}",
            scraped_urls=scraped_urls,
            scrape_errors=scrape_errors,
        )


def _error_result(
    foundation: Foundation,
    error_msg: str,
    scraped_urls: list[str],
    scrape_errors: list[str],
) -> EligibilityResult:
    """Create an error EligibilityResult when the assessment fails entirely."""
    return EligibilityResult(
        foundation=foundation,
        eligible=None,
        confidence="low",
        reasoning=error_msg,
        scraped_urls=scraped_urls,
        scrape_errors=scrape_errors,
    )
