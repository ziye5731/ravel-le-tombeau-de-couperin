# 拉威尔《库普兰之墓》室内乐改编工程

当前包含钢琴原版六乐章的 LilyPond 工作稿，以及长笛、双簧管、B♭ 单簧管与钢琴的室内乐总谱框架；三个管乐声部暂为空。

## 查看乐谱

- [全套钢琴谱 PDF](output/pdf/le-tombeau-de-couperin.pdf)：31 页，印刷页码 2–32，与仓库内 Durand 扫描版的音乐正文对应。
- [LilyPond 总入口](piano/lilypond/le-tombeau-de-couperin.ly)。
- 每乐章另有独立入口 `piano/lilypond/01-prelude.ly` 至 `06-toccata.ly`。
- 可编辑音符位于 `piano/lilypond/movements/*.ily`，按声部组织，每小节有原谱小节号注释。
- 公共版式位于 `piano/lilypond/common.ily`。

原始钢琴版、管弦乐版 PDF 均保留原样。新谱包含六乐章的音符、节奏、复调声部、跨谱表、装饰音、主要奏法、力度、速度文字、反复与分支、八度线及震音。分行与分页以本地扫描版为目标；字体、局部间距和部分连线尚有差异。

**这是一份可继续校订的全曲录入稿，不是已经逐音人工校订完毕的出版定稿。** 已知限制与校订记录见 [EDITORIAL.md](EDITORIAL.md)。

## 编译

需要 LilyPond；本机使用并验证的版本为 **2.26.0**。普通编译只需 Python 标准库，不需要下载或安装其他 Python 包。

```sh
python3 scripts/build.py
```

输出到 `output/pdf/le-tombeau-de-couperin.pdf`。单独编译某乐章：

```sh
python3 scripts/build.py 01-prelude.ly
```

编译同时生成钢琴音色的 MIDI，存放在 `output/midi/`：六个分乐章文件，以及拼接后的 `le-tombeau-de-couperin.midi`。全曲文件保留各乐章的速度与事件时间信息。

仅输出 MIDI：

```sh
python3 scripts/build.py --midi-only
```

MIDI 是当前录入稿的机械回放。源码中的印刷反复线和分支目前没有写成可展开的 LilyPond 反复结构，因此 MIDI 按源码顺序播放，不重复反复段；它也继承工作稿尚待校订的音乐细节。

检查 LilyPond 实际解析的音符数与每条声部的精确时长：

```sh
python3 scripts/validate_music.py
```

可选的 PDF 校对工具依赖 `pymupdf`：

```sh
python3 scripts/render_pdf.py output/pdf/le-tombeau-de-couperin.pdf --pages 1 5
```

## 录入与来源

最终校对依据是本仓库 `piano/IMSLP46605-…Durand_9569_reissue.pdf`。为避免从扫描图像完全重新键入，基础音符录入取自 [PDMX 公开谱库](https://zenodo.org/records/15571083) 中的完整钢琴版，并结合另一份数字谱的原版布局和表情标记进行整理。两份数字谱都有错误，均未直接视为权威版本。

`piano/source/` 保留取得的 MXL、工作用 MusicXML、PDMX 元数据及 SHA-256 校验值。PDMX 的两条记录分别对应 MuseScore 5145647 和 5306349；网站许可元数据均为 CC0。后一份内部保留了 “Copyright © DURAND Cie 1918”，因此 PDMX 标记了许可信息冲突；这里完整保留其来源记录。

`scripts/engrave.py` 是从存档 MusicXML 重建 `.ily` 的导入工具。**日常编辑之后只运行 `build.py`；重新运行 `engrave.py` 会覆盖乐章源码中的人工修改。**

本项目使用 Git 管理版本；改编工作位于 `fl-ob-cl-piano/`。
