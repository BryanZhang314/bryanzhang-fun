#!/usr/bin/env python3
"""Builds bryanzhang.fun as plain static files, plus a one-file preview.

  python3 build.py            -> ./public (the real site) and ./preview.html

Pages are defined once below. The real site gets one folder per page with
live embeds; the preview swaps embeds and photos for labelled slots, because
the preview host blocks outside frames and images.
"""
import html, os, shutil, sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "public")
PREVIEW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "preview.html")
SITE = "Bryan's Cyber-Physiognomy"
ORIGIN = "https://www.bryanzhang.fun"

# page key -> (url path on the real site, hash name in the preview)
ROUTES = {
    "home": ("/", "home"),
    "games": ("/games/", "games"),
    "14-points": ("/14-points/", "fourteen-points"),
    "sheng-ji": ("/sheng-ji/", "sheng-ji"),
    "drink-diary": ("/drink-diary/", "drink-diary"),
    "cards": ("/bryan-xingjia-holiday-card/", "cards"),
    "about": ("/about/", "about"),
    "privacy": ("/privacy/", "privacy"),
}

# These two pages are the game files themselves (static/<name>/index.html), not a
# shell around a frame, so they load fast and their invite links stay short.
GAME_FILES = {"14-points", "sheng-ji"}

EMBEDS = {
    "14-points": "https://bryanzhang.pythonanywhere.com/14-points/14-points.html",
    "sheng-ji": "https://bryanzhang.pythonanywhere.com/sheng-ji/Sheng-Ji-80-points.html",
    "drink-diary": "https://beverage-journal.onrender.com/public/",
    "cards": "https://bryanzhang.pythonanywhere.com/",
}

