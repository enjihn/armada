# Odin 3 stereo and virtual surround audio

This integration gives the AYN Odin 3 two user-facing speaker outputs:

- **Stereo** downmixes multichannel content to the built-in stereo speakers.
- **Virtual Surround Sound** applies an HRIR convolution to 7.1 content before
  sending the result to the built-in stereo speakers.

The physical speaker sink remains an internal transport. Steam sees the two
profiles above instead of exposing **Built-In Audio** as a third selectable
output.

## Device scope

The setup is restricted to an exact device-policy match for the AYN Odin 3 on
SM8750. A non-matching device installs nothing and removes only this package's
exact managed links if they survived an earlier image. Original files displaced
by those links are restored. Internal Odin 3 audio values and policy must not
be applied to other handhelds or external audio devices.

## Defaults and persistence

On a new account with no saved audio state, the first session:

1. Sets both public sinks to 100 percent.
2. Selects **Stereo** as the default.
3. Records that initialization has completed.

That initialization is not repeated. If the user later selects **Virtual
Surround Sound**, the normal PipeWire and WirePlumber state preserves that
choice across sessions and reboots. Selecting **Stereo** makes it the persistent
choice again. An update must not replace an existing user selection.

The physical speaker route is held at unity gain. User volume is applied to the
selected public sink, so a restored hardware-route volume cannot silently make
both profiles quieter or louder.

Steam keeps a separate output-device override inside its SharedJSContext. On
each Steam launch, `launch-steam` nonblockingly restarts
`armada-odin3-audio-steam-restore.service`. If and only if the exact Odin 3 /
SM8750 device policy matches and PipeWire's current default sink is exactly
**Virtual Surround Sound**, the bounded helper waits for Steam CEF and restores
that same output in Steam. It selects only the `SharedJSContext` target served
for `steamloopback.host` through a loopback WebSocket, verifies Steam exposes
one exact matching output, applies the override, and reads it back. A missing
target, ambiguous device, timeout, or protocol error leaves the system audio
default unchanged and is reported in the user journal. **Stereo** and all
external/default sinks therefore cause no Steam override mutation.

## Signal level

Both profiles use a base gain of `0.295248`. This is 12 percent of the
logarithmic interval from the earlier `0.25` setting (`-12.0412 dB`) toward
unity (`0 dB`):

```text
-12.0412 dB + (0.12 * 12.0412 dB) = -10.5963 dB
10 ^ (-10.5963 / 20) = 0.295248
```

Virtual-surround channel weights retain the established relative balance:

| Input | Gain |
|---|---:|
| Front and LFE | `0.295248` |
| Side | `0.265723` |
| Rear | `0.236199` |
| Center | `0.354298` |

The final left and right samples are clamped to `+/-0.8912509381`, which is a
hard `-1 dBFS` sample ceiling. This is an emergency peak limit, not a loudness
normalizer or a guarantee that all upstream combinations are free of audible
compression.

The Stereo profile enables center, surround, and LFE downmixing so those
channels are retained when an application supplies multichannel audio.

## Installation lifecycle

The image contains immutable profile templates under
`/usr/share/armada/audio/odin3`. Before the display manager starts,
`armada-odin3-audio-setup.service` verifies the device and installs only the six
managed configuration links in the `armada` user's PipeWire and WirePlumber
directories. It also creates
`/var/home/armada/.local/share/armada/odin3-audio` with mode `0700` and seeds
`hrir.wav` with the packaged MIT KEMAR profile, mode `0600`, only when that file
is absent. An existing regular `hrir.wav` is always retained. Setup fails
closed on a symlink, special file, or unsafe parent path.

If a managed path already contains a regular file, setup moves it to an
adjacent file ending in `.armada-odin3-audio.backup` before creating the link.
Setup refuses to replace foreign symlinks, special files, unsafe parent paths,
or an existing backup.

The user service `armada-odin3-audio-default.service` performs the one-time
clean-account initialization after PipeWire, PipeWire Pulse, and WirePlumber
are available. Existing audio state suppresses that initialization.

`armada-odin3-audio-steam-restore.service` is launch-triggered and intentionally
is not enabled. Its bounded one-shot failure cannot prevent Steam from starting.

## Rollback

On an Odin 3, restore displaced configuration with:

```text
sudo /usr/libexec/armada/odin3-audio-setup --restore
systemctl --user restart pipewire pipewire-pulse wireplumber
```

The restore operation removes only links owned by this integration and puts
the adjacent backups back in place. It refuses to remove a foreign link or
overwrite a current user file. Reboot instead of restarting the user services
if the Qualcomm audio path does not return cleanly. Rollback and non-Odin
cleanup do not delete `hrir.wav`, because it may be user-supplied.

## HRIR provenance

The distributable profile uses the MIT KEMAR compact HRTF measurements by Bill
Gardner and Keith Martin. MIT permits unrestricted use with author citation.
The committed 14-channel asset is deterministically assembled from the
zero-elevation 0, 30, 90, and 150 degree measurements.

The exact source archive, license terms, channel mapping, generation command,
source checksum, and generated checksum are recorded in
`system_files/usr/share/armada/audio/odin3/hrir/PROVENANCE.md`.

### Optional user HRIR

An advanced user may replace
`/var/home/armada/.local/share/armada/odin3-audio/hrir.wav` with a regular
14-channel WAV using the same channel order documented in `PROVENANCE.md`.
Stop the user PipeWire services before replacing it, keep the path free of
symlinks, set ownership to `armada:armada` and mode `0600`, then restart
PipeWire, PipeWire Pulse, and WirePlumber.

The user is responsible for confirming that any replacement HRIR is legally
obtained and for complying with its license and redistribution terms. The
package continues to ship the licensed MIT KEMAR asset as the fallback and
does not redistribute user replacements.

## Limitations

- Virtual surround is a perceptual widening preset for the Odin 3 built-in
  speakers; it does not create discrete physical surround channels. HRIRs
  assume isolated ears, while speakers introduce acoustic crosstalk and the
  listener's own head response, so this is not geometrically accurate binaural
  rendering.
- Perceived localization varies by listener and by the HRIR dataset.
- The hard sample ceiling protects the final graph output but is not a
  true-peak limiter.
- The virtual sinks, hidden transport, unity-route enforcement, and gain tuning
  apply only to the built-in Odin 3 speakers. PipeWire Pulse's multichannel
  downmix coefficients are session-wide, so they are also used when a
  multichannel Pulse application is reduced to any external stereo sink.
  External sink gain, routing, and visibility are otherwise unchanged.
- The packaged MIT KEMAR fallback passed live channel-order and routing
  validation on the Odin 3. Its short anechoic response produced comparatively
  subtle speaker localization, so perceived quality remains profile-dependent.

## Tests

Run the repository checks from the repository root:

```text
bash tests/odin3-audio-test.sh
```

Run the opt-in, read-only live-session checks on an Odin 3:

```text
ODIN3_AUDIO_DEVICE_TEST=1 bash tests/odin3-audio-device-test.sh
```

The repository test validates the device gate, managed installation and
rollback, first-run default policy, Steam rehydration contract, graph structure,
channel routing, gain ratios, and final sample clamps. The device check verifies
the two public sinks, the internal hardware route, and an expected persistent
default selection.
