"""Extract navigational link actions from HTML.

This module provides a small helper that finds internal links on a page
and returns a compact action description useful for page-extraction and
click-based scenario generation.
"""

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


class NavigationExtractor:
    """Extracts navigational link events scoped to a base URL.

    Only links that resolve to the same domain as `base_url` are returned.
    The extractor normalizes relative URLs and skips anchors and javascript
    pseudo-links.
    """

    def __init__(self, base_url: str):
        """Initialize with the page's base URL.

        Args:
            base_url: The page's canonical URL used to resolve relative links.
        """

        self.base_url = base_url
        self.base_domain = urlparse(base_url).netloc

    def extract(self, html: str):
        """Return a list of link action dicts found in `html`.

        Each returned event includes `target_url`, a simple `selector`
        (id, classes or tag), and a human-readable `description`.
        """

        soup = BeautifulSoup(html, "html.parser")
        events = []

        # Find all anchor tags with an href attribute
        for a in soup.find_all("a", href=True):
            href = a.get("href").strip()

            # Skip page anchors and javascript handlers
            if href.startswith("#") or href.lower().startswith("javascript"):
                continue

            # Resolve relative URLs against the base URL
            target_url = urljoin(self.base_url, href)
            parsed = urlparse(target_url)

            # Ignore external links (different domain)
            if parsed.netloc and parsed.netloc != self.base_domain:
                continue

            events.append({
                "target_url": target_url,
                "selector": self._build_selector(a),
                "description": f"Click link '{a.get_text(strip=True)}'",
            })

        return events

    def _build_selector(self, el):
        """Build a simple CSS-like selector for the element.

        Prefer ID, then class list, then the tag name as a fallback.
        """

        if el.get("id"):
            return f"#{el.get('id')}"
        if el.get("class"):
            return "." + ".".join(el.get("class"))
        return el.name
