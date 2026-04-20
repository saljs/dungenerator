function highlightSearchTerms (el) {
    const query = document.querySelector("body").dataset
        .query.toLowerCase().split(" ");
    const highlights = query.flatMap((searchTerm) => {
        const regex = new RegExp(searchTerm, "g");
        const lines = el.childNodes.values().flatMap((node) => {
            const matches = node.textContent.toLowerCase().matchAll(regex);
            ranges = matches.map((match) => {
                const range = new Range();
                range.setStart(node, match.index);
                range.setEnd(node, match.index + searchTerm.length);
                return range;
            });
            return ranges.toArray();
        });
        return lines.toArray();
    });
    console.log(highlights);
    const marks = new Highlight(...highlights);
    CSS.highlights.set("search-term-match", marks);
}

document.addEventListener("DOMContentLoaded", function() {
    const full_result = document.getElementById("search-full-result");
    const full_result_link = document.getElementById("result-link");
    const full_result_title = document.getElementById("search-full-result-title");
    const selectResult = (res) => {
        full_result.innerText = res.querySelector(".search-result-text")
            .innerHTML;
        full_result_link.href = window.location.pathname.replace("search", 
            `level/${res.dataset.level}/${res.dataset.floor}#${res.dataset.roomid}`);
        full_result_title.innerText = res.querySelector("h3").innerText;
        let selected = document.querySelector(".selected");
        if (selected) {
            selected.classList.remove("selected");
        }
        res.classList.add("selected");
        highlightSearchTerms(full_result);
    };
    document.querySelectorAll(".search-result").forEach((res) => {
        res.onclick = () => { selectResult(res) };
    });
    selectResult(document.querySelector(".search-result"));
});
