# Right Now — how items are added

This repository is the Right Now feed for filmsuperintelligence.org. It is served by GitHub Pages at now.filmsuperintelligence.org. The homepage reads `now.json`, `site.json` and `atlas.json` from here, so changes here never need a Netlify deploy.

## One item = one file

Each item is one JSON file in `items/`. The file name is the item id: `YYYY-MM-DD-short-name.json` (lowercase, hyphens only).

```json
{
 "id": "2026-09-28-pope-risk",
 "date": "2026-09-28",
 "who": "Pope Leo XIV",
 "role": "Head of the Catholic Church",
 "kind": "quote",
 "text": "I do think that the concerns raised by many of the experts, specialists in AI, should be taken seriously.",
 "context": "On his flight home from France, after AI fears were called a hoax.",
 "outlet": "Al Jazeera",
 "sourceNote": "Papal news conference; AFP, AP and Reuters",
 "url": "https://www.aljazeera.com/economy/2026/9/29/pope-leo-says-ai-risk-concerns-not-fake-news"
}
```

- `date`: the day it was said or published.
- `kind`: `quote` (the person's exact words) or `headline` (an outlet's exact headline, word for word).
- `text`: 25 words or fewer where possible, 40 maximum. Mark cuts with `…`. Never paraphrase inside a quote.
- `context`: one plain sentence. Short quoted fragments are allowed if they are exact.
- `outlet`: who reported it; `url`: the best available link, preferably the original (transcript, the person's own post, the agency report).
- Optional `sourceNote`: where exactly it was said (hearing, interview, post).
- Optional `note`: shown on the card, for example `Translated from Chinese`.

## Standards

- Every quote is checked against the original video, transcript, post or agency report before it goes in. If the exact words cannot be confirmed, it does not go in.
- Worldwide, not US-only. Builders first, then governments, international bodies, faith leaders, scientists, artists and critics, from every region.
- The most striking, consequential statements: probabilities, timelines, warnings of loss of control, admissions by builders, bold claims of what AI will do. Hopeful and alarmed both qualify. The feed takes no position.
- Bert Holland approves every item before it is published.

## Publishing

```
python3 tools/build.py      # validates every item and rebuilds the site files
git add -A && git commit -m "Right Now: <who>, <date>" && git push
```

GitHub Pages updates within a minute or two. Corrections: edit the item file, rebuild, push. Git keeps every earlier version.

## Other data the homepage reads

- `site.json`: `enterUrl` (where every Enter button goes) and `deadlines`, a list of `{label, short, date}` with ISO date-times such as `2026-11-21T23:59:00-08:00`. The countdown always shows the next deadline still ahead.
- `atlas.json`: countries for the Atlas globe. `fs` lists confirmed Film Superintelligence winners only. While `sample` is true, the dimmer network layer is a placeholder.
