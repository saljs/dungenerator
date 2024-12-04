const svgStyles = {
    "highlight_monsters": ".monsters { stroke: magenta; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_traps": ".trap { stroke: yellow; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_shops": ".shop { stroke: orange; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_treasure": ".treasure { stroke: chartreuse; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_stairs_up": ".up { stroke: royalblue; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_stairs_down": ".down { stroke: coral; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
};
const cachedInfo = {};
const encounter_endpoint = window.location.href.replace("level", "encounter");

function addStyletoSVG(id, style) {
    const svg = document.querySelector(".map svg");
    const defs = svg.querySelector("defs");
    const styleEl = document.createElement("style");

    styleEl.innerText = style.replace("$$", 
        parseInt(svg.parentElement.dataset.scale) * 4);
    styleEl.id = id;
    defs.appendChild(styleEl);
}

function removeStylefromSVG(id) {
    const el = document.getElementById(id);
    if (el != null) el.remove();
}

function setEncounterItems(encounter) {
    const items = document.getElementById("encounter_items");
    items.replaceChildren();
    const keys = ["name", "initiative", "hp", "xp", "book", "book_page"];
    encounter.items.forEach((row) => {
        const newRow = items.insertRow();
        keys.forEach((key) => {
            let cell = newRow.insertCell();
            cell.innerText = row[key];
        });
        let last_cell = newRow.insertCell();
        let rm_btn = document.createElement("button");
        rm_btn.innerText = "Remove";
        rm_btn.onclick = () => {
            encounter.items = encounter.items.filter((i) => i !== row);
            setEncounterItems(encounter);
        };
        last_cell.appendChild(rm_btn);
    });
}

function addEncounter(items) {
    const encounter = {};
    for (const pair of items) {
        encounter[pair[0]] = pair[1];
    }
    const tb = syncRoomText();
    if ("currentRoom" in tb.dataset) {
        cachedInfo[tb.dataset.currentRoom].encounter.items.push(encounter);
        setEncounterItems(cachedInfo[tb.dataset.currentRoom].encounter);
    }
}

function updateRoomInfo(id) {
    if (id in cachedInfo) {
        return Promise.resolve(cachedInfo[id]);
    }
    const apiUrl = "/api/"
        + document.querySelector("body").dataset.dungeon
        + "/room/" + id;
    return fetch(apiUrl).then((r) => r.json()).then((info) => {
        cachedInfo[id] = info;
        return info;
    });
}

function syncRoomText() {
    const tb = document.getElementById("room_info");
    if ("currentRoom" in tb.dataset) {
        cachedInfo[tb.dataset.currentRoom].notes = tb.innerText;
    }
    document.getElementById("save_btn").classList.remove("success");
    return tb;
}

function selectRoom(id) {
    const uid = id.slice(5);
    removeStylefromSVG("selected-room");
    addStyletoSVG("selected-room",
        "#" + id + "{ stroke: aqua; stroke-width: $$px; }");
    const tb = syncRoomText();
    tb.dataset.currentRoom = uid;
    tb.contentEditable = true;
    document.querySelectorAll("#encounter form input").forEach((input) => {
        input.disabled = false;
    });
    document.getElementById("encounter_link").href = "/"
        + document.querySelector("body").dataset.dungeon
        + "/encounter/" + uid;
    updateRoomInfo(uid).then((info) => {
        tb.innerText = info.notes;
        setEncounterItems(info.encounter);
    });
}

function deselectRoom() {
    removeStylefromSVG("selected-room");
    const tb = syncRoomText();
    tb.innerText = "";
    tb.contentEditable = false;
    delete tb.dataset.currentRoom;
    document.querySelectorAll("#encounter form input").forEach((input) => {
        input.disabled = true;
    });
    document.getElementById("encounter_items").replaceChildren();
    document.getElementById("encounter_link").href = "#";
}

function toggleStyle(className, btn) {
    if (btn.classList.contains("selected")) {
        // Remove style
        btn.classList.remove("selected");
        removeStylefromSVG(className);
    }
    else {
        // Add style
        btn.classList.add("selected");
        addStyletoSVG(className, svgStyles[className]);
    }
}

function saveRooms() {
    syncRoomText();
    fetch("/api/save/" + document.querySelector("body").dataset.dungeon + "/rooms", {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify(cachedInfo),
    });
}

