# Odin 3 HRIR provenance

## Source

- Name: MIT KEMAR compact HRTF measurements
- Authors: Bill Gardner and Keith Martin
- Copyright: 1994 MIT Media Laboratory
- License identifier: `LicenseRef-MIT-KEMAR-HRTF`
- Permission: unrestricted use with author citation
- Project page: <https://sound.media.mit.edu/resources/KEMAR.html>
- Technical description:
  <https://sound.media.mit.edu/resources/KEMAR/hrtfdoc.txt>
- Source archive:
  <https://sound.media.mit.edu/resources/KEMAR/compact.zip>
- Source archive SHA-256:
  `0bcd69f8e8760cf8eacff4a89594ceca7d44fb94f28ecf0bf19970003bbfb3e0`
- Verified: 2026-07-25

The source is measurement data, not software code. The archive's compact
responses are 128-frame, 16-bit stereo PCM at 44.1 kHz. Each file contains the
left-ear channel followed by the right-ear channel. Azimuth zero is forward
and positive azimuth proceeds toward the listener's right.

## Selected measurements

Only the zero-elevation measurements needed for a standard horizontal 7.1
layout are used:

| Role | Archive member | Azimuth |
|---|---|---:|
| Center | `elev0/H0e000a.wav` | 0 degrees |
| Front | `elev0/H0e030a.wav` | 30 degrees right |
| Side | `elev0/H0e090a.wav` | 90 degrees right |
| Rear | `elev0/H0e150a.wav` | 150 degrees right |

The compact data is a symmetrical set derived from one KEMAR ear. A left-side
source uses the corresponding right-side response with the left and right ear
channels exchanged.

## Output channel order

`odin3-hrir.wav` contains the following 14 channels:

| Index | Output | Source |
|---:|---|---|
| 0 | FL to left speaker | 30-degree right-ear response |
| 1 | FL to right speaker | 30-degree left-ear response |
| 2 | SL to left speaker | 90-degree right-ear response |
| 3 | SL to right speaker | 90-degree left-ear response |
| 4 | RL to left speaker | 150-degree right-ear response |
| 5 | RL to right speaker | 150-degree left-ear response |
| 6 | FC to left speaker | 0-degree left-ear response |
| 7 | FR to right speaker | 30-degree right-ear response |
| 8 | FR to left speaker | 30-degree left-ear response |
| 9 | SR to right speaker | 90-degree right-ear response |
| 10 | SR to left speaker | 90-degree left-ear response |
| 11 | RR to right speaker | 150-degree right-ear response |
| 12 | RR to left speaker | 150-degree left-ear response |
| 13 | FC to right speaker | 0-degree right-ear response |

The LFE path reuses the two center response channels in the PipeWire graph.

## Reproduction

From the repository root:

```text
python3 tools/odin3-audio/build-hrir.py \
  /path/to/compact.zip \
  system_files/usr/share/armada/audio/odin3/hrir/odin3-hrir.wav
```

The generator verifies the source archive before reading it and verifies the
generated result before succeeding. It selects, mirrors, and interleaves
samples without changing their values.

The generated output is:

- 14 channels
- 16-bit signed PCM
- 44.1 kHz
- 128 frames
- SHA-256:
  `0c6a2b60feb4e2fe0ec81ec6e0372b5b8b7bde90612fdace7c5fc569bfc89715`

PipeWire 1.6.8 resamples the impulse responses to the 48 kHz graph rate while
loading each convolver. Every convolver explicitly requests resampling quality
15. The committed asset is not pre-resampled, which keeps the derivation
sample-exact and independently reproducible.

## Attribution

Bill Gardner and Keith Martin, "HRTF Measurements of a KEMAR Dummy-Head
Microphone," MIT Media Lab Perceptual Computing Technical Report #280, 1994.

No implementation code was copied or adapted from the MIT archive.
