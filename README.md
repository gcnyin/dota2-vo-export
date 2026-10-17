# dota2-vo-export

**English:** Extract Dota 2 announcer / mega-kill / TI broadcast voice packs from the game's VPK archives
into plain, directly playable `mp3` / `wav` files. No hero in-game voice lines. Pure Python stdlib, managed with [uv](https://docs.astral.sh/uv/).

从 Dota 2（Source 2）的 VPK 仓库中提取**播音类语音**——播音包、连杀配音、TI 战队播报、赛事主播语音
（不含英雄战斗配音）——无损转成可直接播放的音频文件。纯 Python 标准库，无第三方依赖。

## 功能

- 解析 Source 2 VPK（version 2）目录树（38 万+ 条目），按前缀筛选、逐文件读取，全部 CRC32 校验
- 解包 `vsnd_c`：文件头第一个 `uint32` 即音频本体偏移；语音基本是 MP3 流，**直接切出字节、零转码损失**；
  少数 PCM16（采样率取自 KV3 元数据）封装为标准 WAV
- 中文仓库输出支持一键改为**官方中文文件夹名**（名称取自游戏 `dota_schinese` 本地化文件）

## 环境要求

- WSL / Linux（默认路径为 WSL 视角的 Steam 库；其他环境用 `--vpk` 或环境变量 `DOTA2_PAK01` 指定）
- [uv](https://docs.astral.sh/uv/)（Python ≥ 3.10）

## 快速开始

```bash
# 0) 先统计会导出什么（不写文件）
uv run extract_vo.py --dry

# 1) 英文主仓库
uv run extract_vo.py --out ./dota2_语音包

# 2) 简体中文仓库（英雄主题播音包的中文配音都在这里）
uv run extract_vo.py \
  --vpk "/mnt/d/Program Files (x86)/Steam/steamapps/common/dota 2 beta/game/dota_schinese/pak01_dir.vpk" \
  --out "./dota2_语音包/中文版"

# 3) 中文输出文件夹改为官方中文名（同步 manifest.csv）
uv run rename_schinese.py "./dota2_语音包/中文版"
```

说明：

- 游戏装在其他位置：`--vpk <pak01_dir.vpk 路径>` 或 `export DOTA2_PAK01=<路径>`
- 若 `~/.cache` 只读（容器/沙箱环境），命令前加 `UV_CACHE_DIR=<可写目录>`
- 每次导出会在输出目录生成 `manifest.csv`（VPK 内路径 → 输出文件、编码、字节数、CRC 结果）

## 文件说明

| 文件 | 作用 |
| --- | --- |
| `vpk.py` | Source 2 VPK 读取模块（目录树解析 + 按条目读取 + CRC32 校验） |
| `extract_vo.py` | 主脚本：提取播音范围并转为音频文件（`--dry` / `--vpk` / `--out`） |
| `rename_schinese.py` | 中文输出文件夹改官方中文名，并同步 `manifest.csv` |
| `scan_vpk.py` | 扫描仓库目录树，统计语音分类 / 播音包清单 |
| `dump_samples.py` | 抽样导出 `vsnd_c`，用于检查音频编码 |

## 原理速记

- **VPK**：version 2，28 字节头 + 目录树；目录项 18 字节（CRC32 / 预载长度 / 分卷号 / 偏移 / 长度 / `0xFFFF`）；
  分卷文件（`pak01_NNN.vpk`）无文件头，条目偏移即绝对偏移
- **vsnd_c**：Source 2 编译资源，头部为 REDI/DATA 元数据块，随后是音频本体：
  - MP3（`FF Ex` 帧同步，多数带 Xing 头）→ 切出存 `.mp3`
  - PCM16 → 从 KV3 元数据取采样率（如 `44 ac 00 00` = 44100）封装 `.wav`
- **提取范围**：`extract_vo.py` 的 `SCOPE_PREFIXES`（`sounds/vo/announcer/`、`sounds/vo/announcer_*`、
  `sounds/talentcontent/`）。想加英雄战斗配音，加 `sounds/vo/<英雄>/`（如 `sounds/vo/pudge/`）重跑即可

## 预期产出（参考值）

- 英文主仓库：约 16670 个文件（16570 mp3 + 102 wav），约 700 MB
  - 35+ 个播音包（GLaDOS、堡垒、史丹利的寓言、瑞克和莫蒂、暗黑地牢、辐射 4、GabeN、PyrionFlax、
    TI10 赛事播音等），绝大多数带 `*_killing_spree` 连杀播报
  - `announcer/`：默认播音员 + TI 战队播报（ti8/ti9/intl，多语言）+ 自定义游戏播音；
    另有默认连杀配音、夜魇暗潮 2012 播音、`announcer_dota_fighter`
  - `talentcontent/season_11~13/`：赛事主播/选手语音
- 简体中文仓库：约 7111 个 mp3，约 320 MB
  - 有中文：默认播音员、默认连杀配音、夜魇暗潮 2012/2020，以及斧王、钢背兽、发条技师、水晶室女、
    邪影芳灵、主宰、昆卡与潮汐猎人、莉娜、米波、齐天大圣、百戏大王、风暴之灵、工程师、巨牙海民播音包
    （其中 9 个另带"连杀配音"）
  - 无中文（Valve 未录制）：GLaDOS、Cave Johnson、堡垒、暗黑地牢、防御网格、杀出重围、辐射 4、
    GabeN、克莱纳、先知播音、PyrionFlax、瑞克和莫蒂、史丹利的寓言、TI10 播音、三位一体、海盗、TI 聊天轮盘

## 中英文文件夹对照（`rename_schinese.py`）

| VPK 目录 | 官方中文名 |
| --- | --- |
| announcer / announcer_killing_spree | 默认播音员 / 默认连杀配音 |
| announcer_diretide_2012 | 夜魇暗潮2012播音 |
| announcer_dlc_diretide2020_killing_spree | 夜魇暗潮2020连杀配音 |
| announcer_dlc_axe | 斧王播音包 |
| announcer_dlc_bristleback | 钢背兽播音包（+钢背兽连杀配音） |
| announcer_dlc_clockwerk | 发条技师播音包 |
| announcer_dlc_crystal_maiden | 水晶室女播音包（+水晶室女连杀配音） |
| announcer_dlc_dark_willow | 邪影芳灵播音包（+邪影芳灵连杀配音） |
| announcer_dlc_juggernaut | 主宰播音包（+主宰连杀配音） |
| announcer_dlc_kunkka_tide | 昆卡与潮汐猎人播音包（+连杀配音） |
| announcer_dlc_lina | 莉娜播音包 |
| announcer_dlc_meepo | 米波播音包（+米波连杀配音） |
| announcer_dlc_monkey_king | 齐天大圣播音包（+齐天大圣连杀配音） |
| announcer_dlc_ringmaster | 百戏大王播音包（+百戏大王连杀配音） |
| announcer_dlc_stormspirit | 风暴之灵播音包 |
| announcer_dlc_techies | 工程师播音包（+工程师连杀配音） |
| announcer_dlc_tusk | 巨牙海民播音包 |

官方名出处（主仓库内 `resource/localization/dota_schinese.txt`）：
`DOTA_TI8_Meepo_Announcer_Pack`="米波播音包"、`StoreBanner_Header_Monkey_King_Announcer_Pack`="齐天大圣播音包"、
`DOTA_MegaKill_Default`="默认连杀配音"、`DOTA_PlayDiretide`="游玩夜魇暗潮"、Ringmaster 官方名"百戏大王"等。

## 声明

- 本工具只读取本地已安装的游戏文件，供个人学习 / 备份使用；语音与文本内容的版权归 Valve 所有
- 请勿把提取出的音频提交进本仓库（`.gitignore` 已排除输出目录）
