function mostrarCampos() {
    const rol = document.getElementById("rol").value;
    const campos = document.getElementById("campos_estudiante");

    if (campos) {
        campos.style.display = (rol === "estudiante") ? "block" : "none";
    }
}

function volverRegistro() {
    window.location.href = "/";
}

window.onload = function () {
    mostrarCampos();
};
