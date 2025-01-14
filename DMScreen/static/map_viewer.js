const light_radius_options = [0, 2, 5, 10, 20];
let light_radius = 0;

function set_light_mask(maskEl, x, y, width, height, scale) {
    if (light_radius > 0) {
        //change light radius and draw
        const r = light_radius_options[light_radius] * scale;
        maskEl.setAttributeNS(null, "fill", "url(#light-gradient)");
        maskEl.setAttributeNS(null, "x", x - r);
        maskEl.setAttributeNS(null, "y", y - r);
        maskEl.setAttributeNS(null, "width", r * 2);
        maskEl.setAttributeNS(null, "height", r * 2);
    }
    else {
        maskEl.setAttributeNS(null, "fill", "white");
        maskEl.setAttributeNS(null, "x", 0);
        maskEl.setAttributeNS(null, "y", 0);
        maskEl.setAttributeNS(null, "width", width);
        maskEl.setAttributeNS(null, "height", height);
    }
}

function toggle_shadows(svg) {
    const fg = svg.querySelector("#fg-elements");
    if (fg.getAttribute("filter")) {
        fg.setAttributeNS(null, "filter", "");
    }
    else {
        fg.setAttributeNS(null, "filter", "url(#shadow)");
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

document.addEventListener("DOMContentLoaded", function() {
    const svg = document.querySelector(".map svg");
    const defs = svg.querySelector("defs");
    // Add in initial mask
    const grad = document.createElementNS(svg.namespaceURI, "radialGradient");
    grad.setAttributeNS(null, "id", "light-gradient");
    grad.innerHTML = `
        <stop offset="0%" stop-color="white" />
        <stop offset="80%" stop-color="white" />
        <stop offset="100%" stop-color="black" />`;
    defs.appendChild(grad);
    
    const mask = document.createElementNS(svg.namespaceURI, "mask");
    const svgWidth = svg.clientWidth;
    const svgHeight = svg.clientHeight;
    mask.setAttributeNS(null, "id", "light-mask");
    mask.innerHTML = `
        <rect
            fill="black"
            x=0 y=0
            width="120%" height="120%"
        />
        <rect
            id="light-mask-rect"
            fill="white"
            x=0 y=0
            width="${svgWidth}" height="${svgHeight}"
        />`;
    defs.appendChild(mask);
    svg.querySelector("g").setAttributeNS(null, "mask", "url(#light-mask)");
    // Add in shadow filter
    const scale = parseInt(document.querySelector(".map").dataset.scale);
    const shadow = document.createElementNS(svg.namespaceURI, "filter");
    shadow.setAttributeNS(null, "id", "shadow");
    shadow.innerHTML = `
      <feFlood flood-color="black"/>
      <feComposite operator="out" in2="SourceGraphic"/>
      <feGaussianBlur stdDeviation="${scale / 4}"/>
      <feOffset dx="${scale / 10}" dy="${scale / 10}" result="drop-shadow"/>
      <feComposite operator="atop" in2="SourceGraphic"/>`;
    defs.appendChild(shadow);
                        
    // Add in click-to-drag handler
    const light = document.getElementById("light-mask-rect");
    const lightHandler = (x, y) => {
        set_light_mask(
            light,
            x, y, svgWidth, svgHeight,
            scale,
        );
    };
    const svg_view = new SVGView(null,
        (ev) => {
            ev.preventDefault();
            light_radius++;
            if (light_radius >= light_radius_options.length) {
                light_radius = 0;
            }
            lightHandler(ev.layerX, ev.layerY);
        }, 
        (ev) => {
            if (ev.shiftKey) {
                // Only move light if shift key is held
                lightHandler(ev.layerX, ev.layerY);
            }
            update_url_hash(svg_view.svg);
        });

    // Add in keyboard actions
    document.addEventListener("keydown", (ev) => {
        if (ev.key === 'z') {
            svg_view.zoomToExtents();
        }
        else if (ev.key === 's') {
            toggle_shadows(svg);
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
});
