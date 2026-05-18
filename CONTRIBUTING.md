# Contributing to Xonotic RustChain Arena

Thank you for contributing to Xonotic RustChain Arena, a modded Xonotic FPS arena where players can earn RustChain tokens through competitive play and hardware-based antiquity bonuses.

## Project Overview

Xonotic RustChain Arena combines competitive FPS gameplay with blockchain rewards. Older hardware and slower processors earn higher antiquity multipliers, encouraging the use of vintage computing equipment.

## Development Setup

### Prerequisites

- Xonotic game client (0.8.6+)
- RustChain node running for token rewards
- Linux/Windows/macOS

### Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/Scottcjn/xonotic-rustchain.git
cd xonotic-rustchain

# Install Xonotic if not already installed
# Download from https://xonotic.org/

# Copy mod files to Xonotic data directory
cp -r rustchain/* ~/.xonotic/data/
```

## Code Style

- QuakeC for Xonotic game mods
- Follow existing code conventions
- Comment complex logic
- Use descriptive variable names

## Testing

```bash
# Run Xonotic with the mod
./xonotic-linux-sdl.sh +set fs_game rustchain +map DM

# Check console for errors
# Report any issues with version info
```

## Submitting Changes

1. Fork the repository
2. Create a branch: `git checkout -b fix/your-fix`
3. Make changes to QuakeC source
4. Test in game
5. Submit a pull request

## Ideas for Contributions

- New game modes leveraging antiquity bonuses
- Anti-cheat improvements
- Hardware fingerprinting for antiquity verification
- Leaderboard integration with RustChain
- Performance optimizations for vintage hardware
