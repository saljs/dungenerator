class SVGView {
    constructor(
        onclick = () => null,
        onrightclick = () => null,
        onmousemove = () => null,
    ) {
        this.map = document.querySelector(".map");
        this.svg = this.map.querySelector("svg");
        const handleZoom = (ev) => {
            d3.select("svg g").attr("transform", ev.transform);
        }
        this.zoom = d3.zoom().on("zoom", handleZoom);
        d3.select("svg").call(this.zoom);
        this.zoomToExtents();
    
        const innerG = this.svg.querySelector("g");
        const eventHandler = (func) => {
            return (ev) => {
                if (func) {
                    let x = ev.layerX;
                    let y = ev.layerY;
                    if ( ev.originalTarget.nodeName.toLowerCase() === "image"
                        && ev.originalTarget.getAttribute("transform")
                    ) {
                        x += parseInt(ev.originalTarget.getAttribute("x"));
                        y += parseInt(ev.originalTarget.getAttribute("y"));
                    }
                    func(x, y, ev);
                }
            };
        };
        innerG.addEventListener("click", eventHandler(onclick));
        innerG.addEventListener("mousemove", eventHandler(onmousemove));
        innerG.addEventListener("contextmenu", eventHandler(onrightclick));
    }
        
    zoomToExtents() {
        this.svg.scale = this.map.clientWidth / this.svg.clientWidth;
        const d3map = d3.select("svg");
        d3map.call(this.zoom.scaleTo, this.svg.scale, [0, 0]);
        d3map.call(this.zoom.translateTo, 0, 0, [0, 0]);
    }
}
