"""
audit_frame.py — GestorEFi
Módulo de Auditoría y Bajas Definitivas (Fase 5).

Permite a los administradores:
1. Registrar bajas definitivas de materiales por rotura, pérdida o robo.
2. Descontar en una única transacción tanto el stock total como el disponible.
3. Registrar al usuario administrador como responsable del hecho de forma automática.
4. Consultar el historial cronológico completo de bajas con filtros de búsqueda.
5. Protección estricta: accesible únicamente para usuarios con rol ADMIN.
"""

import customtkinter
from tkinter import messagebox
from datetime import datetime

from database.queries import (
    obtener_materiales,
    registrar_baja,
    obtener_historial_bajas,
)

# ─── Paleta de colores institucional ──────────────────────────────────────────
COLOR_PRIMARIO         = "#1e3a8a"   # Dark Blue
COLOR_HOVER_BTN        = "#1e40af"
COLOR_FONDO            = "#f8fafc"   # Light Gray
COLOR_BLANCO           = "#ffffff"
COLOR_TEXTO_CLARO      = "#eff6ff"
COLOR_TEXTO_OSCURO     = "#1e293b"
COLOR_TEXTO_SECUNDARIO = "#64748b"
COLOR_BORDE            = "#e2e8f0"
COLOR_ENCABEZADO       = "#1e3a8a"
COLOR_FILA_PAR         = "#f8fafc"
COLOR_FILA_IMPAR       = "#ffffff"
COLOR_FILA_HOVER       = "#fee2e2"   # Suave rojizo para filas de baja
COLOR_PELIGRO          = "#dc2626"   # Rojo para bajas definitivas
COLOR_HOVER_PELIGRO    = "#b91c1c"
COLOR_ADVERTENCIA      = "#d97706"   # Ámbar
COLOR_EXITO            = "#16a34a"   # Verde

# ─── Opciones válidas para motivo de baja ─────────────────────────────────────
MOTIVOS_BAJA = ["Rotura", "Pérdida", "Robado"]

# Colores para badges de motivo
COLOR_BADGE_MOTIVO = {
    "Rotura":  ("#ffedd5", "#c2410c"),  # Fondo naranja suave, texto oscuro
    "Pérdida": ("#fef3c7", "#b45309"),  # Fondo ámbar suave, texto oscuro
    "Robado":  ("#fee2e2", "#b91c1c"),  # Fondo rojo suave, texto oscuro
}

# ─── Columnas de la tabla de auditoría ────────────────────────────────────────
_COLUMNAS_AUDITORIA: list[tuple[str, int, str]] = [
    ("MATERIAL",          3, "w"),
    ("CANTIDAD",          1, "center"),
    ("MOTIVO",            2, "center"),
    ("RESPONSABLE",       2, "center"),
    ("FECHA Y HORA",      2, "center"),
]


class _FilaAuditoria(customtkinter.CTkFrame):
    """
    Representa una fila en el historial de bajas definitivas.
    """

    def __init__(self, master, baja: dict, index: int):
        color_base = COLOR_FILA_PAR if index % 2 == 0 else COLOR_FILA_IMPAR
        super().__init__(master, fg_color=color_base, corner_radius=0)
        self.baja = baja

        pesos = [c[1] for c in _COLUMNAS_AUDITORIA]
        for col_idx, peso in enumerate(pesos):
            self.columnconfigure(col_idx, weight=peso)

        # ── 1. Material ──────────────────────────────────────────────────────
        lbl_mat = customtkinter.CTkLabel(
            self,
            text=baja.get("material", "Material"),
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        )
        lbl_mat.grid(row=0, column=0, sticky="ew", padx=(16, 8), pady=11)

        # ── 2. Cantidad ──────────────────────────────────────────────────────
        lbl_cant = customtkinter.CTkLabel(
            self,
            text=f"-{baja.get('cantidad', 0)} u.",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_PELIGRO,
            anchor="center"
        )
        lbl_cant.grid(row=0, column=1, sticky="ew", padx=8, pady=11)

        # ── 3. Motivo (Badge) ────────────────────────────────────────────────
        motivo = baja.get("motivo", "Otro")
        bg_badge, fg_badge = COLOR_BADGE_MOTIVO.get(motivo, ("#f1f5f9", "#475569"))

        frame_badge = customtkinter.CTkFrame(self, fg_color="transparent")
        frame_badge.grid(row=0, column=2, padx=8, pady=11)

        lbl_motivo = customtkinter.CTkLabel(
            frame_badge,
            text=f"  {motivo}  ",
            font=customtkinter.CTkFont(size=11, weight="bold"),
            fg_color=bg_badge,
            text_color=fg_badge,
            corner_radius=6
        )
        lbl_motivo.pack()

        # ── 4. Responsable ───────────────────────────────────────────────────
        lbl_resp = customtkinter.CTkLabel(
            self,
            text=f"👤 {baja.get('responsable_registro', '—')}",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="center"
        )
        lbl_resp.grid(row=0, column=3, sticky="ew", padx=8, pady=11)

        # ── 5. Fecha y Hora ──────────────────────────────────────────────────
        fecha_fmt = self._formatear_fecha(baja.get("fecha", ""))
        lbl_fecha = customtkinter.CTkLabel(
            self,
            text=fecha_fmt,
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO,
            anchor="center"
        )
        lbl_fecha.grid(row=0, column=4, sticky="ew", padx=(8, 16), pady=11)

        # Separador inferior
        sep = customtkinter.CTkFrame(self, fg_color=COLOR_BORDE, height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=len(_COLUMNAS_AUDITORIA), sticky="ew")

    @staticmethod
    def _formatear_fecha(fecha_str: str) -> str:
        """Formatea 'YYYY-MM-DD HH:MM:SS' a 'DD/MM/YYYY HH:MM hs'."""
        if not fecha_str:
            return "—"
        try:
            dt = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M hs")
        except Exception:
            return str(fecha_str)


