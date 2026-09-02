import logging
import re
import unicodedata
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Browser

from ports.tour_provider import TourProvider
from schemas.tours import TourResult
from utils.browser_pool import browser_pool

logger = logging.getLogger(__name__)

BASE_URL = "https://www.getyourguide.com"
NAV_TIMEOUT_MS = 20000
CONTENT_TIMEOUT_MS = 15000
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
)

CURRENCY_SYMBOLS = {"$": "USD", "€": "EUR", "£": "GBP"}

# Best-effort seed list — city slugs are "<city>-l<id>" where the numeric id is
# assigned by GetYourGuide and not derivable from the city name. Every entry
# below was verified by cross-checking a GetYourGuide search result and the
# destination page content (title/URL matching the exact city, not a same-named
# region/neighborhood/wrong-country city or a country/POI page) — do not add
# more without the same verification.
_CITY_SLUGS: dict[str, str] = {
    "abu dhabi": "abu-dhabi-l494",
    "agra": "agra-l824",
    "amman": "amman-l1035",
    "amsterdam": "amsterdam-l36",
    "antalya": "antalya-l172",
    "athens": "athens-l91",
    "auckland": "auckland-l822",
    "bali": "bali-l347",
    "bangkok": "bangkok-l169",
    "barcelona": "barcelona-l45",
    "beijing": "beijing-l186",
    "beirut": "beirut-l1484",
    "belgrade": "belgrade-l1688",
    "berlin": "berlin-l17",
    "bogota": "bogota-l361",
    "bologna": "bologna-l1431",
    "bordeaux": "bordeaux-l287",
    "boston": "boston-l260",
    "brussels": "brussels-l8",
    "bucharest": "bucharest-l111",
    "budapest": "budapest-l29",
    "buenos aires": "buenos-aires-l1",
    "cairo": "cairo-l92",
    "cancun": "cancun-l150",
    "cape town": "cape-town-l103",
    "cartagena": "cartagena-l362",
    "casablanca": "casablanca-l244",
    "chicago": "chicago-l225",
    "cologne": "cologne-l19",
    "copenhagen": "copenhagen-l12",
    "cusco": "cusco-l359",
    "delhi": "new-delhi-l231",
    "doha": "doha-l1885",
    "dubai": "dubai-l173",
    "dublin": "dublin-l31",
    "dubrovnik": "dubrovnik-l513",
    "edinburgh": "edinburgh-l44",
    "florence": "florence-l32",
    "frankfurt": "frankfurt-l21",
    "geneva": "geneva-l54",
    "guadalajara": "guadalajara-l677",
    "hamburg": "hamburg-l23",
    "hanoi": "hanoi-l205",
    "havana": "havana-l480",
    "helsinki": "helsinki-l13",
    "ho chi minh city": "ho-chi-minh-city-l272",
    "hong kong": "hong-kong-l174",
    "istanbul": "istanbul-l56",
    "jaipur": "jaipur-l1149",
    "jakarta": "jakarta-l278",
    "jerusalem": "jerusalem-l97",
    "krakow": "krakow-l40",
    "kuala lumpur": "kuala-lumpur-l171",
    "kyoto": "kyoto-l96826",
    "las vegas": "las-vegas-l58",
    "lima": "lima-l39",
    "lisbon": "lisbon-l42",
    "ljubljana": "ljubljana-l318",
    "london": "london-l57",
    "los angeles": "los-angeles-l179",
    "lyon": "lyon-l295",
    "madrid": "madrid-l46",
    "manila": "manila-l235",
    "marrakech": "marrakesh-l208",
    "marseille": "marseille-l292",
    "medellin": "medellin-l1215",
    "melbourne": "melbourne-l202",
    "mexico city": "mexico-city-l194",
    "miami": "miami-l176",
    "milan": "milan-l139",
    "montreal": "montreal-l195",
    "mumbai": "mumbai-l201",
    "munich": "munich-l26",
    "nairobi": "nairobi-l267",
    "naples": "naples-l162",
    "new orleans": "new-orleans-l370",
    "new york": "new-york-city-l59",
    "nice": "nice-l314",
    "orlando": "orlando-l191",
    "oslo": "oslo-l38",
    "osaka": "osaka-l1204",
    "panama city": "panama-city-l811",
    "paris": "paris-l16",
    "phuket": "phuket-l32123",
    "pisa": "pisa-l157",
    "porto": "porto-l151",
    "prague": "prague-l10",
    "punta cana": "punta-cana-l411",
    "queenstown": "queenstown-l498",
    "quito": "quito-l504",
    "reykjavik": "reykjavik-l30",
    "riga": "riga-l213",
    "rio de janeiro": "rio-de-janeiro-l9",
    "riyadh": "riyadh-l153731",
    "rome": "rome-l33",
    "san francisco": "san-francisco-l61",
    "san juan": "san-juan-puerto-rico-l355",
    "santiago": "santiago-chile-l226",
    "sao paulo": "sao-paulo-l384",
    "seattle": "seattle-l198",
    "seoul": "seoul-l197",
    "seville": "seville-l48",
    "shanghai": "shanghai-l178",
    "siem reap": "siem-reap-l274",
    "singapore": "singapore-l170",
    "split": "split-l268",
    "stockholm": "stockholm-l50",
    "sydney": "sydney-l200",
    "taipei": "taipei-city-l190",
    "tallinn": "tallinn-l394",
    "tel aviv": "tel-aviv-l487",
    "tokyo": "tokyo-l193",
    "toronto": "toronto-l177",
    "vancouver": "vancouver-l189",
    "venice": "venice-l35",
    "verona": "verona-l389",
    "vienna": "vienna-l7",
    "vilnius": "vilnius-l245",
    "warsaw": "warsaw-l41",
    "washington dc": "washington-dc-l62",
    "zagreb": "zagreb-l803",
    "zurich": "zurich-l55",
}

