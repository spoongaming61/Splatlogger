# Splatlogger (c) 2025 Shadow Doggo.

from tcpgecko import *


class TCPGeckoAroma(TCPGecko):
    """Extends pyGecko to add TCPGeckoAroma support."""

    def __init__(self, ip: str, port: int, timeout: int) -> None:
        super().__init__(ip, port, timeout)

    def readmem(self, address: int, length: int) -> bytes:
        """Read memory at starting at address and ending at address + length.
        Returns a bytes object.
        """

        value: int
        ret: bytes = b""
        request: bytes
        response: bytes

        # Read in chunks if the length is over 4 bytes.
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
            # Always read as u32.
            # The plugin supports reading different data types with bit shifting
            # but I'm doing it this way for compatibility.
            request = bytes(f"peek -t u32 -a 0x{address:X}", "utf-8")
            self._socket.send(request)

            response = self._socket.recv(32)
            # The plugin sends the data as an integer value encoded into a string.
            # I'm converting it to int and then to a bytes object.
            value = int(response.decode("utf-8"))
            ret = value.to_bytes(4, byteorder="big")[:length]  # Slice the data to the desired length.

        return ret
