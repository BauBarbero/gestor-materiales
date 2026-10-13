"""
loans_frame.py — GestorEFi
Módulo de Préstamos Rápidos de Recreo (Fase 4).

Permite:
1. Registrar préstamos rápidos a alumnos (descontando 1 del stock disponible).
2. Filtrar y consultar préstamos activos en tiempo real.
3. Registrar la devolución de materiales (reponiendo 1 al stock disponible).
Accesible tanto para rol ADMIN como CONSULTA.
"""

import customtkinter
from tkinter import messagebox
from datetime import datetime

from database.queries import (
    obtener_materiales,
    registrar_prestamo,
    obtener_prestamos_activos,
    registrar_devolucion,
)

# ─── Paleta de colores institucional ──────────────────────────────────────────
COLOR_PRIMARIO         = "#1e3a8a"   # Dark Blue
COLOR_HOVER_BTN        = "#1e40af"   # Hover primario
COLOR_FONDO            = "#f8fafc"   # Light Gray — fondo general
COLOR_BLANCO           = "#ffffff"   # Fondo de tarjetas
COLOR_TEXTO_CLARO      = "#eff6ff"   # Blanco / Off-white
COLOR_TEXTO_OSCURO     = "#1e293b"   # Slate oscuro — texto principal
COLOR_TEXTO_SECUNDARIO = "#64748b"   # Gris — subtítulos y metadatos
COLOR_BORDE            = "#e2e8f0"   # Gris suave — bordes
COLOR_ENCABEZADO       = "#1e3a8a"   # Encabezado de tabla
COLOR_FILA_PAR         = "#f8fafc"   # Fila par
COLOR_FILA_IMPAR       = "#ffffff"   # Fila impar
COLOR_FILA_HOVER       = "#dbeafe"   # Fila hover
COLOR_EXITO            = "#16a34a"   # Verde — botón registrar
COLOR_HOVER_EXITO      = "#15803d"
COLOR_ACCION_DEV       = "#0284c7"   # Celeste institucional — devolver
COLOR_HOVER_DEV        = "#0369a1"
COLOR_ERROR            = "#dc2626"   # Rojo error

# ─── Columnas de la tabla de préstamos activos ────────────────────────────────
# (encabezado, ancho_relativo, ancla)
_COLUMNAS_PRESTAMOS: list[tuple[str, int, str]] = [
    ("MATERIAL",     3, "w"),
    ("ALUMNO/A",     3, "w"),
    ("CURSO",        2, "center"),
    ("HORA SALIDA",  2, "center"),
    ("ACCIÓN",       2, "center"),
]


class _FilaPrestamo(customtkinter.CTkFrame):
    """
    Representa una fila dentro de la tabla de préstamos activos.
    Incluye los datos del préstamo y un botón directo para registrar su devolución.
    """

    def __init__(self, master, prestamo: dict, index: int, on_devolver):
        color_base = COLOR_FILA_PAR if index % 2 == 0 else COLOR_FILA_IMPAR
        super().__init__(master, fg_color=color_base, corner_radius=0)
        self.prestamo = prestamo
        self.color_base = color_base
        self.on_devolver = on_devolver

        # Configurar proporción de columnas
        pesos = [c[1] for c in _COLUMNAS_PRESTAMOS]
        for col_idx, peso in enumerate(pesos):
            self.columnconfigure(col_idx, weight=peso)

        # ── 1. Material ──────────────────────────────────────────────────────
        lbl_mat = customtkinter.CTkLabel(
            self,
            text=prestamo.get("material", ""),
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        )
        lbl_mat.grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=10)

        # ── 2. Alumno/a ──────────────────────────────────────────────────────
        lbl_alum = customtkinter.CTkLabel(
            self,
            text=prestamo.get("alumno_nombre", ""),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        )
        lbl_alum.grid(row=0, column=1, sticky="ew", padx=8, pady=10)

        # ── 3. Curso / División ──────────────────────────────────────────────
        lbl_curso = customtkinter.CTkLabel(
            self,
            text=prestamo.get("curso_division", ""),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="center"
        )
        lbl_curso.grid(row=0, column=2, sticky="ew", padx=8, pady=10)

        # ── 4. Hora de Salida ────────────────────────────────────────────────
        hora_texto = self._formatear_hora(prestamo.get("fecha_salida", ""))
        lbl_hora = customtkinter.CTkLabel(
            self,
            text=hora_texto,
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO,
            anchor="center"
        )
        lbl_hora.grid(row=0, column=3, sticky="ew", padx=8, pady=10)

        # ── 5. Botón Devolver ────────────────────────────────────────────────
        btn_devolver = customtkinter.CTkButton(
            self,
            text="✓ Devolver",
            font=customtkinter.CTkFont(size=11, weight="bold"),
            fg_color=COLOR_ACCION_DEV,
            hover_color=COLOR_HOVER_DEV,
            text_color=COLOR_TEXTO_CLARO,
            height=30,
            width=88,
            corner_radius=7,
            command=lambda: self.on_devolver(self.prestamo)
        )
        btn_devolver.grid(row=0, column=4, padx=(8, 14), pady=6)

        # ── Separador inferior ───────────────────────────────────────────────
        sep = customtkinter.CTkFrame(self, fg_color=COLOR_BORDE, height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=len(_COLUMNAS_PRESTAMOS), sticky="ew")

    @staticmethod
    def _formatear_hora(fecha_str: str) -> str:
        """Formatea 'YYYY-MM-DD HH:MM:SS' a 'HH:MM hs (DD/MM)'."""
        if not fecha_str:
            return "—"
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%H:%M hs (%d/%m)")
        except Exception:
            return str(fecha_str)


