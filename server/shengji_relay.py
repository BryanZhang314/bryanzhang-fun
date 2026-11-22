"""Sheng Ji online rooms: a tiny relay for bryanzhang.pythonanywhere.com.

The host's phone runs the whole game. This relay only passes messages:
  - guests -> host: joins, declares, answers (a queue the host reads)
  - host -> each guest: the latest view of the table (each guest only ever
    receives their own hand)

Phones poll about once a second. Plain HTTP, so it runs on any
PythonAnywhere plan; no WebSockets. Rooms live in a small SQLite file
next to this module and are cleaned up after 12 hours.

Add it to the existing Flask app (holiday_cards or any other):

    from shengji_relay import relay
    app.register_blueprint(relay)          # serves /sj/...

then reload the web app. Nothing else on the site changes.

Daily board (added Nov 22): the same file also keeps the 14 Points daily
board at /sj/board/post and /sj/board/top. A score is a name someone typed
plus their points for that day's deal; the first score a name posts for a
day is the one that stands. No accounts, so treat it as a board for friends.
"""
import json
import os
import random
import secrets
import sqlite3
import time
import unicodedata

from flask import Blueprint, Response, request

relay = Blueprint("shengji_relay", __name__, url_prefix="/sj")

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "shengji_rooms.sqlite3")
CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"   # no 0/O, 1/I/L
ROOM_TTL = 12 * 3600
MAX_GUESTS = 7          # 3 players + up to 4 watchers (Nov 21)
MAX_BODY = 96 * 1024
BOARD_GAMES = {"14p": 999}   # game -> highest score accepted
BOARD_DAY_ZERO = 1735689600  # 2025-01-01 UTC, the day the games count from
BOARD_MAX_ROWS = 300         # per game per day


def db():
    con = sqlite3.connect(DB, timeout=10)
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS rooms (code TEXT PRIMARY KEY, created REAL);
        CREATE TABLE IF NOT EXISTS players (code TEXT, pid INTEGER, token TEXT, name TEXT, last_seen REAL,
                                            PRIMARY KEY (code, pid));
        CREATE TABLE IF NOT EXISTS msgs (id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT, to_pid INTEGER,
                                         from_pid INTEGER, body TEXT, ts REAL);
        CREATE TABLE IF NOT EXISTS states (code TEXT, pid INTEGER, v INTEGER, body TEXT, PRIMARY KEY (code, pid));
        CREATE INDEX IF NOT EXISTS msgs_to ON msgs (code, to_pid, id);
        CREATE TABLE IF NOT EXISTS board (game TEXT, day INTEGER, key TEXT, name TEXT, score INTEGER,
                                          won INTEGER, steals INTEGER, ts REAL, PRIMARY KEY (game, day, key));
        """
    )
    return con


def reply(obj, status=200):
    return Response(json.dumps(obj), status=status, mimetype="application/json")


@relay.after_request
def cors(resp):
    # the game page may be served from another site (e.g. embedded on Wix)
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Cache-Control"] = "no-store"
    return resp


def body():
    raw = request.get_data(cache=False, as_text=True) or "{}"
    if len(raw) > MAX_BODY:
        raise ValueError("too big")
    return json.loads(raw)


def who(con, code, token):
    row = con.execute("SELECT pid FROM players WHERE code=? AND token=?", (code, token)).fetchone()
    if row:
        con.execute("UPDATE players SET last_seen=? WHERE code=? AND pid=?", (time.time(), code, row[0]))
    return row[0] if row else None


def cleanup(con):
    old = time.time() - ROOM_TTL
    codes = [r[0] for r in con.execute("SELECT code FROM rooms WHERE created < ?", (old,))]
    for c in codes:
        for t in ("rooms", "players", "msgs", "states"):
            con.execute("DELETE FROM %s WHERE code=?" % t, (c,))
    con.execute("DELETE FROM msgs WHERE ts < ?", (time.time() - 3600,))


@relay.route("/<path:_any>", methods=["OPTIONS"])
def options(_any):
    return reply({})


@relay.route("/create", methods=["POST"])
def create():
    b = body()
    con = db()
    with con:
        cleanup(con)
        for _ in range(20):
            code = "".join(random.choice(CODE_CHARS) for _ in range(4))
            if not con.execute("SELECT 1 FROM rooms WHERE code=?", (code,)).fetchone():
                break
        token = secrets.token_hex(12)
        con.execute("INSERT INTO rooms VALUES (?, ?)", (code, time.time()))
        con.execute("INSERT INTO players VALUES (?, 0, ?, ?, ?)", (code, token, str(b.get("name", ""))[:20], time.time()))
    return reply({"code": code, "token": token, "pid": 0})


@relay.route("/join", methods=["POST"])
def join():
    b = body()
    code = str(b.get("code", "")).upper().strip()
    con = db()
    with con:
        if not con.execute("SELECT 1 FROM rooms WHERE code=?", (code,)).fetchone():
            return reply({"error": "noroom"}, 404)
        tok = b.get("token")
        if tok:   # rejoin after a reload
            pid = who(con, code, tok)
            if pid is not None:
                con.execute("INSERT INTO msgs (code, to_pid, from_pid, body, ts) VALUES (?, 0, ?, ?, ?)",
                            (code, pid, json.dumps({"t": "rejoin"}), time.time()))
                return reply({"code": code, "token": tok, "pid": pid})
        taken = [r[0] for r in con.execute("SELECT pid FROM players WHERE code=?", (code,))]
        free = [p for p in range(1, MAX_GUESTS + 1) if p not in taken]
        if not free:
            return reply({"error": "full"}, 409)
        pid, token, name = free[0], secrets.token_hex(12), str(b.get("name", ""))[:20]
        con.execute("INSERT INTO players VALUES (?, ?, ?, ?, ?)", (code, pid, token, name, time.time()))
        con.execute("INSERT INTO msgs (code, to_pid, from_pid, body, ts) VALUES (?, 0, ?, ?, ?)",
                    (code, pid, json.dumps({"t": "join", "name": name}), time.time()))
    return reply({"code": code, "token": token, "pid": pid})


@relay.route("/send", methods=["POST"])
def send():
    """msgs: [{to: pid, body}] queued in order; states: {pid: body} replace that player's view (host only)."""
    b = body()
    code = str(b.get("code", "")).upper()
    con = db()
    with con:
        pid = who(con, code, b.get("token"))
        if pid is None:
            return reply({"error": "auth"}, 403)
        now = time.time()
        for m in b.get("msgs", [])[:50]:
            to = 0 if pid != 0 else int(m.get("to", 0))   # guests can only write to the host
            con.execute("INSERT INTO msgs (code, to_pid, from_pid, body, ts) VALUES (?, ?, ?, ?, ?)",
                        (code, to, pid, json.dumps(m.get("body")), now))
        if pid == 0:
            for k, v in (b.get("states") or {}).items():
                row = con.execute("SELECT v FROM states WHERE code=? AND pid=?", (code, int(k))).fetchone()
                ver = (row[0] if row else 0) + 1
                con.execute("INSERT OR REPLACE INTO states VALUES (?, ?, ?, ?)", (code, int(k), ver, json.dumps(v)))
    return reply({"ok": True})


