"""
queries.py — GestorEFi
Colección centralizada de consultas SQL preparadas para todas las operaciones de la app.
NUNCA se concatenan variables directamente en strings SQL: se usan tuplas con '?' para
evitar inyecciones SQL.
"""

import sqlite3
from datetime import datetime
from database.connection import get_connection, hash_password


# ═══════════════════════════════════════════════════════════════════════════════
# USUARIOS
# ═══════════════════════════════════════════════════════════════════════════════

def autenticar_usuario(username: str, password: str) -> sqlite3.Row | None:
    """
    Verifica las credenciales del usuario contra la tabla 'usuarios'.
    Usa hashlib.sha256 para comparar el hash almacenado.
    Retorna el registro (sqlite3.Row) si son correctas, o None en caso contrario.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM usuarios WHERE username = ? AND password_hash = ?;",
            (username, hash_password(password))
        )
        usuario = cursor.fetchone()
        conn.close()
        return usuario
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al autenticar usuario: {e}")


def verificar_credenciales(username: str, password: str) -> dict | None:
    """
    Función auxiliar de autenticación para consumo directo por la capa GUI.
    Retorna un diccionario {'id', 'username', 'rol'} si las credenciales
    son válidas, o None si el usuario no existe o la contraseña es incorrecta.
    No expone el hash de contraseña a la interfaz.
    """
    try:
        row = autenticar_usuario(username, password)
        if row is None:
            return None
        return {
            "id":       row["id"],
            "username": row["username"],
            "rol":      row["rol"],
        }
    except RuntimeError:
        raise


def obtener_todos_los_usuarios() -> list[sqlite3.Row]:
    """Retorna todos los usuarios registrados (sin incluir el hash de contraseña en la vista)."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, rol FROM usuarios ORDER BY username;")
        usuarios = cursor.fetchall()
        conn.close()
        return usuarios
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener usuarios: {e}")


def crear_usuario(username: str, password: str, rol: str) -> None:
    """Registra un nuevo usuario en el sistema (solo ADMIN)."""
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO usuarios (username, password_hash, rol) VALUES (?, ?, ?);",
            (username, hash_password(password), rol)
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        raise ValueError(f"El nombre de usuario '{username}' ya existe.")
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al crear usuario: {e}")


def cambiar_password(usuario_id: int, nueva_password: str) -> None:
    """Actualiza la contraseña de un usuario con hash SHA-256 (solo ADMIN)."""
    if not nueva_password or not nueva_password.strip():
        raise ValueError("La nueva contraseña no puede estar vacía.")
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE usuarios SET password_hash = ? WHERE id = ?;",
            (hash_password(nueva_password), usuario_id)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al cambiar contraseña: {e}")


def eliminar_usuario(usuario_id: int) -> None:
    """Elimina un usuario por su ID (solo ADMIN)."""
    try:
        conn = get_connection()
        conn.execute("DELETE FROM usuarios WHERE id = ?;", (usuario_id,))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al eliminar usuario: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MATERIALES Y CATEGORÍAS
# ═══════════════════════════════════════════════════════════════════════════════

def obtener_categorias() -> list[str]:
    """
    Retorna la lista ordenada de todas las categorías disponibles.
    Combina la tabla 'categorias' y cualquier categoría existente en 'materiales'.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT nombre FROM categorias
            UNION
            SELECT DISTINCT categoria AS nombre FROM materiales
            WHERE categoria IS NOT NULL AND categoria != ''
            ORDER BY nombre COLLATE NOCASE ASC;
        """)
        filas = cursor.fetchall()
        conn.close()
        return [f["nombre"] for f in filas if f["nombre"]]
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener categorías: {e}")


def crear_categoria(nombre: str) -> None:
    """Registra una nueva categoría en la base de datos (solo ADMIN)."""
    nombre_limpio = nombre.strip()
    if not nombre_limpio:
        raise ValueError("El nombre de la categoría no puede estar vacío.")
    try:
        conn = get_connection()
        conn.execute(
            "INSERT INTO categorias (nombre) VALUES (?);",
            (nombre_limpio,)
        )
        conn.commit()
        conn.close()
    except sqlite3.IntegrityError:
        raise ValueError(f"La categoría '{nombre_limpio}' ya existe.")
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al crear categoría: {e}")


