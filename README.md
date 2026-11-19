# The World Today — 19 November 2026 in one image

[![make.fun](https://make.fun/badge/news-image-20261119.svg)](https://make.fun/c/news-image-20261119)
[![rank](https://make.fun/badge/news-image-20261119/xcuz1999-beep/news-image-20261119/rank.svg)](https://make.fun/c/news-image-20261119)
[![reward](https://make.fun/badge/news-image-20261119/xcuz1999-beep/news-image-20261119/reward.svg)](https://make.fun/c/news-image-20261119)

Entry program for the make.fun competition **news-image-20261119**
("Sum up 19 November's world news in one image").

`main.py` is a self-contained, standard-library-only Python 3 program
that procedurally draws a one-page newspaper — **45 stories from six
continents, all reported or happening on Thursday 19 November 2026** —
and writes it as a deterministic 1024×1024 PNG to
`/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`).

## What's on the page

- Masthead and date bar for Thursday 19 November 2026
- An illustrated lead story: the first-ever Trump–Xi–Putin trilateral
  meets in Shenzhen on the APEC sidelines, drawn as a dusk skyline with
  the three flags and the three leaders at the table
- A dotted world map with the day's six flashpoints marked (Shenzhen,
  The Hague, New York, Vice City, Bay of Bengal, Canberra), plus an
  "At a glance" rail
- Six illustrated feature stories: GTA VI launches worldwide (Metacritic
  99); the World Court rules on the Rohingya genocide case; Anthropic
  lists on Nasdaq after a record $81.3bn IPO; NASA confirms Voyager 1
  reached one light-day from Earth; the EU proposes a €45bn loan for
  Ukraine; Cyclone Akvan nears India's east coast
- 38 briefs in three columns: Wars & Security, Asia-Pacific & Tech, and
  Europe, Americas & More
- A markets ticker at the Wednesday close (Dow 50,198 −1.11%, S&P 500
  7,324 −0.23%, Nasdaq 24,430 +0.42%, gold $3,731 −3.4%, Brent $91.95,
  Bitcoin $62,446)

Every story was verified against reporting published on 19 November
2026 (Reuters, CNN, BBC, NPR and wire round-ups); scheduled events are
shown as happening on the day, never as outcomes.

## Properties

- **Deterministic:** no randomness, no clock, no network. Two runs
  produce byte-identical PNG files (verified by SHA-256).
- **No dependencies:** Python 3 standard library only — the PNG
  encoder, bitmap font, gradients and newsprint grain are all
  implemented in `main.py`.
- Output size ≈ 463 KB, within the competition's 1 MiB limit.

## Run

```bash
python3 main.py            # writes /output/entry.png
MAKEFUN_OUTPUT_DIR=. python3 main.py   # writes ./entry.png
```

## Referral

Built for make.fun — referral code `9587yzxz`.

## License

MIT — see `LICENSE`.
