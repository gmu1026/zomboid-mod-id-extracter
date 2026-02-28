from pathlib import Path
from typing import Any, Dict, List


def _parse_mod_info(path: Path) -> Dict[str, str]:
    info: Dict[str, str] = {}
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, value = line.partition("=")
                    info[key.strip()] = value.strip()
    except OSError:
        pass
    return info


def _find_maps(mod_root: Path) -> List[str]:
    maps: List[str] = []
    for maps_dir in mod_root.rglob("media/maps"):
        if maps_dir.is_dir():
            for entry in maps_dir.iterdir():
                if entry.is_dir():
                    maps.append(entry.name)
    return maps


def extract_mods(workshop_path: Path) -> List[Dict[str, Any]]:
    mods: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for mod_info_path in workshop_path.rglob("mod.info"):
        info = _parse_mod_info(mod_info_path)
        mod_id = info.get("id", "").strip()
        if not mod_id or mod_id in seen:
            continue
        seen.add(mod_id)

        requires_raw = info.get("require", "")
        requires = [
            r.strip().lstrip("\\")
            for r in requires_raw.split(";")
            if r.strip().lstrip("\\")
        ]

        mods.append({
            "mod_id": mod_id,
            "name": info.get("name", ""),
            "mod_version": info.get("modversion", ""),
            "requires": requires,
            "maps": _find_maps(mod_info_path.parent),
        })

    return mods


def build_server_config(workshop_ids: List[str], all_mods: List[Dict[str, Any]]) -> Dict[str, str]:
    mod_ids = [m["mod_id"] for m in all_mods]
    maps = list(dict.fromkeys(m for mod in all_mods for m in mod["maps"]))  # deduplicated, ordered

    config: Dict[str, str] = {
        "Mods": ";".join(f"\\{mid}" for mid in mod_ids),
        "WorkshopItems": ";".join(workshop_ids),
    }
    if maps:
        config["Map"] = ";".join(maps) + ";Muldraugh, KY"

    return config
