/*
 * Constant data
 */

const svgStyles = {
    "highlight_monsters": "#rooms .monsters { stroke: magenta; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_traps": "#rooms .trap { stroke: yellow; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_shops": "#rooms .shop { stroke: orange; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_treasure": "#rooms .treasure { stroke: chartreuse; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_stairs_up": "#rooms .up { stroke: red; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
    "highlight_stairs_down": "#rooms .down { stroke: coral; stroke-width: $$px; animation: blinker 0.5s linear infinite; }",
};

const roomAttributes = ["monsters", "treasure", "trap", "shop"];


/*
 * Utility functions
 */

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

function markPageDirty() {
    document.getElementById("save_btn").classList.remove("success");
}

function markPageClean() {
    document.getElementById("save_btn").classList.add("success");
}

function isPageDirty() {
    return !document.getElementById("save_btn").classList.contains("success");
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


/*
 * Mode objects
 */

const notesMode = {
    name: "Notepad",
    abortController: new AbortController(),
    eventHandlerSignal: null,

    oneTimeSetup: function() {
        const mode = this;
        this.eventHandlerSignal = this.abortController.signal;
        document.getElementById("room_info").addEventListener("input", () => {
            mode.syncRoom();
        });
        // Create attribute checkboxes
        const attrForm = document.querySelector("#room_attrs form");
        attrForm.replaceChildren(...roomAttributes.map((attr) => {
            const opt = document.createElement("label");
            const input = document.createElement("input");
            input.type = "checkbox";
            input.name = attr;
            input.value = true;
            opt.innerText = attr;
            opt.appendChild(input);
            input.addEventListener("change", () => {
                mode.syncRoom();
            });
            return opt;
        }));
        // Add encounter add handler
        document.querySelector("#encounter form").addEventListener("submit", (ev) => {
            ev.preventDefault();
            const data = new FormData(ev.target);
            mode.addEncounter(data.entries());
        });
    },
    setup: function() {
        const mode = this;
        document.getElementById("bg-elements").addEventListener("click", () => {
            mode.deselectRoom();
        }, { signal: mode.eventHandlerSignal });
        document.querySelectorAll(".map .hall").forEach((rm) => {
            rm.addEventListener("click", () => {
                mode.deselectRoom();
            });
        }, { signal: mode.eventHandlerSignal });
        document.querySelectorAll(".map .room").forEach((rm) => {
            rm.addEventListener("click", (ev) => {
                mode.selectRoom(rm.id.slice(5));
                ev.preventDefault();
            }, { signal: mode.eventHandlerSignal });
        });
        this.deselectRoom();
        document.getElementById("notes-mode").style.display = "flex";
    },
    teardown: function() {
        this.deselectRoom();
        this.abortController.abort();
        this.abortController = new AbortController();
        this.eventHandlerSignal = this.abortController.signal;
        document.getElementById("notes-mode").style.display = "none";
    },
    leftClick: null,
    rightClick: null,
    mouseMove: null,
    keyDown: null,
    keyUp: null,
    shortcuts: null,
    saveData: function() {
        this.syncRoom();
        const data = Object.fromEntries(
            this.modifiedRooms.entries().map((o) => {
                const uid = o[0];
                const room = o[1];
                return [
                    uid,
                    {
                        encounter: room.encounter,
                        notes: room.notes,
                        attributes: room.attributes
                    }
                ];
            })
        );
        this.modifiedRooms.clear();
        return data;
    },
    /*
     * Mode functions
     */
    currentRoom: null,
    modifiedRooms: new Map(),
    selectRoom: function(uid) {
        const tb = document.getElementById("room_info");
        const room = document.getElementById("room-" + uid);
        const books_url = document.querySelector("body").dataset.bookurl;
        const dungeon = document.querySelector("body").dataset.dungeon;
        const levelId = document.querySelector(".map").dataset.lvid;
        const floorId = document.querySelector(".map").dataset.floorid;

        this.deselectRoom();
        addStyletoSVG("selected-room",
            "#room-" + uid + "{ stroke: aqua; stroke-width: $$px; }");
        window.location.hash = uid;

        tb.contentEditable = "plaintext-only";
        document.querySelectorAll("form input").forEach((input) => {
            input.disabled = false;
        });
        document.getElementById("encounter_link").href =
            `/${dungeon}/encounter/${levelId}/${floorId}/${uid}`;

        let noteStr = decodeURIComponent(room.dataset.roomNote).trim().replaceAll(/\n/g, "<br>")
            .replaceAll(/(https?:\/\/[^ ]*)/ig,
                '<a href="$&" onmousedown="window.open(this.href, \'_blank\').focus()">$&</a>');
        if (books_url) {
            noteStr = noteStr.replaceAll(/([A-Za-z0-9]{3,5})pg(\d+)/g, 
                (match, book, page) => '<a href="'
                    + books_url.replace("$b", book.toLowerCase()).replace("$p", page)
                    + '" onmousedown="window.open(this.href, \'_blank\').focus()"'
                    + '>' + match + "</a>");
        }

        const attrBoxes = document.querySelectorAll("#room_attrs form input[type='checkbox']");
        attrBoxes.forEach((attr) => {
            attr.checked = room.classList.contains(attr.name);
        });
        tb.innerHTML = noteStr;
        this.currentRoom = {
            uid: uid,
            element: room,
            encounter: JSON.parse(decodeURIComponent(room.dataset.roomEncounter)),
            attributes: roomAttributes.filter((attr) => room.classList.contains(attr)),
            notes: decodeURIComponent(room.dataset.roomNote).trim()
        };
        this.setEncounterItems(this.currentRoom.encounter);
    },
    deselectRoom: function() {
        this.syncRoom();
        removeStylefromSVG("selected-room");
        const tb = document.getElementById("room_info");
        tb.innerText = "";
        tb.contentEditable = false;
        window.location.hash = "";
        document.querySelectorAll("#notes-mode form input").forEach((input) => {
            input.disabled = true;
        });
        document.getElementById("encounter_items").replaceChildren();
        document.getElementById("encounter_link").href = "#";
        const attrBoxes = document.querySelectorAll("#room_attrs form input[type='checkbox']");
        attrBoxes.forEach((attr) => {
            attr.checked = false;
        });
        this.currentRoom = null;
    },
    syncRoom: function () {
        if (this.currentRoom === null) {
            return;
        }
        const tbText = document.getElementById("room_info").innerText.trim();
        const roomEl = this.currentRoom.element;
        const mode = this;
        const encounterText = encodeURIComponent(JSON.stringify(this.currentRoom.encounter));
        const attrForm = document.querySelector("#room_attrs form");
        const fd = new FormData(attrForm);
        const roomAttrs = Array.from(fd.entries(), (a) => a[0]);
        if (roomEl.dataset.roomEncounter != encounterText) {
            roomEl.dataset.roomEncounter = encounterText;
            this.modifiedRooms.set(this.currentRoom.uid, this.currentRoom);
            markPageDirty();
        }
        if (tbText != this.currentRoom.notes) {
            roomEl.dataset.roomNote = encodeURIComponent(tbText);
            this.currentRoom.notes = tbText;
            this.modifiedRooms.set(this.currentRoom.uid, this.currentRoom);
            markPageDirty();
        }
        if (!(this.currentRoom.attributes.every((a) => roomAttrs.includes(a))
            && roomAttrs.every((a) => mode.currentRoom.attributes.includes(a)))) {
            mode.currentRoom.attributes = roomAttrs;
            roomAttributes.forEach((a) => {
                if (mode.currentRoom.attributes.includes(a)) {
                    roomEl.classList.add(a);
                }
                else {
                    roomEl.classList.remove(a);
                }
            });
            this.modifiedRooms.set(this.currentRoom.uid, this.currentRoom);
            markPageDirty();
        }
    },
    setEncounterItems: function(encounter) {
        const mode = this;
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
                mode.setEncounterItems(encounter);
                markPageDirty();
            };
            last_cell.appendChild(rm_btn);
        });
    },
    addEncounter: function(items) {
        if (this.currentRoom != null) {
            const roomEl = this.currentRoom.element;
            const encounter = {};
            for (const pair of items) {
                encounter[pair[0]] = pair[1];
            }
            this.currentRoom.encounter.items.push(encounter);
            this.setEncounterItems(this.currentRoom.encounter);
            this.syncRoom();
        }
    }
};

