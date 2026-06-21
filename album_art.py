import requests
import logging
from functools import lru_cache
from typing import Optional

logger = logging.getLogger(__name__)


@lru_cache(maxsize=32)
def get_album_art_url(title: str, artist: str, album: str = "") -> Optional[str]:
    """
    Fetch album art URL from iTunes Search API.
    Returns a high-res image URL or None.
    """
    try:
        params = {
            "term": f"{title} {artist} {album}".strip(),
            "media": "music",
            "entity": "song",
            "limit": 5,
        }
        resp = requests.get(
            "https://itunes.apple.com/search",
            params=params,
            timeout=5
        )

        if resp.status_code != 200:
            return None

        data = resp.json()
        results = data.get("results", [])

        if album:
            for item in results:
                art_url = item.get("artworkUrl100", "")
                item_album = item.get("collectionName", "").lower()
                if art_url and album.lower() in item_album:
                    return art_url.replace("100x100bb", "600x600bb")

        for item in results:
            art_url = item.get("artworkUrl100", "")
            if art_url:
                return art_url.replace("100x100bb", "600x600bb")

    except requests.RequestException as e:
        logger.warning(f"Album art fetch failed: {e}")

    return None
