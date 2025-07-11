# 🎬 Spriter - Video to Sprite Sheet Converter

[![Tests](https://github.com/harperreed/spriter/actions/workflows/uv-pytest.yml/badge.svg)](https://github.com/harperreed/spriter/actions/workflows/uv-pytest.yml)
[![Coverage](https://github.com/harperreed/spriter/actions/workflows/uv-pytest-coverage.yml/badge.svg)](https://github.com/harperreed/spriter/actions/workflows/uv-pytest-coverage.yml)
[![Linting](https://github.com/harperreed/spriter/actions/workflows/py-ruff-lint.yaml/badge.svg)](https://github.com/harperreed/spriter/actions/workflows/py-ruff-lint.yaml)

A powerful, easy-to-use command-line tool that converts video files (MOV, MP4, MPG) into sprite sheets for game development, web animations, and other creative projects! 🎮✨

## ⚡ Quick Start

```bash
# Run directly with uvx (no installation required)
uvx --from git+https://github.com/harperreed/spriter.git spriter video.mp4 --preset web

# Or install globally and use anywhere
uv tool install git+https://github.com/harperreed/spriter.git
spriter video.mp4 --preset game
```

## 📋 Summary

Spriter is a Python CLI tool that leverages FFmpeg to extract frames from video files and arrange them into tile-based sprite sheets. Perfect for:

- 🎮 Game development (character animations, effects)
- 🌐 Web animations (CSS sprites, canvas animations)
- 📱 Mobile app development
- 🎨 Creative projects requiring frame-by-frame animations

### Key Features

- **Batch Processing**: Process single files or entire directories
- **Preset Configurations**: Quick setup for common use cases (game, web, hires)
- **Flexible Parameters**: Customize FPS, sprite size, and grid layout
- **Rich UI**: Beautiful progress indicators and configuration display
- **Smart Naming**: Automatic output file naming with parameter details
- **Multiple Formats**: Support for MOV, MP4, and MPG files

## 🚀 How to Use

### Prerequisites

- Python 3.12+
- FFmpeg (must be installed and available in PATH)
- UV package manager (recommended)

### Installation

#### Option 1: Quick Start with uvx (Recommended)

```bash
# Run directly without installation
uvx --from git+https://github.com/harperreed/spriter.git spriter video.mp4 --preset web

# Or from local directory
git clone https://github.com/harperreed/spriter.git
cd spriter
uvx --from . spriter video.mp4 --preset web
```

#### Option 2: Global Installation

```bash
# Install globally with uv tool
git clone https://github.com/harperreed/spriter.git
cd spriter
uv tool install .

# Now use anywhere
spriter video.mp4 --preset web
```

#### Option 3: Development Installation

```bash
# Clone and install for development
git clone https://github.com/harperreed/spriter.git
cd spriter
uv sync
uv run spriter video.mp4 --preset web
```

### Basic Usage

```bash
# Convert a single video file with default settings
spriter video.mp4

# Process an entire directory of videos
spriter ./videos/

# Use preset configurations
spriter video.mp4 --preset game    # 64x64, 10fps, 6x6 grid
spriter video.mp4 --preset web     # 32x32, 8fps, 4x4 grid
spriter video.mp4 --preset hires   # 128x128, 12fps, 8x8 grid
```

### Advanced Usage

```bash
# Custom parameters
spriter video.mp4 \
  --fps 15 \
  --size 48x48 \
  --grid 5x5 \
  --output custom_spritesheet.png

# Process directory with custom settings
spriter ./videos/ --preset web
```

### Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--fps` | `-f` | Frames per second to extract | 10 |
| `--size` | `-s` | Size of each sprite frame | 64x64 |
| `--grid` | `-g` | Grid layout (columns x rows) | 6x6 |
| `--output` | `-o` | Output file path | Auto-generated |
| `--preset` | `-p` | Use preset configuration | None |

### Preset Configurations

- **game**: `64x64` sprites, `10fps`, `6x6` grid - Perfect for retro games
- **web**: `32x32` sprites, `8fps`, `4x4` grid - Optimized for web use
- **hires**: `128x128` sprites, `12fps`, `8x8` grid - High-resolution animations

### Output File Naming

When no output file is specified, Spriter automatically generates descriptive filenames:

- With preset: `video_spritesheet_game.png`
- With custom params: `video_spritesheet_15fps_48x48_5x5.png`

## 🛠️ Tech Info

### Architecture

- **CLI Framework**: Click for command-line interface
- **UI/UX**: Rich library for beautiful terminal output
- **Video Processing**: FFmpeg integration via subprocess
- **Testing**: pytest with comprehensive test coverage
- **Code Quality**: Ruff for linting, pre-commit hooks

### Dependencies

```toml
[project]
dependencies = [
    "click>=8.2.1",    # CLI framework
    "rich>=14.0.0",    # Rich terminal output
]

[project.optional-dependencies]
dev = [
    "pytest>=8.4.1",   # Testing framework
]
```

### Development Setup

```bash
# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=spriter

# Run linting
uv run ruff check

# Install pre-commit hooks
uv run pre-commit install
```

### FFmpeg Integration

The tool uses FFmpeg's powerful video filter chain:

```bash
ffmpeg -i input.mp4 -vf "fps=10,scale=64x64,tile=6x6" -frames:v 1 output.png
```

- **fps**: Extracts frames at specified rate
- **scale**: Resizes each frame to target dimensions
- **tile**: Arranges frames in a grid pattern

### CI/CD Pipeline

- **GitHub Actions**: Automated testing on push/PR
- **Coverage Reports**: Pytest coverage with comment bot
- **Code Quality**: Ruff linting checks
- **Multi-workflow**: Separate jobs for testing and linting

### Project Structure

```
spriter/
├── spriter/
│   ├── __init__.py         # Package initialization
│   └── main.py             # Main CLI application
├── test_spriter.py         # Comprehensive test suite
├── pyproject.toml          # Project configuration
├── .github/workflows/      # CI/CD pipelines
├── .pre-commit-config.yaml # Code quality hooks
└── README.md              # This file!
```

### Error Handling

- **FFmpeg Detection**: Automatic check for FFmpeg availability
- **File Validation**: Support for MOV, MP4, MPG formats
- **Graceful Failures**: Detailed error messages and recovery suggestions
- **Progress Indicators**: Real-time feedback during conversion

### Testing

Comprehensive test suite covering:

- CLI argument parsing and validation
- File format detection and handling
- FFmpeg integration and error handling
- Preset configuration application
- Directory processing functionality
- Integration tests with real video files

---

Built with ❤️ by [Harper Reed](https://github.com/harperreed) • Perfect for indie game developers, web designers, and creative coders! 🎨🚀
