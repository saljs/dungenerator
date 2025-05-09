from dungen import Encounter

import time
from pathlib import Path
from typing import Optional
from uuid import UUID
from flask import Flask, Response, abort, jsonify, render_template, request, send_file
from .dungeons import DungenList
from .stamps import StampInfo, StampRepository, set_stamps
from .maps import render_as_map

app = Flask(__name__)

@app.route("/")
def dungeon_index():
    return render_template(
        "index.html",
        dungeons = app.config["DUNGEONS"].names,
    )

@app.route("/<dungeon>")
def level_index(dungeon: str):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    return render_template(
        "level_index.html",
        dungen_name = dungeon,
        dungeon = d,
        len = len,
    )

@app.route("/<dungeon>/level/<int:lvid>/<int:floorid>")
def level_screen(dungeon: str, lvid: int, floorid: int):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    return render_template(
        "level_screen.html",
        dungeon = d,
        dungen_name = dungeon,
        lvid = lvid,
        floorid = floorid,
        book_url = app.config["BOOKS_URL"] if app.config["BOOKS_URL"] else "",
    )

@app.route("/<dungeon>/encounter/<roomId>")
def encounter_screen(dungeon: str, roomId: str):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    def book_link(book:str, page: int) -> str:
        if app.config["BOOKS_URL"]:
            return app.config["BOOKS_URL"].replace("$b", book).replace("$p", str(page))
        return "#"
    return render_template(
        "encounter_screen.html",
        dungeon = d,
        roomId = UUID(roomId),
        createBookLink = book_link,
    )

@app.route("/<dungeon>/map/<int:lvid>/<int:floorid>")
def map_screen(dungeon: str, lvid: int, floorid: int):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    return render_template(
        "map_screen.html",
        lvid = lvid,
        floorid = floorid,
        dungen_name = dungeon,
        dungeon = d,
    )

@app.route("/<dungeon>/export/<int:lvid>/<int:floorid>")
def map_export(dungeon: str, lvid: int, floorid: int):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    return Response(render_as_map(d.images[lvid][floorid], d.scale), mimetype="image/svg+xml")

@app.route("/svg/<dungeon>/<int:lvid>/<int:floorid>")
def raw_svg(dungeon: str, lvid: int, floorid: int):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    return Response(str(d.images[lvid][floorid]), mimetype="image/svg+xml")

@app.route("/stamps/<path:path>")
def get_stamp(path):
    stamp_file = app.config["STAMP_REPO"].get_stamp(path)
    if stamp_file is None:
        abort(404)
        return None
    return send_file(stamp_file)

@app.route("/api/<dungeon>/room/<roomId>")
def room_notes(dungeon: str, roomId: str):
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    return jsonify({
        "notes": d.room_notes[UUID(roomId)],
        "encounter": d.room_encounters[UUID(roomId)],
    })

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
        results = stamps.search_stamps(key)
    dungeon = request.args.get("dungeon", None)
    if dungeon:
        lvid = request.args.get("lvid", None)
        floorid = request.args.get("floorid", None)
        if lvid is None or floorid is None:
            abort(400, "Error: lvid and floorid are required parameters.")
        d = app.config["DUNGEONS"].get(dungeon)
        results = stamps.in_svg(d.images[int(lvid)][int(floorid)])
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
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    if request.method == "POST" and request.json is not None:
        for lvl, text in request.json.get("levels", {}).items():
            d.level_notes[int(lvl)] = text
    if app.config["DUNGEONS"].save(dungeon):
        return "OK"
    abort(500)

@app.route("/api/save/<dungeon>/rooms", methods=["POST"])
def update_rooms(dungeon: str):
    if request.json is None:
        abort(400)
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    for rid, info in request.json.items():
        roomId = UUID(rid)
        d.room_notes[roomId] = info["notes"]
        d.room_encounters[roomId] = Encounter.from_dict(info["encounter"])
    return "OK"

@app.route("/api/save/<dungeon>/stamps", methods=["POST"])
def update_stamps(dungeon: str):
    if request.json is None:
        abort(400)
    d = app.config["DUNGEONS"].get(dungeon)
    if d is None:
        abort(404)
    lvid = request.json.get("lvid")
    floorid = request.json.get("floorid")
    stamps = [StampInfo(**s) for s in request.json.get("stamps", [])]
    set_stamps(stamps, d.images[lvid][floorid])
    return "OK"

def set_app_config(dungen_files: Path, stamps_path: str, books_url: Optional[str] = None) -> Optional[Flask]:
    app.config["DUNGEONS"] = DungenList(dungen_files, app.logger)

    start = time.time()
    app.config["STAMP_REPO"] = StampRepository.from_path(stamps_path)
    end = time.time()
    if end - start > 1:
        app.logger.warn(f"Startup took {end - start} seconds.")
    else:
        app.logger.info(f"Startup took {end - start} seconds.")

    app.config["BOOKS_URL"] = books_url
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
        "--port",
        type = int,
        help = "Port to run local server on",
        default = 8080,
    )
    args = parser.parse_args()

    app.logger.setLevel(logging.DEBUG)
    set_app_config(args.dungens_path, args.stamps_path, args.books_url)
    app.run(port = args.port)

if __name__ == "__main__":
    main_func()
