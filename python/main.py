from __future__ import annotations

import socket
from enum import Enum


DEFAULT_ADDRESS = "192.168.3.7"
DEFAULT_PORT = 8887
DEFAULT_UNIT_ID = 1
DEFAULT_TIMEOUT = 2.0

DEFAULT_FREQUENCY = 300
DEFAULT_AMPLITUDE = 200

REG_CONTROL = 4192
REG_FAULTS = 8194
REG_LIGHT1_BRIGHTNESS = 4099

BIT_MOTION_ENABLE = 1 << 4
BIT_LIGHT1_ENABLE = 1 << 5
BIT_CLEAR_FAULTS = 1 << 15
MOTION_BITS_MASK = 0x000F


class MotionMode(Enum):
    MoveRight = (1, 4166, 4167)
    MoveLeft = (2, 4168, 4169)
    MoveForward = (3, 4170, 4171)
    MoveBackward = (4, 4172, 4173)
    MoveUpperRight = (5, 4174, 4175)
    MoveUpperLeft = (6, 4176, 4177)
    MoveLowerLeft = (7, 4178, 4179)
    MoveLowerRight = (8, 4180, 4181)
    Bounce = (9, 4182, 4183)
    CenterHorizontal = (10, 4184, 4185)
    CenterVertical = (11, 4186, 4187)
    CenterDiagonalUp = (12, 4188, 4189)
    CenterDiagonalDown = (13, 4190, 4191)

    @property
    def motion_code(self) -> int:
        return self.value[0]

    @property
    def frequency_register(self) -> int:
        return self.value[1]

    @property
    def amplitude_register(self) -> int:
        return self.value[2]


class VibrationTable:
    def __init__(
        self,
        address: str = DEFAULT_ADDRESS,
        port: int = DEFAULT_PORT,
        unit_id: int = DEFAULT_UNIT_ID,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.address = address
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.control_word = 0
        self.transaction = 1

    @classmethod
    def can_connect(
        cls,
        address: str = DEFAULT_ADDRESS,
        port: int = DEFAULT_PORT,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> bool:
        try:
            with socket.create_connection((address, port), timeout=timeout):
                return True
        except OSError:
            return False

    def start_vibration(self, mode: MotionMode) -> None:
        self.start_vibration_with_params(mode, DEFAULT_FREQUENCY, DEFAULT_AMPLITUDE)

    def start_vibration_with_params(self, mode: MotionMode, frequency: int, amplitude: int) -> None:
        self._validate_frequency(frequency)
        self._validate_amplitude(amplitude)

        self._write_register(mode.frequency_register, frequency)
        self._write_register(mode.amplitude_register, amplitude)

        self.control_word &= ~MOTION_BITS_MASK
        self.control_word |= mode.motion_code
        self.control_word |= BIT_MOTION_ENABLE
        self._write_register(REG_CONTROL, self.control_word)

    def stop_vibration(self) -> None:
        self.control_word &= ~BIT_MOTION_ENABLE
        self.control_word &= ~MOTION_BITS_MASK
        self._write_register(REG_CONTROL, self.control_word)

    def light_on(self, brightness: int) -> None:
        self._validate_brightness(brightness)

        self._write_register(REG_LIGHT1_BRIGHTNESS, brightness)
        self.control_word |= BIT_LIGHT1_ENABLE
        self._write_register(REG_CONTROL, self.control_word)

    def light_off(self) -> None:
        self.control_word &= ~BIT_LIGHT1_ENABLE
        self._write_register(REG_CONTROL, self.control_word)

    def read_faults(self) -> int:
        return self._read_input_register(REG_FAULTS)

    def has_fault(self) -> bool:
        return self.read_faults() != 0

    def clear_faults(self) -> None:
        self._write_register(REG_CONTROL, self.control_word | BIT_CLEAR_FAULTS)

    def _write_register(self, register: int, value: int) -> None:
        payload = register.to_bytes(2, "big") + value.to_bytes(2, "big")
        response = self._request(0x06, payload)

        if len(response) < 12 or response[7] != 0x06:
            raise RuntimeError(f"invalid write response: {response.hex(' ')}")

    def _read_input_register(self, register: int) -> int:
        payload = register.to_bytes(2, "big") + (1).to_bytes(2, "big")
        response = self._request(0x04, payload)

        if len(response) < 11 or response[7] != 0x04 or response[8] != 2:
            raise RuntimeError(f"invalid read response: {response.hex(' ')}")

        return int.from_bytes(response[9:11], "big")

    def _request(self, function: int, payload: bytes) -> bytes:
        transaction = self._next_transaction()
        pdu = bytes([function]) + payload
        mbap = (
            transaction.to_bytes(2, "big")
            + (0).to_bytes(2, "big")
            + (len(pdu) + 1).to_bytes(2, "big")
            + bytes([self.unit_id])
        )
        frame = mbap + pdu

        with socket.create_connection((self.address, self.port), timeout=self.timeout) as stream:
            stream.settimeout(self.timeout)
            stream.sendall(frame)

            header = self._recv_exact(stream, 7)
            response_transaction = int.from_bytes(header[0:2], "big")
            protocol_id = int.from_bytes(header[2:4], "big")
            response_len = int.from_bytes(header[4:6], "big")

            if response_transaction != transaction or protocol_id != 0 or response_len == 0:
                raise RuntimeError(f"invalid response header: {header.hex(' ')}")

            body = self._recv_exact(stream, response_len - 1)
            response = header + body

        if len(response) >= 9 and response[7] == (function | 0x80):
            raise RuntimeError(f"modbus exception {response[8]}: {response.hex(' ')}")

        return response

    def _next_transaction(self) -> int:
        current = self.transaction
        self.transaction = (self.transaction + 1) & 0xFFFF
        return current

    @staticmethod
    def _recv_exact(stream: socket.socket, size: int) -> bytes:
        chunks = bytearray()
        while len(chunks) < size:
            chunk = stream.recv(size - len(chunks))
            if not chunk:
                raise RuntimeError("connection closed while reading response")
            chunks.extend(chunk)
        return bytes(chunks)

    @staticmethod
    def _validate_frequency(value: int) -> None:
        if not 100 <= value <= 4000:
            raise ValueError("frequency must be 100..=4000, unit is 0.1Hz")

    @staticmethod
    def _validate_amplitude(value: int) -> None:
        if not 0 <= value <= 1000:
            raise ValueError("amplitude must be 0..=1000, unit is 0.1%")

    @staticmethod
    def _validate_brightness(value: int) -> None:
        if not 0 <= value <= 1000:
            raise ValueError("brightness must be 0..=1000, unit is 0.1%")
