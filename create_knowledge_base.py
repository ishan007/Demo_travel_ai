"""Download html content and create knowledge markdown files.

Sources:
  1. https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/singapore-city-tour-guide/
  2. https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/4-days-in-singapore/
  3. https://www.visitsingapore.com/see-do-singapore/things-to-do/
  4. https://en.wikivoyage.org/w/api.php

output-dir knowledge
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, Tag

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.config import KNOWLEDGE_SOURCES

DEFAULT_OUTPUT_DIR = BASE_DIR / "knowledge"

USER_AGENT = "SingaporeTravelAssistant/1.0 (education; contact: local-dev)"
TIMEOUT = 30.0


WIKIVOYAGE_SECTIONS = [
    "Districts",
    "Understand",
    "Get around",
    "See",
    "Do",
    "Buy",
    "Eat",
    "Stay safe",
    "Respect",
]

VISIT_SINGAPORE_ITINERARY_URLS = [
    (
        "2-Day City Tour",
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/singapore-city-tour-guide/",
    ),
    (
        "4 Days in Singapore",
        "https://www.visitsingapore.com/travel-tips/travelling-to-singapore/itineraries/4-days-in-singapore/",
    ),
    (
        "Things To Do",
        "https://www.visitsingapore.com/see-do-singapore/things-to-do/",
    ),
]


def fetch_url(client: httpx.Client, url: str) -> str:
    response = client.get(url)
    response.raise_for_status()
    return response.text


def write_markdown(output_dir: Path, filename: str, body: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / filename
    path.write_text(f"{body.strip()}\n", encoding="utf-8")
    return path


def clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def filter_wikivoyage_sections(text: str, sections: list[str]) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    current_section: str | None = None
    include = False

    for line in lines:
        if line.startswith("== ") and line.endswith(" =="):
            current_section = line.strip("= ").strip()
            include = current_section in sections
            if include:
                kept.append(f"\n## {current_section}\n")
            continue

        if line.startswith("=== ") and include:
            kept.append(f"\n### {line.strip('= ').strip()}\n")
            continue

        if include:
            kept.append(line)

    return clean_text("\n".join(kept))


def fetch_wikivoyage(client: httpx.Client) -> str:
    api_url = "https://en.wikivoyage.org/w/api.php"
    params = {
        "action": "query",
        "prop": "extracts",
        "explaintext": "true",
        "titles": "Singapore",
        "format": "json",
    }
    response = client.get(api_url, params=params)
    response.raise_for_status()
    data = response.json()
    pages = data["query"]["pages"]
    page = next(iter(pages.values()))
    extract = page.get("extract", "")
    if not extract:
        raise ValueError("Wikivoyage API returned empty content for Singapore.")

    filtered = filter_wikivoyage_sections(extract, WIKIVOYAGE_SECTIONS)
    header = "# Singapore Travel Guide\n\n"
    return header + filtered


def _heading_level(tag_name: str) -> int | None:
    if tag_name in {"h1", "h2", "h3", "h4"}:
        return int(tag_name[1])
    return None


def html_to_markdown(root: Tag) -> str:
    """Convert key HTML elements to simple markdown."""
    lines: list[str] = []

    for element in root.find_all(["h1", "h2", "h3", "h4", "p", "li"]):
        level = _heading_level(element.name)
        if level is not None:
            text = element.get_text(" ", strip=True)
            if text:
                prefix = "#" * min(level + 1, 4)
                lines.append(f"\n{prefix} {text}\n")
            continue

        if element.name == "p":
            text = element.get_text(" ", strip=True)
            if text:
                lines.append(text)
            continue

        if element.name == "li":
            text = element.get_text(" ", strip=True)
            if text:
                lines.append(f"- {text}")

    return clean_text("\n".join(lines))


def extract_main_content(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main is None:
        return clean_text(soup.get_text("\n", strip=True))

    return html_to_markdown(main)


def fetch_visit_singapore_essential(client: httpx.Client) -> str:
    url = "https://www.visitsingapore.com/travel-tips/essential-travel-information/"
    html = fetch_url(client, url)
    body = extract_main_content(html)
    if len(body) < 200:
        raise ValueError(f"Visit Singapore essential page returned too little content ({len(body)} chars).")
    return "# Essential Singapore Travel Information\n\n" + body


def fetch_visit_singapore_itineraries(client: httpx.Client) -> str:
    sections: list[str] = ["# Singapore Itineraries and Things To Do\n"]

    for section_title, url in VISIT_SINGAPORE_ITINERARY_URLS:
        html = fetch_url(client, url)
        content = extract_main_content(html)
        if len(content) < 100:
            sections.append(f"\n## {section_title}\n\n(Source: {url})\n\n[Content unavailable from page fetch]\n")
            continue
        sections.append(f"\n## {section_title}\n\nSource: {url}\n\n{content}\n")

    body = clean_text("\n".join(sections))
    if len(body) < 300:
        raise ValueError("Visit Singapore itinerary pages returned too little combined content.")
    return body


FETCHERS = {
    "wikivoyage_singapore.md": ("Wikivoyage Singapore", fetch_wikivoyage),
    "visit_singapore_essential.md": ("Visit Singapore Essential Information", fetch_visit_singapore_essential),
    "visit_singapore_itineraries.md": (
        "Visit Singapore Itineraries and Things To Do",
        fetch_visit_singapore_itineraries,
    ),
}


def create_knowledge_files(output_dir: Path) -> list[Path]:
    headers = {"User-Agent": USER_AGENT}
    created: list[Path] = []

    with httpx.Client(headers=headers, timeout=TIMEOUT, follow_redirects=True) as client:
        for filename, (label, fetcher) in FETCHERS.items():
            if filename not in KNOWLEDGE_SOURCES:
                raise ValueError(f"No metadata configured for {filename}")
            print(f"Fetching {label}...")
            created.append(write_markdown(output_dir, filename, fetcher(client)))

    return created


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Singapore travel knowledge markdown files.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write markdown files (default: knowledge)",
    )
    args = parser.parse_args()

    try:
        created = create_knowledge_files(args.output_dir)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("\nCreated knowledge base files:")
    for path in created:
        print(f"  - {path.name}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
