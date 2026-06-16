import rumps
import threading
import logging
import webbrowser
from tracker import MusicTracker
from config import DONATE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)

class MusicPresenceApp(rumps.App):
    def __init__(self):
        super().__init__(
            name="MusicPresence",
            icon="icon.png",
            template=True,
            quit_button=None
        )

        self.tracker = MusicTracker(on_update=self.on_track_update)
        self.title = ""
        self._presence_active = True
        self._lyrics_state = True

        # Header
        self.app_name_item = rumps.MenuItem("Music Presence", callback=self.open_github)

        # Now Playing section
        self.now_playing_header = rumps.MenuItem("Now Playing", callback=None)
        self.status_item = rumps.MenuItem("♫  Idle", callback=None)
        self._current_title = None
        self._current_artist = None

        # Configuration section
        self.config_header = rumps.MenuItem("Configuration", callback=None)
        self.presence_toggle = rumps.MenuItem("Presence is active", callback=self.toggle_presence)
        self.presence_toggle.state = True
        self.lyrics_toggle = rumps.MenuItem("Show Lyrics", callback=self.toggle_lyrics)
        self.lyrics_toggle.state = True

        # Footer
        self.donate_item = rumps.MenuItem("♥  Donate", callback=self.open_donate)
        self.exit_item = rumps.MenuItem("Exit", callback=self.quit_app)

        self.menu = [
            self.app_name_item,
            None,
            self.now_playing_header,
            self.status_item,
            None,
            self.config_header,
            self.presence_toggle,
            self.lyrics_toggle,
            None,
            self.donate_item,
            None,
            self.exit_item,
        ]

        # Disable status item pada awal karena belum ada lagu
        self.status_item._menuitem.setEnabled_(False)

    def on_track_update(self, track_info):
        self._pending_update = track_info

    @rumps.timer(1)
    def check_update(self, _):
        if not hasattr(self, '_pending_update'):
            return
        data = self._pending_update
        if isinstance(data, dict):
            title = data.get("title", "")
            artist = data.get("artist", "")
            title_display = title[:20] + "…" if len(title) > 20 else title
            self.now_playing_header.title = "Now Playing"
            self.status_item.title = f"♫  {title_display} by {artist}"
            self.status_item._menuitem.setEnabled_(True)
            self.status_item.set_callback(self.open_in_apple_music)
            self._current_title = title
            self._current_artist = artist
        elif data is None:
            self.now_playing_header.title = "Now Playing"
            self.status_item.title = "♫  Idle"
            self.status_item._menuitem.setEnabled_(False)
            self.status_item.set_callback(None)
            self._current_title = None
            self._current_artist = None

    def open_in_apple_music(self, _):
        if self._current_title and self._current_artist:
            import urllib.parse
            query = urllib.parse.quote(f"{self._current_title} {self._current_artist}")
            webbrowser.open(f"music://music.apple.com/search?term={query}")

    def _set_lyrics_enabled(self, enabled: bool):
        if enabled:
            self.lyrics_toggle.state = self._lyrics_state
            self.tracker.show_lyrics = self._lyrics_state
            self.lyrics_toggle.title = "Show Lyrics"
            self.lyrics_toggle.set_callback(self.toggle_lyrics)
        else:
            self._lyrics_state = bool(self.lyrics_toggle.state)
            self.lyrics_toggle.state = False
            self.lyrics_toggle.title = "Show Lyrics"
            self.tracker.show_lyrics = False
            self.lyrics_toggle.set_callback(None)

    def toggle_presence(self, sender):
        self._presence_active = not self._presence_active
        sender.state = self._presence_active
        self._set_lyrics_enabled(self._presence_active)
        if self._presence_active:
            self.tracker.resume()
        else:
            self.tracker.pause()

    def toggle_lyrics(self, sender):
        sender.state = not sender.state
        self._lyrics_state = bool(sender.state)
        self.tracker.show_lyrics = sender.state

    def open_donate(self, _):
        webbrowser.open(DONATE_URL)

    def open_github(self, _):
        webbrowser.open("https://github.com/MhmmdRFadhil/Discord-Music-Presence")

    def quit_app(self, _):
        self.tracker.stop()
        rumps.quit_application()


if __name__ == "__main__":
    app = MusicPresenceApp()
    t = threading.Thread(target=app.tracker.run, daemon=True)
    t.start()
    app.run()
