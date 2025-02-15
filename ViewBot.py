"""
ViewBot v2.1 2025
Author: @RanveerisdeGOAT,
Co-Authors: Deepseek, Gemini, ChatGPT ;)
Open source: Free to use, modify and improve: https://github.com/RanveerisdeGOAT?tab=repositories
(The EXE file may take some time to boot up)

REQUIREMENTS:
pip install subprocess, PyQt5, pillow, numpy, keyboard, google.generativeai
"""

__author__ = '@RanveerisdeGOAT'

import sys
import threading
import subprocess  # For launching external applications
import os  # For file operations
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QInputDialog, QPushButton
import tkinter as tk
from PIL import ImageGrab, Image
import numpy as np
import keyboard  # For global hotkey support
from io import BytesIO  # For converting QBuffer to a PIL-compatible format
import google.generativeai as genai
import re
import time


class SnippingTool(QtWidgets.QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window  # Reference to the main window
        root = tk.Tk()
        root.withdraw()  # Hide the Tkinter root window
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.setGeometry(0, 0, screen_width, screen_height)
        self.setWindowTitle(' ')
        self.begin = QtCore.QPoint()
        self.end = QtCore.QPoint()
        self.setWindowOpacity(0.3)

        # Set frameless and on-top
        self.setWindowFlags(QtCore.Qt.WindowType.FramelessWindowHint | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CursorShape.CrossCursor))

        print('Capture the screen...')

        # Create a button in the middle-top
        self.wholeScreenCaptureButton = QPushButton(self)
        self.wholeScreenCaptureButton.setStyleSheet("background-color: white; font-size: 14px; padding: 5px;")
        self.wholeScreenCaptureButton.clicked.connect(self.capture_whole_screen)

        try:
            self.wholeScreenCaptureButton.setIcon(QtGui.QIcon('resources/whole_screenshot.png'))
        except:
            try:
                self.wholeScreenCaptureButton.setIcon(resource_path(QtGui.QIcon('resources/whole_screenshot.png')))
            except:
                self.wholeScreenCaptureButton.setText('Screenshot')

        # Position the button at the middle-top
        button_width = 200
        button_height = 40
        self.wholeScreenCaptureButton.setGeometry(
            (screen_width // 2) - (button_width // 2), 10,  # Centered horizontally, 10px from top
            button_width, button_height
        )

        self.show()

    def paintEvent(self, event):
        qp = QtGui.QPainter(self)
        qp.setPen(QtGui.QPen(QtGui.QColor('black'), 3))
        qp.setBrush(QtGui.QColor(128, 128, 255, 128))
        qp.drawRect(QtCore.QRect(self.begin, self.end))

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = self.begin
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        QtWidgets.QApplication.restoreOverrideCursor()
        self.close()

        x1 = min(self.begin.x(), self.end.x())
        y1 = min(self.begin.y(), self.end.y())
        x2 = max(self.begin.x(), self.end.x())
        y2 = max(self.begin.y(), self.end.y())

        # Capture the image
        img = ImageGrab.grab(bbox=(x1, y1, x2, y2))

        # Save the image to a temporary file
        self.main_window.temp_image_path = "capture_temp.png"
        img.save(self.main_window.temp_image_path)

        # Convert the image to Qt format (without OpenCV)
        img = np.array(img)  # Convert PIL image to NumPy array
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(img.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(q_img)

        # Update the main window with the captured image
        self.main_window.display_captured_image(pixmap)
        self.main_window.bring_to_front()  # Bring the main window back to front

    def capture_whole_screen(self):
        """Captures the entire screen and sends it to the main window."""
        self.close()
        screen = ImageGrab.grab()
        self.main_window.temp_image_path = "whole_screen_capture.png"
        screen.save(self.main_window.temp_image_path)

        # Convert to QPixmap
        img = np.array(screen)
        height, width, channel = img.shape
        bytes_per_line = 3 * width
        q_img = QtGui.QImage(img.data, width, height, bytes_per_line, QtGui.QImage.Format.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(q_img)

        self.main_window.display_captured_image(pixmap)
        self.main_window.bring_to_front()



class ViewBot(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ViewBot v2.1")
        self.setGeometry(100, 100, 800, 600)
        try:
            self.setWindowIcon(QtGui.QIcon('resources/favicon.ico'))
        except:
            try:
                self.setWindowIcon(QtGui.QIcon(resource_path('resources/favicon.ico')))
            except:
                pass

        # Configure Gemini API
        self.genai = genai
        self.genai.configure(api_key="REPLACE THIS WITH REAL API KEY")  # Plaintext API key
        self.model = genai.GenerativeModel('gemini-1.5-flash')  # Or your preferred model

        # Add a QLabel to display the captured image
        self.image_label = QtWidgets.QLabel(self)
        self.image_label.setAlignment(QtCore.Qt.AlignCenter)
        self.image_label.setText("Press Ctrl+Y to capture the screen")

        self.explanation_text = QtWidgets.QTextEdit(self)
        self.explanation_text.setReadOnly(True)
        self.explanation_text.setStyleSheet("font-size: 14px;")
        self.explanation_text.setMinimumWidth(400)
        self.gemini_explanation_label = QtWidgets.QLabel(self)
        self.gemini_explanation_label.setText("AI Explanation:")
        self.gemini_explanation_label.setStyleSheet(
            "font-family: 'Courtier'; font-size: 14pt; font-weight: bold; color: blue;")
        self.explanation_frame = QtWidgets.QFrame(self)
        self.explanation_frame.setFrameStyle(QtWidgets.QFrame.Box | QtWidgets.QFrame.Plain)
        self.explanation_frame.setLayout(QtWidgets.QVBoxLayout())
        self.explanation_frame.layout().addWidget(self.gemini_explanation_label)
        self.explanation_frame.layout().addWidget(self.explanation_text)
        self.explanation_frame.hide()

        # Create a layout and add widgets
        layout = QtWidgets.QHBoxLayout()  # Use QHBoxLayout for side-by-side layout
        layout.addWidget(self.image_label, 70)  # 70% width for the image
        layout.addWidget(self.explanation_frame, 30)  # 30% width for the explanation

        central_widget = QtWidgets.QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

        # Set up a global hotkey for Ctrl+Y using the `keyboard` library
        self.setup_global_hotkey()

        # Create a toolbar
        self.create_toolbar()

        # Variable to store the current pixmap
        self.current_pixmap = None
        # Temporary file path for the captured image
        self.temp_image_path = None

        # Thread to monitor file changes
        self.file_monitor_thread = None
        self.stop_monitoring = False

        # Track the MS Paint process
        self.ms_paint_process = None

        self.snipping_tool = None

    def create_toolbar(self):
        """Creates a toolbar with actions."""
        toolbar = self.addToolBar("Main Toolbar")

        # Add actions to the toolbar
        new_action = QtWidgets.QAction("New", self)
        new_action.triggered.connect(self.on_new)
        toolbar.addAction(new_action)

        save_action = QtWidgets.QAction("Save", self)
        save_action.triggered.connect(self.on_save)
        toolbar.addAction(save_action)

        # Add a Paint action to open MS Paint
        paint_action = QtWidgets.QAction("Paint", self)
        paint_action.triggered.connect(self.open_ms_paint)
        toolbar.addAction(paint_action)

        # Add an Explain action
        explain_action = QtWidgets.QAction("Explain", self)
        explain_action.triggered.connect(self.on_explain)
        toolbar.addAction(explain_action)
        # Add a separator
        toolbar.addSeparator()

        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        toolbar.addAction(exit_action)

        try:
            new_action.setIcon(QtGui.QIcon('resources/new.png'))
            save_action.setIcon(QtGui.QIcon('resources/save.png'))
            paint_action.setIcon(QtGui.QIcon('resources/paint.png'))
            explain_action.setIcon(QtGui.QIcon('resources/explain.png'))
            exit_action.setIcon(QtGui.QIcon('resources/exit.png'))
        except:
            try:
                new_action.setIcon(resource_path(QtGui.QIcon('resources/new.png')))
                save_action.setIcon(resource_path(QtGui.QIcon('resources/save.png')))
                paint_action.setIcon(resource_path(QtGui.QIcon('resources/paint.png')))
                explain_action.setIcon(resource_path(QtGui.QIcon('resources/explain.png')))
                exit_action.setIcon(resource_path(QtGui.QIcon('resources/exit.png')))
            except:
                pass

        self.bring_to_front()

    def setup_global_hotkey(self):
        """Sets up a global hotkey in a separate thread."""

        def hotkey_listener():
            keyboard.add_hotkey('ctrl+y', self.launch_snipping_tool_safe)
            keyboard.wait('esc')  # Keep the listener running until 'esc' is pressed

        # Run the hotkey listener in a separate thread
        threading.Thread(target=hotkey_listener, daemon=True).start()

    def on_new(self):
        """Handles the 'New' action."""
        self.showMinimized()
        self.launch_snipping_tool_safe()

    def on_save(self):
        """Handles the 'Save' action."""
        if self.current_pixmap:
            # Open a file dialog to choose the save location
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save Image", "", "PNG Files (*.png);;All Files (*)"
            )
            if file_path:
                # Save the pixmap to the selected file
                self.current_pixmap.save(file_path)
                print(f"Image saved to {file_path}")
        else:
            print("No image to save")

    def on_explain(self):
        """Handles the 'Explain' action."""
        if self.current_pixmap:
            try:
                text, ok = QInputDialog.getText(None, "Prompt", "Enter prompt for the captured image:")
                if ok:
                    # Convert the QPixmap to a PIL image
                    self.explanation_frame.show()
                    pil_image = self.qpixmap_to_pil(self.current_pixmap)

                    # Generate an explanation for the image
                    explanation = self.explain_screenshot(pil_image, text=text)

                    # Display the explanation in a dialog
                    self.add_message(explanation)
            except Exception as e:
                print(f"Error during explanation: {e}")
                self.show_explanation_dialog("Failed to generate explanation.")
        else:
            print("No image to explain")

    @staticmethod
    def qpixmap_to_pil(qpixmap):
        """Converts a QPixmap to a PIL image."""
        try:
            # Convert QPixmap to QImage
            qimage = qpixmap.toImage()

            # Convert QImage to a byte array
            buffer = QtCore.QBuffer()
            buffer.open(QtCore.QIODevice.ReadWrite)
            qimage.save(buffer, "PNG")

            # Convert the byte array to a PIL image
            pil_image = Image.open(BytesIO(buffer.data()))
            buffer.close()
            return pil_image
        except Exception as e:
            print(f"Error converting QPixmap to PIL image: {e}")
            raise

    def explain_screenshot(self, image, text='Explain the given image'):
        """Generates an explanation for the given image."""
        try:
            # Ensure the image is in a format the API can handle
            if not isinstance(image, Image.Image):
                raise ValueError("Invalid image format. Expected a PIL image.")

            # Generate an explanation using the Gemini API
            response = self.model.generate_content([text, image], stream=True)
            print('Explaining...')
            explanation = ""
            for part in response:
                explanation += part.text + '\n'
                self.add_message(part.text)
                print(part.text, end="", flush=True)
            self.explanation_text.clear()
            return explanation
        except Exception as e:
            print(f"Error generating explanation: {e}")
            return "Unable to generate explanation due to an error."

    def add_message(self, message):
        """Adds a message to the explanation panel with formatting."""
        # Apply formatting to the message
        formatted_message = self.apply_formatting(message)

        # Insert the formatted message into the QTextEdit
        self.explanation_text.insertHtml(f"<p>{formatted_message}</p><br><br>")
        self.explanation_text.moveCursor(QtGui.QTextCursor.End)
        self.explanation_text.update()
        QApplication.processEvents()

    @staticmethod
    def apply_formatting(text):
        """Applies formatting to the text (bold, italic, monospace, etc.)."""
        # Apply bold formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

        # Apply monospace formatting
        text = re.sub(r'```(.*?)```', r'<code>\1</code>', text, flags=re.DOTALL)

        # Highlight integers
        text = re.sub(r'-?\d+', r'<span style="color: blue;">\g<0></span>', text)

        # Highlight strings
        text = re.sub(r'(\".*?\")', r'<span style="color: green;">\1</span>', text)

        text = re.sub(r'(?<!\*)\*(?!\*)', '<br><br>', text)

        return text

    def open_ms_paint(self):
        """Opens Microsoft Paint with the captured image."""
        if self.temp_image_path and os.path.exists(self.temp_image_path):
            try:
                # Launch MS Paint with the temporary image file
                self.ms_paint_process = subprocess.Popen(["mspaint", self.temp_image_path])
                print("Microsoft Paint opened with the captured image.")

                # Start monitoring the file for changes
                self.stop_monitoring = False
                self.file_monitor_thread = threading.Thread(target=self.monitor_file_changes)
                self.file_monitor_thread.start()
            except Exception as e:
                print(f"Failed to open MS Paint: {e}")
        else:
            print("No captured image to open in MS Paint.")

    def monitor_file_changes(self):
        """Monitors the temporary file for changes."""
        if not self.temp_image_path:
            return

        # Get the initial modification time of the file
        last_modified = os.path.getmtime(self.temp_image_path)

        while not self.stop_monitoring:
            try:
                # Check if the file has been modified
                current_modified = os.path.getmtime(self.temp_image_path)
                if current_modified != last_modified:
                    print("Image file modified. Reloading...")
                    last_modified = current_modified

                    # Reload the image into the main window
                    self.reload_image_from_file()

                    # Close MS Paint after the file is updated
                    self.close_ms_paint()

                # Sleep for a short time to avoid high CPU usage
                time.sleep(1)
            except Exception as e:
                print(f"Error monitoring file: {e}")
                break

    def reload_image_from_file(self):
        """Reloads the image from the temporary file."""
        if self.temp_image_path and os.path.exists(self.temp_image_path):
            # Load the image from the file
            pixmap = QtGui.QPixmap(self.temp_image_path)
            if not pixmap.isNull():
                # Update the main window with the new image
                self.display_captured_image(pixmap)
                print("Image reloaded from file.")
            else:
                print("Failed to load image from file.")
        else:
            print("Temporary image file does not exist.")

    def close_ms_paint(self):
        """Closes the MS Paint process."""
        if self.ms_paint_process:
            try:
                # Terminate the MS Paint process
                self.ms_paint_process.terminate()
                self.ms_paint_process = None
                print("MS Paint closed.")
            except Exception as e:
                print(f"Failed to close MS Paint: {e}")

    def launch_snipping_tool_safe(self):
        """Safely launches the snipping tool from the main thread."""
        QtCore.QTimer.singleShot(0, self.launch_snipping_tool)

    def launch_snipping_tool(self):
        """Launches the snipping tool when Ctrl+Y is pressed."""
        self.snipping_tool = SnippingTool(self)
        self.snipping_tool.show()

    def display_captured_image(self, pixmap):
        """Displays the captured image in the main window."""
        self.current_pixmap = pixmap  # Store the current pixmap
        self.image_label.setPixmap(pixmap.scaled(self.image_label.size(), QtCore.Qt.KeepAspectRatio))

    def bring_to_front(self):
        """Brings the main window to the front."""
        self.setWindowState(QtCore.Qt.WindowActive)  # Ensure the window is active
        if self.isMinimized():
            self.showNormal()  # Restore if minimized
        self.raise_()  # Bring to front
        self.activateWindow()  # Focus the window

    def closeEvent(self, event):
        """Handles the window close event."""
        try:
            # Delete the temporary file if it exists
            if self.temp_image_path and os.path.exists(self.temp_image_path):
                os.remove(self.temp_image_path)
        except Exception as e:
            print(f"Error deleting temporary file: {e}")

        event.accept()


def resource_path(relative_path):
    """ Get the path to the resource, works for both development and bundled app """
    try:
        # PyInstaller creates a temporary folder for bundled resources
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(__file__))
    except Exception:
        base_path = os.path.dirname(__file__)
    return os.path.join(base_path, relative_path)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main_window = ViewBot()
    main_window.show()
    sys.exit(app.exec_())
