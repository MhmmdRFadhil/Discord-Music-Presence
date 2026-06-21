from setuptools import setup

APP = ['main.py']
DATA_FILES = ['icon.png']
OPTIONS = {
    'argv_emulation': False,
    'plist': {
        'CFBundleName': 'Music Presence',
        'CFBundleDisplayName': 'Music Presence',
        'CFBundleIdentifier': 'com.user.musicpresence',
        'CFBundleVersion': '1.1.0',
        'CFBundleShortVersionString': '1.1.0',
        'CFBundleIconFile': 'icon',
        'LSUIElement': True,
        'NSAppleEventsUsageDescription': 'Required to read current track from Apple Music.',
    },
    'packages': ['rumps', 'requests'],
    'includes': ['apple_music', 'lyrics', 'discord_rpc', 'album_art', 'tracker'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