CSS = r"""
:root{
  /* layout: one quiet column on blush; each destination is a plain row, the game of the day gets the only dark block */
  --blush:#EBC3CA; --petal:#F4DCE0; --paper:#FCF4F4; --olive:#4C5327; --ink:#2E3220; --rule:rgba(46,50,32,.22);
  --display:"Poppins","Helvetica Neue",Arial,sans-serif;
  --body:"Poppins","Helvetica Neue",Arial,sans-serif;
  color-scheme:light;
}
*{box-sizing:border-box}
html,body{margin:0}
body{background:var(--blush);color:var(--ink);font:400 16px/1.6 var(--body);-webkit-text-size-adjust:100%}
a{color:var(--olive);text-underline-offset:.18em}
a:focus-visible,button:focus-visible{outline:3px solid var(--ink);outline-offset:3px;border-radius:4px}
img{max-width:100%;display:block}
h1,h2,h3{font-family:var(--display);font-weight:500;color:var(--olive);line-height:1.14;text-wrap:balance;margin:0}
h1{font-size:clamp(2rem,5.6vw,3.2rem);letter-spacing:-.015em}
h2{font-size:1.45rem}
h3{font-size:1.1rem}
p{margin:0;max-width:62ch;text-wrap:pretty}
.wrap{max-width:1040px;margin:0 auto;padding:0 20px}
.stack{display:flex;flex-direction:column;gap:18px}

/* header */
.top{border-bottom:1.5px solid var(--rule)}
.top .wrap{display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;gap:6px 24px;padding-top:14px;padding-bottom:14px}
.brand{font-family:var(--display);font-weight:600;color:var(--olive);text-decoration:none;font-size:1.02rem}
.nav{display:flex;flex-wrap:wrap;gap:4px 18px}
.nav a{text-decoration:none;font-weight:500;font-size:.95rem;padding:4px 0;border-bottom:2px solid transparent}
.nav a:hover,.nav a[aria-current="page"]{border-bottom-color:var(--olive)}

main{padding:44px 0 64px}
.lede{font-size:1.15rem}
.btn{display:inline-block;font-weight:600;text-decoration:none;padding:11px 20px;border-radius:8px;border:2px solid var(--ink);background:var(--ink);color:var(--paper)}
.btn.ghost{background:transparent;color:var(--ink)}
.btn:hover{transform:translateY(-1px)}
@media (prefers-reduced-motion:reduce){.btn:hover{transform:none}}
.row{display:flex;flex-wrap:wrap;gap:12px;align-items:center}
.eyebrow{font-weight:600;font-size:.78rem;letter-spacing:.09em;text-transform:uppercase;color:var(--olive)}

/* home */
.hero{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:36px;align-items:start}
.today{background:var(--ink);color:var(--paper);border-radius:14px;padding:26px;display:flex;flex-direction:column;gap:12px}
.today h2,.today .eyebrow{color:var(--paper)}
.today h2{font-size:1.9rem}
.today .btn{background:var(--paper);color:var(--ink);border-color:var(--paper);align-self:flex-start}
.today .quiet{color:var(--paper);font-weight:500}
.cats{display:flex;flex-direction:column;margin-top:44px;border-bottom:1.5px solid var(--rule)}
.cat{display:grid;grid-template-columns:minmax(0,8.5rem) minmax(0,1fr);gap:0 28px;border-top:1.5px solid var(--rule)}
.cat>h2{padding-top:25px;font-size:1rem;letter-spacing:.09em;text-transform:uppercase}
.doors{display:flex;flex-direction:column}
.door{display:grid;grid-template-columns:minmax(0,10.5rem) minmax(0,1fr) auto;gap:8px 24px;align-items:baseline;padding:20px 0;text-decoration:none;color:inherit}
.door+.door{border-top:1.5px solid var(--rule)}
.door h3{font-size:1.3rem}
.door .go{font-weight:600;color:var(--olive);white-space:nowrap}
.door:hover h3{text-decoration:underline;text-underline-offset:.15em}
.lately{margin-top:44px}
.lately ul{list-style:none;margin:10px 0 0;padding:0;display:flex;flex-direction:column;gap:6px}
.lately li{display:grid;grid-template-columns:5.5rem minmax(0,1fr);gap:0 8px}
.lately time{font-weight:600;color:var(--olive);font-variant-numeric:tabular-nums}

/* photo and card slots */
.slot{margin:0;position:relative;background:var(--petal);border:1.5px solid var(--rule);border-radius:10px;overflow:hidden;display:flex;align-items:flex-end}
.slot img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.slot figcaption{position:relative;z-index:1;width:100%;padding:8px 12px;font-size:.85rem;font-weight:500;background:rgba(252,244,244,.92);border-top:1.5px solid var(--rule)}
.slot.photo{aspect-ratio:4/5}
.slot.card{display:block}
.slot.card img{position:static;width:100%;height:auto}
.slot.card.empty{aspect-ratio:3/4;display:flex}
.slot .missing{position:absolute;inset:0 0 40px 0;display:grid;place-items:center;text-align:center;padding:12px;font-size:.85rem;color:var(--olive);font-weight:500}

/* embeds */
.stage{position:relative;background:var(--petal);border:1.5px solid var(--rule);border-radius:12px;overflow:hidden}
.stage.live::before{content:"Loading\2026";position:absolute;inset:0 0 auto 0;padding:64px 24px;text-align:center;color:var(--olive);font-weight:500}
.stage iframe{position:relative;display:block;width:100%;border:0;height:max(720px,calc(100dvh - 150px))}
.stage.tall iframe{height:1650px}
.stage .standin{padding:56px 24px;display:flex;flex-direction:column;gap:14px;align-items:flex-start}
.gamehead{display:flex;flex-wrap:wrap;align-items:baseline;justify-content:space-between;gap:8px 24px;margin-bottom:16px}
.gamehead h1{font-size:clamp(1.7rem,4.5vw,2.4rem)}
.gamehead p{font-size:.98rem}

/* games hub */
.games{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:20px;margin-top:28px}
.game{background:var(--paper);border:1.5px solid var(--rule);border-radius:14px;padding:24px;display:flex;flex-direction:column;gap:12px}
.game .btn{align-self:flex-start;margin-top:auto}
.aside{margin-top:36px;font-size:.92rem}

/* cards */
.years{display:flex;flex-direction:column;gap:28px;margin-top:20px}
.year{display:grid;grid-template-columns:7rem minmax(0,1fr);gap:8px 24px;align-items:start;border-top:1.5px solid var(--rule);padding-top:18px}
.year .when{font-family:var(--display);font-weight:500;font-size:1.6rem;color:var(--olive);font-variant-numeric:tabular-nums;line-height:1}
.year .where{font-weight:500;font-size:.92rem}
.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;max-width:640px;align-items:start}
.pair.wide{grid-template-columns:minmax(0,1fr)}
.prose{display:flex;flex-direction:column;gap:16px}
.prose h2{margin-top:14px}
.split{display:grid;grid-template-columns:minmax(0,1.6fr) minmax(0,1fr);gap:36px;align-items:start}

/* footer */
.foot{border-top:1.5px solid var(--rule);padding:26px 0 40px;font-size:.92rem}
.foot .wrap{display:flex;flex-wrap:wrap;gap:8px 28px;justify-content:space-between}
.foot .links{display:flex;flex-wrap:wrap;gap:6px 20px}

@media (max-width:720px){
  main{padding:28px 0 48px}
  .hero,.split,.games{grid-template-columns:minmax(0,1fr)}
  .door{grid-template-columns:minmax(0,1fr)}
  .cat{grid-template-columns:minmax(0,1fr)}
  .cat>h2{padding-top:18px}
  .cat .door:first-child{padding-top:10px}
  .year{grid-template-columns:minmax(0,1fr)}
  .stage iframe{height:max(640px,calc(100dvh - 120px))}
}
"""

