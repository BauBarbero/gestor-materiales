"""
inventory_frame.py — GestorEFi
Frame de Inventario de Materiales (Fase 3).

Muestra una tabla scrolleable con todos los materiales del depósito.
Incluye barra de búsqueda instantánea y filtro por categoría.
Los controles de edición (Agregar / Editar) solo son visibles para rol ADMIN.
"""

import customtkinter
from tkinter import messagebox

from database.queries import (
    obtener_materiales,
    crear_material,
    actualizar_material,
    obtener_categorias,
    crear_categoria,
)
from models.material import ESTADOS_VALIDOS

# ─── Paleta de colores (coherente con app.py) ─────────────────────────────────
COLOR_PRIMARIO         = "#1e3a8a"
COLOR_HOVER_BTN        = "#1e40af"
COLOR_FONDO            = "#f8fafc"
COLOR_BLANCO           = "#ffffff"
COLOR_TEXTO_CLARO      = "#eff6ff"
COLOR_TEXTO_OSCURO     = "#1e293b"
COLOR_TEXTO_SECUNDARIO = "#64748b"
COLOR_BORDE            = "#e2e8f0"
COLOR_ENCABEZADO       = "#1e3a8a"   # Azul oscuro — cabecera de tabla
COLOR_FILA_PAR         = "#f1f5f9"   # Gris muy claro — filas pares
COLOR_FILA_IMPAR       = "#ffffff"   # Blanco — filas impares
COLOR_FILA_HOVER       = "#dbeafe"   # Azul pálido — hover
COLOR_FILA_SELECCION   = "#bfdbfe"   # Azul claro — fila seleccionada
COLOR_EXITO            = "#16a34a"   # Verde — botón Agregar
COLOR_HOVER_EXITO      = "#15803d"
COLOR_ADVERTENCIA      = "#d97706"   # Ámbar — botón Editar
COLOR_HOVER_ADV        = "#b45309"
COLOR_STOCK_BAJO       = "#fee2e2"   # Rojo pálido — stock disponible = 0
COLOR_STOCK_CRITICO    = "#fef9c3"   # Amarillo pálido — stock disponible <= 20 %

# ─── Columnas de la tabla ─────────────────────────────────────────────────────
# (encabezado, clave_dato, ancho_relativo, ancla)
_COLUMNAS: list[tuple[str, str, int, str]] = [
    ("Nombre",           "nombre",           4, "w"),
    ("Categoría",        "categoria",        2, "center"),
    ("Stock Total",      "stock_total",      1, "center"),
    ("Stock Disponible", "stock_disponible", 1, "center"),
    ("Condición",        "estado",           2, "center"),
]


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO: CREAR NUEVA CATEGORÍA
# ─────────────────────────────────────────────────────────────────────────────

