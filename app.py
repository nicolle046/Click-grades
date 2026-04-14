from flask import Flask, render_template, request, redirect, url_for, session, jsonify
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

        cursor.execute("SELECT id_usuario FROM usuario WHERE correo = ?", (correo,))
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

            cursor.execute("SELECT id_curso FROM curso WHERE grado=? AND grupo=?", (grado, grupo))
            curso = cursor.fetchone()

            if curso:
                id_curso = curso["id_curso"]
            else:
                cursor.execute("INSERT INTO curso (grado, grupo) VALUES (?, ?)", (grado, grupo))
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

        return render_template("registro.html", mensaje="Usuario registrado exitosamente")

    except sqlite3.Error as e:
        return f"<h3>Error de base de datos: {e}</h3>"


# -----------------------
# LOGIN
# -----------------------

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

            if usuario["rol"] == "estudiante":
                session["nombre"] = usuario["nombre_est"]
            elif usuario["rol"] == "profesor":
                session["nombre"] = usuario["nombre_prof"]
            else:
                session["nombre"] = usuario["nombre_admin"]

            if usuario["rol"] == "admin":
                return redirect(url_for("panel_admin"))
            elif usuario["rol"] == "profesor":
                return redirect(url_for("panel_profesor"))
            else:
                return redirect(url_for("panel_estudiante"))

        else:
            mensaje = "Correo o contraseña no válidos"

    return render_template("login.html", mensaje=mensaje)


# -----------------------
# PANEL PROFESOR
# -----------------------

@app.route("/profesor")
def panel_profesor():
    if "usuario_id" not in session or session["rol"] != "profesor":
        return redirect(url_for("login"))

    return render_template("profesor/panel_profesor.html")


# -----------------------
# PLANILLA
# -----------------------

@app.route("/planilla", methods=["GET", "POST"])
def planilla():

    if "usuario_id" not in session or session["rol"] != "profesor":
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT id_profesor FROM profesor WHERE id_usuario = ?", (session["usuario_id"],))
    prof = cursor.fetchone()

    if not prof:
        conn.close()
        return redirect(url_for("panel_profesor"))

    id_profesor = prof["id_profesor"]

    # cargas del profesor
    cursor.execute("""
        SELECT ca.id_carga, a.nombre AS materia, c.grado, c.grupo
        FROM carga_academica ca
        JOIN asignatura a ON ca.id_asignatura = a.id_asignatura
        JOIN curso c ON ca.id_curso = c.id_curso
        WHERE ca.id_profesor = ?
    """, (id_profesor,))
    cargas = cursor.fetchall()

    estudiantes = []
    encabezados = []
    id_carga = None

    if request.method == "POST":

        id_carga = request.form.get("id_carga")

        # estudiantes
        cursor.execute("""
            SELECT e.id_estudiante, e.nombre, e.apellido
            FROM estudiante e
            WHERE e.id_curso = (
                SELECT id_curso FROM carga_academica WHERE id_carga = ?
            )
            ORDER BY e.apellido, e.nombre
        """, (id_carga,))
        estudiantes_raw = cursor.fetchall()

        # 🔹 encabezados
        cursor.execute("""
            SELECT nombre_columna
            FROM encabezado_notas
            WHERE id_carga = ?
            ORDER BY posicion
        """, (id_carga,))
        encabezados_db = cursor.fetchall()

        if encabezados_db:
            encabezados = [e["nombre_columna"] for e in encabezados_db]
        else:
            encabezados = ["Nota 1", "Nota 2", "Nota 3"]

        # 🔹 notas
        for est in estudiantes_raw:

            cursor.execute("""
                SELECT valor_numerico
                FROM nota
                WHERE id_estudiante = ? AND id_carga = ?
                ORDER BY posicion
            """, (est["id_estudiante"], id_carga))

            notas_db = cursor.fetchall()

            # 🔹 traer promedio guardado
            cursor.execute("""
                SELECT promedio
                FROM promedio_estudiante
                WHERE id_estudiante = ? AND id_carga = ?
            """, (est["id_estudiante"], id_carga))

            prom_db = cursor.fetchone()

            fila = [est["nombre"], est["apellido"]]

            for i in range(len(encabezados)):
                if i < len(notas_db):
                    valor = notas_db[i]["valor_numerico"]

                    if valor == 2.5:
                        fila.append("B")
                    elif valor == 3.5:
                        fila.append("BS")
                    elif valor == 4.3:
                        fila.append("A")
                    elif valor == 4.8:
                        fila.append("S")
                    else:
                        fila.append("")
                else:
                    fila.append("")

            # 🔹 agregar promedio al final
            if prom_db:
                fila.append(prom_db["promedio"])
            else:
                fila.append("")

            estudiantes.append(fila)
        conn.close()

        return render_template(
            "profesor/planilla.html",
            cargas=cargas,
            estudiantes=estudiantes,
            encabezados=encabezados,
            id_carga=id_carga
        )

    conn.close()
    return render_template("profesor/planilla.html", cargas=cargas)

