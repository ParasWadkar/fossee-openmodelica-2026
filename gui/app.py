"""
OpenModelica Simulation Runner
-------------------------------
A PyQt6 desktop application to launch OpenModelica-compiled
executables with configurable start and stop times.

Author: Paras
Project: FOSSEE Summer Fellowship 2026 - OpenModelica Screening Task
"""

import sys
import subprocess
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QTextEdit,
    QFrame,
    QSpinBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon


class SimulationWorker(QThread):
    """
    Worker thread to run the simulation executable without
    blocking the main GUI thread.
    """

    output_received = pyqtSignal(str)
    simulation_finished = pyqtSignal(int)
    error_occurred = pyqtSignal(str)

    def __init__(self, executable: str, start_time: int, stop_time: int):
        super().__init__()
        self.executable = executable
        self.start_time = start_time
        self.stop_time = stop_time

    def run(self):
        """Execute the simulation with the given parameters."""
        command = [
            self.executable,
            f"-startTime={self.start_time}",
            f"-stopTime={self.stop_time}",
        ]

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(Path(self.executable).parent),
            )

            for line in process.stdout:
                self.output_received.emit(line.rstrip())

            process.wait()
            self.simulation_finished.emit(process.returncode)

        except FileNotFoundError:
            self.error_occurred.emit(
                f"Executable not found: {self.executable}"
            )
        except PermissionError:
            self.error_occurred.emit(
                "Permission denied. Cannot execute the selected file."
            )
        except Exception as e:
            self.error_occurred.emit(f"Unexpected error: {str(e)}")


