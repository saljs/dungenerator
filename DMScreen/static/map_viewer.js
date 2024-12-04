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

document.addEventListener("DOMContentLoaded", function() {
    // Add in initial mask
    const svg = document.querySelector(".map svg");
    const defs = svg.querySelector("defs");
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
            width="${svgWidth}" height="${svgHeight}"
        />
        <rect
            id="light-mask-rect"
            fill="white"
            x=0 y=0
            width="${svgWidth}" height="${svgHeight}"
        />`;
    defs.appendChild(mask);
    svg.querySelector("g").setAttributeNS(null, "mask", "url(#light-mask)");

    // Add in click-to-drag handler
    const light = document.getElementById("light-mask-rect");
    const lightHandler = (x, y, ev) => {
        console.log(ev);
        set_light_mask(
            light,
            x, y, svgWidth, svgHeight,
            parseInt(document.querySelector(".map").dataset.scale),
        );
    };
    const svg_view = new SVGView(null,
        (x, y, ev) => {
            ev.preventDefault();
            light_radius++;
            if (light_radius >= light_radius_options.length) {
                light_radius = 0;
            }
            lightHandler(x, y, ev);
        }, 
        (x, y, ev) => {
            if (ev.shiftKey) {
                // Only move light if shift key is held
                lightHandler(x, y, ev);
            }
        });

    // Add in keyboard actions
    document.addEventListener("keydown", (ev) => {
        if (ev.key === 'z') {
            svg_view.zoomToExtents();
        }
        else if (ev.key === 'l') {

            svg.dispatchEvent();
        }
    });
});
