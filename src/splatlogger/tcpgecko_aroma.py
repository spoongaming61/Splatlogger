# Splatlogger (c) 2025 Shadow Doggo.

from .tcpgecko import TCPGecko, TCPGeckoException


class TCPGeckoAroma(TCPGecko):
    """Extends pyGecko to add TCPGeckoAroma support."""

    def __init__(self, ip: str, *, port: int=7332, timeout: int=10) -> None:
        super().__init__(ip, port=port, timeout=timeout)

    def peek_raw(self, address: int, *, length: int) -> bytes:
        """Read raw memory starting at address and ending at address + length.
        Returns a bytes object.
        """

        if length == 0:
            raise TCPGeckoException("Reading memory requires a length (# of bytes).")

        if not self._valid_range(address, length):
            raise TCPGeckoException(f"Address 0x{address:X} is outside the valid range.")

        if not self._valid_access(address, length, access="read"):
            raise TCPGeckoException(f"Cannot read from address 0x{address:X}.")

        value: int
        ret: bytes = b""
        request: bytes
        response: bytes

        # peekmultiple could work as well, but the implementation would
        # have to be a lot more complicated to allow for arbitrary lengths.
        if length > 4:
            for i in range((length // 4) + 1):
                if length > 4:
                    request = bytes(f"peek -t u32 -a 0x{address:X}", "utf-8")
                    self._socket.send(request)

                    response = self._socket.recv(32)
                    value = int(response.decode("utf-8"))
                    ret += value.to_bytes(length=4, byteorder="big")

                    address += 0x4
                    length -= 0x4
                else:
                    request = bytes(f"peek -t u32 -a 0x{address:X}", "utf-8")
                    self._socket.send(request)

                    response = self._socket.recv(32)
                    value = int(response.decode("utf-8"))
                    ret += value.to_bytes(length=4, byteorder="big")[:length]
        else:
            request = bytes(f"peek -t u32 -a 0x{address:X}", "utf-8")
            self._socket.send(request)

            response = self._socket.recv(32)
            value = int(response.decode("utf-8"))
            ret = value.to_bytes(4, byteorder="big")[:length]

        return ret

    def peek8(self, address: int, *, signed: bool=False) -> int:
        """Get an 8-bit integer value stored at the specified address."""

        if not self._valid_range(address, length=0x1):
            raise TCPGeckoException(f"Address 0x{address:X} is outside the valid range.")

        if not self._valid_access(address, length=0x1, access="read"):
            raise TCPGeckoException(f"Cannot read from address 0x{address:X}.")

        request = bytes(f"peek -t u8 -a 0x{address + 0x3:X}", "utf-8")
        self._socket.send(request)

        response = self._socket.recv(8)
        val = int(response.decode("utf-8"))
        if signed and val >= 2 ** 31:  # Rough unsigned to signed conversion.
            return val - 2 ** 32

        return val

    def peek16(self, address: int, *, signed: bool=False) -> int:
        """Get a 16-bit integer value stored at the specified address."""

        if not self._valid_range(address, length=0x2):
            raise TCPGeckoException(f"Address 0x{address:X} is outside the valid range.")

        if not self._valid_access(address, length=0x2, access="read"):
            raise TCPGeckoException(f"Cannot read from address 0x{address:X}.")

        request = bytes(f"peek -t u16 -a 0x{address + 0x2:X}", "utf-8")
        self._socket.send(request)

        response = self._socket.recv(16)
        val = int(response.decode("utf-8"))
        if signed and val >= 2 ** 31:
            return val - 2 ** 32

        return val

    def peek32(self, address: int, *, signed: bool=False) -> int:
        """Get a 32-bit integer value stored at the specified address."""

        if not self._valid_range(address, length=0x4):
            raise TCPGeckoException(f"Address 0x{address:X} is outside the valid range.")

        if not self._valid_access(address, length=0x4, access="read"):
            raise TCPGeckoException(f"Cannot read from address 0x{address:X}.")

        request = bytes(f"peek -t u32 -a 0x{address:X}", "utf-8")
        self._socket.send(request)

        response = self._socket.recv(32)
        val = int(response.decode("utf-8"))
        if signed and val >= 2 ** 31:
            return val - 2 ** 32

        return val

    def peek_float(self, address: int) -> float:
        """Get a floating point value stored at the specified address."""

        if not self._valid_range(address, length=0x4):
            raise TCPGeckoException(f"Address 0x{address:X} is outside the valid range.")

        if not self._valid_access(address, length=0x4, access="read"):
            raise TCPGeckoException(f"Cannot read from address 0x{address:X}.")

        request = bytes(f"peek -t f32 -a 0x{address:X}", "utf-8")
        self._socket.send(request)

        response = self._socket.recv(32)
        return float(response.decode("utf-8"))
