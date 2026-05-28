# RustChain Awakening: Story Mode Implementation Notes

This campaign uses Xonotic's native `g_campaign` system plus a small SVQC story layer.

## Running

- Deploy campaign file: `./source/build.sh story`
- Launch: `./rustchain_story_launcher.sh`

## Where The Story Logic Lives

- Campaign file: `story/maps/campaignrustchain.txt`
- Mission briefings + hooks: `source/qcsrc/server/campaign.qc`
- Story helpers + map entities: `source/qcsrc/server/rustchain_story.qc`

## Objective Mode

- RustChain campaign now enforces objective-driven progression by default:
  - `g_rustchain_objective_mode 1` (default)
  - Forces `fraglimit 0`, `leadlimit 0`, `timelimit 0` on mission start
- Use objective entities in maps to complete missions instead of score/time.

## Map Scripting Building Blocks (Quake-Style)

### RustChain Node (checkpoint/beat trigger)

Use a standard trigger to call a story node once, then let the node fire map targets.

1. Place a `trigger_multiple` brush.
2. Set `trigger_multiple.target` to the node's `targetname`.
3. Place a point entity:

- `classname` = `target_rustchain_node`
- `targetname` = `node_01` (example)
- `target` = whatever should happen after activation (doors, relays, enemy spawns, etc.)

On first activation, the node:
- Prints `[RustChain] Node activated ...`
- Increments a per-mission counter
- Fires its own `target`s via `SUB_UseTargets()`

### RustChain Wave (reinforcement trigger)

Use this as a target from nodes/logs/relays to add hostile pressure.

- `classname` = `target_rustchain_wave`
- `count` = number of bots to add (`<=0` uses mission default)
- `health` = optional wave skill override (if omitted, mission/stage default skill is used)
- `message` = optional narrative warning print
- `netname` = faction tag (`bbd`, `boris`, `mixed`)

On activation, it raises `bot_number`, applies `bot_fixcount(true)`, and can fire further targets.

### RustChain Dialogue (line trigger)

- `classname` = `target_rustchain_dialogue`
- `message` = speaker (`sophia`, `bbd`, `boris`)
- `netname` = dialogue line text

Use this with `trigger_once` or from relays after node/log/wave events.

Supported speaker tags currently:
- `sophia`
- `bbd`
- `boris`
- `survivor`
- `archivist`
- `vossl`
- `player`
- `narrator`

### Lore Log Pickup (counts toward the Mission 6 reveal)

1. Place a `trigger_multiple` brush over a terminal area.
2. Set `trigger_multiple.target` to the log entity's `targetname`.
3. Place a point entity:

- `classname` = `target_rustchain_log`
- `targetname` = `log_a` (example)
- `message` = log title (shown in header)
- `netname` = log body text (supports `\\n`)

On first activation, the log:
- Prints a `=== TITLE ===` block with the body text
- Increments `rustchain_story_logs_collected`
- If in Mission 6 and logs reach 3, prints Sophia's descendant reveal line

### RustChain Exit (objective completion)

- `classname` = `target_rustchain_exit`

Use with a `trigger_once` volume at extraction points.

When touched by a real player:
- Forces campaign win (`campaign_forcewin = true`)
- Ends the match by setting `timelimit -1`
- Campaign advances through normal intermission/campaign pipeline

## Notes

- The descendant reveal is intentionally scripted in SVQC (not menu-only) so it works in-game.
- `elyan_labs` and `chambers_ruins` both use objective entities (`target_rustchain_node`, `target_rustchain_log`, `target_rustchain_wave`, `target_rustchain_exit`).
- Mission maps currently wired to objective flow:
  - `elyan_labs` (Mission 1)
  - `first_signal` (Mission 2)
  - `museum_vault` (Mission 3)
  - `chambers_ruins` (Mission 6)
