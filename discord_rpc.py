import socket
import json
import struct
import time
import logging
import glob
import os
from typing import Optional

logger = logging.getLogger(__name__)

from config import DISCORD_CLIENT_ID

class DiscordRPC:
    def __init__(self, client_id: str = DISCORD_CLIENT_ID):
        self.client_id = client_id
        self.socket = None
        self.connected = False
        self._last_track_key = None
        self._last_details = None
        self._last_state = None

    def connect(self) -> bool:
        try:
            pipe = self._find_pipe()
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.connect(pipe)
            self._handshake()
            self.connected = True
            logger.info("Connected to Discord RPC")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to Discord: {e}")
            self.connected = False
            return False

    def disconnect(self):
        if self.socket:
            try:
                self.socket.close()
            except Exception:
                pass
        self.connected = False
        self.socket = None

    def _find_pipe(self) -> str:
        patterns = [
            "/var/folders/*/*/T/discord-ipc-*",
            f"{os.environ.get('TMPDIR', '/tmp')}discord-ipc-*",
            "/tmp/discord-ipc-*",
        ]
        for pattern in patterns:
            pipes = glob.glob(pattern)
            if pipes:
                return pipes[0]
        raise FileNotFoundError("Discord IPC pipe not found — is Discord running?")

    def _send(self, opcode: int, payload: dict):
        data = json.dumps(payload).encode()
        header = struct.pack("<II", opcode, len(data))
        self.socket.sendall(header + data)

    def _recv(self):
        try:
            header = self.socket.recv(8)
            if len(header) < 8:
                return None
            opcode, length = struct.unpack("<II", header)
            data = self.socket.recv(length)
            return json.loads(data.decode())
        except Exception:
            return None

    def _handshake(self):
        self._send(0, {"v": 1, "client_id": self.client_id})
        self._recv()

    def _reconnect(self) -> bool:
        self.disconnect()
        time.sleep(1)
        return self.connect()

    def update(self, title, artist, album, current_lyric, position, duration, art_url=None, force=False):
        if not self.connected:
            if not self.connect():
                return

        details = f"{title} by {artist}"[:128]
        if current_lyric and current_lyric != "♪":
            state = current_lyric[:128]
        elif current_lyric == "♪":
            state = "• • •"
        else:
            state = f"♪  {album}"[:128]

        # Skip update jika lirik tidak berubah
        if not force and details == self._last_details and state == self._last_state:
            return

        now = int(time.time())
        start_ts = now - int(position)
        end_ts = now + max(0, int(duration - position))

        activity = {
            "details": details,
            "state": state,
            "timestamps": {
                "start": start_ts,
                "end": end_ts,
            },
            "assets": {
                "large_image": art_url if art_url else "applemusiclogo",
                "large_text": album[:128] if album else "Apple Music",
                "small_image": "applemusiclogo",
                "small_text": f"{_fmt_time(position)} / {_fmt_time(duration)}",
            },
            "type": 2,
            "sync_id": title,
            "metadata": {
                "album": album,
                "artist": [artist],
                "album_id": "1",
                "artist_ids": ["1"],
            },
            "flags": 48,
            "buttons": [
                {
                    "label": "Play on Apple Music",
                    "url": f"https://music.apple.com/search?term={_urlencode(title + ' ' + artist)}"
                },
                {
                    "label": "Try it",
                    "url": f"https://github.com/MhmmdRFadhil/Discord-Music-Presence"
                }
            ]
        }

        payload = {
            "cmd": "SET_ACTIVITY",
            "args": {
                "pid": os.getpid(),
                "activity": activity,
            },
            "nonce": str(time.time()),
        }

        try:
            self._send(1, payload)
            resp = self._recv()
            if resp and resp.get("evt") == "ERROR":
                logger.warning(f"Discord error: {resp}")
            self._last_track_key = f"{title}||{artist}"
            self._last_details = details
            self._last_state = state
        except Exception as e:
            logger.warning(f"RPC update failed: {e}")
            self._reconnect()

    def clear(self):
        if not self.connected:
            return
        try:
            payload = {
                "cmd": "SET_ACTIVITY",
                "args": {"pid": os.getpid(), "activity": None},
                "nonce": str(time.time()),
            }
            self._send(1, payload)
            self._recv()
            self._last_track_key = None
            self._last_details = None
            self._last_state = None
        except Exception as e:
            logger.warning(f"RPC clear failed: {e}")
            self._reconnect()

def _urlencode(text: str) -> str:
    import urllib.parse
    return urllib.parse.quote(text)


def _fmt_time(seconds: float) -> str:
    m = int(seconds) // 60
    s = int(seconds) % 60
    return f"{m}:{s:02d}"