"""PRS India Bill Tracker scraper."""
import logging
from datetime import datetime
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

PRS_URL = "https://prsindia.org/billtrack"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


def scrape_prs() -> List[Dict]:
    """
    Scrape recent bills from PRS India Bill Tracker.
    Returns list of policy dicts with: title, source, date, description, link.
    """
    policies = []
    try:
        resp = requests.get(PRS_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # PRS bill tracker table rows
        rows = soup.select("table.views-table tbody tr")
        if not rows:
            # Try alternate selectors
            rows = soup.select(".view-content .views-row")

        for row in rows[:20]:
            try:
                policy = _parse_prs_row(row)
                if policy:
                    policies.append(policy)
            except Exception as e:
                logger.debug(f"PRS row parse error: {e}")

        if not policies:
            logger.warning("PRS scraper returned no results — using fallback data")
            policies = _fallback_prs_data()

    except Exception as e:
        logger.error(f"PRS scraper failed: {e}")
        policies = _fallback_prs_data()

    return policies


def _parse_prs_row(row) -> Optional[Dict]:
    """Parse a single PRS table row into a policy dict."""
    cells = row.find_all("td")
    if len(cells) < 2:
        return None

    title_el = row.find("a")
    title = title_el.get_text(strip=True) if title_el else cells[0].get_text(strip=True)
    if not title:
        return None

    link = ""
    if title_el and title_el.get("href"):
        href = title_el["href"]
        link = href if href.startswith("http") else f"https://prsindia.org{href}"

    # Try to extract date from cells
    date_str = ""
    for cell in cells:
        text = cell.get_text(strip=True)
        if any(c.isdigit() for c in text) and len(text) < 30:
            date_str = text
            break

    date = _parse_date(date_str)
    description = cells[-1].get_text(strip=True) if len(cells) > 2 else title

    return {
        "title": title,
        "source": "PRS",
        "date": date,
        "description": description[:500],
        "link": link or PRS_URL,
        "raw_content": f"{title}\n\n{description}",
    }


def _parse_date(date_str: str) -> datetime:
    """Parse various date formats."""
    formats = ["%d %b %Y", "%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%b %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return datetime.utcnow()


def _fallback_prs_data() -> List[Dict]:
    """Return sample PRS policy data for development/fallback."""
    return [
        {
            "title": "The Digital Personal Data Protection Act, 2023",
            "source": "PRS",
            "date": datetime(2026, 1, 15),
            "description": (
                "A landmark legislation establishing rules for processing digital personal data "
                "of individuals in India, creating obligations for data fiduciaries and rights for data principals."
            ),
            "link": "https://prsindia.org/billtrack/digital-personal-data-protection-bill-2023",
            "raw_content": (
                "The Digital Personal Data Protection Act, 2023 (DPDP Act) is a comprehensive data "
                "protection law in India, receiving Presidential assent on August 11, 2023.\n\n"
                "KEY PROVISIONS:\n"
                "1. Data Fiduciaries: Any entity that determines the purpose and means of processing "
                "personal data must register and comply with obligations under the Act.\n"
                "2. Data Principals: Indian citizens have the right to access information about their "
                "data, correct or erase it, and nominate a person to exercise these rights in case of death.\n"
                "3. Consent: Personal data may only be processed with the individual's consent, or for "
                "certain legitimate uses. Consent must be free, specific, informed, unconditional, and unambiguous.\n"
                "4. Data Protection Board: The Act establishes the Data Protection Board of India to "
                "adjudicate complaints and impose penalties.\n"
                "5. Significant Data Fiduciaries: The government may designate certain entities as "
                "Significant Data Fiduciaries based on volume of data processed, risk to national security, "
                "and impact on sovereignty. They face additional obligations.\n"
                "6. Cross-border transfers: Personal data may be transferred outside India except to "
                "countries specifically restricted by the government.\n"
                "7. Children's data: Special protections apply for processing data of children under 18, "
                "including verifiable parental consent.\n"
                "8. Penalties: Non-compliance can attract penalties up to Rs 250 crore per instance, "
                "up to a total of Rs 500 crore.\n\n"
                "IMPACT ON CITIZENS: Citizens (Data Principals) can demand information about how their "
                "data is used, request correction of inaccurate data, request erasure of data, and "
                "withdraw consent at any time. Grievance redressal must be provided by Data Fiduciaries.\n\n"
                "IMPACT ON BUSINESSES: Companies must appoint Data Protection Officers, implement "
                "security safeguards, report data breaches within 72 hours, and maintain records of "
                "processing activities. Small businesses processing limited data have lighter obligations."
            ),
        },
        {
            "title": "The Telecommunications Act, 2023",
            "source": "PRS",
            "date": datetime(2026, 1, 20),
            "description": (
                "Replaces the Indian Telegraph Act of 1885, regulating telecom services, "
                "spectrum assignment, and establishing new licensing frameworks."
            ),
            "link": "https://prsindia.org/billtrack/telecommunications-bill-2023",
            "raw_content": (
                "The Telecommunications Act, 2023 (Telecom Act 2023) received Presidential assent on "
                "December 24, 2023. It repeals and replaces three colonial-era laws: the Indian Telegraph "
                "Act, 1885; the Indian Wireless Telegraphy Act, 1933; and the Telegraph Wires (Unlawful "
                "Possession) Act, 1950.\n\n"
                "KEY PROVISIONS:\n"
                "1. Authorisation Framework: All telecom service providers must obtain authorisation from "
                "the central government. The old licensing regime is replaced with a streamlined "
                "authorisation system covering telecom services, networks, and infrastructure.\n"
                "2. Spectrum Assignment: The Act allows spectrum to be assigned via auction or "
                "administrative process. Spectrum assigned administratively includes defence, railways, "
                "and scientific use. Satellite spectrum will be allocated administratively, not auctioned.\n"
                "3. Right of Way: Telecom infrastructure providers have a right to install equipment on "
                "public and private property, with compensation to landowners. Local authorities must "
                "decide right-of-way applications within 60 days.\n"
                "4. National Security: The government can take over control of telecom networks during "
                "public emergency or in the interest of public safety. It can also direct interception "
                "of messages on grounds of national security.\n"
                "5. Over-The-Top (OTT) Services: Internet-based communication services like WhatsApp, "
                "Zoom, and Google Meet are brought under the telecom regulatory framework, requiring "
                "authorisation.\n"
                "6. TRAI Reforms: The Telecom Regulatory Authority of India's role is clarified. TRAI's "
                "recommendations on spectrum auction are not binding on the government.\n"
                "7. User Protections: Telecom entities must provide specified services to rural/remote "
                "areas. Users must be protected from unsolicited commercial communications (spam calls).\n"
                "8. Biometric Verification: SIM cards can only be issued after biometric-based verification "
                "of users to curb fraudulent connections.\n"
                "9. Penalty Framework: Offences include providing telecom services without authorisation "
                "(up to 3 years imprisonment or Rs 2 crore fine), possessing wireless equipment without "
                "a licence (up to 3 years or Rs 2 crore fine).\n\n"
                "IMPACT ON CITIZENS: Users get stronger protections against spam and unsolicited calls. "
                "SIM card fraud should reduce with biometric verification. Telecom services must be "
                "available in rural and underserved areas.\n\n"
                "IMPACT ON BUSINESSES: Telecom companies and OTT providers must obtain new authorisations. "
                "Existing licencees are deemed authorised for 90 days. Spectrum acquired at auction can "
                "now be shared and traded between operators."
            ),
        },
        {
            "title": "The Jan Vishwas (Amendment of Provisions) Act, 2023",
            "source": "PRS",
            "date": datetime(2026, 1, 15),
            "description": (
                "Decriminalises minor offences across 42 central Acts, replacing imprisonment "
                "with monetary penalties to ease business compliance burden."
            ),
            "link": "https://prsindia.org/billtrack/jan-vishwas-bill-2023",
            "raw_content": (
                "The Jan Vishwas (Amendment of Provisions) Act, 2023 amends 42 central Acts to "
                "decriminalise 183 minor offences by replacing imprisonment with monetary penalties. "
                "It received Presidential assent on August 11, 2023.\n\n"
                "KEY PROVISIONS:\n"
                "1. Decriminalisation: Removes imprisonment for minor, technical, or procedural violations "
                "across sectors including agriculture, environment, trade, and media.\n"
                "2. Monetary Penalties: Replaces jail terms with fines for offences like minor labelling "
                "violations, minor environmental infractions, and technical non-compliance.\n"
                "3. Acts Amended: Includes the Environment Protection Act, the Drugs and Cosmetics Act, "
                "the Trade Marks Act, the Copyright Act, the Information Technology Act, and 37 others.\n"
                "4. Adjudicating Officers: Disputes are to be resolved by designated adjudicating officers "
                "rather than criminal courts, reducing the burden on the judiciary.\n\n"
                "IMPACT ON BUSINESSES: Reduces compliance burden and fear of criminal prosecution for "
                "technical violations. Startups and MSMEs benefit as minor paperwork errors no longer "
                "attract imprisonment. Improves India's ease of doing business ranking.\n\n"
                "IMPACT ON CITIZENS: Reduces criminalization of minor violations. Disputes resolved "
                "faster through administrative adjudication rather than lengthy criminal trials."
            ),
        },
        {
            "title": "The Right to Information (Amendment) Act, 2019",
            "source": "PRS",
            "date": datetime(2026, 2, 10),
            "description": (
                "Amends the RTI Act to change the tenure and service conditions of Information "
                "Commissioners, making them serve at the pleasure of the central government."
            ),
            "link": "https://prsindia.org/billtrack/right-to-information-amendment-bill-2019",
            "raw_content": (
                "The Right to Information (Amendment) Act, 2019 amends the Right to Information Act, 2005.\n\n"
                "KEY PROVISIONS:\n"
                "1. Tenure: The fixed 5-year terms of the Chief Information Commissioner and Information "
                "Commissioners at both central and state levels are removed. Tenure will now be as "
                "prescribed by the central government.\n"
                "2. Salary: Salaries, allowances, and service conditions will be as prescribed by the "
                "central government, removing parity with Election Commissioners.\n\n"
                "IMPACT ON CITIZENS: Critics argue this undermines the independence of the RTI "
                "apparatus. Proponents say it allows flexibility in appointments. Citizens can still "
                "file RTI applications to access government information, request correction of records, "
                "and seek accountability from public authorities."
            ),
        },
        {
            "title": "The Consumer Protection Act, 2019",
            "source": "PRS",
            "date": datetime(2026, 2, 18),
            "description": (
                "Replaces the Consumer Protection Act, 1986, establishing a Central Consumer "
                "Protection Authority and regulating e-commerce and direct selling."
            ),
            "link": "https://prsindia.org/billtrack/consumer-protection-bill-2019",
            "raw_content": (
                "The Consumer Protection Act, 2019 replaces the Consumer Protection Act, 1986.\n\n"
                "KEY PROVISIONS:\n"
                "1. Central Consumer Protection Authority (CCPA): A new regulatory body to promote, "
                "protect, and enforce the rights of consumers. It can impose penalties up to Rs 10 lakh "
                "and ban misleading advertisements.\n"
                "2. E-Commerce Regulation: E-commerce entities must display prices, country of origin, "
                "return/refund policies, and grievance officer details. Sellers cannot manipulate prices.\n"
                "3. Product Liability: Manufacturers, product service providers, and product sellers are "
                "liable for harm caused by defective products or deficient services.\n"
                "4. Unfair Trade Practices: Expanded definition includes withholding personal data "
                "collected for service delivery.\n"
                "5. Mediation: Consumer disputes can be settled through mediation before going to court.\n"
                "6. Consumer Forums: Pecuniary jurisdiction enhanced — District Forums handle up to "
                "Rs 1 crore, State Commissions up to Rs 10 crore, National Commission above Rs 10 crore.\n\n"
                "IMPACT ON CITIZENS: Stronger protections when buying online. Right to seek compensation "
                "for product defects. Faster grievance resolution through mediation. Protection from "
                "misleading advertisements and fake reviews."
            ),
        },
    ]
