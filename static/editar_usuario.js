// 🔵 AGREGAR NUEVA CARGA (VACÍA)
function agregarCarga() {

    const container = document.getElementById("carga-container");

    const div = document.createElement("div");
    div.classList.add("carga-item");

    let cursoSelect = document.createElement("select");
    cursoSelect.innerHTML = '<option value="">Seleccione curso</option>';

    cursos.forEach(c => {
        cursoSelect.innerHTML += `
            <option value="${c.id_curso}" data-grado="${c.grado}">
                ${c.grado}°${c.grupo}
            </option>`;
    });

    let materiaSelect = document.createElement("select");
    materiaSelect.innerHTML = '<option value="">Seleccione materia</option>';

    let inputHidden = document.createElement("input");
    inputHidden.type = "hidden";
    inputHidden.name = "carga";

    // 🔥 FILTRO
    cursoSelect.addEventListener("change", () => {

        const grado = cursoSelect.options[cursoSelect.selectedIndex].dataset.grado;

        materiaSelect.innerHTML = '<option value="">Seleccione materia</option>';

        asignaturas.forEach(a => {

            if (a.nombre.toLowerCase().includes("especialidad")) {
                if (grado != 9 && grado != 11) return;
            }

            materiaSelect.innerHTML += `
                <option value="${a.id_asignatura}">
                    ${a.nombre}
                </option>`;
        });

    });

    function actualizarValor() {
        if (cursoSelect.value && materiaSelect.value) {
            inputHidden.value = `${materiaSelect.value}-${cursoSelect.value}`;
        }
    }

    cursoSelect.addEventListener("change", actualizarValor);
    materiaSelect.addEventListener("change", actualizarValor);

    // ❌ BOTÓN ELIMINAR
    let btnEliminar = document.createElement("button");
    btnEliminar.innerText = "Eliminar";
    btnEliminar.type = "button";
    btnEliminar.onclick = () => div.remove();

    div.appendChild(cursoSelect);
    div.appendChild(materiaSelect);
    div.appendChild(inputHidden);
    div.appendChild(btnEliminar);

    container.appendChild(div);
}


// 🟣 CARGAR DATOS EXISTENTES
function agregarCargaConDatos(id_asignatura, id_curso) {

    const container = document.getElementById("carga-container");

    const div = document.createElement("div");
    div.classList.add("carga-item");

    let cursoSelect = document.createElement("select");
    let materiaSelect = document.createElement("select");
    let inputHidden = document.createElement("input");

    inputHidden.type = "hidden";
    inputHidden.name = "carga";

    cursos.forEach(c => {
        cursoSelect.innerHTML += `
            <option value="${c.id_curso}" ${c.id_curso == id_curso ? "selected" : ""} data-grado="${c.grado}">
                ${c.grado}°${c.grupo}
            </option>`;
    });

    const cursoElegido = cursos.find(c => c.id_curso == id_curso);

    asignaturas.forEach(a => {

        if (a.nombre.toLowerCase().includes("especialidad")) {
            if (cursoElegido.grado != 9 && cursoElegido.grado != 11) return;
        }

        materiaSelect.innerHTML += `
            <option value="${a.id_asignatura}" ${a.id_asignatura == id_asignatura ? "selected" : ""}>
                ${a.nombre}
            </option>`;
    });

    inputHidden.value = `${id_asignatura}-${id_curso}`;

    function actualizarValor() {
        if (cursoSelect.value && materiaSelect.value) {
            inputHidden.value = `${materiaSelect.value}-${cursoSelect.value}`;
        }
    }

    cursoSelect.addEventListener("change", actualizarValor);
    materiaSelect.addEventListener("change", actualizarValor);

    // ❌ BOTÓN ELIMINAR
    let btnEliminar = document.createElement("button");
    btnEliminar.innerText = "Eliminar";
    btnEliminar.type = "button";
    btnEliminar.onclick = () => div.remove();

    div.appendChild(cursoSelect);
    div.appendChild(materiaSelect);
    div.appendChild(inputHidden);
    div.appendChild(btnEliminar);

    container.appendChild(div);
}


// 🚀 CARGAR AUTOMÁTICAMENTE AL ABRIR
window.onload = () => {
    if (typeof cargasActuales !== "undefined") {
        cargasActuales.forEach(c => {
            agregarCargaConDatos(c.id_asignatura, c.id_curso);
        });
    }
};