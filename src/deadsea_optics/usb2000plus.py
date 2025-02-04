from dataclasses import dataclass

import libusb_package
import numpy as np
import plotext as plt
import usb.core
from numpy.typing import NDArray


class DeviceNotFoundError(Exception):
    """Raised when no compatible device is connected."""


class AccessError(Exception):
    """Raised when the device cannot be accessed."""


class SpectrumTimeOutError(Exception):
    """Raised when a timeout occurs while reading a spectrum."""


@dataclass
class DeviceConfiguration:
    serial_number: str
    wavelength_calibration_coefficients: list[float]
    stray_light_constant: float
    nonlinearity_correction_coefficients: list[float]
    polynomial_order_nonlinearity_calibration: int
    optical_bench: str
    device_configuration: str
    saturation_level: np.uint16


class OceanOpticsUSB2000Plus:
    _integration_time: int = 100_000

    _config: DeviceConfiguration

    _ENDPOINT_OUT = 0x01
    _ENDPOINT_IN_CMD = 0x81
    _ENDPOINT_IN_SPECTRUM = 0x82

    has_overflow: bool = False

    def __init__(self) -> None:
        self.device = libusb_package.find(idVendor=0x2457, idProduct=0x101E)
        if self.device is None:
            raise DeviceNotFoundError()

        # Configuration is set automatically and setting it explicitly, as
        # required by the PyUSB documentation, messes up the device on Linux. On
        # that OS the first packet on each IN endpoint disappears into the void
        # resulting in timeouts. This happens _only_ on the second run of the
        # script _after_ an _odd_ number of operations in the previous run. This
        # is really, really, weird.
        # self.device.set_configuration()

        # There may be stale data from incompleted reads in the buffers.
        try:
            self.clear_buffers()
        except NotImplementedError:
            # Device was opened, but is not functional
            raise DeviceNotFoundError()
        except usb.core.USBError as exc:
            raise AccessError(exc)

        # Initialize device
        self.device.write(self._ENDPOINT_OUT, b"\x01")
        # Set default integration time
        self.set_integration_time(self._integration_time)

        self.set_shutdown_mode()
        self._config = self.get_configuration()

    def set_integration_time(self, integration_time: int) -> None:
        """Set device integration time.

        The integration time is how long the device collects photons to measure
        the spectrum.

        Args:
            integration_time: The desired integration time in microseconds.
        """
        self.device.write(
            self._ENDPOINT_OUT, b"\x02" + int(integration_time).to_bytes(4, "little")
        )
        self._integration_time = integration_time

    def get_integration_time(self) -> int:
        """Return device integration time.

        The integration time is how long the device collects photons to measure
        the spectrum.

        Returns:
            The integration time in microseconds as an integer value.
        """
        return self._integration_time

    def clear_buffers(self) -> None:
        """Clear buffers by reading from both IN endpoints."""
        for endpoint in self._ENDPOINT_IN_CMD, self._ENDPOINT_IN_SPECTRUM:
            try:
                self.device.read(
                    endpoint=endpoint, size_or_buffer=1_000_000, timeout=100
                )
            except usb.core.USBTimeoutError:
                pass

    def get_configuration(self) -> DeviceConfiguration:
        """Get all configuration parameters.

        Returns:
            DeviceConfiguration: the configuration parameters.
        """
        serial = self._query_configuration_parameter(0)
        wavelength = [
            float(self._query_configuration_parameter(param)) for param in range(1, 5)
        ]
        stray_light = float(self._query_configuration_parameter(5))
        nonlinearity = [
            float(self._query_configuration_parameter(param)) for param in range(6, 14)
        ]
        polynomial = int(self._query_configuration_parameter(14))
        bench = self._query_configuration_parameter(15)
        dev_config = self._query_configuration_parameter(16)
        saturation_level = self._get_saturation_level()

        return DeviceConfiguration(
            serial_number=serial,
            wavelength_calibration_coefficients=wavelength,
            stray_light_constant=stray_light,
            nonlinearity_correction_coefficients=nonlinearity,
            polynomial_order_nonlinearity_calibration=polynomial,
            optical_bench=bench,
            device_configuration=dev_config,
            saturation_level=saturation_level,
        )

    def _query_configuration_parameter(self, index: int) -> str:
        """Query a configuration parameter.

        The indexes can be looked up in the data sheet. End users should call
        the `get_configuration()` method.

        Args:
            index: the requested configuration index.

        Returns:
            A string with the configuration value.
        """
        command = b"\x05" + index.to_bytes(1)
        self.device.write(self._ENDPOINT_OUT, command)
        value: bytes = self.device.read(self._ENDPOINT_IN_CMD, 17).tobytes()
        assert value[:2] == command
        # ignore everything after the first \x00 byte in the data range
        data = value[2 : value.find(b"\x00", 2)]
        return data.decode()

    def _get_saturation_level(self) -> np.uint16:
        """Get device saturation level.

        Returns:
            The saturation level as an integer.
        """
        command = b"\x05\x11"
        self.device.write(self._ENDPOINT_OUT, command)
        data: bytes = self.device.read(self._ENDPOINT_IN_CMD, 17).tobytes()
        assert data[:2] == command
        return np.uint16(np.frombuffer(data[6:8], dtype=np.uint16)[0])

    def get_spectrum(self) -> tuple[NDArray[np.floating], NDArray[np.floating]]:
        """Record a calibrated spectrum.

        Returns:
            A tuple of `np.ndarrays` with wavelength, intensity data. The
            wavelengths are in nanometers but the intensity is in arbitrary
            units (but should be calibrated so that different devices yield the
            same output). The maximum intensity value is 65535, so you can check
            that to see if the device was saturated. This does _not_mean that
            the resolution of the intensity 16 bits. The number of possible
            different intensity levels is the so-called 'saturation level'.
        """
        data = self.get_raw_spectrum()
        x = np.arange(len(data), dtype=np.float64)
        c = self._config.wavelength_calibration_coefficients
        x = c[0] + c[1] * x + c[2] * x**2 + c[3] * x**3
        # scale data, described as 'autonulling' in the manual.
        intensity = data * (65535 / self._config.saturation_level)
        self.has_overflow = bool(intensity.max() == 65535)
        return x[20:], intensity[20:]

    def get_raw_spectrum(self) -> NDArray[np.uint16]:
        """Record a raw spectrum, including dark pixels.

        Returns:
            A tuple of `np.ndarrays` with wavelength, intensity data. The
            wavelengths are in pixels and the intensity is in arbitrary
            uncalibrated units.
        """
        self.device.write(self._ENDPOINT_OUT, b"\x09")
        # Don't sleep, because the device will automatically acquire two
        # additional spectra which will be available sooner than acquiring a
        # fresh one.
        # Set timeout for measurement to complete, integration time is in
        # microseconds, timeout is in milliseconds. Add 100 ms (default timeout)
        # to be sure.
        timeout = self._integration_time // 1_000 + 100
        packets = []
        for _ in range(8):
            try:
                packets.append(
                    self.device.read(self._ENDPOINT_IN_SPECTRUM, 512, timeout).tobytes()
                )
                # after waiting for the first packet, next timeout can be short
                timeout = 100
            except usb.core.USBTimeoutError:
                break
        else:
            packets.append(
                self.device.read(self._ENDPOINT_IN_SPECTRUM, 1, 100).tobytes()
            )
        assert packets[-1][-1] == 0x69

        data = b"".join(packets[:-1])
        return np.frombuffer(data, dtype=np.uint16)

    def set_shutdown_mode(self) -> None:
        """Set shutdown (low power) mode."""
        self.device.write(self._ENDPOINT_OUT, b"\x04\x00\x00")


if __name__ == "__main__":
    dev = OceanOpticsUSB2000Plus()

    x, data = dev.get_spectrum()
    plt.clf()
    plt.plot(x, [int(y) for y in data])
    plt.show()

    print(f"{dev.has_overflow=}")
    print(dev.get_configuration())