class SimulationRunner(QMainWindow):
    """
    Main application window for the OpenModelica Simulation Runner.

    Provides a GUI to:
    - Select an OpenModelica-compiled executable
    - Set simulation start and stop times
    - Run the simulation and view live output
    """

    def __init__(self):
        super().__init__()
        self.worker = None
        self._init_ui()

    def _init_ui(self):
        """Initialize and lay out all UI components."""
        self.setWindowTitle("OpenModelica Simulation Runner")
        self.setMinimumSize(700, 550)
        self.setStyleSheet(self._stylesheet())

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(24, 24, 24, 24)

        # Header
        header = QLabel("OpenModelica Simulation Runner")
        header.setObjectName("header")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        subtitle = QLabel("FOSSEE Summer Fellowship 2026 — Screening Task")
        subtitle.setObjectName("subtitle")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle)

        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setObjectName("divider")
        main_layout.addWidget(divider)

        # Executable selector
        main_layout.addWidget(self._make_label("Executable Path"))
        exe_row = QHBoxLayout()
        self.exe_input = QLineEdit()
        self.exe_input.setPlaceholderText(
            "Select the compiled OpenModelica executable (.exe)"
        )
        self.exe_input.setObjectName("exe_input")
        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("browse_btn")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse_executable)
        exe_row.addWidget(self.exe_input)
        exe_row.addWidget(browse_btn)
        main_layout.addLayout(exe_row)

        # Time inputs
        time_row = QHBoxLayout()
        time_row.setSpacing(16)

        start_col = QVBoxLayout()
        start_col.addWidget(self._make_label("Start Time (s)"))
        self.start_input = QSpinBox()
        self.start_input.setRange(0, 4)
        self.start_input.setValue(0)
        self.start_input.setObjectName("time_input")
        start_col.addWidget(self.start_input)

        stop_col = QVBoxLayout()
        stop_col.addWidget(self._make_label("Stop Time (s)"))
        self.stop_input = QSpinBox()
        self.stop_input.setRange(1, 4)
        self.stop_input.setValue(1)
        self.stop_input.setObjectName("time_input")
        stop_col.addWidget(self.stop_input)

        time_row.addLayout(start_col)
        time_row.addLayout(stop_col)
        main_layout.addLayout(time_row)

        # Constraint hint
        hint = QLabel("Constraint: 0 ≤ start time < stop time < 5")
        hint.setObjectName("hint")
        main_layout.addWidget(hint)

        # Run button
        self.run_btn = QPushButton("▶  Run Simulation")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setFixedHeight(44)
        self.run_btn.clicked.connect(self._run_simulation)
        main_layout.addWidget(self.run_btn)

        # Output console
        main_layout.addWidget(self._make_label("Simulation Output"))
        self.output_console = QTextEdit()
        self.output_console.setReadOnly(True)
        self.output_console.setObjectName("console")
        self.output_console.setPlaceholderText(
            "Simulation output will appear here..."
        )
        main_layout.addWidget(self.output_console)

        # Status bar
        self.statusBar().showMessage("Ready")

    def _make_label(self, text: str) -> QLabel:
        """Create a styled form label."""
        label = QLabel(text)
        label.setObjectName("form_label")
        return label

    def _browse_executable(self):
        """Open a file dialog to select the simulation executable."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select OpenModelica Executable",
            str(Path.home()),
            "Executable Files (*.exe);;All Files (*)",
        )
        if file_path:
            self.exe_input.setText(file_path)

    def _validate_inputs(self) -> bool:
        """
        Validate all user inputs before running the simulation.

        Returns:
            True if all inputs are valid, False otherwise.
        """
        exe_path = self.exe_input.text().strip()
        if not exe_path.endswith(".exe"):
            self._show_error("Please select a valid .exe file.")
            return False

        if not exe_path:
            self._show_error("Please select an executable file.")
            return False

        if not Path(exe_path).exists():
            self._show_error("The selected executable file does not exist.")
            return False

        if not Path(exe_path).is_file():
            self._show_error("The selected path is not a file.")
            return False

        start = self.start_input.value()
        stop = self.stop_input.value()

        if not (0 <= start < stop < 5):
            self._show_error(
                "Invalid time range.\n"
                "Ensure: 0 ≤ start time < stop time < 5"
            )
            return False

        return True

    def _run_simulation(self):
        """Validate inputs and launch the simulation in a worker thread."""
        if not self._validate_inputs():
            return

        self.output_console.clear()
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳  Running...")
        self.statusBar().showMessage("Simulation running...")

        self.worker = SimulationWorker(
            executable=self.exe_input.text().strip(),
            start_time=self.start_input.value(),
            stop_time=self.stop_input.value(),
        )
        self.worker.output_received.connect(self._append_output)
        self.worker.simulation_finished.connect(self._on_simulation_finished)
        self.worker.error_occurred.connect(self._on_error)
        self.worker.start()

    def _append_output(self, line: str):
        """Append a line of output to the console."""
        self.output_console.append(line)

    def _on_simulation_finished(self, return_code: int):
        """Handle simulation completion."""
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  Run Simulation")

        if return_code == 0:
            self.output_console.append("\n✅ Simulation completed successfully.")
            self.statusBar().showMessage("Simulation completed successfully.")
        else:
            self.output_console.append(
                f"\n❌ Simulation failed (exit code {return_code}). Check logs above."
            )
            self.statusBar().showMessage("Simulation failed.")

    def _on_error(self, message: str):
        """Handle errors from the worker thread."""
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶  Run Simulation")
        self.statusBar().showMessage("Error occurred.")
        self._show_error(message)

    def _show_error(self, message: str):
        """Display an error dialog."""
        QMessageBox.critical(self, "Error", message)

    def _stylesheet(self) -> str:
        """Return the application stylesheet."""
        return """
            QMainWindow, QWidget {
                background-color: #0f1117;
                color: #e2e8f0;
                font-family: 'Consolas', 'Courier New', monospace;
            }
            QLabel#header {
                font-size: 20px;
                font-weight: bold;
                color: #63b3ed;
                letter-spacing: 1px;
            }
            QLabel#subtitle {
                font-size: 11px;
                color: #718096;
            }
            QFrame#divider {
                color: #2d3748;
                margin: 4px 0;
            }
            QLabel#form_label {
                font-size: 12px;
                color: #a0aec0;
                margin-bottom: 2px;
            }
            QLabel#hint {
                font-size: 11px;
                color: #f6ad55;
            }
            QLineEdit, QSpinBox {
                background-color: #1a202c;
                border: 1px solid #2d3748;
                border-radius: 6px;
                padding: 8px 10px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QLineEdit:focus, QSpinBox:focus {
                border: 1px solid #63b3ed;
            }
            QPushButton#browse_btn {
                background-color: #2d3748;
                border: 1px solid #4a5568;
                border-radius: 6px;
                padding: 8px;
                color: #e2e8f0;
                font-size: 13px;
            }
            QPushButton#browse_btn:hover {
                background-color: #4a5568;
            }
            QPushButton#run_btn {
                background-color: #2b6cb0;
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 14px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }
            QPushButton#run_btn:hover {
                background-color: #3182ce;
            }
            QPushButton#run_btn:disabled {
                background-color: #2d3748;
                color: #718096;
            }
            QTextEdit#console {
                background-color: #1a202c;
                border: 1px solid #2d3748;
                border-radius: 6px;
                padding: 10px;
                color: #68d391;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
            }
            QStatusBar {
                color: #718096;
                font-size: 11px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #2d3748;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #4a5568;
            }
        """


def main():
    """Entry point for the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("OpenModelica Simulation Runner")
    app.setStyle("Fusion")

    window = SimulationRunner()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
