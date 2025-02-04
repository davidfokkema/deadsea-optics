from typing import Iterator

import numpy as np
from numpy.typing import NDArray

from deadsea_optics.usb2000 import OceanOpticsUSB2000
from deadsea_optics.usb2000plus import (
    AccessError,
    DeviceNotFoundError,
    OceanOpticsUSB2000Plus,
    SpectrumTimeOutError,
)

__all__ = [
    "AccessError",
    "DeviceNotFoundError",
    "SpectroscopyExperiment",
    "SpectrumTimeOutError",
]


class SpectroscopyExperiment:
    stopped = True
    has_overflow: bool = False

    def __init__(self) -> None:
        try:
            self.device = OceanOpticsUSB2000Plus()
        except DeviceNotFoundError:
            self.device = OceanOpticsUSB2000()

    def get_spectrum(self) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        """Record a spectrum.

        Returns:
            A tuple of `np.ndarrays` with wavelength, intensity data. The
            wavelengths are in nanometers but the intensity is in arbitrary
            units (but should be calibrated so that different devices yield the
            same output).
        """
        data = self.device.get_spectrum()
        self.has_overflow = self.device.has_overflow
        return data

    def integrate_spectrum(
        self, count: int
    ) -> Iterator[tuple[NDArray[np.floating], NDArray[np.floating]]]:
        """Record a spectrum by integrating over multiple measurements.

        Record an integrated spectrum using the spectrometer. This method acts
        as an iterator. Multiple measurements are taken and they are summed to
        increase the signal to noise ratio. After each measurement, the current
        dataset is yielded. The unit of intensity is arbitrary.

        If the `stopped` attribute of the class instance is set to `True` during
        the measurement, no further measurements are taken and the iterator will
        finish executing.

        Args:
            count: The number of measurements to perform.

        Yields:
            A tuple of `np.ndarrays` with wavelength, intensity data. The
            wavelengths are in nanometers but the intensity is in arbitrary
            units (but should be calibrated so that different devices yield the
            same output).
        """
        self.stopped = False
        self.has_overflow = False
        all_spectra = []
        for _ in range(count):
            wavelengths, intensities = self.device.get_spectrum()
            if self.device.has_overflow:
                self.has_overflow = True
            all_spectra.append(intensities)
            yield wavelengths, np.sum(all_spectra, axis=0)
            if self.stopped:
                break

    def set_integration_time(self, integration_time: int) -> None:
        """Set device integration time.

        The integration time is how long the device collects photons to measure
        the spectrum.

        Args:
            integration_time: The desired integration time in microseconds.
        """
        self.device.set_integration_time(integration_time)