# -----------------------
# GUARDAR NOTAS
# -----------------------

@app.route("/guardar_notas", methods=["POST"])
def guardar_notas():

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    id_carga = data["id_carga"]

    # -------------------------
    # GUARDAR ENCABEZADOS
    # -------------------------
    cursor.execute("DELETE FROM encabezado_notas WHERE id_carga = ?", (id_carga,))

    for i, nombre in enumerate(data["encabezados"]):
        cursor.execute("""
            INSERT INTO encabezado_notas (id_carga, nombre_columna, posicion)
            VALUES (?, ?, ?)
        """, (id_carga, nombre, i))

    # -------------------------
    # GUARDAR NOTAS + PROMEDIO
    # -------------------------
    for est in data["estudiantes"]:

        cursor.execute("""
            SELECT id_estudiante FROM estudiante
            WHERE nombre = ? AND apellido = ?
        """, (est["nombre"], est["apellido"]))

        est_db = cursor.fetchone()
        if not est_db:
            continue

        id_estudiante = est_db["id_estudiante"]

        # borrar notas anteriores
        cursor.execute("""
            DELETE FROM nota
            WHERE id_estudiante = ? AND id_carga = ?
        """, (id_estudiante, id_carga))

        # guardar notas
        for i, nota in enumerate(est["notas"]):

            valor = None
            if nota == "B":
                valor = 2.5
            elif nota == "BS":
                valor = 3.5
            elif nota == "A":
                valor = 4.3
            elif nota == "S":
                valor = 4.8

            cursor.execute("""
                INSERT INTO nota (id_estudiante, id_carga, valor_numerico, posicion)
                VALUES (?, ?, ?, ?)
            """, (id_estudiante, id_carga, valor, i))

        # -------------------------
        # GUARDAR PROMEDIO
        # -------------------------
        cursor.execute("""
            INSERT INTO promedio_estudiante (id_estudiante, id_carga, promedio)
            VALUES (?, ?, ?)
            ON CONFLICT(id_estudiante, id_carga)
            DO UPDATE SET promedio = excluded.promedio
        """, (id_estudiante, id_carga, est["promedio"]))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route('/perfil_p')
def perfil_p():
    if "usuario_id" not in session or session["rol"] != "profesor":
        return redirect(url_for("login"))

    return render_template('profesor/perfil_p.html')

    conn.commit()
    conn.close()

    return jsonify({"mensaje": "Notas guardadas correctamente"})

@app.route("/estudiante")
def panel_estudiante():
    if "usuario_id" not in session or session["rol"] != "estudiante":
        return redirect(url_for("login"))

    return render_template("estudiante/panel_estudiante.html")