# Spanish name -> the English _CITY_SLUGS key it should resolve to. Only needed
# where the Spanish exonym differs from the English name after accent-stripping
# (e.g. "Niza" vs "nice"); cities that are spelled the same in both languages
# once normalized (Paris, Lyon, Berlín/berlin, Dubái/dubai, ...) need no entry
# here since _normalize_city's accent-stripping already makes them match.
_CITY_ES_TO_EN: dict[str, str] = {
    "abu dabi": "abu dhabi",
    "aman": "amman",
    "atenas": "athens",
    "belgrado": "belgrade",
    "bolonia": "bologna",
    "bombay": "mumbai",
    "bruselas": "brussels",
    "bucarest": "bucharest",
    "burdeos": "bordeaux",
    "ciudad de mexico": "mexico city",
    "ciudad de panama": "panama city",
    "ciudad del cabo": "cape town",
    "ciudad ho chi minh": "ho chi minh city",
    "colonia": "cologne",
    "copenhague": "copenhagen",
    "cracovia": "krakow",
    "cuzco": "cusco",
    "edimburgo": "edinburgh",
    "el cairo": "cairo",
    "estambul": "istanbul",
    "estocolmo": "stockholm",
    "florencia": "florence",
    "ginebra": "geneva",
    "hamburgo": "hamburg",
    "jerusalen": "jerusalem",
    "kioto": "kyoto",
    "la habana": "havana",
    "lisboa": "lisbon",
    "liubliana": "ljubljana",
    "londres": "london",
    "marraquech": "marrakech",
    "marsella": "marseille",
    "napoles": "naples",
    "niza": "nice",
    "nueva delhi": "delhi",
    "nueva orleans": "new orleans",
    "nueva york": "new york",
    "oporto": "porto",
    "pekin": "beijing",
    "praga": "prague",
    "reikiavik": "reykjavik",
    "riad": "riyadh",
    "roma": "rome",
    "sevilla": "seville",
    "seul": "seoul",
    "singapur": "singapore",
    "tallin": "tallinn",
    "tokio": "tokyo",
    "varsovia": "warsaw",
    "venecia": "venice",
    "viena": "vienna",
    "washington": "washington dc",
    "yakarta": "jakarta",
}


class GetYourGuideAdapter(TourProvider):
    """Only file in the codebase allowed to know about GetYourGuide's URL scheme."""

    def search_tours(self, city: str) -> list[TourResult]:
        slug = _resolve_slug(city)
        if not slug:
            return []

        html = browser_pool.run(lambda browser: _scrape_listing_page(browser, slug))
        return _parse_tours(html, city)

    def get_fallback_search_url(self, city: str) -> str | None:
        # No verified GetYourGuide URL format takes a free-text city query — its
        # own search UI only resolves a location from an autocomplete pick, never
        # from typed text, so an unmapped city has no fallback link (None) rather
        # than a guessed one. Only cities already resolvable via _CITY_SLUGS get
        # a real link, straight to that city's listing page.
        slug = _resolve_slug(city)
        return f"{BASE_URL}/{slug}/" if slug else None


def _resolve_slug(city: str) -> str | None:
    normalized = _normalize_city(city)
    normalized = _CITY_ES_TO_EN.get(normalized, normalized)
    return _CITY_SLUGS.get(normalized)


def _normalize_city(city: str) -> str:
    stripped = unicodedata.normalize("NFKD", city.strip().lower())
    return "".join(c for c in stripped if not unicodedata.combining(c))


