import tkinter as tk
from tkinter import messagebox, ttk, Frame, Toplevel
from datetime import datetime, timedelta
import math
import mysql.connector
import random
import threading
import time
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class Database:
    def __init__(self):
        try:
            self.connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="oneparking_db"
            )
            self.cursor = self.connection.cursor(buffered=True)
            self.create_parking_spaces_table()
        except mysql.connector.Error as err:
            messagebox.showerror("Error de Conexión", f"No se pudo conectar a la base de datos: {err}")
            raise

    def create_parking_spaces_table(self):
        try:
            self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS parking_spaces (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    space_number VARCHAR(10) UNIQUE NOT NULL,
                    space_type VARCHAR(20) DEFAULT 'regular',
                    status VARCHAR(20) DEFAULT 'available',
                    vehicle_plate VARCHAR(10),
                    occupied_since DATETIME
                )
            """)
            self.connection.commit()
        except mysql.connector.Error as err:
            print(f"Error creando tabla de espacios: {err}")

    def close(self):
        self.cursor.close()
        self.connection.close()

    def commit(self):
        self.connection.commit()


class ParkingApp:
    # ============ COLORES PROFESIONALES ============
    BG_COLOR = "#F5F5F5"
    PRIMARY_COLOR = "#1976D2"
    SECONDARY_COLOR = "#424242"
    ACCENT_COLOR = "#FF5722"
    SUCCESS_COLOR = "#4CAF50"
    WARNING_COLOR = "#FF9800"
    ERROR_COLOR = "#F44336"
    CARD_COLOR = "#FFFFFF"
    BORDER_COLOR = "#BDBDBD"

    # ============ FUENTES GRANDES ============
    FONT_TITLE = ("Helvetica", 36, "bold")
    FONT_SUBTITLE = ("Helvetica", 24, "bold")
    FONT_HEADING = ("Helvetica", 20, "bold")
    FONT_BODY = ("Arial", 16)
    FONT_BUTTON = ("Arial", 14, "bold")
    FONT_SMALL = ("Arial", 14)

    def __init__(self, root):
        self.root = root
        self.root.title("OneParking - Sistema de Parqueadero")
        self.root.geometry("900x700")
        self.root.configure(bg=self.BG_COLOR)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.db = Database()
        self.current_user = None
        self.last_reset_date = None
        self.vehicle_update_id = None
        self.rates = {}
        self.exit_timers = {}
        
        self.load_session()
        self.check_daily_reset()
        self.update_clock()
        
        if not self.current_user:
            self.create_login_screen()
        else:
            self.create_main_screen()

    def on_closing(self):
        try:
            for plate, timer_info in self.exit_timers.items():
                timer = timer_info.get('timer')
                if timer and timer.is_alive():
                    timer.cancel()
            
            if hasattr(self, 'db'):
                self.db.close()
        except Exception as e:
            print(f"Error al cerrar la conexión a la base de datos: {e}")
        finally:
            self.root.destroy()

    def format_currency(self, amount):
        amount = int(amount)
        amount_str = str(amount)
        length = len(amount_str)
        result = ""
        for i in range(length):
            if i > 0 and (length - i) % 3 == 0:
                result += "."
            result += amount_str[i]
        return f"${result}"

    def format_time_difference(self, seconds):
        days = int(seconds // (24 * 3600))
        seconds %= (24 * 3600)
        hours = int(seconds // 3600)
        seconds %= 3600
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        
        time_parts = []
        if days > 0:
            time_parts.append(f"{days} día{'s' if days != 1 else ''}")
        if hours > 0:
            time_parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
        if minutes > 0:
            time_parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
        if seconds > 0 or not time_parts:
            time_parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")
        
        return ", ".join(time_parts)

    def update_clock(self):
        current_time = datetime.now().strftime("%H:%M:%S")
        if not hasattr(self, 'clock_label') or not self.clock_label.winfo_exists():
            self.clock_label = tk.Label(
                self.root, 
                text=f"Hora: {current_time}", 
                fg=self.SECONDARY_COLOR, 
                bg=self.BG_COLOR, 
                font=self.FONT_SMALL
            )
            self.clock_label.pack(anchor="ne", padx=20, pady=5)
        else:
            self.clock_label.config(text=f"Hora: {current_time}")
        self.root.after(1000, self.update_clock)

    def load_session(self):
        self.current_user = None
        self.load_rates()
        self.load_last_reset_date()

    def load_rates(self):
        try:
            self.db.cursor.execute("SELECT vehicle_type, rate FROM rates")
            results = self.db.cursor.fetchall()
            for vehicle_type, rate in results:
                self.rates[vehicle_type] = rate
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE rates (
                        vehicle_type VARCHAR(10) PRIMARY KEY,
                        rate INT NOT NULL
                    )
                """)
                self.db.cursor.execute("INSERT INTO rates (vehicle_type, rate) VALUES ('carro', 3000)")
                self.db.cursor.execute("INSERT INTO rates (vehicle_type, rate) VALUES ('moto', 1500)")
                self.db.cursor.execute("INSERT INTO rates (vehicle_type, rate) VALUES ('cicla', 500)")
                self.db.commit()
                self.db.cursor.execute("SELECT vehicle_type, rate FROM rates")
                results = self.db.cursor.fetchall()
                for vehicle_type, rate in results:
                    self.rates[vehicle_type] = rate
            else:
                raise err

    def load_last_reset_date(self):
        try:
            self.db.cursor.execute("SELECT last_reset_date FROM reset_dates ORDER BY last_reset_date DESC LIMIT 1")
            result = self.db.cursor.fetchone()
            self.last_reset_date = result[0] if result and result[0] else datetime.now().date()
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE reset_dates (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        last_reset_date DATE NOT NULL
                    )
                """)
                self.db.commit()
                self.last_reset_date = datetime.now().date()
            else:
                raise err

    def check_daily_reset(self):
        current_date = datetime.now().date()
        if self.last_reset_date is None or current_date > self.last_reset_date:
            current_date_str = current_date.strftime("%Y-%m-%d")
            self.db.cursor.execute("INSERT INTO daily_income (date, total_income) VALUES (%s, 0) ON DUPLICATE KEY UPDATE total_income=0", (current_date_str,))
            self.db.cursor.execute("INSERT INTO daily_expenses (date, total_expenses) VALUES (%s, 0) ON DUPLICATE KEY UPDATE total_expenses=0", (current_date_str,))
            self.db.cursor.execute("INSERT INTO daily_net_totals (date, net_total) VALUES (%s, 0) ON DUPLICATE KEY UPDATE net_total=0", (current_date_str,))
            self.db.cursor.execute("INSERT INTO reset_dates (last_reset_date) VALUES (%s)", (current_date,))
            self.db.commit()
            self.last_reset_date = current_date

    def logout(self):
        self.current_user = None
        self.create_login_screen()

    def create_login_screen(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=40, pady=40)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=30)
        tk.Label(
            title_frame, 
            text="🚗 ONEPARKING", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()
        tk.Label(
            title_frame, 
            text="Inicio de Sesión", 
            font=self.FONT_SUBTITLE, 
            fg=self.SECONDARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=10)

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="Usuario:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        self.username = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        self.username.pack(pady=8, ipady=3)
        
        tk.Label(
            entry_frame, 
            text="Contraseña:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        self.password = tk.Entry(
            entry_frame, 
            show="*", 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        self.password.pack(pady=8, ipady=3)

        # Botones de login
        btn_frame = Frame(main_frame, bg=self.BG_COLOR)
        btn_frame.pack(pady=15)
        ttk.Button(
            btn_frame, 
            text="🔑 INICIAR SESIÓN", 
            command=self.login
        ).pack(side="left", padx=10, ipady=5, ipadx=15)
        
        ttk.Button(
            btn_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=10, ipady=5, ipadx=15)

    def login(self):
        username = self.username.get()
        password = self.password.get()
        try:
            self.db.cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
            result = self.db.cursor.fetchone()
            if result and result[0] == password:
                self.current_user = username
                self.create_main_screen()
            else:
                messagebox.showerror("Error", "Usuario o contraseña incorrectos", parent=self.root)
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE users (
                        username VARCHAR(50) PRIMARY KEY,
                        password VARCHAR(50) NOT NULL
                    )
                """)
                self.db.cursor.execute("INSERT INTO users (username, password) VALUES ('admin', '1234')")
                self.db.cursor.execute("INSERT INTO users (username, password) VALUES ('caja', 'caja123')")
                self.db.commit()
                self.db.cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
                result = self.db.cursor.fetchone()
                if result and result[0] == password:
                    self.current_user = username
                    self.create_main_screen()
                else:
                    messagebox.showerror("Error", "Usuario o contraseña incorrectos", parent=self.root)
            else:
                messagebox.showerror("Error", f"Error al intentar iniciar sesión: {err}", parent=self.root)

    def clear_screen(self):
        if self.vehicle_update_id:
            self.root.after_cancel(self.vehicle_update_id)
            self.vehicle_update_id = None
        
        for widget in self.root.winfo_children():
            if widget != self.clock_label:
                widget.destroy()

    def create_main_screen(self):
        self.clear_screen()
        
        # Frame principal con scroll si es necesario
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        # ============ TÍTULO ============
        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=15)
        tk.Label(
            title_frame, 
            text="🅿️ ONEPARKING - MENÚ PRINCIPAL", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()
        tk.Label(
            title_frame, 
            text=f"Usuario: {self.current_user}", 
            font=self.FONT_SMALL, 
            fg=self.SECONDARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=5)

        # ============ BOTONES DEL MENÚ (más pequeños para que quepan todos) ============
        button_container = Frame(main_frame, bg=self.BG_COLOR)
        button_container.pack(pady=10, fill="both", expand=True)

        # Columna izquierda
        left_frame = Frame(button_container, bg=self.BG_COLOR)
        left_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(
            left_frame, 
            text="📋 OPERACIONES", 
            font=self.FONT_HEADING, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=5)
        
        operations = [
            ("🚗 Entrada", self.register_entry),
            ("🚙 Salida", self.register_exit),
            ("📍 Espacios", self.view_parking_spaces),
            ("🎫 Ticket", self.generate_ticket_view),
        ]
        
        for text, command in operations:
            ttk.Button(
                left_frame, 
                text=text, 
                command=command
            ).pack(pady=3, fill="x", ipady=4)

        # Columna centro
        center_frame = Frame(button_container, bg=self.BG_COLOR)
        center_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(
            center_frame, 
            text="💰 FINANZAS", 
            font=self.FONT_HEADING, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=5)
        
        finances = [
            ("💵 Gasto", self.register_expense),
            ("📊 Estadísticas", self.show_statistics),
            ("📅 Historial", self.show_daily_history),
            ("🏦 Cierre Caja", self.show_cash_closure_prompt),
        ]
        
        for text, command in finances:
            ttk.Button(
                center_frame, 
                text=text, 
                command=command
            ).pack(pady=3, fill="x", ipady=4)

        # Columna derecha
        right_frame = Frame(button_container, bg=self.BG_COLOR)
        right_frame.pack(side="left", padx=10, fill="both", expand=True)
        
        tk.Label(
            right_frame, 
            text="📊 INFO", 
            font=self.FONT_HEADING, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=5)
        
        info = [
            ("🏍️ Día Moto/Carro", self.register_day_rate),
            ("🚗 Vehículos", self.show_current_vehicles),
        ]
        
        for text, command in info:
            ttk.Button(
                right_frame, 
                text=text, 
                command=command
            ).pack(pady=3, fill="x", ipady=4)

        # Botones de administrador
        if self.current_user == "admin":
            admin_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
            admin_frame.pack(pady=10, fill="x", padx=30)
            
            tk.Label(
                admin_frame, 
                text="🔒 ADMINISTRACIÓN", 
                font=self.FONT_HEADING, 
                fg=self.ACCENT_COLOR, 
                bg=self.CARD_COLOR
            ).pack(pady=8)
            
            admin_inner = Frame(admin_frame, bg=self.CARD_COLOR)
            admin_inner.pack(pady=5)
            
            admin_ops = [
                ("👥 Usuarios", self.manage_users),
                ("💸 Tarifas", self.modify_rates),
                ("📄 Reporte", self.view_full_report),
                ("🔄 Reiniciar", self.show_reset_system),
                ("🧪 Datos Prueba", self.generate_test_data),
            ]
            
            for text, command in admin_ops:
                ttk.Button(
                    admin_inner, 
                    text=text, 
                    command=command
                ).pack(side="left", padx=5, ipady=3, ipadx=8)

        # ============ BOTONES INFERIORES (VOLVER ATRÁS y SALIR) ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=20)

        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.logout,
            style="Warning.TButton"
        ).pack(side="left", padx=15, ipady=8, ipadx=20)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR DEL SISTEMA", 
            command=self.root.quit,
            style="Danger.TButton"
        ).pack(side="left", padx=15, ipady=8, ipadx=20)

    # ============ VISTA DE ESPACIOS ============
    def view_parking_spaces(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=15)
        tk.Label(
            title_frame, 
            text="📍 VISTA DE ESPACIOS", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        occupancy_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        occupancy_frame.pack(pady=15, fill="x", padx=30, ipady=10)
        
        self.db.cursor.execute("SELECT COUNT(*) FROM parking_spaces")
        total = self.db.cursor.fetchone()[0]
        self.db.cursor.execute("SELECT COUNT(*) FROM parking_spaces WHERE status = 'occupied'")
        occupied = self.db.cursor.fetchone()[0]
        self.db.cursor.execute("SELECT COUNT(*) FROM parking_spaces WHERE status = 'exiting'")
        exiting = self.db.cursor.fetchone()[0]
        percentage = ((occupied + exiting) / total * 100) if total > 0 else 0
        
        tk.Label(
            occupancy_frame, 
            text=f"📊 OCUPACIÓN: {occupied+exiting}/{total} ({percentage:.1f}%)",
            font=("Arial", 20, "bold"),
            fg=self.PRIMARY_COLOR,
            bg=self.CARD_COLOR
        ).pack(pady=10)

        legend_frame = Frame(main_frame, bg=self.BG_COLOR)
        legend_frame.pack(pady=10)
        
        tk.Label(
            legend_frame, 
            text="🟢 LIBRE", 
            fg=self.SUCCESS_COLOR, 
            bg=self.BG_COLOR, 
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=20)
        tk.Label(
            legend_frame, 
            text="🔴 OCUPADO", 
            fg=self.ERROR_COLOR, 
            bg=self.BG_COLOR, 
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=20)
        tk.Label(
            legend_frame, 
            text="🟠 SALIENDO", 
            fg=self.WARNING_COLOR, 
            bg=self.BG_COLOR, 
            font=("Arial", 14, "bold")
        ).pack(side="left", padx=20)

        spaces_frame = Frame(main_frame, bg=self.BG_COLOR)
        spaces_frame.pack(pady=15, fill="both", expand=True)
        
        self.db.cursor.execute("""
            SELECT space_number, status, space_type, vehicle_plate, occupied_since 
            FROM parking_spaces 
            ORDER BY space_number
        """)
        spaces = self.db.cursor.fetchall()
        
        row = 0
        col = 0
        
        for space_number, status, space_type, plate, occupied_since in spaces:
            if status == 'occupied':
                bg_color = self.ERROR_COLOR
                fg_color = "white"
                text = f"{space_number}\n{plate or 'OCUPADO'}"
            elif status == 'exiting':
                bg_color = self.WARNING_COLOR
                fg_color = "black"
                text = f"{space_number}\nSALIENDO..."
            else:
                bg_color = self.SUCCESS_COLOR
                fg_color = "white"
                text = f"{space_number}\nLIBRE"
            
            space_btn = tk.Button(
                spaces_frame,
                text=text,
                bg=bg_color,
                fg=fg_color,
                font=("Arial", 12, "bold"),
                width=10,
                height=3,
                relief="raised",
                bd=2
            )
            space_btn.grid(row=row, column=col, padx=5, pady=5)
            
            if plate and occupied_since:
                time_diff = (datetime.now() - occupied_since).total_seconds()
                time_str = self.format_time_difference(time_diff)
                space_btn.bind("<Enter>", lambda e, sn=space_number, pl=plate, tm=time_str: 
                    self.show_tooltip(e, f"Espacio: {sn}\nPlaca: {pl}\nTiempo: {tm}"))
            
            col += 1
            if col >= 6:
                col = 0
                row += 1

        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def show_tooltip(self, event, text):
        tooltip = Toplevel(self.root)
        tooltip.wm_overrideredirect(True)
        tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
        label = tk.Label(
            tooltip, 
            text=text, 
            bg="yellow", 
            fg="black", 
            font=("Arial", 12), 
            relief="solid", 
            bd=1, 
            padx=8, 
            pady=3
        )
        label.pack()
        self.root.after(2000, tooltip.destroy)

    def generate_ticket_view(self):
        ticket_window = Toplevel(self.root)
        ticket_window.title("🎫 Generar Ticket")
        ticket_window.geometry("600x550")
        ticket_window.configure(bg=self.BG_COLOR)
        
        tk.Label(
            ticket_window, 
            text="🎫 GENERAR TICKET", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack(pady=15)
        
        form_frame = Frame(ticket_window, bg=self.CARD_COLOR, bd=2, relief="solid")
        form_frame.pack(pady=15, padx=30, fill="x", ipady=15)
        
        tk.Label(
            form_frame, 
            text="PLACA:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        plate_entry = tk.Entry(
            form_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        plate_entry.pack(pady=8, ipady=3)
        
        tk.Label(
            form_frame, 
            text="TIPO DE VEHÍCULO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        vehicle_type = ttk.Combobox(
            form_frame, 
            values=["carro", "moto", "cicla"], 
            font=("Arial", 16)
        )
        vehicle_type.set("carro")
        vehicle_type.pack(pady=8, ipady=3)
        
        tk.Label(
            form_frame, 
            text="ESPACIO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        
        self.db.cursor.execute("SELECT space_number FROM parking_spaces WHERE status = 'available' ORDER BY space_number LIMIT 10")
        available_spaces = [row[0] for row in self.db.cursor.fetchall()]
        
        space_var = tk.StringVar(value=available_spaces[0] if available_spaces else "")
        space_menu = ttk.Combobox(
            form_frame, 
            textvariable=space_var, 
            values=available_spaces, 
            font=("Arial", 16)
        )
        space_menu.pack(pady=8, ipady=3)
        
        if not available_spaces:
            tk.Label(
                form_frame, 
                text="⚠️ NO HAY ESPACIOS", 
                fg=self.ERROR_COLOR, 
                bg=self.CARD_COLOR, 
                font=("Arial", 14, "bold")
            ).pack(pady=8)
        
        def generate():
            plate = plate_entry.get().strip().upper()
            vtype = vehicle_type.get()
            space = space_var.get()
             
            if not plate or len(plate) < 3:
                messagebox.showerror("Error", "Ingrese una placa válida", parent=ticket_window)
                return
            
            if not space:
                messagebox.showerror("Error", "Seleccione un espacio", parent=ticket_window)
                return
            
            self.db.cursor.execute("SELECT id FROM vehicles WHERE plate = %s AND exit_time IS NULL", (plate,))
            if self.db.cursor.fetchone():
                messagebox.showerror("Error", f"El vehículo {plate} ya está en el parqueadero", parent=ticket_window)
                return
            
            entry_time = datetime.now()
            
            self.db.cursor.execute("""
                UPDATE parking_spaces 
                SET status = 'occupied', vehicle_plate = %s, occupied_since = %s 
                WHERE space_number = %s
            """, (plate, entry_time, space))
            
            self.db.cursor.execute("SELECT id FROM parking_spaces WHERE space_number = %s", (space,))
            space_id = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute(
                "INSERT INTO vehicles (plate, vehicle_type, entry_time, space_id) VALUES (%s, %s, %s, %s)",
                (plate, vtype, entry_time, space_id)
            )
            vehicle_id = self.db.cursor.lastrowid
            
            self.db.commit()
            
            self.show_generated_ticket(ticket_window, vehicle_id, plate, space, entry_time, vtype)
        
        ttk.Button(
            form_frame, 
            text="✅ GENERAR", 
            command=generate
        ).pack(pady=15, ipady=5, ipadx=20)
        ttk.Button(
            form_frame, 
            text="❌ CANCELAR", 
            command=ticket_window.destroy
        ).pack(pady=5, ipady=5, ipadx=20)

    def show_generated_ticket(self, parent_window, vehicle_id, plate, space, entry_time, vehicle_type):
        ticket_window = Toplevel(parent_window)
        ticket_window.title("🎫 Ticket Generado")
        ticket_window.geometry("450x550")
        ticket_window.configure(bg="white")
        
        ticket_frame = Frame(ticket_window, bg="white", bd=3, relief="solid")
        ticket_frame.pack(padx=25, pady=25, fill="both", expand=True)
        
        tk.Label(
            ticket_frame, 
            text="╔══════════════════════════════╗", 
            font=("Courier", 12), 
            bg="white", 
            fg="black"
        ).pack()
        tk.Label(
            ticket_frame, 
            text="║  🅿️ ONEPARKING 🅿️  ║", 
            font=("Courier", 16, "bold"), 
            bg="white", 
            fg=self.PRIMARY_COLOR
        ).pack()
        tk.Label(
            ticket_frame, 
            text="║  TICKET DE ENTRADA  ║", 
            font=("Courier", 14, "bold"), 
            bg="white", 
            fg=self.SUCCESS_COLOR
        ).pack()
        tk.Label(
            ticket_frame, 
            text="╚══════════════════════════════╝", 
            font=("Courier", 12), 
            bg="white", 
            fg="black"
        ).pack()
        
        content = f"""
TICKET: TKT{vehicle_id:06d}

🚗 PLACA: {plate}
📍 ESPACIO: {space}
🚙 TIPO: {vehicle_type}

📅 FECHA: {entry_time.strftime('%Y-%m-%d')}
⏰ HORA: {entry_time.strftime('%H:%M:%S')}

💰 TARIFA: ${self.rates.get(vehicle_type, 0):,}/hora

⚠️ TIEMPO LÍMITE DESPUÉS DEL PAGO: 3 MIN

¡GRACIAS!
        """
        
        tk.Label(
            ticket_frame, 
            text=content, 
            font=("Courier", 11), 
            bg="white", 
            fg="black", 
            justify="left"
        ).pack(pady=12)
        
        tk.Label(
            ticket_frame, 
            text="═══════════════════════════════", 
            font=("Courier", 12), 
            bg="white", 
            fg="black"
        ).pack()
        
        ttk.Button(
            ticket_frame, 
            text="✅ ACEPTAR", 
            command=ticket_window.destroy
        ).pack(pady=12, ipady=5, ipadx=20)
        
        parent_window.destroy()

    def register_entry(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="🚗 REGISTRAR ENTRADA", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="PLACA:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        plate = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        plate.pack(pady=8, ipady=3)
        
        tk.Label(
            entry_frame, 
            text="TIPO DE VEHÍCULO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        vehicle_type = ttk.Combobox(
            entry_frame, 
            values=["carro", "moto", "cicla"], 
            font=("Arial", 16)
        )
        vehicle_type.set("carro")
        vehicle_type.pack(pady=8, ipady=3)
        
        ttk.Button(
            main_frame, 
            text="✅ REGISTRAR", 
            command=lambda: self.add_vehicle(plate.get(), datetime.now(), vehicle_type.get())
        ).pack(pady=10, ipady=6, ipadx=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def add_vehicle(self, plate, entry_time, vehicle_type):
        if plate and vehicle_type in ["carro", "moto", "cicla"]:
            try:
                self.db.cursor.execute("SELECT id FROM vehicles WHERE plate = %s AND exit_time IS NULL", (plate,))
                existing_vehicle = self.db.cursor.fetchone()
                if existing_vehicle:
                    messagebox.showerror("Error", f"El vehículo {plate} ya está en el parqueadero.", parent=self.root)
                    return

                self.db.cursor.execute("SELECT id, space_number FROM parking_spaces WHERE status = 'available' ORDER BY space_number LIMIT 1")
                space = self.db.cursor.fetchone()
                
                if not space:
                    messagebox.showerror("Error", "No hay espacios disponibles.", parent=self.root)
                    return
                
                space_id, space_number = space
                
                self.db.cursor.execute("UPDATE parking_spaces SET status = 'occupied', vehicle_plate = %s, occupied_since = %s WHERE id = %s",
                    (plate, entry_time, space_id)
                )
                
                self.db.cursor.execute(
                    "INSERT INTO vehicles (plate, vehicle_type, entry_time, space_id) VALUES (%s, %s, %s, %s)",
                    (plate, vehicle_type, entry_time, space_id)
                )
                self.db.commit()
                
                messagebox.showinfo("Éxito", f"Entrada registrada: {plate}\nEspacio: {space_number}", parent=self.root)
                self.create_main_screen()
            except mysql.connector.Error as err:
                if err.errno == 1146:
                    self.db.cursor.execute("""
                        CREATE TABLE vehicles (
                            id INT AUTO_INCREMENT PRIMARY KEY,
                            plate VARCHAR(10) NOT NULL,
                            vehicle_type VARCHAR(10) NOT NULL,
                            entry_time DATETIME NOT NULL,
                            exit_time DATETIME,
                            cost INT,
                            space_id INT
                        )
                    """)
                    self.db.commit()
                    self.db.cursor.execute(
                        "INSERT INTO vehicles (plate, vehicle_type, entry_time) VALUES (%s, %s, %s)",
                        (plate, vehicle_type, entry_time)
                    )
                    self.db.commit()
                    messagebox.showinfo("Éxito", f"Entrada registrada: {plate}", parent=self.root)
                    self.create_main_screen()
                else:
                    messagebox.showerror("Error", f"No se pudo registrar: {err}", parent=self.root)
        else:
            messagebox.showerror("Error", "Ingrese placa y tipo de vehículo válido", parent=self.root)

    def register_exit(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="🚙 REGISTRAR SALIDA", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="PLACA:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        self.exit_plate = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        self.exit_plate.pack(pady=8, ipady=3)
        
        ttk.Button(
            main_frame, 
            text="🔍 BUSCAR", 
            command=self.search_vehicle_for_exit
        ).pack(pady=10, ipady=6, ipadx=20)
        
        self.exit_info_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        self.exit_info_frame.pack(pady=15, padx=40, fill="x", ipady=15)
        tk.Label(
            self.exit_info_frame, 
            text="Busque un vehículo", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=15)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def search_vehicle_for_exit(self):
        plate = self.exit_plate.get().strip().upper()
        
        if not plate:
            messagebox.showerror("Error", "Ingrese una placa", parent=self.root)
            return
        
        try:
            self.db.cursor.execute("""
                SELECT v.id, v.vehicle_type, v.entry_time, v.space_id, ps.space_number
                FROM vehicles v
                LEFT JOIN parking_spaces ps ON v.space_id = ps.id
                WHERE v.plate = %s AND v.exit_time IS NULL
            """, (plate,))
            vehicle = self.db.cursor.fetchone()
            
            if not vehicle:
                for widget in self.exit_info_frame.winfo_children():
                    widget.destroy()
                tk.Label(
                    self.exit_info_frame, 
                    text="❌ NO ENCONTRADO", 
                    fg=self.ERROR_COLOR, 
                    bg=self.CARD_COLOR, 
                    font=("Arial", 16, "bold")
                ).pack(pady=15)
                return
            
            for widget in self.exit_info_frame.winfo_children():
                widget.destroy()
            
            vehicle_id, vehicle_type, entry_time, space_id, space_number = vehicle
            time_diff = (datetime.now() - entry_time).total_seconds()
            hours = math.ceil(time_diff / 3600)
            rate = self.rates.get(vehicle_type, 3000)
            cost = hours * rate
            
            info_text = f"""
✅ VEHÍCULO ENCONTRADO

PLACA: {plate}
TIPO: {vehicle_type}
ESPACIO: {space_number}

ENTRADA: {entry_time.strftime('%Y-%m-%d %H:%M:%S')}
TIEMPO: {self.format_time_difference(time_diff)}
HORAS: {hours}

TARIFA: ${rate:,}/hora
TOTAL: {self.format_currency(cost)}
            """
            
            tk.Label(
                self.exit_info_frame, 
                text=info_text, 
                fg=self.SECONDARY_COLOR, 
                bg=self.CARD_COLOR, 
                font=("Arial", 14), 
                justify="left"
            ).pack(pady=10)
            
            pay_btn = ttk.Button(
                self.exit_info_frame, 
                text="💳 PAGAR Y SALIR", 
                command=lambda: self.remove_vehicle(plate, datetime.now())
            )
            pay_btn.pack(pady=10, ipady=5, ipadx=15)
            
            self.current_exit_vehicle = {
                'plate': plate,
                'id': vehicle_id,
                'space_id': space_id,
                'cost': cost,
                'space_number': space_number
            }
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}", parent=self.root)

    def remove_vehicle(self, plate, exit_time):
        self.db.cursor.execute("""
            SELECT v.id, v.vehicle_type, v.entry_time, v.space_id, ps.space_number
            FROM vehicles v
            LEFT JOIN parking_spaces ps ON v.space_id = ps.id
            WHERE v.plate = %s AND v.exit_time IS NULL
        """, (plate,))
        vehicle = self.db.cursor.fetchone()
        
        if vehicle:
            vehicle_id, vehicle_type, entry_time, space_id, space_number = vehicle
            time_diff_seconds = (exit_time - entry_time).total_seconds()
            hours_charged = math.ceil(time_diff_seconds / 3600)
            cost = hours_charged * self.rates[vehicle_type]
            date_key = exit_time.strftime("%Y-%m-%d")
            
            timer_end = exit_time + timedelta(minutes=3)
            
            self.db.cursor.execute(
                "UPDATE vehicles SET cost = %s, exit_timer_end = %s WHERE id = %s",
                (cost, timer_end, vehicle_id)
            )
            
            if space_id:
                self.db.cursor.execute(
                    "UPDATE parking_spaces SET status = 'exiting', occupied_since = %s WHERE id = %s",
                    (exit_time, space_id)
                )
            
            try:
                self.db.cursor.execute(
                    "INSERT INTO daily_income (date, total_income) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_income = total_income + %s",
                    (date_key, cost, cost)
                )
                self.db.commit()
            except mysql.connector.Error as err:
                if err.errno == 1146:
                    self.db.cursor.execute("""
                        CREATE TABLE daily_income (
                            date DATE PRIMARY KEY,
                            total_income INT NOT NULL DEFAULT 0
                        )
                    """)
                    self.db.commit()
                    self.db.cursor.execute(
                        "INSERT INTO daily_income (date, total_income) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_income = total_income + %s",
                        (date_key, cost, cost)
                    )
                    self.db.commit()
                else:
                    raise err
            
            self.start_exit_timer(vehicle_id, space_id, timer_end, plate)
            
            timer_end_str = timer_end.strftime('%H:%M:%S')
            messagebox.showinfo(
                "✅ PAGO PROCESADO", 
                f"Pago: {plate}\nMonto: {self.format_currency(cost)}\n\n"
                f"⏰ SALIR ANTES DE: {timer_end_str}\n(3 minutos)",
                parent=self.root
            )
            self.create_main_screen()
        else:
            messagebox.showerror("Error", "Placa no encontrada", parent=self.root)

    def start_exit_timer(self, vehicle_id, space_id, timer_end, plate):
        def finalize_exit():
            try:
                now = datetime.now()
                if now >= timer_end:
                    self.db.cursor.execute(
                        "UPDATE vehicles SET exit_time = %s WHERE id = %s AND exit_time IS NULL",
                        (timer_end, vehicle_id)
                    )
                    if space_id:
                        self.db.cursor.execute(
                            "UPDATE parking_spaces SET status = 'available', vehicle_plate = NULL, occupied_since = NULL WHERE id = %s",
                            (space_id,)
                        )
                    self.db.commit()
            except Exception as e:
                print(f"Error: {e}")
        
        delay = (timer_end - datetime.now()).total_seconds()
        if delay > 0:
            timer = threading.Timer(delay, finalize_exit)
            timer.daemon = True
            timer.start()
            self.exit_timers[plate] = {'timer': timer, 'end_time': timer_end}

    def register_expense(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="💰 REGISTRAR GASTO", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="DESCRIPCIÓN:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        desc = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        desc.pack(pady=8, ipady=3)
        
        tk.Label(
            entry_frame, 
            text="MONTO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        amount = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        amount.pack(pady=8, ipady=3)
        
        ttk.Button(
            main_frame, 
            text="✅ REGISTRAR", 
            command=lambda: self.add_expense(desc.get(), amount.get())
        ).pack(pady=10, ipady=6, ipadx=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def add_expense(self, desc, amount_str):
        try:
            amount = int(float(str(amount_str).replace(',', '')))
            if desc.strip() and amount > 0:
                current_date = datetime.now().strftime("%Y-%m-%d")
                self.db.cursor.execute(
                    "INSERT INTO expenses (description, amount, date) VALUES (%s, %s, %s)",
                    (desc.strip(), amount, current_date)
                )
                try:
                    self.db.cursor.execute(
                        "INSERT INTO daily_expenses (date, total_expenses) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_expenses = total_expenses + %s",
                        (current_date, amount, amount)
                    )
                except mysql.connector.Error as err:
                    if err.errno == 1146:
                        self.db.cursor.execute("""
                            CREATE TABLE daily_expenses (
                                date DATE PRIMARY KEY,
                                total_expenses INT NOT NULL DEFAULT 0
                            )
                        """)
                        self.db.commit()
                        self.db.cursor.execute(
                            "INSERT INTO daily_expenses (date, total_expenses) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_expenses = total_expenses + %s",
                            (current_date, amount, amount)
                        )
                    else:
                        raise err
                self.db.commit()
                messagebox.showinfo("Éxito", f"Gasto registrado: {self.format_currency(amount)}", parent=self.root)
                self.create_main_screen()
            else:
                messagebox.showerror("Error", "Descripción y monto válidos requeridos", parent=self.root)
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE expenses (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        description VARCHAR(255) NOT NULL,
                        amount INT NOT NULL,
                        date DATE NOT NULL
                    )
                """)
                self.db.commit()
                current_date = datetime.now().strftime("%Y-%m-%d")
                self.db.cursor.execute(
                    "INSERT INTO expenses (description, amount, date) VALUES (%s, %s, %s)",
                    (desc.strip(), amount, current_date)
                )
                self.db.cursor.execute(
                    "INSERT INTO daily_expenses (date, total_expenses) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_expenses = total_expenses + %s",
                    (current_date, amount, amount)
                )
                self.db.commit()
                messagebox.showinfo("Éxito", f"Gasto registrado: {self.format_currency(amount)}", parent=self.root)
                self.create_main_screen()
            else:
                messagebox.showerror("Error", f"Error: {err}", parent=self.root)
        except ValueError:
            messagebox.showerror("Error", "Monto debe ser número válido", parent=self.root)

    def show_statistics(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=15)
        tk.Label(
            title_frame, 
            text="📊 ESTADÍSTICAS", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        period_frame = Frame(main_frame, bg=self.BG_COLOR)
        period_frame.pack(pady=15)
        
        ttk.Button(
            period_frame, 
            text="📅 DIARIO", 
            command=lambda: self.show_graph('daily')
        ).pack(side="left", padx=10, ipady=5, ipadx=15)
        ttk.Button(
            period_frame, 
            text="📆 SEMANAL", 
            command=lambda: self.show_graph('weekly')
        ).pack(side="left", padx=10, ipady=5, ipadx=15)
        ttk.Button(
            period_frame, 
            text="🗓️ MENSUAL", 
            command=lambda: self.show_graph('monthly')
        ).pack(side="left", padx=10, ipady=5, ipadx=15)
        
        self.graph_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        self.graph_frame.pack(pady=15, fill="both", expand=True, ipady=15)
        
        tk.Label(
            self.graph_frame, 
            text="Seleccione un período", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 16)
        ).pack(pady=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def show_graph(self, period):
        for widget in self.graph_frame.winfo_children():
            widget.destroy()
        
        try:
            if period == 'daily':
                self.db.cursor.execute("""
                    SELECT date, total_income 
                    FROM daily_income 
                    ORDER BY date DESC 
                    LIMIT 7
                """)
                data = self.db.cursor.fetchall()
                if data:
                    data.reverse()
                title = "Ingresos Diarios - 7 días"
                xlabel = "Fecha"
                
            elif period == 'weekly':
                self.db.cursor.execute("""
                    SELECT DATE_FORMAT(date, '%Y-%u') as week, SUM(total_income) as income
                    FROM daily_income
                    GROUP BY week
                    ORDER BY week DESC
                    LIMIT 4
                """)
                raw_data = self.db.cursor.fetchall()
                data = [(f"Sem {i+1}", row[1]) for i, row in enumerate(raw_data)]
                if data:
                    data.reverse()
                title = "Ingresos Semanales - 4 semanas"
                xlabel = "Semana"
                
            else:
                self.db.cursor.execute("""
                    SELECT DATE_FORMAT(date, '%Y-%m') as month, SUM(total_income) as income
                    FROM daily_income
                    GROUP BY month
                    ORDER BY month DESC
                    LIMIT 6
                """)
                data = self.db.cursor.fetchall()
                if data:
                    data.reverse()
                title = "Ingresos Mensuales - 6 meses"
                xlabel = "Mes"
            
            if not data:
                tk.Label(
                    self.graph_frame, 
                    text="No hay datos", 
                    fg=self.WARNING_COLOR, 
                    bg=self.CARD_COLOR, 
                    font=("Arial", 16)
                ).pack(pady=20)
                return
            
            dates = [str(d[0]) for d in data]
            incomes = [d[1] for d in data]
            
            fig, ax = plt.subplots(figsize=(8, 5))
            bars = ax.bar(dates, incomes, color=self.PRIMARY_COLOR, alpha=0.8, edgecolor='black')
            
            ax.set_xlabel(xlabel, fontsize=12, fontweight='bold')
            ax.set_ylabel('Ingresos ($)', fontsize=12, fontweight='bold')
            ax.set_title(title, fontsize=14, fontweight='bold', pad=15)
            ax.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
            
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height,
                        f'${height:,.0f}',
                        ha='center', va='bottom', fontsize=9, fontweight='bold')
            
            plt.tight_layout()
            
            canvas = FigureCanvasTkAgg(fig, master=self.graph_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)
            
        except mysql.connector.Error as err:
            tk.Label(
                self.graph_frame, 
                text=f"Error: {err}", 
                fg=self.ERROR_COLOR, 
                bg=self.CARD_COLOR, 
                font=("Arial", 14)
            ).pack(pady=20)
        except Exception as e:
            tk.Label(
                self.graph_frame, 
                text=f"Error: {e}", 
                fg=self.ERROR_COLOR, 
                bg=self.CARD_COLOR, 
                font=("Arial", 14)
            ).pack(pady=20)

    def show_daily_history(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="📅 HISTORIAL DIARIO", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        history_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        history_frame.pack(pady=20, padx=40, fill="both", expand=True, ipady=15)

        try:
            self.db.cursor.execute("SELECT date, total_income FROM daily_income")
            daily_income = {row[0]: row[1] for row in self.db.cursor.fetchall()}
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE daily_income (
                        date DATE PRIMARY KEY,
                        total_income INT NOT NULL DEFAULT 0
                    )
                """)
                self.db.commit()
                daily_income = {}
            else:
                raise err

        try:
            self.db.cursor.execute("SELECT date, total_expenses FROM daily_expenses")
            daily_expenses = {row[0]: row[1] for row in self.db.cursor.fetchall()}
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE daily_expenses (
                        date DATE PRIMARY KEY,
                        total_expenses INT NOT NULL DEFAULT 0
                    )
                """)
                self.db.commit()
                daily_expenses = {}
            else:
                raise err

        if not daily_income and not daily_expenses:
            tk.Label(
                history_frame, 
                text="No hay historial", 
                fg=self.SECONDARY_COLOR, 
                bg=self.CARD_COLOR, 
                font=("Arial", 16)
            ).pack(pady=15)
        else:
            dates = set(daily_income.keys()) | set(daily_expenses.keys())
            for date in sorted(dates):
                income = daily_income.get(date, 0)
                expenses = daily_expenses.get(date, 0)
                net = income - expenses
                tk.Label(
                    history_frame, 
                    text=f"📅 {date} | Ingresos: {self.format_currency(income)} | Gastos: {self.format_currency(expenses)} | Neto: {self.format_currency(net)}", 
                    fg=self.SECONDARY_COLOR, 
                    bg=self.CARD_COLOR, 
                    font=("Arial", 14)
                ).pack(pady=5)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def show_cash_closure_prompt(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="🏦 CIERRE DE CAJA", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        prompt_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        prompt_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            prompt_frame, 
            text="¿Realizar cierre de caja hoy?", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 18)
        ).pack(pady=15)
        
        ttk.Button(
            prompt_frame, 
            text="✅ REALIZAR", 
            command=self.perform_cash_closure
        ).pack(pady=10, ipady=5, ipadx=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def perform_cash_closure(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="🏦 CIERRE DE CAJA", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        closure_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        closure_frame.pack(pady=20, padx=40, fill="both", expand=True, ipady=15)

        current_date = datetime.now().strftime("%Y-%m-%d")
        tk.Label(
            closure_frame, 
            text=f"📅 Día: {current_date}", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 18)
        ).pack(pady=8)

        try:
            self.db.cursor.execute("SELECT total_income FROM daily_income WHERE date = %s", (current_date,))
            total_income_result = self.db.cursor.fetchone()
            total_income = total_income_result[0] if total_income_result else 0
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE daily_income (
                        date DATE PRIMARY KEY,
                        total_income INT NOT NULL DEFAULT 0
                    )
                """)
                self.db.commit()
                total_income = 0
            else:
                raise err
        
        tk.Label(
            closure_frame, 
            text=f"💵 Ingresos: {self.format_currency(total_income)}", 
            fg=self.SUCCESS_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 18, "bold")
        ).pack(pady=8)

        try:
            self.db.cursor.execute("SELECT description, amount FROM expenses WHERE date = %s", (current_date,))
            expenses = self.db.cursor.fetchall()
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE expenses (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        description VARCHAR(255) NOT NULL,
                        amount INT NOT NULL,
                        date DATE NOT NULL
                    )
                """)
                self.db.commit()
                expenses = []
            else:
                raise err
        
        total_expenses = sum(expense[1] for expense in expenses)
        
        tk.Label(
            closure_frame, 
            text="📊 Gastos:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 16, "bold")
        ).pack(pady=8)
        
        if not expenses:
            tk.Label(
                closure_frame, 
                text="Sin gastos hoy", 
                fg=self.SECONDARY_COLOR, 
                bg=self.CARD_COLOR, 
                font=("Arial", 14)
            ).pack(pady=3)
        else:
            for desc, amount in expenses:
                tk.Label(
                    closure_frame, 
                    text=f"- {desc}: {self.format_currency(amount)}", 
                    fg=self.SECONDARY_COLOR, 
                    bg=self.CARD_COLOR, 
                    font=("Arial", 14)
                ).pack(pady=2)
        
        tk.Label(
            closure_frame, 
            text=f"💸 Total Gastos: {self.format_currency(total_expenses)}", 
            fg=self.ERROR_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 18, "bold")
        ).pack(pady=8)

        net_profit = total_income - total_expenses
        tk.Label(
            closure_frame, 
            text=f"💰 GANANCIA NETA: {self.format_currency(net_profit)}", 
            fg=self.PRIMARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 20, "bold")
        ).pack(pady=12)

        ttk.Button(
            main_frame, 
            text="🔄 CONFIRMAR", 
            command=lambda: self.confirm_cash_closure(current_date)
        ).pack(pady=10, ipady=6, ipadx=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def confirm_cash_closure(self, current_date):
        messagebox.showinfo(
            "✅ CIERRE COMPLETADO", 
            "Cierre realizado.\n\n"
            "• Ingresos y gastos guardados\n"
            "• Historial intacto\n"
            "• Nuevo día mañana con contadores en cero\n\n"
            "¡Gracias!",
            parent=self.root
        )
        self.logout()

    def show_current_vehicles(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=15)
        tk.Label(
            title_frame, 
            text="📋 VEHÍCULOS ACTUALES", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        container = Frame(main_frame, bg=self.BG_COLOR)
        container.pack(fill="both", expand=True, padx=15, pady=15)

        canvas = tk.Canvas(container, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        scrollable_frame = Frame(canvas, bg=self.BG_COLOR)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_and_display_current_vehicles(scrollable_frame)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def load_and_display_current_vehicles(self, scrollable_frame):
        for widget in scrollable_frame.winfo_children():
            widget.destroy()
        
        try:
            self.db.cursor.execute("""
                SELECT v.plate, v.vehicle_type, v.entry_time, v.exit_timer_end, ps.space_number, ps.status
                FROM vehicles v
                LEFT JOIN parking_spaces ps ON v.space_id = ps.id
                WHERE v.exit_time IS NULL
                ORDER BY v.entry_time ASC
            """)
            current_vehicles = self.db.cursor.fetchall()
            
            if not current_vehicles:
                tk.Label(
                    scrollable_frame, 
                    text="✅ PARQUEADERO VACÍO", 
                    fg=self.SUCCESS_COLOR, 
                    bg=self.BG_COLOR, 
                    font=("Arial", 18, "bold")
                ).pack(pady=20)
            else:
                tk.Label(
                    scrollable_frame, 
                    text=f"VEHÍCULOS: {len(current_vehicles)}",
                    fg=self.PRIMARY_COLOR, 
                    bg=self.BG_COLOR, 
                    font=("Arial", 16, "bold")
                ).pack(pady=10)
                
                vehicles_container = Frame(scrollable_frame, bg=self.BG_COLOR)
                vehicles_container.pack(fill="x", padx=15, pady=8)
                
                for i, (plate, vehicle_type, entry_time, exit_timer_end, space_number, space_status) in enumerate(current_vehicles):
                    time_diff_seconds = (datetime.now() - entry_time).total_seconds()
                    time_str = self.format_time_difference(time_diff_seconds)
                    
                    if exit_timer_end and datetime.now() < exit_timer_end:
                        remaining = (exit_timer_end - datetime.now()).total_seconds()
                        mins = int(remaining // 60)
                        secs = int(remaining % 60)
                        status_text = f"⏰ SALIENDO EN {mins:02d}:{secs:02d}"
                        bg_color = self.WARNING_COLOR
                        fg_color = "black"
                    else:
                        status_text = "🅿️ ESTACIONADO"
                        bg_color = self.CARD_COLOR if i % 2 == 0 else self.BG_COLOR
                        fg_color = self.SECONDARY_COLOR
                    
                    vehicle_frame = Frame(vehicles_container, bg=bg_color, relief="solid", bd=1)
                    vehicle_frame.pack(fill="x", pady=3, padx=8, ipady=6)
                    
                    tk.Label(
                        vehicle_frame, 
                        text=f"🚗 {plate} | {vehicle_type} | {space_number or 'N/A'}", 
                        fg=fg_color, 
                        bg=bg_color, 
                        font=("Arial", 14, "bold")
                    ).pack(pady=3, padx=10, fill="x")
                    tk.Label(
                        vehicle_frame, 
                        text=f"⏱️ {time_str} | {status_text}", 
                        fg=fg_color, 
                        bg=bg_color, 
                        font=("Arial", 13)
                    ).pack(pady=2, padx=10, fill="x")
                
                tk.Label(
                    scrollable_frame, 
                    text="🟦 Normal | 🟠 Saliendo (3 min)", 
                    fg=self.SECONDARY_COLOR, 
                    bg=self.BG_COLOR, 
                    font=("Arial", 13)
                ).pack(pady=10)
                
                ttk.Button(
                    scrollable_frame, 
                    text="🔄 ACTUALIZAR",
                    command=lambda: self.load_and_display_current_vehicles(scrollable_frame)
                ).pack(pady=10, ipady=4, ipadx=15)
                
        except mysql.connector.Error as err:
            tk.Label(
                scrollable_frame, 
                text=f"Error: {err}", 
                fg=self.ERROR_COLOR, 
                bg=self.BG_COLOR, 
                font=("Arial", 14)
            ).pack(pady=20)

    def register_day_rate(self):
        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="🏍️ DÍA MOTO/CARRO", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="TIPO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        vehicle_type = ttk.Combobox(
            entry_frame, 
            values=["carro", "moto"], 
            font=("Arial", 16)
        )
        vehicle_type.set("carro")
        vehicle_type.pack(pady=8, ipady=3)
        
        ttk.Button(
            main_frame, 
            text="✅ REGISTRAR", 
            command=lambda: self.add_day_rate(vehicle_type.get())
        ).pack(pady=10, ipady=6, ipadx=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def add_day_rate(self, vehicle_type):
        if vehicle_type in ["carro", "moto"]:
            cost = 18000 if vehicle_type == "carro" else 12000
            current_date = datetime.now().strftime("%Y-%m-%d")
            try:
                self.db.cursor.execute(
                    "INSERT INTO daily_income (date, total_income) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_income = total_income + %s",
                    (current_date, cost, cost)
                )
                self.db.commit()
                messagebox.showinfo("Éxito", f"Registrado: {vehicle_type} - {self.format_currency(cost)}", parent=self.root)
                self.create_main_screen()
            except mysql.connector.Error as err:
                if err.errno == 1146:
                    self.db.cursor.execute("""
                        CREATE TABLE daily_income (
                            date DATE PRIMARY KEY,
                            total_income INT NOT NULL DEFAULT 0
                        )
                    """)
                    self.db.commit()
                    self.db.cursor.execute(
                        "INSERT INTO daily_income (date, total_income) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_income = total_income + %s",
                        (current_date, cost, cost)
                    )
                    self.db.commit()
                    messagebox.showinfo("Éxito", f"Registrado: {vehicle_type} - {self.format_currency(cost)}", parent=self.root)
                    self.create_main_screen()
                else:
                    messagebox.showerror("Error", f"Error: {err}", parent=self.root)
        else:
            messagebox.showerror("Error", "Tipo inválido", parent=self.root)

    def manage_users(self):
        if self.current_user != "admin":
            messagebox.showerror("Acceso Denegado", "Solo administrador", parent=self.root)
            return

        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="👥 USUARIOS", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="USUARIO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        user = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        user.pack(pady=8, ipady=3)
        
        tk.Label(
            entry_frame, 
            text="CONTRASEÑA:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        password = tk.Entry(
            entry_frame, 
            show="*", 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        password.pack(pady=8, ipady=3)
        
        ttk.Button(
            main_frame, 
            text="✅ AGREGAR", 
            command=lambda: self.add_user(user.get(), password.get())
        ).pack(pady=8, ipady=5, ipadx=15)
        ttk.Button(
            main_frame, 
            text="❌ ELIMINAR", 
            command=lambda: self.remove_user(user.get())
        ).pack(pady=8, ipady=5, ipadx=15)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def add_user(self, username, password):
        if username and password:
            try:
                self.db.cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
                self.db.commit()
                messagebox.showinfo("Éxito", f"Usuario {username} agregado", parent=self.root)
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Error: {err}", parent=self.root)
        else:
            messagebox.showerror("Error", "Campos vacíos", parent=self.root)

    def remove_user(self, username):
        if username and username != "admin":
            try:
                self.db.cursor.execute("DELETE FROM users WHERE username = %s", (username,))
                if self.db.cursor.rowcount > 0:
                    self.db.commit()
                    messagebox.showinfo("Éxito", f"Usuario {username} eliminado", parent=self.root)
                else:
                    messagebox.showerror("Error", "Usuario no existe", parent=self.root)
            except mysql.connector.Error as err:
                messagebox.showerror("Error", f"Error: {err}", parent=self.root)
        else:
            messagebox.showerror("Error", "No puede eliminar admin", parent=self.root)

    def modify_rates(self):
        if self.current_user != "admin":
            messagebox.showerror("Acceso Denegado", "Solo administrador", parent=self.root)
            return

        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="💸 TARIFAS", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        entry_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        entry_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            entry_frame, 
            text="TIPO:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        vehicle_type = ttk.Combobox(
            entry_frame, 
            values=["carro", "moto", "cicla"], 
            font=("Arial", 16)
        )
        vehicle_type.set("carro")
        vehicle_type.pack(pady=8, ipady=3)
        
        tk.Label(
            entry_frame, 
            text="NUEVA TARIFA:", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=self.FONT_BODY
        ).pack(pady=8)
        new_rate = tk.Entry(
            entry_frame, 
            bg="white", 
            font=("Arial", 18), 
            bd=2, 
            relief="solid"
        )
        new_rate.pack(pady=8, ipady=3)
        
        ttk.Button(
            main_frame, 
            text="✅ ACTUALIZAR", 
            command=lambda: self.update_rate(vehicle_type.get(), new_rate.get())
        ).pack(pady=10, ipady=6, ipadx=20)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def update_rate(self, vehicle_type, rate_str):
        try:
            rate = int(float(str(rate_str).replace(',', '')))
            if vehicle_type in ["carro", "moto", "cicla"] and rate > 0:
                self.db.cursor.execute(
                    "UPDATE rates SET rate = %s WHERE vehicle_type = %s",
                    (rate, vehicle_type)
                )
                self.db.commit()
                self.rates[vehicle_type] = rate
                messagebox.showinfo("Éxito", f"Tarifa {vehicle_type}: {self.format_currency(rate)}/hora", parent=self.root)
                self.create_main_screen()
            else:
                messagebox.showerror("Error", "Tipo o tarifa inválida", parent=self.root)
        except ValueError:
            messagebox.showerror("Error", "Tarifa debe ser número", parent=self.root)

    def view_full_report(self):
        if self.current_user != "admin":
            messagebox.showerror("Acceso Denegado", "Solo administrador", parent=self.root)
            return

        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=15)
        tk.Label(
            title_frame, 
            text="📊 REPORTE COMPLETO", 
            font=self.FONT_TITLE, 
            fg=self.PRIMARY_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        container = Frame(main_frame, bg=self.BG_COLOR)
        container.pack(fill="both", expand=True, padx=15, pady=10)

        canvas = tk.Canvas(container, bg=self.BG_COLOR, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        report_frame = Frame(canvas, bg=self.BG_COLOR)
        
        report_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=report_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        try:
            self.db.cursor.execute("SELECT COUNT(*) FROM vehicles")
            total_vehicles = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute("SELECT plate, vehicle_type, entry_time, exit_time, cost FROM vehicles ORDER BY entry_time DESC")
            all_vehicles = self.db.cursor.fetchall()
        except mysql.connector.Error as err:
            if err.errno == 1146:
                self.db.cursor.execute("""
                    CREATE TABLE vehicles (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        plate VARCHAR(10) NOT NULL,
                        vehicle_type VARCHAR(10) NOT NULL,
                        entry_time DATETIME NOT NULL,
                        exit_time DATETIME,
                        cost INT,
                        space_id INT
                    )
                """)
                self.db.commit()
                all_vehicles = []
                total_vehicles = 0
            else:
                raise err

        tk.Label(report_frame, text=f"VEHÍCULOS: {total_vehicles}", fg=self.PRIMARY_COLOR, bg=self.BG_COLOR, font=("Arial", 16, "bold")).pack(pady=5)
        
        if not all_vehicles:
            tk.Label(report_frame, text="Sin registros", fg=self.SECONDARY_COLOR, bg=self.BG_COLOR, font=("Arial", 14)).pack(pady=2)
        else:
            self.db.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE exit_time IS NULL")
            current_vehicles = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE vehicle_type = 'carro'")
            carros = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE vehicle_type = 'moto'")
            motos = self.db.cursor.fetchone()[0]
            
            self.db.cursor.execute("SELECT COUNT(*) FROM vehicles WHERE vehicle_type = 'cicla'")
            ciclas = self.db.cursor.fetchone()[0]
            
            stats_text = f"📊 Actuales: {current_vehicles} | Carros: {carros} | Motos: {motos} | Ciclas: {ciclas}"
            tk.Label(report_frame, text=stats_text, fg=self.PRIMARY_COLOR, bg=self.BG_COLOR, font=("Arial", 14, "bold")).pack(pady=5)
            
            for vehicle in all_vehicles:
                plate, vehicle_type, entry_time, exit_time, cost = vehicle
                
                if exit_time:
                    time_diff_seconds = (exit_time - entry_time).total_seconds()
                    time_str = self.format_time_difference(time_diff_seconds)
                    cost_str = self.format_currency(cost) if cost is not None else "Pendiente"
                    status = "SALIÓ"
                else:
                    time_diff_seconds = (datetime.now() - entry_time).total_seconds()
                    time_str = self.format_time_difference(time_diff_seconds)
                    cost_str = "En parqueadero"
                    status = "ACTUAL"
                
                vehicle_frame = Frame(report_frame, bg=self.CARD_COLOR, relief="solid", bd=1)
                vehicle_frame.pack(fill="x", pady=2, padx=5)
                
                vehicle_info = f"{plate} | {vehicle_type} | {status} | {time_str} | {cost_str}"
                vehicle_label = tk.Label(vehicle_frame, text=vehicle_info, fg=self.SECONDARY_COLOR, bg=self.CARD_COLOR, 
                                       font=("Arial", 12), anchor="w", justify="left")
                vehicle_label.pack(pady=4, padx=8, fill="x")

        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def show_reset_system(self):
        if self.current_user != "admin":
            messagebox.showerror("Acceso Denegado", "Solo administrador", parent=self.root)
            return

        self.clear_screen()
        main_frame = Frame(self.root, bg=self.BG_COLOR)
        main_frame.pack(expand=True, fill="both", padx=30, pady=20)

        title_frame = Frame(main_frame, bg=self.BG_COLOR)
        title_frame.pack(pady=20)
        tk.Label(
            title_frame, 
            text="🔄 REINICIAR", 
            font=self.FONT_TITLE, 
            fg=self.ACCENT_COLOR, 
            bg=self.BG_COLOR
        ).pack()

        prompt_frame = Frame(main_frame, bg=self.CARD_COLOR, bd=2, relief="solid")
        prompt_frame.pack(pady=20, padx=40, fill="x", ipady=15)
        
        tk.Label(
            prompt_frame, 
            text="⚠️ ESTO ELIMINARÁ TODOS LOS DATOS", 
            fg=self.ERROR_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 16, "bold")
        ).pack(pady=8)
        tk.Label(
            prompt_frame, 
            text="¿ESTÁ SEGURO?", 
            fg=self.SECONDARY_COLOR, 
            bg=self.CARD_COLOR, 
            font=("Arial", 16)
        ).pack(pady=8)
        
        ttk.Button(
            prompt_frame, 
            text="✅ CONFIRMAR", 
            command=self.reset_system
        ).pack(pady=10, ipady=5, ipadx=15)
        
        # ============ BOTONES INFERIORES ============
        bottom_frame = Frame(main_frame, bg=self.BG_COLOR)
        bottom_frame.pack(side="bottom", pady=15)
        
        ttk.Button(
            bottom_frame, 
            text="🔙 VOLVER ATRÁS", 
            command=self.create_main_screen
        ).pack(side="left", padx=15, ipady=6, ipadx=15)
        
        ttk.Button(
            bottom_frame, 
            text="❌ SALIR", 
            command=self.root.quit
        ).pack(side="left", padx=15, ipady=6, ipadx=15)

    def reset_system(self):
        try:
            self.db.cursor.execute("DELETE FROM vehicles")
            self.db.cursor.execute("DELETE FROM daily_income")
            self.db.cursor.execute("DELETE FROM expenses")
            self.db.cursor.execute("DELETE FROM daily_expenses")
            self.db.cursor.execute("DELETE FROM daily_net_totals")
            self.db.cursor.execute("DELETE FROM reset_dates")
            self.db.cursor.execute("INSERT INTO reset_dates (last_reset_date) VALUES (%s)", (datetime.now().date(),))
            self.db.commit()
            messagebox.showinfo("Éxito", "Sistema reiniciado", parent=self.root)
            self.logout()
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}", parent=self.root)

    def generate_test_data(self):
        if self.current_user != "admin":
            messagebox.showerror("Acceso Denegado", "Solo administrador", parent=self.root)
            return

        confirm = messagebox.askyesno(
            "Generar Datos", 
            "⚠️ Generará 1000 registros aleatorios.\n\n¿Continuar?",
            parent=self.root
        )
        
        if not confirm:
            return

        try:
            progress_window = Toplevel(self.root)
            progress_window.title("Generando...")
            progress_window.geometry("350x120")
            progress_window.configure(bg=self.BG_COLOR)
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            tk.Label(progress_window, text="Generando 1000 registros...", 
                    fg=self.SECONDARY_COLOR, bg=self.BG_COLOR, font=("Arial", 14)).pack(pady=10)
            
            progress = ttk.Progressbar(progress_window, orient="horizontal", length=280, mode="determinate")
            progress.pack(pady=10)
            progress["maximum"] = 1000
            progress["value"] = 0
            
            self.db.cursor.execute("DELETE FROM vehicles")
            self.db.cursor.execute("DELETE FROM daily_income")
            self.db.cursor.execute("DELETE FROM expenses")
            self.db.cursor.execute("DELETE FROM daily_expenses")
            self.db.cursor.execute("DELETE FROM daily_net_totals")
            self.db.cursor.execute("DELETE FROM reset_dates")
            self.db.cursor.execute("INSERT INTO reset_dates (last_reset_date) VALUES (%s)", (datetime.now().date(),))

            plates_used = set()
            
            for i in range(1000):
                while True:
                    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
                    numbers = ''.join(random.choices('0123456789', k=3))
                    plate = f"{letters}{numbers}"
                    if plate not in plates_used:
                        plates_used.add(plate)
                        break
                
                if i < 700:
                    vehicle_type = "carro"
                elif i < 950:
                    vehicle_type = "moto"
                else:
                    vehicle_type = "cicla"
                
                days_ago = random.randint(0, 30)
                entry_time = datetime.now() - timedelta(days=days_ago, 
                                                       hours=random.randint(0, 23),
                                                       minutes=random.randint(0, 59))
                
                if random.random() < 0.8:
                    stay_hours = random.uniform(0.5, 48)
                    exit_time = entry_time + timedelta(hours=stay_hours)
                    
                    time_diff_seconds = (exit_time - entry_time).total_seconds()
                    hours_charged = math.ceil(time_diff_seconds / 3600)
                    cost = hours_charged * self.rates[vehicle_type]
                    
                    self.db.cursor.execute(
                        "INSERT INTO vehicles (plate, vehicle_type, entry_time, exit_time, cost) VALUES (%s, %s, %s, %s, %s)",
                        (plate, vehicle_type, entry_time, exit_time, cost)
                    )
                    
                    date_key = exit_time.strftime("%Y-%m-%d")
                    self.db.cursor.execute(
                        "INSERT INTO daily_income (date, total_income) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_income = total_income + %s",
                        (date_key, cost, cost)
                    )
                else:
                    self.db.cursor.execute(
                        "INSERT INTO vehicles (plate, vehicle_type, entry_time) VALUES (%s, %s, %s)",
                        (plate, vehicle_type, entry_time)
                    )
                
                progress["value"] = i + 1
                progress_window.update()
            
            expense_descriptions = [
                "Mantenimiento", "Limpieza", "Material oficina",
                "Servicios", "Reparación", "Publicidad",
                "Seguros", "Impuestos", "Combustible", "Alimentación"
            ]
            
            for i in range(50):
                desc = random.choice(expense_descriptions)
                amount = random.randint(5000, 50000)
                days_ago = random.randint(0, 30)
                expense_date = datetime.now() - timedelta(days=days_ago)
                date_str = expense_date.strftime("%Y-%m-%d")
                
                self.db.cursor.execute(
                    "INSERT INTO expenses (description, amount, date) VALUES (%s, %s, %s)",
                    (desc, amount, date_str)
                )
                
                self.db.cursor.execute(
                    "INSERT INTO daily_expenses (date, total_expenses) VALUES (%s, %s) ON DUPLICATE KEY UPDATE total_expenses = total_expenses + %s",
                    (date_str, amount, amount)
                )
            
            self.db.commit()
            progress_window.destroy()
            
            self.db.cursor.execute("SELECT COUNT(*) FROM vehicles")
            total_vehicles = self.db.cursor.fetchone()[0]
            
            messagebox.showinfo(
                "Datos Generados", 
                f"✅ {total_vehicles} vehículos\n50 gastos\nÚltimos 30 días",
                parent=self.root
            )
            
        except mysql.connector.Error as err:
            messagebox.showerror("Error", f"Error: {err}", parent=self.root)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {e}", parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    
    style = ttk.Style()
    style.configure("TButton", 
                    font=("Arial", 14, "bold"),
                    padding=8)
    style.configure("Warning.TButton",
                    font=("Arial", 14, "bold"),
                    padding=10,
                    foreground="#FF9800")
    style.configure("Danger.TButton",
                    font=("Arial", 14, "bold"),
                    padding=10,
                    foreground="#F44336")
    
    app = ParkingApp(root)
    root.mainloop()