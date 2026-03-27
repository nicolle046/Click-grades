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

        # 🔥 AQUÍ VA TODO BIEN INDENTADO

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

        elif rol == "admin":

            cursor.execute("""
                INSERT INTO admin (id_usuario, nombre, apellido)
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

        cursor.execute("""
            SELECT u.id_usuario, u.rol,
                   e.nombre AS nombre_est,
                   p.nombre AS nombre_prof,
                   a.nombre AS nombre_admin
            FROM usuario u
            LEFT JOIN estudiante e ON u.id_usuario = e.id_usuario
            LEFT JOIN profesor p ON u.id_usuario = p.id_usuario
            LEFT JOIN admin a ON u.id_usuario = a.id_usuario
            WHERE u.correo = ? AND u.contrasena = ?
        """, (correo, contrasena))

        usuario = cursor.fetchone()
        conn.close()

        if usuario:
            session["usuario_id"] = usuario["id_usuario"]
            session["correo"] = correo
            session["rol"] = usuario["rol"]

            # 🔥 TODO ESTO VA DENTRO
            if usuario["rol"] == "estudiante":
                session["nombre"] = usuario["nombre_est"]
            elif usuario["rol"] == "profesor":
                session["nombre"] = usuario["nombre_prof"]
            else:
                session["nombre"] = usuario["nombre_admin"]

            # 🔥 REDIRECCIONES
            if usuario["rol"] == "admin":
                return redirect(url_for("panel_admin"))
            elif usuario["rol"] == "profesor":
                return redirect(url_for("panel_profesor"))
            else:
                return redirect(url_for("panel_estudiante"))

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

@app.route('/mis_cursos')
def mis_cursos():
    return render_template('profesor/mis_cursos.html')


@app.route('/reportes')
def reportes():
    return render_template('profesor/reportes.html')


@app.route('/perfil_p')
def perfil_p():
    return render_template('profesor/perfil_p.html')


@app.route("/admin")
def panel_admin():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("login"))

    filtro = request.args.get("rol", "")
    busqueda = request.args.get("busqueda", "")

    conn = get_db()
    cursor = conn.cursor()

    query = """
    SELECT u.id_usuario, u.correo, u.rol,
           COALESCE(e.nombre, p.nombre, a.nombre, 'Sin nombre') AS nombre,
           COALESCE(e.apellido, p.apellido, a.apellido, '') AS apellido
    FROM usuario u
    LEFT JOIN estudiante e ON u.id_usuario = e.id_usuario
    LEFT JOIN profesor p ON u.id_usuario = p.id_usuario
    LEFT JOIN admin a ON u.id_usuario = a.id_usuario
    WHERE 1=1
    """

    params = []

    if filtro:
        query += " AND u.rol = ?"
        params.append(filtro)

    if busqueda:
        query += """
        AND (
            u.correo LIKE ?
            OR e.nombre LIKE ?
            OR p.nombre LIKE ?
        )
        """
        params.extend([f"%{busqueda}%", f"%{busqueda}%", f"%{busqueda}%"])

    cursor.execute(query, params)
    usuarios = cursor.fetchall()

    conn.close()

    return render_template("panel_admin.html", usuarios=usuarios)


@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):
    if session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("panel_admin"))
    
@app.route('/asignaturas')
def asignaturas():
    return render_template('estudiante/asignaturas.html')

@app.route('/mis_estadisticas')
def mis_estadisticas():
    return render_template('estudiante/mis_estadisticas.html')

@app.route('/planes_mejoramiento')
def planes_mejoramiento():
    return render_template('estudiante/planes_mejoramiento.html')

@app.route('/perfil_e')
def perfil_e():
    return render_template('estudiante/perfil_e.html')

if __name__ == "__main__":
    app.run(debug=True)