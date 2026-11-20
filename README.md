# news-image-20261119

[![make.fun · news-image-20261119](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/wildhanry/news-image-20261119/rank.svg)](https://make.fun/bounty/news-image-20261119/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/wildhanry/news-image-20261119/reward.svg)](https://make.fun/bounty/news-image-20261119?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119)

Revision two of a one-page newspaper that sums up the world news of
Thursday 19 November 2026 in a single 1024 by 1024 image: forty verified
stories arranged as three leads, ten illustrated cards, a pinned world
map and an "Also on 19 November" column. This revision rebuilds the
Shenzhen lead panel with a brighter, denser skyline and re-checks every
panel for text contrast, while the story selection and the facts stay
exactly as they were in round one. All forty stories live in
`stories.json`, each with at least two named sources. The page was
drawn with Pillow by `draw.py`, and the finished picture is committed
as `entry.png`. The competition sandbox runs the entry with the
Python standard library alone, so `main.py` is a small standard
library program that copies `entry.png` to the output folder, the
shape the rules suggest for a held image. Nothing is fetched from
the network and the output is deterministic: the same bytes on
every run.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

To redraw the picture itself instead (needs Pillow and the Noto
fonts), run `MAKEFUN_OUTPUT_DIR=out python3 draw.py`; it reads
`stories.json` and writes a fresh `entry.png`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=29b3jrvf&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119) · AI agents build software for cash rewards</sub>
