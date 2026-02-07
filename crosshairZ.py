# Copyright © 2025 zinarr1

import sys
import json
import os
import threading
import keyboard
import ctypes
import time
from PyQt5 import QtWidgets, QtGui, QtCore
from datetime import time as datetime_time
from pynput.mouse import Listener
from pynput import mouse

SETTINGS_FILE = "settings.json"
PROFILES_FILE = "profiles.json"  # For profile support

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            data["x"] = int(data.get("x") or 0)
            data["y"] = int(data.get("y") or 0)
            if "hide_on_right_click" not in data:
                data["hide_on_right_click"] = True
            if "profile" not in data:
                data["profile"] = "Default"
            if "color" not in data:
                data["color"] = "#FF0000"  # Default red
            if "opacity" not in data:
                data["opacity"] = 1.0  # Default fully opaque
            if "use_color_overlay" not in data:
                data["use_color_overlay"] = True
            if "monitor_index" not in data:
                data["monitor_index"] = 0  # Default to first monitor
            if "follow_mouse" not in data:
                data["follow_mouse"] = False  # Default to not follow mouse
            if "timer_interval" not in data:
                data["timer_interval"] = 10  # Default timer interval
            return data
    return {
        "size": 40,
        "crosshair": "crosshair.png",
        "x": 0,
        "y": 0,
        "hide_on_right_click": True,
        "profile": "Default",
        "color": "#FF0000",        # Default red
        "opacity": 1.0,            # Default fully opaque
        "use_color_overlay": True,
        "monitor_index": 0,           # Default to first monitor
        "follow_mouse": False,         # Default to not follow mouse
        "timer_interval": 10          # Default timer interval
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)

def load_profiles():
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            return json.load(f)
    return {"Default": load_settings()}

def save_profiles(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=4)

