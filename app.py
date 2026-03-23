from sys import last_value

from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout,
    QPushButton, QHBoxLayout, QFrame
)
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtWidgets import QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from datetime import datetime
from sensors.gpio_sensors import setup_doors
from PySide6.QtGui import QPen
import random
import time
import pandas as pd

EXIT_CODE = "1234"
from PySide6.QtCore import QTimer, Qt

class BootScreen(QWidget):
    def __init__(self, on_finish):
        super().__init__()

        self.on_finish = on_finish
        self.step = 0
        self.phase = "boot"

        self.setStyleSheet("""
            background-color: #1c1c1c;
            color: #468a1a;
            font-size: 24px;
            font-family: monospace;
        """)

        layout = QVBoxLayout()

        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        layout.addWidget(self.label)
        self.setLayout(layout)

        self.showFullScreen()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_text)
        self.timer.start(400)  # velocidade do "terminal"

    def update_text(self):
        if self.phase == "boot":
            messages = [
                "Booting Darlene OS...",
                "Loading kernel modules...",
                "Initializing subsystems...",
                "Checking sensors...",
                "Mounting storage...",
                "Starting services...",
                "System ready."
            ]

            if self.step < len(messages):
                current = self.label.text()
                self.label.setText(current + "\n" + messages[self.step])
                self.step += 1
            else:
                # muda para fase final
                self.timer.stop()
                QTimer.singleShot(800, self.show_logo)

    def show_logo(self):
        self.phase = "logo"

        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("""
            color: #00ff00;
            font-size: 40px;
            font-family: monospace;
        """)

        self.label.setText("DARLENE OS v1.0")

        # fica 2 segundos
        QTimer.singleShot(2000, self.finish)

    def finish(self):
        self.on_finish()
        self.close()

