"""
loans_frame.py — GestorEFi
Módulo de Préstamos Rápidos de Recreo (Fase 4 y Fase 5 extendida).

Permite:
1. Registrar préstamos rápidos a alumnos (descontando 1 del stock disponible).
2. Consultar y filtrar préstamos activos en tiempo real con devolución en 1 clic.
3. Consultar el historial completo de préstamos (activos, devueltos y no devueltos)
   con fecha y hora exacta de salida y devolución, junto a filtros por estado y texto.
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
    obtener_todos_los_prestamos,
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

# ─── Badges de estado de préstamo ─────────────────────────────────────────────
COLOR_BADGE_ESTADO = {
    "Activo":      ("#e0f2fe", "#0369a1"),
    "Devuelto":    ("#dcfce7", "#15803d"),
    "No Devuelto": ("#fee2e2", "#b91c1c"),
}

# ─── Columnas de las tablas ───────────────────────────────────────────────────
_COLUMNAS_ACTIVOS: list[tuple[str, int, str]] = [
    ("MATERIAL",     3, "w"),
    ("ALUMNO/A",     3, "w"),
    ("CURSO",        2, "center"),
    ("HORA SALIDA",  2, "center"),
    ("ACCIÓN",       2, "center"),
]

_COLUMNAS_HISTORIAL: list[tuple[str, int, str]] = [
    ("MATERIAL",     3, "w"),
    ("ALUMNO/A",     3, "w"),
    ("CURSO",        2, "center"),
    ("SALIDA",       2, "center"),
    ("DEVOLUCIÓN",   2, "center"),
    ("ESTADO",       2, "center"),
]


class _FilaPrestamoActivo(customtkinter.CTkFrame):
    """
    Representa una fila dentro de la tabla de préstamos activos con botón 'Devolver'.
    """

    def __init__(self, master, prestamo: dict, index: int, on_devolver):
        color_base = COLOR_FILA_PAR if index % 2 == 0 else COLOR_FILA_IMPAR
        super().__init__(master, fg_color=color_base, corner_radius=0)
        self.prestamo = prestamo
        self.on_devolver = on_devolver

        pesos = [c[1] for c in _COLUMNAS_ACTIVOS]
        for col_idx, peso in enumerate(pesos):
            self.columnconfigure(col_idx, weight=peso)

        # 1. Material
        lbl_mat = customtkinter.CTkLabel(
            self, text=prestamo.get("material", ""),
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        )
        lbl_mat.grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=10)

        # 2. Alumno/a
        lbl_alum = customtkinter.CTkLabel(
            self, text=prestamo.get("alumno_nombre", ""),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        )
        lbl_alum.grid(row=0, column=1, sticky="ew", padx=8, pady=10)

        # 3. Curso
        lbl_curso = customtkinter.CTkLabel(
            self, text=prestamo.get("curso_division", ""),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO, anchor="center"
        )
        lbl_curso.grid(row=0, column=2, sticky="ew", padx=8, pady=10)

        # 4. Hora salida
        hora_texto = self._formatear_hora(prestamo.get("fecha_salida", ""))
        lbl_hora = customtkinter.CTkLabel(
            self, text=hora_texto,
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO, anchor="center"
        )
        lbl_hora.grid(row=0, column=3, sticky="ew", padx=8, pady=10)

        # 5. Botón Devolver
        btn_devolver = customtkinter.CTkButton(
            self, text="✓ Devolver",
            font=customtkinter.CTkFont(size=11, weight="bold"),
            fg_color=COLOR_ACCION_DEV, hover_color=COLOR_HOVER_DEV,
            text_color=COLOR_TEXTO_CLARO, height=30, width=88, corner_radius=7,
            command=lambda: self.on_devolver(self.prestamo)
        )
        btn_devolver.grid(row=0, column=4, padx=(8, 14), pady=6)

        # Separador inferior
        sep = customtkinter.CTkFrame(self, fg_color=COLOR_BORDE, height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=len(_COLUMNAS_ACTIVOS), sticky="ew")

    @staticmethod
    def _formatear_hora(fecha_str: str) -> str:
        if not fecha_str:
            return "—"
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%H:%M hs (%d/%m)")
        except Exception:
            return str(fecha_str)


class _FilaHistorialPrestamo(customtkinter.CTkFrame):
    """
    Representa una fila dentro del historial general de préstamos.
    """

    def __init__(self, master, prestamo: dict, index: int):
        color_base = COLOR_FILA_PAR if index % 2 == 0 else COLOR_FILA_IMPAR
        super().__init__(master, fg_color=color_base, corner_radius=0)

        pesos = [c[1] for c in _COLUMNAS_HISTORIAL]
        for col_idx, peso in enumerate(pesos):
            self.columnconfigure(col_idx, weight=peso)

        # 1. Material
        customtkinter.CTkLabel(
            self, text=prestamo.get("material", ""),
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=(14, 8), pady=10)

        # 2. Alumno/a
        customtkinter.CTkLabel(
            self, text=prestamo.get("alumno_nombre", ""),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        ).grid(row=0, column=1, sticky="ew", padx=8, pady=10)

        # 3. Curso
        customtkinter.CTkLabel(
            self, text=prestamo.get("curso_division", ""),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO, anchor="center"
        ).grid(row=0, column=2, sticky="ew", padx=8, pady=10)

        # 4. Salida
        salida_fmt = self._formatear_hora(prestamo.get("fecha_salida", ""))
        customtkinter.CTkLabel(
            self, text=salida_fmt,
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO, anchor="center"
        ).grid(row=0, column=3, sticky="ew", padx=8, pady=10)

        # 5. Devolución
        dev_raw = prestamo.get("fecha_devolucion")
        dev_fmt = self._formatear_hora(dev_raw) if dev_raw else "En curso..."
        color_dev = COLOR_TEXTO_SECUNDARIO if dev_raw else "#0284c7"
        customtkinter.CTkLabel(
            self, text=dev_fmt,
            font=customtkinter.CTkFont(size=11, slant="italic" if not dev_raw else "roman"),
            text_color=color_dev, anchor="center"
        ).grid(row=0, column=4, sticky="ew", padx=8, pady=10)

        # 6. Estado (Badge)
        estado = prestamo.get("estado", "Activo")
        bg_b, fg_b = COLOR_BADGE_ESTADO.get(estado, ("#f1f5f9", "#475569"))

        frame_badge = customtkinter.CTkFrame(self, fg_color="transparent")
        frame_badge.grid(row=0, column=5, padx=8, pady=8)

        customtkinter.CTkLabel(
            frame_badge,
            text=f"  {estado}  ",
            font=customtkinter.CTkFont(size=11, weight="bold"),
            fg_color=bg_b, text_color=fg_b, corner_radius=6
        ).pack()

        # Separador inferior
        sep = customtkinter.CTkFrame(self, fg_color=COLOR_BORDE, height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=len(_COLUMNAS_HISTORIAL), sticky="ew")

    @staticmethod
    def _formatear_hora(fecha_str: str) -> str:
        if not fecha_str:
            return "—"
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M hs")
        except Exception:
            return str(fecha_str)


class LoansFrame(customtkinter.CTkFrame):
    """
    Frame del módulo de Préstamos Rápidos de Recreo con navegación por pestañas:
    - Pestaña 1: Préstamos Activos (Formulario de salida + Tabla de activos con devolución)
    - Pestaña 2: Historial Completo (Listado general de préstamos con filtros)
    """

    def __init__(self, master, username: str, rol: str, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.username = username
        self.rol      = rol

        self._mapa_materiales: dict[str, int] = {}
        self._prestamos_activos: list[dict] = []
        self._prestamos_activos_vis: list[dict] = []
        self._historial_completo: list[dict] = []
        self._historial_vis: list[dict] = []

        self._timer_estado = None
        self._timer_busqueda_activos = None
        self._timer_busqueda_historial = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._construir_barra_superior()
        self._construir_pestanas()

        # Cargar datos iniciales
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()
        self._cargar_historial_completo()

    # ── Barra Superior ────────────────────────────────────────────────────────

    def _construir_barra_superior(self):
        barra = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        barra.grid(row=0, column=0, sticky="ew", padx=28, pady=(28, 10))
        barra.columnconfigure(0, weight=1)

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
            text="  ·  Gestión de salidas, devoluciones e historial",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(side="left", pady=(3, 0))

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
            text="↺  Refrescar Todo",
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

    # ── Pestañas de Navegación ────────────────────────────────────────────────

    def _construir_pestanas(self):
        self.tabview = customtkinter.CTkTabview(
            self,
            fg_color="transparent",
            segmented_button_fg_color="#e2e8f0",
            segmented_button_selected_color=COLOR_PRIMARIO,
            segmented_button_selected_hover_color=COLOR_HOVER_BTN,
            segmented_button_unselected_color=COLOR_BLANCO,
            segmented_button_unselected_hover_color="#f1f5f9",
            text_color=COLOR_TEXTO_CLARO
        )
        self.tabview.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 24))

        self.tab_activos   = self.tabview.add("⚡  Préstamos Activos")
        self.tab_historial = self.tabview.add("📜  Historial Completo")

        # ── Contenido Pestaña 1: Activos (Formulario + Tabla) ─────────────────
        self.tab_activos.rowconfigure(0, weight=1)
        self.tab_activos.columnconfigure(0, weight=0)
        self.tab_activos.columnconfigure(1, weight=1)

        self._construir_tarjeta_formulario(self.tab_activos)
        self._construir_tarjeta_activos(self.tab_activos)

        # ── Contenido Pestaña 2: Historial Completo ───────────────────────────
        self.tab_historial.rowconfigure(0, weight=1)
        self.tab_historial.columnconfigure(0, weight=1)

        self._construir_tarjeta_historial(self.tab_historial)

    # ── Formulario de Préstamo (Pestaña 1) ────────────────────────────────────

    def _construir_tarjeta_formulario(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE,
            width=380
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 16), pady=8)
        tarjeta.grid_propagate(False)

        customtkinter.CTkLabel(
            tarjeta,
            text="⚡  Nuevo Préstamo",
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=24, pady=(20, 2))

        customtkinter.CTkLabel(
            tarjeta,
            text="Asigná un material con stock a un alumno.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # Material disponible
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
        self.combo_material.pack(fill="x", padx=24, pady=(0, 12))

        # Alumno
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
        self.campo_alumno.pack(fill="x", padx=24, pady=(0, 12))

        # Curso
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
        self.campo_curso.pack(fill="x", padx=24, pady=(0, 14))

        # Estado feedback
        self.etiqueta_estado = customtkinter.CTkLabel(
            tarjeta,
            text="",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_ERROR,
            wraplength=330,
            height=18
        )
        self.etiqueta_estado.pack(padx=24, pady=(0, 6))

        # Botón Prestar
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
        self.btn_prestar.pack(fill="x", padx=24, pady=(0, 20))

        self.campo_alumno.bind("<Return>", lambda _: self.campo_curso.focus())
        self.campo_curso.bind("<Return>", lambda _: self._enviar_prestamo())

    def _label_campo(self, parent, texto: str):
        customtkinter.CTkLabel(
            parent,
            text=texto,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 4))

    # ── Tabla de Préstamos Activos (Pestaña 1) ────────────────────────────────

    def _construir_tarjeta_activos(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta.grid(row=0, column=1, sticky="nsew", pady=8)
        tarjeta.rowconfigure(2, weight=1)
        tarjeta.columnconfigure(0, weight=1)

        # Buscador activos
        barra_busqueda = customtkinter.CTkFrame(tarjeta, fg_color="transparent")
        barra_busqueda.grid(row=0, column=0, sticky="ew", padx=20, pady=14)
        barra_busqueda.columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            barra_busqueda, text="🔍",
            font=customtkinter.CTkFont(size=15),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).grid(row=0, column=0, padx=(0, 8))

        self.var_busqueda_activos = customtkinter.StringVar()
        self.var_busqueda_activos.trace_add("write", self._on_busqueda_activos_cambia)

        self.campo_busqueda_activos = customtkinter.CTkEntry(
            barra_busqueda,
            textvariable=self.var_busqueda_activos,
            placeholder_text="Buscar en activos por alumno, curso o material…",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=38
        )
        self.campo_busqueda_activos.grid(row=0, column=1, sticky="ew")

        # Encabezado
        cabecera = customtkinter.CTkFrame(
            tarjeta, fg_color=COLOR_ENCABEZADO, corner_radius=0
        )
        cabecera.grid(row=1, column=0, sticky="ew")

        pesos = [c[1] for c in _COLUMNAS_ACTIVOS]
        for idx, peso in enumerate(pesos):
            cabecera.columnconfigure(idx, weight=peso)

        for col_idx, (titulo, _, ancla) in enumerate(_COLUMNAS_ACTIVOS):
            customtkinter.CTkLabel(
                cabecera,
                text=titulo,
                font=customtkinter.CTkFont(size=11, weight="bold"),
                text_color=COLOR_TEXTO_CLARO,
                anchor=ancla
            ).grid(
                row=0, column=col_idx, sticky="ew",
                padx=(14 if col_idx == 0 else 8, 14 if col_idx == len(_COLUMNAS_ACTIVOS) - 1 else 8),
                pady=11
            )

        # Scrollable activos
        self.scroll_activos = customtkinter.CTkScrollableFrame(
            tarjeta, fg_color="transparent", corner_radius=0
        )
        self.scroll_activos.grid(row=2, column=0, sticky="nsew")
        self.scroll_activos.columnconfigure(0, weight=1)

        # Placeholder vacío
        self.frame_vacio_activos = customtkinter.CTkFrame(
            self.scroll_activos, fg_color="transparent"
        )
        self.frame_vacio_activos.grid(row=0, column=0, sticky="ew", pady=40)

        self.icono_vacio_activos = customtkinter.CTkLabel(
            self.frame_vacio_activos, text="✅", font=customtkinter.CTkFont(size=44)
        )
        self.icono_vacio_activos.pack(pady=(10, 8))

        self.titulo_vacio_activos = customtkinter.CTkLabel(
            self.frame_vacio_activos,
            text="No hay préstamos activos",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        )
        self.titulo_vacio_activos.pack()

        self.subtitulo_vacio_activos = customtkinter.CTkLabel(
            self.frame_vacio_activos,
            text="Todos los materiales se encuentran en el depósito escolar.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.subtitulo_vacio_activos.pack(pady=(4, 20))

    # ── Tabla de Historial Completo (Pestaña 2) ───────────────────────────────

    def _construir_tarjeta_historial(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", pady=8)
        tarjeta.rowconfigure(2, weight=1)
        tarjeta.columnconfigure(0, weight=1)

        # Barra de filtros
        barra_filtro = customtkinter.CTkFrame(tarjeta, fg_color="transparent")
        barra_filtro.grid(row=0, column=0, sticky="ew", padx=20, pady=14)
        barra_filtro.columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            barra_filtro, text="🔍",
            font=customtkinter.CTkFont(size=15),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).grid(row=0, column=0, padx=(0, 8))

        self.var_busqueda_historial = customtkinter.StringVar()
        self.var_busqueda_historial.trace_add("write", self._on_busqueda_historial_cambia)

        self.campo_busqueda_historial = customtkinter.CTkEntry(
            barra_filtro,
            textvariable=self.var_busqueda_historial,
            placeholder_text="Buscar en historial por alumno, curso o material…",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=38
        )
        self.campo_busqueda_historial.grid(row=0, column=1, sticky="ew", padx=(0, 14))

        # Filtro de Estado
        customtkinter.CTkLabel(
            barra_filtro, text="Estado:",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).grid(row=0, column=2, padx=(0, 8))

        self.var_filtro_estado = customtkinter.StringVar(value="Todos")
        self.combo_filtro_estado = customtkinter.CTkOptionMenu(
            barra_filtro,
            variable=self.var_filtro_estado,
            values=["Todos", "Activo", "Devuelto", "No Devuelto"],
            command=self._on_filtro_estado_cambia,
            font=customtkinter.CTkFont(size=12),
            fg_color=COLOR_FONDO,
            button_color=COLOR_PRIMARIO,
            button_hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_OSCURO,
            dropdown_fg_color=COLOR_BLANCO,
            dropdown_text_color=COLOR_TEXTO_OSCURO,
            corner_radius=8,
            height=38,
            width=140
        )
        self.combo_filtro_estado.grid(row=0, column=3, padx=(0, 14))

        self.etiqueta_conteo_historial = customtkinter.CTkLabel(
            barra_filtro, text="0 registros",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.etiqueta_conteo_historial.grid(row=0, column=4)

        # Encabezado historial
        cabecera = customtkinter.CTkFrame(
            tarjeta, fg_color=COLOR_ENCABEZADO, corner_radius=0
        )
        cabecera.grid(row=1, column=0, sticky="ew")

        pesos = [c[1] for c in _COLUMNAS_HISTORIAL]
        for idx, peso in enumerate(pesos):
            cabecera.columnconfigure(idx, weight=peso)

        for col_idx, (titulo, _, ancla) in enumerate(_COLUMNAS_HISTORIAL):
            customtkinter.CTkLabel(
                cabecera,
                text=titulo,
                font=customtkinter.CTkFont(size=11, weight="bold"),
                text_color=COLOR_TEXTO_CLARO,
                anchor=ancla
            ).grid(
                row=0, column=col_idx, sticky="ew",
                padx=(14 if col_idx == 0 else 8, 14 if col_idx == len(_COLUMNAS_HISTORIAL) - 1 else 8),
                pady=11
            )

        # Scrollable historial
        self.scroll_historial = customtkinter.CTkScrollableFrame(
            tarjeta, fg_color="transparent", corner_radius=0
        )
        self.scroll_historial.grid(row=2, column=0, sticky="nsew")
        self.scroll_historial.columnconfigure(0, weight=1)

        # Placeholder vacío historial
        self.frame_vacio_historial = customtkinter.CTkFrame(
            self.scroll_historial, fg_color="transparent"
        )
        self.frame_vacio_historial.grid(row=0, column=0, sticky="ew", pady=40)

        self.icono_vacio_historial = customtkinter.CTkLabel(
            self.frame_vacio_historial, text="📜", font=customtkinter.CTkFont(size=44)
        )
        self.icono_vacio_historial.pack(pady=(10, 8))

        self.titulo_vacio_historial = customtkinter.CTkLabel(
            self.frame_vacio_historial,
            text="Sin registros de préstamos",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        )
        self.titulo_vacio_historial.pack()

        self.subtitulo_vacio_historial = customtkinter.CTkLabel(
            self.frame_vacio_historial,
            text="Aún no se han registrado movimientos de recreo.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.subtitulo_vacio_historial.pack(pady=(4, 20))

    # ── Carga y Actualización de Datos ────────────────────────────────────────

    def _cargar_materiales_disponibles(self):
        try:
            todos = obtener_materiales()
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
        try:
            rows = obtener_prestamos_activos()
            self._prestamos_activos = [dict(r) for r in rows]
        except RuntimeError as e:
            messagebox.showerror("Error de base de datos", str(e), parent=self)
            self._prestamos_activos = []

        total = len(self._prestamos_activos)
        self.etiqueta_badge.configure(text=f"{total} activo{'s' if total != 1 else ''}")
        self._aplicar_filtro_activos()

    def _cargar_historial_completo(self):
        try:
            rows = obtener_todos_los_prestamos()
            self._historial_completo = [dict(r) for r in rows]
        except RuntimeError as e:
            messagebox.showerror("Error de base de datos", str(e), parent=self)
            self._historial_completo = []

        self._aplicar_filtro_historial()

    def _refrescar_todo(self):
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()
        self._cargar_historial_completo()

    # ── Filtrado y Renderizado: Activos ───────────────────────────────────────

    def _on_busqueda_activos_cambia(self, *_args):
        if self._timer_busqueda_activos is not None:
            self.after_cancel(self._timer_busqueda_activos)
        self._timer_busqueda_activos = self.after(200, self._aplicar_filtro_activos)

    def _aplicar_filtro_activos(self):
        query = self.var_busqueda_activos.get().strip().lower()
        if not query:
            self._prestamos_activos_vis = self._prestamos_activos
        else:
            self._prestamos_activos_vis = [
                p for p in self._prestamos_activos
                if query in p.get("alumno_nombre", "").lower()
                or query in p.get("curso_division", "").lower()
                or query in p.get("material", "").lower()
            ]
        self._renderizar_tabla_activos(query_activa=bool(query))

    def _renderizar_tabla_activos(self, query_activa: bool = False):
        for widget in self.scroll_activos.winfo_children():
            if widget != self.frame_vacio_activos:
                widget.destroy()

        if not self._prestamos_activos_vis:
            self.frame_vacio_activos.grid()
            if query_activa:
                self.icono_vacio_activos.configure(text="🔍")
                self.titulo_vacio_activos.configure(text="Sin coincidencias")
                self.subtitulo_vacio_activos.configure(text="No se encontraron préstamos activos para esa búsqueda.")
            else:
                self.icono_vacio_activos.configure(text="✅")
                self.titulo_vacio_activos.configure(text="No hay préstamos activos")
                self.subtitulo_vacio_activos.configure(text="Todos los materiales se encuentran en el depósito escolar.")
            return

        self.frame_vacio_activos.grid_remove()

        for idx, prestamo in enumerate(self._prestamos_activos_vis):
            fila = _FilaPrestamoActivo(
                self.scroll_activos,
                prestamo=prestamo,
                index=idx,
                on_devolver=self._confirmar_devolucion
            )
            fila.grid(row=idx, column=0, sticky="ew")

    # ── Filtrado y Renderizado: Historial ─────────────────────────────────────

    def _on_busqueda_historial_cambia(self, *_args):
        if self._timer_busqueda_historial is not None:
            self.after_cancel(self._timer_busqueda_historial)
        self._timer_busqueda_historial = self.after(200, self._aplicar_filtro_historial)

    def _on_filtro_estado_cambia(self, _val: str = None):
        self._aplicar_filtro_historial()

    def _aplicar_filtro_historial(self):
        query = self.var_busqueda_historial.get().strip().lower()
        estado = self.var_filtro_estado.get()

        resultado = self._historial_completo

        if estado != "Todos":
            resultado = [p for p in resultado if p.get("estado") == estado]

        if query:
            resultado = [
                p for p in resultado
                if query in p.get("alumno_nombre", "").lower()
                or query in p.get("curso_division", "").lower()
                or query in p.get("material", "").lower()
            ]

        self._historial_vis = resultado
        self.etiqueta_conteo_historial.configure(
            text=f"{len(self._historial_vis)} de {len(self._historial_completo)} registros"
        )
        self._renderizar_tabla_historial(query_activa=bool(query or estado != "Todos"))

    def _renderizar_tabla_historial(self, query_activa: bool = False):
        for widget in self.scroll_historial.winfo_children():
            if widget != self.frame_vacio_historial:
                widget.destroy()

        if not self._historial_vis:
            self.frame_vacio_historial.grid()
            if query_activa:
                self.icono_vacio_historial.configure(text="🔍")
                self.titulo_vacio_historial.configure(text="Sin coincidencias")
                self.subtitulo_vacio_historial.configure(text="No se encontraron préstamos con los filtros aplicados.")
            else:
                self.icono_vacio_historial.configure(text="📜")
                self.titulo_vacio_historial.configure(text="Sin registros de préstamos")
                self.subtitulo_vacio_historial.configure(text="Aún no se han registrado préstamos en el sistema.")
            return

        self.frame_vacio_historial.grid_remove()

        for idx, prestamo in enumerate(self._historial_vis):
            fila = _FilaHistorialPrestamo(self.scroll_historial, prestamo=prestamo, index=idx)
            fila.grid(row=idx, column=0, sticky="ew")

    # ── Registro de Préstamo ──────────────────────────────────────────────────

    def _enviar_prestamo(self):
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

        self.btn_prestar.configure(state="disabled", text="Registrando...")

        try:
            registrar_prestamo(material_id, alumno, curso)
        except (ValueError, RuntimeError) as e:
            self._mostrar_estado(str(e), es_error=True)
            self.btn_prestar.configure(state="normal", text="⚡  Registrar Préstamo")
            return

        self.campo_alumno.delete(0, "end")
        self.campo_curso.delete(0, "end")
        self.campo_alumno.focus()
        self.btn_prestar.configure(state="normal", text="⚡  Registrar Préstamo")

        self._mostrar_estado(f"✓ Préstamo de material registrado con éxito.", es_error=False)
        self._cargar_materiales_disponibles()
        self._cargar_prestamos_activos()
        self._cargar_historial_completo()

    # ── Devolución de Préstamo ────────────────────────────────────────────────

    def _confirmar_devolucion(self, prestamo: dict):
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
        self._cargar_historial_completo()

    # ── Mensaje de Estado / Feedback ──────────────────────────────────────────

    def _mostrar_estado(self, mensaje: str, es_error: bool = False):
        if self._timer_estado is not None:
            self.after_cancel(self._timer_estado)

        color = COLOR_ERROR if es_error else COLOR_EXITO
        self.etiqueta_estado.configure(text=mensaje, text_color=color)

        if not es_error:
            self._timer_estado = self.after(4000, lambda: self.etiqueta_estado.configure(text=""))
