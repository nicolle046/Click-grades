from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "password_secure"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_db():
    return sqlite3.connect(DB_PATH)


@app.route("/")
def home():
    return render_template("registro.html")


@app.route("/registro", methods=["POST"])
def registro():
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
                id_curso = curso[0]
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

        try:
            conn = get_db()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT id_usuario, rol FROM usuario WHERE correo = ? AND contrasena = ?",
                (correo, contrasena)
            )

            usuario = cursor.fetchone()
            conn.close()

            if usuario:
                session["usuario_id"] = usuario[0]
                session["correo"] = correo
                session["rol"] = usuario[1]

                return redirect(url_for("dashboard"))
            else:
                mensaje = "Correo o contraseña no válidos"

        except sqlite3.Error as e:
            return f"<h3>Error de base de datos: {e}</h3>"

    return render_template("login.html", mensaje=mensaje)


@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    rol = session.get("rol")
    correo = session.get("correo")

    if rol == "estudiante":
        mensaje = "Panel de Estudiante"
    elif rol == "profesor":
        mensaje = "Panel de Profesor"
    else:
        mensaje = "Panel General"

    return f"""
    <h2>{mensaje}</h2>
    <p>Bienvenido</p>
    <a href='/logout'>Cerrar sesión</a>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route ("/dashboard_prof")
def dashboard_prof(): {

}

if __name__ == "__main__":
    app.run(debug=True)

   