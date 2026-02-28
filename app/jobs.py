import json
import uuid

import aiosqlite

from .config import settings


async def create_job(workshop_ids: list[str]) -> dict:
    job_id = str(uuid.uuid4())
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "INSERT INTO jobs (id, workshop_ids) VALUES (?, ?)",
            (job_id, json.dumps(workshop_ids)),
        )
        await db.commit()
    return await get_job(job_id)


async def get_job(job_id: str) -> dict | None:
    async with aiosqlite.connect(settings.db_path) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)) as cur:
            row = await cur.fetchone()
            if not row:
                return None
            return {
                "id": row["id"],
                "status": row["status"],
                "workshop_ids": json.loads(row["workshop_ids"]),
                "progress": json.loads(row["progress"]),
                "result": json.loads(row["result"]) if row["result"] else None,
                "error": row["error"],
                "created_at": row["created_at"],
            }


async def update_job(job_id: str, **kwargs) -> None:
    for key in ("progress", "result", "workshop_ids"):
        if key in kwargs and not isinstance(kwargs[key], str):
            kwargs[key] = json.dumps(kwargs[key])

    sets = ", ".join(f"{k} = ?" for k in kwargs)
    values = list(kwargs.values()) + [job_id]

    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(f"UPDATE jobs SET {sets} WHERE id = ?", values)
        await db.commit()


async def append_progress(job_id: str, workshop_id: str, step: str, message: str) -> None:
    job = await get_job(job_id)
    if not job:
        return
    progress = job["progress"]
    progress.append({"workshop_id": workshop_id, "step": step, "message": message})
    await update_job(job_id, progress=progress)


async def get_workshop_cache(workshop_id: str) -> dict | None:
    async with aiosqlite.connect(settings.db_path) as db:
        async with db.execute(
            "SELECT data FROM workshop_cache WHERE workshop_id = ?", (workshop_id,)
        ) as cur:
            row = await cur.fetchone()
            return json.loads(row[0]) if row else None


async def save_workshop_cache(workshop_id: str, data: dict) -> None:
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "INSERT OR REPLACE INTO workshop_cache (workshop_id, data) VALUES (?, ?)",
            (workshop_id, json.dumps(data)),
        )
        await db.commit()
