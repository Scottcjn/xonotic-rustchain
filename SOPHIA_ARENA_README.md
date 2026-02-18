# Sophia Arena - DarkPlaces Audio Modifications

## Overview

Sophia Arena is a custom Xonotic modification featuring an AI-generated announcer voice (Sophia) using XTTS voice cloning technology. The announcer audio system is implemented directly in the DarkPlaces engine to ensure reliable playback.

## Problem Solved

The standard DarkPlaces audio mixer sometimes fails to play announcer sounds correctly, resulting in fallback "ding" sounds instead of the custom voice files. This modification creates a parallel audio pathway specifically for announcer sounds that bypasses the internal mixer.

## Files Modified/Created

### Created Files

| File | Purpose |
|------|---------|
| `source/darkplaces/snd_sophia.c` | Sophia announcer audio system implementation |
| `source/darkplaces/snd_sophia.h` | Header file with public API |
| `xonotic-linux64-sophia` | Compiled binary with Sophia support |

### Modified Files

| File | Changes |
|------|---------|
| `source/darkplaces/snd_main.c` | Added init/shutdown calls and sound interception |
| `source/darkplaces/makefile.inc` | Added snd_sophia.o to build, added -std=gnu11 flag |

## Technical Implementation

### Audio System Architecture

```
Normal Sound Path:
  QuakeC -> S_StartSound -> S_PlaySfxOnChannel -> Internal Mixer -> Audio Output

Sophia Announcer Path:
  QuakeC -> S_StartSound -> S_Sophia_IsAnnouncerSound?
                              |
                              +-> YES -> S_Sophia_PlayAnnouncer -> ffplay/paplay -> Audio Output
                              |
                              +-> NO  -> S_PlaySfxOnChannel -> Internal Mixer
```

### Console Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `snd_sophia_enable` | 1 | Enable/disable Sophia announcer system |
| `snd_sophia_volume` | 1.0 | Announcer volume (0.0-1.0) |

These variables are saved to config (CVAR_SAVE) and persist across sessions.

### Sound Detection

Sounds are routed through the Sophia system if they match:
- Path contains `announcer/` (e.g., `sound/announcer/sophia/begin.ogg`)

### External Audio Playback

The system uses external audio players for reliable playback:

1. **Primary**: `ffplay` (FFmpeg)
   - `-nodisp` - No video window
   - `-autoexit` - Exit when done
   - `-loglevel quiet` - Silent operation
   - `-volume N` - Volume control (0-256)

2. **Fallback**: `paplay` (PulseAudio)
   - `--volume=N` - Volume control (0-65535)

## Build Instructions

### Prerequisites

```bash
# Install dependencies (Debian/Ubuntu)
sudo apt install build-essential libsdl2-dev libogg-dev libvorbis-dev \
                 libpng-dev libjpeg-dev libfreetype6-dev zlib1g-dev

# For audio playback
sudo apt install ffmpeg pulseaudio-utils
```

### Compilation

```bash
cd ~/Games/Xonotic/source/darkplaces

# Clean previous build
make clean

# Build SDL client
make cl-release

# Copy binary
cp darkplaces-sdl ../xonotic-linux64-sophia
chmod +x ../xonotic-linux64-sophia
```

### Build Flags

The makefile includes `-std=gnu11` to ensure C11 compatibility. This is required because DarkPlaces uses `typedef enum {false, true} qboolean` which conflicts with C23's reserved keywords.

## Voice Files

### Location

Voice files must be placed in:
```
~/.xonotic/data/sound/announcer/sophia/
```

Or in the game directory:
```
~/Games/Xonotic/data/sound/announcer/sophia/
```

### Required Files

| Filename | Event |
|----------|-------|
| `begin.ogg` | Match start |
| `prepare.ogg` | Pre-match countdown |
| `1.ogg` - `10.ogg` | Countdown numbers |
| `go.ogg` | Match begin |
| `impressive.ogg` | Impressive achievement |
| `excellent.ogg` | Excellent achievement |
| `humiliation.ogg` | Humiliation kill |
| `firstblood.ogg` | First kill |
| `lead_taken.ogg` | Lead taken |
| `lead_lost.ogg` | Lead lost |
| `lead_tied.ogg` | Lead tied |
| `1fragleft.ogg` | 1 frag remaining |
| `2fragsleft.ogg` | 2 frags remaining |
| `3fragsleft.ogg` | 3 frags remaining |
| `1minuteremains.ogg` | 1 minute warning |
| `5minuteremains.ogg` | 5 minute warning |