class Card(QFrame):
    def __init__(self, title):
        super().__init__()

        self.setStyleSheet("""
            QFrame {
                border: 2px solid #00ffcc;
                border-radius: 12px;
                padding: 2px;
                background-color: #050505;
            }
        """)

        layout = QVBoxLayout()

        self.title = QLabel(title)
        self.title.setStyleSheet("font-size: 24px;")

        self.value = QLabel("--")
        self.value.setStyleSheet("font-size: 26px;")

        layout.addWidget(self.title)
        layout.addWidget(self.value)

        self.setLayout(layout)

    def set_color(self, color):
        self.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color};
                border-radius: 10px;
                padding: 2px;
                background-color: #050505;
                font-family: monospace;
            }}
        """)

        self.value.setStyleSheet(f"""
            font-size: 30px;
            color: {color};
            font-family: monospace;
        """)

        # efeito glow leve (simulado via sombra visual)
        self.title.setStyleSheet(f"""
            font-size: 26px;
            color: {color};
        """)

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.input_buffer = ""
        self.command_mode = False
        self.setStyleSheet("""
            background-color: #1c1c1c;
            color: #468a1a;
            font-size: 24px;
            font-family: monospace;
            border: 3px solid #00ffcc;
            border-radius: 12px;
        """)

        # cursor piscante
        self.cursor_visible = True
        self.base_title = "> DARLENE OS:~$ "
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.update_cursor)
        self.cursor_timer.start(500)  # pisca a cada 0.5s


        outer_layout = QVBoxLayout()
        outer_layout.setContentsMargins(8, 8, 8, 8)  # espaço da borda

        self.container = QWidget()
        self.container.setStyleSheet("""
            background-color: #1c1c1c;
            border: 3px solid #00ffcc;
            border-radius: 10px;
            font-size: 22px;
            font-family: monospace;
            color: #468a1a;
        """)

        main_layout = QVBoxLayout()
        self.container.setLayout(main_layout)
        outer_layout.addWidget(self.container)
        self.setLayout(outer_layout)

        self.kombi_view = KombiWidget()
        self.credits_view = CreditsWidget()
        #main_layout.addWidget(self.kombi_view)
        #main_layout.addWidget(self.credits_view)
        self.kombi_view.setVisible(False)
        self.credits_view.setVisible(False)

        # GRAFICOS
        self.graph_view = GraphWidget()
        self.graph_view.setVisible(False)

        # pop up de saida
        self.code_popup = QLabel(self)
        self.code_popup.setAlignment(Qt.AlignCenter)

        self.code_popup.setStyleSheet("""
            background-color: rgba(0, 0, 0, 180);
            color: #ffaa00;
            font-size: 32px;
            border: 2px solid #ffaa00;
            border-radius: 10px;
            padding: 20px;
        """)

        self.code_popup.setFixedSize(200, 100)
        self.code_popup.move(
            (self.width() - 200) // 2,
            (self.height() - 100) // 2
        )
        self.code_popup.hide()


        # CARDS
        self.cards = []
        grid = QGridLayout()

        self.devices_config = [
            # sensores numéricos
            {"name": "> BATERIA 1", "type": "numeric", "unit": "V"},
            {"name": "> BATERIA 2", "type": "numeric", "unit": "V"},
            {"name": "> TEMP MOTOR", "type": "numeric", "unit": "°C"},
            {"name": "> ÁGUA LIMPA", "type": "numeric", "unit": "%"},
            {"name": "> ÁGUA SUJA", "type": "numeric", "unit": "%"},
            {"name": "> SOLAR", "type": "numeric", "unit": "Wh"},
            {"name": "> CONSUMO", "type": "numeric", "unit": "Wh"},

            # dispositivos digitais
            {"name": "> INVERSOR", "type": "digital"},
            {"name": "> BOMBA ÁGUA", "type": "digital"},

            # portas físicas (GPIO)
            {"name": "> MOTORISTA", "pin": 17, "type": "door", "pos": (0.12, 0.19)},
            {"name": "> PASSAGEIRO", "pin": 27, "type": "door", "pos": (0.5, 0.73)},
            {"name": "> CASA", "pin": 22, "type": "door", "pos": (0.32, 0.75)},
            {"name": "> MALA", "pin": 23,  "type": "door", "pos": (0.84, 0.68)},
            {"name": "> MOTOR", "pin": 24,  "type": "door", "pos": (0.84, 0.82)},
            {"name": "> DISPONIVEL", "pin": 17, "type": "door", "pos": (0, 0)},
            {"name": "> DISPONIVEL", "pin": 18, "type": "door", "pos": (0, 0)},
            {"name": "> DISPONIVEL", "pin": 19, "type": "door", "pos": (0, 0)},
            {"name": "> DISPONIVEL", "pin": 20,  "type": "door", "pos": (0, 0)},
        ]

        self.numeric_devices = [d for d in self.devices_config if d["type"] == "numeric"]
        self.digital_devices = [d for d in self.devices_config if d["type"] == "digital"]
        self.door_devices = [d for d in self.devices_config if d["type"] == "door"]
        setup_doors(self.door_devices)

        devices = self.numeric_devices + self.digital_devices

        for i in range(9):
            name = devices[i]["name"] if i < len(devices) else "- DISPONIVEL"

            card = Card(name)
            self.cards.append(card)

            row = i // 3
            col = i % 3
            grid.addWidget(card, row, col)

        self.grid = grid

        # HEADER
        header_layout = QHBoxLayout()

        self.header_container = QWidget()
        self.header_container.setFixedHeight(40)  # altura fixa

        self.header_container.setStyleSheet("""
            background-color: #111;
            border: 2px solid green;
            font-family: monospace;
        """)

        # título
        self.header_title = QLabel("> DARLENE OS:~$ ")
        self.header_title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.header_title.setStyleSheet("""
            font-size: 24px;
            color: #b0b0b0;
            border: 0px;
        """)

        # hora
        self.header_time = QLabel("--:--")
        self.header_time.setAlignment(Qt.AlignRight)
        self.header_time.setStyleSheet("""
            font-size: 27px;
            color: #b0b0b0;
            border: 0px;
        """)

        # layout interno
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.header_time)
        self.header_container.setLayout(header_layout)

        # distribuicao do layout
        main_layout.insertWidget(0, self.header_container)
        main_layout.addLayout(self.grid)
        main_layout.addWidget(self.kombi_view)
        main_layout.addWidget(self.credits_view)
        main_layout.addWidget(self.graph_view)

        # timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

        self.last_states = {}
        self.last_log_time = 0

        self.blink_state = True
        self.current_page = "sensors"
        self.showFullScreen()

    def log_sensors(self, data):
        import os
        from datetime import datetime

        filename = "sensors_log.csv"

        # verifica se arquivo existe
        file_exists = os.path.isfile(filename)

        with open(filename, "a") as f:
            # cria header na primeira vez
            if not file_exists:
                header = "timestamp," + ",".join(data.keys()) + "\n"
                f.write(header)

            # escreve linha
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            values = ",".join(str(v) for v in data.values())

            f.write(f"{now},{values}\n")

    def log_event(self, message):
        from datetime import datetime

        now = datetime.now().strftime("%H:%M:%S")

        line = f"{now} - {message}\n"

        with open("darlene.log", "a") as f:
            f.write(line)

    def next_page(self):
        idx = self.pages.index(self.current_page)
        idx = (idx + 1) % len(self.pages)
        self.current_page = self.pages[idx]

    def prev_page(self):
        idx = self.pages.index(self.current_page)
        idx = (idx - 1) % len(self.pages)
        self.current_page = self.pages[idx]

    def update_cursor(self):
        if self.cursor_visible:
            self.header_title.setText(self.base_title + "_")
        else:
            self.header_title.setText(self.base_title + " ")

        self.cursor_visible = not self.cursor_visible

    def update_code_display(self):
        if self.command_mode:
            masked = self.input_buffer + "_" * (4 - len(self.input_buffer))
            self.code_popup.setText(f"[*{masked}]")

            # 🔥 garante posição correta
            self.code_popup.move(
                (self.width() - self.code_popup.width()) // 2,
                (self.height() - self.code_popup.height()) // 2
            )

            self.code_popup.raise_()  # 🔥 traz pra frente
            self.code_popup.show()

        else:
            self.code_popup.hide()


    def update_data(self):
        now = datetime.now().strftime("%H:%M")
        self.header_time.setText(now)
        sensor_data = {}

        if self.current_page == "sensors":
            self.base_title = "> DARLENE OS:~$ SENSORES"

        elif self.current_page == "status":
            self.base_title = "> DARLENE OS:~$ PORTAS"

        elif self.current_page == "doors":
            self.base_title = "> DARLENE OS:~$ PORTAS - IMG"

        elif self.current_page == "graphs":
            self.base_title = "> DARLENE OS:~$ GRÁFICOS"

        elif self.current_page == "credits":
            self.base_title = "> DARLENE OS:~$ SOBRE"


        self.blink_state = not self.blink_state

        self.hide_all()
        from sensors.gpio_sensors import read_doors

        if self.current_page == "sensors":
            devices = self.numeric_devices + self.digital_devices

            for card, device in zip(self.cards, devices):

                card.setVisible(True)
                card.title.setText(device["name"])

                if (device["name"] == "> BATERIA 1"):
                    value = 12.5
                    unit = device.get("unit", "")
                    sensor_data["bateria1"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 14:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                    elif value > 11.5:
                        card.set_color("#468a1a")
                    else:
                        card.set_color("#ffaa00")
                if (device["name"] == "> BATERIA 2") :
                    value = 12.5
                    unit = device.get("unit", "")
                    sensor_data["bateria2"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 14:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                    elif value > 11.5:
                        card.set_color("#468a1a")
                    else:
                        card.set_color("#ffaa00")
                elif device["name"] == "> TEMP MOTOR":
                    value = 102
                    unit = device.get("unit", "")
                    sensor_data["temp_motor"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 100:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                    elif value > 95:
                        card.set_color("#ffaa00")
                    else:
                        card.set_color("#468a1a")
                elif device["name"] == "> ÁGUA LIMPA":
                    value = 80
                    unit = device.get("unit", "")
                    sensor_data["agua_limpa"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 70:
                        card.set_color("#468a1a")
                    elif value > 30:
                        card.set_color("#ffaa00")
                    else:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                elif device["name"] == "> ÁGUA SUJA":
                    value = 32
                    unit = device.get("unit", "")
                    sensor_data["agua_suja"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 70:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                    elif value > 30:
                        card.set_color("#ffaa00")
                    else:
                        card.set_color("#468a1a")
                elif device["name"] == "> INVERSOR":
                    state = False
                    sensor_data["inversor"] = state
                    card.value.setText("-> ON" if state else "-> OFF")
                    card.set_color("#468a1a" if state else "#ff3333")
                elif device["name"] == "> SOLAR":
                    value = 10
                    unit = device.get("unit", "")
                    sensor_data["solar"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 10:
                        card.set_color("#468a1a")
                    elif value > 5:
                        card.set_color("#ffaa00")
                    else:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                elif device["name"] == "> CONSUMO":
                    value = 30
                    unit = device.get("unit", "")
                    sensor_data["consumo"] = value
                    card.value.setText(f"-> {value} {unit}")
                    if value > 60:
                        color = "#ff3333" if self.blink_state else "#440000"
                        card.set_color(color)
                    elif value > 50:
                        card.set_color("#ffaa00")
                    else:
                        card.set_color("#468a1a")
                elif device["name"] == "> BOMBA ÁGUA":
                    state = True
                    sensor_data["bomba_agua"] = state
                    card.value.setText("-> ON" if state else "-> OFF")
                    card.set_color("#468a1a" if state else "#ff3333")

            current_time = time.time()

            if current_time - self.last_log_time >= 60:
                self.log_sensors(sensor_data)
                self.last_log_time = current_time

        elif self.current_page == "status":
            door_states = read_doors(self.door_devices)

            for card, device in zip(self.cards, self.door_devices):

                card.setVisible(True)

                name = device["name"]
                card.title.setText(name)

                state = door_states[name]

                last_state = self.last_states.get(name)

                if last_state is None:
                    self.last_states[name] = state
                    continue

                if state != last_state:
                    if state:
                        self.log_event(f"PORTA {name} ABERTA (GPIO {device['pin']})")
                    else:
                        self.log_event(f"PORTA {name} FECHADA (GPIO {device['pin']})")

                    self.last_states[name] = state

                if state:
                    card.value.setText("-> ABERTA")
                    card.set_color("#ff3333")
                else:
                    card.value.setText("-> FECHADA")
                    card.set_color("#468a1a")

        elif self.current_page == "doors":
            door_states = read_doors(self.door_devices)
            self.kombi_view.update_data(self.door_devices, door_states)
            self.kombi_view.setVisible(True)

        elif self.current_page == "graphs":
            self.graph_view.update_plot()
            self.graph_view.setVisible(True)

        elif self.current_page == "credits":
            self.credits_view.setVisible(True)

    def resizeEvent(self, event):
        self.code_popup.move(
            (self.width() - self.code_popup.width()) // 2,
            (self.height() - self.code_popup.height()) // 2
        )


    def show_all(self):
        self.battery_card.setVisible(True)
        self.water_card.setVisible(True)
        self.temp_card.setVisible(True)

    def hide_all(self):
        for card in self.cards:
            card.setVisible(False)

        self.kombi_view.setVisible(False)
        self.credits_view.setVisible(False)
        self.graph_view.setVisible(False)

    def toggle_menu(self):
        self.menu.setVisible(not self.menu.isVisible())

    def request_exit(self):
        print("Digite 1234 para sair")

    def handle_code(self, code):
        if code == EXIT_CODE:
            self.close()

        elif code == "0000":
            self.current_page = "sensors"

        elif code == "2222":
            self.current_page = "status"

        elif code == "3333":
            self.current_page = "doors"

        elif code == "4444":
            self.current_page = "credits"

    def keyPressEvent(self, event):
        key = event.text()

        # ---- modo código (começou com *) ----
        if self.command_mode:
            if key.isdigit():
                self.input_buffer += key
                self.update_code_display()
                print(f"Código: {self.input_buffer}")

                if len(self.input_buffer) == 4:
                    if self.input_buffer == EXIT_CODE:
                        self.close()
                    else:
                        print("Código inválido")

                    self.input_buffer = ""
                    self.command_mode = False
                    self.update_code_display()

            return

        # ---- ativar modo código ----
        if key == "*":
            self.command_mode = True
            self.input_buffer = ""
            self.update_code_display()
            print("Modo código ativado")
            return

        # ---- navegação direta ----
        if key == "1":
            self.current_page = "sensors"

        elif key == "2":
            self.current_page = "status"

        elif key == "3":
            self.current_page = "doors"

        elif key == "4":
            self.current_page = "graphs"

        elif key == "5":
            self.current_page = "credits"

        self.input_buffer = ""
        self.command_mode = False
        self.update_code_display()

    def mousePressEvent(self, event):
        self.setFocus()

class KombiWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.pixmap = QPixmap("img/kombi.png")
        self.doors_config = []
        self.status = {}

        self.blink_state = True

    def update_data(self, doors_config, door_states):
        self.doors_config = doors_config
        self.status = door_states
        self.blink_state = not self.blink_state
        self.repaint()

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.drawPixmap(self.rect(), self.pixmap)

        w = self.width()
        h = self.height()

        for door in self.doors_config:
            name = door["name"]
            px, py = door["pos"]

            x = int(px * w)
            y = int(py * h)

            state = self.status.get(name, False)

            if state:  # aberto
                color = "#ff3333" if self.blink_state else "#440000"
            else:
                color = "#468a1a"

            # borda preta
            pen = QPen(QColor("#000000"))
            pen.setWidth(2)
            painter.setPen(pen)

            painter.setBrush(QColor(color))
            painter.drawEllipse(x, y, 30, 30)

class CreditsWidget(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout()

        self.image = QLabel()
        pixmap = QPixmap("img/credits.png")
        self.image.setPixmap(pixmap.scaled(300, 200))
        self.image.setStyleSheet("""
            border: 0px solid #00ffcc;
            border-radius: 0px;
        """)

        self.text = QLabel("Darlene OS v1.0\nby Alexandre Mascarenhas")
        self.text.setStyleSheet("font-size: 30px;border:0px;color:#468a1a")

        layout.addWidget(self.image)
        layout.addWidget(self.text)

        self.setLayout(layout)

class GraphWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.selected_sensor = "bateria1"

        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.last_update = 0

        # botões
        self.btn_layout = QHBoxLayout()

        self.buttons = {}

        self.sensor_groups = {
            "baterias": {
                "label": "BATERIAS",
                "keys": ["bateria1", "bateria2"]
            },
            "agua": {
                "label": "AGUA",
                "keys": ["agua_limpa", "agua_suja"]
            },
            "temp": {
                "label": "TEMP",
                "keys": ["temp_motor"]
            },
            "consumo": {
                "label": "CONSUMO",
                "keys": ["consumo"]
            }
        }

        for group_key, group in self.sensor_groups.items():
            btn = QPushButton(group["label"])
            btn.setFixedHeight(35)

            btn.clicked.connect(lambda _, k=group_key: self.select_sensor(k))
            btn.setStyleSheet("""
                background-color: #111;
                color: #ffaa00;
                border: 2px solid black;
                font-size: 18px;
            }

            QPushButton:pressed {
                color: #00ffcc;
            }
            """)
            self.buttons[group_key] = btn
            self.btn_layout.addWidget(btn)

        # layout geral
        layout = QVBoxLayout()
        layout.addLayout(self.btn_layout)
        layout.addWidget(self.canvas)

        self.setLayout(layout)

    def select_sensor(self, group_key):
        self.selected_sensor = group_key
        self.update_plot()

    def update_plot(self):
        #if time.time() - self.last_update < 5:
            #return

        #self.last_update = time.time()

        try:
            df = pd.read_csv("sensors_log.csv")
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            #df = df.tail(50)

            self.figure.clear()
            ax = self.figure.add_subplot(111)
            

            group = self.sensor_groups[self.selected_sensor]

            colors = ["#00ffcc", "#ffaa00"]

            if self.selected_sensor == "temp":
                ax.axhline(y=100, color="red", linestyle="--")

            last_value = None        

            for i, key in enumerate(group["keys"]):
                if key in df.columns:
                    last_value = df[key].iloc[-1]
                    ax.plot(df["timestamp"], df[key],
                            label=f"{key.upper()} ({last_value})",
                            color=colors[i % len(colors)])
                    ax.scatter(df["timestamp"].iloc[-1],
                        df[key].iloc[-1],
                        color="#ffffff",
                        zorder=5)

            
            ax.set_title(
                group["label"],
                color="#b0b0b0",
                fontsize=12
            )
            
            ax.legend()
            ax.tick_params(axis='x', colors="#00ffcc")
            ax.tick_params(axis='y', colors="#00ffcc")
            ax.tick_params(axis='x', rotation=45)

            # estilo
            ax.grid(True)
            ax.set_facecolor("#1c1c1c")
            self.figure.set_facecolor("#1c1c1c")
            ax.tick_params(colors="#00ffcc")
            ax.spines[:].set_color("#00ffcc")
            for spine in ax.spines.values():
                spine.set_color("#00ffcc")

            self.figure.tight_layout()
            self.figure.subplots_adjust(bottom=0.25)

            self.canvas.setMinimumHeight(200)
            self.canvas.setMaximumHeight(300)
            self.canvas.draw()

        except Exception as e:
            print("Erro gráfico:", e)

app = QApplication([])

def start_dashboard():
    global window
    window = Dashboard()
    window.show()

boot = BootScreen(start_dashboard)

app.exec()
