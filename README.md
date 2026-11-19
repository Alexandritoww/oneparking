# 🚗 OneParking - Sistema de Gestión de Parqueadero

Aplicación de escritorio desarrollada en **Python** con interfaz gráfica en **Tkinter** y persistencia de datos en **MySQL**, diseñada para administrar el flujo vehicular, la disponibilidad de cupos y el control financiero diario de un parqueadero.

---

## ✨ Funcionalidades Principales

* **Control de Acceso por Roles:** Inicio de sesión diferenciado para administradores (`admin`) y cajeros (`caja`).
* **Gestión de Entradas y Salidas:** Registro de vehículos (`carro`, `moto`, `cicla`), asignación automática o manual de espacios, cálculo automático de cobro por fracción/hora y temporizador de 3 minutos tras el pago para liberar el cupo.
* **Mapa de Espacios en Tiempo Real:** Visualización gráfica de 30 cupos (`A01–A10` premium, `B01–B10` y `C01–C10` regulares) con indicadores de estado (`LIBRE`, `OCUPADO`, `SALIENDO`) y vista emergente de placa y tiempo de estadía.
* **Generación de Tickets:** Emisión de comprobantes de entrada con código único, tarifa aplicable y hora de ingreso.
* **Control Financiero y Cierre de Caja:** Registro de gastos operativos, historial diario, modalidad de tarifa plena por día (`carro` y `moto`), cierre de caja con cálculo de ganancia neta y reinicio automático de contadores diarios.
* **Estadísticas Gráficas:** Gráficos de barras integrados con **Matplotlib** para analizar ingresos diarios (últimos 7 días), semanales (últimas 4 semanas) y mensuales (últimos 6 meses).
* **Panel de Administración:** Gestión de usuarios, actualización de tarifas por tipo de vehículo, reporte general de movimientos, reinicio de base de datos y generador de datos de prueba.

---

## 🛠️ Requisitos Previos

* **Python 3.8** o superior.
* **Servidor MySQL / MariaDB** (por ejemplo, **XAMPP**).
* Librerías de Python incluidas en `requirements.txt`:
  * `mysql-connector-python`
  * `matplotlib`

---

## ⚙️ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone [https://github.com/Alexandritoww/oneparking.git](https://github.com/Alexandritoww/oneparking.git)
cd oneparking