@relay.route("/poll", methods=["GET"])
def poll():
    code = request.args.get("code", "").upper()
    con = db()
    with con:
        pid = who(con, code, request.args.get("token"))
        if pid is None:
            return reply({"error": "auth"}, 403)
        after = int(request.args.get("after", 0) or 0)
        rows = con.execute("SELECT id, from_pid, body FROM msgs WHERE code=? AND to_pid=? AND id>? ORDER BY id LIMIT 200",
                           (code, pid, after)).fetchall()
        out = {"msgs": [{"seq": r[0], "from": r[1], "body": json.loads(r[2])} for r in rows]}
        v = int(request.args.get("v", 0) or 0)
        st = con.execute("SELECT v, body FROM states WHERE code=? AND pid=?", (code, pid)).fetchone()
        if st and st[0] > v:
            out["state"] = {"v": st[0], "body": json.loads(st[1])}
        if pid == 0:
            now = time.time()
            out["peers"] = {str(r[0]): {"name": r[1], "age": round(now - r[2], 1)}
                            for r in con.execute("SELECT pid, name, last_seen FROM players WHERE code=? AND pid>0", (code,))}
    return reply(out)


# ---------------------------------------------------------------------------
# Daily board
# ---------------------------------------------------------------------------
def board_name(raw):
    """A typed name, trimmed to something safe to show: no control characters, 20 long at most."""
    name = "".join(ch for ch in str(raw or "") if unicodedata.category(ch)[0] != "C")
    return " ".join(name.split())[:20]


def board_rows(con, game, day):
    rows = con.execute("SELECT name, score, won, steals FROM board WHERE game=? AND day=? "
                       "ORDER BY score DESC, ts ASC LIMIT 50", (game, day)).fetchall()
    return [{"name": r[0], "score": r[1], "won": bool(r[2]), "steals": r[3]} for r in rows]


def board_day_ok(day):
    """Days are counted on each phone's own calendar, so allow one either side of the server's."""
    today = int((time.time() - BOARD_DAY_ZERO) // 86400)
    return abs(day - today) <= 1


@relay.route("/board/top", methods=["GET"])
def board_top():
    game = request.args.get("g", "")
    try:
        day = int(request.args.get("day", ""))
    except ValueError:
        return reply({"error": "day"}, 400)
    if game not in BOARD_GAMES:
        return reply({"error": "game"}, 400)
    con = db()
    with con:
        return reply({"game": game, "day": day, "rows": board_rows(con, game, day)})


@relay.route("/board/post", methods=["POST"])
def board_post():
    try:
        b = body()
        game, day, score = str(b.get("g", "")), int(b.get("day")), int(b.get("score"))
        steals = max(0, min(99, int(b.get("steals", 0) or 0)))
    except (TypeError, ValueError):
        return reply({"error": "bad"}, 400)
    name = board_name(b.get("name"))
    if game not in BOARD_GAMES or not name:
        return reply({"error": "bad"}, 400)
    if not board_day_ok(day):
        return reply({"error": "day"}, 400)
    if not 0 <= score <= BOARD_GAMES[game]:
        return reply({"error": "score"}, 400)
    key = unicodedata.normalize("NFKC", name).casefold()
    con = db()
    with con:
        kept = con.execute("SELECT score FROM board WHERE game=? AND day=? AND key=?", (game, day, key)).fetchone()
        if kept is None:
            count = con.execute("SELECT COUNT(*) FROM board WHERE game=? AND day=?", (game, day)).fetchone()[0]
            if count >= BOARD_MAX_ROWS:
                return reply({"error": "full"}, 409)
            con.execute("INSERT INTO board VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (game, day, key, name, score, 1 if b.get("won") else 0, steals, time.time()))
        return reply({"game": game, "day": day, "name": name, "new": kept is None,
                      "score": score if kept is None else kept[0], "rows": board_rows(con, game, day)})


if __name__ == "__main__":   # local test: python shengji_relay.py
    from flask import Flask
    app = Flask(__name__)
    app.register_blueprint(relay)
    app.run(port=int(os.environ.get("PORT", 5055)), threaded=True)