const stampMode = {
    name: "Stamp editor",
    abortController: new AbortController(),
    eventHandlerSignal: null,

    oneTimeSetup: function () {
        const mode = this;
        this.eventHandlerSignal = this.abortController.signal;
        document.querySelector("#stamp-mode input[type='text']")
        .addEventListener("change", (sb) => {
            fetch("/api/stamprepo?q=" + sb.target.value)
                .then((r) => r.json()).then((sr) => {
                    mode.displayStamps(sr);
                });
        });
        document.querySelector("#stamp-mode input[type='button']")
        .addEventListener("click", () => {
            const vals = { parent: "", dirs: [], stamps: [] };
            document.querySelectorAll("#stamps image").forEach((el) => {
                const stamp = mode.stampToObj(el);
                stamp.name = stamp.href.split(/[/]/).pop();
                if (!vals.stamps.find((st) => st.href === stamp.href)) {
                    vals.stamps.push(stamp);
                }
            });
            mode.displayStamps(vals);
        });
        this.getStamps(null);
    },
    setup: function () {
        addStyletoSVG("img-no-interaction", "image { pointer-events: none }");
        document.getElementById("stamp-mode").style.display = "flex";
    },
    teardown: function () {
        const prev_stamp = document.getElementById("stamp_preview");
        if (prev_stamp) {
            prev_stamp.remove();
        }
        removeStylefromSVG("img-no-interaction");
        document.getElementById("stamp-mode").style.display = "none";
    },
    leftClick: null,
    rightClick: function(ev) {
        ev.preventDefault();
        this.dropStamp();
    },
    mouseMove: function(ev) {
        this.moveStamp(ev.layerX, ev.layerY);
    },
    keyDown: function(ev) {
        if (ev.key === "q") {
            const mode = this;
            const prev_stamp = document.getElementById("stamp_preview");
            if (prev_stamp) {
                prev_stamp.remove();
            }
            removeStylefromSVG("img-no-interaction");
            document.querySelectorAll("#stamps image").forEach((stamp) => {
                stamp.addEventListener("click", (ev) => {
                    stamp.remove();
                    markPageDirty()
                }, { signal: mode.eventHandlerSignal });
            });
        }
        else if (ev.key === "r") {
            this.rotateStamp();
        }
    },
    keyUp: function(ev) {
        if (ev.key === "q") {
            addStyletoSVG("img-no-interaction", "image { pointer-events: none }");
            this.abortController.abort();
            this.abortController = new AbortController();
            this.eventHandlerSignal = this.abortController.signal;
        }
    },
    shortcuts: [
        "q: Click to delete stamps",
        "r: Rotate current stamp",
        "Right-click: Place stamp"
    ],
    saveData: function() {
        const mode = this;
        const data = [];
        document.getElementById("stamps").childNodes.forEach((s) => {
            data.push(mode.stampToObj(s));
        });
        return data;
    },
    /*
     * Mode functions
     */
    getStamps: function(path) {
        const mode = this;
        const stamp_list = document.getElementById("stamp-list");
        let apiURL = "/api/stamprepo";
        if (path) {
            apiURL += "/" + path;
        }
        fetch(apiURL).then((r) => r.json()).then((sr) => {
            mode.displayStamps(sr);
        });
    },
    displayStamps: function(sr) {
        const mode = this;
        const children = [];
        const stamp_list = document.getElementById("stamp-list");
        if (sr.parent !== null) {
            const parentDir = document.createElement("div");
            const link = document.createElement("a");
            parentDir.classList.add("stamp");
            parentDir.classList.add("stamp-folder");
            link.onclick = () => mode.getStamps(sr.parent);
            link.innerText = "up a level";
            parentDir.appendChild(link);
            children.push(parentDir);
        }
        stamp_list.replaceChildren(...children.concat(
            sr.dirs.map((dir) => {
                const dirEl = document.createElement("div");
                const link = document.createElement("a");
                link.onclick = () => mode.getStamps(dir);
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
                link.onclick = () => mode.selectStamp(stamp);
                img.src = stamp.href;
                img.setAttribute("loading", "lazy");
                link.appendChild(img);
                dirEl.appendChild(link);
                dirEl.classList.add("stamp");
                return dirEl;
            })
        ));
    },
    selectStamp: function(stamp) {
        const svg = document.querySelector(".map svg g");
        const prev_stamp = document.getElementById("stamp_preview");
        const stampPointer = document.createElementNS(svg.namespaceURI, "image");
        stampPointer.setAttributeNS(null, "x", 0);
        stampPointer.setAttributeNS(null, "y", 0);
        stampPointer.setAttributeNS(null, "width", stamp.width);
        stampPointer.setAttributeNS(null, "height", stamp.height);
        stampPointer.setAttributeNS(null, "href", stamp.href);
        stampPointer.setAttributeNS(null, "opacity", 0.3);
        stampPointer.setAttributeNS(null, "id", "stamp_preview");
        if (prev_stamp) {
            prev_stamp.remove();
        }
        svg.appendChild(stampPointer);
    },
    dropStamp: function() {
        const svg = document.querySelector(".map svg");
        const svg_stamps = document.getElementById("stamps");
        const stampPointer = document.getElementById("stamp_preview");
        if (stampPointer) {
            const stamp = document.createElementNS(svg.namespaceURI, "image");
            const angle = this.getStampAngle(stampPointer);
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
            svg_stamps.appendChild(stamp);
            markPageDirty();
        }
    },
    rotateStamp: function() {
        const stampPointer = document.getElementById("stamp_preview");
        if (stampPointer) {
            const angle = (this.getStampAngle(stampPointer) + 45) % 360;
            const x = stampPointer.x.animVal.value;
            const y = stampPointer.y.animVal.value;
            const width = stampPointer.width.animVal.value;
            const height = stampPointer.height.animVal.value;
            stampPointer.setAttributeNS(null, "transform",
                `rotate(${angle}, ${x + (width / 2)}, ${y + (height / 2)})`);
        }
    },
    moveStamp: function(x, y) {
        const stampPointer = document.getElementById("stamp_preview");
        if (stampPointer !== null) {
            const angle = this.getStampAngle(stampPointer);
            const width = stampPointer.width.animVal.value;
            const height = stampPointer.height.animVal.value;
            stampPointer.setAttributeNS(null, "x", x);
            stampPointer.setAttributeNS(null, "y", y);
            stampPointer.setAttributeNS(null, "transform",
                `rotate(${angle}, ${x + (width / 2)}, ${y + (height / 2)})`);
        }
    },
    getStampAngle: function(stamp) {
        const transform = stamp.transform.animVal;
        if (transform.numberOfItems === 0) {
            return 0;
        }
        return transform.getItem(0).angle;
    },
    stampToObj: function(stamp) {
        const angle = this.getStampAngle(stamp);
        const x = stamp.x.animVal.value;
        const y = stamp.y.animVal.value;
        const width = stamp.width.animVal.value;
        const height = stamp.height.animVal.value;
        const href = stamp.href.animVal;
        return {
            x: x, y: y,
            width: width, height: height,
            href: href, angle: angle,
        };
    }
};

