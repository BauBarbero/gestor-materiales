"""
login_frame.py — GestorEFi
Pantalla de inicio de sesión.
Construida con CustomTkinter usando la paleta institucional Dark Blue / Light Gray.
Llama a 'callback_exito(username, rol)' al autenticarse correctamente.
"""

import customtkinter
from database.queries import verificar_credenciales

# ─── Paleta de colores ────────────────────────────────────────────────────────
COLOR_PRIMARIO        = "#1e3a8a"   # Dark Blue — encabezado y botón principal
COLOR_HOVER_BTN       = "#1e40af"   # Blue ligeramente más claro para hover
COLOR_FONDO           = "#f8fafc"   # Light Gray — fondo del formulario
COLOR_BLANCO          = "#ffffff"   # Tarjeta del formulario
COLOR_TEXTO_CLARO     = "#eff6ff"   # Off-white para texto sobre fondo azul
COLOR_SUBTITULO       = "#93c5fd"   # Azul claro para subtítulo
COLOR_TEXTO_OSCURO    = "#1e293b"   # Dark slate para texto sobre fondo claro
COLOR_ERROR           = "#dc2626"   # Rojo para mensajes de error
COLOR_BORDE           = "#cbd5e1"   # Gris suave para bordes de entrada


class LoginFrame(customtkinter.CTkFrame):
    """
    Frame de inicio de sesión.
    Se empaqueta directamente en la ventana raíz (CTk) y ocupa toda la pantalla.
    """

    def __init__(self, master, callback_exito, **kwargs):
        super().__init__(master, fg_color=COLOR_PRIMARIO, corner_radius=0, **kwargs)
        self.callback_exito = callback_exito
        self._construir_ui()

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _construir_ui(self):
        """Construye el layout completo de la pantalla de login."""
        # Centrar el contenido dentro del frame
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        marco_central = customtkinter.CTkFrame(
            self, fg_color="transparent", corner_radius=0
        )
        marco_central.grid(row=0, column=0)

        self._construir_encabezado(marco_central)
        self._construir_tarjeta(marco_central)

    def _construir_encabezado(self, parent):
        """Ícono, título y subtítulo de la aplicación."""
        customtkinter.CTkLabel(
            parent,
            text="🏫",
            font=customtkinter.CTkFont(size=56),
            text_color=COLOR_TEXTO_CLARO
        ).pack(pady=(50, 6))

        customtkinter.CTkLabel(
            parent,
            text="GestorEFi",
            font=customtkinter.CTkFont(family="Helvetica", size=36, weight="bold"),
            text_color=COLOR_TEXTO_CLARO
        ).pack()

        customtkinter.CTkLabel(
            parent,
            text="Sistema de Gestión de Materiales  ·  Educación Física",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_SUBTITULO
        ).pack(pady=(5, 36))

    def _construir_tarjeta(self, parent):
        """Tarjeta blanca con el formulario de autenticación."""
        tarjeta = customtkinter.CTkFrame(
            parent,
            fg_color=COLOR_BLANCO,
            corner_radius=16,
            border_width=1,
            border_color=COLOR_BORDE
        )
        tarjeta.pack(padx=48, pady=(0, 50), ipadx=6, ipady=6)

        # ── Título de la tarjeta ─────────────────────────────────────────────
        customtkinter.CTkLabel(
            tarjeta,
            text="Iniciar Sesión",
            font=customtkinter.CTkFont(size=19, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(pady=(28, 22), padx=38)

        # ── Campo: Usuario ───────────────────────────────────────────────────
        customtkinter.CTkLabel(
            tarjeta,
            text="Usuario",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        ).pack(fill="x", padx=38, pady=(0, 5))

        self.campo_usuario = customtkinter.CTkEntry(
            tarjeta,
            width=320,
            height=44,
            placeholder_text="Ingresá tu usuario",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            border_width=2,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9
        )
        self.campo_usuario.pack(padx=38, pady=(0, 16))

        # ── Campo: Contraseña ────────────────────────────────────────────────
        customtkinter.CTkLabel(
            tarjeta,
            text="Contraseña",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO,
            anchor="w"
        ).pack(fill="x", padx=38, pady=(0, 5))

        self.campo_password = customtkinter.CTkEntry(
            tarjeta,
            width=320,
            height=44,
            placeholder_text="Ingresá tu contraseña",
            show="●",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            border_color=COLOR_BORDE,
            border_width=2,
            text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9
        )
        self.campo_password.pack(padx=38, pady=(0, 6))

        # ── Mensaje de error ─────────────────────────────────────────────────
        self.etiqueta_error = customtkinter.CTkLabel(
            tarjeta,
            text="",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_ERROR,
            height=18
        )
        self.etiqueta_error.pack(pady=(2, 6))

        # ── Botón principal ──────────────────────────────────────────────────
        self.boton_ingresar = customtkinter.CTkButton(
            tarjeta,
            text="Ingresar al Sistema",
            font=customtkinter.CTkFont(size=14, weight="bold"),
            width=320,
            height=48,
            fg_color=COLOR_PRIMARIO,
            hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_BLANCO,
            corner_radius=9,
            command=self._intentar_login
        )
        self.boton_ingresar.pack(padx=38, pady=(4, 30))

        # ── Atajos de teclado ────────────────────────────────────────────────
        # Enter en usuario → mueve foco a contraseña
        self.campo_usuario.bind("<Return>", lambda _: self.campo_password.focus())
        # Enter en contraseña → intenta login
        self.campo_password.bind("<Return>", lambda _: self._intentar_login())

        # Foco inicial
        self.campo_usuario.focus()

    # ── Lógica de autenticación ───────────────────────────────────────────────

    def _intentar_login(self):
        """
        Lee los campos, valida que no estén vacíos, consulta la base de datos
        usando verificar_credenciales() y llama al callback si el login es exitoso.
        """
        username = self.campo_usuario.get().strip()
        password = self.campo_password.get()

        # Validación de campos vacíos
        if not username or not password:
            self._mostrar_error("Completá el usuario y la contraseña para continuar.")
            return

        # Bloquear el botón mientras se procesa
        self.boton_ingresar.configure(state="disabled", text="Verificando...")

        try:
            usuario = verificar_credenciales(username, password)
        except RuntimeError as e:
            self._mostrar_error(f"Error de base de datos: {e}")
            self.boton_ingresar.configure(state="normal", text="Ingresar al Sistema")
            return
        finally:
            # Restaurar botón si hubo error (en caso de éxito el frame se destruye)
            self.after(200, lambda: self.boton_ingresar.configure(
                state="normal", text="Ingresar al Sistema"
            ) if self.winfo_exists() else None)

        if usuario is None:
            self._mostrar_error("Usuario o contraseña incorrectos.")
            self.campo_password.delete(0, "end")
            self.campo_password.focus()
            return

        # ── Login exitoso → notificar a main.py ─────────────────────────────
        self._mostrar_error("")
        self.callback_exito(usuario["username"], usuario["rol"])

    def _mostrar_error(self, mensaje: str):
        """Actualiza el texto de la etiqueta de error."""
        self.etiqueta_error.configure(text=mensaje)
