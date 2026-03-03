from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from models import ScrapedPage

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "da-DK,da;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

TIMEOUT = 15  # seconds
MAX_CONTENT_LENGTH = 15_000  # characters

# Danish keywords indicating pages with eligibility/application info
LINK_KEYWORDS = [
    "ansøg", "kriterier", "betingelser", "formål", "støtte", "vilkår",
    "legat", "fond", "apply", "criteria", "about", "om-fond", "om-os",
    "uddeling", "bevilling", "purpose", "grants",
]


def fetch_page(url: str) -> ScrapedPage:
    """Fetch a URL and return a ScrapedPage with both cleaned text and raw HTML."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
        response.raise_for_status()
        raw_html = response.text
        text = extract_text(raw_html)
        return ScrapedPage(url=url, text=text, raw_html=raw_html, success=True)
    except requests.exceptions.Timeout:
        return ScrapedPage(url=url, text="", raw_html="", success=False, error=f"Timeout after {TIMEOUT}s")
    except requests.exceptions.ConnectionError:
        return ScrapedPage(url=url, text="", raw_html="", success=False, error="Connection failed")
    except requests.exceptions.HTTPError as e:
        return ScrapedPage(url=url, text="", raw_html="", success=False, error=f"HTTP {e.response.status_code}")
    except requests.exceptions.RequestException as e:
        return ScrapedPage(url=url, text="", raw_html="", success=False, error=str(e))


def extract_text(html: str) -> str:
    """Convert raw HTML to cleaned plain text, truncated to MAX_CONTENT_LENGTH."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove non-content elements
    for tag in soup.find_all(["script", "style", "nav", "footer", "header", "noscript", "iframe"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    lines = [line.strip() for line in text.splitlines()]
    lines = [line for line in lines if line]
    text = "\n".join(lines)

    if len(text) > MAX_CONTENT_LENGTH:
        text = text[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated]"

    return text


def extract_links(html: str, base_url: str) -> list[str]:
    """Find internal links likely to contain eligibility criteria or foundation info.

    Filters by Danish/English keywords in href or link text.
    Returns deduplicated absolute URLs, limited to 5.
    """
    soup = BeautifulSoup(html, "html.parser")
    base_domain = urlparse(base_url).netloc

    candidates: list[str] = []
    seen: set[str] = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        link_text = a_tag.get_text(strip=True).lower()
        href_lower = href.lower()

        # Check if href or link text contains any relevant keyword
        has_keyword = any(kw in href_lower or kw in link_text for kw in LINK_KEYWORDS)
        if not has_keyword:
            continue

        # Resolve to absolute URL
        absolute_url = urljoin(base_url, href)

        # Only keep links on the same domain
        if urlparse(absolute_url).netloc != base_domain:
            continue

        # Skip anchors, mailto, tel
        if href.startswith(("#", "mailto:", "tel:")):
            continue

        # Deduplicate
        if absolute_url in seen:
            continue
        seen.add(absolute_url)
        candidates.append(absolute_url)

    return candidates[:5]