const waterMode = {
    name: "Water editor",
    oneTimeSetup: function() {
        const mode = this;
        const widthSlider = document.getElementById("water-el-width");
        widthSlider.addEventListener("change", (ev) => {
            mode.changeSize(ev.target.value);
        });
        document.querySelectorAll("#water-mode input[name='mode']").forEach((el) => {
            el.addEventListener("change", (ev) => {
                if (ev.target.value == "add") {
                    mode.preview.setAttributeNS(null, "fill", "limegreen");
                }
                else if (ev.target.value == "remove") {
                    mode.preview.setAttributeNS(null, "fill", "none");
                }
            });
        });
    },
    setup: function() {
        document.getElementById("water-el-width").value = this.currentSize;
        document.querySelector("#water-mode input[value='add']").checked = true;
        this.preview = this.showMaskPreview();
        document.getElementById("water-mode").style.display = "flex";
    },
    teardown: function() {
        this.preview.remove();
        this.preview = null;
        document.getElementById("water-mode").style.display = "none";
    },
    leftClick: null,
    rightClick: null,
    mouseMove: function(ev) {
        this.preview.setAttributeNS(null, "cx", ev.layerX);
        this.preview.setAttributeNS(null, "cy", ev.layerY);
    },
    keyDown: function(ev) {
        if (ev.key === "w") {
            const maskMode = document.querySelector("#water-mode input[name='mode']:checked").value;
            if (maskMode == "add") {
                this.addToMask();
            }
            else if (maskMode == "remove") {
                this.removeFromMask();
            }
        }
    },
    keyUp: null,
    shortcuts: [
        "w: Edit water mask",
    ],
    saveData: function() {
        const maskEls = document.querySelectorAll("#water_mask .mask-element");
        return Array.from(maskEls.entries().map((e) => {
            const el = e[1];
            return {
                x: el.cx.animVal.value,
                y: el.cy.animVal.value,
                r: el.r.animVal.value
            };
        }));
    },

    /*
     * Mode funtions
     */
    currentSize: 1,
    preview: null,
    showMaskPreview: function() {
        const scale = parseInt(document.querySelector(".map").dataset.scale);
        const svg = document.querySelector(".map svg g");
        const waterPrev = document.createElementNS(svg.namespaceURI, "circle");
        waterPrev.setAttributeNS(null, "id", "water_preview");
        waterPrev.setAttributeNS(null, "cx", 0);
        waterPrev.setAttributeNS(null, "cy", 0);
        waterPrev.setAttributeNS(null, "filter", "url(#water_filter)");
        waterPrev.setAttributeNS(null, "r", (scale * this.currentSize) / 2);
        waterPrev.setAttributeNS(null, "opacity", 0.35);
        waterPrev.setAttributeNS(null, "fill", "limegreen");
        waterPrev.style.pointerEvents = "none";
        svg.appendChild(waterPrev);
        return waterPrev;
    },
    addToMask: function() {
        const maskEls = document.querySelectorAll("#water_mask .mask-element");
        const x = this.preview.cx.animVal.value;
        const y = this.preview.cy.animVal.value;
        const radius = this.preview.r.animVal.value;
        const dup = maskEls.entries().map((e) => {
            const el = e[1];
            const dist = Math.hypot(x - el.cx.animVal.value, y - el.cy.animVal.value);
            return dist < radius / 2;
        }).reduce((a, b) => a || b, false);
        if (!dup) {
            const svg = document.getElementById("water_mask");
            const maskEl = document.createElementNS(svg.namespaceURI, "circle");
            maskEl.setAttributeNS(null, "cx", x);
            maskEl.setAttributeNS(null, "cy", y);
            maskEl.setAttributeNS(null, "filter", "url(#water_filter)");
            maskEl.setAttributeNS(null, "r", radius);
            maskEl.setAttributeNS(null, "fill", "white");
            maskEl.classList.add("mask-element");
            svg.appendChild(maskEl);
            markPageDirty();
        }
    },
    removeFromMask: function() {
        const maskEls = document.querySelectorAll("#water_mask .mask-element");
        const x = this.preview.cx.animVal.value;
        const y = this.preview.cy.animVal.value;
        maskEls.forEach((el) => {
            const dist = Math.hypot(x - el.cx.animVal.value, y - el.cy.animVal.value);
            if (dist < el.r.animVal.value) {
                el.parentNode.removeChild(el);
                el.remove();
                markPageDirty();
            }
        });
    },
    changeSize: function(factor) {
        const scale = parseInt(document.querySelector(".map").dataset.scale);
        this.preview.setAttributeNS(null, "r", (factor * scale) / 2);
        this.currentSize = factor;
    }
};