@app.route("/admin")
def panel_admin():
    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT u.id_usuario, u.correo, u.rol,
               COALESCE(e.nombre, p.nombre, a.nombre) AS nombre
        FROM usuario u
        LEFT JOIN estudiante e ON u.id_usuario = e.id_usuario
        LEFT JOIN profesor p ON u.id_usuario = p.id_usuario
        LEFT JOIN admin a ON u.id_usuario = a.id_usuario
    """)

    usuarios = cursor.fetchall()
    conn.close()

    return render_template("admin/panel_admin.html", usuarios=usuarios)

@app.route("/admin/editar_usuario/<int:id>", methods=["GET", "POST"])
def editar_usuario(id):

    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # =========================
    # OBTENER USUARIO
    # =========================
    cursor.execute("SELECT * FROM usuario WHERE id_usuario = ?", (id,))
    usuario = cursor.fetchone()

    if not usuario:
        conn.close()
        return redirect(url_for("panel_admin"))

    # =========================
    # OBTENER ID PROFESOR (SI APLICA)
    # =========================
    id_profesor = None

    if usuario["rol"] == "profesor":
        cursor.execute("SELECT id_profesor FROM profesor WHERE id_usuario = ?", (id,))
        prof = cursor.fetchone()

        if prof:
            id_profesor = prof["id_profesor"]

    # =========================
    # OBTENER ASIGNATURAS Y CURSOS
    # =========================
    cursor.execute("SELECT * FROM asignatura")
    asignaturas = [dict(row) for row in cursor.fetchall()]

    cursor.execute("SELECT * FROM curso")
    cursos = [dict(row) for row in cursor.fetchall()]

    # =========================
    # POST (GUARDAR CAMBIOS)
    # =========================
    if request.method == "POST":

        # 🔐 CAMBIAR CONTRASEÑA
        nueva_contrasena = request.form.get("contrasena")
        if nueva_contrasena:
            cursor.execute("""
                UPDATE usuario
                SET contrasena = ?
                WHERE id_usuario = ?
            """, (nueva_contrasena, id))

        # 👨‍🏫 ASIGNAR MATERIAS Y CURSOS
        if usuario["rol"] == "profesor" and id_profesor:

            cargas = request.form.getlist("carga")

            # borrar asignaciones anteriores
            cursor.execute("""
                DELETE FROM carga_academica
                WHERE id_profesor = ?
            """, (id_profesor,))

            # insertar nuevas
            for c in cargas:
                if "-" in c:
                    id_asignatura, id_curso = c.split("-")

                    cursor.execute("""
                        INSERT INTO carga_academica
                        (id_profesor, id_asignatura, id_curso)
                        VALUES (?, ?, ?)
                    """, (id_profesor, id_asignatura, id_curso))

        conn.commit()
        conn.close()

        return redirect(url_for("panel_admin"))
    cargas_actuales = []

    if usuario["rol"] == "profesor" and id_profesor:
        cursor.execute("""
            SELECT id_asignatura, id_curso
            FROM carga_academica
            WHERE id_profesor = ?
        """, (id_profesor,))

        cargas_actuales = [dict(row) for row in cursor.fetchall()]

    conn.close()

    return render_template(
        "admin/editar_usuario.html",
        usuario=usuario,
        asignaturas=asignaturas,
        cursos=cursos,
        cargas_actuales=cargas_actuales
    )

@app.route("/eliminar_usuario/<int:id>")
def eliminar_usuario(id):

    if "usuario_id" not in session or session.get("rol") != "admin":
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    # eliminar usuario (y todo lo relacionado por cascade)
    cursor.execute("DELETE FROM usuario WHERE id_usuario = ?", (id,))

    conn.commit()
    conn.close()

    return redirect(url_for("panel_admin"))


@app.route('/asignaturas')
def asignaturas():
    if "usuario_id" not in session:
        return redirect(url_for("login"))
    
    usuario_id = session["usuario_id"]
    
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                ca.id_carga,
                a.nombre AS asignatura_nombre, 
                p.nombre AS prof_nombre, 
                p.apellido AS prof_apellido,
                pe.promedio
            FROM estudiante e
            JOIN carga_academica ca ON e.id_curso = ca.id_curso
            JOIN asignatura a ON ca.id_asignatura = a.id_asignatura
            JOIN profesor p ON ca.id_profesor = p.id_profesor
            LEFT JOIN promedio_estudiante pe 
                ON pe.id_estudiante = e.id_estudiante 
                AND pe.id_carga = ca.id_carga
            WHERE e.id_usuario = ?
        """, (usuario_id,))
        
        materias = cursor.fetchall()

        # periodo activo
        cursor.execute("SELECT nombre FROM periodo WHERE activo = 1")
        periodo = cursor.fetchone()

    except Exception as e:
        print(f"Error: {e}")
        materias = []
        periodo = None

    finally:
        conn.close()
    
    return render_template(
        'estudiante/asignaturas.html',
        materias=materias,
        periodo=periodo
    )