class AuditFrame(customtkinter.CTkFrame):
    """
    Frame del módulo de Auditoría y Bajas Definitivas.

    Layout:
    ┌────────────────────────────────────────────────────────────────────────┐
    │  Barra superior: Título + Badge de total de bajas + Refrescar          │
    ├───────────────────────────────────┬────────────────────────────────────┤
    │  Columna izquierda (Formulario):   │  Columna derecha (Historial):      │
    │  - Material con stock disponible  │  - Buscador en tiempo real         │
    │  - Cantidad a dar de baja         │  - Encabezado de tabla             │
    │  - Motivo (Rotura/Pérdida/Robo)   │  - Lista scrolleable de bajas      │
    │  - Responsable (auto-completado)  │  - Métricas de bajas               │
    │  - Botón: Confirmar Baja          │                                    │
    └───────────────────────────────────┴────────────────────────────────────┘
    """

    def __init__(self, master, username: str, rol: str, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.username = username
        self.rol      = rol

        # ── Restricción de Rol ───────────────────────────────────────────────
        if self.rol != "ADMIN":
            self._construir_acceso_denegado()
            return

        self._mapa_materiales: dict[str, dict] = {}
        self._historial_todos: list[dict] = []
        self._historial_vis:   list[dict] = []
        self._timer_estado = None
        self._timer_busqueda = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._construir_barra_superior()
        self._construir_cuerpo()

        # Cargar datos
        self._cargar_materiales()
        self._cargar_historial()

    # ── Pantalla de Acceso Denegado (Protección de Rol) ───────────────────────

    def _construir_acceso_denegado(self):
        """Pantalla mostrada si un rol no autorizado intenta acceder al frame."""
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        tarjeta = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO, corner_radius=16,
            border_width=1, border_color=COLOR_BORDE
        )
        tarjeta.grid(row=0, column=0, padx=40, pady=40)

        customtkinter.CTkLabel(
            tarjeta, text="🔒", font=customtkinter.CTkFont(size=56)
        ).pack(pady=(36, 12), padx=48)

        customtkinter.CTkLabel(
            tarjeta,
            text="Acceso Restringido",
            font=customtkinter.CTkFont(size=22, weight="bold"),
            text_color=COLOR_PELIGRO
        ).pack(padx=48)

        customtkinter.CTkLabel(
            tarjeta,
            text=(
                "El módulo de Auditoría y Bajas está reservado exclusivamente\n"
                "para usuarios con rol Administrador (ADMIN).\n\n"
                f"Tu rol actual es: {self.rol}."
            ),
            font=customtkinter.CTkFont(size=13),
            text_color=COLOR_TEXTO_SECUNDARIO,
            justify="center"
        ).pack(padx=48, pady=(12, 36))

    # ── Barra Superior ────────────────────────────────────────────────────────

    def _construir_barra_superior(self):
        barra = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        barra.grid(row=0, column=0, sticky="ew", padx=28, pady=(28, 14))
        barra.columnconfigure(0, weight=1)

        # Lado izquierdo
        lado_izq = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_izq.grid(row=0, column=0, sticky="w", padx=24, pady=16)

        customtkinter.CTkLabel(
            lado_izq,
            text="📋  Auditoría y Bajas Definitivas",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(side="left")

        customtkinter.CTkLabel(
            lado_izq,
            text="  ·  Control de roturas, pérdidas y descartes",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(side="left", pady=(3, 0))

        # Lado derecho: Contador y botón de refresco
        lado_der = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_der.grid(row=0, column=1, sticky="e", padx=24, pady=16)

        self.etiqueta_badge = customtkinter.CTkLabel(
            lado_der,
            text="0 registros",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color="#fee2e2",
            text_color=COLOR_PELIGRO,
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

    # ── Cuerpo Principal ──────────────────────────────────────────────────────

    def _construir_cuerpo(self):
        cuerpo = customtkinter.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))
        cuerpo.rowconfigure(0, weight=1)
        cuerpo.columnconfigure(0, weight=0)  # Formulario: ancho fijo
        cuerpo.columnconfigure(1, weight=1)  # Historial: expandible

        self._construir_formulario(cuerpo)
        self._construir_tabla_historial(cuerpo)

    # ── Formulario de Registro de Baja (Columna Izquierda) ─────────────────────

    def _construir_formulario(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE,
            width=380
        )
        tarjeta.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        tarjeta.grid_propagate(False)

        # Encabezado
        customtkinter.CTkLabel(
            tarjeta,
            text="⚠️  Registrar Baja",
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=24, pady=(22, 2))

        customtkinter.CTkLabel(
            tarjeta,
            text="Descuento definitivo del inventario escolar.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=24, pady=(0, 16))

        # ── Campo: Material ───────────────────────────────────────────────────
        self._label_campo(tarjeta, "Material afectado")
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

        # ── Campo: Cantidad ───────────────────────────────────────────────────
        self._label_campo(tarjeta, "Cantidad a dar de baja")
        self.campo_cantidad = customtkinter.CTkEntry(
            tarjeta,
            placeholder_text="Ej: 1",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9,
            height=42
        )
        self.campo_cantidad.insert(0, "1")
        self.campo_cantidad.pack(fill="x", padx=24, pady=(0, 12))

        # ── Campo: Motivo ─────────────────────────────────────────────────────
        self._label_campo(tarjeta, "Motivo de la baja")
        self.var_motivo = customtkinter.StringVar(value=MOTIVOS_BAJA[0])
        self.combo_motivo = customtkinter.CTkOptionMenu(
            tarjeta,
            variable=self.var_motivo,
            values=MOTIVOS_BAJA,
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
        self.combo_motivo.pack(fill="x", padx=24, pady=(0, 12))

        # ── Campo: Responsable (Auto-capturado del usuario actual) ─────────────
        self._label_campo(tarjeta, "Responsable del registro")
        marco_resp = customtkinter.CTkFrame(
            tarjeta, fg_color=COLOR_FONDO, corner_radius=9,
            border_width=1, border_color=COLOR_BORDE, height=42
        )
        marco_resp.pack(fill="x", padx=24, pady=(0, 14))
        marco_resp.pack_propagate(False)

        customtkinter.CTkLabel(
            marco_resp,
            text=f"👤  {self.username}  (Administrador)",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(side="left", padx=14, pady=10)

        # ── Mensaje de estado ─────────────────────────────────────────────────
        self.etiqueta_estado = customtkinter.CTkLabel(
            tarjeta,
            text="",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_PELIGRO,
            wraplength=330,
            height=18
        )
        self.etiqueta_estado.pack(padx=24, pady=(0, 6))

        # ── Botón Confirmar Baja ──────────────────────────────────────────────
        self.btn_registrar = customtkinter.CTkButton(
            tarjeta,
            text="⚠️  Registrar Baja Definitiva",
            font=customtkinter.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_PELIGRO,
            hover_color=COLOR_HOVER_PELIGRO,
            text_color=COLOR_TEXTO_CLARO,
            height=44,
            corner_radius=9,
            command=self._enviar_baja
        )
        self.btn_registrar.pack(fill="x", padx=24, pady=(0, 22))

    def _label_campo(self, parent, texto: str):
        customtkinter.CTkLabel(
            parent,
            text=texto,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        ).pack(fill="x", padx=24, pady=(0, 4))

    # ── Tabla de Historial de Bajas (Columna Derecha) ─────────────────────────

    def _construir_tabla_historial(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta.grid(row=0, column=1, sticky="nsew")
        tarjeta.rowconfigure(2, weight=1)
        tarjeta.columnconfigure(0, weight=1)

        # ── Barra de búsqueda ─────────────────────────────────────────────────
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
            placeholder_text="Buscar por material, motivo o responsable…",
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

        pesos = [c[1] for c in _COLUMNAS_AUDITORIA]
        for idx, peso in enumerate(pesos):
            cabecera.columnconfigure(idx, weight=peso)

        for col_idx, (titulo, _, ancla) in enumerate(_COLUMNAS_AUDITORIA):
            customtkinter.CTkLabel(
                cabecera,
                text=titulo,
                font=customtkinter.CTkFont(size=11, weight="bold"),
                text_color=COLOR_TEXTO_CLARO,
                anchor=ancla
            ).grid(
                row=0, column=col_idx, sticky="ew",
                padx=(16 if col_idx == 0 else 8, 16 if col_idx == len(_COLUMNAS_AUDITORIA) - 1 else 8),
                pady=11
            )

        # ── Área Scrolleable ──────────────────────────────────────────────────
        self.scroll_filas = customtkinter.CTkScrollableFrame(
            tarjeta, fg_color="transparent", corner_radius=0
        )
        self.scroll_filas.grid(row=2, column=0, sticky="nsew")
        self.scroll_filas.columnconfigure(0, weight=1)

        # Estado vacío
        self.frame_vacio = customtkinter.CTkFrame(
            self.scroll_filas, fg_color="transparent"
        )
        self.frame_vacio.grid(row=0, column=0, sticky="ew", pady=40)

        self.icono_vacio = customtkinter.CTkLabel(
            self.frame_vacio, text="📋", font=customtkinter.CTkFont(size=44)
        )
        self.icono_vacio.pack(pady=(10, 8))

        self.titulo_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="Sin registros de bajas",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        )
        self.titulo_vacio.pack()

        self.subtitulo_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="No se han registrado roturas ni pérdidas en el sistema.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.subtitulo_vacio.pack(pady=(4, 20))

    # ── Carga de Datos ────────────────────────────────────────────────────────

    def _cargar_materiales(self):
        """Carga materiales con stock_disponible > 0 en el menú de bajas."""
        try:
            todos = obtener_materiales()
            con_stock = [dict(m) for m in todos if m["stock_disponible"] > 0]
        except RuntimeError as e:
            self._mostrar_estado(f"Error cargando materiales: {e}", es_error=True)
            con_stock = []

        self._mapa_materiales.clear()
        opciones = []

        for m in con_stock:
            etiqueta = f"{m['nombre']}  ·  {m['stock_disponible']} disp. (Total: {m['stock_total']})"
            self._mapa_materiales[etiqueta] = m
            opciones.append(etiqueta)

        if opciones:
            self.combo_material.configure(values=opciones, state="normal")
            actual = self.var_material.get()
            if actual in self._mapa_materiales:
                self.var_material.set(actual)
            else:
                self.var_material.set(opciones[0])
            self.btn_registrar.configure(state="normal")
        else:
            self.combo_material.configure(values=["Sin materiales con stock disponible"], state="disabled")
            self.var_material.set("Sin materiales con stock disponible")
            self.btn_registrar.configure(state="disabled")

    def _cargar_historial(self):
        """Recupera el historial de bajas desde la base de datos."""
        try:
            rows = obtener_historial_bajas()
            self._historial_todos = [dict(r) for r in rows]
        except RuntimeError as e:
            messagebox.showerror("Error de base de datos", str(e), parent=self)
            self._historial_todos = []

        total = len(self._historial_todos)
        self.etiqueta_badge.configure(
            text=f"{total} baja{'s' if total != 1 else ''}"
        )
        self._aplicar_filtro_busqueda()

    def _refrescar_todo(self):
        self._cargar_materiales()
        self._cargar_historial()

    # ── Búsqueda y Filtrado ───────────────────────────────────────────────────

    def _on_busqueda_cambia(self, *_args):
        if self._timer_busqueda is not None:
            self.after_cancel(self._timer_busqueda)
        self._timer_busqueda = self.after(200, self._aplicar_filtro_busqueda)

    def _aplicar_filtro_busqueda(self):
        query = self.var_busqueda.get().strip().lower()
        if not query:
            self._historial_vis = self._historial_todos
        else:
            self._historial_vis = [
                b for b in self._historial_todos
                if query in b.get("material", "").lower()
                or query in b.get("motivo", "").lower()
                or query in b.get("responsable_registro", "").lower()
            ]
        self._renderizar_tabla(query_activa=bool(query))

    def _renderizar_tabla(self, query_activa: bool = False):
        for widget in self.scroll_filas.winfo_children():
            if widget != self.frame_vacio:
                widget.destroy()

        if not self._historial_vis:
            self.frame_vacio.grid()
            if query_activa:
                self.icono_vacio.configure(text="🔍")
                self.titulo_vacio.configure(text="Sin coincidencias")
                self.subtitulo_vacio.configure(text="No se encontraron registros de baja para esa búsqueda.")
            else:
                self.icono_vacio.configure(text="📋")
                self.titulo_vacio.configure(text="Sin registros de bajas")
                self.subtitulo_vacio.configure(text="No se han registrado roturas ni pérdidas en el sistema.")
            return

        self.frame_vacio.grid_remove()

        for idx, baja in enumerate(self._historial_vis):
            fila = _FilaAuditoria(self.scroll_filas, baja=baja, index=idx)
            fila.grid(row=idx, column=0, sticky="ew")

    # ── Envío de Baja Definitiva ──────────────────────────────────────────────

    def _enviar_baja(self):
        """Valida y registra la baja en la base de datos previa confirmación modal."""
        etiqueta_sel = self.var_material.get()
        mat_info = self._mapa_materiales.get(etiqueta_sel)

        if not mat_info:
            self._mostrar_estado("Seleccioná un material con stock disponible.", es_error=True)
            return

        cant_str = self.campo_cantidad.get().strip()
        if not cant_str.isdigit() or int(cant_str) <= 0:
            self._mostrar_estado("La cantidad debe ser un número entero mayor a 0.", es_error=True)
            self.campo_cantidad.focus()
            return

        cantidad = int(cant_str)
        disponible = mat_info.get("stock_disponible", 0)

        if cantidad > disponible:
            self._mostrar_estado(
                f"No podés dar de baja {cantidad} u. (Solo hay {disponible} disponibles).",
                es_error=True
            )
            self.campo_cantidad.focus()
            return

        motivo = self.var_motivo.get()
        material_id = mat_info["id"]
        material_nombre = mat_info["nombre"]

        # Confirmación obligatoria para evitar bajas accidentales
        confirmar = messagebox.askyesno(
            "Confirmar Baja Definitiva",
            f"¿Estás seguro/a de registrar la baja definitiva?\n\n"
            f"• Material: {material_nombre}\n"
            f"• Cantidad: {cantidad} unidad{'es' if cantidad != 1 else ''}\n"
            f"• Motivo: {motivo}\n"
            f"• Responsable: {self.username}\n\n"
            "⚠️ Esta acción reducirá el stock total y disponible y no se puede deshacer.",
            parent=self
        )

        if not confirmar:
            return

        self.btn_registrar.configure(state="disabled", text="Registrando baja...")

        try:
            registrar_baja(
                material_id=material_id,
                cantidad=cantidad,
                motivo=motivo,
                responsable=self.username
            )
        except (ValueError, RuntimeError) as e:
            self._mostrar_estado(str(e), es_error=True)
            self.btn_registrar.configure(state="normal", text="⚠️  Registrar Baja Definitiva")
            return

        # Éxito: restablecer formulario
        self.campo_cantidad.delete(0, "end")
        self.campo_cantidad.insert(0, "1")
        self.btn_registrar.configure(state="normal", text="⚠️  Registrar Baja Definitiva")

        self._mostrar_estado(f"✓ Baja de {cantidad} u. de '{material_nombre}' registrada.", es_error=False)
        self._cargar_materiales()
        self._cargar_historial()

    def _mostrar_estado(self, mensaje: str, es_error: bool = False):
        if self._timer_estado is not None:
            self.after_cancel(self._timer_estado)

        color = COLOR_PELIGRO if es_error else COLOR_EXITO
        self.etiqueta_estado.configure(text=mensaje, text_color=color)

        if not es_error:
            self._timer_estado = self.after(4000, lambda: self.etiqueta_estado.configure(text=""))
