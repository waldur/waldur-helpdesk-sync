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
        try:
            sync = Synchronization()
            logger.info('Looking for new tasks in RT...')
            sync.pull_issues()

            logger.info('Sync resolved tasks...')
            sync.sync_resolved()

            logger.info('Sync comments from Waldur to RT...')
            sync.pull_comments_from_waldur_to_rt()

            logger.info('Sync comments from RT to Waldur...')
            sync.pull_comments_from_rt_to_waldur()

            logger.info('The end of sync.')
        except Exception as e:
            logger.exception(f"Synchronization error. Message: {e}.")

        sleep(float(60 * 5))
