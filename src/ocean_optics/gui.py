import sys

import numpy as np
import pyqtgraph as pg
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Slot

from ocean_optics.spectroscopy import SpectroscopyExperiment
from ocean_optics.ui_main_window import Ui_MainWindow

# PyQtGraph global options
pg.setConfigOption("background", "w")
pg.setConfigOption("foreground", "k")


class MeasurementWorker(QtCore.QThread):
    new_data = QtCore.Signal(np.ndarray, np.ndarray)
    stopped = False

    def setup(self, experiment: SpectroscopyExperiment) -> None:
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


class ContinuousSpectrumWorker(MeasurementWorker):
    def run(self) -> None:
        self.stopped = False
        while True:
            wavelengths, intensities = self.experiment.get_spectrum()
            self.new_data.emit(wavelengths, intensities)
            if self.stopped:
                break


class UserInterface(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        # Load UI
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Slots and signals
        self.ui.integration_time.valueChanged.connect(self.set_integration_time)
        self.ui.single_button.clicked.connect(self.single_measurement)
        self.ui.integrate_button.clicked.connect(self.integrate_spectrum)
        self.ui.continuous_button.clicked.connect(self.continuous_spectrum)
        self.ui.stop_button.clicked.connect(self.stop_measurement)

        # Open device
        self.experiment = SpectroscopyExperiment()
        self.experiment.set_integration_time(self.ui.integration_time.value())

        # Workers
        self.integrate_spectrum_worker = IntegrateSpectrumWorker()
        self.integrate_spectrum_worker.new_data.connect(self.plot_new_data)
        self.integrate_spectrum_worker.progress.connect(self.update_progress_bar)
        self.integrate_spectrum_worker.finished.connect(self.worker_has_finished)
        self.continuous_spectrum_worker = ContinuousSpectrumWorker()
        self.continuous_spectrum_worker.new_data.connect(self.plot_new_data)
        self.continuous_spectrum_worker.finished.connect(self.worker_has_finished)

    @Slot()
    def set_integration_time(self, value: int) -> None:
        self.experiment.set_integration_time(value)

    @Slot()
    def single_measurement(self) -> None:
        self.ui.progress_bar.setRange(0, 1)
        wavelengths, intensities = self.experiment.get_spectrum()
        self.plot_data(wavelengths, intensities)

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
            print("Continuous is running")
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
    def worker_has_finished(self) -> None:
        self.ui.single_button.setEnabled(True)
        self.ui.integrate_button.setEnabled(True)
        self.ui.continuous_button.setEnabled(True)
        self.ui.stop_button.setEnabled(False)

    def plot_data(self, wavelengths, intensities) -> None:
        self.ui.plot_widget.clear()
        self.ui.plot_widget.plot(
            wavelengths, intensities, symbol=None, pen={"color": "k", "width": 5}
        )
        self.ui.plot_widget.setLabel("left", "Intensity")
        self.ui.plot_widget.setLabel("bottom", "Wavelength (nm)")
        self.ui.plot_widget.setLimits(yMin=0)

    @Slot(tuple)
    def plot_new_data(self, wavelengths: np.ndarray, intensities: np.ndarray) -> None:
        self.plot_data(wavelengths, intensities)

    @Slot(int)
    def update_progress_bar(self, value: int) -> None:
        self.ui.progress_bar.setValue(value)


def main():
    app = QtWidgets.QApplication(sys.argv)
    ui = UserInterface()
    ui.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
