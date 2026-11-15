# 长笛、双簧管、B♭ 单簧管与钢琴：室内乐工作总谱

这是六乐章的室内乐改编工作稿。《前奏曲》第 1–14 小节已分配双簧管旋律和部分木管伴奏；第 22–29 小节已依次分配单簧管、双簧管及三木管的旋律，钢琴负责流动织体。其余部分仍待改编。钢琴以 `../piano/lilypond/movements/` 的现有工作稿为基础。小节号按乐章编号；Forlane 第 140 小节的两个分支沿用钢琴稿编号。

- `score.ly` 是总谱入口；`output/score.pdf` 是总谱。
- `flute/*.ily` 和 `oboe/*.ily` 分别按乐章保存长笛和双簧管声部，可各自逐小节编辑。
- `clarinet/*.ily` 按乐章保存 B♭ 单簧管声部，使用**记谱音高**：写出的 C 实际发声 B♭。调号已比实际音高高大二度；Toccata 的 F♯ 大调段以 A♭ 大调（G♯ 大调的等音）记谱。
- `piano/*.ily` 是钢琴稿的独立副本，除已改编的小节外，音符及标记沿用原工作稿；为适应总谱移除了钢琴独奏谱的强制换行。
- `output/score.midi` 包含长笛、双簧管、单簧管和钢琴四个乐器轨，以及 MIDI 所需的速度轨。木管轨包含已改编的小节；钢琴的左右手共用一个轨道。MIDI 的声道音量将三个木管设为 120、钢琴设为 45（满值 127）；不改动谱面力度和音符力度。
- `output/score.musicxml` 是六乐章完整总谱，包含三个木管声部和双谱表钢琴声部，单簧管使用 B♭ 移调记谱。

需要 LilyPond（以 2.26.0 验证）和 Python 3。首次使用时，在仓库根目录安装 MusicXML 导出依赖：

```sh
python3 -m venv fl-ob-cl-piano/.venv
fl-ob-cl-piano/.venv/bin/pip install -r fl-ob-cl-piano/requirements-musicxml.txt
```

然后运行：

```sh
python3 fl-ob-cl-piano/build.py
```

此命令会同时更新总谱 PDF、全曲 MIDI 和完整 MusicXML，并自动核对 MusicXML 和 MIDI 的音高及起音位置。MusicXML 从 LilyPond 编译后的声部结构生成，不依赖旧的钢琴 MusicXML；不同记谱软件中的排版及个别记号显示可能有所差异，演奏时请以 PDF 总谱为准。

钢琴声部继承原稿尚未逐音精校的限制，详见 `../EDITORIAL.md`；MIDI 的印刷反复线尚未展开。管弦乐原谱注明小音符应在拍上演奏；当前 LilyPond 生成的 MIDI 将装饰音放在主音前，试听时请留意。原有 `output/prelude-22-29.musicxml` 仅是较早生成的节选，完整总谱请使用 `score.musicxml`。
