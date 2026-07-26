#!/usr/bin/env python3
"""Build Armada's 14-channel Odin 3 HRIR from MIT KEMAR compact data."""

from __future__ import annotations

import argparse
import hashlib
import io
import struct
import wave
import zipfile
from pathlib import Path


SOURCE_SHA256 = "0bcd69f8e8760cf8eacff4a89594ceca7d44fb94f28ecf0bf19970003bbfb3e0"
OUTPUT_SHA256 = "0c6a2b60feb4e2fe0ec81ec6e0372b5b8b7bde90612fdace7c5fc569bfc89715"
SOURCE_FORMAT = (2, 2, 44100, 128)

# MIT KEMAR compact azimuth is clockwise: 0 degrees is forward and
# 90 degrees is to the listener's right. Each file contains left-ear then
# right-ear samples. Left-side speakers are the right-side measurement with
# the ear channels exchanged, as prescribed for the symmetrical compact set.
#
# The order matches the convolver channel indices in 50-hrir-7_1.conf:
# FL_L, FL_R, SL_L, SL_R, RL_L, RL_R, FC_L,
# FR_R, FR_L, SR_R, SR_L, RR_R, RR_L, FC_R.
CHANNELS = (
    ("FL_L", 30, 1),
    ("FL_R", 30, 0),
    ("SL_L", 90, 1),
    ("SL_R", 90, 0),
    ("RL_L", 150, 1),
    ("RL_R", 150, 0),
    ("FC_L", 0, 0),
    ("FR_R", 30, 1),
    ("FR_L", 30, 0),
    ("SR_R", 90, 1),
    ("SR_L", 90, 0),
    ("RR_R", 150, 1),
    ("RR_L", 150, 0),
    ("FC_R", 0, 1),
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def member_name(azimuth: int) -> str:
    return f"elev0/H0e{azimuth:03d}a.wav"


def read_measurement(archive: zipfile.ZipFile, azimuth: int) -> tuple[list[int], list[int]]:
    name = member_name(azimuth)
    try:
        payload = archive.read(name)
    except KeyError as error:
        raise SystemExit(f"missing source measurement: {name}") from error

    with wave.open(io.BytesIO(payload), "rb") as source:
        actual = (
            source.getnchannels(),
            source.getsampwidth(),
            source.getframerate(),
            source.getnframes(),
        )
        if actual != SOURCE_FORMAT or source.getcomptype() != "NONE":
            raise SystemExit(
                f"unexpected source format for {name}: {actual}, "
                f"compression={source.getcomptype()}"
            )
        samples = struct.unpack(
            f"<{source.getnframes() * source.getnchannels()}h",
            source.readframes(source.getnframes()),
        )

    return list(samples[0::2]), list(samples[1::2])


def build(source_zip: Path, output: Path) -> str:
    actual_source_hash = sha256(source_zip)
    if actual_source_hash != SOURCE_SHA256:
        raise SystemExit(
            "MIT KEMAR source checksum mismatch: "
            f"found {actual_source_hash}, expected {SOURCE_SHA256}"
        )

    with zipfile.ZipFile(source_zip) as archive:
        measurements = {
            azimuth: read_measurement(archive, azimuth)
            for azimuth in sorted({azimuth for _, azimuth, _ in CHANNELS})
        }

    output.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output), "wb") as target:
        target.setnchannels(len(CHANNELS))
        target.setsampwidth(SOURCE_FORMAT[1])
        target.setframerate(SOURCE_FORMAT[2])
        for frame in range(SOURCE_FORMAT[3]):
            target.writeframesraw(
                struct.pack(
                    f"<{len(CHANNELS)}h",
                    *(
                        measurements[azimuth][ear][frame]
                        for _, azimuth, ear in CHANNELS
                    ),
                )
            )

    digest = sha256(output)
    if digest != OUTPUT_SHA256:
        raise SystemExit(
            f"generated HRIR checksum mismatch: found {digest}, expected {OUTPUT_SHA256}"
        )
    return digest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source_zip", type=Path)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()

    digest = build(arguments.source_zip, arguments.output)
    print(f"{digest}  {arguments.output}")


if __name__ == "__main__":
    main()
