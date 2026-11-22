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
Card scans (`static/img/cards/`) and the About photo (`static/img/home-photo.jpg`)
live in this repo. Nothing on the site loads from Wix. To add a year's card, drop
the scan in `static/img/cards/` and add it to `CARD_YEARS` in `build.py`.

## Games
14 Points and Sheng Ji are single files: `static/14-points/index.html` and
`static/sheng-ji/index.html`. These are now the copies to edit. The older
copies on PythonAnywhere are no longer what the site serves.

## What still lives elsewhere
- Card sign-up form, and the online-room relay both games share (`/sj`): bryanzhang.pythonanywhere.com
- Drink Diary: beverage-journal.onrender.com

## Daily board and the home page's "Today" rows
- `server/shengji_relay.py` is the file that runs on PythonAnywhere at `/sj`. It
  passes messages for online rooms and keeps the 14 Points daily board
  (`/sj/board/post`, `/sj/board/top`). This repo holds the copy to edit; to
  release a change, upload it over the one on PythonAnywhere and reload the
  web app. Nothing deploys it automatically.
- Only the standard daily deal (you against one medium computer) posts to the
  board. A name is typed once and kept on that device. There are no accounts,
  so anyone can post under any name.
- The home page fills in the deal number, yesterday's top score (from the
  board) and the newest drink (from the journal's `/public/latest.json`). A row
  whose source can't be reached stays hidden.
