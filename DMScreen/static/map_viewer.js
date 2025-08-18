const light_radius_options = ["0", "15%", "20%", "30%", "40%"];
let light_radius = 0;

function toggle_shadows(svg) {
    const fg = document.getElementById("fg-elements");
    if (fg.getAttribute("filter")) {
        fg.setAttributeNS(null, "filter", "");
    }
    else {
        fg.setAttributeNS(null, "filter", "url(#shadow_filter)");
    }
}

function scale_light_overlay(size) {
    const svg = document.querySelector("div.overlay svg");
    const mask = document.getElementById("overlay-mask");
    const rect = mask.querySelector("rect");
    const circle = mask.querySelector("circle");
    const circle2 = document.getElementById("overlay-grad-circ");
    svg.setAttribute("viewBox", `0 0 ${window.innerWidth}, ${window.innerHeight}`);
    rect.setAttributeNS(null, "width", window.innerWidth);
    rect.setAttributeNS(null, "height", window.innerHeight);
    circle.setAttributeNS(null, "cx", window.innerWidth / 2);
    circle.setAttributeNS(null, "cy", window.innerHeight / 2);
    circle.setAttributeNS(null, "r", light_radius_options[light_radius]);
    circle2.setAttributeNS(null, "cx", window.innerWidth / 2);
    circle2.setAttributeNS(null, "cy", window.innerHeight / 2);
    circle2.setAttributeNS(null, "r", light_radius_options[light_radius]);
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

function toggle_light() {
    const overlay = document.querySelector("div.overlay");
    if(light_radius === light_radius_options.length - 1) {
        light_radius = 0;
        overlay.style.display = "none";
    }
    else {
        light_radius++;
        overlay.style.display = "inherit";
    }
    scale_light_overlay();
}

document.addEventListener("DOMContentLoaded", function() {
    const svg = document.querySelector(".map svg");
    const scale = parseInt(document.querySelector(".map").dataset.scale);

    const svg_view = new SVGView(null, null, (ev) => {
        update_url_hash(svg_view.svg);
        document.body.style.cursor = "grab";
        setTimeout(() => {
            document.body.style.cursor = "none";
        }, 3000);
    });

    // Add in keyboard actions
    document.addEventListener("keydown", (ev) => {
        if (ev.key === '?' || ev.key == 'F1') {
            alert(
`Keyboard actions:
z: Zoom to extents
g: Scale to 5' = 1"
s: Toggle shadows
l: Toggle light mask size
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
        else if (ev.key === 's') {
            toggle_shadows(svg);
        }
        else if (ev.key === 'l') {
            toggle_light();
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
    });

    if (window.location.hash) {
        const hashVal = decodeURIComponent(window.location.hash.slice(1));
        const zoomProps = JSON.parse(hashVal);
        svg_view.zoomTo(zoomProps["x"], zoomProps["y"], zoomProps["k"]);
    }

    // Aquire screen wakelock
    navigator.wakeLock.request("screen");

    // Add listeners for scaling light overlay
    scale_light_overlay();
    window.addEventListener("resize", scale_light_overlay);
});
