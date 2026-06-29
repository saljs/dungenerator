const light_radius_map = {
    2: 5,
    5: 10,
    10: 20,
    20: 2,
};
let mouseCursorTimeout = null;

function toggle_shadows(svg) {
    const fg = document.getElementById("fg-elements");
    if (fg.getAttribute("filter")) {
        fg.setAttributeNS(null, "filter", "");
    }
    else {
        fg.setAttributeNS(null, "filter", "url(#shadow_filter)");
    }
}

function scale_light_overlay(svg, scale) {
    const svgEl = d3.zoomTransform(svg);
    const overlaySvg = document.querySelector("div.overlay svg");
    const sfac = scale * svgEl.k;
    overlaySvg.setAttribute("viewBox",
        `0 0 ${window.innerWidth / sfac}, ${window.innerHeight / sfac}`
    );
    return sfac;
}

function place_light(clickX, clickY, del = false) {
    const overlay = document.getElementById("overlay-mask");
    const svg = document.querySelector("div.overlay svg");
    const lights = overlay.querySelectorAll("circle");
    let circleClicked = false;

    lights.forEach((l) => {
        const dist = Math.hypot(
            clickX - l.cx.animVal.value,
            clickY - l.cy.animVal.value
        );
        // Check if light source was clicked
        if (dist < l.r.animVal.value) {
            if (del) {
                // Remove light source
                circleClicked = true;
                l.remove();
            }
            else {
                // Increment light source size
                circleClicked = true;
                l.setAttributeNS(null, "r", light_radius_map[l.r.animVal.value]);
            }
        }
    });
    if (!circleClicked && !del) {
        // Create new light source
        const newLS = document.createElementNS(svg.namespaceURI, "circle");
        newLS.setAttributeNS(null, "r", 2);
        newLS.setAttributeNS(null, "cx",
            `${100 * (clickX / svg.width.animVal.value)}%`);
        newLS.setAttributeNS(null, "cy",
            `${100 * (clickY / svg.height.animVal.value)}%`);
        newLS.setAttributeNS(null, "fill", "url(#light-grad)");
        overlay.appendChild(newLS);
    }
}

function update_url_hash(svg) {
    const svgEl = d3.zoomTransform(svg);
    const zoomProps = {
        "x": svgEl.x,
        "y": svgEl.y,
        "k": svgEl.k,
    };
    window.location.hash = JSON.stringify(zoomProps);
}

function toggle_light_mask() {
    const overlay = document.querySelector("div.overlay");
    if (overlay.style.display === "none" || !overlay.style.display) {
        overlay.style.display = "block";
    }
    else {
        overlay.style.display = "none";
    }
}

function reload_svg_img(url) {
    // We only need to swap out "stamps" and "water"
    const parser = new DOMParser();
    fetch(url).then((resp) => resp.text()).then((newsvg) => {
        const newImg = parser.parseFromString(newsvg, "image/svg+xml");
        document.getElementById("water").replaceWith(newImg.getElementById("water"));
        document.getElementById("stamps").replaceWith(newImg.getElementById("stamps"));
    });
}

document.addEventListener("DOMContentLoaded", function() {
    const scale = parseInt(document.querySelector(".map").dataset.scale);
    const overlay = document.querySelector("div.overlay");

    const svg_view = new SVGView(null, null, (ev) => {
        update_url_hash(svg_view.svg);
    });

    // Add in keyboard actions
    document.addEventListener("keydown", (ev) => {
        if (ev.key === '?' || ev.key == 'F1') {
            alert(
`Keyboard actions:
z: Zoom to extents
g: Scale to 5' = 1"
r: Reload map
s: Toggle shadows
l: Toggle light mask on/off
n: Add new lightsource
k: Move to next floor up
j: Move to next floor down`
            );
        }
        else if (ev.key === 'z') {
            svg_view.zoomToExtents();
        }
        else if (ev.key === 'g') {
            const svgEl = d3.zoomTransform(svg_view.svg);
            const displayWidth = parseInt(window.prompt("Enter display width (Inches):"));
            if (displayWidth) {
                svg_view.zoomTo(
                    svgEl.x + (window.innerWidth / 2),
                    svgEl.y + (window.innerHeight / 2),
                    (window.innerWidth / displayWidth) / scale
                );
                update_url_hash(svg_view.svg);
            }
        }
        else if (ev.key === 'r') {
            reload_svg_img(svg_view.map.dataset.svgurl);
        }
        else if (ev.key === 's') {
            toggle_shadows(svg_view.svg);
        }
        else if (ev.key === 'l') {
            scale_light_overlay(svg_view.svg, scale);
            toggle_light_mask();
        }
        else if (ev.key === 'k') {
            if ("floor_up" in svg_view.map.dataset) {
                update_url_hash(svg_view.svg);
                window.location = svg_view.map.dataset.floor_up
                    + window.location.hash;
            }
        }
        else if (ev.key === 'j') {
            if ("floor_down" in svg_view.map.dataset) {
                update_url_hash(svg_view.svg);
                window.location = svg_view.map.dataset.floor_down
                    + window.location.hash;
            }
        }
        else if (ev.key === "Shift") {
            overlay.style.pointerEvents = "none";
        }
    });
    document.addEventListener("keyup", (ev) => {
        if (ev.key === "Shift") {
            overlay.style.pointerEvents = "auto";
        }
    });

    // Add listeners for light overlay
    scale_light_overlay(svg_view.svg, scale);
    window.addEventListener("resize", () => {
        scale_light_overlay(svg_view.svg, scale);
    });
    const lights_click = (ev) => {
        if (ev.shiftKey) {
            return;
        }
        ev.preventDefault();
        const sfac = scale_light_overlay(svg_view.svg, scale);
        const clickX = ev.clientX / sfac;
        const clickY = ev.clientY / sfac;
        place_light(clickX, clickY,  ev.button === 2);
    };
    overlay.onclick = lights_click;
    overlay.addEventListener("contextmenu", lights_click);

    // Add mouse cursor hiding listeners
    document.addEventListener("mousemove", () => {
        document.body.style.cursor = "crosshair";
        if(mouseCursorTimeout !== null) {
            clearTimeout(mouseCursorTimeout);
            mouseCursorTimeout = null;
        }
        mouseCursorTimeout = setTimeout(() => {
            document.body.style.cursor = "none";
            mouseCursorTimeout = null;
        }, 3000);
    });

    // Aquire screen wakelock
    navigator.wakeLock.request("screen");

    // Set window hash zoom
    if (window.location.hash) {
        const hashVal = decodeURIComponent(window.location.hash.slice(1));
        const zoomProps = JSON.parse(hashVal);
        svg_view.zoomTo(zoomProps["x"], zoomProps["y"], zoomProps["k"]);
    }
});
