from typing import Iterator

import numpy as np
from numpy.typing import NDArray

from ocean_optics.usb2000plus import DeviceNotFoundError, OceanOpticsUSB2000Plus

__all__ = ["DeviceNotFoundError", "SpectroscopyExperiment"]


class SpectroscopyExperiment:
    stopped = True

    def __init__(self) -> None:
        self.device = OceanOpticsUSB2000Plus()

    def get_spectrum(self) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        """Record a spectrum.

        Returns:
            A tuple of `np.ndarrays` with wavelength, intensity data. The
            wavelengths are in nanometers but the intensity is in arbitrary
            units (but should be calibrated so that different devices yield the
            same output).
        """
        return self.device.get_spectrum()

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
        all_spectra = []
        for _ in range(count):
            wavelengths, intensities = self.device.get_spectrum()
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
