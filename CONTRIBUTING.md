# Contributing

Thanks for contributing to Xonotic RustChain Arena. This repo combines Xonotic
server setup, DarkPlaces modding, RTC reward mechanics, Discord integration, and
AI bot experiments, so changes should be focused and testable.

## Getting Started

1. Read `README.md` for gameplay systems and the quick start path.
2. Review the relevant docs before editing:
   - `deploy/SETUP_GUIDE.md` for server setup.
   - `mapping/` for arena and Quake map guidance.
   - `sdk/` for arena SDK and design research.
   - `SOPHIA_ARENA_README.md` for Sophia/DarkPlaces context.
3. Work on a focused branch:

   ```bash
   git checkout -b your-change-name
   ```

## Development Workflow

Keep pull requests scoped to one area:

- Gameplay economy or RTC reward logic.
- Weapon, style-rank, or anti-cheat behavior.
- Bot AI or Ollama integration.
- Discord bridge and event notifications.
- Maps, textures, or SDK documentation.

Avoid mixing game-balance changes with infrastructure changes. Reviewers need to
understand whether a PR affects gameplay, rewards, deployment, or docs.

## Validation

For code or gameplay changes, include:

- Xonotic/DarkPlaces version.
- Commands used to start the arena.
- Python version and dependencies installed.
- Map or mode tested.
- Expected vs observed RTC reward or gameplay behavior.

For docs-only changes, include the files reviewed and the setup path affected.

## Contribution Guidelines

- Do not hardcode real wallets, API keys, Discord tokens, or node secrets.
- Keep reward logic deterministic and auditable.
- Document balance changes to RTC payouts or style multipliers.
- Separate asset/model/map contributions from Python server logic.

## Pull Request Checklist

Before opening a PR, include:

- Summary of the gameplay, rewards, bot, Discord, or docs area affected.
- Test commands and observed output.
- Any maps/assets added and their license/source.
- Known limitations or untested modes.

