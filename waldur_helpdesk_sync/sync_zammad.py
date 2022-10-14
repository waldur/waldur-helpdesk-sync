from backend_zammad import Backend as BackendZammad
from sync_base import SyncBase


class Sync(SyncBase):
    @property
    def backend_client(self):
        return BackendZammad()
