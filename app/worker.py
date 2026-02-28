import asyncio
import shutil
from pathlib import Path

from .config import settings
from .jobs import append_progress, get_job, get_workshop_cache, save_workshop_cache, update_job
from .mod_parser import build_server_config, extract_mods
from .steamcmd import download_workshop_item

job_queue: asyncio.Queue = asyncio.Queue()


async def _process_job(job_id: str) -> None:
    job = await get_job(job_id)
    workshop_ids: list[str] = job["workshop_ids"]
    all_items: list[dict] = []

    for workshop_id in workshop_ids:
        # Return cached result without downloading again
        cached = await get_workshop_cache(workshop_id)
        if cached:
            await append_progress(job_id, workshop_id, "cached", "Found in cache")
            all_items.append(cached)
            continue

        # Download via SteamCMD in Docker
        await append_progress(job_id, workshop_id, "downloading", f"Downloading {workshop_id}...")
        try:
            mod_path = await download_workshop_item(workshop_id)
        except Exception as exc:
            await append_progress(job_id, workshop_id, "error", f"Download failed: {exc}")
            continue

        # Parse mod.info files
        await append_progress(job_id, workshop_id, "parsing", "Parsing mod files...")
        try:
            mods = extract_mods(mod_path)
        except Exception as exc:
            await append_progress(job_id, workshop_id, "error", f"Parse failed: {exc}")
            shutil.rmtree(Path(settings.workshop_dir) / workshop_id, ignore_errors=True)
            continue

        item = {
            "workshop_id": workshop_id,
            "mods": mods,
            "server_config": build_server_config([workshop_id], mods),
        }
        await save_workshop_cache(workshop_id, item)
        all_items.append(item)

        # Remove downloaded files after saving to DB
        shutil.rmtree(Path(settings.workshop_dir) / workshop_id, ignore_errors=True)
        await append_progress(job_id, workshop_id, "completed", "Done")

    all_mods = [m for item in all_items for m in item["mods"]]
    all_wids = [item["workshop_id"] for item in all_items]

    result = {
        "items": all_items,
        "combined_config": build_server_config(all_wids, all_mods),
    }
    await update_job(job_id, status="completed", result=result)


async def start_worker() -> None:
    while True:
        job_id = await job_queue.get()
        try:
            await update_job(job_id, status="processing")
            await _process_job(job_id)
        except Exception as exc:
            await update_job(job_id, status="failed", error=str(exc))
        finally:
            job_queue.task_done()
