from typing import Dict, List, Optional
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from playwright.sync_api import Browser
import json

from utils.browser_pool import browser_pool

NAV_TIMEOUT_MS = 20000
CONTENT_TIMEOUT_MS = 15000

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)


class ScrapeBlockedError(Exception):
    """Raised when the page loaded but returned no usable listing data (bot block, challenge page, etc.)."""


def _detect_provider(url: str) -> str:
    host = urlparse(url).netloc.lower()
    if "airbnb." in host:
        return "AIRBNB"
    if "booking." in host:
        return "BOOKING"
    if "expedia." in host:
        return "EXPEDIA"
    return "OTHER"


def scrape_accommodation(url: str) -> Dict[str, Optional[str] | List[str]]:
    provider = _detect_provider(url)
    if provider == "AIRBNB":
        return _scrape_with_playwright(url, provider, _extract_airbnb)
    if provider == "BOOKING":
        return _scrape_with_playwright(url, provider, _extract_booking)
    # if provider == "EXPEDIA":
    #     return _scrape_expedia(url)
    # Fallback
    return {"provider": provider, "title": None, "description": None, "images": []}


def _scrape_with_playwright(url: str, provider: str, extractor) -> Dict[str, Optional[str] | List[str]]:
    def do_scrape(browser: Browser) -> str:
        context = browser.new_context(
            user_agent=USER_AGENT,
            locale="en-US",
        )
        try:
            page = context.new_page()
            page.set_default_timeout(CONTENT_TIMEOUT_MS)
            page.goto(url, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
            try:
                page.wait_for_load_state("networkidle", timeout=CONTENT_TIMEOUT_MS)
            except Exception:
                pass
            return page.content()
        finally:
            context.close()

    html = browser_pool.run(do_scrape)
    result = extractor(html, provider)

    if _is_blocked(result, html):
        raise ScrapeBlockedError(f"{provider} returned no usable listing data (possible bot block) for {url}")

    return result


_BLOCK_TITLE_MARKERS = (
    "attention required",
    "access denied",
    "just a moment",
    "pardon our interruption",
    "are you a human",
    "request unsuccessful",
)


def _is_blocked(result: Dict[str, Optional[str] | List[str]], html: str) -> bool:
    if not result["title"] and not result["description"]:
        return True
    doc_title_match = BeautifulSoup(html, "html.parser").select_one("title")
    doc_title = (doc_title_match.text if doc_title_match else "").lower()
    return any(marker in doc_title for marker in _BLOCK_TITLE_MARKERS)


def _extract_airbnb(html: str, provider: str) -> Dict[str, Optional[str] | List[str]]:
    soup = BeautifulSoup(html, "html.parser")

    title = _first_non_empty(
        soup.select_one('meta[property="og:title"]'),
        soup.select_one('meta[name="twitter:title"]'),
    )
    title_text = title.get("content") if title else None

    description_el = _first_non_empty(
        soup.select_one('meta[property="og:description"]'),
        soup.select_one('meta[name="description"]'),
        soup.select_one('meta[name="twitter:description"]'),
    )
    description_text = description_el.get("content") if description_el else None

    images: List[str] = []

    # Try JSON-LD blocks (Airbnb often embeds listing data)
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            imgs = _extract_images_from_jsonld(data)
            if imgs:
                images.extend(imgs)
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    imgs = _extract_images_from_jsonld(item)
                    if imgs:
                        images.extend(imgs)

    # Fallback to OpenGraph image(s)
    if not images:
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get("content"):
            images.append(og_image.get("content"))

    images_out = _dedupe_cap(images, 5)

    return {
        "provider": provider,
        "title": title_text,
        "description": description_text,
        "images": images_out,
    }


def _extract_booking(html: str, provider: str) -> Dict[str, Optional[str] | List[str]]:
    soup = BeautifulSoup(html, "html.parser")

    title = _first_non_empty(
        soup.select_one('meta[property="og:title"]'),
        soup.select_one('meta[name="twitter:title"]'),
        soup.select_one('title'),
    )
    title_text = (title.get("content") if title and title.name == "meta" else title.text.strip() if title else None)

    description_el = _first_non_empty(
        soup.select_one('meta[property="og:description"]'),
        soup.select_one('meta[name="description"]'),
        soup.select_one('meta[name="twitter:description"]'),
    )
    description_text = description_el.get("content") if description_el else None

    images: List[str] = []

    # JSON-LD images if present
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "{}")
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            images.extend(_extract_images_from_jsonld(data))
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    images.extend(_extract_images_from_jsonld(item))

    if not images:
        # Booking often has og:image
        og_image = soup.select_one('meta[property="og:image"]')
        if og_image and og_image.get("content"):
            images.append(og_image.get("content"))

    images_out = _dedupe_cap(images, 5)

    return {
        "provider": provider,
        "title": title_text,
        "description": description_text,
        "images": images_out,
    }


def _extract_images_from_jsonld(data: dict) -> List[str]:
    images: List[str] = []
    if "image" in data:
        image_val = data["image"]
        if isinstance(image_val, str):
            images.append(image_val)
        elif isinstance(image_val, list):
            images.extend([u for u in image_val if isinstance(u, str)])
        elif isinstance(image_val, dict):
            # Some formats use @type ImageObject
            url = image_val.get("url")
            if isinstance(url, str):
                images.append(url)
    return images


def _first_non_empty(*elements):
    for el in elements:
        if el is not None:
            return el
    return None


def _dedupe_cap(items: List[str], limit: int) -> List[str]:
    seen = set()
    out: List[str] = []
    for u in items:
        if isinstance(u, str) and u not in seen:
            seen.add(u)
            out.append(u)
            if len(out) >= limit:
                break
    return out
