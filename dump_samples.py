"""Dump a handful of vsnd_c samples to inspect the audio encoding."""
import os
import sys

from vpk import VPK

DIR_VPK = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("DOTA2_PAK01")
    or "/mnt/d/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/pak01_dir.vpk"
)
OUT = os.environ.get("SAMPLE_OUT") or "work/samples"

PATTERNS = [
    "sounds/vo/announcer_dlc_bastion/",
    "sounds/vo/announcer_dlc_ti10_vog/",
    "sounds/vo/announcer_dlc_pflax/",
    "sounds/vo/announcer/ti9_ann_",
    "sounds/vo/announcer/ann_custom_",
    "sounds/vo/announcer/announcer_intl",
    "sounds/talentcontent/season_13/community_broadcasts/",
]


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    vpk = VPK(DIR_VPK)
    print(f"entries={len(vpk.entries)}")
    for pat in PATTERNS:
        cand = sorted(p for p in vpk.entries if p.startswith(pat))
        if not cand:
            print(f"NO MATCH: {pat}")
            continue
        # take one from the middle for variety
        p = cand[min(5, len(cand) - 1)]
        data, ok = vpk.read(p)
        name = p.replace("/", "__")
        with open(os.path.join(OUT, name), "wb") as f:
            f.write(data)
        print(f"{p}  size={len(data)}  crc_ok={ok}")
    vpk.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
