from dungen import Encounter, FloorData, DungenSave, StampInfo

import time
from pathlib import Path
from typing import Optional, Tuple
from uuid import UUID
from flask import Flask, Response, abort, jsonify, render_template, request, send_file
from .dungeons import DungenList
from .stamps import StampRepository
from .maps import render_as_map

app = Flask(__name__)

def check_get_floor(dungeon: str, lvid: int, floorid: int) -> Tuple[DungenSave, FloorData]:
    """Returns the specified floor, aborting if any pat of the path does not
    exist."""
    start = time.time()
    d = app.config["DUNGEONS"][dungeon]
    if d is None:
        abort(404)
    f = d.get_floor(lvid, floorid)
    if f is None:
        abort(404)
    end = time.time()
    if end - start > app.config["WARN_SECS"]:
        app.logger.warn(f"Opening level {lvid} floor {floorid} in '{dungeon}' took {end - start} seconds.")
    return d, f

@app.route("/")
def dungeon_index():
    return render_template(
        "index.html",
        dungeons = app.config["DUNGEONS"].names,
    )

@app.route("/<dungeon>")
def level_index(dungeon: str):
    d = app.config["DUNGEONS"][dungeon]
    if d is None:
        abort(404)
    return render_template(
        "level_index.html",
        dungen_name = dungeon,
        levels = range(1, d.levels + 1),
        floors = { i: d.floor_count(i) for i in range(1, d.levels + 1) },
        notes = d.get_level_notes(),
    )

@app.route("/<dungeon>/level/<int:lvid>/<int:floorid>")
def level_screen(dungeon: str, lvid: int, floorid: int):
    d, f = check_get_floor(dungeon, lvid, floorid)
    return render_template(
        "level_editor.html",
        dungen_name = dungeon,
        lvid = lvid,
        floorid = floorid,
        floors = d.floor_count(lvid),
        scale = d.scale,
        img = f.img,
        book_url = app.config["BOOKS_URL"] if app.config["BOOKS_URL"] else "",
    )

@app.route("/<dungeon>/encounter/<int:lvid>/<int:floorid>/<roomId>")
def encounter_screen(dungeon: str, lvid: int, floorid: int, roomId: str):
    d, f = check_get_floor(dungeon, lvid, floorid)
    uid = UUID(roomId)
    if f is None:
        abort(404)
    def book_link(book:str, page: int) -> str:
        if app.config["BOOKS_URL"]:
            return app.config["BOOKS_URL"].replace("$b", book).replace("$p", str(page))
        return "#"
    return render_template(
        "encounter_screen.html",
        room = f[uid],
        roomId = uid,
        createBookLink = book_link,
    )

@app.route("/<dungeon>/map/<int:lvid>/<int:floorid>")
def map_screen(dungeon: str, lvid: int, floorid: int):
    d, f = check_get_floor(dungeon, lvid, floorid)
    return render_template(
        "map_screen.html",
        lvid = lvid,
        floorid = floorid,
        dungen_name = dungeon,
        floors = d.floor_count(lvid),
        scale = d.scale,
        img = f.img,
    )

@app.route("/<dungeon>/export/<int:lvid>/<int:floorid>")
def map_export(dungeon: str, lvid: int, floorid: int):
    d, f = check_get_floor(dungeon, lvid, floorid)
    return Response(render_as_map(f.img, d.scale), mimetype="image/svg+xml")

@app.route("/svg/<dungeon>/<int:lvid>/<int:floorid>")
def raw_svg(dungeon: str, lvid: int, floorid: int):
    _, f = check_get_floor(dungeon, lvid, floorid)
    return Response(str(f.img), mimetype="image/svg+xml")

@app.route("/stamps/<path:path>")
def get_stamp(path):
    stamp_file = app.config["STAMP_REPO"].get_stamp(path)
    if stamp_file is None:
        abort(404)
        return None
    return send_file(stamp_file)

def stamp_response(stamps: StampRepository):
    ret = {
        "parent": stamps.parent,
        "stamps": [s.to_dict() for s in stamps.stamps],
        "dirs": [n.relative_path for n in stamps.dirs],
    }
    return jsonify(ret)

