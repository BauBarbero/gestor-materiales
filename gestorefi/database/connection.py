"""
connection.py — GestorEFi
Módulo encargado de la conexión, inicialización y semilla de la base de datos SQLite.
Crea automáticamente el archivo 'gestor_efi.db' y todas las tablas en la primera ejecución.
"""

import sqlite3
import hashlib
import os
from pathlib import Path

# Ruta del archivo de base de datos (en el mismo directorio que este módulo)
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "gestor_efi.db"


def hash_password(password: str) -> str:
    """Genera un hash SHA-256 de la contraseña proporcionada (función pública)."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


# Alias interno para mantener compatibilidad con llamadas previas en este módulo
_hash_password = hash_password


def get_connection() -> sqlite3.Connection:
    """
    Retorna una conexión activa a la base de datos SQLite.
    Activa soporte de claves foráneas en cada conexión.
    """
    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.row_factory = sqlite3.Row  # Permite acceso a columnas por nombre
        return conn
    except sqlite3.Error as e:
        raise RuntimeError(f"No se pudo conectar a la base de datos: {e}")


def _crear_tablas(conn: sqlite3.Connection) -> None:
    """Ejecuta las sentencias DDL para crear todas las tablas si no existen."""
    cursor = conn.cursor()

    # ─── Tabla: categorias ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
    """)

    # ─── Tabla: materiales ──────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS materiales (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre           TEXT    NOT NULL,
            categoria        TEXT    NOT NULL,
            stock_total      INTEGER NOT NULL CHECK(stock_total >= 0),
            stock_disponible INTEGER NOT NULL CHECK(stock_disponible >= 0),
            estado           TEXT    NOT NULL DEFAULT 'Bueno'
                                CHECK(estado IN ('Nuevo', 'Bueno', 'Gastado', 'Inutilizable'))
        );
    """)

    # ─── Tabla: prestamos ───────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prestamos (
            id               INTEGER  PRIMARY KEY AUTOINCREMENT,
            material_id      INTEGER  NOT NULL REFERENCES materiales(id),
            alumno_nombre    TEXT     NOT NULL,
            curso_division   TEXT     NOT NULL,
            fecha_salida     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_devolucion DATETIME NULL,
            estado           TEXT     NOT NULL DEFAULT 'Activo'
                                CHECK(estado IN ('Activo', 'Devuelto', 'No Devuelto'))
        );
    """)

    # ─── Tabla: historial_bajas ─────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historial_bajas (
            id                   INTEGER  PRIMARY KEY AUTOINCREMENT,
            material_id          INTEGER  NOT NULL REFERENCES materiales(id),
            cantidad             INTEGER  NOT NULL CHECK(cantidad > 0),
            motivo               TEXT     NOT NULL
                                    CHECK(motivo IN ('Rotura', 'Pérdida', 'Robado')),
            responsable_registro TEXT     NOT NULL,
            fecha                DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # ─── Tabla: usuarios ────────────────────────────────────────────────────
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            username      TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            rol           TEXT    NOT NULL
                            CHECK(rol IN ('ADMIN', 'CONSULTA'))
        );
    """)

    conn.commit()


def _insertar_datos_semilla(conn: sqlite3.Connection) -> None:
    """
    Inserta usuarios y materiales iniciales solo si las tablas están vacías.
    Las contraseñas se almacenan como hashes SHA-256.
    """
    cursor = conn.cursor()

    # ── Usuarios por defecto ─────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM usuarios;")
    if cursor.fetchone()[0] == 0:
        usuarios_semilla = [
            # (username, contraseña en texto plano, rol)
            ("admin",  "admin123", "ADMIN"),    # Docente / Administrador
            ("recreo", "recreo",   "CONSULTA"), # Acceso general sin contraseña compleja
        ]
        for username, password, rol in usuarios_semilla:
            cursor.execute(
                "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?);",
                (username, _hash_password(password), rol)
            )
        print("[DB] Usuarios semilla creados: 'admin' (ADMIN) y 'recreo' (CONSULTA).")

    # ── Materiales de ejemplo ────────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM materiales;")
    if cursor.fetchone()[0] == 0:
        materiales_semilla = [
            # (nombre, categoria, stock_total, stock_disponible, estado)
            ("Pelota de Fútbol N°5",     "Pelotas",      8,  8,  "Bueno"),
            ("Pelota de Básquet N°7",    "Pelotas",      4,  4,  "Bueno"),
            ("Pelota de Vóley",          "Pelotas",      3,  3,  "Nuevo"),
            ("Pelota de Rugby",          "Pelotas",      2,  2,  "Gastado"),
            ("Cono Naranja Mediano",     "Conos",       20, 20,  "Bueno"),
            ("Cono Amarillo Pequeño",    "Conos",       15, 15,  "Bueno"),
            ("Colchoneta Azul Grande",   "Colchonetas",  6,  6,  "Bueno"),
            ("Colchoneta Roja Pequeña",  "Colchonetas",  4,  4,  "Gastado"),
            ("Pechera Roja (talle M)",   "Indumentaria", 10, 10, "Bueno"),
            ("Pechera Azul (talle M)",   "Indumentaria", 10, 10, "Bueno"),
            ("Soga de Saltar",           "Indumentaria",  5,  5, "Bueno"),
        ]
        cursor.executemany(
            """INSERT INTO materiales
               (nombre, categoria, stock_total, stock_disponible, estado)
               VALUES (?, ?, ?, ?, ?);""",
            materiales_semilla
        )
        print(f"[DB] {len(materiales_semilla)} materiales semilla insertados.")

    # ── Categorías por defecto ───────────────────────────────────────────────
    cursor.execute("SELECT COUNT(*) FROM categorias;")
    if cursor.fetchone()[0] == 0:
        categorias_base = ["Pelotas", "Conos", "Indumentaria", "Colchonetas"]
        for cat in categorias_base:
            cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?);", (cat,))
        print("[DB] Categorías base insertadas.")

    conn.commit()


def _migrar_si_es_necesario(conn: sqlite3.Connection) -> None:
    """Migra tablas existentes si aún tienen restricciones obsoletas."""
    cursor = conn.cursor()
    # 1. Asegurar categorías base en la tabla 'categorias'
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id     INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE NOT NULL
        );
    """)
    categorias_base = ["Pelotas", "Conos", "Indumentaria", "Colchonetas"]
    for cat in categorias_base:
        cursor.execute("INSERT OR IGNORE INTO categorias (nombre) VALUES (?);", (cat,))

    # 2. Migrar 'materiales' si tiene la restricción CHECK de categorías fija
    row = cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='materiales';").fetchone()
    if row and "CHECK(categoria IN" in row[0]:
        conn.commit()
        # Conexión dedicada sin claves foráneas para la recreación segura
        conn_migr = sqlite3.connect(str(DB_PATH))
        conn_migr.execute("PRAGMA foreign_keys = OFF;")
        cur_migr = conn_migr.cursor()
        cur_migr.execute("""
            CREATE TABLE materiales_temp (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre           TEXT    NOT NULL,
                categoria        TEXT    NOT NULL,
                stock_total      INTEGER NOT NULL CHECK(stock_total >= 0),
                stock_disponible INTEGER NOT NULL CHECK(stock_disponible >= 0),
                estado           TEXT    NOT NULL DEFAULT 'Bueno'
                                    CHECK(estado IN ('Nuevo', 'Bueno', 'Gastado', 'Inutilizable'))
            );
        """)
        cur_migr.execute("INSERT INTO materiales_temp SELECT * FROM materiales;")
        cur_migr.execute("DROP TABLE materiales;")
        cur_migr.execute("ALTER TABLE materiales_temp RENAME TO materiales;")
        conn_migr.commit()
        conn_migr.close()
        print("[DB] Migración aplicada: 'materiales' ahora admite categorías dinámicas.")


def inicializar_base_de_datos() -> None:
    """
    Punto de entrada principal del módulo.
    Crea la base de datos, las tablas y los datos semilla si es la primera ejecución.
    """
    primera_vez = not DB_PATH.exists()

    try:
        conn = get_connection()
        _crear_tablas(conn)
        _migrar_si_es_necesario(conn)
        _insertar_datos_semilla(conn)
        conn.close()

        if primera_vez:
            print(f"[DB] Base de datos creada en: {DB_PATH}")
        else:
            print(f"[DB] Conexión exitosa con: {DB_PATH}")

    except sqlite3.Error as e:
        raise RuntimeError(f"Error al inicializar la base de datos: {e}")


# Permite ejecutar este módulo directamente para pruebas rápidas
if __name__ == "__main__":
    inicializar_base_de_datos()
    print("[DB] Inicialización completada correctamente.")