def _scrape_listing_page(browser: Browser, slug: str) -> str:
    context = browser.new_context(user_agent=USER_AGENT, locale="en-US")
    try:
        page = context.new_page()
        page.set_default_timeout(CONTENT_TIMEOUT_MS)
        page.goto(f"{BASE_URL}/{slug}/", timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        try:
            page.wait_for_load_state("networkidle", timeout=CONTENT_TIMEOUT_MS)
        except Exception:
            pass
        return page.content()
    finally:
        context.close()


# GetYourGuide serves at least two structurally different page variants for the
# same city listing (observed via its `data-theme-variant` attribute flipping
# between "old" and "new" across otherwise-identical requests, likely an A/B
# experiment). "old" renders plain semantic HTML (card-block__container etc.);
# "new" renders a Vue/server-driven-UI grid whose cards only expose stable
# `id`s scoped as "<tourId>-<field>" (verticalActivityCard). Try "old" first,
# fall back to "new" so either one still produces results.
_GRANULAR_CARD_SELECTOR = 'a[data-test-id="verticalActivityCard"]'
_DURATION_PATTERN = re.compile(r"\d+.*?(hour|hora|day|d[ií]a|minute|min)", re.IGNORECASE)


def _parse_tours(html: str, city: str) -> list[TourResult]:
    soup = BeautifulSoup(html, "html.parser")

    cards = soup.select("a.card-block__container")
    if cards:
        results = [_parse_card(card) for card in cards]
    else:
        cards = soup.select(_GRANULAR_CARD_SELECTOR)
        results = [_parse_granular_card(card) for card in cards]

    results = [result for result in results if result is not None]
    if not results:
        logger.warning(
            "GetYourGuide: no tour cards parsed for city=%r under either known page variant "
            "(old 'card-block__container' or new 'verticalActivityCard') — its HTML structure "
            "may have changed again and the adapter's selectors need updating",
            city,
        )
    return results


def _parse_card(card) -> TourResult | None:
    try:
        title_el = card.select_one("h3.card-body__title")
        href = card.get("href")
        if not title_el or not href:
            return None

        rating, review_count = _parse_rating(card, ".c-activity-rating__rating", ".card-footer__review-count")
        price, currency = _parse_price(card, ".activity-price__text-price")
        image_el = card.select_one("img.c-image__img")

        return TourResult(
            title=title_el.get_text(strip=True),
            price=price,
            currency=currency,
            rating=rating,
            review_count=review_count,
            image_url=image_el.get("src") if image_el else None,
            external_url=urljoin(BASE_URL, href),
        )
    except Exception:
        return None


def _parse_granular_card(card) -> TourResult | None:
    try:
        title_el = card.select_one('[id$="-title"]')
        href = card.get("href")
        if not title_el or not href:
            return None

        rating, review_count = _parse_rating(card, '[id$="-polished-rating-text"]', '[id$="-polished-review-description"]')
        price, currency = _parse_price(card, '[id$="-polished-price-start-v2"]')
        image_el = card.select_one("img.c-image__img")

        return TourResult(
            title=title_el.get_text(strip=True),
            price=price,
            currency=currency,
            rating=rating,
            review_count=review_count,
            image_url=image_el.get("src") if image_el else None,
            external_url=urljoin(BASE_URL, href),
            duration=_parse_granular_duration(card),
        )
    except Exception:
        return None


def _parse_price(card, selector: str) -> tuple[float, str]:
    price_el = card.select_one(selector)
    if not price_el:
        return 0.0, "USD"

    text = price_el.get_text(strip=True)
    symbol = text[0] if text and not text[0].isdigit() else ""
    currency = CURRENCY_SYMBOLS.get(symbol, "USD")
    numeric = "".join(c for c in text if c.isdigit() or c == ".")
    return float(numeric) if numeric else 0.0, currency


def _parse_rating(card, rating_selector: str, review_count_selector: str) -> tuple[float | None, int | None]:
    rating_el = card.select_one(rating_selector)
    rating = float(rating_el.get_text(strip=True)) if rating_el else None

    review_el = card.select_one(review_count_selector)
    review_count = None
    if review_el:
        digits = review_el.get_text(strip=True).strip("()").replace(",", "")
        review_count = int(digits) if digits.isdigit() else None

    return rating, review_count


def _parse_granular_duration(card) -> str | None:
    """Best-effort duration extraction: the "new" variant only exposes a single
    joined text (e.g. "1 - 2 days • Optional audio guide") with no per-segment
    tagging in the DOM, so only a segment that clearly looks like a duration is
    used — anything ambiguous is left as None rather than guessed."""
    attrs_el = card.select_one('[id$="-attributes"]')
    if not attrs_el:
        return None
    for segment in attrs_el.get_text(strip=True).split("•"):
        segment = segment.strip()
        if segment and _DURATION_PATTERN.search(segment):
            return segment
    return None
