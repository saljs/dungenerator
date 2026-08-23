document.addEventListener("DOMContentLoaded", function() {
    // Roll for initiative
    document.querySelectorAll(".initiative").forEach((item) => {
        const initiative = parseInt(item.dataset.initiative);
        const rolled = Math.round(Math.random() * 19 + 1);
        item.value = rolled + initiative;
    });

    // Handler for hp change
    const deathCheck = (hp) => {
        const row = hp.closest(".encounter-player");
        if(parseInt(hp.value) <= 0) {
            row.classList.add("dead");
        }
        else {
            row.classList.remove("dead");
        }
    };
    document.querySelectorAll(".hp").forEach((item) => {
        item.onchange = () => { deathCheck(item); };
    });

    // Handler for select player item
    const selectPlayer = (player) => {
        document.querySelectorAll(".encounter-player").forEach((item) => {
            item.classList.remove("selected");
        });
        player.classList.add("selected");
        const book = player.querySelector(".book-ref");
        if (book) {
            const bookPrev = document.querySelector(".book-popout > iframe");
            bookPrev.src = book.href;
        }
    };
    document.querySelectorAll(".encounter-player").forEach((item) => {
        item.onclick = () => { selectPlayer(item); }
    });

    // Handler for add damage buttons
    document.querySelectorAll(".add-damage").forEach((item) => {
        item.onclick = () => {
            const hp = item.parentElement.querySelector(".hp");
            const damage = parseInt(prompt("Damage:"));
            const health = parseInt(hp.value);
            hp.value = health - damage;
            deathCheck(hp);
        };
    });

    // Handler for 'Add ally' button
    const addAlly = (allyName) => {
        const ally = document.createElement("div");
        ally.classList.add("encounter-player");
        ally.innerHTML = `
            <h4>${allyName}</h4>
            <label>
                Initiative
                <input type="number" class="initiative">
            </label>
            <br />
            <button class="remove-ally">Remove ally</button>
        `;
        ally.onclick = () => { selectPlayer(ally); };
        ally.querySelector(".remove-ally").onclick = () => {
            ally.remove();
            const allies = localStorage.getItem("encounter-allies")
                ? localStorage.getItem("encounter-allies").split(",")
                : [];
            localStorage.setItem("encounter-allies",
                allies.filter((i) => i !== allyName).join(","));
        };
        document.getElementById("encounter-players").appendChild(ally);
        selectPlayer(ally);

        // Save to local storage
        const allies = localStorage.getItem("encounter-allies")
            ? localStorage.getItem("encounter-allies").split(",")
            : [];
        if (! allies.includes(allyName)) {
            allies.push(allyName);
        }
        localStorage.setItem("encounter-allies", allies.join(","));
    };
    document.getElementById("add-ally").onclick = () => {
        addAlly(prompt("Ally name:"));
    };
    if (localStorage.getItem("encounter-allies")) {
        const allies = localStorage.getItem("encounter-allies").split(",");
        allies.forEach((i) => { addAlly(i); });
    }

    // Handler for 'Tally XP' button
    document.getElementById("tally-xp").onclick = () => {
        let xpTotal = 0;
        document.querySelectorAll(".xp").forEach((xp) => {
            xpTotal += parseInt(xp.innerText);
        });
        alert(`Total XP for encounter: ${xpTotal}`);
    };

    // Handler for arrange in initiative order
    document.getElementById("sort-init").onclick = () => {
        const ordered = Array.from(
            document.querySelectorAll(".initiative")
        ).sort((i1, i2) => {
            const init1 = parseInt(i1.value);
            const init2 = parseInt(i2.value);
            return init2 - init1;
        }).map((i) => {
            return i.closest(".encounter-player");
        });
        document.getElementById("encounter-players")
            .replaceChildren(...ordered);
    };
});