@app.route("/api/stamprepo")
def get_stamps_root():
    stamps = app.config["STAMP_REPO"]
    results = None
    key = request.args.get("q", None)
    if key:
        start = time.time()
        results = stamps.search_stamps(key)
        end = time.time()
        if end - start > app.config["WARN_SECS"]:
            app.logger.warn(f"Searching for stamps with termp '{key}' took {end - start} seconds.")
    if results is not None:
        return jsonify({
            "parent": "",
            "stamps": [s.to_dict() for s in results],
            "dirs": [],
        });
    return stamp_response(stamps)

@app.route("/api/stamprepo/<path:path>")
def get_stamps(path):
    stamps = app.config["STAMP_REPO"].get_stamps(path)
    if stamps is None:
        abort(404)
        return None
    return stamp_response(stamps)

@app.route("/api/save/<dungeon>", methods=["GET", "POST"])
def update_dungeon(dungeon: str):
    if request.json is None:
        abort(400)
    d = app.config["DUNGEONS"][dungeon]
    if d is None:
        abort(404)
    start = time.time()
    for lvl, text in request.json.get("levels", {}).items():
        d.set_level_note(int(lvl), text)
    end = time.time()
    if end - start > app.config["WARN_SECS"]:
        app.logger.warn(f"Saving level notes in '{dungeon}' took {end - start} seconds.")
    return "OK"

@app.route("/api/save/<dungeon>/<int:lvid>/<int:floorid>", methods=["POST"])
def update_floor(dungeon: str, lvid: int, floorid: int):
    if request.json is None:
        abort(400)
    d, f = check_get_floor(dungeon, lvid, floorid)
    for rid, info in request.json.get("rooms", {}).items():
        roomId = UUID(rid)
        info["encounter"] = Encounter.from_dict(info["encounter"])
        f[roomId] = info
    start = time.time()
    f.set_stamps([StampInfo(**s) for s in request.json.get("stamps", [])])
    d.set_floor(lvid, floorid, f)
    end = time.time()
    if end - start > app.config["WARN_SECS"]:
        app.logger.warn(f"Saving level {lvid} floor {floorid} in '{dungeon}' took {end - start} seconds.")
    return "OK"

def set_app_config(
    dungen_files: Path,
    stamps_path: str,
    books_url: Optional[str] = None,
    warn_duration: float = 1.0,
) -> Optional[Flask]:
    """Return the DMScreen app with parameters set."""
    app.config["DUNGEONS"] = DungenList(dungen_files)

    start = time.time()
    app.config["STAMP_REPO"] = StampRepository.from_path(stamps_path)
    end = time.time()
    if end - start > warn_duration:
        app.logger.warn(f"Startup took {end - start} seconds.")
    else:
        app.logger.info(f"Startup took {end - start} seconds.")

    app.config["BOOKS_URL"] = books_url
    app.config["WARN_SECS"] = warn_duration
    return app

def main_func():
    import argparse
    import logging
    parser = argparse.ArgumentParser(description="DMscreen: View, edit, and run games for a dungeon.")
    parser.add_argument(
        "dungens_path",
        type = Path,
        help = "Path to Dungen save files.",
    )
    parser.add_argument(
        "stamps_path",
        type = Path,
        help = "Relative path to stamps directory.",
    )
    parser.add_argument(
        "--books-url",
        type = str,
        help = "Url pattern for source books. Will replace $b with book name and $p with page.",
        default = None,
    )
    parser.add_argument(
        "--warn-duration",
        type = int,
        help = "Log a warning if operation takes longer than thiw many seconds.",
        default = 1,
    )
    parser.add_argument(
        "--port",
        type = int,
        help = "Port to run local server on",
        default = 8080,
    )
    args = parser.parse_args()

    app.logger.setLevel(logging.DEBUG)
    set_app_config(args.dungens_path, args.stamps_path, args.books_url, args.warn_duration)
    app.run(port = args.port)

if __name__ == "__main__":
    main_func()