class _DialogoNuevaCategoria(customtkinter.CTkToplevel):
    """
    Ventana modal para crear una nueva categoría personalizada.
    """

    def __init__(self, master, callback_guardado):
        super().__init__(master)
        self.callback_guardado = callback_guardado
        self.title("Nueva Categoría")
        self.resizable(False, False)
        self.grab_set()
        self._construir_ui()
        self._centrar_ventana()

    def _construir_ui(self):
        marco = customtkinter.CTkFrame(self, fg_color=COLOR_BLANCO, corner_radius=16)
        marco.pack(padx=24, pady=24, fill="both", expand=True)

        customtkinter.CTkLabel(
            marco, text="🏷️  Nueva Categoría",
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(pady=(20, 14), padx=28)

        customtkinter.CTkLabel(
            marco, text="Nombre de la categoría:",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        ).pack(fill="x", padx=28, pady=(0, 4))

        self.campo_nombre = customtkinter.CTkEntry(
            marco, width=280, height=42,
            placeholder_text="Ej: Atletismo, Gimnasia...",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=9
        )
        self.campo_nombre.pack(padx=28, pady=(0, 10))
        self.campo_nombre.bind("<Return>", lambda _: self._guardar())

        self.etiqueta_error = customtkinter.CTkLabel(
            marco, text="", font=customtkinter.CTkFont(size=11),
            text_color="#dc2626", height=16
        )
        self.etiqueta_error.pack()

        fila_btns = customtkinter.CTkFrame(marco, fg_color="transparent")
        fila_btns.pack(padx=28, pady=(6, 20), fill="x")

        customtkinter.CTkButton(
            fila_btns, text="Cancelar",
            font=customtkinter.CTkFont(size=12),
            fg_color="transparent", hover_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_SECUNDARIO,
            border_width=1, border_color=COLOR_BORDE,
            height=38, corner_radius=9,
            command=self.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 6))

        customtkinter.CTkButton(
            fila_btns, text="Crear Categoría",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            fg_color=COLOR_EXITO, hover_color=COLOR_HOVER_EXITO,
            text_color=COLOR_TEXTO_CLARO,
            height=38, corner_radius=9,
            command=self._guardar
        ).pack(side="left", expand=True, fill="x")

        self.campo_nombre.focus()

    def _guardar(self):
        nombre = self.campo_nombre.get().strip()
        if not nombre:
            self.etiqueta_error.configure(text="El nombre no puede estar vacío.")
            return
        try:
            crear_categoria(nombre)
        except (ValueError, RuntimeError) as e:
            self.etiqueta_error.configure(text=str(e))
            return

        if self.callback_guardado:
            self.callback_guardado(nombre)
        self.destroy()

    def _centrar_ventana(self):
        self.update_idletasks()
        ancho = self.winfo_reqwidth()
        alto  = self.winfo_reqheight()
        x = (self.winfo_screenwidth()  // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto  // 2)
        self.geometry(f"+{x}+{y}")


# ─────────────────────────────────────────────────────────────────────────────
# DIÁLOGO: AGREGAR / EDITAR MATERIAL
# ─────────────────────────────────────────────────────────────────────────────

class _DialogoMaterial(customtkinter.CTkToplevel):
    """
    Ventana modal para crear un material nuevo o editar uno existente.
    Llama a 'callback_guardado()' al cerrar con cambios guardados.
    Solo accesible para rol ADMIN.
    """

    def __init__(self, master, callback_guardado, material: dict | None = None):
        super().__init__(master)
        self.callback_guardado = callback_guardado
        self.material = material          # None → modo creación
        self._guardado = False

        # ── Configuración de ventana ──────────────────────────────────────────
        titulo = "Editar Material" if material else "Agregar Nuevo Material"
        self.title(titulo)
        self.resizable(False, False)
        self.grab_set()                   # Modal: bloquea la ventana padre

        self._construir_ui()
        self._centrar_ventana()

    def _obtener_categorias_disponibles(self) -> list[str]:
        try:
            cats = obtener_categorias()
            return cats if cats else ["General"]
        except Exception:
            return ["Pelotas", "Conos", "Indumentaria", "Colchonetas"]

    # ── Construcción de la UI ─────────────────────────────────────────────────

    def _construir_ui(self):
        marco = customtkinter.CTkFrame(self, fg_color=COLOR_BLANCO,
                                       corner_radius=16)
        marco.pack(padx=28, pady=28, fill="both", expand=True)

        # Título
        customtkinter.CTkLabel(
            marco,
            text="Editar Material" if self.material else "Nuevo Material",
            font=customtkinter.CTkFont(size=17, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(pady=(24, 20), padx=32)

        # ── Campo: Nombre ─────────────────────────────────────────────────────
        self._label(marco, "Nombre del material")
        self.campo_nombre = customtkinter.CTkEntry(
            marco, width=340, height=42,
            placeholder_text="Ej: Pelota de básquet",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=9
        )
        self.campo_nombre.pack(padx=32, pady=(0, 14))

        # ── Campo: Categoría (con botón ＋ para crear nueva) ───────────────────
        self._label(marco, "Categoría")
        fila_cat = customtkinter.CTkFrame(marco, fg_color="transparent")
        fila_cat.pack(padx=32, pady=(0, 14), fill="x")

        categorias = self._obtener_categorias_disponibles()
        self.combo_categoria = customtkinter.CTkOptionMenu(
            fila_cat, height=42,
            values=categorias,
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, button_color=COLOR_PRIMARIO,
            button_hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_OSCURO,
            dropdown_fg_color=COLOR_BLANCO,
            dropdown_text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9
        )
        self.combo_categoria.pack(side="left", expand=True, fill="x", padx=(0, 8))

        customtkinter.CTkButton(
            fila_cat, text="＋", width=42, height=42,
            font=customtkinter.CTkFont(size=16, weight="bold"),
            fg_color=COLOR_PRIMARIO, hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_CLARO, corner_radius=9,
            command=self._abrir_nueva_categoria
        ).pack(side="left")

        # ── Campo: Stock Total ────────────────────────────────────────────────
        self._label(marco, "Stock total")
        self.campo_stock = customtkinter.CTkEntry(
            marco, width=340, height=42,
            placeholder_text="Ej: 20",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=9
        )
        self.campo_stock.pack(padx=32, pady=(0, 14))

        # ── Campo: Estado / Condición ─────────────────────────────────────────
        self._label(marco, "Condición")
        self.combo_estado = customtkinter.CTkOptionMenu(
            marco, width=340, height=42,
            values=ESTADOS_VALIDOS,
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, button_color=COLOR_PRIMARIO,
            button_hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_OSCURO,
            dropdown_fg_color=COLOR_BLANCO,
            dropdown_text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9
        )
        self.combo_estado.pack(padx=32, pady=(0, 18))

        # ── Mensaje de error ──────────────────────────────────────────────────
        self.etiqueta_error = customtkinter.CTkLabel(
            marco, text="", font=customtkinter.CTkFont(size=11),
            text_color="#dc2626", height=16
        )
        self.etiqueta_error.pack()

        # ── Botones ───────────────────────────────────────────────────────────
        fila_btns = customtkinter.CTkFrame(marco, fg_color="transparent")
        fila_btns.pack(padx=32, pady=(6, 28), fill="x")

        customtkinter.CTkButton(
            fila_btns, text="Cancelar",
            font=customtkinter.CTkFont(size=13),
            fg_color="transparent", hover_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_SECUNDARIO,
            border_width=1, border_color=COLOR_BORDE,
            height=42, corner_radius=9,
            command=self.destroy
        ).pack(side="left", expand=True, fill="x", padx=(0, 8))

        customtkinter.CTkButton(
            fila_btns,
            text="Guardar Cambios" if self.material else "Agregar Material",
            font=customtkinter.CTkFont(size=13, weight="bold"),
            fg_color=COLOR_EXITO, hover_color=COLOR_HOVER_EXITO,
            text_color=COLOR_TEXTO_CLARO,
            height=42, corner_radius=9,
            command=self._guardar
        ).pack(side="left", expand=True, fill="x")

        # ── Pre-cargar datos si es edición ────────────────────────────────────
        if self.material:
            self.campo_nombre.insert(0, self.material["nombre"])
            self.combo_categoria.set(self.material["categoria"])
            self.campo_stock.insert(0, str(self.material["stock_total"]))
            self.combo_estado.set(self.material["estado"])

    def _label(self, parent, texto: str):
        customtkinter.CTkLabel(
            parent, text=texto,
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO, anchor="w"
        ).pack(fill="x", padx=32, pady=(0, 5))

    def _abrir_nueva_categoria(self):
        _DialogoNuevaCategoria(self, callback_guardado=self._on_categoria_creada)

    def _on_categoria_creada(self, nueva_cat: str = ""):
        opciones = self._obtener_categorias_disponibles()
        self.combo_categoria.configure(values=opciones)
        if nueva_cat and nueva_cat in opciones:
            self.combo_categoria.set(nueva_cat)

    # ── Lógica de guardado ────────────────────────────────────────────────────

    def _guardar(self):
        nombre = self.campo_nombre.get().strip()
        categoria = self.combo_categoria.get()
        estado = self.combo_estado.get()
        stock_str = self.campo_stock.get().strip()

        # Validaciones básicas
        if not nombre:
            self.etiqueta_error.configure(text="El nombre no puede estar vacío.")
            return
        if not stock_str.isdigit() or int(stock_str) < 0:
            self.etiqueta_error.configure(
                text="El stock debe ser un número entero ≥ 0."
            )
            return

        stock_total = int(stock_str)

        try:
            if self.material:
                # Modo edición
                actualizar_material(
                    self.material["id"], nombre, categoria, stock_total, estado
                )
            else:
                # Modo creación
                crear_material(nombre, categoria, stock_total, estado)
        except RuntimeError as e:
            self.etiqueta_error.configure(text=str(e))
            return

        self._guardado = True
        self.callback_guardado()
        self.destroy()

    def _centrar_ventana(self):
        """Centra el diálogo en la pantalla una vez que Tk haya calculado su tamaño."""
        self.update_idletasks()
        ancho  = self.winfo_reqwidth()
        alto   = self.winfo_reqheight()
        x = (self.winfo_screenwidth()  // 2) - (ancho // 2)
        y = (self.winfo_screenheight() // 2) - (alto // 2)
        self.geometry(f"+{x}+{y}")


# ─────────────────────────────────────────────────────────────────────────────
# FILA DE TABLA (widget compuesto)
# ─────────────────────────────────────────────────────────────────────────────

class _FilaTabla(customtkinter.CTkFrame):
    """
    Frame que representa una fila de la tabla de inventario.
    Colorea el fondo según el nivel de stock disponible y resalta al hacer
    hover o al ser seleccionada.
    """

    def __init__(self, master, material: dict, index: int,
                 on_click=None, col_weights: list[int] | None = None):
        # Color de fondo base según stock
        color_base = self._color_base(material, index)
        super().__init__(master, fg_color=color_base, corner_radius=0,
                         cursor="hand2")
        self.material    = material
        self.color_base  = color_base
        self.on_click    = on_click
        self._seleccionada = False

        # Configurar columnas con los pesos proporcionales de _COLUMNAS
        pesos = col_weights or [c[2] for c in _COLUMNAS]
        total = sum(pesos)
        for i, p in enumerate(pesos):
            self.columnconfigure(i, weight=p, minsize=max(60, int(600 * p / total)))

        # Crear etiquetas de celda
        self._etiquetas: list[customtkinter.CTkLabel] = []
        for col_idx, (_, clave, _, ancla) in enumerate(_COLUMNAS):
            valor = str(material.get(clave, ""))
            lbl = customtkinter.CTkLabel(
                self, text=valor,
                font=customtkinter.CTkFont(size=12),
                text_color=COLOR_TEXTO_OSCURO,
                anchor=ancla
            )
            lbl.grid(row=0, column=col_idx, sticky="ew",
                     padx=(14 if col_idx == 0 else 8, 8), pady=10)
            self._etiquetas.append(lbl)

        # Separador inferior
        sep = customtkinter.CTkFrame(self, fg_color=COLOR_BORDE,
                                     height=1, corner_radius=0)
        sep.grid(row=1, column=0, columnspan=len(_COLUMNAS), sticky="ew")

        # Eventos de ratón
        self._bind_recursivo(self)

    # ── Colores según nivel de stock ──────────────────────────────────────────

    @staticmethod
    def _color_base(material: dict, index: int) -> str:
        disponible = material.get("stock_disponible", 0)
        total      = material.get("stock_total", 1) or 1
        if disponible == 0:
            return COLOR_STOCK_BAJO
        if disponible / total <= 0.2:
            return COLOR_STOCK_CRITICO
        return COLOR_FILA_PAR if index % 2 == 0 else COLOR_FILA_IMPAR

    # ── Interacciones ─────────────────────────────────────────────────────────

    def _bind_recursivo(self, widget):
        """Aplica bindings de mouse al widget y todos sus hijos."""
        widget.bind("<Enter>",  self._on_enter)
        widget.bind("<Leave>",  self._on_leave)
        widget.bind("<Button-1>", self._on_click)
        for hijo in widget.winfo_children():
            self._bind_recursivo(hijo)

    def _on_enter(self, _event=None):
        if not self._seleccionada:
            self._aplicar_color(COLOR_FILA_HOVER)

    def _on_leave(self, _event=None):
        if not self._seleccionada:
            self._aplicar_color(self.color_base)

    def _on_click(self, _event=None):
        if self.on_click:
            self.on_click(self)

    def seleccionar(self):
        self._seleccionada = True
        self._aplicar_color(COLOR_FILA_SELECCION)

    def deseleccionar(self):
        self._seleccionada = False
        self._aplicar_color(self.color_base)

    def _aplicar_color(self, color: str):
        self.configure(fg_color=color)
        for lbl in self._etiquetas:
            lbl.configure(fg_color=color)


# ─────────────────────────────────────────────────────────────────────────────
# FRAME PRINCIPAL: INVENTARIO
# ─────────────────────────────────────────────────────────────────────────────

class InventoryFrame(customtkinter.CTkFrame):
    """
    Frame de Inventario de Materiales.

    Layout:
    ┌──────────────────────────────────────────────────────────┐
    │  Barra de título + botones ADMIN (Agregar / Editar)      │
    ├──────────────────────────────────────────────────────────┤
    │  Barra de filtros: [Buscar...] [Categoría ▾] [↺ Refrescar] │
    ├──────────────────────────────────────────────────────────┤
    │  Cabecera de tabla                                       │
    │  ─────────────────────────────────────────────────────── │
    │  Tabla scrolleable con filas de materiales               │
    └──────────────────────────────────────────────────────────┘
    """

    def __init__(self, master, username: str, rol: str, **kwargs):
        super().__init__(master, fg_color=COLOR_FONDO, corner_radius=0, **kwargs)
        self.username = username
        self.rol      = rol

        self._materiales_todos: list[dict] = []   # Cache completo de la BD
        self._materiales_vis:  list[dict] = []    # Subconjunto visible tras filtros
        self._fila_seleccionada: _FilaTabla | None = None
        self._id_seleccionado:   int | None = None
        self._after_id = None                     # ID del after() para debounce

        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)

        self._construir_barra_titulo()
        self._construir_barra_filtros()
        self._construir_tabla()
        self._cargar_datos()

    # ── Barra de título ───────────────────────────────────────────────────────

    def _construir_barra_titulo(self):
        barra = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        barra.grid(row=0, column=0, sticky="ew", padx=28, pady=(28, 10))
        barra.columnconfigure(0, weight=1)

        # Título e icono
        lado_izq = customtkinter.CTkFrame(barra, fg_color="transparent")
        lado_izq.grid(row=0, column=0, sticky="w", padx=24, pady=16)

        customtkinter.CTkLabel(
            lado_izq,
            text="📦  Inventario de Materiales",
            font=customtkinter.CTkFont(size=20, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(side="left")

        customtkinter.CTkLabel(
            lado_izq,
            text="  ·  Gestión del depósito escolar",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(side="left", pady=(3, 0))

        # Botones solo para ADMIN
        if self.rol == "ADMIN":
            lado_der = customtkinter.CTkFrame(barra, fg_color="transparent")
            lado_der.grid(row=0, column=1, sticky="e", padx=24, pady=16)

            self.btn_editar = customtkinter.CTkButton(
                lado_der,
                text="✏️  Editar Material",
                font=customtkinter.CTkFont(size=12, weight="bold"),
                fg_color=COLOR_ADVERTENCIA,
                hover_color=COLOR_HOVER_ADV,
                text_color=COLOR_TEXTO_CLARO,
                height=38, corner_radius=9,
                state="disabled",           # Se habilita solo al seleccionar una fila
                command=self._abrir_dialogo_editar
            )
            self.btn_editar.pack(side="left", padx=(0, 8))

            customtkinter.CTkButton(
                lado_der,
                text="🏷️  Nueva Categoría",
                font=customtkinter.CTkFont(size=12, weight="bold"),
                fg_color="#334155",
                hover_color="#1e293b",
                text_color=COLOR_TEXTO_CLARO,
                height=38, corner_radius=9,
                command=self._abrir_dialogo_nueva_categoria
            ).pack(side="left", padx=(0, 8))

            customtkinter.CTkButton(
                lado_der,
                text="＋  Agregar Material",
                font=customtkinter.CTkFont(size=12, weight="bold"),
                fg_color=COLOR_EXITO,
                hover_color=COLOR_HOVER_EXITO,
                text_color=COLOR_TEXTO_CLARO,
                height=38, corner_radius=9,
                command=self._abrir_dialogo_agregar
            ).pack(side="left")

    # ── Barra de filtros ──────────────────────────────────────────────────────

    def _construir_barra_filtros(self):
        barra = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        barra.grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 10))

        # Campo de búsqueda
        customtkinter.CTkLabel(
            barra, text="🔍",
            font=customtkinter.CTkFont(size=16),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(side="left", padx=(18, 6), pady=14)

        self.var_busqueda = customtkinter.StringVar()
        self.var_busqueda.trace_add("write", self._on_busqueda_cambia)

        self.campo_busqueda = customtkinter.CTkEntry(
            barra, textvariable=self.var_busqueda,
            width=260, height=38,
            placeholder_text="Buscar por nombre…",
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO, border_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_OSCURO, corner_radius=9
        )
        self.campo_busqueda.pack(side="left", pady=14)

        # Separador visual
        customtkinter.CTkFrame(
            barra, fg_color=COLOR_BORDE, width=1, height=32, corner_radius=0
        ).pack(side="left", padx=18, pady=14)

        # Filtro por categoría
        customtkinter.CTkLabel(
            barra, text="Categoría:",
            font=customtkinter.CTkFont(size=12, weight="bold"),
            text_color=COLOR_TEXTO_OSCURO
        ).pack(side="left", padx=(0, 8), pady=14)

        self._categorias_actuales = self._obtener_lista_categorias()
        self.var_categoria = customtkinter.StringVar(value="Todas")
        self.combo_categoria = customtkinter.CTkOptionMenu(
            barra,
            variable=self.var_categoria,
            values=["Todas"] + self._categorias_actuales,
            command=self._on_categoria_cambia,
            width=180, height=38,
            font=customtkinter.CTkFont(size=13),
            fg_color=COLOR_FONDO,
            button_color=COLOR_PRIMARIO,
            button_hover_color=COLOR_HOVER_BTN,
            text_color=COLOR_TEXTO_OSCURO,
            dropdown_fg_color=COLOR_BLANCO,
            dropdown_text_color=COLOR_TEXTO_OSCURO,
            corner_radius=9
        )
        self.combo_categoria.pack(side="left", pady=14)

        # Separador visual
        customtkinter.CTkFrame(
            barra, fg_color=COLOR_BORDE, width=1, height=32, corner_radius=0
        ).pack(side="left", padx=18, pady=14)

        # Botón refrescar
        customtkinter.CTkButton(
            barra, text="↺  Refrescar",
            font=customtkinter.CTkFont(size=12),
            fg_color="transparent",
            hover_color=COLOR_BORDE,
            text_color=COLOR_TEXTO_SECUNDARIO,
            border_width=1, border_color=COLOR_BORDE,
            height=38, corner_radius=9,
            command=self._cargar_datos
        ).pack(side="left", pady=14)

        # Contador de resultados (lado derecho)
        self.etiqueta_conteo = customtkinter.CTkLabel(
            barra, text="",
            font=customtkinter.CTkFont(size=11),
            text_color=COLOR_TEXTO_SECUNDARIO
        )
        self.etiqueta_conteo.pack(side="right", padx=18, pady=14)

    # ── Tabla de materiales ───────────────────────────────────────────────────

    def _construir_tabla(self):
        """Crea la cabecera fija y el área scrolleable de filas."""
        contenedor = customtkinter.CTkFrame(
            self, fg_color=COLOR_BLANCO,
            corner_radius=12, border_width=1, border_color=COLOR_BORDE
        )
        contenedor.grid(row=2, column=0, sticky="nsew", padx=28, pady=(0, 28))
        contenedor.rowconfigure(1, weight=1)
        contenedor.columnconfigure(0, weight=1)

        # ── Cabecera ──────────────────────────────────────────────────────────
        self._cabecera = customtkinter.CTkFrame(
            contenedor, fg_color=COLOR_ENCABEZADO, corner_radius=0
        )
        self._cabecera.grid(row=0, column=0, sticky="ew")

        pesos = [c[2] for c in _COLUMNAS]
        for i, p in enumerate(pesos):
            self._cabecera.columnconfigure(i, weight=p)

        for col_idx, (encabezado, _, _, ancla) in enumerate(_COLUMNAS):
            customtkinter.CTkLabel(
                self._cabecera,
                text=encabezado.upper(),
                font=customtkinter.CTkFont(size=11, weight="bold"),
                text_color=COLOR_TEXTO_CLARO,
                anchor=ancla
            ).grid(row=0, column=col_idx, sticky="ew",
                   padx=(14 if col_idx == 0 else 8, 8), pady=12)

        # ── Área scrolleable ──────────────────────────────────────────────────
        self._scroll_area = customtkinter.CTkScrollableFrame(
            contenedor, fg_color="transparent", corner_radius=0
        )
        self._scroll_area.grid(row=1, column=0, sticky="nsew")
        self._scroll_area.columnconfigure(0, weight=1)

        # Mensaje de estado cuando no hay resultados
        self._frame_vacio = customtkinter.CTkFrame(
            self._scroll_area, fg_color="transparent"
        )
        self._frame_vacio.grid(row=0, column=0, sticky="ew")

        customtkinter.CTkLabel(
            self._frame_vacio,
            text="Sin resultados",
            font=customtkinter.CTkFont(size=15, weight="bold"),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(pady=(40, 6))

        customtkinter.CTkLabel(
            self._frame_vacio,
            text="No se encontraron materiales con los filtros aplicados.",
            font=customtkinter.CTkFont(size=12),
            text_color=COLOR_TEXTO_SECUNDARIO
        ).pack(pady=(0, 40))

        self._frame_vacio.grid_remove()   # Ocultarlo hasta que sea necesario

    def _obtener_lista_categorias(self) -> list[str]:
        try:
            cats = obtener_categorias()
            return cats if cats else ["General"]
        except Exception:
            return ["Pelotas", "Conos", "Indumentaria", "Colchonetas"]

    def _abrir_dialogo_nueva_categoria(self):
        _DialogoNuevaCategoria(self, callback_guardado=lambda _: self._cargar_datos())

    # ── Carga y filtrado de datos ─────────────────────────────────────────────

    def _cargar_datos(self):
        """Recupera categorías y materiales de la BD y aplica los filtros activos."""
        try:
            self._categorias_actuales = self._obtener_lista_categorias()
            opciones_cat = ["Todas"] + self._categorias_actuales
            self.combo_categoria.configure(values=opciones_cat)
            if self.var_categoria.get() not in opciones_cat:
                self.var_categoria.set("Todas")

            rows = obtener_materiales()
            self._materiales_todos = [dict(r) for r in rows]
        except RuntimeError as e:
            messagebox.showerror("Error de base de datos", str(e), parent=self)
            self._materiales_todos = []
        finally:
            # Limpiar selección al recargar
            self._fila_seleccionada = None
            self._id_seleccionado   = None
            if self.rol == "ADMIN" and hasattr(self, "btn_editar"):
                self.btn_editar.configure(state="disabled")
            self._aplicar_filtros()

    def _on_busqueda_cambia(self, *_args):
        """Debounce de 250 ms para no filtrar en cada tecla."""
        if self._after_id is not None:
            self.after_cancel(self._after_id)
        self._after_id = self.after(250, self._aplicar_filtros)

    def _on_categoria_cambia(self, _valor: str = None):
        self._aplicar_filtros()

    def _aplicar_filtros(self):
        """Filtra _materiales_todos con búsqueda y categoría, luego re-renderiza."""
        texto     = self.var_busqueda.get().strip().lower()
        categoria = self.var_categoria.get()

        resultado = self._materiales_todos

        if texto:
            resultado = [m for m in resultado
                         if texto in m["nombre"].lower()]

        if categoria != "Todas":
            resultado = [m for m in resultado
                         if m["categoria"] == categoria]

        self._materiales_vis = resultado
        self._renderizar_filas()
        self._actualizar_conteo()

    # ── Renderizado de filas ──────────────────────────────────────────────────

    def _renderizar_filas(self):
        """Destruye y reconstruye las filas del área scrolleable."""
        # Limpiar filas anteriores
        for widget in self._scroll_area.winfo_children():
            if widget is not self._frame_vacio:
                widget.destroy()

        if not self._materiales_vis:
            self._frame_vacio.grid()
            return

        self._frame_vacio.grid_remove()

        for idx, material in enumerate(self._materiales_vis):
            fila = _FilaTabla(
                self._scroll_area,
                material=material,
                index=idx,
                on_click=self._on_fila_click
            )
            fila.grid(row=idx, column=0, sticky="ew")
            self._scroll_area.columnconfigure(0, weight=1)

    def _on_fila_click(self, fila: _FilaTabla):
        """Gestiona la selección de una fila de la tabla."""
        # Deseleccionar la fila previa
        if self._fila_seleccionada and self._fila_seleccionada.winfo_exists():
            self._fila_seleccionada.deseleccionar()

        fila.seleccionar()
        self._fila_seleccionada = fila
        self._id_seleccionado   = fila.material.get("id")

        # Habilitar el botón Editar (solo ADMIN)
        if self.rol == "ADMIN" and hasattr(self, "btn_editar"):
            self.btn_editar.configure(state="normal")

    # ── Diálogos ADMIN ────────────────────────────────────────────────────────

    def _abrir_dialogo_agregar(self):
        _DialogoMaterial(self, callback_guardado=self._cargar_datos)

    def _abrir_dialogo_editar(self):
        if not self._id_seleccionado:
            messagebox.showwarning(
                "Sin selección",
                "Seleccioná un material de la tabla antes de editar.",
                parent=self
            )
            return

        # Buscar el material seleccionado en la vista actual
        material = next(
            (m for m in self._materiales_vis
             if m.get("id") == self._id_seleccionado),
            None
        )
        if material is None:
            messagebox.showwarning(
                "Material no encontrado",
                "No se pudo encontrar el material seleccionado.",
                parent=self
            )
            return

        _DialogoMaterial(self, callback_guardado=self._cargar_datos, material=material)

    # ── Utilidades ────────────────────────────────────────────────────────────

    def _actualizar_conteo(self):
        total_bd = len(self._materiales_todos)
        visible  = len(self._materiales_vis)
        if visible == total_bd:
            texto = f"{total_bd} material{'es' if total_bd != 1 else ''} en total"
        else:
            texto = f"{visible} de {total_bd} materiales"
        self.etiqueta_conteo.configure(text=texto)
