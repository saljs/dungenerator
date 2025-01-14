function selectLevel(lvid) {
    // Make textbox visable
    const all_textboxes = document.querySelectorAll(".notes textarea");
    all_textboxes.forEach((tb) => { tb.classList.remove("active"); });
    document.querySelector(".notes textarea[data-lvid='" + lvid + "']")
        .classList.add("active");

    // Make button selected
    const all_buttons = document.querySelectorAll(".choose_lvl_btn");
    all_buttons.forEach((btn) => { btn.classList.remove("selected"); });
    document.querySelector(".choose_lvl_btn[data-lvid='" + lvid + "']")
        .classList.add("selected");

    // Set options for floors
    const floor_opts = document.getElementById("floor_selection");
    const floors = parseInt(
        document.querySelector(".notes textarea[data-lvid='" + lvid + "']")
            .dataset.floors
    );
    floor_opts.replaceChildren(
        ...Array.from({length: floors}, (v, k) => k+1)
            .map((floorid) => {
                const opt = document.createElement("option");
                opt.value = floorid;
                opt.innerText = `Floor ${floorid}`;
                return opt;
            })
    );
    // Set correct level URL
    document.getElementById("edit_lvl_btn").onclick = () => {
        window.location = "/"
            + document.querySelector("body").dataset.dungeon
            + "/level/" + lvid + "/" + floor_opts.value;
    };
    window.location.hash = lvid;    
}

function saveLevels() {
    // Loop over textboxes and get text
    const all_textboxes = document.querySelectorAll(".notes textarea");
    const update = { "levels": {}}
    for (let i = 0; i < all_textboxes.length; i++) {
        update["levels"][i + 1] = all_textboxes[i].value;
    }
    fetch("/api/save/" + document.querySelector("body").dataset.dungeon, {
        method: "POST",
        headers: {
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
        body: JSON.stringify(update),
    }).then((r) => {
        if (r.ok) {
            document.getElementById("save_btn").classList.add("success");
        }
        else {
            console.error(r);
        }
    });
}

document.addEventListener("DOMContentLoaded", function() {
    // Select the first level to being
    if (window.location.hash) {
        selectLevel(parseInt(window.location.hash.slice(1)));
    }
    else {
        selectLevel(1);
    }

    // Add click handler to level buttons
    document.querySelectorAll(".choose_lvl_btn").forEach((btn) => {
        btn.onclick = () => { selectLevel(btn.dataset.lvid); };
    });

    // Add event listeners to textboxes
    const save_btn = document.getElementById("save_btn");
    document.querySelectorAll(".notes textarea").forEach((tb) => {
        tb.addEventListener("input", () => {
            save_btn.classList.remove("success");
        });
    });
    
    // Add handlers for save
    save_btn.onclick = saveLevels;
    window.addEventListener("beforeunload", (e) => {
        if (save_btn.classList.contains("success")) {
            return true;
        }
        e.preventDefault();
        return false;
    });
});