function getStampAngle(stamp) {
    const transform = stamp.transform.animVal;
    if (transform.numberOfItems === 0) {
        return 0;
    }
    return transform.getItem(0).angle;
}

function moveStamp(x, y) {
    const stampPointer = document.getElementById("stamp_preview");
    if (stampPointer !== null) {
        const angle = getStampAngle(stampPointer);
        const width = stampPointer.width.animVal.value;
        const height = stampPointer.height.animVal.value;
        stampPointer.setAttributeNS(null, "x", x);
        stampPointer.setAttributeNS(null, "y", y);
        stampPointer.setAttributeNS(null, "transform",
            `rotate(${angle}, ${x + (width / 2)}, ${y + (height / 2)})`);
    }
}

function dropStamp() {
    const svg = document.querySelector(".map svg");
    const svg_stamps = document.getElementById("stamps");
    const stampPointer = document.getElementById("stamp_preview");
    if (stampPointer) {
        const stamp = document.createElementNS(svg.namespaceURI, "image");
        const angle = getStampAngle(stampPointer);
        const x = stampPointer.x.animVal.value;
        const y = stampPointer.y.animVal.value;
        const width = stampPointer.width.animVal.value;
        const height = stampPointer.height.animVal.value;
        stamp.setAttributeNS(null, "x", x);
        stamp.setAttributeNS(null, "y", y);
        stamp.setAttributeNS(null, "width", width);
        stamp.setAttributeNS(null, "height", height);
        stamp.setAttributeNS(null, "href", stampPointer.href.animVal);
        stamp.setAttributeNS(null, "transform",
            `rotate(${angle}, ${x + (width / 2)}, ${y + (height / 2)})`);
        stamp.onclick = (ev) => { 
            if (ev.shiftKey) {
                stamp.remove();
            }
        };
        svg_stamps.appendChild(stamp);
        document.getElementById("save_btn").classList.remove("success");
    }
}

function rotateStamp() {
    const stampPointer = document.getElementById("stamp_preview");
    if (stampPointer) {
        const angle = (getStampAngle(stampPointer) + 45) % 360;
        const x = stampPointer.x.animVal.value;
        const y = stampPointer.y.animVal.value;
        const width = stampPointer.width.animVal.value;
        const height = stampPointer.height.animVal.value;
        stampPointer.setAttributeNS(null, "transform",
            `rotate(${angle}, ${x + (width / 2)}, ${y + (height / 2)})`);
    }
}

function selectStamp(stamp) {
    const svg = document.querySelector(".map svg g");
    const prev_stamp = document.getElementById("stamp_preview");
    const stampPointer = document.createElementNS(svg.namespaceURI, "image");
    stampPointer.setAttributeNS(null, "x", 0);
    stampPointer.setAttributeNS(null, "y", 0);
    stampPointer.setAttributeNS(null, "width", stamp.width);
    stampPointer.setAttributeNS(null, "height", stamp.height);
    stampPointer.setAttributeNS(null, "href", "/stamps/" + stamp.href);
    stampPointer.setAttributeNS(null, "opacity", 0.3);
    stampPointer.setAttributeNS(null, "id", "stamp_preview");
    if (prev_stamp) {
        prev_stamp.remove();
    }
    svg.appendChild(stampPointer);
}

function saveStamps() {
    const stamps = document.getElementById("stamps");
    const lvid = parseInt(document.querySelector(".map").dataset.lvid);
    const objs = [];
    stamps.childNodes.forEach((el) => {
        const angle = getStampAngle(el);
        const x = el.x.animVal.value;
        const y = el.y.animVal.value;
        const width = el.width.animVal.value;
        const height = el.height.animVal.value;
        const href = el.href.animVal;
        objs.push({
            x: x, y: y,
            width: width, height: height,
            href: href, angle: angle,
        });
    });
    fetch("/api/save/" + document.querySelector("body").dataset.dungeon + "/stamps", {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            "lvid": lvid,
            "stamps": objs,
        }),
    });
}

