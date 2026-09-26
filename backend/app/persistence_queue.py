import asyncio
from dataclasses import dataclass

from app.crdt import CRDTDocument
from app.crdt_persistence import persist_document
from app.database import SessionLocal
from app.models import CodeFile


@dataclass
class PersistenceJob:
    file_id: int
    user_id: int
    content: str


class PersistenceQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.worker_task = None

    async def start(self):
        if self.worker_task is None or self.worker_task.done():
            self.worker_task = asyncio.create_task(self._worker())

    async def stop(self):
        if self.worker_task is None:
            return

        await self.queue.join()

        self.worker_task.cancel()

        try:
            await self.worker_task
        except asyncio.CancelledError:
            pass

        self.worker_task = None

    async def enqueue(self, file_id: int, user_id: int, content: str):
        await self.queue.put(
            PersistenceJob(
                file_id=file_id,
                user_id=user_id,
                content=content,
            )
        )

    async def _worker(self):
        while True:
            job = await self.queue.get()

            try:
                db = SessionLocal()

                try:
                    code_file = db.get(CodeFile, job.file_id)

                    if code_file is not None:
                        document = CRDTDocument(job.content)
                        persist_document(
                            code_file,
                            document,
                            job.user_id,
                            db,
                        )
                finally:
                    db.close()

            except Exception as exc:
                print(
                    f"[PersistenceQueue] Failed to persist "
                    f"file {job.file_id}: {exc}"
                )

            finally:
                self.queue.task_done()


persistence_queue = PersistenceQueue()
