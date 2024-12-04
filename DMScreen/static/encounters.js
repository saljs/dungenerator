document.addEventListener("DOMContentLoaded", function() {
    // Roll for initiative
    document.querySelectorAll("[data-initiative]").forEach((cell) => {
        const initiative = cell.dataset.initiative;
        const rolled = Math.round(Math.random() * 19 + 1);
        cell.querySelector("input").value = rolled;
    });

    // Handler for hp chnage
    const deathCheck = (hp) => {
        const row = hp.closest("tr");
        if(parseInt(hp.value) <= 0) {
            row.classList.add("row-dead");
        }
        else {
            row.classList.remove("row-dead");
        }
    };
    document.querySelectorAll(".enemy-hp input").forEach((hp) => {
        hp.onchange = () => { deathCheck(hp); };
    });

    // Handler for add damage buttons
    const addDamage = (hp) => {
        const damage = parseInt(prompt("Damage:"));
        const health = parseInt(hp.value);
        hp.value = health - damage;
        deathCheck(hp);
    };
    document.querySelectorAll(".add-dmg button").forEach((btn) => {
        const hp = btn.closest("tr").querySelector(".enemy-hp input");
        btn.onclick = () => {
            addDamage(hp);
        };
    });

    const table = document.getElementById("encounter-table")
    // Handler for 'Add ally' button
    document.getElementById("add-ally").onclick = () => {
        const row = table.insertRow(0);
        
        row.insertCell(0).innerHTML = '<input type="text" />';
        row.insertCell(1).innerHTML = '<input type="number" />';
        
        const hpRow = row.insertCell(2);
        const hp = document.createElement("input");
        hp.type = "number";
        hp.onchange = deathCheck;
        hpRow.appendChild(hp);
        
        const btnRow = row.insertCell(3);
        const button = document.createElement("button");
        button.innerHTML = "Add damage";
        button.onclick = () => { deathCheck(hp); };
        btnRow.appendChild(button);
        
        row.insertCell(4);
    };

    // Handler for 'Tally XP' button
    document.getElementById("tally-xp").onclick = () => {
        let xpTotal = 0;
        for(let row of table.rows) {
            if (row.cells[2].firstChild.value <= 0) {
                if (parseInt(row.cells[4].innerHTML)) {
                    xpTotal += parseInt(row.cells[4].innerHTML);
                }
            }
        }
        alert(`Total XP for encounter: ${xpTotal}`);
    };
 
    // Handler for 'Arrange in initiative order' button
    document.getElementById("sort-init").onclick = () => {
        const ordered = Array.from(table.rows).sort(function(r1, r2) {
            let tb1 = r1.cells[1].querySelector("input");
            let tb2 = r2.cells[1].querySelector("input");
            let init1 = tb1.value ? parseInt(tb1.value) : 0;
            let init2 = tb2.value ? parseInt(tb2.value) : 0;
            if(init1 === init2) {
                return r2.cells[1].dataset.initiative - r1.cells[1].dataset.initiative;
            }
            return init2 - init1;
        }).forEach((tr) => table.appendChild(tr) );
  };
});
