# bryanzhang.fun

Plain static site. `python3 build.py` writes `public/` (the site) and `preview.html`.
Edit copy and pages in `build.py`; never edit `public/` by hand.

## Hosting (Render static site)
- Build command: leave empty
- Publish directory: `public`
- Auto-deploy: on push to main

`public/` is committed, so the host serves it as-is. Run `python3 build.py` before
committing any change to `build.py` or `static/`.

## Images
Card scans and the About photo are loaded straight from Wix's image host
(static.wixstatic.com), using the files uploaded there in July 2026. They keep
working only while those files stay in the Wix account. To make the site
independent, save them into `static/img/` and point `CARD_YEARS` and
`HOME_PHOTO` in `build.py` at the local paths.

## Games
14 Points and Sheng Ji are single files: `static/14-points/index.html` and
`static/sheng-ji/index.html`. These are now the copies to edit. The older
copies on PythonAnywhere are no longer what the site serves.

## What still lives elsewhere
- Card sign-up form and the Sheng Ji online-room relay: bryanzhang.pythonanywhere.com
- Drink Diary: beverage-journal.onrender.com