### Audio Format

- Format: OGG Vorbis
- Sample Rate: 44100 Hz or 48000 Hz
- Channels: Mono or Stereo

## Usage

### Running the Modified Engine

```bash
cd ~/Games/Xonotic
./xonotic-linux64-sophia
```

### In-Game Commands

```
# Check if Sophia system is enabled
snd_sophia_enable

# Toggle Sophia system
snd_sophia_enable 0   # Disable
snd_sophia_enable 1   # Enable

# Adjust announcer volume
snd_sophia_volume 0.8
```

### Debug Output

The system prints debug messages to the console:
```
[SOPHIA] Audio system initialized (external player backend)
[SOPHIA] Sound base path: /home/user/.xonotic/data/sound/
[SOPHIA] Attempting to play: /home/user/.xonotic/data/sound/announcer/sophia/begin.ogg
[SOPHIA] Playing via external player: announcer/sophia/begin
```

## Voice Generation

The Sophia voice was generated using Coqui XTTS v2 with voice cloning.

### Generation Script Location

```
/tmp/sophia_tts/generate_announcer.py
```

### Sample Generation Command

```python
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
tts.tts_to_file(
    text="Begin!",
    speaker_wav="reference_voice.wav",
    language="en",
    file_path="begin.wav"
)
```

## Code Changes Detail

### snd_main.c Additions

```c
// At top with other includes
#include "snd_sophia.h"

// In S_Shutdown() function (around line 780)
// SOPHIA: Shutdown the parallel announcer audio system
S_Sophia_Shutdown();

// In S_Init() function (at end, around line 926)
// SOPHIA: Initialize the parallel announcer audio system
S_Sophia_Init();
```

### makefile.inc Changes

```makefile
# Line 46: Added snd_sophia.o to sound objects
OBJ_SND_COMMON=snd_main.o snd_mem.o snd_mix.o snd_ogg.o snd_wav.o snd_sophia.o

# Line 177: Added -std=gnu11 for C11 compatibility
CFLAGS_COMMON=-std=gnu11 $(CFLAGS_MAKEDEP) ...
```

## Troubleshooting

### No Sound Playing

1. Check if files exist:
   ```bash
   ls -la ~/.xonotic/data/sound/announcer/sophia/
   ```

2. Check console for errors:
   ```
   developer 1
   ```

3. Verify ffplay is installed:
   ```bash
   which ffplay
   ```

4. Test manual playback:
   ```bash
   ffplay -nodisp -autoexit ~/.xonotic/data/sound/announcer/sophia/begin.ogg
   ```

### Wrong Voice Playing

Ensure the `cv_announcer` cvar is set to "sophia":
```
cv_announcer "sophia"
```

### Volume Too Low/High

Adjust in console:
```
snd_sophia_volume 0.5
```

## Known Issues

1. **Music playback**: Background music may have issues (pending fix)
2. **HUD interface**: Some HUD elements may need adjustment (pending fix)
3. **Sound interception not triggering**: See detailed trial documentation below

## Sound Hook Trial Documentation (2025-12-08)

### Goal
Intercept announcer sounds at the engine level and route them through external ffplay for reliable playback, bypassing the DarkPlaces internal audio mixer.

### The Problem
Xonotic's internal audio mixer sometimes fails to play announcer sounds, producing fallback "ding" sounds instead of custom voice files. The goal was to intercept announcer sounds and play them via external ffplay.

### Hook Attempts (All Unsuccessful)

#### Attempt 1: S_LocalSound (snd_main.c:2345)
```c
// SOPHIA: Intercept announcer sounds played via localsound() from CSQC
if (sound && S_Sophia_IsAnnouncerSound(sound))
{
    Con_Printf("[SOPHIA] Intercepting localsound: %s\n", sound);
    if (S_Sophia_PlayAnnouncer(sound, 1.0f))
        return true;
}
```
**Result**: Hook never triggered. Xonotic doesn't use `localsound()` for announcers.