/*
 * Setup event listeners
 */

document.addEventListener("DOMContentLoaded", function() {
    // Setup mode selection
    const allModes = [notesMode, stampMode, waterMode];
    let currentMode = null;
    const modeSelect = document.getElementById("mode_select");
    allModes.forEach((mode) => {
        if (mode.oneTimeSetup) {
            mode.oneTimeSetup();
        }
        const op = document.createElement("option");
        op.innerText = mode.name;
        modeSelect.appendChild(op);
    });
    modeSelect.addEventListener("change", (ev) => {
        if (currentMode.teardown) {
            currentMode.teardown();
        }
        currentMode = allModes[modeSelect.selectedIndex];
        if (currentMode.setup) {
            currentMode.setup();
        }
    });
    modeSelect.selectedIndex = 0;
    currentMode = notesMode;
    if (currentMode.setup) {
        currentMode.setup();
    }

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

    // Handlers for mode map interaction
    const leftClickHandler = (ev) => {
        if (currentMode.leftClick) {
            currentMode.leftClick(ev);
        }
    };
    const rightClickHandler = (ev) => {
        if (currentMode.rightClick) {
            currentMode.rightClick(ev);
        }
    };
    const moveHandler = (ev) => {
        if (currentMode.mouseMove) {
            currentMode.mouseMove(ev);
        }
    };
    // Add click-to-drag handler to map
    const svg = new SVGView(
        leftClickHandler,
        rightClickHandler,
        moveHandler
    );
    document.getElementById("zoom_to_fit_btn").onclick = () => {
        svg.zoomToExtents();
    };

    // Add keyboard interactions
    document.addEventListener("keydown", (ev) => {
        if (ev.key == "?" && currentMode.shortcuts) {
            alert("Keyboard actions:\n" + currentMode.shortcuts.join("\n"));
        }
        else if (currentMode.keyDown) {
            currentMode.keyDown(ev);
            svg.refresh();
        }
    });
    document.addEventListener("keyup", (ev) => {
        if (currentMode.keyUp) {
            currentMode.keyUp(ev);
            svg.refresh();
        }
    });

    // Add hanlder for map view button
    const dungeon = document.querySelector("body").dataset.dungeon;
    const levelId = document.querySelector(".map").dataset.lvid;
    const floorId = document.querySelector(".map").dataset.floorid;
    document.getElementById("view_map_btn").onclick = () => {
        const svgEl = d3.zoomTransform(svg.svg);
        const zoomProps = {
            "x": svgEl.x,
            "y": svgEl.y,
            "k": svgEl.k,
        };
        window.open(
            `/${dungeon}/map/${levelId}/${floorId}#${JSON.stringify(zoomProps)}`,
            "_blank"
        ).focus();
    }

    // Add handlers for save
    const save_btn = document.getElementById("save_btn");
    save_btn.onclick = () => {
        fetch(`/api/save/${dungeon}/${levelId}/${floorId}`, {
            method: "POST",
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                rooms: notesMode.saveData(),
                stamps: stampMode.saveData(),
                water: waterMode.saveData()
            })
        }).then((r) => { if (r.ok) markPageClean(); });
    };
    window.addEventListener("beforeunload", (e) => {
        if (!isPageDirty()) {
            return true;
        }
        e.preventDefault();
        return false;
    });

    // Check if there is a room selected in the URL
    if (window.location.hash) {
        notesMode.selectRoom(window.location.hash.slice(1));
    }
});