FAVICON = ("data:image/svg+xml," + "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
           "%3Crect width='64' height='64' rx='12' fill='%23EBC3CA'/%3E"
           "%3Crect x='14' y='10' width='36' height='44' rx='5' fill='%23FCF4F4' stroke='%232E3220' stroke-width='3'/%3E"
           "%3Ctext x='32' y='41' text-anchor='middle' font-family='sans-serif' font-weight='900' font-size='20' fill='%234C5327'%3E14%3C/text%3E%3C/svg%3E")

NAV = [("cards", "Holiday Card"), ("games", "Games"), ("drink-diary", "Drink Diary"), ("about", "About")]


def e(s):
    return html.escape(s, quote=True)


class Ctx:
    """Knows whether we are writing the real site or the one-file preview."""

    def __init__(self, preview):
        self.preview = preview

    def link(self, key):
        path, name = ROUTES[key]
        return "#" + name if self.preview else path

    def embed(self, key, title, tall=False):
        url = EMBEDS[key]
        cls = "stage tall" if tall else "stage"
        if self.preview:
            return (f'<div class="{cls}"><div class="standin"><span class="eyebrow">Preview stand-in</span>'
                    f'<h2>{e(title)} loads here on the live site</h2>'
                    f'<p>This preview can\'t show outside frames. On bryanzhang.fun this box is the real thing, full width.</p>'
                    f'<a class="btn ghost" href="{e(url)}">Open it in a new tab</a></div></div>')
        return (f'<div class="{cls} live"><iframe src="{e(url)}" title="{e(title)}" '
                f'allow="clipboard-write; fullscreen; web-share"></iframe></div>'
                f'<p class="aside"><a href="{e(url)}">Open it on its own page</a> if the frame misbehaves.</p>')

    def slot(self, kind, src, alt, caption="", w=None, h=None):
        cap = f'<figcaption>{e(caption)}</figcaption>' if caption else ""
        if self.preview:
            return f'<figure class="slot {kind} empty"><div class="missing">Image goes here</div>{cap}</figure>'
        dims = f' width="{w}" height="{h}"' if w and h else ""
        return f'<figure class="slot {kind}"><img src="{e(src)}" alt="{e(alt)}"{dims} loading="lazy">{cap}</figure>'


