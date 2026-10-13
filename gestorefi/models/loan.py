"""
loan.py — GestorEFi
Modelo de negocio para la entidad Préstamo (Prestamo).
Encapsula la lógica de validación y representación de un préstamo de recreo.
"""

from dataclasses import dataclass
from datetime import datetime


# Estados válidos de un préstamo
ESTADOS_PRESTAMO: list[str] = ["Activo", "Devuelto", "No Devuelto"]


@dataclass
class Prestamo:
    """Representa un préstamo de material a un alumno durante el recreo."""

    id:               int
    material_id:      int
    alumno_nombre:    str
    curso_division:   str
    fecha_salida:     str          # Formato ISO: 'YYYY-MM-DD HH:MM:SS'
    fecha_devolucion: str | None   # None mientras el préstamo está activo
    estado:           str

    # ── Validaciones ──────────────────────────────────────────────────────────

    def __post_init__(self):
        self._validar()

    def _validar(self) -> None:
        """Lanza ValueError si algún campo no cumple las reglas de negocio."""
        if not self.alumno_nombre or not self.alumno_nombre.strip():
            raise ValueError("El nombre del alumno no puede estar vacío.")
        if not self.curso_division or not self.curso_division.strip():
            raise ValueError("El curso/división no puede estar vacío.")
        if self.estado not in ESTADOS_PRESTAMO:
            raise ValueError(
                f"Estado '{self.estado}' inválido. "
                f"Opciones: {ESTADOS_PRESTAMO}"
            )

    # ── Propiedades calculadas ────────────────────────────────────────────────

    @property
    def esta_activo(self) -> bool:
        """True si el préstamo todavía no fue cerrado."""
        return self.estado == "Activo"

    @property
    def duracion_minutos(self) -> int | None:
        """
        Calcula la duración del préstamo en minutos.
        Retorna None si el préstamo sigue activo o si las fechas son inválidas.
        """
        if not self.fecha_devolucion:
            return None
        try:
            fmt = "%Y-%m-%d %H:%M:%S"
            salida = datetime.strptime(self.fecha_salida, fmt)
            devolucion = datetime.strptime(self.fecha_devolucion, fmt)
            delta = devolucion - salida
            return int(delta.total_seconds() / 60)
        except ValueError:
            return None

    # ── Representación ────────────────────────────────────────────────────────

    def __str__(self) -> str:
        devolucion = self.fecha_devolucion or "Pendiente"
        return (
            f"Préstamo #{self.id} — {self.alumno_nombre} ({self.curso_division}) — "
            f"Salida: {self.fecha_salida} — Devolución: {devolucion} — "
            f"Estado: {self.estado}"
        )

    # ── Método de fábrica desde Row de SQLite ─────────────────────────────────

    @classmethod
    def desde_row(cls, row) -> "Prestamo":
        """Crea una instancia de Prestamo a partir de un sqlite3.Row."""
        return cls(
            id=row["id"],
            material_id=row["material_id"],
            alumno_nombre=row["alumno_nombre"],
            curso_division=row["curso_division"],
            fecha_salida=row["fecha_salida"],
            fecha_devolucion=row["fecha_devolucion"],
            estado=row["estado"],
        )
