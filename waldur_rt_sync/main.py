from time import sleep
import logging

from tasks import Synchronization

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    while True:
        sync = Synchronization()
        logger.info('Looking for new tasks in RT...')
        sync.pull_issues()
        logger.info('Sync resolved tasks...')
        sync.sync_resolved()
        sleep(float(60 * 5))