def home(c):
    past = "#past-cards" if c.preview else ROUTES["cards"][0] + "#past-cards"
    return f"""
<div class="hero">
  <div class="stack">
    <h1>This was supposed to be a holiday card sign-up page.</h1>
    <p class="lede">It got out of hand. Now it has two card games and a drink diary.</p>
  </div>
  <div class="today">
    <span class="eyebrow">2026 card list is open</span>
    <h2>Holiday Card</h2>
    <p>Tell us where to send yours, or check we still have your address right. Cards go out before the year ends.</p>
    <div class="row">
      <a class="btn" href="{c.link('cards')}">Get on the card list</a>
      <a class="quiet" href="{past}">See past cards</a>
    </div>
  </div>
</div>

<div class="cats">
  <section class="cat">
    <h2>Cards</h2>
    <div class="doors">
      <a class="door" href="{c.link('cards')}"><h3>Card sign-up</h3><p>Once a year we mail out a card. Get on the list or fix your address.</p><span class="go">Sign up &rarr;</span></a>
      <a class="door" href="{past}"><h3>Past cards</h3><p>Every card we've sent since 2021: Harlem, New Jersey, Tokyo, HD Museum, Alhambra.</p><span class="go">Look &rarr;</span></a>
    </div>
  </section>
  <section class="cat">
    <h2>Games</h2>
    <div class="doors">
      <a class="door" href="{c.link('14-points')}"><h3>14 Points</h3><p>My own card game. Make sets that add up to 14. Today's deal is the same shuffle for everyone, so play it and send someone your result.</p><span class="go">Play &rarr;</span></a>
      <a class="door" href="{c.link('sheng-ji')}"><h3>Sheng Ji <span lang="zh">升级</span></h3><p>80 points, in English or 中文. Play solo, or send one friend a link and play from two phones.</p><span class="go">Play &rarr;</span></a>
    </div>
  </section>
  <section class="cat">
    <h2>Drinks</h2>
    <div class="doors">
      <a class="door" href="{c.link('drink-diary')}"><h3>Drink Diary</h3><p>What we've been drinking, with notes and ratings from both of us.</p><span class="go">Read &rarr;</span></a>
    </div>
  </section>
</div>

<div class="lately">
  <h2>Lately</h2>
  <ul>
    <li><time datetime="2026-11-15">15 Nov</time><span>The Drink Diary opened.</span></li>
    <li><time datetime="2026-11">Nov</time><span>The 2026 card list is open. Cards go out before the year ends.</span></li>
  </ul>
</div>
"""


def games(c):
    return f"""
<div class="stack">
  <h1>Games</h1>
  <p class="lede">Once you own a website, apparently you have to put games on it. Play them. Someone has to.</p>
</div>
<div class="games">
  <div class="game">
    <span class="eyebrow">2 to 4 players, or solo</span>
    <h2>14 Points</h2>
    <p>Make sets that add up to 14: one field card plus cards from your hand. There's a daily deal, the same shuffle for everyone, and a two-minute tutorial. The card backs are our old holiday cards.</p>
    <a class="btn" href="{c.link('14-points')}">Play 14 Points</a>
  </div>
  <div class="game">
    <span class="eyebrow">2 to 4 players, or solo</span>
    <h2>Sheng Ji <span lang="zh">升级</span> · 80 points</h2>
    <p>The trick-taking game, with trump hosts, kitties and overtrumps. Play the computers, pass one device around, or open a room and send a friend the link.</p>
    <a class="btn" href="{c.link('sheng-ji')}">Play Sheng Ji</a>
  </div>
</div>
"""


def game_page(key, title, blurb):
    def render(c):
        return f"""
<div class="gamehead">
  <h1>{title}</h1>
  <p>{blurb}</p>
</div>
{c.embed(key, PAGES[key]['embed_title'])}
"""
    return render


def drink(c):
    return f"""
<div class="gamehead">
  <h1>Drink Diary</h1>
  <p>A journal kept by Bryan and Xingjia.</p>
</div>
{c.embed('drink-diary', 'The Drink Diary', tall=True)}
"""


# Card scans are still served from Wix's image host (the files uploaded there in July 2026).
WIX = "https://static.wixstatic.com/media/"
CARD_YEARS = [
    ("2026", "On its way", []),
    ("2025", "Alhambra", [("3409c0_127c7685e49445ca80f4ea74d4b44e38~mv2.png", 620, 838), ("3409c0_c3af685ff9bf4949ba208cfc751caf84~mv2.png", 624, 855)]),
    ("2024", "HD Museum", [("3409c0_844e7e2efb4147f299016c2ef83fea5c~mv2.png", 593, 804), ("3409c0_65416871495f4ff6b0288069d6371cd2~mv2.png", 614, 806)]),
    ("2023", "Tokyo", [("3409c0_1ea9292511674fafa770594bafef4791~mv2.png", 606, 798), ("3409c0_3024c3234fbd4633b97397cb825af68b~mv2.png", 594, 791)]),
    ("2022", "New Jersey", [("3409c0_c66085823e824023b05a67cd5996f97a~mv2.png", 1309, 837)]),
    ("2021", "Harlem", [("3409c0_2a74c66615b347ae987364a93466ce77~mv2.png", 695, 884)]),
]
HOME_PHOTO = WIX + "3409c0_2f1e84c2a5b84c1fad418d7263765fdf~mv2.jpg/v1/fill/w_800,h_1000,al_c,q_85/photo.jpg"


