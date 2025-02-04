import csv
import importlib.metadata
import importlib.resources
import sys
from textwrap import dedent
from typing import Any

import numpy as np
import pyqtgraph as pg
from numpy.typing import NDArray
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Slot

from deadsea_optics.spectroscopy import (
    AccessError,
    DeviceNotFoundError,
    SpectroscopyExperiment,
    SpectrumTimeOutError,
)
from deadsea_optics.ui_main_window import Ui_MainWindow

metadata = importlib.metadata.metadata("deadsea_optics")
__name__ = metadata["name"]
__version__ = metadata["version"]

# PyQtGraph global options
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class MeasurementWorker(QtCore.QThread):
    new_data = QtCore.Signal(np.ndarray, np.ndarray)
    stopped = False

    def setup(
        self, experiment: SpectroscopyExperiment, *args: Any, **kwargs: Any
    ) -> None:
        self.experiment = experiment

    def run(self) -> None: ...

    def stop(self) -> None:
        self.stopped = True


class IntegrateSpectrumWorker(MeasurementWorker):
    progress = QtCore.Signal(int)

    def setup(
        self,
        experiment: SpectroscopyExperiment,
        count: int,
    ) -> None:
        self.experiment = experiment
        self.count = count

    def run(self) -> None:
        self.stopped = False
        for idx, (wavelengths, intensities) in enumerate(
            self.experiment.integrate_spectrum(self.count), start=1
        ):
            self.new_data.emit(wavelengths, intensities)
            self.progress.emit(idx)
            if self.stopped:
                self.experiment.stopped = True


class SingleSpectrumWorker(MeasurementWorker):
    def run(self) -> None:
        self.stopped = False
        wavelengths, intensities = self.experiment.get_spectrum()
        self.new_data.emit(wavelengths, intensities)


class ContinuousSpectrumWorker(MeasurementWorker):
    def run(self) -> None:
        self.stopped = False
        while True:
            try:
                wavelengths, intensities = self.experiment.get_spectrum()
            except SpectrumTimeOutError:
                continue
            self.new_data.emit(wavelengths, intensities)
            if self.stopped:
                break


