import sqlite3
import os

print("RUTA REAL DE LA BASE:")
print(os.path.abspath("database.db"))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.executescript("""
PRAGMA foreign_keys = ON;

DROP TABLE IF EXISTS ultima_materia_abierta;
DROP TABLE IF EXISTS plan_mejoramiento;
DROP TABLE IF EXISTS nota;
DROP TABLE IF EXISTS tema;
DROP TABLE IF EXISTS carga_academica;
DROP TABLE IF EXISTS periodo;
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

CREATE TABLE profesor (
    id_profesor INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE
);

CREATE TABLE estudiante (
    id_estudiante INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL UNIQUE,
    nombre TEXT NOT NULL,
    apellido TEXT NOT NULL,
    id_curso INTEGER NOT NULL,
    FOREIGN KEY (id_usuario) REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso)
);

CREATE TABLE asignatura (
    id_asignatura INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL
);

-- TABLA CLAVE
CREATE TABLE carga_academica (
    id_carga INTEGER PRIMARY KEY AUTOINCREMENT,
    id_profesor INTEGER NOT NULL,
    id_asignatura INTEGER NOT NULL,
    id_curso INTEGER NOT NULL,
    FOREIGN KEY (id_profesor) REFERENCES profesor(id_profesor),
    FOREIGN KEY (id_asignatura) REFERENCES asignatura(id_asignatura),
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso),
    UNIQUE(id_profesor, id_asignatura, id_curso)
);

-- NUEVA TABLA PARA RECORDAR ÚLTIMA MATERIA ABIERTA
CREATE TABLE ultima_materia_abierta (
    id_profesor INTEGER NOT NULL,
    id_curso INTEGER NOT NULL,
    id_carga INTEGER NOT NULL,
    PRIMARY KEY (id_profesor, id_curso),
    FOREIGN KEY (id_profesor) REFERENCES profesor(id_profesor) ON DELETE CASCADE,
    FOREIGN KEY (id_curso) REFERENCES curso(id_curso) ON DELETE CASCADE,
    FOREIGN KEY (id_carga) REFERENCES carga_academica(id_carga) ON DELETE CASCADE
);

CREATE TABLE periodo (
    id_periodo INTEGER PRIMARY KEY AUTOINCREMENT,
    numero INTEGER NOT NULL CHECK (numero BETWEEN 1 AND 4),
    nombre TEXT NOT NULL,
    fecha_inicio TEXT,
    fecha_fin TEXT,
    activo INTEGER DEFAULT 0 CHECK (activo IN (0,1)),
    cerrado INTEGER DEFAULT 0 CHECK (cerrado IN (0,1))
);

INSERT INTO periodo (numero, nombre, activo, cerrado) VALUES
(1, 'Periodo 1', 1, 0),
(2, 'Periodo 2', 0, 0),
(3, 'Periodo 3', 0, 0),
(4, 'Periodo 4', 0, 0);

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
    valor_numerico REAL NOT NULL CHECK (valor_numerico >= 1 AND valor_numerico <= 5),
    id_estudiante INTEGER NOT NULL,
    id_carga INTEGER NOT NULL,
    id_tema INTEGER NOT NULL,
    FOREIGN KEY (id_estudiante) REFERENCES estudiante(id_estudiante),
    FOREIGN KEY (id_carga) REFERENCES carga_academica(id_carga),
    FOREIGN KEY (id_tema) REFERENCES tema(id_tema)
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

print("Base de datos PROFESIONAL creada correctamente")