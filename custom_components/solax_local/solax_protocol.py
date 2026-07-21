from __future__ import annotations

import base64
from typing import Any
from urllib import error, request


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
    if len(decoded) < 112:
        return {
            "online": False,
            "status": 0,
            "mode": "Unknown",
            "mptt1": 0,
            "mptt2": 0,
            "mptt_total": 0,
            "prod_auj": 0.0,
            "prod_total": 0.0,
            "temp": 0,
            "ip": host,
            "num_inverter": serial,
        }

    serial_bytes = decoded[8:22]
    serial_inverter = serial_bytes.decode("ascii", errors="ignore")
    if decoded[2] != 0x70 or serial_inverter != serial:
        return {
            "online": False,
            "status": 0,
            "mode": "Unknown",
            "mptt1": 0,
            "mptt2": 0,
            "mptt_total": 0,
            "prod_auj": 0.0,
            "prod_total": 0.0,
            "temp": 0,
            "ip": host,
            "num_inverter": serial,
        }

    mode = _u16(decoded, 90)
    if mode == 2:
        status = 1
    else:
        status = 0

    if mode == 0:
        mode_name = "WaitMode"
    elif mode == 1:
        mode_name = "CheckMode"
    elif mode == 2:
        mode_name = "NormalMode"
    else:
        mode_name = "Unknown"

    return {
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


def fetch_inverter_state(host: str, serial: str) -> dict[str, Any]:
    payload = build_data_packet(serial)
    req = request.Request(f"http://{host}", data=payload.encode("ascii"), method="POST")
    req.add_header("Content-Type", "application/octet-stream")

    try:
        with request.urlopen(req, timeout=5) as response:
            body = response.read().decode("ascii", errors="ignore")
            if response.status == 200 and len(body) >= 150:
                return parse_data(body.replace("\n", ""), host, serial)
    except (error.URLError, error.HTTPError, TimeoutError, ValueError):
        pass

    return {
        "online": False,
        "status": 0,
        "mode": "Offline",
        "mptt1": 0,
        "mptt2": 0,
        "mptt_total": 0,
        "prod_auj": 0.0,
        "prod_total": 0.0,
        "temp": 0,
        "ip": host,
        "num_inverter": serial,
    }


def set_inverter_state(host: str, serial: str, on: bool) -> bool:
    payload = build_sys_packet(serial, on)
    req = request.Request(f"http://{host}", data=payload.encode("ascii"), method="POST")
    req.add_header("Content-Type", "application/octet-stream")

    try:
        with request.urlopen(req, timeout=5) as response:
            return response.status == 200
    except (error.URLError, error.HTTPError, TimeoutError, ValueError):
        return False