def obtener_materiales(categoria: str = None, nombre: str = None) -> list[sqlite3.Row]:
    """
    Retorna materiales con filtros opcionales por categoría y/o nombre (búsqueda parcial).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = "SELECT * FROM materiales WHERE 1=1"
        params = []

        if categoria:
            query += " AND categoria = ?"
            params.append(categoria)
        if nombre:
            query += " AND nombre LIKE ?"
            params.append(f"%{nombre}%")

        query += " ORDER BY categoria, nombre;"
        cursor.execute(query, params)
        materiales = cursor.fetchall()
        conn.close()
        return materiales
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener materiales: {e}")


def obtener_material_por_id(material_id: int) -> sqlite3.Row | None:
    """Retorna un material por su ID, o None si no existe."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM materiales WHERE id = ?;", (material_id,))
        material = cursor.fetchone()
        conn.close()
        return material
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener material: {e}")


def crear_material(nombre: str, categoria: str, stock_total: int, estado: str = "Nuevo") -> None:
    """Agrega un nuevo material al inventario (solo ADMIN)."""
    try:
        conn = get_connection()
        conn.execute(
            """INSERT INTO materiales (nombre, categoria, stock_total, stock_disponible, estado)
               VALUES (?, ?, ?, ?, ?);""",
            (nombre, categoria, stock_total, stock_total, estado)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al crear material: {e}")


def actualizar_material(material_id: int, nombre: str, categoria: str,
                        stock_total: int, estado: str) -> None:
    """Actualiza los datos de un material existente (solo ADMIN)."""
    try:
        conn = get_connection()
        conn.execute(
            """UPDATE materiales
               SET nombre = ?, categoria = ?, stock_total = ?, estado = ?
               WHERE id = ?;""",
            (nombre, categoria, stock_total, estado, material_id)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al actualizar material: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# PRÉSTAMOS
# ═══════════════════════════════════════════════════════════════════════════════

def registrar_prestamo(material_id: int, alumno_nombre: str, curso_division: str) -> None:
    """
    Registra un préstamo rápido de recreo y descuenta 1 del stock_disponible.
    Lanza ValueError si no hay stock disponible.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Verificar stock disponible antes de prestar
        cursor.execute(
            "SELECT stock_disponible FROM materiales WHERE id = ?;",
            (material_id,)
        )
        fila = cursor.fetchone()
        if not fila or fila["stock_disponible"] < 1:
            conn.close()
            raise ValueError("No hay stock disponible para este material.")

        # Insertar préstamo y descontar stock en una única transacción
        cursor.execute(
            """INSERT INTO prestamos (material_id, alumno_nombre, curso_division)
               VALUES (?, ?, ?);""",
            (material_id, alumno_nombre, curso_division)
        )
        cursor.execute(
            "UPDATE materiales SET stock_disponible = stock_disponible - 1 WHERE id = ?;",
            (material_id,)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al registrar préstamo: {e}")


def registrar_devolucion(prestamo_id: int) -> None:
    """
    Marca un préstamo como 'Devuelto' y repone 1 al stock_disponible del material.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener el material_id del préstamo
        cursor.execute(
            "SELECT material_id, estado FROM prestamos WHERE id = ?;",
            (prestamo_id,)
        )
        prestamo = cursor.fetchone()
        if not prestamo:
            conn.close()
            raise ValueError("El préstamo indicado no existe.")
        if prestamo["estado"] != "Activo":
            conn.close()
            raise ValueError("El préstamo ya fue cerrado anteriormente.")

        fecha_devolucion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """UPDATE prestamos
               SET estado = 'Devuelto', fecha_devolucion = ?
               WHERE id = ?;""",
            (fecha_devolucion, prestamo_id)
        )
        cursor.execute(
            "UPDATE materiales SET stock_disponible = stock_disponible + 1 WHERE id = ?;",
            (prestamo["material_id"],)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al registrar devolución: {e}")


def obtener_prestamos_activos() -> list[sqlite3.Row]:
    """Retorna todos los préstamos en estado 'Activo' con el nombre del material."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT p.id, m.nombre AS material, p.alumno_nombre,
                      p.curso_division, p.fecha_salida
               FROM prestamos p
               JOIN materiales m ON p.material_id = m.id
               WHERE p.estado = 'Activo'
               ORDER BY p.fecha_salida DESC;"""
        )
        prestamos = cursor.fetchall()
        conn.close()
        return prestamos
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener préstamos activos: {e}")


def marcar_prestamo_no_devuelto(prestamo_id: int) -> None:
    """Marca un préstamo como 'No Devuelto' (pérdida o robo) sin reponer stock."""
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE prestamos SET estado = 'No Devuelto' WHERE id = ?;",
            (prestamo_id,)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al marcar préstamo como no devuelto: {e}")


def obtener_todos_los_prestamos(filtro_estado: str = None, busqueda: str = None) -> list[sqlite3.Row]:
    """
    Retorna el historial completo de préstamos (activos, devueltos y no devueltos).
    Soporta filtros parametrizados por estado y por término de búsqueda.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        query = """
            SELECT p.id, m.nombre AS material, p.alumno_nombre,
                   p.curso_division, p.fecha_salida, p.fecha_devolucion, p.estado
            FROM prestamos p
            JOIN materiales m ON p.material_id = m.id
            WHERE 1=1
        """
        params = []
        if filtro_estado and filtro_estado != "Todos":
            query += " AND p.estado = ?"
            params.append(filtro_estado)
        if busqueda:
            query += " AND (m.nombre LIKE ? OR p.alumno_nombre LIKE ? OR p.curso_division LIKE ?)"
            patron = f"%{busqueda.strip()}%"
            params.extend([patron, patron, patron])

        query += " ORDER BY p.fecha_salida DESC;"
        cursor.execute(query, params)
        prestamos = cursor.fetchall()
        conn.close()
        return prestamos
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener historial de préstamos: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# HISTORIAL DE BAJAS
# ═══════════════════════════════════════════════════════════════════════════════

def registrar_baja(material_id: int, cantidad: int,
                   motivo: str, responsable: str) -> None:
    """
    Registra una baja definitiva (rotura/pérdida/robo) y descuenta del stock total y disponible.
    Solo accesible para rol ADMIN.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT stock_total, stock_disponible FROM materiales WHERE id = ?;",
            (material_id,)
        )
        fila = cursor.fetchone()
        if not fila:
            conn.close()
            raise ValueError("Material no encontrado.")
        if fila["stock_disponible"] < cantidad:
            conn.close()
            raise ValueError(
                f"No se pueden dar de baja {cantidad} unidades: "
                f"solo hay {fila['stock_disponible']} disponibles."
            )

        cursor.execute(
            """INSERT INTO historial_bajas (material_id, cantidad, motivo, responsable_registro)
               VALUES (?, ?, ?, ?);""",
            (material_id, cantidad, motivo, responsable)
        )
        cursor.execute(
            """UPDATE materiales
               SET stock_total      = stock_total      - ?,
                   stock_disponible = stock_disponible - ?
               WHERE id = ?;""",
            (cantidad, cantidad, material_id)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al registrar baja: {e}")


def obtener_historial_bajas() -> list[sqlite3.Row]:
    """Retorna todo el historial de bajas con el nombre del material correspondiente."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT b.id, m.nombre AS material, b.cantidad, b.motivo,
                      b.responsable_registro, b.fecha
               FROM historial_bajas b
               JOIN materiales m ON b.material_id = m.id
               ORDER BY b.fecha DESC;"""
        )
        bajas = cursor.fetchall()
        conn.close()
        return bajas
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al obtener historial de bajas: {e}")


def revertir_baja(baja_id: int) -> None:
    """
    Anula un registro de baja y reintegra automáticamente las unidades
    al stock_total y stock_disponible del material en una única transacción (solo ADMIN).
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Obtener los datos de la baja a revertir
        cursor.execute(
            "SELECT material_id, cantidad FROM historial_bajas WHERE id = ?;",
            (baja_id,)
        )
        baja = cursor.fetchone()
        if not baja:
            conn.close()
            raise ValueError("El registro de baja no existe o ya fue anulado.")

        material_id = baja["material_id"]
        cantidad = baja["cantidad"]

        # Reintegrar stock y eliminar registro en transacción atómica
        cursor.execute(
            """UPDATE materiales
               SET stock_total      = stock_total      + ?,
                   stock_disponible = stock_disponible + ?
               WHERE id = ?;""",
            (cantidad, cantidad, material_id)
        )
        cursor.execute(
            "DELETE FROM historial_bajas WHERE id = ?;",
            (baja_id,)
        )
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        raise RuntimeError(f"Error al revertir baja: {e}")
