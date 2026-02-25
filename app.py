from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "password_secure"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# -----------------------
# HOME
# -----------------------

@app.route("/")
def home():
    return render_template("registro.html")


# -----------------------
# REGISTRO
# -----------------------

@app.route("/registro", methods=["GET", "POST"])
def registro():

    if request.method == "GET":
        return render_template("registro.html")

    nombre = request.form.get("nombre", "").strip()
    apellido = request.form.get("apellido", "").strip()
    correo = request.form.get("correo", "").strip().lower()
    contrasena = request.form.get("contrasena", "")
    rol = request.form.get("rol", "")

    grado = request.form.get("grado")
    grupo = request.form.get("grupo")

    if not correo.endswith("@comfandi.edu.co"):
        return "<h3>Solo se permiten correos institucionales</h3>"

    try:
        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id_usuario FROM usuario WHERE correo = ?",
            (correo,)
        )
        if cursor.fetchone():
            conn.close()
            return "<h3>Este correo ya está registrado</h3>"

        cursor.execute("""
            INSERT INTO usuario (correo, contrasena, rol)
            VALUES (?, ?, ?)
        """, (correo, contrasena, rol))

        id_usuario = cursor.lastrowid

        if rol == "estudiante":

            if not grado or not grupo:
                conn.close()
                return "<h3>Debe seleccionar grado y grupo</h3>"

            cursor.execute(
                "SELECT id_curso FROM curso WHERE grado=? AND grupo=?",
                (grado, grupo)
            )
            curso = cursor.fetchone()

            if curso:
                id_curso = curso["id_curso"]
            else:
                cursor.execute(
                    "INSERT INTO curso (grado, grupo) VALUES (?, ?)",
                    (grado, grupo)
                )
                id_curso = cursor.lastrowid

            cursor.execute("""
                INSERT INTO estudiante (id_usuario, nombre, apellido, id_curso)
                VALUES (?, ?, ?, ?)
            """, (id_usuario, nombre, apellido, id_curso))

        elif rol == "profesor":

            cursor.execute("""
                INSERT INTO profesor (id_usuario, nombre, apellido)
                VALUES (?, ?, ?)
            """, (id_usuario, nombre, apellido))

        else:
            conn.close()
            return "<h3>Rol no válido</h3>"

        conn.commit()
        conn.close()

        return render_template(
            "registro.html",
            mensaje="Usuario registrado exitosamente"
        )

    except sqlite3.Error as e:
        return f"<h3>Error de base de datos: {e}</h3>"

@app.route("/login", methods=["GET", "POST"])
def login():
    mensaje = None

    if request.method == "POST":
        correo = request.form.get("correo", "").strip()
        contrasena = request.form.get("contrasena", "")

        conn = get_db()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT u.id_usuario, u.rol, p.nombre
            FROM usuario u
            LEFT JOIN profesor p ON u.id_usuario = p.id_usuario
            WHERE u.correo = ? AND u.contrasena = ?
            """,
            (correo, contrasena)
        )

        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session["usuario_id"] = usuario["id_usuario"]
            session["correo"] = correo
            session["rol"] = usuario["rol"]
            session["nombre"] = usuario["nombre"]

            if usuario["rol"] == "profesor":
                return redirect(url_for("panel_profesor"))
            elif usuario["rol"] == "estudiante":
                return redirect(url_for("panel_estudiante"))
            else:
                return redirect(url_for("login"))
        else:
            mensaje = "Correo o contraseña no válidos"

    return render_template("login.html", mensaje=mensaje)

@app.route("/profesor")
def panel_profesor():

    if "usuario_id" not in session or session["rol"] != "profesor":
        return redirect(url_for("login"))

    return render_template("profesor/panel_profesor.html")


@app.route("/estudiante")
def panel_estudiante():

    if "usuario_id" not in session or session["rol"] != "estudiante":
        return redirect(url_for("login"))

    return render_template("estudiante/panel_estudiante.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)