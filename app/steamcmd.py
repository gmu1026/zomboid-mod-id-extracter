import asyncio
from pathlib import Path

from .config import settings


async def download_workshop_item(workshop_id: str) -> Path:
    output_dir = Path(settings.workshop_dir) / workshop_id
    output_dir.mkdir(parents=True, exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        "docker", "run", "--rm",
        "-v", f"{output_dir}:/output",
        settings.steamcmd_image,
        "+force_install_dir", "/output",
        "+login", "anonymous",
        "+workshop_download_item", "108600", workshop_id,
        "+quit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    stdout, _ = await proc.communicate()
    output = stdout.decode(errors="replace")

    if proc.returncode != 0:
        raise RuntimeError(f"SteamCMD exited {proc.returncode}: {output[-1000:]}")

    mod_path = output_dir / "steamapps" / "workshop" / "content" / "108600" / workshop_id
    if not mod_path.exists():
        raise RuntimeError(f"Expected path not found after download: {mod_path}\n{output[-500:]}")

    return mod_path
