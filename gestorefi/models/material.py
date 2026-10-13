"""
material.py — GestorEFi
Modelo de negocio para la entidad Material.
Encapsula la lógica de validación y representación de un material del inventario.
"""

from dataclasses import dataclass, field
from typing import ClassVar


# Valores válidos definidos en la especificación técnica
CATEGORIAS_VALIDAS: list[str] = ["Pelotas", "Conos", "Indumentaria", "Colchonetas"]
ESTADOS_VALIDOS: list[str] = ["Nuevo", "Bueno", "Gastado", "Inutilizable"]


@dataclass
class Material:
    """Representa un material del depósito de Educación Física."""

    id:               int
    nombre:           str
    categoria:        str
    stock_total:      int
    stock_disponible: int
    estado:           str

    # ── Validaciones ──────────────────────────────────────────────────────────

    def __post_init__(self):
        self._validar()

    def _validar(self) -> None:
        """Lanza ValueError si algún campo no cumple las reglas de negocio."""
        if not self.nombre or not self.nombre.strip():
            raise ValueError("El nombre del material no puede estar vacío.")
        if self.categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(
                f"Categoría '{self.categoria}' inválida. "
                f"Opciones: {CATEGORIAS_VALIDAS}"
            )
        if self.estado not in ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado '{self.estado}' inválido. "
                f"Opciones: {ESTADOS_VALIDOS}"
            )
        if self.stock_total < 0:
            raise ValueError("El stock total no puede ser negativo.")
        if self.stock_disponible < 0:
            raise ValueError("El stock disponible no puede ser negativo.")
        if self.stock_disponible > self.stock_total:
            raise ValueError(
                "El stock disponible no puede superar el stock total."
            )

    # ── Propiedades calculadas ────────────────────────────────────────────────

    @property
    def stock_en_prestamo(self) -> int:
        """Cantidad de unidades actualmente prestadas."""
        return self.stock_total - self.stock_disponible

    @property
    def tiene_stock(self) -> bool:
        """True si hay al menos una unidad disponible para prestar."""
        return self.stock_disponible > 0

    # ── Representación ────────────────────────────────────────────────────────

    def __str__(self) -> str:
        return (
            f"[{self.categoria}] {self.nombre} — "
            f"Disponible: {self.stock_disponible}/{self.stock_total} — "
            f"Estado: {self.estado}"
        )

    # ── Método de fábrica desde Row de SQLite ─────────────────────────────────

    @classmethod
    def desde_row(cls, row) -> "Material":
        """Crea una instancia de Material a partir de un sqlite3.Row."""
        return cls(
            id=row["id"],
            nombre=row["nombre"],
            categoria=row["categoria"],
            stock_total=row["stock_total"],
            stock_disponible=row["stock_disponible"],
            estado=row["estado"],
        )
