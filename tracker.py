import time
import logging
import threading
from typing import Optional, Callable
from apple_music import get_now_playing, is_music_running
from lyrics import fetch_lyrics, get_current_line
from discord_rpc import DiscordRPC
from album_art import get_album_art_url

logger = logging.getLogger(__name__)

POLL_INTERVAL = 0.5


class MusicTracker:
    def __init__(self, on_update: Optional[Callable] = None):
        self.rpc = DiscordRPC()
        self.on_update = on_update
        self._running = False
        self._paused = False
        self._last_track = None
        self._cached_lyrics = None
        self._cached_art_url = None
        self._fetch_start_time = None
        self._fetch_start_position = None
        self.show_lyrics = True

    def run(self):
        self._running = True
        self.rpc.connect()
        logger.info("🎵 Music Presence tracker started")

        while self._running:
            try:
                if self._paused:
                    time.sleep(POLL_INTERVAL)
                    continue

                if not is_music_running():
                    if self._last_track:
                        logger.info("Apple Music closed")
                        self._reset()
                    time.sleep(POLL_INTERVAL * 3)
                    continue

                track = get_now_playing()

                if not track:
                    if self._last_track:
                        logger.info("Paused")
                        self._reset()
                    time.sleep(POLL_INTERVAL)
                    continue

                track_key = f"{track['title']}||{track['artist']}"

                if track_key != self._last_track:
                    logger.info(f"Now playing: {track['title']} — {track['artist']}")
                    self._last_track = track_key
                    self._cached_lyrics = None
                    self._cached_art_url = None

                    # Fetch dulu baru update presence
                    self._fetch_metadata(
                        track["title"], track["artist"],
                        track["album"], track["duration"], track_key
                    )

                # Get current lyric
                current_lyric = ""
                if self._cached_lyrics and self.show_lyrics:
                    current_lyric = get_current_line(self._cached_lyrics, track["position"])

                self.rpc.update(
                    title=track["title"],
                    artist=track["artist"],
                    album=track["album"],
                    current_lyric=current_lyric,
                    position=track["position"],
                    duration=track["duration"],
                    art_url=self._cached_art_url,
                )

                self._notify({"title": track["title"], "artist": track["artist"], "lyric": current_lyric})

            except Exception as e:
                logger.error(f"Tracker error: {e}", exc_info=True)

            time.sleep(POLL_INTERVAL)

    def _fetch_metadata(self, title, artist, album, duration, track_key):
        try:
            lyrics_result = [None]
            art_result = [None]

            def do_lyrics():
                lyrics_result[0] = fetch_lyrics(title, artist, album, duration)

            def do_art():
                art_result[0] = get_album_art_url(title, artist, album)

            t1 = threading.Thread(target=do_lyrics, daemon=True)
            t2 = threading.Thread(target=do_art, daemon=True)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            lyrics = lyrics_result[0]
            art_url = art_result[0]

            logger.info(f"  Fetch done. current={self._last_track}, expected={track_key}, match={self._last_track == track_key}")
            if self._last_track == track_key:
                self._cached_lyrics = lyrics
                self._cached_art_url = art_url
                self.rpc._last_track_key = None
                if lyrics:
                    logger.info(f"  ✓ Lyrics loaded ({len(lyrics)} lines)")
                else:
                    logger.info("  ✗ No lyrics found")
                if art_url:
                    logger.info("  ✓ Album art found")
        except Exception as e:
            logger.error(f"Metadata fetch error: {e}")

    def _reset(self):
        self._last_track = None
        self._cached_lyrics = None
        self._cached_art_url = None
        self._fetch_start_time = None
        self._fetch_start_position = None
        self.rpc.clear()
        self._notify(None)

    def pause(self):
        self._paused = True
        self.rpc.clear()

    def resume(self):
        self._paused = False

    def stop(self):
        self._running = False
        self.rpc.clear()
        self.rpc.disconnect()

    def _notify(self, data):
        if self.on_update:
            try:
                self.on_update(data)
            except Exception:
                pass