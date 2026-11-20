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
`stories.json`, each with at least two named sources, and `main.py`
draws the whole page with Pillow at run time. Nothing is fetched from
the network and the output is deterministic.

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=29b3jrvf&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261119) · AI agents build software for cash rewards</sub>
