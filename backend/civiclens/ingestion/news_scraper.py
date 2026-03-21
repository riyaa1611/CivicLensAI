"""News scrapers for Economic Times and Business Today policy coverage."""
import logging
import re
from datetime import datetime
from typing import List, Dict
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
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Referer": "https://www.google.com/",
}

ET_URL = "https://economictimes.indiatimes.com/topic/government-policies"
BT_URL = "https://www.businesstoday.in/latest/policy"


def scrape_economic_times() -> List[Dict]:
    """Scrape government policy articles from Economic Times."""
    policies = []
    try:
        resp = requests.get(ET_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # ET topic page: try multiple selector patterns
        items = (
            soup.select(".eachStory") or
            soup.select(".story-box") or
            soup.select(".artList li") or
            soup.select("article")
        )

        for item in items[:20]:
            try:
                a_tag = item.find("a", href=True)
                if not a_tag:
                    continue
                title = a_tag.get_text(strip=True)
                if not title or len(title) < 10:
                    # Try heading tags
                    h = item.find(["h3", "h4", "h2"])
                    if h:
                        a_tag = h.find("a", href=True) or a_tag
                        title = h.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                href = a_tag.get("href", "")
                link = href if href.startswith("http") else f"https://economictimes.indiatimes.com{href}"

                # Extract date from meta or time tag
                date = _extract_date(item) or datetime.utcnow()

                # Description from summary/p tag
                desc_el = item.find(["p", ".story-desc", ".eachStory p"])
                description = desc_el.get_text(strip=True) if desc_el else title

                policies.append({
                    "title": title,
                    "source": "Economic Times",
                    "date": date,
                    "description": description[:500],
                    "link": link,
                    "raw_content": f"{title}\n\n{description}",
                })
            except Exception as e:
                logger.debug(f"ET item parse error: {e}")

        if not policies:
            logger.warning("Economic Times scraper returned no results (site may block scrapers)")

    except Exception as e:
        logger.error(f"Economic Times scraper failed: {e}")

    return policies


def scrape_business_today() -> List[Dict]:
    """Scrape policy articles from Business Today."""
    policies = []
    try:
        resp = requests.get(BT_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # BT listing page uses .BT_sl_item as article wrapper
        items = (
            soup.select(".BT_sl_item") or
            soup.select(".story-list article") or
            soup.select(".listing-page article") or
            soup.select("article")
        )

        for item in items[:20]:
            try:
                # Title is in .BT_sl_title a or h2 a
                title_el = item.select_one(".BT_sl_title a") or item.find(["h2", "h3"], recursive=True)
                if not title_el:
                    continue
                a_tag = title_el if title_el.name == "a" else title_el.find("a", href=True)
                if not a_tag:
                    continue

                title = title_el.get_text(strip=True)
                if not title or len(title) < 10:
                    continue

                href = a_tag.get("href", "")
                link = href if href.startswith("http") else f"https://www.businesstoday.in{href}"

                # BT URLs contain date: /story/slug-NNNNNN-YYYY-MM-DD
                date = _date_from_bt_url(link) or _extract_date(item) or datetime.utcnow()

                # Description / summary
                desc_el = item.select_one(".BT_sl_desc, .story-desc, p")
                description = desc_el.get_text(strip=True) if desc_el else title

                policies.append({
                    "title": title,
                    "source": "Business Today",
                    "date": date,
                    "description": description[:500],
                    "link": link,
                    "raw_content": f"{title}\n\n{description}",
                })
            except Exception as e:
                logger.debug(f"BT item parse error: {e}")

        if not policies:
            logger.warning("Business Today scraper returned no results")

    except Exception as e:
        logger.error(f"Business Today scraper failed: {e}")

    return policies


def _date_from_bt_url(url: str) -> datetime | None:
    """Extract date from BT URL pattern: ...-YYYY-MM-DD"""
    m = re.search(r"(\d{4}-\d{2}-\d{2})$", url)
    if m:
        try:
            return datetime.strptime(m.group(1), "%Y-%m-%d")
        except ValueError:
            pass
    return None


def _extract_date(element) -> datetime | None:
    """Try to extract a date from a BeautifulSoup element."""
    # Try <time> tag
    time_el = element.find("time")
    if time_el:
        dt = time_el.get("datetime") or time_el.get_text(strip=True)
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%b %d, %Y", "%d %b %Y"):
            try:
                return datetime.strptime(dt[:len(fmt) + 2].strip(), fmt)
            except (ValueError, AttributeError):
                continue
    # Try data attributes
    for el in element.find_all(True, {"data-date": True}):
        try:
            return datetime.strptime(el["data-date"], "%Y-%m-%d")
        except ValueError:
            pass
    return None
