import sqlite3
import os

print ("RUTA REAL DE LA BASE:")
print (os.path.abspath("database.db"))


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.executescript("""
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS plan_mejoramiento;
DROP TABLE IF EXISTS nota;
DROP TABLE IF EXISTS tema;
DROP TABLE IF EXISTS periodo;
DROP TABLE IF EXISTS profesor_asignatura;
DROP TABLE IF EXISTS asignatura;
DROP TABLE IF EXISTS estudiante;
DROP TABLE IF EXISTS profesor;
DROP TABLE IF EXISTS curso;
DROP TABLE IF EXISTS usuario;

CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    correo TEXT UNIQUE NOT NULL,
    contrasena TEXT NOT NULL,
    rol TEXT NOT NULL CHECK (rol IN ('estudiante', 'profesor', 'admin'))
);

CREATE TABLE curso (
    id_curso INTEGER PRIMARY KEY AUTOINCREMENT,
    grado TEXT NOT NULL,
    grupo TEXT NOT NULL
);

CREATE TABLE estudiante (
    id_estudiante INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    id_curso INTEGER NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario),
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso)
);

CREATE TABLE profesor (
    id_profesor INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario)
);

CREATE TABLE asignatura (
    id_asignatura INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

CREATE TABLE profesor_asignatura (
    id_profesor INTEGER NOT NULL,
    id_asignatura INTEGER NOT NULL,
    id_curso INTEGER NOT NULL,
    PRIMARY KEY (id_profesor, id_asignatura, id_curso),
    FOREIGN KEY (id_profesor) REFERENCES profesor(id_profesor),
    FOREIGN KEY (id_asignatura) REFERENCES asignatura(id_asignatura),
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso)
);

CREATE TABLE periodo (
    id_periodo INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

CREATE TABLE tema (
    id_tema INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    id_asignatura INTEGER NOT NULL,
    id_periodo INTEGER NOT NULL,
    FOREIGN KEY (id_asignatura) REFERENCES asignatura(id_asignatura),
    FOREIGN KEY (id_periodo) REFERENCES periodo(id_periodo)
);

CREATE TABLE nota (
    id_nota INTEGER PRIMARY KEY AUTOINCREMENT,
    valor TEXT NOT NULL CHECK (valor IN ('Bajo', 'Basico', 'Alto', 'Superior')),
    id_estudiante INTEGER NOT NULL,
    id_tema INTEGER NOT NULL,
    id_profesor INTEGER NOT NULL,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante),
    FOREIGN KEY (id_tema) REFERENCES tema(id_tema),
    FOREIGN KEY (id_profesor) REFERENCES profesor(id_profesor)
);

CREATE TABLE plan_mejoramiento (
    id_plan INTEGER PRIMARY KEY AUTOINCREMENT,
    id_estudiante INTEGER NOT NULL,
    id_tema INTEGER NOT NULL,
    contenido TEXT NOT NULL,
    generado_por_ia INTEGER DEFAULT 1,
    fecha TEXT NOT NULL,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante),
    FOREIGN KEY (id_tema) REFERENCES tema(id_tema)
);
""")

conn.commit()
conn.close()

print("Base de datos COMPLETA creada correctamente")
