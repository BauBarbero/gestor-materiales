"""
app.py — GestorEFi
Ventana principal post-login.
Compuesta por un sidebar de navegación (Dark Blue) y un área de contenido (Light Gray)
que intercambia frames según la sección seleccionada.
Los ítems del menú se ajustan automáticamente al rol del usuario (ADMIN / CONSULTA).
"""

import customtkinter
from tkinter import messagebox

from gui.inventory_frame import InventoryFrame
from gui.loans_frame import LoansFrame
from gui.audit_frame import AuditFrame

# ─── Paleta de colores ────────────────────────────────────────────────────────
COLOR_PRIMARIO        = "#1e3a8a"   # Dark Blue — sidebar
COLOR_NAV_HOVER       = "#2d4fa3"   # Azul medio — botón hover
COLOR_NAV_ACTIVO      = "#1e40af"   # Azul — botón seleccionado
COLOR_FONDO           = "#f8fafc"   # Light Gray — área de contenido
COLOR_BLANCO          = "#ffffff"   # Tarjetas / cards
COLOR_TEXTO_CLARO     = "#eff6ff"   # Off-white para texto sobre azul
COLOR_SUBTITULO_NAV   = "#93c5fd"   # Azul claro — rol de usuario en sidebar
COLOR_TEXTO_OSCURO    = "#1e293b"   # Dark slate — texto principal en contenido
COLOR_TEXTO_SECUNDARIO = "#64748b"  # Gris — texto secundario
COLOR_BORDE           = "#e2e8f0"   # Gris suave — bordes de cards

# ─── Ítems de navegación por rol ─────────────────────────────────────────────
# Formato: (etiqueta, ícono, id_sección)
_NAV_CONSULTA: list[tuple[str, str, str]] = [
    ("Inventario",  "📦", "inventario"),
    ("Préstamos",   "🏃", "prestamos"),
]

_NAV_ADMIN: list[tuple[str, str, str]] = _NAV_CONSULTA + [
    ("Auditoría",   "📋", "auditoria"),
    ("Usuarios",    "👥", "usuarios"),
]


# ─────────────────────────────────────────────────────────────────────────────
# PANTALLA DE BIENVENIDA
# ─────────────────────────────────────────────────────────────────────────────

