# bryanzhang.fun

Plain static site. `python3 build.py` writes `public/` (the site) and `preview.html`.
Edit copy and pages in `build.py`; never edit `public/` by hand.

## Hosting (Render static site)
- Build command: leave empty
- Publish directory: `public`
- Auto-deploy: on push to main

`public/` is committed, so the host serves it as-is. Run `python3 build.py` before
committing any change to `build.py` or `static/`.

## Images still needed (put them here, then rebuild)
- `static/img/about.jpg`            Bryan
- `static/img/cards/2025-alhambra-1.png`, `2025-alhambra-2.png`
- `static/img/cards/2024-hd-museum-1.png`, `2024-hd-museum-2.png`
- `static/img/cards/2023-tokyo-1.png`, `2023-tokyo-2.png`
- `static/img/cards/2022-new-jersey-1.png`
- `static/img/cards/2021-harlem-1.png`

## What still lives elsewhere
- 14 Points, Sheng Ji, card sign-up form: bryanzhang.pythonanywhere.com
- Drink Diary: beverage-journal.onrender.com
- Snake: a Wix-hosted embed. Copy it out before the Wix plan ends.
