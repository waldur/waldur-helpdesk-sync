from backend_rt import Backend as BackendRT
from sync_base import SyncBase


class Sync(SyncBase):
    @property
    def backend_client(self):
        return BackendRT()
