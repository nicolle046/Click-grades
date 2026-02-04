function mostrarCampos() {
    const rol = document.getElementById("rol").value;
    const campos = document.getElementById("campos_estudiante");

    if (campos) {
        campos.style.display = (rol === "estudiante") ? "flex" : "none";
    }
}

function volverRegistro() {
    window.location.href = "/";
}

/* ALERTA FLOTANTE */
function mostrarAlertaCorreo() {
    const alerta = document.getElementById("alerta-correo");
    alerta.classList.add("mostrar");

    setTimeout(() => {
        alerta.classList.remove("mostrar");
    }, 3000);
}

/* VALIDACIÓN CORREO INSTITUCIONAL */
document.addEventListener("DOMContentLoaded", function () {
    mostrarCampos();

    const form = document.querySelector(".formulario");

    if (form) {
        form.addEventListener("submit", function (e) {
            const correo = document.querySelector('input[name="correo"]').value;

            // CAMBIA ESTE DOMINIO AL REAL DE TU COLEGIO
            if (!correo.endsWith("@colegio.edu.co")) {
                e.preventDefault();
                mostrarAlertaCorreo();
            }
        });
    }
});
