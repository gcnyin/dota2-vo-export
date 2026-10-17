"""Scan Dota 2 pak01_dir.vpk tree: index files, categorize voice resources."""
import os
import struct
import sys
from collections import Counter

DIR_VPK = (
    sys.argv[1]
    if len(sys.argv) > 1
    else os.environ.get("DOTA2_PAK01")
    or "/mnt/d/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota/pak01_dir.vpk"
)


def cstr(buf: bytes, pos: int) -> tuple[str, int]:
    end = buf.index(b"\x00", pos)
    return buf[pos:end].decode("utf-8", "replace"), end + 1


def parse_tree(dir_vpk: str) -> dict[str, tuple[int, int, int, int]]:
    with open(dir_vpk, "rb") as f:
        data = f.read()
    sig, version, tree_size = struct.unpack_from("<III", data, 0)
    assert sig == 0x55AA1234, hex(sig)
    header_size = 28 if version == 2 else 12
    tree = data[header_size : header_size + tree_size]
    entries: dict[str, tuple[int, int, int, int]] = {}
    pos = 0
    bad_term = 0
    while True:
        ext, pos = cstr(tree, pos)
        if ext == "":
            break
        while True:
            path, pos = cstr(tree, pos)
            if path == "":
                break
            while True:
                name, pos = cstr(tree, pos)
                if name == "":
                    break
                crc, preload, arch, off, length, term = struct.unpack_from("<IHHIIH", tree, pos)
                pos += 18
                if term != 0xFFFF:
                    bad_term += 1
                if preload:
                    pos += preload
                entries[f"{path}/{name}.{ext}"] = (arch, off, length, crc)
    print(f"version={version} tree_size={tree_size} entries={len(entries)} bad_terminators={bad_term}")
    return entries


def main() -> None:
    entries = parse_tree(DIR_VPK)

    # top-level prefix census
    top = Counter(p.split("/", 1)[0] for p in entries)
    print("\n== top-level prefixes ==")
    for k, v in top.most_common(15):
        print(f"{v:8d}  {k}")

    # sounds/ subtree census
    snd = Counter("/".join(p.split("/")[:3]) for p in entries if p.startswith("sounds/"))
    print("\n== sounds/* categories ==")
    for k, v in snd.most_common(40):
        print(f"{v:8d}  {k}")

    # vo subcategories
    vo = Counter("/".join(p.split("/")[:3]) for p in entries if p.startswith("sounds/vo/"))
    print("\n== sounds/vo/* categories ==")
    for k, v in vo.most_common(60):
        print(f"{v:8d}  {k}")

    # announcer packs
    ann = Counter("/".join(p.split("/")[3:4]) for p in entries if p.startswith("sounds/vo/announcer/"))
    print(f"\n== announcer packs ({len(ann)}) ==")
    for k, v in sorted(ann.items()):
        print(f"{v:6d}  {k}")

    # anything ti/broadcast related outside announcer
    print("\n== ti/broadcast/caster candidates outside sounds/vo/announcer ==")
    hits = Counter()
    for p in entries:
        lp = p.lower()
        if ("broadcast" in lp or "caster" in lp) and not lp.startswith("sounds/vo/announcer/") and lp.startswith("sounds/"):
            hits["/".join(p.split("/")[:4])] += 1
    for k, v in sorted(hits.items()):
        print(f"{v:6d}  {k}")


if __name__ == "__main__":
    sys.exit(main())
