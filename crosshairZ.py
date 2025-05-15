import sys
import json
import os
import threading
import keyboard
import ctypes
from PyQt5 import QtWidgets, QtGui, QtCore
SETTINGS_FILE = "settings.json"

print("Program starting...")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            data["x"] = int(data.get("x") or 0)
            data["y"] = int(data.get("y") or 0)
            return data
    return {
        "size": 40,
        "crosshair": "crosshair.png",
        "x": 0,
        "y": 0
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings, crosshair, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self.crosshair = crosshair

        layout = QtWidgets.QFormLayout(self)

        self.sizeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sizeSlider.setRange(10, 400)
        self.sizeSlider.setValue(settings["size"])
        self.sizeSlider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sizeLabel = QtWidgets.QLabel(str(settings["size"]))
        sizeLayout = QtWidgets.QHBoxLayout()
        sizeLayout.addWidget(self.sizeSlider)
        sizeLayout.addWidget(self.sizeLabel)
        layout.addRow("Crosshair Size:", sizeLayout)

        self.sizeSlider.valueChanged.connect(self.update_size)
        self.sizeSlider.installEventFilter(self)
        self.installEventFilter(self)

        btnBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(btnBox)
        for btn in btnBox.buttons():
            btn.setFocusPolicy(QtCore.Qt.NoFocus)

        self.setLayout(layout)
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            # Move crosshair with arrow keys
            step = 1  # Pixel sensitivity
            if event.key() == QtCore.Qt.Key_Left:
                self.crosshair.move_crosshair(-step, 0)
                return True
            elif event.key() == QtCore.Qt.Key_Right:
                self.crosshair.move_crosshair(step, 0)
                return True
            elif event.key() == QtCore.Qt.Key_Up:
                self.crosshair.move_crosshair(0, -step)
                return True
            elif event.key() == QtCore.Qt.Key_Down:
                self.crosshair.move_crosshair(0, step)
                return True
        return super().eventFilter(obj, event)

    def update_size(self, value):
        self.sizeLabel.setText(str(value))
        self.crosshair.settings["size"] = value
        save_settings(self.crosshair.settings)
        self.crosshair.load_crosshair()
        self.crosshair.follow_mouse()

    def get_settings(self):
        return {
            "size": int(self.sizeSlider.value())
        }

class Crosshair(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.settings = load_settings()
        self.setWindowFlags(
            QtCore.Qt.FramelessWindowHint |
            QtCore.Qt.WindowStaysOnTopHint |
            QtCore.Qt.Tool
        )
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents)
        self.make_clickthrough()
        self.load_crosshair()
        self.resize(self.crosshair.size())
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.follow_mouse)
        self.timer.start(30)
        self.installEventFilter(self)

    def make_clickthrough(self):
        hwnd = int(self.winId())
        extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style | 0x80000 | 0x20)

    def load_crosshair(self):
        try:
            crosshair_path = self.settings.get("crosshair", "crosshair.png")
            size = int(self.settings.get("size", 40))
            if os.path.exists(crosshair_path):
                pixmap = QtGui.QPixmap(crosshair_path)
                if pixmap.isNull():
                    pixmap = self.draw_default_crosshair(size)
            else:
                pixmap = self.draw_default_crosshair(size)
            self.crosshair = pixmap.scaled(
                size, size,
                QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation
            )
            # Check pixmap size
            w, h = self.crosshair.width(), self.crosshair.height()
            if w > 0 and h > 0:
                self.resize(w, h)
            else:
                print("Invalid pixmap size:", w, h)
        except Exception as e:
            print("load_crosshair error:", e)
            self.crosshair = self.draw_default_crosshair(40)
            self.resize(40, 40)

    def draw_default_crosshair(self, size):
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        pen = QtGui.QPen(QtCore.Qt.red, 2)
        painter.setPen(pen)
        painter.drawLine(size//2, 0, size//2, size)
        painter.drawLine(0, size//2, size, size//2)
        painter.end()
        return pixmap

    def follow_mouse(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        x_offset = int(self.settings.get("x") or 0)
        y_offset = int(self.settings.get("y") or 0)
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            w, h = 40, 40  # Default value
        center_x = screen.center().x() - w // 2 + x_offset
        center_y = screen.center().y() - h // 2 + y_offset

        min_x = screen.left()
        max_x = screen.right() - w
        min_y = screen.top()
        max_y = screen.bottom() - h
        center_x = max(min_x, min(center_x, max_x))
        center_y = max(min_y, min(center_y, max_y))

        self.move(center_x, center_y)

    def move_crosshair(self, dx, dy):
        self.settings["x"] = int(self.settings.get("x", 0)) + dx
        self.settings["y"] = int(self.settings.get("y", 0)) + dy
        save_settings(self.settings)
        self.follow_mouse()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.crosshair)

    @QtCore.pyqtSlot()
    def open_settings(self):
        print("Settings window opened")
        # Backup current settings before opening settings
        old_settings = self.settings.copy()
        dialog = SettingsDialog(self.settings, self, None)
        dialog.setWindowFlags(QtCore.Qt.Window)
        result = dialog.exec_()
        if result:
            print("Saving settings:", dialog.get_settings())
            self.settings.update(dialog.get_settings())
            save_settings(self.settings)
            self.load_crosshair()
            print("Settings loaded")
        else:
            # If Cancel pressed, restore old settings
            self.settings = old_settings
            save_settings(self.settings)
            self.load_crosshair()
            self.follow_mouse()

    def closeEvent(self, event):
        print("Crosshair tried to close the window!")
        event.ignore()  # Prevent closing

app = QtWidgets.QApplication(sys.argv)
w = Crosshair()
w.show()

def listen_f2():
    while True:
        keyboard.wait("f2")
        QtCore.QMetaObject.invokeMethod(w, "open_settings", QtCore.Qt.QueuedConnection)

listener = threading.Thread(target=listen_f2, daemon=True)
listener.start()

sys.exit(app.exec_())

print("Program ended.")