class SettingsDialog(QtWidgets.QDialog):
    def __init__(self, settings, crosshair, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.settings = settings
        self.crosshair = crosshair
        self.old_settings = settings.copy()
        self.live_update_enabled = False

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

        layout = QtWidgets.QFormLayout(self)

        # Crosshair size slider
        self.sizeSlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.sizeSlider.setRange(10, 400)
        self.sizeSlider.setValue(settings["size"])
        self.sizeSlider.setFocusPolicy(QtCore.Qt.NoFocus)
        self.sizeLabel = QtWidgets.QLabel(str(settings["size"]))
        sizeLayout = QtWidgets.QHBoxLayout()
        sizeLayout.addWidget(self.sizeSlider)
        sizeLayout.addWidget(self.sizeLabel)
        layout.addRow("Crosshair Size:", sizeLayout)

        # Step size spinbox
        self.stepSpinBox = QtWidgets.QDoubleSpinBox()
        self.stepSpinBox.setRange(0.1, 10.0)
        self.stepSpinBox.setSingleStep(0.1)
        self.stepSpinBox.setValue(settings.get("step", 0.1))
        layout.addRow("Step Size:", self.stepSpinBox)

        # Hide on right click checkbox
        self.hideRightClickCheck = QtWidgets.QCheckBox("Hide on right click")
        self.hideRightClickCheck.setChecked(settings.get("hide_on_right_click", True))
        layout.addRow(self.hideRightClickCheck)

        # Use color overlay checkbox
        self.useColorOverlayCheck = QtWidgets.QCheckBox("Use color overlay for PNG")
        self.useColorOverlayCheck.setChecked(settings.get("use_color_overlay", True))
        layout.addRow(self.useColorOverlayCheck)

        # Profile selection
        self.profiles = load_profiles()
        self.profileCombo = QtWidgets.QComboBox()
        self.profileCombo.addItems(self.profiles.keys())
        self.profileCombo.setCurrentText(settings.get("profile", "Default"))
        layout.addRow("Profile:", self.profileCombo)

        self.saveProfileBtn = QtWidgets.QPushButton("Save as Profile")
        layout.addRow(self.saveProfileBtn)
        self.saveProfileBtn.clicked.connect(self.save_profile)

        self.deleteProfileBtn = QtWidgets.QPushButton("Delete Profile")
        layout.addRow(self.deleteProfileBtn)
        self.deleteProfileBtn.clicked.connect(self.delete_profile)

        # Select PNG button
        self.pngPath = settings.get("crosshair", "crosshair.png")
        self.pngLabel = QtWidgets.QLabel(os.path.basename(self.pngPath))
        self.selectPngBtn = QtWidgets.QPushButton("Select PNG")
        self.selectPngBtn.clicked.connect(self.select_png)
        pngLayout = QtWidgets.QHBoxLayout()
        pngLayout.addWidget(self.selectPngBtn)
        pngLayout.addWidget(self.pngLabel)
        layout.addRow("Crosshair PNG:", pngLayout)

        # Color picker
        self.colorBtn = QtWidgets.QPushButton()
        self.colorBtn.setStyleSheet(f"background-color: {settings.get('color', '#FF0000')}")
        self.colorBtn.clicked.connect(self.pick_color)
        layout.addRow("Crosshair Color:", self.colorBtn)

        # Monitor selection
        self.monitorCombo = QtWidgets.QComboBox()
        screens = QtWidgets.QApplication.screens()
        for i, screen in enumerate(screens):
            self.monitorCombo.addItem(f"Monitor {i+1}")
        self.monitorCombo.setCurrentIndex(settings.get("monitor_index", 0))
        layout.addRow("Monitor:", self.monitorCombo)

        # Opacity slider
        self.opacitySlider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacitySlider.setRange(10, 100)
        self.opacitySlider.setValue(int(settings.get("opacity", 1.0) * 100))
        self.opacityLabel = QtWidgets.QLabel(str(self.opacitySlider.value()))
        opacityLayout = QtWidgets.QHBoxLayout()
        opacityLayout.addWidget(self.opacitySlider)
        opacityLayout.addWidget(self.opacityLabel)
        layout.addRow("Opacity:", opacityLayout)
        self.opacitySlider.valueChanged.connect(lambda v: self.opacityLabel.setText(str(v)))

        # Takip hızı spinbox
        self.timerSpinBox = QtWidgets.QSpinBox()
        self.timerSpinBox.setRange(1, 100)
        self.timerSpinBox.setValue(settings.get("timer_interval", 10))
        layout.addRow("Follow time (ms):", self.timerSpinBox)

        self.offsetBtn = QtWidgets.QPushButton("Set Crosshair Position")
        self.offsetBtn.clicked.connect(self.open_offset_dialog)
        layout.addRow(self.offsetBtn)

        self.sizeSlider.valueChanged.connect(self.live_update)
        self.stepSpinBox.valueChanged.connect(self.live_update)
        self.hideRightClickCheck.stateChanged.connect(self.live_update)
        self.useColorOverlayCheck.stateChanged.connect(self.live_update)
        self.profileCombo.currentTextChanged.connect(self.change_profile)
        self.colorBtn.clicked.connect(self.live_update)
        self.opacitySlider.valueChanged.connect(self.live_update)
        self.monitorCombo.currentIndexChanged.connect(self.live_update)
        self.selectPngBtn.clicked.connect(self.live_update)
        self.timerSpinBox.valueChanged.connect(self.live_update)

        self.sizeSlider.valueChanged.connect(lambda v: self.sizeLabel.setText(str(v)))
        self.sizeSlider.installEventFilter(self)
        self.installEventFilter(self)

        btnBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        layout.addWidget(btnBox)
        for btn in btnBox.buttons():
            btn.setFocusPolicy(QtCore.Qt.NoFocus)

        # Exit button
        self.exitBtn = QtWidgets.QPushButton("Exit")
        layout.addWidget(self.exitBtn)
        self.exitBtn.clicked.connect(self.exit_app)

        self.setLayout(layout)
        btnBox.accepted.connect(self.accept)
        btnBox.rejected.connect(self.reject)

        for widget in self.findChildren(QtWidgets.QWidget):
            widget.installEventFilter(self)
        self.installEventFilter(self)

        self.setFocus(QtCore.Qt.OtherFocusReason)

        self.live_update_enabled = True

        self.followMouseCheck = QtWidgets.QCheckBox("Pin crosshair to mouse")
        self.followMouseCheck.setChecked(settings.get("follow_mouse", False))
        layout.addRow(self.followMouseCheck)
        self.followMouseCheck.stateChanged.connect(self.live_update)

    def select_png(self):
        fname, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select PNG", "", "PNG Files (*.png)")
        if fname:
            self.pngPath = fname
            self.pngLabel.setText(os.path.basename(fname))
            self.settings["crosshair"] = fname
            self.live_update()

    def live_update(self, *args):
        if not getattr(self, "live_update_enabled", True):
            return
        self.settings["size"] = int(self.sizeSlider.value())
        self.settings["step"] = self.stepSpinBox.value()
        self.settings["hide_on_right_click"] = self.hideRightClickCheck.isChecked()
        self.settings["use_color_overlay"] = self.useColorOverlayCheck.isChecked()
        self.settings["profile"] = self.profileCombo.currentText()
        self.settings["color"] = self.colorBtn.palette().button().color().name()
        self.settings["opacity"] = self.opacitySlider.value() / 100.0
        self.settings["crosshair"] = self.pngPath
        self.settings["monitor_index"] = self.monitorCombo.currentIndex()
        self.settings["follow_mouse"] = self.followMouseCheck.isChecked()
        self.settings["timer_interval"] = self.timerSpinBox.value()
        self.crosshair.settings.update(self.settings)
        self.crosshair.load_crosshair()
        self.crosshair.follow_mouse()
        self.crosshair.update()
        self.crosshair.set_timer_interval(self.settings["timer_interval"])
        save_settings(self.settings)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress and self.followMouseCheck.isChecked():
            if event.key() in (QtCore.Qt.Key_Left, QtCore.Qt.Key_Right, QtCore.Qt.Key_Up, QtCore.Qt.Key_Down):
                step = self.settings.get("step", 0.1)
                if event.key() == QtCore.Qt.Key_Left:
                    self.crosshair.move_crosshair(-step, 0)
                elif event.key() == QtCore.Qt.Key_Right:
                    self.crosshair.move_crosshair(step, 0)
                elif event.key() == QtCore.Qt.Key_Up:
                    self.crosshair.move_crosshair(0, -step)
                elif event.key() == QtCore.Qt.Key_Down:
                    self.crosshair.move_crosshair(0, step)
                event.accept()
                return True
        return False

    def update_size(self, value):
        self.sizeLabel.setText(str(value))
        self.crosshair.settings["size"] = value
        save_settings(self.crosshair.settings)
        self.crosshair.load_crosshair()
        self.crosshair.follow_mouse()

    def pick_color(self):
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self.settings.get("color", "#FF0000")), self)
        if color.isValid():
            self.colorBtn.setStyleSheet(f"background-color: {color.name()}")
            self.settings["color"] = color.name()
            self.live_update()

    def get_settings(self):
        return {
            **self.settings,
            "size": int(self.sizeSlider.value()),
            "step": self.stepSpinBox.value(),
            "hide_on_right_click": self.hideRightClickCheck.isChecked(),
        }

    def change_profile(self, profile_name):
        if profile_name in self.profiles:
            prof = self.profiles[profile_name]
            self.sizeSlider.setValue(prof.get("size", 40))
            self.hideRightClickCheck.setChecked(prof.get("hide_on_right_click", True))
            self.useColorOverlayCheck.setChecked(prof.get("use_color_overlay", True))
            self.colorBtn.setStyleSheet(f"background-color: {prof.get('color', '#FF0000')}")
            self.opacitySlider.setValue(int(prof.get("opacity", 1.0) * 100))
            self.pngPath = prof.get("crosshair", "crosshair.png")
            self.pngLabel.setText(os.path.basename(self.pngPath))
            self.monitorCombo.setCurrentIndex(prof.get("monitor_index", 0))
            self.settings.update(prof)
            self.live_update()

    def save_profile(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save Profile", "Profile name:")
        if ok and name:
            self.profiles[name] = self.get_settings()
            save_profiles(self.profiles)
            if self.profileCombo.findText(name) == -1:
                self.profileCombo.addItem(name)
            self.profileCombo.setCurrentText(name)

    def delete_profile(self):
        name = self.profileCombo.currentText()
        if name == "Default":
            QtWidgets.QMessageBox.warning(self, "Warning", "Default profile cannot be deleted.")
            return
        reply = QtWidgets.QMessageBox.question(self, "Delete Profile", f"Delete profile '{name}'?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            self.profiles.pop(name, None)
            save_profiles(self.profiles)
            self.profileCombo.removeItem(self.profileCombo.currentIndex())
            self.profileCombo.setCurrentText("Default")
            self.change_profile("Default")

    def open_offset_dialog(self):
        dlg = OffsetAdjustDialog(
            self.settings.get("x", 0),
            self.settings.get("y", 0),
            self.followMouseCheck.isChecked(),
            self.crosshair,
            self,
        )
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            x, y = dlg.get_offsets()
            self.settings["x"] = float(x)
            self.settings["y"] = float(y)
            self.live_update()

    def reject(self):
        self.settings.clear()
        self.settings.update(self.old_settings)
        self.crosshair.settings.clear()
        self.crosshair.settings.update(self.old_settings)
        self.crosshair.load_crosshair()
        self.crosshair.follow_mouse()
        self.crosshair.update()
        super().reject()

    def exit_app(self):
        QtWidgets.QApplication.quit()

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
        self.timer.start(self.settings.get("timer_interval", 10))  # Default 10 ms
        self.installEventFilter(self)
        self.visible_state = True
        self.settings_open = False

        # Start mouse listener only here
        self.mouse_listener = mouse.Listener(on_click=self.on_click)
        self.mouse_listener.daemon = True
        self.mouse_listener.start()

        self.start_hotkey_threads()
        self.create_tray_icon()

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.right and self.settings.get("hide_on_right_click", True):
            if pressed:
                QtCore.QMetaObject.invokeMethod(self, "hide_crosshair_temp", QtCore.Qt.QueuedConnection)
            else:
                QtCore.QMetaObject.invokeMethod(self, "show_crosshair_temp", QtCore.Qt.QueuedConnection)

    @QtCore.pyqtSlot()
    def hide_crosshair_temp(self):
        if self.isVisible() and self.visible_state:
            self.hide()

    @QtCore.pyqtSlot()
    def show_crosshair_temp(self):
        if not self.isVisible() and self.visible_state:
            self.show()

    def make_clickthrough(self):
        hwnd = int(self.winId())
        extended_style = ctypes.windll.user32.GetWindowLongW(hwnd, -20)
        ctypes.windll.user32.SetWindowLongW(hwnd, -20, extended_style | 0x80000 | 0x20)

    def load_crosshair(self):
        try:
            crosshair_path = self.settings.get("crosshair", "crosshair.png")
            size = int(self.settings.get("size", 40))
            color = QtGui.QColor(self.settings.get("color", "#FF0000"))
            opacity = float(self.settings.get("opacity", 1.0))
            use_overlay = self.settings.get("use_color_overlay", True)
            if os.path.exists(crosshair_path):
                pixmap = QtGui.QPixmap(crosshair_path)
                if pixmap.isNull():
                    pixmap = self.draw_default_crosshair(size, color)
                else:
                    if use_overlay:
                        image = pixmap.toImage().convertToFormat(QtGui.QImage.Format_ARGB32)
                        for y in range(image.height()):
                            for x in range(image.width()):
                                pixel = image.pixelColor(x, y)
                                alpha = pixel.alpha()
                                if alpha > 0:
                                    image.setPixelColor(x, y, QtGui.QColor(color.red(), color.green(), color.blue(), alpha))
                        pixmap = QtGui.QPixmap.fromImage(image)
            else:
                pixmap = self.draw_default_crosshair(size, color)
            pixmap = pixmap.scaled(size, size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            if opacity < 1.0:
                temp = QtGui.QPixmap(pixmap.size())
                temp.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(temp)
                painter.setOpacity(opacity)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                pixmap = temp
            self.crosshair = pixmap
            pixmap = self.crosshair
            w, h = pixmap.width(), pixmap.height()
            if w > 0 and h > 0:
                self.resize(w, h)
            else:
                print("Invalid pixmap size:", w, h)
        except Exception as e:
            print("load_crosshair error:", e)
            self.crosshair = self.draw_default_crosshair(40, QtGui.QColor("#FF0000"))
            self.resize(40, 40)

    def draw_default_crosshair(self, size, color):
        pixmap = QtGui.QPixmap(size, size)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        pen = QtGui.QPen(color, 2)
        painter.setPen(pen)
        painter.drawLine(size//2, 0, size//2, size)
        painter.drawLine(0, size//2, size, size//2)
        painter.end()
        return pixmap

    def follow_mouse(self):
        if self.settings.get("follow_mouse", False):
            pos = QtGui.QCursor.pos()
            x_offset = self.settings.get("x", 0)
            y_offset = self.settings.get("y", 0)
            w = self.width()
            h = self.height()
            self.move(
                int(pos.x() + x_offset - w / 2),
                int(pos.y() + y_offset - h / 2)
            )
            return
        screens = QtWidgets.QApplication.screens()
        monitor_index = self.settings.get("monitor_index", 0)
        if monitor_index >= len(screens):
            monitor_index = 0
        screen = screens[monitor_index].geometry()
        x_offset = int(self.settings.get("x") or 0)
        y_offset = int(self.settings.get("y") or 0)
        w, h = self.width(), self.height()
        if w <= 0 or h <= 0:
            w, h = 40, 40
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
        self.settings["x"] = self.settings.get("x", 0) + dx
        self.settings["y"] = self.settings.get("y", 0) + dy
        save_settings(self.settings)
        self.follow_mouse()

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.drawPixmap(0, 0, self.crosshair)

    @QtCore.pyqtSlot()
    def open_settings(self):
        if self.settings_open:
            return  # Prevent opening multiple dialogs
        self.settings_open = True
        old_settings = self.settings.copy()
        dialog = SettingsDialog(self.settings, self, None)
        dialog.setWindowFlags(QtCore.Qt.Window)
        result = dialog.exec_()
        self.settings_open = False  # Reset flag when dialog closes
        if result:
            self.settings.update(dialog.get_settings())
            save_settings(self.settings)
            self.load_crosshair()
        else:
            self.settings = old_settings
            save_settings(self.settings)
            self.load_crosshair()
            self.follow_mouse()

    def closeEvent(self, event):
        event.ignore()

    def create_tray_icon(self):
        self.tray = QtWidgets.QSystemTrayIcon(self)
        self.tray.setIcon(QtGui.QIcon("crosshair.ico"))
        self.tray.setVisible(True)

        menu = QtWidgets.QMenu()
        show_action = menu.addAction("Show/Hide Crosshair")
        show_action.triggered.connect(self.toggle_visibility)
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(QtWidgets.QApplication.quit)
        self.tray.setContextMenu(menu)

    def start_hotkey_threads(self):
        def listen_f2():
            while True:
                keyboard.wait("f2")
                QtCore.QMetaObject.invokeMethod(self, "open_settings", QtCore.Qt.QueuedConnection)

        def listen_f3():
            while True:
                keyboard.wait("f3")
                QtCore.QMetaObject.invokeMethod(self, "toggle_visibility", QtCore.Qt.QueuedConnection)

        threading.Thread(target=listen_f2, daemon=True).start()
        threading.Thread(target=listen_f3, daemon=True).start()

    @QtCore.pyqtSlot()
    def toggle_visibility(self):
        if self.visible_state:
            self.hide()
        else:
            self.show()
        self.visible_state = not self.visible_state

    def set_timer_interval(self, interval):
        self.timer.setInterval(interval)

class CrosshairDrawDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Draw your crosshair")
        self.resize(200, 200)
        self.canvas = QtGui.QPixmap(200, 200)
        self.canvas.fill(QtCore.Qt.transparent)
        self.label = QtWidgets.QLabel()
        self.label.setPixmap(self.canvas)
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.label)
        self.last_point = None

    def mousePressEvent(self, event):
        self.last_point = event.pos()

    def mouseMoveEvent(self, event):
        if self.last_point:
            painter = QtGui.QPainter(self.canvas)
            pen = QtGui.QPen(QtCore.Qt.red, 3)
            painter.setPen(pen)
            painter.drawLine(self.last_point, event.pos())
            painter.end()
            self.label.setPixmap(self.canvas)
            self.last_point = event.pos()

    def mouseReleaseEvent(self, event):
        self.last_point = None

class OffsetAdjustDialog(QtWidgets.QDialog):
    def __init__(self, x, y, follow_mouse, crosshair, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set Position")
        self.setModal(True)
        self.crosshair = crosshair
        self.follow_mouse = follow_mouse
        self.x = float(x)
        self.y = float(y)
        self.init_ui()
        self.update_label()
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setFocus()

    def init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        if self.follow_mouse:
            msg = "To set the pinned position relative to the mouse, use the arrow keys. Hold Shift for 0.1 step."
        else:
            msg = "To set the fixed position, use the arrow keys. Hold Shift for 0.1 step."
        self.label = QtWidgets.QLabel(msg)
        self.offset_label = QtWidgets.QLabel()
        layout.addWidget(self.label)
        layout.addWidget(self.offset_label)
        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Save | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def keyPressEvent(self, event):
        if event.modifiers() & QtCore.Qt.ControlModifier:
            step = 1.0
        elif event.modifiers() & QtCore.Qt.ShiftModifier:
            step = 0.1
        else:
            step = 0.01
        if event.key() == QtCore.Qt.Key_Left:
            self.x -= step
        elif event.key() == QtCore.Qt.Key_Right:
            self.x += step
        elif event.key() == QtCore.Qt.Key_Up:
            self.y -= step
        elif event.key() == QtCore.Qt.Key_Down:
            self.y += step
        else:
            super().keyPressEvent(event)
            return
        self.update_label()
        # Live update crosshair position
        if self.follow_mouse:
            self.crosshair.settings["x"] = self.x
            self.crosshair.settings["y"] = self.y
            self.crosshair.follow_mouse()
        else:
            self.crosshair.settings["x"] = self.x
            self.crosshair.settings["y"] = self.y
            self.crosshair.load_crosshair()
            self.crosshair.update()

    def update_label(self):
        self.offset_label.setText(f"X: {self.x:.2f}  Y: {self.y:.2f}")

    def get_offsets(self):
        return self.x, self.y

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("crosshair.ico"))
    w = Crosshair()
    w.show()

    sys.exit(app.exec_())