class PantallaInicio(customtkinter.CTkFrame):
    """
    Frame de bienvenida que se muestra al ingresar al sistema.
    Presenta un saludo personalizado y tarjetas de acceso rápido a cada módulo.
    """

    def __init__(self, master, username: str, rol: str, callback_navegar=None, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.callback_navegar = callback_navegar
        self._construir(username, rol)

    def _construir(self, username: str, rol: str):
        rol_legible = "Administrador" if rol == "ADMIN" else "Consulta / Recreo"

        # ── Barra de saludo ──────────────────────────────────────────────────
        barra = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        barra.pack(fill="x", padx=28, pady=(28, 14))

        customtkinter.CTkLabel(
            barra,
            text=f"Bienvenido/a, {username} 👋",
            font=customtkinter.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=24, pady=(20, 4))

        customtkinter.CTkLabel(
            barra,
            text=(
                f"Rol activo: {rol_legible}  ·  "
                "Sistema funcionando en modo local (sin conexión a internet)."
            ),
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=24, pady=(0, 20))

        # ── Título de sección ────────────────────────────────────────────────
        customtkinter.CTkLabel(
            self,
            text="Acceso rápido",
            font=customtkinter.CTkFont(size=14, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=28, pady=(6, 10))

        # ── Cards de módulos disponibles ─────────────────────────────────────
        cards_base = [
            ("📦", "Inventario",
             "Consultá el stock disponible\nde materiales del depósito.",
             "inventario"),
            ("🏃", "Préstamos",
             "Registrá préstamos rápidos\na alumnos durante el recreo.",
             "prestamos"),
        ]
        cards_admin = [
            ("📋", "Auditoría",
             "Registrá bajas definitivas\npor rotura o pérdida.",
             "auditoria"),
            ("👥", "Usuarios",
             "Gestioná el acceso\nal sistema.",
             "usuarios"),
        ]
        cards = cards_base + (cards_admin if rol == "ADMIN" else [])

        contenedor_cards = customtkinter.CTkFrame(self, fg_color="transparent")
        contenedor_cards.pack(anchor="w", padx=28, pady=(0, 28))

        for icono, titulo, descripcion, seccion_id in cards:
            card = customtkinter.CTkFrame(
                contenedor_cards,
                fg_color=COLOR_BLANCO,
                corner_radius=12,
                border_width=1,
                border_color=COLOR_BORDE,
                width=200,
                cursor="hand2" if self.callback_navegar else ""
            )
            card.pack(side="left", padx=(0, 14), pady=4)
            card.pack_propagate(False)

            customtkinter.CTkLabel(
                card, text=icono,
                font=customtkinter.CTkFont(size=32)
            ).pack(pady=(20, 6))

            customtkinter.CTkLabel(
                card, text=titulo,
                font=customtkinter.CTkFont(size=13, weight="bold"),
                text_color=COLOR_TEXTO_OSCURO
            ).pack()

            customtkinter.CTkLabel(
                card, text=descripcion,
                font=customtkinter.CTkFont(size=11),
                text_color=COLOR_TEXTO_SECUNDARIO,
                justify="center"
            ).pack(pady=(6, 20), padx=10)

            if self.callback_navegar:
                self._bind_card_click(card, seccion_id)

    def _bind_card_click(self, widget, seccion_id: str):
        widget.bind("<Button-1>", lambda _: self.callback_navegar(seccion_id))
        for hijo in widget.winfo_children():
            self._bind_card_click(hijo, seccion_id)


# ─────────────────────────────────────────────────────────────────────────────
# PLACEHOLDER PARA SECCIONES NO IMPLEMENTADAS
# ─────────────────────────────────────────────────────────────────────────────

class _PlaceholderFrame(customtkinter.CTkFrame):
    """
    Frame genérico de marcador de posición.
    Se usa para secciones que se implementarán en fases posteriores.
    """

    def __init__(self, master, titulo: str, fase: str, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        contenedor = customtkinter.CTkFrame(self, fg_color="transparent")
        contenedor.grid(row=0, column=0)

        customtkinter.CTkLabel(
            contenedor, text="🚧",
            font=customtkinter.CTkFont(size=52)
        ).pack(pady=(0, 12))

        customtkinter.CTkLabel(
            contenedor, text=titulo,
            font=customtkinter.CTkFont(size=22, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack()

        customtkinter.CTkLabel(
            contenedor, text=f"Módulo en desarrollo — {fase}",
            font=customtkinter.CTkFont(size=13),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(pady=(8, 0))


# ─────────────────────────────────────────────────────────────────────────────
# VENTANA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────────────

class App(customtkinter.CTkFrame):
    """
    Frame principal de la aplicación (post-login).
    Layout: sidebar de 220 px a la izquierda + área de contenido a la derecha.
    """

    def __init__(self, master, username: str, rol: str, callback_logout, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.username       = username
        self.rol            = rol
        self.callback_logout = callback_logout
        self._frame_activo  = None
        self._botones_nav: dict[str, customtkinter.CTkButton] = {}

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)  # El área de contenido se expande

        self._construir_sidebar()
        self._construir_area_contenido()
        self._navegar("inicio")   # Mostrar pantalla de bienvenida al arrancar

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _construir_sidebar(self):
        """Panel de navegación lateral con logo, menú y datos del usuario."""
        sidebar = customtkinter.CTkFrame(
            self, fg_color=COLOR_PRIMARIO, corner_radius=0, width=222
        )
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.rowconfigure(2, weight=1)  # El área de nav se expande verticalmente
        sidebar.columnconfigure(0, weight=1)

        # ── Logo ─────────────────────────────────────────────────────────────
        marco_logo = customtkinter.CTkFrame(
            sidebar, fg_color="transparent", corner_radius=0
        )
        marco_logo.grid(row=0, column=0, sticky="ew")

        customtkinter.CTkLabel(
            marco_logo,
            text="🏫  GestorEFi",
            font=customtkinter.CTkFont(size=17, weight="bold"),
            text_color=COLOR_TEXTO_CLARO
        ).pack(padx=18, pady=20, anchor="w")

        # ── Separador ────────────────────────────────────────────────────────
        customtkinter.CTkFrame(
            sidebar, fg_color="#2d4fa3", corner_radius=0, height=1
        ).grid(row=1, column=0, sticky="ew")

        # ── Botones de navegación ─────────────────────────────────────────────
        marco_nav = customtkinter.CTkFrame(
            sidebar, fg_color="transparent", corner_radius=0
        )
        marco_nav.grid(row=2, column=0, sticky="nsew")

        items = _NAV_ADMIN if self.rol == "ADMIN" else _NAV_CONSULTA
        for texto, icono, seccion_id in items:
            btn = customtkinter.CTkButton(
                marco_nav,
                text=f"  {icono}  {texto}",
                font=customtkinter.CTkFont(size=13),
                fg_color="transparent",
                hover_color=COLOR_NAV_HOVER,
                text_color=COLOR_TEXTO_CLARO,
                anchor="w",
                height=48,
                corner_radius=0,
                command=lambda s=seccion_id: self._navegar(s)
            )
            btn.pack(fill="x", pady=1)
            self._botones_nav[seccion_id] = btn

        # ── Separador inferior ────────────────────────────────────────────────
        customtkinter.CTkFrame(
            sidebar, fg_color="#2d4fa3", corner_radius=0, height=1
        ).grid(row=3, column=0, sticky="ew")

        # ── Información del usuario ───────────────────────────────────────────
        marco_usuario = customtkinter.CTkFrame(
            sidebar, fg_color="transparent", corner_radius=0
        )
        marco_usuario.grid(row=4, column=0, sticky="ew")

        rol_legible = "Administrador" if self.rol == "ADMIN" else "Consulta"

        customtkinter.CTkLabel(
            marco_usuario,
            text=f"👤  {self.username}",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_CLARO
        ).pack(padx=18, pady=(16, 3), anchor="w")

        customtkinter.CTkLabel(
            marco_usuario,
            text=rol_legible,
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_SUBTITULO_NAV
        ).pack(padx=18, pady=(0, 10), anchor="w")

        # ── Botón Cerrar Sesión ───────────────────────────────────────────────
        customtkinter.CTkButton(
            marco_usuario,
            text="Cerrar Sesión",
            font=customtkinter.CTkFont(size=12),
            fg_color="transparent",
            hover_color="#7f1d1d",
            text_color="#fca5a5",
            border_width=1,
            border_color="#60a5fa",
            height=36,
            corner_radius=7,
            command=self._confirmar_logout
        ).pack(fill="x", padx=14, pady=(0, 16))

    # ── Área de contenido ─────────────────────────────────────────────────────

    def _construir_area_contenido(self):
        """Contenedor derecho que aloja el frame de la sección activa."""
        self._area = customtkinter.CTkFrame(
            self, fg_color=COLOR_FONDO, corner_radius=0
        )
        self._area.grid(row=0, column=1, sticky="nsew")
        self._area.rowconfigure(0, weight=1)
        self._area.columnconfigure(0, weight=1)

    # ── Navegación ────────────────────────────────────────────────────────────

    def _navegar(self, seccion_id: str):
        """Destruye el frame activo y carga el frame de la sección indicada."""
        if self._frame_activo is not None:
            self._frame_activo.destroy()

        self._marcar_boton_activo(seccion_id)
        nuevo_frame = self._crear_frame(seccion_id)
        nuevo_frame.grid(row=0, column=0, sticky="nsew")
        self._frame_activo = nuevo_frame

    def _marcar_boton_activo(self, seccion_id: str):
        """Resalta el botón del sidebar que corresponde a la sección activa."""
        for sid, btn in self._botones_nav.items():
            btn.configure(
                fg_color=COLOR_NAV_ACTIVO if sid == seccion_id else "transparent"
            )

    def _crear_frame(self, seccion_id: str) -> customtkinter.CTkFrame:
        """Instancia y retorna el frame correspondiente a la sección solicitada."""
        if seccion_id == "inicio":
            return PantallaInicio(self._area, self.username, self.rol, callback_navegar=self._navegar)

        elif seccion_id == "inventario":
            return InventoryFrame(self._area, self.username, self.rol)
        elif seccion_id == "prestamos":
            return LoansFrame(self._area, self.username, self.rol)
        elif seccion_id == "auditoria":
            return AuditFrame(self._area, self.username, self.rol)
        elif seccion_id == "usuarios":
            # TODO Fase 5: reemplazar por UsersFrame
            return _PlaceholderFrame(
                self._area, "👥  Gestión de Usuarios", "Fase 5"
            )
        else:
            return _PlaceholderFrame(self._area, "Sección desconocida", "")

    # ── Logout ────────────────────────────────────────────────────────────────

    def _confirmar_logout(self):
        """Pide confirmación antes de cerrar la sesión actual."""
        confirmar = messagebox.askyesno(
            "Cerrar Sesión",
            f"¿Querés cerrar la sesión de «{self.username}»?"
        )
        if confirmar:
            self.callback_logout()
