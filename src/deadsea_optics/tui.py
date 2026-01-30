import itertools
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from textual import on, work
from textual.app import App, ComposeResult
from textual.message import Message
from textual.widgets import Footer, Header
from textual.worker import Worker, get_current_worker
from textual_plot.plot_widget import HiResMode, PlotWidget

from deadsea_optics import SpectroscopyExperiment


class DeadSeaOpticsApp(App[None]):
    AUTO_FOCUS = "PlotWidget"

    CSS_PATH = "tui.tcss"

    BINDINGS = [("m", "cycle_modes", "Cycle Modes")]

    _hires_modes = itertools.cycle(
        [HiResMode.QUADRANT, HiResMode.BRAILLE, None, HiResMode.HALFBLOCK]
    )
    hires_mode = next(_hires_modes)

    @dataclass
    class NewSpectrum(Message):
        wavelengths: NDArray[np.floating]
        intensities: NDArray[np.floating]

    spectrum_worker: Worker[None] | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield PlotWidget()

    def on_mount(self) -> None:
        self.spectrum_worker = self.get_spectra()

    def on_unmount(self) -> None:
        if self.spectrum_worker is not None:
            self.spectrum_worker.cancel()

    @work(thread=True)
    def get_spectra(self) -> None:
        worker = get_current_worker()
        experiment = SpectroscopyExperiment()
        experiment.set_integration_time(200_000)
        while True:
            wavelengths, intensities = experiment.get_spectrum()
            if worker.is_cancelled:
                break
            else:
                self.post_message(
                    self.NewSpectrum(wavelengths=wavelengths, intensities=intensities)
                )

    @on(NewSpectrum)
    def handle_new_data(self, event: NewSpectrum) -> None:
        self.wavelengths = event.wavelengths
        self.intensities = event.intensities
        self.plot_spectrum()

    def plot_spectrum(self) -> None:
        plot = self.query_one(PlotWidget)
        plot.clear()
        plot.plot(self.wavelengths, self.intensities, hires_mode=self.hires_mode)
        plot.set_ylimits(ymin=0)
        plot.set_xlabel("Wavelength (nm)")
        plot.set_ylabel("Intensity")

    def action_cycle_modes(self) -> None:
        self.hires_mode = next(self._hires_modes)
        self.plot_spectrum()


app = DeadSeaOpticsApp


def main() -> None:
    app().run()


if __name__ == "__main__":
    main()
