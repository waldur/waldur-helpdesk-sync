import os

from time import sleep
import logging


BACKEND = os.environ.get('BACKEND', 'rt')

if BACKEND == 'zammad':
    from sync_zammad import Sync
else:
    from sync_rt import Sync

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    backend_name = BACKEND[0].upper() + BACKEND[1:]

    while True:
        try:
            sync = Sync()
            logger.info(f'Start of {backend_name} sync.')
            logger.info(f'Looking for new tasks in {backend_name} ...')
            sync.pull_issues()

            logger.info(f'Sync resolved tasks...')
            sync.sync_resolved()

            logger.info(f'Sync comments from Waldur to {backend_name} ...')
            sync.pull_comments_from_waldur_to_backend()

            logger.info(f'Sync comments from {backend_name} to Waldur...')
            sync.pull_comments_from_backend_to_waldur()

            logger.info(f'The end of sync.')
        except Exception as e:
            logger.exception(f"{backend_name} synchronization error. Message: {e}.")

        sleep(float(60 * 5))
