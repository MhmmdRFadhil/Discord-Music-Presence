# 🎵 Music Presence

A macOS menu bar app that displays real-time Apple Music lyrics as Discord Rich Presence — complete with album art and a progress bar.

## Preview

<img width="443" height="157" alt="image" src="https://github.com/user-attachments/assets/10ad6a3b-f9f5-43b4-9806-d32a3127f253" />

In the macOS menu bar:

<img width="316" height="286" alt="image" src="https://github.com/user-attachments/assets/5692322b-c7de-42a1-a6ff-11c6db6454a1" />

---

## Features

- Real-time detection of the currently playing track in Apple Music
- Synced lyrics powered by [LRCLIB](https://lrclib.net)
- Automatic album art via the iTunes Search API
- Native Discord progress bar (start/end timestamps)
- Menu bar app — no terminal window needed
- Pause/Resume presence directly from the menu bar
- Auto-reconnects to Discord if the connection drops

---

## Requirements

- macOS
- Python 3.9+
- Apple Music app
- Discord Desktop app

---

## Setup

### 1. Clone the repo

```bash
git clone https://github.com/MhmmdRFadhil/Discord-Music-Presence
cd music-presence
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Create a Discord Application

1. Open the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name (e.g. "Apple Music")
3. Copy the **Application ID** from the General Information page

### 4. Upload Art Assets

Still on your application's Developer Portal page:

1. Go to **Rich Presence → Art Assets**
2. Upload an Apple Music logo and name it exactly: `applemusiclogo`
3. Click **Save Changes** and wait 1-2 minutes for it to be processed

### 5. Set the Client ID

Copy the example config file and add your own Client ID:

```bash
cp config.example.py config.py
```

Open `config.py` and replace the placeholder:
```python
DISCORD_CLIENT_ID = "YOUR_CLIENT_ID_HERE"
```
with the Application ID from step 3.

`config.py` is git-ignored, so your personal Client ID is never committed and won't be overwritten by future `git pull` updates.

### 6. Run

```bash
python3 main.py
```

An icon will appear in the menu bar. Make sure **Discord desktop** and **Apple Music** are both open, then play a song.

---

## Building the App (.app)

To avoid running it from the terminal every time:

### 1. Prepare the icon

Place `icon.png` (for the menu bar) and `icon.icns` (for the app icon) in the project root.

Convert PNG to ICNS:
```bash
mkdir icon.iconset
sips -z 16 16   icon.png --out icon.iconset/icon_16x16.png
sips -z 32 32   icon.png --out icon.iconset/icon_16x16@2x.png
sips -z 32 32   icon.png --out icon.iconset/icon_32x32.png
sips -z 64 64   icon.png --out icon.iconset/icon_32x32@2x.png
sips -z 128 128 icon.png --out icon.iconset/icon_128x128.png
sips -z 256 256 icon.png --out icon.iconset/icon_128x128@2x.png
sips -z 256 256 icon.png --out icon.iconset/icon_256x256.png
sips -z 512 512 icon.png --out icon.iconset/icon_256x256@2x.png
sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
iconutil -c icns icon.iconset -o icon.icns
```

### 2. Build

```bash
pip3 install py2app
rm -rf build dist
python3 setup.py py2app
```

### 3. Install to Applications

```bash
rm -rf "/Applications/Music Presence.app"
cp -r "dist/Music Presence.app" /Applications/
```

Open it from Launchpad. For auto-start on login, add it via **System Settings → General → Login Items**.

### 4. Updating after code changes

Every time you change the code, repeat steps 2 and 3.

---

## Usage

1. Open **Discord** and **Apple Music**
2. Launch **Music Presence** from Launchpad (an icon appears in the menu bar)
3. Play any song — your Discord status updates automatically
4. Click the menu bar icon to see the current track, or to Pause/Resume the presence

In Discord, make sure **User Settings → Activity Privacy → Display current activity as a status message** is turned **ON**.

---

## Project Structure

```
music-presence/
├── main.py          # Menu bar app (rumps)
├── tracker.py        # Main loop — orchestrates all components
├── apple_music.py     # Reads the current track via AppleScript
├── lyrics.py          # Fetches & syncs lyrics from LRCLIB
├── discord_rpc.py     # Talks to Discord over the IPC socket
├── album_art.py        # Fetches album art from the iTunes Search API
├── requirements.txt
├── setup.py            # Builds the .app with py2app
├── icon.png            # Menu bar icon
└── icon.icns           # App icon
```

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Presence doesn't appear | Make sure the Discord desktop app is open and `DISCORD_CLIENT_ID` is correct |
| Lyrics not found | The song might not exist on LRCLIB — check manually at [lrclib.net](https://lrclib.net) |
| Menu bar icon doesn't show | Make sure `icon.png` exists in the project root and the path in `main.py` is correct |
| Album art doesn't appear | Wait a few seconds — fetching from the iTunes API takes a moment |
| App is "not responding" | Make sure you're using the latest code (UI updates run on the main thread) |
| Logo still shows a question mark | Make sure the `applemusiclogo` asset has been uploaded and approved in the Discord Developer Portal |

---

## How It Works

```
Apple Music (AppleScript)
        │
        ▼
   Detect track + position
        │
        ├──► LRCLIB API ──► Synced lyrics
        │
        ├──► iTunes API ──► Album art
        │
        ▼
  Discord IPC Socket ──► Rich Presence
        │
        ▼
   Menu Bar (rumps)
```

The app polls every 0.5 seconds to read the current playback position and display the matching lyric line. Updates are only sent to Discord when something actually changes, to stay within rate limits.

---

## License

Free to use and modify for personal purposes.
