import yfinance as yf
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import pystray
import threading
import os

# Configuración de actualización
UPDATE_INTERVAL = 10  # Segundos

# Lista de activos disponibles
ASSETS = {
    "S&P 500": "^GSPC",
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Nvidia": "NVDA",
    "Google (Alphabet)": "GOOGL",
    "Amazon": "AMZN",
    "Meta (Facebook)": "META",
    "Tesla": "TSLA"
}

class StockTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stock Tracker")
        self.root.geometry("250x105")
        self.root.configure(bg="black")

        # Interceptar el cierre de la ventana para minimizarla en lugar de cerrarla
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        # Variable de selección
        self.selected_stock = tk.StringVar(value="S&P 500")

        # Menú desplegable
        self.dropdown = ttk.Combobox(root, textvariable=self.selected_stock, values=list(ASSETS.keys()), state="readonly")
        self.dropdown.grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=0)
        self.dropdown.bind("<<ComboboxSelected>>", self.update_stock)

        # Frame para logo y etiqueta de precio
        self.top_frame = tk.Frame(root, bg="black")
        self.top_frame.grid(row=1, column=0, columnspan=2, sticky="w")

        self.stock_label = tk.Label(self.top_frame, text="Cargando...", font=("Arial", 14), bg="black", fg="white")
        self.stock_label.pack(side="left", padx=5)

        self.load_logo()  # Cargar el logo

        # Etiquetas de cambios
        self.today_changes = tk.Label(root, text="Cargando...", font=("Arial", 14), bg="black", fg="white")
        self.yesterday_changes = tk.Label(root, text="Cargando...", font=("Arial", 14), bg="black", fg="white")

        self.today_changes.grid(row=2, column=0, sticky="w", padx=5, pady=0)
        self.yesterday_changes.grid(row=3, column=0, sticky="w", padx=5, pady=0)

        # Iniciar actualización de datos
        self.update_data()

        # Crear icono en la bandeja del sistema
        self.create_system_tray_icon()

    def load_logo(self):
        try:
            logo_path = "tendencia.png"
            if not os.path.exists(logo_path):
                print(f"❌ No se encontró el archivo: {logo_path}")
                return

            logo = Image.open(logo_path).resize((25, 25), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)

            self.logo_label = tk.Label(self.top_frame, image=self.logo_img, bg="black")
            self.logo_label.pack(side="left", padx=5)

        except Exception as e:
            print(f"❌ Error al cargar el logo: {e}")

    def update_stock(self, event=None):
        """ Actualiza la acción seleccionada """
        self.update_data()

    def get_stock_data(self):
        """ Obtiene los datos del activo seleccionado """
        stock_symbol = ASSETS[self.selected_stock.get()]
        sp500 = yf.Ticker(stock_symbol)

        data = sp500.history(period="2d")

        if len(data) < 2:
            return None, None, None, None

        prev_close = data["Close"].iloc[-1]
        prev_close_yesterday = data["Close"].iloc[-2]

        current_data = sp500.history(period="1d", interval="1m")
        current_price = current_data["Close"].iloc[-1] if not current_data.empty else prev_close

        change_today = ((current_price - prev_close) / prev_close) * 100
        change_yesterday = ((prev_close - prev_close_yesterday) / prev_close_yesterday) * 100

        return prev_close, current_price, change_today, change_yesterday

    def update_data(self):
        """ Actualiza los datos en la interfaz cada pocos segundos """
        prev_close, current_price, change_today, change_yesterday = self.get_stock_data()

        if prev_close and current_price:
            color_today = "green" if change_today > 0 else "red"
            color_yesterday = "green" if change_yesterday > 0 else "red"

            text = f"💰 {self.selected_stock.get()} {current_price:.2f} USD"
            textYesterdayChange = f"📊 Hoy: {change_today:.2f}%"
            textToday = f"📉 Ayer: {change_yesterday:.2f}%"

            self.stock_label.config(text=text)
            self.yesterday_changes.config(text=textYesterdayChange, fg=color_yesterday)
            self.today_changes.config(text=textToday, fg=color_today)

        self.root.after(UPDATE_INTERVAL * 1000, self.update_data)

    def create_system_tray_icon(self):
        """ Crea el icono en la bandeja del sistema """
        icon_path = "tendencia.png"  # Cambia esto al icono que quieres mostrar
        if not os.path.exists(icon_path):
            print("❌ No se encontró el icono para la bandeja.")
            return

        image = Image.open(icon_path).resize((32, 32), Image.Resampling.LANCZOS)

        # 📌 Configurar el icono
        self.tray_icon = pystray.Icon("stock_tracker", image, "Stock Tracker")

        # 📌 Asignar clic izquierdo a abrir la ventana
        self.tray_icon.run_detached(setup=self.on_tray_setup)

    def on_tray_setup(self, icon):
        """ Asigna la acción al clic izquierdo cuando el icono está listo """
        icon.visible = True  # Asegura que el icono sea visible
        icon.update_menu()
        icon._menu = pystray.Menu(
            pystray.MenuItem("Abrir", self.show_window, default=True),  # Clic izquierdo abre ventana
            pystray.MenuItem("Salir", self.exit_app)
        )

    def hide_window(self):
        """ Minimiza la ventana en lugar de cerrarla al hacer clic en la 'X' """
        self.root.withdraw()

    def show_window(self, icon=None, item=None):
        """ Muestra la ventana al hacer clic en el icono de la bandeja """
        self.root.deiconify()
        self.root.lift()

    def exit_app(self, icon, item):
        """ Cierra la aplicación completamente """
        self.tray_icon.stop()
        self.root.quit()

# Iniciar la aplicación
root = tk.Tk()
app = StockTrackerApp(root)
root.mainloop()