@app.route('/perfil_e')
def perfil_e():
    return render_template('estudiante/perfil_e.html')

@app.route("/planes_mejoramiento")
def planes_mejoramiento():

    conn = get_db()
    cursor = conn.cursor()

    usuario_id = session.get("usuario_id")

    if not usuario_id:
        return redirect(url_for("login"))

    # obtener estudiante
    cursor.execute("""
        SELECT id_estudiante
        FROM estudiante
        WHERE id_usuario = ?
    """, (usuario_id,))
    
    estudiante = cursor.fetchone()

    if not estudiante:
        conn.close()
        return render_template(
            "estudiante/planes_mejoramiento.html",
            planes=[]
        )

    # obtener planes
    cursor.execute("""
        SELECT 
            pm.contenido,
            pm.fecha,
            t.nombre AS tema,
            a.nombre AS asignatura
        FROM plan_mejoramiento pm
        JOIN tema t ON pm.id_tema = t.id_tema
        JOIN asignatura a ON t.id_asignatura = a.id_asignatura
        WHERE pm.id_estudiante = ?
        ORDER BY pm.fecha DESC
    """, (estudiante["id_estudiante"],))

    planes = cursor.fetchall()

    conn.close()

    return render_template(
        "estudiante/planes_mejoramiento.html",
        planes=planes
    )


@app.route('/mis_estadisticas')
def mis_estadisticas():
    return render_template('estudiante/mis_estadisticas.html')


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route('/ver_materia/<int:id_carga>')
def ver_materia(id_carga):

    if "usuario_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    cursor = conn.cursor()

    usuario_id = session["usuario_id"]

    # 🔥 obtener estudiante
    cursor.execute("""
        SELECT id_estudiante
        FROM estudiante
        WHERE id_usuario = ?
    """, (usuario_id,))
    
    estudiante = cursor.fetchone()

    # 🔥 info materia
    cursor.execute("""
        SELECT 
            a.nombre AS asignatura
        FROM carga_academica ca
        JOIN asignatura a ON ca.id_asignatura = a.id_asignatura
        WHERE ca.id_carga = ?
    """, (id_carga,))
    
    materia = cursor.fetchone()

    # 🔥 ENCABEZADOS (TEMAS REALES)
    cursor.execute("""
        SELECT nombre_columna, posicion
        FROM encabezado_notas
        WHERE id_carga = ?
        ORDER BY posicion
    """, (id_carga,))
    
    encabezados = cursor.fetchall()

    # 🔥 NOTAS
    cursor.execute("""
        SELECT valor_numerico, posicion
        FROM nota
        WHERE id_estudiante = ? AND id_carga = ?
    """, (estudiante["id_estudiante"], id_carga))
    
    notas = cursor.fetchall()

    # 🔥 PROMEDIO
    cursor.execute("""
        SELECT promedio
        FROM promedio_estudiante
        WHERE id_estudiante = ? AND id_carga = ?
    """, (estudiante["id_estudiante"], id_carga))
    
    promedio = cursor.fetchone()

    conn.close()

    return render_template(
        "estudiante/ver_materia.html",
        materia=materia,
        encabezados=encabezados,
        notas=notas,
        promedio=promedio
    )

if __name__ == "__main__":
    app.run(debug=True)