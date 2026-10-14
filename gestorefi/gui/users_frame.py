"""
users_frame.py — GestorEFi
Módulo de Gestión de Usuarios (Exclusivo para ADMIN).

Permite:
1. Listar todos los usuarios del sistema con sus roles (ADMIN / CONSULTA).
2. Crear nuevos usuarios con almacenamiento seguro mediante hashes SHA-256.
3. Restablecer la contraseña de cualquier usuario.
4. Eliminar usuarios (previniendo la auto-eliminación de la cuenta en uso).
5. Búsqueda y filtrado dinámico.
6. Restricción estricta de seguridad por rol.
"""

import customtkinter
from tkinter import messagebox

from database.queries import (
    obtener_todos_los_usuarios,
    crear_usuario,
    cambiar_password,
    eliminar_usuario,
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
COLOR_FILA_SELECCION   = "#dbeafe"
COLOR_EXITO            = "#16a34a"   # Verde
COLOR_HOVER_EXITO      = "#15803d"
COLOR_PELIGRO          = "#dc2626"   # Rojo
COLOR_HOVER_PELIGRO    = "#b91c1c"
COLOR_AZUL_ACCION      = "#0284c7"
COLOR_HOVER_AZUL       = "#0369a1"

# ─── Badges de rol ────────────────────────────────────────────────────────────
COLOR_BADGE_ROL = {
    "ADMIN":    ("#dbeafe", "#1e40af"),  # Azul suave
    "CONSULTA": ("#f1f5f9", "#475569"),  # Gris pizarra suave
}

# ─── Columnas de la tabla de usuarios ─────────────────────────────────────────
_COLUMNAS_USUARIOS: list[tuple[str, int, str]] = [
    ("ID",       1, "center"),
    ("USUARIO",  3, "w"),
    ("ROL",      2, "center"),
    ("ACCIÓN",   2, "center"),
]


class _FilaUsuario(customtkinter.CTkFrame):
    """
    Fila individual en la tabla de usuarios registrados.
    """

    def __init__(self, master, usuario: dict, index: int, es_usuario_actual: bool,
                 on_seleccionar, on_eliminar):
        color_base = COLOR_FILA_PAR if index % 2 == 0 else COLOR_FILA_IMPAR
        super().__init__(master, fg_color=color_base, corner_radius=0, cursor="hand2")
        self.usuario = usuario
        self.color_base = color_base
        self.on_seleccionar = on_seleccionar
        self.on_eliminar = on_eliminar
        self._seleccionada = False

        pesos = [c[1] for c in _COLUMNAS_USUARIOS]
        for col_idx, peso in enumerate(pesos):
            self.columnconfigure(col_idx, weight=peso)

        # 1. ID
        self.lbl_id = customtkinter.CTkLabel(
            self, text=str(usuario.get("id", "")),
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO, anchor="center"
        )
        self.lbl_id.grid(row=0, column=0, sticky="ew", padx=8, pady=10)

        # 2. Nombre de usuario
        nombre_display = usuario.get("username", "")
        if es_usuario_actual:
            nombre_display += "  (tu cuenta)"

        self.lbl_nombre = customtkinter.CTkLabel(
            self, text=nombre_display,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        )
        self.lbl_nombre.grid(row=0, column=1, sticky="ew", padx=(12, 8), pady=10)

        # 3. Rol (Badge)
        rol = usuario.get("rol", "CONSULTA")
        bg_b, fg_b = COLOR_BADGE_ROL.get(rol, ("#f1f5f9", "#475569"))

        frame_badge = customtkinter.CTkFrame(self, fg_color="transparent")
        frame_badge.grid(row=0, column=2, padx=8, pady=8)

        self.lbl_rol = customtkinter.CTkLabel(
            frame_badge,
            text=f"  {rol}  ",
            font=customtkinter.CTkFont(size=11, weight="bold"),
            fg_color=bg_b, text_color=fg_b, corner_radius=6
        )
        self.lbl_rol.pack()

        # 4. Acción: Eliminar
        if es_usuario_actual:
            lbl_bloq = customtkinter.CTkLabel(
                self, text="—", font=customtkinter.CTkFont(size=12),
                text_color=COLOR_TEXTO_SECUNDARIO, anchor="center"
            )
            lbl_bloq.grid(row=0, column=3, padx=(8, 14), pady=6)
        else:
            btn_del = customtkinter.CTkButton(
                self, text="🗑️ Eliminar",
                font=customtkinter.CTkFont(size=11),
                fg_color="transparent", hover_color="#fee2e2",
                text_color=COLOR_PELIGRO, border_width=1,
                border_color="#fca5a5", height=30, width=82,
                corner_radius=7,
                command=lambda: self.on_eliminar(self.usuario)
            )
            btn_del.grid(row=0, column=3, padx=(8, 14), pady=6)

        # Separador inferior
        sep = customtkinter.CTkFrame(self, fg_color=COLOR_BORDE, height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=len(_COLUMNAS_USUARIOS), sticky="ew")

        # Evento de selección de fila para cambio de password
        self.bind("<Button-1>", lambda _: self.on_seleccionar(self.usuario, self))
        self.lbl_id.bind("<Button-1>", lambda _: self.on_seleccionar(self.usuario, self))
        self.lbl_nombre.bind("<Button-1>", lambda _: self.on_seleccionar(self.usuario, self))

    def seleccionar(self):
        self._seleccionada = True
        self.configure(fg_color=COLOR_FILA_SELECCION)

    def deseleccionar(self):
        self._seleccionada = False
        self.configure(fg_color=self.color_base)


class UsersFrame(customtkinter.CTkFrame):
    """
    Frame del módulo de Administración de Usuarios.
    Acceso exclusivo para rol ADMIN.
    """

    def __init__(self, master, username: str, rol: str, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.username = username
        self.rol      = rol

        # ── Restricción Estricta por Rol ─────────────────────────────────────
        if self.rol != "ADMIN":
            self._construir_acceso_denegado()
            return

        self._usuarios_todos: list[dict] = []
        self._usuarios_vis: list[dict] = []
        self._fila_activa: _FilaUsuario | None = None
        self._usuario_para_reset: dict | None = None
        self._timer_busqueda = None
        self._timer_estado_crear = None
        self._timer_estado_reset = None

        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)

        self._construir_barra_superior()
        self._construir_cuerpo()
        self._cargar_usuarios()

    # ── Pantalla de Acceso Denegado ───────────────────────────────────────────

    def _construir_acceso_denegado(self):
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
                "El módulo de Gestión de Usuarios está reservado exclusivamente\n"
                "para cuentas con rol Administrador (ADMIN).\n\n"
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

        lado_izq = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_izq.grid(row=0, column=0, sticky="w", padx=24, pady=16)

        customtkinter.CTkLabel(
            lado_izq,
            text="👥  Gestión de Usuarios",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(side="left")

        customtkinter.CTkLabel(
            lado_izq,
            text="  ·  Administración de cuentas, contraseñas y permisos",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(side="left", pady=(3, 0))

        lado_der = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_der.grid(row=0, column=1, sticky="e", padx=24, pady=16)

        self.etiqueta_badge = customtkinter.CTkLabel(
            lado_der,
            text="0 usuarios",
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
            command=self._cargar_usuarios
        ).pack(side="left")

    # ── Cuerpo Principal ──────────────────────────────────────────────────────

    def _construir_cuerpo(self):
        cuerpo = customtkinter.CTkFrame(self, fg_color="transparent")
        cuerpo.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 28))
        cuerpo.rowconfigure(0, weight=1)
        cuerpo.columnconfigure(0, weight=0)  # Columna formularios: ancho fijo
        cuerpo.columnconfigure(1, weight=1)  # Columna tabla: expandible

        self._construir_columna_formularios(cuerpo)
        self._construir_tarjeta_tabla(cuerpo)

    # ── Columna Formularios (Izquierda) ────────────────────────────────────────

    def _construir_columna_formularios(self, parent):
        columna = customtkinter.CTkFrame(parent, fg_color="transparent", width=380)
        columna.grid(row=0, column=0, sticky="nsew", padx=(0, 16))
        columna.grid_propagate(False)

        # ── Formulario 1: Crear Usuario ───────────────────────────────────────
        tarjeta_crear = customtkinter.CTkFrame(
            columna, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta_crear.pack(fill="x", pady=(0, 14))

        customtkinter.CTkLabel(
            tarjeta_crear,
            text="➕  Registrar Nuevo Usuario",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=20, pady=(16, 2))

        customtkinter.CTkLabel(
            tarjeta_crear,
            text="Creá una cuenta con credenciales locales.",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(anchor="w", padx=20, pady=(0, 12))

        # Usuario
        self._label(tarjeta_crear, "Nombre de usuario")
        self.campo_nuevo_user = customtkinter.CTkEntry(
            tarjeta_crear, placeholder_text="Ej: profesor_gimnasio",
            font=customtkinter.CTkFont(size=12),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=8, height=38
        )
        self.campo_nuevo_user.pack(fill="x", padx=20, pady=(0, 8))

        # Contraseña
        self._label(tarjeta_crear, "Contraseña inicial")
        self.campo_nuevo_pass = customtkinter.CTkEntry(
            tarjeta_crear, placeholder_text="••••••••", show="●",
            font=customtkinter.CTkFont(size=12),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=8, height=38
        )
        self.campo_nuevo_pass.pack(fill="x", padx=20, pady=(0, 8))

        # Rol
        self._label(tarjeta_crear, "Rol de usuario")
        self.combo_nuevo_rol = customtkinter.CTkOptionMenu(
            tarjeta_crear,
            values=["CONSULTA", "ADMIN"],
            font=customtkinter.CTkFont(size=12),
            fg_color=COLOR_FONDO, button_color=COLOR_PRIMARIO,
            button_hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_OSCURO,
            dropdown_fg_color=COLOR_BLANCO,
            dropdown_text_color=COLOR_TEXTO_OSCURO,
            corner_radius=8, height=38
        )
        self.combo_nuevo_rol.pack(fill="x", padx=20, pady=(0, 8))

        # Feedback
        self.lbl_estado_crear = customtkinter.CTkLabel(
            tarjeta_crear, text="", font=customtkinter.CTkFont(size=11),
            text_color=COLOR_PELIGRO, height=16
        )
        self.lbl_estado_crear.pack()

        # Botón
        customtkinter.CTkButton(
            tarjeta_crear,
            text="＋  Crear Usuario",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_EXITO, hover_color=COLOR_HOVER_EXITO,
            text_color=COLOR_TEXTO_CLARO, height=38, corner_radius=8,
            command=self._crear_usuario
        ).pack(fill="x", padx=20, pady=(4, 16))

        # ── Formulario 2: Restablecer Contraseña ──────────────────────────────
        tarjeta_reset = customtkinter.CTkFrame(
            columna, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta_reset.pack(fill="x")

        customtkinter.CTkLabel(
            tarjeta_reset,
            text="🔑  Restablecer Contraseña",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(anchor="w", padx=20, pady=(16, 2))

        self.lbl_info_reset = customtkinter.CTkLabel(
            tarjeta_reset,
            text="Seleccioná un usuario de la tabla para cambiar su clave.",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO,
            wraplength=340
        )
        self.lbl_info_reset.pack(anchor="w", padx=20, pady=(0, 10))

        # Nueva clave
        self._label(tarjeta_reset, "Nueva contraseña (SHA-256)")
        self.campo_reset_pass = customtkinter.CTkEntry(
            tarjeta_reset, placeholder_text="Nueva contraseña segura", show="●",
            font=customtkinter.CTkFont(size=12),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=8, height=38
        )
        self.campo_reset_pass.pack(fill="x", padx=20, pady=(0, 8))

        # Feedback
        self.lbl_estado_reset = customtkinter.CTkLabel(
            tarjeta_reset, text="", font=customtkinter.CTkFont(size=11),
            text_color=COLOR_PELIGRO, height=16
        )
        self.lbl_estado_reset.pack()

        # Botón
        self.btn_reset_pass = customtkinter.CTkButton(
            tarjeta_reset,
            text="🔑  Actualizar Contraseña",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_AZUL_ACCION, hover_color=COLOR_HOVER_AZUL,
            text_color=COLOR_TEXTO_CLARO, height=38, corner_radius=8,
            state="disabled",
            command=self._actualizar_password
        )
        self.btn_reset_pass.pack(fill="x", padx=20, pady=(4, 16))

    def _label(self, parent, texto: str):
        customtkinter.CTkLabel(
            parent, text=texto,
            font=customtkinter.CTkFont(size=11, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        ).pack(fill="x", padx=20, pady=(0, 3))

    # ── Tabla de Usuarios (Derecha) ───────────────────────────────────────────

    def _construir_tarjeta_tabla(self, parent):
        tarjeta = customtkinter.CTkFrame(
            parent, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        tarjeta.grid(row=0, column=1, sticky="nsew")
        tarjeta.rowconfigure(2, weight=1)
        tarjeta.columnconfigure(0, weight=1)

        # Buscador
        barra_busqueda = customtkinter.CTkFrame(tarjeta, fg_color="transparent")
        barra_busqueda.grid(row=0, column=0, sticky="ew", padx=20, pady=14)
        barra_busqueda.columnconfigure(1, weight=1)

        customtkinter.CTkLabel(
            barra_busqueda, text="🔍",
            font=customtkinter.CTkFont(size=15),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).grid(row=0, column=0, padx=(0, 8))

        self.var_busqueda = customtkinter.StringVar()
        self.var_busqueda.trace_add("write", self._on_busqueda_cambia)

        self.campo_busqueda = customtkinter.CTkEntry(
            barra_busqueda,
            textvariable=self.var_busqueda,
            placeholder_text="Buscar por usuario o rol…",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=9, height=38
        )
        self.campo_busqueda.grid(row=0, column=1, sticky="ew")

        # Encabezado
        cabecera = customtkinter.CTkFrame(
            tarjeta, fg_color=COLOR_ENCABEZADO, corner_radius=0
        )
        cabecera.grid(row=1, column=0, sticky="ew")

        pesos = [c[1] for c in _COLUMNAS_USUARIOS]
        for idx, peso in enumerate(pesos):
            cabecera.columnconfigure(idx, weight=peso)

        for col_idx, (titulo, _, ancla) in enumerate(_COLUMNAS_USUARIOS):
            customtkinter.CTkLabel(
                cabecera,
                text=titulo,
                font=customtkinter.CTkFont(size=11, weight="bold"),
                text_color=COLOR_TEXTO_CLARO,
                anchor=ancla
            ).grid(
                row=0, column=col_idx, sticky="ew",
                padx=(14 if col_idx == 0 else 8, 14 if col_idx == len(_COLUMNAS_USUARIOS) - 1 else 8),
                pady=11
            )

        # Scrollable filas
        self.scroll_usuarios = customtkinter.CTkScrollableFrame(
            tarjeta, fg_color="transparent", corner_radius=0
        )
        self.scroll_usuarios.grid(row=2, column=0, sticky="nsew")
        self.scroll_usuarios.columnconfigure(0, weight=1)

        # Placeholder vacío
        self.frame_vacio = customtkinter.CTkFrame(
            self.scroll_usuarios, fg_color="transparent"
        )
        self.frame_vacio.grid(row=0, column=0, sticky="ew", pady=40)

        self.icono_vacio = customtkinter.CTkLabel(
            self.frame_vacio, text="👥", font=customtkinter.CTkFont(size=44)
        )
        self.icono_vacio.pack(pady=(10, 8))

        self.titulo_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="Sin usuarios registrados",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        )
        self.titulo_vacio.pack()

        self.subtitulo_vacio = customtkinter.CTkLabel(
            self.frame_vacio,
            text="No se encontraron usuarios coincidentes.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.subtitulo_vacio.pack(pady=(4, 20))

    # ── Carga y Filtrado de Datos ─────────────────────────────────────────────

    def _cargar_usuarios(self):
        try:
            rows = obtener_todos_los_usuarios()
            self._usuarios_todos = [dict(r) for r in rows]
        except RuntimeError as e:
            messagebox.showerror("Error de base de datos", str(e), parent=self)
            self._usuarios_todos = []

        self.etiqueta_badge.configure(
            text=f"{len(self._usuarios_todos)} usuario{'s' if len(self._usuarios_todos) != 1 else ''}"
        )
        self._aplicar_filtro()

    def _on_busqueda_cambia(self, *_args):
        if self._timer_busqueda is not None:
            self.after_cancel(self._timer_busqueda)
        self._timer_busqueda = self.after(200, self._aplicar_filtro)

    def _aplicar_filtro(self):
        query = self.var_busqueda.get().strip().lower()
        if not query:
            self._usuarios_vis = self._usuarios_todos
        else:
            self._usuarios_vis = [
                u for u in self._usuarios_todos
                if query in u.get("username", "").lower()
                or query in u.get("rol", "").lower()
            ]
        self._renderizar_tabla(query_activa=bool(query))

    def _renderizar_tabla(self, query_activa: bool = False):
        for widget in self.scroll_usuarios.winfo_children():
            if widget != self.frame_vacio:
                widget.destroy()

        if not self._usuarios_vis:
            self.frame_vacio.grid()
            return

        self.frame_vacio.grid_remove()

        for idx, usuario in enumerate(self._usuarios_vis):
            es_actual = (usuario.get("username") == self.username)
            fila = _FilaUsuario(
                self.scroll_usuarios,
                usuario=usuario,
                index=idx,
                es_usuario_actual=es_actual,
                on_seleccionar=self._on_fila_seleccionada,
                on_eliminar=self._confirmar_eliminacion
            )
            fila.grid(row=idx, column=0, sticky="ew")

    # ── Interacciones de Fila ─────────────────────────────────────────────────

    def _on_fila_seleccionada(self, usuario: dict, fila: _FilaUsuario):
        if self._fila_activa and self._fila_activa.winfo_exists():
            self._fila_activa.deseleccionar()

        fila.seleccionar()
        self._fila_activa = fila
        self._usuario_para_reset = usuario

        # Habilitar formulario de reset
        self.btn_reset_pass.configure(state="normal")
        self.lbl_info_reset.configure(
            text=f"Cambiando contraseña para: «{usuario['username']}» ({usuario['rol']})",
            text_color=COLOR_TEXTO_OSCURO
        )
        self.campo_reset_pass.delete(0, "end")
        self.campo_reset_pass.focus()

    # ── Crear Usuario ─────────────────────────────────────────────────────────

    def _crear_usuario(self):
        username = self.campo_nuevo_user.get().strip()
        password = self.campo_nuevo_pass.get()
        rol = self.combo_nuevo_rol.get()

        if not username:
            self._mostrar_estado_crear("Ingresá un nombre de usuario.", es_error=True)
            self.campo_nuevo_user.focus()
            return
        if not password:
            self._mostrar_estado_crear("Ingresá una contraseña inicial.", es_error=True)
            self.campo_nuevo_pass.focus()
            return

        try:
            crear_usuario(username, password, rol)
        except (ValueError, RuntimeError) as e:
            self._mostrar_estado_crear(str(e), es_error=True)
            return

        self.campo_nuevo_user.delete(0, "end")
        self.campo_nuevo_pass.delete(0, "end")
        self._mostrar_estado_crear(f"✓ Usuario «{username}» creado exitosamente.", es_error=False)
        self._cargar_usuarios()

    # ── Actualizar Contraseña ─────────────────────────────────────────────────

    def _actualizar_password(self):
        if not self._usuario_para_reset:
            self._mostrar_estado_reset("Seleccioná un usuario en la tabla primero.", es_error=True)
            return

        nueva_pass = self.campo_reset_pass.get()
        if not nueva_pass:
            self._mostrar_estado_reset("Ingresá la nueva contraseña.", es_error=True)
            self.campo_reset_pass.focus()
            return

        user_id = self._usuario_para_reset["id"]
        username = self._usuario_para_reset["username"]

        try:
            cambiar_password(user_id, nueva_pass)
        except (ValueError, RuntimeError) as e:
            self._mostrar_estado_reset(str(e), es_error=True)
            return

        self.campo_reset_pass.delete(0, "end")
        self._mostrar_estado_reset(f"✓ Clave de «{username}» actualizada.", es_error=False)

    # ── Eliminar Usuario ──────────────────────────────────────────────────────

    def _confirmar_eliminacion(self, usuario: dict):
        user_id = usuario.get("id")
        username = usuario.get("username")

        if username == self.username:
            messagebox.showwarning(
                "Operación no permitida",
                "No podés eliminar tu propia cuenta en uso.",
                parent=self
            )
            return

        confirmar = messagebox.askyesno(
            "Confirmar Eliminación",
            f"¿Estás seguro/a de eliminar al usuario «{username}»?\n\n"
            "Esta acción revocará su acceso al sistema inmediatamente.",
            parent=self
        )
        if not confirmar:
            return

        try:
            eliminar_usuario(user_id)
        except RuntimeError as e:
            messagebox.showerror("Error al eliminar usuario", str(e), parent=self)
            return

        if self._usuario_para_reset and self._usuario_para_reset.get("id") == user_id:
            self._usuario_para_reset = None
            self.btn_reset_pass.configure(state="disabled")
            self.lbl_info_reset.configure(
                text="Seleccioná un usuario de la tabla para cambiar su clave.",
                text_color=COLOR_TEXTO_SECUNDARIO
            )

        self._cargar_usuarios()

    # ── Feedback Timers ───────────────────────────────────────────────────────

    def _mostrar_estado_crear(self, mensaje: str, es_error: bool = False):
        if self._timer_estado_crear is not None:
            self.after_cancel(self._timer_estado_crear)

        color = COLOR_PELIGRO if es_error else COLOR_EXITO
        self.lbl_estado_crear.configure(text=mensaje, text_color=color)

        if not es_error:
            self._timer_estado_crear = self.after(4000, lambda: self.lbl_estado_crear.configure(text=""))

    def _mostrar_estado_reset(self, mensaje: str, es_error: bool = False):
        if self._timer_estado_reset is not None:
            self.after_cancel(self._timer_estado_reset)

        color = COLOR_PELIGRO if es_error else COLOR_EXITO
        self.lbl_estado_reset.configure(text=mensaje, text_color=color)

        if not es_error:
            self._timer_estado_reset = self.after(4000, lambda: self.lbl_estado_reset.configure(text=""))
