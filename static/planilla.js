// --------------------
// VARIABLES
// --------------------

let cantidadNotas = document.querySelectorAll("#fila-head th.encabezado-editable").length;

// --------------------
// AGREGAR COLUMNA
// --------------------

function agregarColumna() {

    let head = document.getElementById("fila-head");

    cantidadNotas++;

    let th = document.createElement("th");
    th.contentEditable = true;
    th.classList.add("encabezado-editable");
    th.innerText = "Nota " + cantidadNotas;

    head.insertBefore(th, head.lastElementChild);

    document.querySelectorAll("#tabla tbody tr").forEach(fila => {

        let td = document.createElement("td");

        td.innerHTML = `
            <select class="nota-select">
                <option value=""></option>
                <option value="B">Bajo</option>
                <option value="BS">Básico</option>
                <option value="A">Alto</option>
                <option value="S">Superior</option>
            </select>
        `;

        fila.insertBefore(td, fila.lastElementChild);
    });

    activarEventos();
}

// --------------------
// PROMEDIO
// --------------------

function convertirNota(letra) {
    if (letra === "B") return 2.5;
    if (letra === "BS") return 3.5;
    if (letra === "A") return 4.3;
    if (letra === "S") return 4.8;
    return null;
}

function convertirPromedio(num) {
    if (num === null) return "";
    if (num <= 3.0) return "B";
    if (num <= 3.9) return "BS";
    if (num <= 4.5) return "A";
    return "S";
}

function calcularPromedio(fila) {

    let promedioCelda = fila.querySelector(".promedio");

    // 🔥 SI YA ESTÁ GUARDADO Y NO SE HAN CAMBIADO NOTAS → NO TOCAR
    if (promedioCelda.dataset.guardado && !promedioCelda.dataset.recalcular) {
        return;
    }

    let selects = fila.querySelectorAll(".nota-select");
    let suma = 0;
    let contador = 0;

    selects.forEach(sel => {
        let val = convertirNota(sel.value);
        if (val !== null) {
            suma += val;
            contador++;
        }
    });

    if (contador === 0) return;

    let prom = suma / contador;

    promedioCelda.innerText = convertirPromedio(prom);

    // 🔥 limpiar flags
    delete promedioCelda.dataset.editado;
    delete promedioCelda.dataset.guardado;
    delete promedioCelda.dataset.recalcular;
}

// --------------------
// EVENTOS
// --------------------

function activarEventos() {

    document.querySelectorAll(".nota-select").forEach(sel => {

        sel.onchange = function() {

            let fila = this.closest("tr");
            let promedioCelda = fila.querySelector(".promedio");

            // 🔥 ahora sí debe recalcular
            promedioCelda.dataset.recalcular = "true";
            delete promedioCelda.dataset.guardado;
            delete promedioCelda.dataset.editado;

            calcularPromedio(fila);
        };
    });
}

// 🔥 detectar edición manual del promedio
document.addEventListener("input", function(e) {
    if (e.target.classList.contains("promedio")) {
        e.target.dataset.editado = "true";
        e.target.dataset.guardado = "true";
    }
});

// --------------------
// INICIALIZACIÓN
// --------------------

document.addEventListener("DOMContentLoaded", function() {

    activarEventos();

    // 🔥 marcar TODOS los promedios cargados como guardados
    document.querySelectorAll(".promedio").forEach(celda => {
        if (celda.innerText.trim() !== "") {
            celda.dataset.guardado = "true";
        }
    });

    document.querySelectorAll("#tabla tbody tr").forEach(fila => {
        calcularPromedio(fila);
    });

});

// --------------------
// GUARDAR
// --------------------

function guardarNotas() {

    let select = document.querySelector("select[name='id_carga']");
    if (!select.value) {
        alert("Debes seleccionar un curso");
        return;
    }

    let tabla = document.getElementById("tabla");

    let encabezados = [];
    document.querySelectorAll("#fila-head th.encabezado-editable").forEach(th => {
        encabezados.push(th.innerText.trim());
    });

    let datos = {
        id_carga: select.value,
        encabezados: encabezados,
        estudiantes: []
    };

    tabla.querySelectorAll("tbody tr").forEach(fila => {

        let celdas = fila.querySelectorAll("td");

        let est = {
            apellido: celdas[1].innerText,
            nombre: celdas[2].innerText,
            promedio: celdas[celdas.length - 1].innerText,
            notas: []
        };

        fila.querySelectorAll(".nota-select").forEach(sel => {
            est.notas.push(sel.value);
        });

        datos.estudiantes.push(est);
    });

    fetch("/guardar_notas", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(datos)
    })
    .then(res => {
        if (!res.ok) {
            return res.text().then(text => { throw new Error(text) });
        }
        return res.json();
    })
    .then(() => alert("Notas guardadas"))
    .catch(error => alert("Error: " + error));
}