def cards(c):
    rows = []
    for year, where, imgs in CARD_YEARS:
        if imgs:
            figs = "".join(c.slot("card", WIX + n, f"{where} holiday card, {year}", f"{where}, {year}", w, h) for n, w, h in imgs)
            body = f'<div class="pair{" wide" if len(imgs) == 1 and imgs[0][1] > imgs[0][2] else ""}">{figs}</div>'
        else:
            body = "<p>This year's card goes out before the year ends. It shows up here once it has landed in mailboxes.</p>"
        rows.append(f'<div class="year"><div><div class="when">{year}</div><div class="where">{e(where)}</div></div>{body}</div>')
    return f"""
<div class="stack">
  <h1>Bryan &amp; Xingjia's Holiday Card</h1>
  <p class="lede">Once a year we mail out a card. Tell us where to send yours, or check we still have your address right.</p>
  <div class="row"><a class="btn ghost" href="#past-cards">See our past cards</a></div>
</div>
<div style="margin-top:28px">{c.embed('cards', 'The card sign-up', tall=True)}</div>
<div class="stack" style="margin-top:48px" id="past-cards">
  <h2>Previous holiday cards</h2>
  <p>Thank you Shannon for the digital holiday cards suggestion. I'm still finding the backs of the older cards, so some years only show the front.</p>
</div>
<div class="years">{''.join(rows)}</div>
"""


def about(c):
    return f"""
<div class="split">
  <div class="prose">
    <h1>About</h1>
    <p class="lede">Hi, I'm Bryan.</p>
    <p>Every year I send holiday cards to friends and family, and Xingjia has since joined in. This site started as the card sign-up. Then I kept adding games. Nothing here is for sale.</p>
    <div class="row"><a class="btn" href="{c.link('cards')}">Get on the card list</a></div>
  </div>
  {c.slot('photo', HOME_PHOTO, 'A person in a pink hat and sunglasses standing in a field of pink flowers', '', 800, 1000)}
</div>
"""


def privacy(c):
    return """
<div class="prose">
  <h1>Privacy policy</h1>
  <p class="lede">The short version.</p>
  <p>This site exists so Xingjia and I can mail you a holiday card, and so you can play cards.</p>
  <p><strong>What we collect:</strong> the name, mailing address, and optional email, phone and notes you enter on the card sign-up form.</p>
  <p><strong>What we use it for:</strong> mailing you a card, and checking once a year that your address is still right.</p>
  <p><strong>What stays on your device:</strong> the games remember your player names, card back and settings in your own browser. That never reaches us.</p>
  <p><strong>Want off the list, or want your info deleted?</strong> Use the personal link we sent you, or email <a href="mailto:BryanZhang314@Gmail.com">BryanZhang314@Gmail.com</a> and we'll take care of it.</p>
</div>
"""


PAGES = {
    "home": dict(title=SITE, desc="Bryan Zhang's site: a yearly holiday card, two card games and a drink diary.", body=home),
    "games": dict(title="Games", desc="14 Points and Sheng Ji, two card games you can play in the browser.", body=games),
    "14-points": dict(title="14 Points", desc="A card game by Bryan. Make sets that add up to 14. Play today's deal, the same shuffle for everyone.", embed_title="14 Points"),
    "sheng-ji": dict(title="Sheng Ji 升级 · 80 points", desc="Sheng Ji (80 points) in the browser, in English or Chinese. Play solo or send a friend the link.", embed_title="Sheng Ji"),
    "drink-diary": dict(title="Drink Diary", desc="What Bryan and Xingjia have been drinking, with notes and ratings.", body=drink),
    "cards": dict(title="Holiday Card", desc="Get on Bryan and Xingjia's holiday card list, and see every card since 2021.", body=cards),
    "about": dict(title="About", desc="About Bryan and this site.", body=about),
    "privacy": dict(title="Privacy", desc="What this site collects and why. It's short.", body=privacy),
}
PAGES["14-points"]["body"] = game_page("14-points", "14 Points", "Make sets that add up to 14. Today's deal is the same shuffle for everyone.")
PAGES["sheng-ji"]["body"] = game_page("sheng-ji", 'Sheng Ji <span lang="zh">升级</span>', "80 points. Two to four players, or solo against the computers.")


