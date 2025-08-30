# n2unes

A command-line music player interface written in Python 3 that provides seamless integration with foobar2000. n2unes enables quick music search, queuing, and playback control through a terminal interface with persistent music library indexing.

## Features

### Core Functionality
- **Fast Music Search**: Wildcard-based searching with fuzzy matching across indexed music libraries
- **Playlist Management**: Queue tracks directly to foobar2000 with configurable queue behavior
- **Database Persistence**: SQLite-based music library indexing
- **Media Player Control**: Direct playback control (play, pause, stop, next, previous)
- **Multi-format Support**: Supports MP3, FLAC, OGG, M4A, AAC, WAV, MPC, and playlist formats

### Search & Display
- Configurable result display with line numbers and path options
- Batch queuing of search results with customizable limits
- Real-time match counting and result pagination

### System Integration
- Windows-optimized with foobar2000 integration
- Automatic music library scanning across multiple directories
- Persistent configuration through `config.py`

## Installation

1. Ensure Python 3.x is installed
2. Copy `config.py.example` to `config.py` and configure:
   - Set `FOOBAR_PATH` to your foobar2000 executable location
   - Update `MUSIC_PATHS` with your music directory locations
3. Run `python n2unes.py`

## Usage

### Interactive Commands

#### Search
```
artist song name    # Search for tracks matching the pattern
```

#### System Commands
```
/index              # Re-index music library
/info               # Display library statistics
/exit               # Exit application
```

#### Playback Control
```
/play               # Start playback
/pause              # Pause playback
/stop               # Stop playback  
/next               # Next track
/prev               # Previous track
```

#### Playlist Management
```
/playlist clear     # Clear current playlist
/playlist sort      # Sort playlist by title
```

#### Match Navigation
```
/match [index]      # Select specific match by index number
```

#### Configuration
```
/set [option] [value]   # Runtime configuration changes
/set queue_clear True   # Example: enable queue clearing
```

## Configuration Options

All options are configured in `config.py`:

### Queue Behavior
- `QUEUE_CLEAR`: Clear queue before adding new results (default: True)
- `QUEUE_MATCHES`: Queue multiple search results (default: True)  
- `QUEUE_MATCHES_MAX`: Maximum matches to queue (default: 50)

### Display Settings
- `DISPLAY_MATCHES`: Show search results (default: True)
- `DISPLAY_MATCHES_MAX`: Maximum results to display (default: 50)
- `DISPLAY_MATCHES_TOTALS`: Show total match count (default: True)
- `DISPLAY_MATCHES_FULLPATH`: Display full file paths (default: False)
- `DISPLAY_MATCHES_LINE_NUMBERS`: Show result line numbers (default: True)

### Playback Preferences
- `PLAY_MATCHES_MODE`: Selection mode - "first" or "random" (default: "random")
- `PLAY_MATCHES_TYPE`: Preferred file type when multiple formats available (default: "flac")

## License

Open source project suitable for personal and educational use.
