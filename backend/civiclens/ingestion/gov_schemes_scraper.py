"""Government ministry and schemes scrapers."""
import logging
import re
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

SOCIAL_JUSTICE_URL = "https://socialjustice.gov.in/"
FINANCIAL_SERVICES_URL = "https://financialservices.gov.in/beta/en"
INDIA_GOV_SCHEMES_URL = "https://www.india.gov.in/my-government/schemes"
ESHRAM_URL = "https://eshram.gov.in/social-security-welfare-schemes"


def scrape_social_justice() -> List[Dict]:
    """Scrape schemes and news from Ministry of Social Justice & Empowerment."""
    policies = []
    try:
        resp = requests.get(SOCIAL_JUSTICE_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Try news/update listings
        items = (
            soup.select(".latest-news li a") or
            soup.select(".news-list li a") or
            soup.select(".whats-new li a") or
            soup.select("ul.news li a") or
            soup.select("a[href*='scheme']") or
            soup.select("a[href*='programme']")
        )

        seen = set()
        for a in items[:20]:
            try:
                title = a.get_text(strip=True)
                if not title or len(title) < 10 or title in seen:
                    continue
                seen.add(title)
                href = a.get("href", "")
                link = href if href.startswith("http") else f"https://socialjustice.gov.in{href}"

                # Try to get date from parent li or sibling span
                date = _extract_nearby_date(a) or datetime.utcnow()

                policies.append({
                    "title": title,
                    "source": "Social Justice Ministry",
                    "date": date,
                    "description": title,
                    "link": link,
                    "raw_content": title,
                })
            except Exception as e:
                logger.debug(f"Social Justice item parse error: {e}")

        if not policies:
            logger.warning("Social Justice scraper returned no results")

    except Exception as e:
        logger.error(f"Social Justice scraper failed: {e}")

    return policies


def scrape_financial_services() -> List[Dict]:
    """Scrape scheme updates from Department of Financial Services."""
    policies = []
    try:
        resp = requests.get(FINANCIAL_SERVICES_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # DFS site — try news/notification sections
        items = (
            soup.select(".news-updates li a") or
            soup.select(".latest-updates li a") or
            soup.select(".notification-list li a") or
            soup.select(".what-new li a") or
            soup.select("ul.list-unstyled li a") or
            soup.select("a[href*='scheme']") or
            soup.select("a[href*='notification']")
        )

        seen = set()
        for a in items[:20]:
            try:
                title = a.get_text(strip=True)
                if not title or len(title) < 10 or title in seen:
                    continue
                seen.add(title)
                href = a.get("href", "")
                link = href if href.startswith("http") else f"https://financialservices.gov.in{href}"

                date = _extract_nearby_date(a) or datetime.utcnow()

                policies.append({
                    "title": title,
                    "source": "Financial Services",
                    "date": date,
                    "description": title,
                    "link": link,
                    "raw_content": title,
                })
            except Exception as e:
                logger.debug(f"Financial Services item parse error: {e}")

        if not policies:
            logger.warning("Financial Services scraper returned no results")

    except Exception as e:
        logger.error(f"Financial Services scraper failed: {e}")

    return policies


def scrape_india_gov_schemes() -> List[Dict]:
    """Scrape government schemes listing from india.gov.in."""
    policies = []
    try:
        resp = requests.get(INDIA_GOV_SCHEMES_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # india.gov.in uses Next.js — extract scheme category cards
        # Category cards have headings and links to /my-government/schemes/search
        items = (
            soup.select("a[href*='/my-government/schemes/search']") or
            soup.select(".content-card-margin-top a") or
            soup.select(".section-padding a") or
            soup.select("a[href*='scheme']")
        )

        seen = set()
        for a in items[:20]:
            try:
                title = a.get_text(strip=True)
                if not title or len(title) < 5 or title in seen:
                    continue
                seen.add(title)
                href = a.get("href", "")
                link = href if href.startswith("http") else f"https://www.india.gov.in{href}"

                # Try to get description from parent card
                parent = a.find_parent(["div", "li", "article"])
                description = title
                if parent:
                    p = parent.find("p")
                    if p:
                        description = p.get_text(strip=True)

                policies.append({
                    "title": title,
                    "source": "India.gov.in",
                    "date": datetime.utcnow(),
                    "description": description[:500],
                    "link": link,
                    "raw_content": f"{title}\n\n{description}",
                })
            except Exception as e:
                logger.debug(f"India.gov.in item parse error: {e}")

        if not policies:
            logger.warning("India.gov.in scraper returned no results")

    except Exception as e:
        logger.error(f"India.gov.in scraper failed: {e}")

    return policies


def scrape_eshram() -> List[Dict]:
    """
    Scrape social security schemes from eSHRAM portal.
    Page is static — each scheme has an h5 title, p description,
    h6 Eligibility/Benefits subsections with ul li items.
    """
    policies = []
    try:
        resp = requests.get(ESHRAM_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Each scheme block: h5 (title) followed by p (desc) and h6+ul (eligibility/benefits)
        scheme_headings = soup.find_all("h5")

        for h5 in scheme_headings:
            try:
                title = h5.get_text(strip=True)
                if not title or len(title) < 5:
                    continue

                # Collect content siblings until next h5
                raw_parts = [title]
                description_parts = []
                link = ESHRAM_URL

                sibling = h5.find_next_sibling()
                while sibling and sibling.name != "h5":
                    if sibling.name == "p":
                        text = sibling.get_text(strip=True)
                        if text:
                            description_parts.append(text)
                            raw_parts.append(text)
                    elif sibling.name == "h6":
                        section_title = sibling.get_text(strip=True)
                        raw_parts.append(f"\n{section_title}:")
                        # Collect following ul
                        ul = sibling.find_next_sibling("ul")
                        if ul:
                            for li in ul.find_all("li"):
                                raw_parts.append(f"- {li.get_text(strip=True)}")
                    elif sibling.name == "a" and sibling.get("href", "").startswith("http"):
                        link = sibling["href"]
                    sibling = sibling.find_next_sibling()

                description = " ".join(description_parts)[:500] or title

                policies.append({
                    "title": title,
                    "source": "eSHRAM",
                    "date": datetime.utcnow(),
                    "description": description,
                    "link": link,
                    "raw_content": "\n".join(raw_parts),
                })
            except Exception as e:
                logger.debug(f"eSHRAM scheme parse error: {e}")

        if not policies:
            logger.warning("eSHRAM scraper returned no results")

    except Exception as e:
        logger.error(f"eSHRAM scraper failed: {e}")

    return policies


def scrape_gov_schemes() -> List[Dict]:
    """Aggregate scraper for all government ministry/scheme sources."""
    all_policies = []
    for fn in [scrape_social_justice, scrape_financial_services, scrape_india_gov_schemes, scrape_eshram]:
        all_policies.extend(fn())
    return all_policies


def _extract_nearby_date(element) -> Optional[datetime]:
    """Look for a date string in parent/sibling elements."""
    parent = element.find_parent(["li", "div", "tr"])
    if not parent:
        return None

    text = parent.get_text(" ", strip=True)
    # Match common Indian govt date formats
    patterns = [
        (r"\d{2}-\w{3}-\d{4}", "%d-%b-%Y"),
        (r"\d{2}/\d{2}/\d{4}", "%d/%m/%Y"),
        (r"\d{2} \w+ \d{4}", "%d %B %Y"),
        (r"\w+ \d{2},? \d{4}", "%b %d %Y"),
    ]
    for pattern, fmt in patterns:
        m = re.search(pattern, text)
        if m:
            try:
                date_str = m.group(0).replace(",", "").strip()
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
    return None
