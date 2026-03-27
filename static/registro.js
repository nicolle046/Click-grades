function mostrarCampos() {
    const rol = document.getElementById("rol").value;
    const camposEstudiante = document.getElementById("campos_estudiante");

    if (rol === "estudiante") {
        camposEstudiante.style.display = "flex";
    } else {
        camposEstudiante.style.display = "none";
    }
}

function volverRegistro() {
    window.location.href = "/";
}

/* alerta flotante */
function mostrarAlertaCorreo() {
    const alerta = document.getElementById("alerta-correo");
    alerta.classList.add("mostrar");

    setTimeout(() => {
        alerta.classList.remove("mostrar");
    }, 3000);
}

/* para validar correo institucional */
document.addEventListener("DOMContentLoaded", function () {
    mostrarCampos();

    const form = document.querySelector(".formulario");

    if (form) {
        form.addEventListener("submit", function (e) {
            const correo = document.querySelector('input[name="correo"]').value;

            if (!correo.toLowerCase().endsWith("@comfandi.edu.co")) {
                e.preventDefault();
                mostrarAlertaCorreo();
            }
        });
    }
});