function showStamps(path) {
    const stamp_list = document.getElementById("stamp-list");
    let apiURL = "/api/stamprepo";
    if (path) {
        apiURL += "/" + path;
    }
    fetch(apiURL)
        .then((r) => r.json())
        .then((sr) => {
            children = []
            if (sr.parent !== null) {
                const parentDir = document.createElement("div");
                const link = document.createElement("a");
                parentDir.classList.add("stamp");
                parentDir.classList.add("stamp-folder");
                link.onclick = () => showStamps(sr.parent);
                link.innerText = "up a level";
                parentDir.appendChild(link);
                children.push(parentDir);
            }
            stamp_list.replaceChildren(...children.concat(
                sr.dirs.map((dir) => {
                    const dirEl = document.createElement("div");
                    const link = document.createElement("a");
                    link.onclick = () => showStamps(dir);
                    link.innerText = dir;
                    dirEl.appendChild(link);
                    dirEl.classList.add("stamp");
                    dirEl.classList.add("stamp-folder");
                    return dirEl;
                }),
                sr.stamps.map((stamp) => {
                    const dirEl = document.createElement("div");
                    const link = document.createElement("a");
                    const img = document.createElement("img");
                    link.innerText = stamp.name;
                    link.dataset.width = stamp.width;
                    link.dataset.height = stamp.height;
                    link.onclick = () => selectStamp(stamp);
                    img.src = "/stamps/" + stamp.href;
                    link.appendChild(img);
                    dirEl.appendChild(link);
                    dirEl.classList.add("stamp");
                    return dirEl;
                })
            ));
        });

    const tb = syncRoomText();
    tb.parentElement.style.display = "none";
    stamp_list.style.display = "block";
}

document.addEventListener("DOMContentLoaded", function() {
    // Add click handler to rooms
    document.querySelectorAll(".map .room").forEach((rm) => {
        rm.onclick = () => { selectRoom(rm.id); };
    });
    document.getElementById("background").onclick = deselectRoom;
    document.querySelectorAll(".map .hall").forEach((hall) => {
        hall.onclick = deselectRoom;
    });

    // Add click handlers to buttons
    document.getElementById("show_monsters_btn").onclick =
        (e) => { toggleStyle("highlight_monsters", e.srcElement); };
    document.getElementById("show_traps_btn").onclick =
        (e) => { toggleStyle("highlight_traps", e.srcElement); };
    document.getElementById("show_shops_btn").onclick =
        (e) => { toggleStyle("highlight_shops", e.srcElement); };
    document.getElementById("show_treasure_btn").onclick =
        (e) => { toggleStyle("highlight_treasure", e.srcElement); };
    document.getElementById("show_stairs_up").onclick =
        (e) => { toggleStyle("highlight_stairs_up", e.srcElement); };
    document.getElementById("show_stairs_down").onclick =
        (e) => { toggleStyle("highlight_stairs_down", e.srcElement); };

    // Add stamp interactions
    document.getElementById("add_stamp_btn").onclick = (ev) => {
        if (ev.srcElement.classList.contains("selected")) {
            const tb = document.getElementById("room_info");
            const stamp_list = document.getElementById("stamp-list");
            const prev_stamp = document.getElementById("stamp_preview");
            tb.parentElement.style.display = "flex";
            stamp_list.style.display = "none";
            ev.srcElement.classList.remove("selected");
            if (prev_stamp) {
                prev_stamp.remove();
            }
        }
        else {
            ev.srcElement.classList.add("selected");
            showStamps("");
        }
    };
    document.addEventListener("keydown", (ev) => {
        if (ev.key === 'r') {
            rotateStamp();
        }
    });
    document.querySelectorAll("#stamps image").forEach((stamp) => {
        stamp.onclick = (ev) => { 
            if (ev.shiftKey) {
                stamp.remove();
            }
        };
    });
    const stampMoveHandler = (x, y, ev) => {
        moveStamp(x, y);
    };
    const stampPlaceHandler = (x, y, ev) => {
        ev.preventDefault();
        dropStamp();
    };

    // Add click-to-drag handler to map
    const svg = new SVGView(null, stampPlaceHandler, stampMoveHandler);
    document.getElementById("zoom_to_fit_btn").onclick = () => {
        svg.zoomToExtents();
    };

    // Add encounter add handler
    document.querySelector("#encounter form")
        .addEventListener("submit", (ev) => {
        ev.preventDefault();
        const data = new FormData(ev.target);
        addEncounter(data.entries());
    });


    // Add handlers for save
    const save_btn = document.getElementById("save_btn");
    save_btn.onclick = () => {
        saveRooms();
        saveStamps();
        document.getElementById("save_btn").classList.add("success");
    };
    window.addEventListener("beforeunload", (e) => {
        if (save_btn.classList.contains("success")) {
            return true;
        }
        e.preventDefault();
        return false;
    });
});