#### Attempt 2: S_StartSound_StartPosition_Flags (snd_main.c:1705)
```c
// SOPHIA: Intercept announcer sounds at core playback function
if (sfx->name && S_Sophia_IsAnnouncerSound(sfx->name))
{
    Con_Printf("[SOPHIA] Intercepting S_StartSound: %s (vol=%.2f)\n", sfx->name, fvol);
    if (S_Sophia_PlayAnnouncer(sfx->name, fvol))
        return 0;
}
```
**Result**: Hook never triggered for announcer sounds. Sounds loaded during precache but playback path unclear.

#### Attempt 3: VM_CL_sound (clvm_cmds.c:233)
```c
// SOPHIA: Intercept announcer sounds at CSQC builtin level
if (sample && strstr(sample, "announcer/"))
{
    extern qboolean S_Sophia_PlayAnnouncer(const char *soundname, float volume);
    Con_Printf("[SOPHIA] VM_CL_sound intercept: %s (vol=%.2f)\n", sample, fvolume);
    if (S_Sophia_PlayAnnouncer(sample, fvolume))
        return;
}
```
**Result**: Hook never triggered. The sound7() builtin path wasn't being used for announcers.

#### Attempt 4: VM_CL_pointsound (clvm_cmds.c:275)
```c
// SOPHIA: Intercept announcer sounds in pointsound
if (sample && strstr(sample, "announcer/"))
{
    extern qboolean S_Sophia_PlayAnnouncer(const char *soundname, float volume);
    Con_Printf("[SOPHIA] VM_CL_pointsound intercept: %s (vol=%.2f)\n", sample, fvolume);
    if (S_Sophia_PlayAnnouncer(sample, fvolume))
        return;
}
```
**Result**: Hook never triggered.

### Observations

1. **Sound files ARE being precached**: The `[SOPHIA-SND] S_LoadSound` debug shows sounds loading:
   ```
   [SOPHIA-SND] S_LoadSound called for: announcer/sophia/amazing.wav
   [SOPHIA-SND] SUCCESS: Loaded OGG sound/announcer/sophia/amazing.ogg
   ```

2. **Playback hooks NOT triggering**: None of the interception points logged announcer playback during actual gameplay.

3. **Theory**: Xonotic may use a different sound playback mechanism than expected, possibly:
   - Direct SDL audio buffer manipulation
   - Threaded audio with separate playback path
   - Sound mixing that doesn't go through standard S_StartSound

### QuakeC Analysis

Xonotic announcers use this QuakeC call chain:
```
Local_Notification(MSG_ANNCE, id)
  -> _sound(NULL, channel, AnnouncerFilename(snd), volume, position)
    -> sound7()  // QuakeC builtin #8
      -> VM_CL_sound  // clvm_cmds.c
```

However, the VM_CL_sound hook didn't trigger, suggesting the sound playback may be optimized or cached differently.

### Files Modified

| File | Line | Hook Type |
|------|------|-----------|
| `snd_main.c` | 1705 | S_StartSound_StartPosition_Flags |
| `snd_main.c` | 2345 | S_LocalSound |
| `clvm_cmds.c` | 233 | VM_CL_sound |
| `clvm_cmds.c` | 275 | VM_CL_pointsound |

### What DOES Work

The Sophia system initializes correctly:
```
[SOPHIA] Audio system initialized (external player backend)
[SOPHIA] Sound base path: /home/scott/.xonotic/data/sound/
```

### Alternative Approaches to Consider

1. **QuakeC modification**: Replace the `_sound()` wrapper in notifications.qc to call a custom command
2. **External monitor**: Python script that watches for announcer events and plays sounds independently
3. **Sound file hook in S_LoadSound**: Intercept at load time and register callbacks
4. **Complete audio system replacement**: Replace the SDL audio mixer entirely

### Conclusion

The DarkPlaces sound system architecture makes it difficult to intercept sounds at playback time. The sound data may be passed directly to the audio mixer thread without going through the expected engine functions. Further investigation into the SDL audio backend (`snd_sdl.c`) and the mixer (`snd_mix.c`) may be needed.

---

## DarkPlaces Shader/Material Model Reference

DarkPlaces uses a traditional **Blinn-Phong** specular model (not PBR). This section documents the texture workflow for characters and world geometry.

