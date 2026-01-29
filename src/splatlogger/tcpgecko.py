# The MIT License (MIT)
#
# Copyright (c) 2015 wiiudev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Splatlogger (c) 2025 Shadow Doggo.
# This is a modified, stripped-down version of tcpgecko.py.

import socket
import struct


class TCPGecko:
    """Python library for use with TCPGecko."""

    def __init__(self, ip: str, *, port: int=7331, timeout: int=10) -> None:
        self._socket: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP)
        self._socket.settimeout(timeout)
        self._socket.connect((ip, port))

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

        ret: bytes = b""
        request: bytes
        status: bytes
        if length > 0x400:  # Read in chunks if length is over 400 bytes.
            for i in range(int(length / 0x400)):  # Number of blocks, ignores extra.
                self._socket.send(b"\x04")  # cmd_readmem
                request = struct.pack(">II", address, address + 0x400)
                self._socket.send(request)

                status = self._socket.recv(1)
                if status == b"\xbd":
                    ret += self._socket.recv(0x400)
                elif status == b"\xb0":
                    ret += b"\x00" * 0x400
                else:
                    raise TCPGeckoException("Unable to read memory.")

                address += 0x400
                length -= 0x400

            if length != 0:  # Now read the last little bit.
                self._socket.send(b"\x04")
                request = struct.pack(">II", address, address + length)
                self._socket.send(request)

                status = self._socket.recv(1)
                if status == b"\xbd":
                    ret += self._socket.recv(length)
                elif status == b"\xb0":
                    ret += b"\x00" * length
                else:
                    raise TCPGeckoException("Unable to read memory.")
        else:
            self._socket.send(b"\x04")
            request = struct.pack(">II", address, address + length)
            self._socket.send(request)

            status = self._socket.recv(1)
            if status == b"\xbd":
                ret += self._socket.recv(length)
            elif status == b"\xb0":
                ret += b"\x00" * length
            else:
                raise TCPGeckoException("Unable to read memory.")

        return ret

    def peek8(self, address: int, *, signed: bool=False) -> int:
        """Get an 8-bit integer value stored at the specified address."""

        return int.from_bytes(self.peek_raw(address + 0x3, length=0x1), byteorder="big", signed=signed)

    def peek16(self, address: int, *, signed: bool=False) -> int:
        """Get a 16-bit integer value stored at the specified address."""

        return int.from_bytes(self.peek_raw(address + 0x2, length=0x2), byteorder="big", signed=signed)

    def peek32(self, address: int, *, signed: bool=False) -> int:
        """Get a 32-bit integer value stored at the specified address."""

        return int.from_bytes(self.peek_raw(address, length=0x4), byteorder="big", signed=signed)

    def peek_float(self, address: int) -> float:
        """Get a floating point value stored at the specified address."""

        return struct.unpack(">f", self.peek_raw(address, length=0x4))[0]

    def read_string(self, address: int, *, strlen: int=1, encoding: str="utf-8") -> str:
        """Read a string of text starting at the specified address."""

        return self.peek_raw(address, length=strlen).decode(encoding)

    @staticmethod
    def _valid_range(address: int, length: int) -> bool:
        end_address: int = address + length

        if 0x01000000 <= address and end_address <= 0x01800000:
            return True
        elif 0x0E000000 <= address and end_address <= 0x10000000:  # Depends on the game.
            return True
        elif 0x10000000 <= address and end_address <= 0x50000000:  # Doesn't quite go to 5.
            return True
        elif 0xE0000000 <= address and end_address <= 0xE4000000:
            return True
        elif 0xE8000000 <= address and end_address <= 0xEA000000:
            return True
        elif 0xF4000000 <= address and end_address <= 0xF6800000:
            return True
        elif 0xF8000000 <= address and end_address <= 0xFB800000:
            return True
        elif 0xFFFE0000 <= address and end_address <= 0xFFFFFFFF:
            return True
        else:
            return False

    @staticmethod
    def _valid_access(address: int, length: int, access: str) -> bool:
        end_address: int = address + length

        if 0x01000000 <= address and end_address <= 0x01800000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0x0E000000 <= address and end_address <= 0x10000000:  # Depends on the game, may be EG 0x0E3.
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0x10000000 <= address and end_address <= 0x50000000:
            if access == "read":  return True
            if access == "write": return True
            return False
        elif 0xE0000000 <= address and end_address <= 0xE4000000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0xE8000000 <= address and end_address <= 0xEA000000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0xF4000000 <= address and end_address <= 0xF6000000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0xF6000000 <= address and end_address <= 0xF6800000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0xF8000000 <= address and end_address <= 0xFB000000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0xFB000000 <= address and end_address <= 0xFB800000:
            if access == "read":  return True
            if access == "write": return False
            return False
        elif 0xFFFE0000 <= address and end_address <= 0xFFFFFFFF:
            if access == "read":  return True
            if access == "write": return True
            return False
        else:
            return False


class TCPGeckoException(Exception):
    pass
