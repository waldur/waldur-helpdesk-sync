import logging
import os
import sys
from functools import lru_cache

from waldur_client import WaldurClient

from backend import Backend


handler = logging.StreamHandler(sys.stdout)
logger = logging.getLogger(__name__)
formatter = logging.Formatter("[%(levelname)s] [%(asctime)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


WALDUR_API_URL = os.environ["WALDUR_API_URL"]
WALDUR_API_TOKEN = os.environ["WALDUR_API_TOKEN"]

ISSUE_USER_URL = os.environ["ISSUE_USER_URL"]
ISSUE_TYPE = os.environ.get("ISSUE_TYPE", "Incident")
ISSUE_ID_PREFIX = os.environ.get("ISSUE_ID_PREFIX", "RT_ID")
REQUEST_TRACKER_RESOLVED_STATUS = os.environ.get("REQUEST_TRACKER_RESOLVED_STATUS", "resolved")


class Synchronization:
    @property
    def rt_client(self):
        return Backend()

    @property
    def waldur_client(self):
        return WaldurClient(WALDUR_API_URL, WALDUR_API_TOKEN)

    @lru_cache(maxsize=1)
    def get_rt_issues(self):
        return self.rt_client.get_issues()

    @lru_cache(maxsize=1)
    def get_waldur_issues(self):
        return self.waldur_client.list_support_issues(filters={'remote_id': ISSUE_ID_PREFIX})

    def pull_issues(self):
        waldur_remote_ids = [issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '') for issue in self.get_waldur_issues()]

        for issue in self.get_rt_issues():
            issue_id = issue.get('id')

            if issue_id in waldur_remote_ids:
                continue

            try:
                comments = self.rt_client.get_comments(issue_id)
                description = '<br>'.join(
                    [
                        '%s wrote on %s:\n%s\n\n' % (comment.creator, comment.created, comment.content)
                        for comment in comments
                    ]
                )
                description = f'{issue["_url"]}\n\n' + description
                response = self.waldur_client.create_support_issue(
                    issue.get('Subject') or 'New issue',
                    ISSUE_TYPE,
                    ISSUE_USER_URL,
                    '%s:%s' % (ISSUE_ID_PREFIX, issue_id),
                    description=description
                )

                self.rt_client.add_comment(
                    issue_id,
                    f'Task has been mirrored. ID of the created task is {response.get("key")}.'
                )
            except Exception as e:
                logger.exception(f'Unable to create issue {issue_id}. Message: {e}.')
            else:
                logger.info(f'An issue {issue_id} has been mirror as {response.get("key")}.')

    def sync_resolved(self):
        waldur_resolved_ids = [
            issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '')
            for issue in self.get_waldur_issues()
            if issue['resolved'] == True
        ]

        for issue in self.get_rt_issues():
            issue_id = issue.get('id')

            if issue_id in waldur_resolved_ids:
                try:
                    self.rt_client.edit_issue(issue_id, Status=REQUEST_TRACKER_RESOLVED_STATUS)
                except Exception as e:
                    logger.exception(f"Unable to resolve issue {issue_id}. Message: {e}.")
                else:
                    logger.info(f"An issue {issue_id} has been resolved.")
