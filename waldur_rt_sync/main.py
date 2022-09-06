from time import sleep
import logging

from tasks import pull_issues

logging.getLogger("requests").setLevel(logging.WARNING)
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(filename)s:%(lineno)d %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    while True:
        logger.info('Looking for new tasks in RT...')
        pull_issues()
        sleep(float(60 * 10))
