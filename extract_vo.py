"""Extract announcer/TI-broadcast voice packs from Dota 2 VPK into plain audio files."""
from __future__ import annotations

import argparse
import csv
import os
import struct
import sys
from collections import Counter

from vpk import VPK

DIR_VPK = os.environ.get("DOTA2_PAK01") or (
    "/mnt/d/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/pak01_dir.vpk"
)

# in-scope prefixes inside the vpk (announcer packs, TI broadcasts, talent/community broadcasts)
SCOPE_PREFIXES = (
    "sounds/vo/announcer/",
    "sounds/vo/announcer_",
    "sounds/talentcontent/",
)

KNOWN_RATES = (44100, 48000, 22050, 32000, 16000, 11025, 8000)


def detect_codec(data: bytes) -> str:
    if data[:4] == b"OggS":
        return "ogg"
    if data[:4] == b"RIFF":
        return "wav"
    if data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "mp3"
    return "pcm"


def audio_slice(data: bytes) -> bytes:
    """vsnd_c: uint32 @0 = offset where raw audio starts."""
    off = struct.unpack_from("<I", data, 0)[0]
    return data[off:]


def guess_pcm_rate(meta: bytes) -> int:
    """Find the m_nRate value in the KV3 blob: first plausible rate by priority."""
    for rate in KNOWN_RATES:
        if struct.pack("<I", rate) in meta:
            return rate
    return 44100


def pcm_to_wav(pcm: bytes, rate: int, channels: int = 1, bits: int = 16) -> bytes:
    byte_rate = rate * channels * bits // 8
    block = channels * bits // 8
    hdr = b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt " + struct.pack(
        "<IHHIIHH", 16, 1, channels, rate, byte_rate, block, bits
    ) + b"data" + struct.pack("<I", len(pcm))
    return hdr + pcm


def out_rel_path(vpk_path: str, codec: str) -> str:
    rel = vpk_path
    for pre in ("sounds/vo/", "sounds/"):
        if rel.startswith(pre):
            rel = rel[len(pre) :]
            break
    rel = rel[: -len(".vsnd_c")] + ("." + codec if codec != "pcm" else ".wav")
    return rel


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vpk", default=DIR_VPK, help="path to pak01_dir.vpk")
    ap.add_argument("--out", default="./dota2_语音包")
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    vpk = VPK(args.vpk)
    targets = sorted(p for p in vpk.entries if p.startswith(SCOPE_PREFIXES) and p.endswith(".vsnd_c"))
    print(f"in-scope vsnd_c files: {len(targets)}")
    groups = Counter("/".join(p.split("/")[:3]) for p in targets)
    for k, v in sorted(groups.items()):
        print(f"  {v:5d}  {k}")

    if args.dry:
        codecs: Counter[str] = Counter()
        bad_crc = 0
        small = []
        for p in targets:
            data, ok = vpk.read(p)
            if not ok:
                bad_crc += 1
            aud = audio_slice(data)
            c = detect_codec(aud)
            codecs[c] += 1
            if len(aud) < 512:
                small.append((p, len(aud), c))
        print("codec distribution:", dict(codecs))
        print("crc mismatches:", bad_crc)
        print("tiny files (<512B):", small[:10], "count", len(small))
        vpk.close()
        return 0

    os.makedirs(args.out, exist_ok=True)
    manifest = [["vpk_path", "output", "codec", "bytes", "crc_ok"]]
    codecs: Counter[str] = Counter()
    bad_crc = 0
    done = 0
    for p in targets:
        data, ok = vpk.read(p)
        if not ok:
            bad_crc += 1
        aud = audio_slice(data)
        c = detect_codec(aud)
        if c == "pcm":
            meta = data[: struct.unpack_from("<I", data, 0)[0]]
            rate = guess_pcm_rate(meta)
            payload = pcm_to_wav(aud, rate)
            ext_out = "wav(pcm16)"
        else:
            payload = aud
            ext_out = c
        rel = out_rel_path(p, c)
        dest = os.path.join(args.out, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(payload)
        codecs[ext_out] += 1
        manifest.append([p, rel, ext_out, len(aud), int(ok)])
        done += 1
        if done % 1000 == 0:
            print(f"  {done}/{len(targets)} ...", flush=True)

    with open(os.path.join(args.out, "manifest.csv"), "w", newline="", encoding="utf-8-sig") as f:
        csv.writer(f).writerows(manifest)
    print(f"done: {done} files -> {args.out}")
    print("codecs:", dict(codecs))
    print("crc mismatches:", bad_crc)
    vpk.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
