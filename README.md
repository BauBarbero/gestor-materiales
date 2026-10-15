# GestorEFi - Sistema de Control e Inventario de Materiales de Educación Física

## Descripción

### Problema a Resolver
En el depósito de educación física de la institución no existe conectividad a Internet estable ni cableado de red Ethernet. Actualmente, el control de stock de pelotas, redes, conos y colchonetas se lleva de forma manual, lo que provoca imprecisiones, extravío de insumos y falta de trazabilidad cuando los alumnos retiran materiales para jugar durante los recreos.

### Solución Propuesta
**GestorEFi** es una aplicación de escritorio local desarrollada en Python con almacenamiento persistente en SQLite. Permite llevar un inventario categorizado, registrar préstamos temporales a estudiantes en los recreos y mantener un historial auditivo de bajas por rotura o pérdida, todo funcionando 100% offline.

### Rol del Agente de IA (Google AntiGravity)
El desarrollo del proyecto se realiza bajo la metodología de *Vibecoding*. El agente de IA en la IDE AntiGravity actúa como **Arquitecto y Desarrollador de Software Automatizado**, asumiendo las siguientes responsabilidades:
* Generación de la arquitectura base del proyecto y esquemas de base de datos SQL.
* Maquetado y programación de interfaces gráficas (UI) con CustomTkinter.
* Implementación de la lógica de autenticación (roles Administrador / Consulta).
* Refactorización, detección y solución automática de errores (*debugging*).

El estudiante cumple el rol de **Líder de Proyecto y Revisor de Código**, definiendo los requerimientos, guiando al agente mediante prompts estructurados y validando cada entrega funcional.

### Valor Agregado de la IA
La integración de AntiGravity permite acelerar drásticamente el flujo de desarrollo de software, permitiendo a un único estudiante construir una aplicación de escritorio robusta, modular y completamente funcional en tiempos acotados, aplicando buenas prácticas de diseño de software.

---

## Integrantes
* **Nombre y Apellido:** [Tu Nombre y Apellido]
* **Modalidad:** Individual

---

## Entorno y Requisitos

### Requisitos del Sistema
* **Sistema Operativo:** Windows 10/11, macOS o Linux.
* **Lenguaje de Programación:** Python 3.10 o superior.
* **Base de Datos:** SQLite3 (incluido en la biblioteca estándar de Python).

### Dependencias Principales
* `customtkinter`: Biblioteca para la interfaz gráfica moderna.
* `sqlite3`: Motor de base de datos local embebido.

### Pasos para Configurar y Ejecutar en Google AntiGravity IDE

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/BauBarbero/gestor-materiales.git
   cd gestor-materiales

1. **Instalar dependencias:**
   ```bash
   pip install -r gestionefi/requirements.txt
