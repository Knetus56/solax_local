from __future__ import annotations

import base64
import logging
from typing import Any
from urllib import error, request

_LOGGER = logging.getLogger(__name__)


def crc16(data: bytes, length: int) -> tuple[int, int]:
    poly = 0x8005
    reg = 0x0000
    mask = 0xFFFF

    for index in range(length):
        reg ^= (data[index] << 8) & 0xFFFF
        for _ in range(8):
            if reg & 0x8000:
                reg = ((reg << 1) ^ poly) & mask
            else:
                reg = (reg << 1) & mask

    return (reg >> 8) & 0xFF, reg & 0xFF


def _offline_state(host: str, serial: str, mode: str = "Offline") -> dict[str, Any]:
    return {
        "online": False,
        "status": 0,
        "mode": mode,
        "mptt1": 0,
        "mptt2": 0,
        "mptt_total": 0,
        "prod_auj": 0.0,
        "prod_total": 0.0,
        "temp": 0,
        "ip": host,
        "num_inverter": serial,
    }


def build_sys_packet(inv: str, on: bool) -> str:
    buff = bytearray(76)
    buff[0] = 0x24
    buff[1] = 0x24
    buff[2] = 0x4C
    buff[4] = 0x08
    buff[5] = 0x03
    buff[6] = 0x01
    buff[7] = 0x1D
    buff[29] = 0x04
    buff[62] = 0x0A
    buff[64] = 0x02
    buff[65] = 0x07
    buff[67] = 0x01
    buff[68] = 0x61
    buff[70] = 0x02
    buff[72] = 0x01 if on else 0x00

    for index in range(14):
        buff[8 + index] = ord(inv[index]) if index < len(inv) else 0x00

    b1, b2 = crc16(buff, len(buff) - 2)
    buff[74] = b1
    buff[75] = b2

    _LOGGER.debug("build_sys_packet: serial=%s on=%s crc=(%02X,%02X)", inv, on, b1, b2)
    return base64.b64encode(bytes(buff)).decode("ascii")


def build_data_packet(inv: str) -> str:
    buff = bytearray(69)
    buff[0] = 0x24
    buff[1] = 0x24
    buff[2] = 0x45
    buff[3] = 0x00
    buff[4] = 0x08
    buff[5] = 0x04
    buff[6] = 0x01
    buff[7] = 0x1C
    buff[64] = 0x01

    for index in range(14):
        buff[8 + index] = ord(inv[index]) if index < len(inv) else 0x00

    b1, b2 = crc16(buff, len(buff) - 2)
    buff[67] = b1
    buff[68] = b2

    _LOGGER.debug("build_data_packet: serial=%s crc=(%02X,%02X)", inv, b1, b2)
    return base64.b64encode(bytes(buff)).decode("ascii")


def _u16(data: bytes, offset: int) -> int:
    return ((data[offset + 1] << 8) | data[offset]) & 0xFFFF


def _u32(data: bytes, offset: int) -> int:
    return (
        ((data[offset + 3] << 24) | (data[offset + 2] << 16) | (data[offset + 1] << 8) | data[offset])
        & 0xFFFFFFFF
    )


def _decode_payload(payload: str) -> bytes:
    return base64.b64decode(payload)


def parse_data(payload: str, host: str, serial: str) -> dict[str, Any]:
    decoded = _decode_payload(payload)
    _LOGGER.debug("parse_data: decoded length=%d", len(decoded))

    if len(decoded) < 112:
        _LOGGER.debug("parse_data: payload too short (%d bytes), marking offline", len(decoded))
        return _offline_state(host, serial, "Unknown")

    serial_bytes = decoded[8:22]
    serial_inverter = serial_bytes.decode("ascii", errors="ignore")
    _LOGGER.debug("parse_data: packet type=0x%02X serial_in_packet=%r expected=%r", decoded[2], serial_inverter, serial)

    if decoded[2] != 0x70 or serial_inverter != serial:
        _LOGGER.debug("parse_data: packet mismatch (type=0x%02X serial=%r), marking offline", decoded[2], serial_inverter)
        return _offline_state(host, serial, "Unknown")

    mode = _u16(decoded, 90)
    status = 1 if mode == 2 else 0
    mode_names = {0: "WaitMode", 1: "CheckMode", 2: "NormalMode"}
    mode_name = mode_names.get(mode, "Unknown")

    result = {
        "online": True,
        "status": status,
        "mode": mode_name,
        "mptt1": _u16(decoded, 86),
        "mptt2": _u16(decoded, 88),
        "mptt_total": _u16(decoded, 74),
        "prod_auj": round(_u16(decoded, 96) / 10.0, 2),
        "prod_total": round(_u32(decoded, 92) / 10.0, 2),
        "temp": _u16(decoded, 100),
        "ip": host,
        "num_inverter": serial,
    }
    _LOGGER.debug("parse_data: result=%s", result)
    return result


def fetch_inverter_state(host: str, serial: str) -> dict[str, Any]:
    payload = build_data_packet(serial)
    req = request.Request(f"http://{host}", data=payload.encode("ascii"), method="POST")
    req.add_header("Content-Type", "application/octet-stream")

    _LOGGER.debug("fetch_inverter_state: querying host=%s serial=%s", host, serial)
    try:
        with request.urlopen(req, timeout=5) as response:
            body = response.read().decode("ascii", errors="ignore")
            _LOGGER.debug("fetch_inverter_state: HTTP %d body_len=%d", response.status, len(body))
            if response.status == 200 and len(body) >= 150:
                return parse_data(body.replace("\n", ""), host, serial)
            _LOGGER.debug("fetch_inverter_state: response too short or bad status, marking offline")
    except (error.URLError, error.HTTPError, TimeoutError, ValueError) as exc:
        _LOGGER.debug("fetch_inverter_state: request failed: %s", exc)

    return _offline_state(host, serial)


def set_inverter_state(host: str, serial: str, on: bool) -> bool:
    payload = build_sys_packet(serial, on)
    req = request.Request(f"http://{host}", data=payload.encode("ascii"), method="POST")
    req.add_header("Content-Type", "application/octet-stream")

    _LOGGER.debug("set_inverter_state: host=%s serial=%s on=%s", host, serial, on)
    try:
        with request.urlopen(req, timeout=5) as response:
            success = response.status == 200
            _LOGGER.debug("set_inverter_state: HTTP %d success=%s", response.status, success)
            return success
    except (error.URLError, error.HTTPError, TimeoutError, ValueError) as exc:
        _LOGGER.debug("set_inverter_state: request failed: %s", exc)
        return False
