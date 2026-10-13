"""
main.py — GestorEFi
Punto de entrada principal de la aplicación.
Orquesta el flujo: Inicialización DB → Login → Dashboard principal.
"""

import sys
import tkinter.messagebox as messagebox
import customtkinter

from database.connection import inicializar_base_de_datos
from gui.login_frame import LoginFrame
from gui.app import App

# ─── Configuración visual global de CustomTkinter ────────────────────────────
customtkinter.set_appearance_mode("Light")
customtkinter.set_default_color_theme("blue")

# ─── Constantes de ventana ───────────────────────────────────────────────────
TITULO_APP       = "GestorEFi — Gestión de Materiales EFi"
ANCHO_LOGIN      = 480
ALTO_LOGIN       = 620
ANCHO_APP        = 1200
ALTO_APP         = 750
MINIMO_APP       = (1000, 650)


def main():
    """
    Función principal:
    1. Inicializa la base de datos (crea tablas y semillas si es la primera vez).
    2. Crea la ventana raíz de CustomTkinter.
    3. Muestra la pantalla de login.
    4. Al autenticarse, reemplaza el login por el dashboard principal.
    """
    # ── Inicialización de la base de datos ───────────────────────────────────
    try:
        inicializar_base_de_datos()
    except RuntimeError as e:
        messagebox.showerror(
            "Error crítico",
            f"No se pudo inicializar la base de datos:\n\n{e}"
        )
        sys.exit(1)

    # ── Ventana raíz (única instancia CTk durante toda la sesión) ─────────────
    raiz = customtkinter.CTk()
    raiz.title(TITULO_APP)
    raiz.iconbitmap(default="")   # Evita errores si no hay .ico disponible

    _mostrar_login(raiz)
    raiz.mainloop()


# ─── Funciones de navegación entre pantallas ─────────────────────────────────

def _centrar_ventana(ventana: customtkinter.CTk, ancho: int, alto: int):
    """Centra la ventana en el monitor del usuario."""
    ventana.update_idletasks()
    pantalla_ancho  = ventana.winfo_screenwidth()
    pantalla_alto   = ventana.winfo_screenheight()
    x = (pantalla_ancho  // 2) - (ancho // 2)
    y = (pantalla_alto   // 2) - (alto  // 2)
    ventana.geometry(f"{ancho}x{alto}+{x}+{y}")


def _limpiar_ventana(raiz: customtkinter.CTk):
    """Destruye todos los widgets actuales de la ventana raíz."""
    for widget in raiz.winfo_children():
        widget.destroy()


def _mostrar_login(raiz: customtkinter.CTk):
    """
    Configura la ventana raíz para el modo login y carga LoginFrame.
    Se llama al iniciar la app y también al cerrar sesión desde el dashboard.
    """
    _limpiar_ventana(raiz)
    raiz.resizable(False, False)
    _centrar_ventana(raiz, ANCHO_LOGIN, ALTO_LOGIN)

    frame_login = LoginFrame(
        raiz,
        callback_exito=lambda usuario, rol: _mostrar_app(raiz, usuario, rol)
    )
    frame_login.pack(fill="both", expand=True)


def _mostrar_app(raiz: customtkinter.CTk, username: str, rol: str):
    """
    Configura la ventana raíz para el modo dashboard y carga App.
    Se llama tras un login exitoso.
    """
    _limpiar_ventana(raiz)
    raiz.resizable(True, True)
    raiz.minsize(*MINIMO_APP)
    _centrar_ventana(raiz, ANCHO_APP, ALTO_APP)

    frame_app = App(
        raiz,
        username=username,
        rol=rol,
        callback_logout=lambda: _mostrar_login(raiz)
    )
    frame_app.pack(fill="both", expand=True)


if __name__ == "__main__":
    main()