class LoansFrame(customtkinter.CTkFrame):
    """
    Frame del módulo de Préstamos Rápidos de Recreo.

    Estructura visual:
    ┌────────────────────────────────────────────────────────────────────────┐
    │  Barra superior: Título + Contador de préstamos activos + Refrescar    │
    ├───────────────────────────────────┬────────────────────────────────────┤
    │  Columna izquierda (Formulario):   │  Columna derecha (Tabla activos):  │
    │  - Material con stock disponible  │  - Barra de búsqueda               │
    │  - Nombre alumno/a                │  - Encabezados de tabla            │
    │  - Curso / división               │  - Filas de préstamos activos      │
    │  - Botón: Registrar Préstamo      │  - Botones de 'Devolver'           │
    └───────────────────────────────────┴────────────────────────────────────┘
    """

    def __init__(self, master, username: str, rol: str, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.username = username
        self.rol      = rol

        # Mapeo: etiqueta del menú -> ID del material
        self._mapa_materiales: dict[str, int] = {}
        self._prestamos_activos: list[dict] = []
        self._prestamos_visibles: list[dict] = []
        self._timer_estado = None
        self._timer_busqueda = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._construir_barra_superior()
        self._construir_cuerpo()

        # Cargar datos iniciales
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()

    # ── Barra Superior ────────────────────────────────────────────────────────

    def _construir_barra_superior(self):
        barra = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        barra.grid(row=0, column=0, sticky="ew", padx=28, pady=(28, 14))
        barra.columnconfigure(0, weight=1)

        # Lado izquierdo: Título y subtítulo
        lado_izq = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_izq.grid(row=0, column=0, sticky="w", padx=24, pady=16)

        customtkinter.CTkLabel(
            lado_izq,
            text="🏃  Préstamos de Recreo",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(side="left")

        customtkinter.CTkLabel(
            lado_izq,
            text="  ·  Registro de salidas y devoluciones rápidas",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(side="left", pady=(3, 0))

        # Lado derecho: Contador y botón de refresco
        lado_der = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_der.grid(row=0, column=1, sticky="e", padx=24, pady=16)

        self.etiqueta_badge = customtkinter.CTkLabel(
            lado_der,
            text="0 activos",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color="#e0f2fe",
            text_color="#0369a1",
            corner_radius=8,
            padx=12,
            pady=4
        )
        self.etiqueta_badge.pack(side="left", padx=(0, 12))

        customtkinter.CTkButton(
            lado_der,
            text="↺  Refrescar",
            font=customtkinter.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_SECUNDARIO,
            border_width=1,
            border_color=COLOR_BORDE,
            height=34,
            corner_radius=8,
            command=self._refrescar_todo
        ).pack(side="left")

    # ── Cuerpo Principal (2 Columnas) ─────────────────────────────────────────

    def _construir_cuerpo(self):
        cuerpo = customtkinter.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))
        cuerpo.rowconfigure(0, weight=1)
        cuerpo.columnconfigure(0, weight=0)  # Columna formulario: ancho fijo
        cuerpo.columnconfigure(1, weight=1)  # Columna tabla: expandible

        self._construir_tarjeta_formulario(cuerpo)
        self._construir_tarjeta_activos(cuerpo)

    # ── Formulario de Préstamo (Columna Izquierda) ─────────────────────────────

    def _construir_tarjeta_formulario(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE,
            width=380
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        tarjeta.grid_propagate(False)

        # Encabezado del formulario
        customtkinter.CTkLabel(
            tarjeta,
            text="⚡  Nuevo Préstamo",
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=24, pady=(22, 2))

        customtkinter.CTkLabel(
            tarjeta,
            text="Asigná un material con stock a un alumno.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=24, pady=(0, 18))

        # ── Campo: Material disponible ───────────────────────────────────────
        self._label_campo(tarjeta, "Material disponible")
        self.var_material = customtkinter.StringVar(value="")
        self.combo_material = customtkinter.CTkOptionMenu(
            tarjeta,
            variable=self.var_material,
            values=["Cargando materiales..."],
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            button_color=COLOR_PRIMARIO,
            button_hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_OSCURO,
            dropdown_fg_color=COLOR_BLANCO,
            dropdown_text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=42
        )
        self.combo_material.pack(fill="x", padx=24, pady=(0, 14))

        # ── Campo: Alumno ────────────────────────────────────────────────────
        self._label_campo(tarjeta, "Nombre del Alumno/a")
        self.campo_alumno = customtkinter.CTkEntry(
            tarjeta,
            placeholder_text="Ej: Lucas Gómez",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=42
        )
        self.campo_alumno.pack(fill="x", padx=24, pady=(0, 14))

        # ── Campo: Curso y división ──────────────────────────────────────────
        self._label_campo(tarjeta, "Curso / División")
        self.campo_curso = customtkinter.CTkEntry(
            tarjeta,
            placeholder_text="Ej: 3° A",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=42
        )
        self.campo_curso.pack(fill="x", padx=24, pady=(0, 16))

        # ── Mensaje de estado / validación ───────────────────────────────────
        self.etiqueta_estado = customtkinter.CTkLabel(
            tarjeta,
            text="",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_ERROR,
            wraplength=330,
            height=18
        )
        self.etiqueta_estado.pack(padx=24, pady=(0, 8))

        # ── Botón de Registrar ───────────────────────────────────────────────
        self.btn_prestar = customtkinter.CTkButton(
            tarjeta,
            text="⚡  Registrar Préstamo",
            font=customtkinter.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_EXITO,
            hover_color=COLOR_HOVER_EXITO,
            text_color=COLOR_TEXTO_CLARO,
            height=44,
            corner_radius=9,
            command=self._enviar_prestamo
        )
        self.btn_prestar.pack(fill="x", padx=24, pady=(0, 24))

        # Atajos de teclado para velocidad en recreo
        self.campo_alumno.bind("<Return>", lambda _: self.campo_curso.focus())
        self.campo_curso.bind("<Return>", lambda _: self._enviar_prestamo())

    def _label_campo(self, parent, texto: str):
        customtkinter.CTkLabel(
            parent,
            text=texto,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 5))

    # ── Tabla de Préstamos Activos (Columna Derecha) ──────────────────────────

    def _construir_tarjeta_activos(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta.grid(row=0, column=1, sticky="nsew")
        tarjeta.rowconfigure(2, weight=1)
        tarjeta.columnconfigure(0, weight=1)

        # ── Barra de búsqueda dentro de la tarjeta ────────────────────────────
        barra_busqueda = customtkinter.CTkFrame(tarjeta, fg_color="transparent")
        barra_busqueda.grid(row=0, column=0, sticky="ew", padx=20, pady=16)
        barra_busqueda.columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            barra_busqueda,
            text="🔍",
            font=customtkinter.CTkFont(size=15),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).grid(row=0, column=0, padx=(0, 8))

        self.var_busqueda = customtkinter.StringVar()
        self.var_busqueda.trace_add("write", self._on_busqueda_cambia)

        self.campo_busqueda = customtkinter.CTkEntry(
            barra_busqueda,
            textvariable=self.var_busqueda,
            placeholder_text="Buscar por alumno, curso o material…",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=38
        )
        self.campo_busqueda.grid(row=0, column=1, sticky="ew")

        # ── Encabezado de la tabla ───────────────────────────────────────────
        cabecera = customtkinter.CTkFrame(
            tarjeta, fg_color=COLOR_ENCABEZADO, corner_radius=0
        )
        cabecera.grid(row=1, column=0, sticky="ew")

        pesos = [c[1] for c in _COLUMNAS_PRESTAMOS]
        for idx, peso in enumerate(pesos):
            cabecera.columnconfigure(idx, weight=peso)

        for col_idx, (titulo, _, ancla) in enumerate(_COLUMNAS_PRESTAMOS):
            customtkinter.CTkLabel(
                cabecera,
                text=titulo,
                font=customtkinter.CTkFont(size=11, weight="bold"),
                text_color=COLOR_TEXTO_CLARO,
                anchor=ancla
            ).grid(
                row=0, column=col_idx, sticky="ew",
                padx=(14 if col_idx == 0 else 8, 14 if col_idx == len(_COLUMNAS_PRESTAMOS) - 1 else 8),
                pady=11
            )

        # ── Área Scrolleable de Filas ─────────────────────────────────────────
        self.scroll_filas = customtkinter.CTkScrollableFrame(
            tarjeta, fg_color="transparent", corner_radius=0
        )
        self.scroll_filas.grid(row=2, column=0, sticky="nsew")
        self.scroll_filas.columnconfigure(0, weight=1)

        # Estado vacío (placeholder)
        self.frame_vacio = customtkinter.CTkFrame(
            self.scroll_filas, fg_color="transparent"
        )
        self.frame_vacio.grid(row=0, column=0, sticky="ew", pady=40)

        self.icono_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="✅",
            font=customtkinter.CTkFont(size=44)
        )
        self.icono_vacio.pack(pady=(10, 8))

        self.titulo_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="No hay préstamos activos",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        )
        self.titulo_vacio.pack()

        self.subtitulo_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="Todos los materiales se encuentran en el depósito escolar.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.subtitulo_vacio.pack(pady=(4, 20))

    # ── Lógica de Carga de Datos ──────────────────────────────────────────────

    def _cargar_materiales_disponibles(self):
        """Carga solo los materiales que tienen stock_disponible > 0 en el menú desplegable."""
        try:
            todos = obtener_materiales()
            # Filtrar solo con stock disponible
            disponibles = [dict(m) for m in todos if m["stock_disponible"] > 0]
        except RuntimeError as e:
            self._mostrar_estado(f"Error cargando materiales: {e}", es_error=True)
            disponibles = []

        self._mapa_materiales.clear()
        opciones = []

        for m in disponibles:
            etiqueta = f"{m['nombre']}  ·  {m['stock_disponible']} disp. ({m['categoria']})"
            self._mapa_materiales[etiqueta] = m["id"]
            opciones.append(etiqueta)

        if opciones:
            self.combo_material.configure(values=opciones, state="normal")
            # Mantener selección si aún existe, sino elegir la primera
            actual = self.var_material.get()
            if actual in self._mapa_materiales:
                self.var_material.set(actual)
            else:
                self.var_material.set(opciones[0])
            self.btn_prestar.configure(state="normal")
        else:
            self.combo_material.configure(values=["Sin materiales disponibles"], state="disabled")
            self.var_material.set("Sin materiales disponibles")
            self.btn_prestar.configure(state="disabled")

    def _cargar_prestamos_activos(self):
        """Recupera préstamos activos de la base de datos."""
        try:
            rows = obtener_prestamos_activos()
            self._prestamos_activos = [dict(r) for r in rows]
        except RuntimeError as e:
            messagebox.showerror("Error de base de datos", str(e), parent=self)
            self._prestamos_activos = []

        total = len(self._prestamos_activos)
        self.etiqueta_badge.configure(
            text=f"{total} activo{'s' if total != 1 else ''}"
        )
        self._aplicar_filtro_busqueda()

    def _refrescar_todo(self):
        """Recarga tanto el formulario de materiales como la lista de préstamos."""
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()

    # ── Filtro de Búsqueda ────────────────────────────────────────────────────

    def _on_busqueda_cambia(self, *_args):
        if self._timer_busqueda is not None:
            self.after_cancel(self._timer_busqueda)
        self._timer_busqueda = self.after(200, self._aplicar_filtro_busqueda)

    def _aplicar_filtro_busqueda(self):
        query = self.var_busqueda.get().strip().lower()
        if not query:
            self._prestamos_visibles = self._prestamos_activos
        else:
            self._prestamos_visibles = [
                p for p in self._prestamos_activos
                if query in p.get("alumno_nombre", "").lower()
                or query in p.get("curso_division", "").lower()
                or query in p.get("material", "").lower()
            ]
        self._renderizar_tabla_activos(query_activa=bool(query))

    def _renderizar_tabla_activos(self, query_activa: bool = False):
        """Dibuja las filas de la tabla de préstamos activos."""
        for widget in self.scroll_filas.winfo_children():
            if widget != self.frame_vacio:
                widget.destroy()

        if not self._prestamos_visibles:
            self.frame_vacio.grid()
            if query_activa:
                self.icono_vacio.configure(text="🔍")
                self.titulo_vacio.configure(text="Sin coincidencias")
                self.subtitulo_vacio.configure(text="No se encontraron préstamos activos para esa búsqueda.")
            else:
                self.icono_vacio.configure(text="✅")
                self.titulo_vacio.configure(text="No hay préstamos activos")
                self.subtitulo_vacio.configure(text="Todos los materiales se encuentran en el depósito escolar.")
            return

        self.frame_vacio.grid_remove()

        for idx, prestamo in enumerate(self._prestamos_visibles):
            fila = _FilaPrestamo(
                self.scroll_filas,
                prestamo=prestamo,
                index=idx,
                on_devolver=self._confirmar_devolucion
            )
            fila.grid(row=idx, column=0, sticky="ew")

    # ── Registro de Préstamo ──────────────────────────────────────────────────

    def _enviar_prestamo(self):
        """Valida los campos y llama a registrar_prestamo en queries.py."""
        etiqueta_sel = self.var_material.get()
        material_id = self._mapa_materiales.get(etiqueta_sel)

        if not material_id:
            self._mostrar_estado("Seleccioná un material con stock disponible.", es_error=True)
            return

        alumno = self.campo_alumno.get().strip()
        if not alumno:
            self._mostrar_estado("Ingresá el nombre y apellido del alumno/a.", es_error=True)
            self.campo_alumno.focus()
            return

        curso = self.campo_curso.get().strip()
        if not curso:
            self._mostrar_estado("Ingresá el curso y división (ej: 4° B).", es_error=True)
            self.campo_curso.focus()
            return

        # Deshabilitar botón durante el proceso
        self.btn_prestar.configure(state="disabled", text="Registrando...")

        try:
            registrar_prestamo(material_id, alumno, curso)
        except (ValueError, RuntimeError) as e:
            self._mostrar_estado(str(e), es_error=True)
            self.btn_prestar.configure(state="normal", text="⚡  Registrar Préstamo")
            return

        # Éxito: limpiar campos de texto y refrescar
        self.campo_alumno.delete(0, "end")
        self.campo_curso.delete(0, "end")
        self.campo_alumno.focus()
        self.btn_prestar.configure(state="normal", text="⚡  Registrar Préstamo")

        self._mostrar_estado(f"✓ Préstamo de material registrado con éxito.", es_error=False)
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()

    # ── Devolución de Préstamo ────────────────────────────────────────────────

    def _confirmar_devolucion(self, prestamo: dict):
        """Pide confirmación antes de marcar un préstamo como devuelto y reponer stock."""
        prestamo_id = prestamo.get("id")
        material = prestamo.get("material", "Material")
        alumno = prestamo.get("alumno_nombre", "Alumno/a")

        confirmar = messagebox.askyesno(
            "Confirmar Devolución",
            f"¿Confirmar la devolución del siguiente material?\n\n"
            f"• Material: {material}\n"
            f"• Alumno/a: {alumno}\n\n"
            f"El stock disponible aumentará automáticamente en +1 unidad.",
            parent=self
        )

        if not confirmar:
            return

        try:
            registrar_devolucion(prestamo_id)
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Error al registrar devolución", str(e), parent=self)
            return

        self._mostrar_estado(f"✓ '{material}' devuelto por {alumno}.", es_error=False)
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()

    # ── Mensaje de Estado / Feedback ──────────────────────────────────────────

    def _mostrar_estado(self, mensaje: str, es_error: bool = False):
        if self._timer_estado is not None:
            self.after_cancel(self._timer_estado)

        color = COLOR_ERROR if es_error else COLOR_EXITO
        self.etiqueta_estado.configure(text=mensaje, text_color=color)

        # Ocultar automáticamente luego de 4 segundos si es éxito
        if not es_error:
            self._timer_estado = self.after(4000, lambda: self.etiqueta_estado.configure(text=""))
