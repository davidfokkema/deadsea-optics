from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from textual import on, work
from textual.app import App, ComposeResult
from textual.message import Message
from textual.worker import Worker, get_current_worker
from textual_plot.plot_widget import HiResMode, PlotWidget

from deadsea_optics import SpectroscopyExperiment


class MyApp(App[None]):
    @dataclass
    class NewSpectrum(Message):
        wavelengths: NDArray[np.floating]
        intensities: NDArray[np.floating]

    spectrum_worker: Worker | None = None

    def compose(self) -> ComposeResult:
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
        while True:
            wavelengths, intensities = experiment.get_spectrum()
            if worker.is_cancelled:
                break
            else:
                self.post_message(
                    self.NewSpectrum(wavelengths=wavelengths, intensities=intensities)
                )

    @on(NewSpectrum)
    def plot_spectrum(self, event: NewSpectrum):
        plot = self.query_one(PlotWidget)
        plot.clear()
        plot.plot(event.wavelengths, event.intensities, hires_mode=HiResMode.BRAILLE)
        plot.set_xlimits(min(event.wavelengths), max(event.wavelengths))
        plot.set_ylimits(0, max(event.intensities))


MyApp().run()
