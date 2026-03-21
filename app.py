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
from datetime import datetime
import random


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
            font-size: 23px;
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
        #self.setStyleSheet("background-color: #0a0a0a;color: #00ffcc;")

        self.cursor_visible = True
        self.base_title = "SENSORES"
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self.update_cursor)
        self.cursor_timer.start(500)  # pisca a cada 0.5s

        main_layout = QVBoxLayout()
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

        main_layout.addWidget(self.kombi_view)
        main_layout.addWidget(self.credits_view)

        self.kombi_view.setVisible(False)
        self.credits_view.setVisible(False)

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
        self.showFullScreen()

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
            {"name": "> PASSAGEIRO", "pin": 18, "type": "door", "pos": (0.5, 0.73)},
            {"name": "> CASA", "pin": 19, "type": "door", "pos": (0.32, 0.75)},
            {"name": "> MALA", "pin": 20,  "type": "door", "pos": (0.84, 0.68)},
            {"name": "> MOTOR", "pin": 21,  "type": "door", "pos": (0.84, 0.82)},
            {"name": "> MOTORISTA", "pin": 17, "type": "door", "pos": (0.12, 0.19)},
            {"name": "> PASSAGEIRO", "pin": 18, "type": "door", "pos": (0.5, 0.73)},
            {"name": "> CASA", "pin": 19, "type": "door", "pos": (0.32, 0.75)},
            {"name": "> MALA", "pin": 20,  "type": "door", "pos": (0.84, 0.68)},
        ]

        self.numeric_devices = [d for d in self.devices_config if d["type"] == "numeric"]
        self.digital_devices = [d for d in self.devices_config if d["type"] == "digital"]
        self.door_devices = [d for d in self.devices_config if d["type"] == "door"]

        from sensors.gpio_sensors import setup_doors
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
        self.header_container.setFixedHeight(40)  # 🔥 altura fixa

        self.header_container.setStyleSheet("""
            background-color: #111;
            border: 2px solid green;
            font-family: monospace;
        """)

        # título
        self.header_title = QLabel("@DARLENE OS:~$ ")
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
        #self.header_icon = QLabel("⚡")
        #self.header_icon.setStyleSheet("font-size: 16px; color: #ffaa00;")
        #header_layout.addStretch()
        #header_layout.addWidget(self.header_icon)
        #header_layout.addStretch()
        header_layout.addWidget(self.header_title)
        header_layout.addStretch()
        header_layout.addWidget(self.header_time)

        self.header_container.setLayout(header_layout)

        # adicionar no topo
        main_layout.insertWidget(0, self.header_container)


        main_layout.addLayout(self.grid)
       # self.setLayout(main_layout)

        # timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)

        self.blink_state = True

        self.current_page = "sensors"

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

        if self.current_page == "sensors":
            self.base_title = "> DARLENE OS:~$ SENSORES"

        elif self.current_page == "status":
            self.base_title = "> DARLENE OS:~$ PORTAS"

        elif self.current_page == "doors":
            self.base_title = "> DARLENE OS:~$ PORTAS - IMG"

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

                if (device["name"] == "> BATERIA 1") or (device["name"] == "> BATERIA 2") :
                    value = 12.5
                    unit = device.get("unit", "")
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
                    card.value.setText("-> ON" if state else "-> OFF")
                    card.set_color("#468a1a" if state else "#ff3333")
                elif device["name"] == "> SOLAR":
                    value = 10
                    unit = device.get("unit", "")
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
                    card.value.setText("-> ON" if state else "-> OFF")
                    card.set_color("#468a1a" if state else "#ff3333")


        elif self.current_page == "status":
            door_states = read_doors(self.door_devices)

            for card, device in zip(self.cards, self.door_devices):

                card.setVisible(True)

                name = device["name"]
                card.title.setText(name)

                state = door_states[name]

                if state:
                    card.value.setText("- ABERTA")
                    card.set_color("#ff3333")
                else:
                    card.value.setText("- FECHADA")
                    card.set_color("#468a1a")

        elif self.current_page == "doors":
            door_states = read_doors(self.door_devices)
            self.kombi_view.update_data(self.door_devices, door_states)
            self.kombi_view.setVisible(True)


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


app = QApplication([])

def start_dashboard():
    global window
    window = Dashboard()
    window.show()

boot = BootScreen(start_dashboard)

app.exec()