def header(c, current):
    items = "".join(
        f'<a href="{c.link(k)}"{" aria-current=\"page\"" if k == current else ""} data-nav="{ROUTES[k][1]}">{label}</a>'
        for k, label in NAV)
    return (f'<header class="top"><div class="wrap"><a class="brand" href="{c.link("home")}">{e(SITE)}</a>'
            f'<nav class="nav" aria-label="Site">{items}</nav></div></header>')


def footer(c):
    return (f'<footer class="foot"><div class="wrap"><div class="links">'
            f'<span>Say hello: <a href="mailto:BryanZhang314@Gmail.com">BryanZhang314@Gmail.com</a></span>'
            f'<a href="{c.link("privacy")}">Privacy policy (it\'s short)</a></div>'
            f'<span>&copy; 2666 by {e(SITE)}</span></div></footer>')


FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">')


def real_page(key):
    c = Ctx(False)
    p = PAGES[key]
    path = ROUTES[key][0]
    full = p["title"] if key == "home" else f'{p["title"]} · {SITE}'
    og_img = f"{ORIGIN}/img/og/{key}.png"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(full)}</title>
<meta name="description" content="{e(p['desc'])}">
<link rel="canonical" href="{ORIGIN}{path}">
<meta property="og:site_name" content="{e(SITE)}">
<meta property="og:title" content="{e(p['title'])}">
<meta property="og:description" content="{e(p['desc'])}">
<meta property="og:type" content="website">
<meta property="og:url" content="{ORIGIN}{path}">
<meta property="og:image" content="{og_img}">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{FAVICON}">
{FONTS}
<link rel="stylesheet" href="/site.css">
</head>
<body>
{header(c, key)}
<main><div class="wrap">{p['body'](c)}</div></main>
{footer(c)}
</body>
</html>
"""


def redirect_page(to):
    return (f'<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Moved</title>'
            f'<meta http-equiv="refresh" content="0; url={to}"><link rel="canonical" href="{ORIGIN}{to}"></head>'
            f'<body><p>This page moved to <a href="{to}">{to}</a>.</p></body></html>\n')


def build_site():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    with open(os.path.join(OUT, "site.css"), "w") as f:
        f.write(CSS.strip() + "\n")
    for key in PAGES:
        if key in GAME_FILES:
            continue  # the game's own file in static/ is the page
        d = os.path.join(OUT, ROUTES[key][0].strip("/"))
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "index.html"), "w") as f:
            f.write(real_page(key))
    # the old Wix address for About
    os.makedirs(os.path.join(OUT, "about-1"))
    with open(os.path.join(OUT, "about-1", "index.html"), "w") as f:
        f.write(redirect_page("/about/"))
    # photos, card scans and link-preview images live in ./static and are copied as-is
    static = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
    if os.path.isdir(static):
        shutil.copytree(static, OUT, dirs_exist_ok=True)


def build_preview():
    c = Ctx(True)
    sections = "".join(
        f'<section data-page="{ROUTES[k][1]}" hidden><div class="wrap">{PAGES[k]["body"](c)}</div></section>' for k in PAGES)
    js = """
const pages=[...document.querySelectorAll('section[data-page]')];
function show(){
  let name=location.hash.slice(1), target=null;
  if(name==='past-cards'){ name='cards'; target='past-cards'; }
  if(!pages.some(p=>p.dataset.page===name)) name='home';
  pages.forEach(p=>p.hidden=p.dataset.page!==name);
  document.querySelectorAll('[data-nav]').forEach(a=>{ if(a.dataset.nav===name) a.setAttribute('aria-current','page'); else a.removeAttribute('aria-current'); });
  if(target){ const el=document.getElementById(target); if(el) el.scrollIntoView(); } else window.scrollTo(0,0);
}
addEventListener('hashchange',show); show();
"""
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>bryanzhang.fun rebuild preview</title>
<link rel="icon" href="{FAVICON}">
{FONTS}
<style>{CSS}
section[hidden]{{display:none}}
</style>
</head>
<body>
{header(c, 'home')}
<main>{sections}</main>
{footer(c)}
<script>{js}</script>
</body>
</html>
"""
    with open(PREVIEW, "w") as f:
        f.write(doc)


if __name__ == "__main__":
    build_site()
    build_preview()
    n = sum(len(fs) for _, _, fs in os.walk(OUT))
    print(f"site: {n} files in {OUT}\npreview: {PREVIEW} ({os.path.getsize(PREVIEW)} bytes)")