class UserInterface(QtWidgets.QMainWindow):
    _wavelengths: NDArray[np.floating] | None = None
    _intensities: NDArray[np.floating] | None = None
    _show_lines: bool = True

    def __init__(self) -> None:
        super().__init__()

        # Load UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)  # type: ignore
        if sys.platform == "win32":
            # On Windows, you have to set app icon manually
            self.setWindowIcon(
                QtGui.QIcon(
                    str(
                        importlib.resources.files("deadsea_optics.resources")
                        / "app_icon.ico"
                    )
                )
            )

        # Slots and signals
        self.ui.integration_time.valueChanged.connect(self.set_integration_time)
        self.ui.single_button.clicked.connect(self.single_spectrum)
        self.ui.integrate_button.clicked.connect(self.integrate_spectrum)
        self.ui.continuous_button.clicked.connect(self.continuous_spectrum)
        self.ui.stop_button.clicked.connect(self.stop_measurement)
        self.ui.toggle_lines_button.clicked.connect(self.toggle_lines_markers)
        self.ui.save_button.clicked.connect(self.save_data)

        # Menu actions
        self.ui.actionQuit.triggered.connect(self.close)
        self.ui.actionAbout_DeadSea_Optics.triggered.connect(self.show_about_dialog)

        # Open device
        try:
            self.experiment = SpectroscopyExperiment()
        except (DeviceNotFoundError, AccessError) as exc:
            msg = "Please connect a compatible device. "
            if sys.platform == "win32":
                msg += "Also make sure the device is registered as a WinUSB device, using device manager. For details, please visit <a href='https://github.com/davidfokkema/deadsea_optics'>https://github.com/davidfokkema/deadsea_optics</a>. "
            if error_msg := str(exc):
                msg += f"The error was: {error_msg}."
            QtWidgets.QMessageBox.critical(
                self, "Device not found or inaccessible", msg
            )  # type: ignore
            sys.exit()
        self.experiment.set_integration_time(self.ui.integration_time.value())

        # Workers
        self.integrate_spectrum_worker = IntegrateSpectrumWorker()
        self.integrate_spectrum_worker.new_data.connect(self.plot_new_data)
        self.integrate_spectrum_worker.progress.connect(self.update_progress_bar)
        self.integrate_spectrum_worker.finished.connect(self.worker_has_finished)
        self.single_spectrum_worker = SingleSpectrumWorker()
        self.single_spectrum_worker.new_data.connect(self.plot_new_data)
        self.single_spectrum_worker.finished.connect(
            self.single_spectrum_worker_has_finished
        )
        self.continuous_spectrum_worker = ContinuousSpectrumWorker()
        self.continuous_spectrum_worker.new_data.connect(self.plot_new_data)
        self.continuous_spectrum_worker.finished.connect(self.worker_has_finished)

    def closeEvent(self, event):
        self.single_spectrum_worker.stop()
        self.continuous_spectrum_worker.stop()
        self.integrate_spectrum_worker.stop()
        self.single_spectrum_worker.wait()
        self.continuous_spectrum_worker.wait()
        self.integrate_spectrum_worker.wait()

    @Slot(int)  # type: ignore
    def set_integration_time(self, value: int) -> None:
        self.experiment.set_integration_time(value)

    @Slot()
    def single_spectrum(self) -> None:
        self.disable_measurement_buttons()
        self.ui.progress_bar.setMinimum(0)
        self.ui.progress_bar.setMaximum(0)
        self.single_spectrum_worker.setup(experiment=self.experiment)
        self.single_spectrum_worker.start()

    @Slot()
    def integrate_spectrum(self) -> None:
        self.disable_measurement_buttons()
        count = self.ui.num_integrations.value()
        self.ui.progress_bar.setRange(0, count)
        self.ui.progress_bar.setValue(0)
        self.integrate_spectrum_worker.setup(experiment=self.experiment, count=count)
        self.integrate_spectrum_worker.start()

    @Slot()
    def continuous_spectrum(self) -> None:
        self.disable_measurement_buttons()
        self.ui.progress_bar.setMinimum(0)
        self.ui.progress_bar.setMaximum(0)
        self.continuous_spectrum_worker.setup(experiment=self.experiment)
        self.continuous_spectrum_worker.start()

    @Slot()
    def stop_measurement(self) -> None:
        if self.continuous_spectrum_worker.isRunning():
            self.continuous_spectrum_worker.stop()
            self.ui.progress_bar.setRange(0, 1)
        else:
            self.integrate_spectrum_worker.stop()

    def disable_measurement_buttons(self) -> None:
        self.ui.single_button.setEnabled(False)
        self.ui.integrate_button.setEnabled(False)
        self.ui.continuous_button.setEnabled(False)
        self.ui.stop_button.setEnabled(True)

    @Slot()
    def single_spectrum_worker_has_finished(self) -> None:
        self.worker_has_finished()
        self.ui.progress_bar.setRange(0, 1)

    @Slot()
    def worker_has_finished(self) -> None:
        self.ui.single_button.setEnabled(True)
        self.ui.integrate_button.setEnabled(True)
        self.ui.continuous_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)

    def plot_data(self) -> None:
        self.ui.plot_widget.clear()
        if self._show_lines:
            self.ui.plot_widget.plot(
                self._wavelengths, self._intensities, pen={"color": "k", "width": 5}
            )

        else:
            self.ui.plot_widget.plot(
                self._wavelengths,
                self._intensities,
                symbol="o",
                symbolSize=3,
                symbolPen={"color": "k"},
                symbolBrush="k",
                pen=None,
            )
        self.ui.plot_widget.setLabel("left", "Intensity")
        self.ui.plot_widget.setLabel("bottom", "Wavelength (nm)")
        self.ui.plot_widget.setLimits(yMin=0)

    @Slot(tuple)  # type: ignore
    def plot_new_data(
        self, wavelengths: NDArray[np.floating], intensities: NDArray[np.floating]
    ) -> None:
        self._wavelengths = wavelengths
        self._intensities = intensities
        if self.experiment.has_overflow:
            self.ui.statusbar.showMessage(
                "🔴 WARNING: overflow detected, reduce integration time."
            )
        else:
            self.ui.statusbar.showMessage("🟢 Data condition: good.")
        self.plot_data()

    @Slot()
    def toggle_lines_markers(self) -> None:
        self._show_lines = not self._show_lines
        self.plot_data()

    @Slot(int)  # type: ignore
    def update_progress_bar(self, value: int) -> None:
        self.ui.progress_bar.setValue(value)

    @Slot()
    def save_data(self) -> None:
        if self._wavelengths is None or self._intensities is None:
            QtWidgets.QMessageBox.warning(
                self, "No data", "Perform a measurement before saving."
            )  # type: ignore
        else:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(filter="CSV Files (*.csv)")
            with open(path, mode="w") as f:
                writer = csv.writer(f)
                writer.writerow(["Wavelength (nm)", "Intensity"])
                for wavelength, intensity in zip(self._wavelengths, self._intensities):
                    writer.writerow([wavelength, intensity])
            QtWidgets.QMessageBox.information(
                self, "Data saved", f"Data saved successfully to {path}."
            )

    def show_about_dialog(self):
        """Show about application dialog."""
        box = QtWidgets.QMessageBox(parent=self)
        box.setText("DeadSea Optics")
        box.setInformativeText(
            dedent(
                f"""
            <p>Version {__version__}.</p>

            <p>DeadSea Optics is written by David Fokkema for use in the physics lab courses at the Vrije Universiteit Amsterdam and the University of Amsterdam.</p>

            <p>DeadSea Optics is free software licensed under the GNU General Public License v3.0 or later.</p>

            <p>For more information, please visit:<br><a href="https://github.com/davidfokkema/deadsea_optics">https://github.com/davidfokkema/deadsea_optics</a></p>
        """
            )
        )
        box.exec()


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
