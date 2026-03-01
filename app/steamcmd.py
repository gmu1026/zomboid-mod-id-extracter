import asyncio
import shutil
from pathlib import Path

from .config import settings

_MAX_RETRIES = 3
_RETRY_DELAY = 5  # seconds between retries


async def _run_steamcmd(host_output_dir: Path) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        "docker", "run", "--rm",
        "--network", "host",
        "-v", f"{host_output_dir}:/output",
        "--entrypoint", settings.steamcmd_entrypoint,
        settings.steamcmd_image,
        "+force_install_dir", "/output",
        "+login", "anonymous",
        "+workshop_download_item", "108600", host_output_dir.name,
        "+quit",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    stdout, _ = await proc.communicate()
    return proc.returncode, stdout.decode(errors="replace")


async def download_workshop_item(workshop_id: str) -> Path:
    # Container-side path for reading results after the SteamCMD container exits
    output_dir = Path(settings.workshop_dir) / workshop_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # Docker socket mounts are resolved by the HOST daemon, so volume paths
    # must be absolute HOST paths, not container-internal paths.
    host_output_dir = Path(settings.host_data_dir) / "workshop" / workshop_id

    last_error = ""
    for attempt in range(1, _MAX_RETRIES + 1):
        returncode, output = await _run_steamcmd(host_output_dir)

        if returncode != 0:
            last_error = f"SteamCMD exited {returncode} (attempt {attempt}/{_MAX_RETRIES}): {output[-1000:]}"
            if attempt < _MAX_RETRIES:
                # Clean partial output before retry
                shutil.rmtree(output_dir, ignore_errors=True)
                output_dir.mkdir(parents=True, exist_ok=True)
                await asyncio.sleep(_RETRY_DELAY)
            continue

        mod_path = output_dir / "steamapps" / "workshop" / "content" / "108600" / workshop_id
        if mod_path.exists():
            return mod_path

        last_error = f"Expected path not found after download (attempt {attempt}/{_MAX_RETRIES}): {mod_path}\n{output[-500:]}"
        if attempt < _MAX_RETRIES:
            shutil.rmtree(output_dir, ignore_errors=True)
            output_dir.mkdir(parents=True, exist_ok=True)
            await asyncio.sleep(_RETRY_DELAY)

    raise RuntimeError(last_error)