### Texture Layer Suffixes

| Suffix | Purpose | Notes |
|--------|---------|-------|
| `_0.tga` | **Diffuse** (required) | Base color/albedo |
| `_norm.tga` | **Normalmap** | Alpha channel can hold heightmap for parallax |
| `_bump.tga` | **Bumpmap** | Heightmap only (auto-converted to normalmap) |
| `_gloss.tga` | **Glossmap** | Specular intensity (grayscale) |
| `_glow.tga` | **Glowmap** | Emissive/fullbright areas |
| `_luma.tga` | **Glow (alt)** | Tenebrae-compatible glow name |
| `_pants.tga` | **Pants mask** | Grayscale, tinted by player color (additive) |
| `_shirt.tga` | **Shirt mask** | Grayscale, tinted by player color (additive) |

### Player Model Texture Example

```
progs/player.mdl_0.tga        # Diffuse (required)
progs/player.mdl_0_norm.tga   # Normalmap
progs/player.mdl_0_gloss.tga  # Specular/gloss intensity
progs/player.mdl_0_glow.tga   # Emissive areas
progs/player.mdl_0_pants.tga  # Team color mask (pants)
progs/player.mdl_0_shirt.tga  # Team color mask (shirt)
```

### World Texture Example

```
textures/mymap/wall01.tga       # Diffuse
textures/mymap/wall01_norm.tga  # Normalmap
textures/mymap/wall01_gloss.tga # Gloss
textures/mymap/wall01_glow.tga  # Glow/emissive
```

### Key Differences from PBR

| DarkPlaces (Blinn-Phong) | PBR (Metallic/Roughness) |
|--------------------------|--------------------------|
| Diffuse + Gloss | Albedo + Roughness + Metallic |
| Single specular intensity | Separate metal/roughness maps |
| No energy conservation | Energy conserving BRDF |
| Empirical shading | Physically accurate lighting |
| Glossmap = shininess | Roughness = inverse of gloss |

### Relevant Console Variables

| CVar | Default | Description |
|------|---------|-------------|
| `r_shadow_gloss` | 1 | 0=off, 1=use textures, 2=force flat gloss |
| `r_shadow_glossexponent` | 32 | Specular sharpness (higher = tighter highlight) |
| `r_shadow_glossintensity` | 1 | Specular brightness multiplier |
| `r_shadow_gloss2intensity` | 0.125 | Forced gloss brightness (when gloss=2) |
| `r_glsl_offsetmapping` | 0 | Enable parallax from normalmap alpha |
| `r_shadow_bumpscale_basetexture` | 0 | Auto-generate bumpmaps from diffuse |

### Skin Files (.skin)

For MD3/DPM/PSK models with multiple skins:

```
# player_0.skin
torso,progs/player_default.tga
gun,progs/player_default.tga
muzzleflash,progs/player_default_muzzleflash.tga
tag_head,
tag_torso,
tag_weapon,
```

### Supported Image Formats

- **TGA** (recommended) - fastest loading
- **PNG** - loads slowly, good for alpha
- **JPG** - loads slowly, lossy
- **PCX, WAL, LMP** - legacy formats

### Workflow Tips

1. **Black out team color areas** in diffuse where pants/shirt masks apply
2. **Normalmap alpha** can store heightmap for parallax/relief mapping
3. **Glow areas** should be black in diffuse (additive blend)
4. **Gloss is intensity only** - no color information, grayscale
5. **Model limits**: 256 skins, 65536 frames/verts/tris per model

### Converting from PBR to DarkPlaces

| PBR Map | DarkPlaces Equivalent |
|---------|----------------------|
| Albedo | Diffuse (`_0.tga`) |
| Normal | Normal (`_norm.tga`) |
| Roughness | Invert → Gloss (`_gloss.tga`) |
| Metallic | Multiply into gloss intensity |
| AO | Bake into diffuse |
| Emissive | Glow (`_glow.tga`) |
| Height | Normalmap alpha channel |

---

## License

This modification is provided for personal use with Xonotic. The DarkPlaces engine is GPL-licensed. Voice files generated with XTTS are subject to Coqui's license terms.

## Author

Created for the Sophiacord project - integrating AI personality systems with gaming experiences.
