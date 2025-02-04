import libusb_package
import numpy as np
import plotext as plt
import usb.core
from numpy.typing import NDArray

from deadsea_optics.usb2000plus import (
    AccessError,
    DeviceNotFoundError,
    OceanOpticsUSB2000Plus,
    SpectrumTimeOutError,
)


class OceanOpticsUSB2000(OceanOpticsUSB2000Plus):
    _ENDPOINT_OUT = 0x02
    _ENDPOINT_IN_CMD = 0x87
    _ENDPOINT_IN_SPECTRUM = 0x82

    def __init__(self) -> None:
        self.device = libusb_package.find(idVendor=0x2457, idProduct=0x1002)
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

        self._config = self.get_configuration()

    def set_integration_time(self, integration_time: int) -> None:
        """Set device integration time.

        The integration time is how long the device collects photons to measure
        the spectrum.

        Args:
            integration_time: The desired integration time in microseconds.
        """
        # This device only accepts the integration time in _milli_seconds
        self.device.write(
            self._ENDPOINT_OUT,
            b"\x02" + int(integration_time // 1000).to_bytes(2, "little"),
        )
        self._integration_time = integration_time

    def _get_saturation_level(self) -> np.uint16:
        """Get device saturation level.

        Returns:
            The saturation level as an integer.
        """
        return np.uint16(4095)

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
        for _ in range(64):
            try:
                packets.append(
                    self.device.read(self._ENDPOINT_IN_SPECTRUM, 64, timeout).tobytes()
                )
                # after waiting for the first packet, next timeout can be short
                timeout = 100
            except usb.core.USBTimeoutError:
                break
        else:
            packets.append(
                self.device.read(self._ENDPOINT_IN_SPECTRUM, 1, 100).tobytes()
            )
        try:
            assert packets[-1][-1] == 0x69
        except IndexError:
            # there was no data at all
            raise SpectrumTimeOutError("No data was received.")

        pixels = []
        for lsb_packet, msb_packet in zip(packets[0:-1:2], packets[1:-1:2]):
            for lsb, msb in zip(lsb_packet, msb_packet):
                pixels.append(bytes((lsb, msb)))

        data = b"".join(pixels[:-1])
        return np.frombuffer(data, dtype=np.uint16)


if __name__ == "__main__":
    dev = OceanOpticsUSB2000()

    x, data = dev.get_spectrum()
    plt.clf()
    plt.plot(x, [int(y) for y in data])
    plt.show()

    print(f"{dev.has_overflow=}")
    print(dev.get_configuration())
