#!/usr/bin/env python3
"""Cleanup Home Assistant registries for the solax_local integration.

Usage:
  python scripts/clean_ha_solax_registry.py --config-dir /path/to/homeassistant

This script updates Home Assistant storage files while HA is stopped.
It removes:
  - devices with identifiers for the integration domain
  - entities attached to those devices
  - entities whose config entry belongs to the integration

It also backs up the original registry files before writing changes.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

INTEGRATION_DOMAIN = "solax_local"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def backup(path: Path) -> Path:
    backup_path = path.with_suffix(path.suffix + ".bak")
    if not backup_path.exists():
        backup_path.write_bytes(path.read_bytes())
    return backup_path


def find_integration_config_entry_ids(config_entries: dict[str, Any]) -> set[str]:
    return {
        entry_id
        for entry_id, entry in config_entries.get("data", {}).get("entries", {}).items()
        if entry.get("domain") == INTEGRATION_DOMAIN
    }


def find_devices_to_remove(device_registry: dict[str, Any], entry_ids: set[str]) -> set[str]:
    removed: set[str] = set()
    devices = device_registry.get("data", {}).get("devices", {})

    for device_id, device in devices.items():
        identifiers = device.get("identifiers", [])
        config_entries = set(device.get("config_entries", []))

        if any(str(identifier[0]) == INTEGRATION_DOMAIN for identifier in identifiers if isinstance(identifier, (list, tuple))):
            removed.add(device_id)
            continue

        if config_entries & entry_ids:
            removed.add(device_id)
            continue

    return removed


def cleanup_device_registry(device_registry: dict[str, Any], device_ids: set[str]) -> tuple[dict[str, Any], int]:
    if not device_ids:
        return device_registry, 0

    devices = device_registry.get("data", {}).get("devices", {})
    cleaned = {device_id: device for device_id, device in devices.items() if device_id not in device_ids}
    device_registry["data"]["devices"] = cleaned
    return device_registry, len(devices) - len(cleaned)


def cleanup_entity_registry(entity_registry: dict[str, Any], device_ids: set[str], entry_ids: set[str]) -> tuple[dict[str, Any], int]:
    entries = entity_registry.get("data", {}).get("entries", [])
    cleaned_entries = []
    removed = 0

    for entry in entries:
        entity_device_id = entry.get("device_id")
        entry_config_entries = set(entry.get("config_entries", []))
        entry_config_entry_id = entry.get("config_entry_id")

        if entity_device_id in device_ids:
            removed += 1
            continue

        if (entry_config_entry_id and entry_config_entry_id in entry_ids) or (entry_config_entries & entry_ids):
            removed += 1
            continue

        cleaned_entries.append(entry)

    entity_registry["data"]["entries"] = cleaned_entries
    return entity_registry, removed


def main() -> None:
    parser = argparse.ArgumentParser(description="Clean Home Assistant registries for solax_local.")
    parser.add_argument("--config-dir", required=True, help="Home Assistant configuration directory")
    args = parser.parse_args()

    config_dir = Path(args.config_dir).expanduser().resolve()
    storage_dir = config_dir / ".storage"

    device_path = storage_dir / "core.device_registry"
    entity_path = storage_dir / "core.entity_registry"
    config_entries_path = storage_dir / "core.config_entries"

    for path in (device_path, entity_path, config_entries_path):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    print(f"Using Home Assistant config dir: {config_dir}")
    print("Backing up registry files...")
    backup(device_path)
    backup(entity_path)
    backup(config_entries_path)

    config_entries = load_json(config_entries_path)
    entry_ids = find_integration_config_entry_ids(config_entries)
    print(f"Found {len(entry_ids)} solax_local config entry ID(s)")

    device_registry = load_json(device_path)
    device_ids = find_devices_to_remove(device_registry, entry_ids)
    print(f"Found {len(device_ids)} solax_local device ID(s) to remove")

    entity_registry = load_json(entity_path)
    device_registry, removed_devices = cleanup_device_registry(device_registry, device_ids)
    entity_registry, removed_entities = cleanup_entity_registry(entity_registry, device_ids, entry_ids)

    save_json(device_path, device_registry)
    save_json(entity_path, entity_registry)

    print(f"Removed {removed_devices} device(s) and {removed_entities} entity(ies)")
    print("Finished. Redémarrez Home Assistant après avoir remis les fichiers en place.")


if __name__ == "__main__":
    main()
