"""Rename schinese output folders to official Chinese names (from game localization).

Run AFTER extract_vo.py --vpk <dota_schinese vpk> --out <dir>. Also patches manifest.csv.
"""
import csv
import os
import sys

RENAME = {
    "announcer": "默认播音员",
    "announcer_killing_spree": "默认连杀配音",
    "announcer_diretide_2012": "夜魇暗潮2012播音",
    "announcer_dlc_diretide2020_killing_spree": "夜魇暗潮2020连杀配音",
    "announcer_dlc_axe": "斧王播音包",
    "announcer_dlc_bristleback": "钢背兽播音包",
    "announcer_dlc_bristleback_killing_spree": "钢背兽连杀配音",
    "announcer_dlc_clockwerk": "发条技师播音包",
    "announcer_dlc_crystal_maiden": "水晶室女播音包",
    "announcer_dlc_crystal_maiden_killing_spree": "水晶室女连杀配音",
    "announcer_dlc_dark_willow": "邪影芳灵播音包",
    "announcer_dlc_dark_willow_killing_spree": "邪影芳灵连杀配音",
    "announcer_dlc_juggernaut": "主宰播音包",
    "announcer_dlc_juggernaut_killing_spree": "主宰连杀配音",
    "announcer_dlc_kunkka_tide": "昆卡与潮汐猎人播音包",
    "announcer_dlc_kunkka_tide_killing_spree": "昆卡与潮汐猎人连杀配音",
    "announcer_dlc_lina": "莉娜播音包",
    "announcer_dlc_meepo": "米波播音包",
    "announcer_dlc_meepo_killing_spree": "米波连杀配音",
    "announcer_dlc_monkey_king": "齐天大圣播音包",
    "announcer_dlc_monkey_king_killing_spree": "齐天大圣连杀配音",
    "announcer_dlc_ringmaster": "百戏大王播音包",
    "announcer_dlc_ringmaster_killing_spree": "百戏大王连杀配音",
    "announcer_dlc_stormspirit": "风暴之灵播音包",
    "announcer_dlc_techies": "工程师播音包",
    "announcer_dlc_techies_killing_spree": "工程师连杀配音",
    "announcer_dlc_tusk": "巨牙海民播音包",
}


def main(root: str) -> int:
    dirs = sorted(d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)))
    for old, new in RENAME.items():
        src, dst = os.path.join(root, old), os.path.join(root, new)
        if os.path.isdir(src) and not os.path.exists(dst):
            os.rename(src, dst)
            print(f"{old} -> {new}")
    mpath = os.path.join(root, "manifest.csv")
    if os.path.isfile(mpath):
        with open(mpath, newline="", encoding="utf-8-sig") as f:
            rows = list(csv.reader(f))
        for r in rows[1:]:
            seg = r[1].split("/", 1)
            if seg[0] in RENAME:
                r[1] = RENAME[seg[0]] + ("/" + seg[1] if len(seg) > 1 else "")
        with open(mpath, "w", newline="", encoding="utf-8-sig") as f:
            csv.writer(f).writerows(rows)
        print(f"manifest rows patched: {len(rows) - 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "./dota2_语音包/中文版"))
