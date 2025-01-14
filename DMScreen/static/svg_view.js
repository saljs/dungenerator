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
        innerG.addEventListener("click", onclick);
        innerG.addEventListener("mousemove", onmousemove);
        innerG.addEventListener("contextmenu", onrightclick);
    }
        
    zoomToExtents() {
        this.zoomTo(0, 0, this.map.clientWidth / this.svg.clientWidth);
    }

    zoomTo(x, y, k) {
        this.svg.scale = k;
        const d3map = d3.select("svg");
        d3map.call(this.zoom.scaleTo, this.svg.scale, [0, 0]);
        d3map.call(this.zoom.translateTo, 0, 0, [x, y]);
    }
}
