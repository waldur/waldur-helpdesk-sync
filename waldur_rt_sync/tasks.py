import logging
import os
import sys
from functools import lru_cache

from waldur_client import WaldurClient

from backend import Backend
from clean_html import clean_html


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
WALDUR_COMMENT_UUID_PREFIX = os.environ.get("WALDUR_COMMENT_UUID_PREFIX", "WALDUR_COMMENT_UUID")
WALDUR_COMMENT_MARKER = os.environ.get("WALDUR_COMMENT_MARKER", "THIS IS WALDUR COMMENT.")


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
                response = self.waldur_client.create_support_issue(
                    issue.get('Subject') or 'New issue',
                    ISSUE_TYPE,
                    ISSUE_USER_URL,
                    '%s:%s' % (ISSUE_ID_PREFIX, issue_id),
                )

                self.rt_client.add_comment(
                    issue_id,
                    f"""{WALDUR_COMMENT_MARKER}
                    Task has been mirrored. ID of the created task is {response.get("key")}."""
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

    def is_waldur_comment_synced(self, waldur_comment, rt_comments):
        for rt_comment in rt_comments:
            if WALDUR_COMMENT_MARKER in rt_comment.content and \
                    waldur_comment['uuid'] in rt_comment.content:
                return True
        return False

    def pull_comments_from_waldur_to_rt(self):
        rt_issues_ids = [issue.get('id') for issue in self.rt_client.get_all_issues()]
        for waldur_issue in self.get_waldur_issues():
            rt_issue_id = waldur_issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '')

            if rt_issue_id not in rt_issues_ids:
                logger.info(f"Unable to pull issue comments from Waldur to RT. Issue {rt_issue_id} does not exist.")
                continue

            waldur_comments = self.waldur_client.list_support_comments(
                filters={
                    'is_public': True,
                    'issue_uuid': waldur_issue['uuid'],
                    'remote_id_is_set': False,
                }
            )

            rt_comments = self.rt_client.get_comments(rt_issue_id)

            for waldur_comment in waldur_comments:
                try:
                    if self.is_waldur_comment_synced(waldur_comment, rt_comments):
                        continue

                    message = '%s / %s\n\n%s wrote on %s:\n%s\n\n' % (
                        WALDUR_COMMENT_MARKER,
                        waldur_comment['uuid'],
                        waldur_comment['author_name'],
                        waldur_comment['created'],
                        clean_html(waldur_comment['description'])
                    )

                    self.rt_client.add_comment(rt_issue_id, message)
                    logger.info(f"A Waldur comment {waldur_comment['uuid']} in RT for issue {rt_issue_id} has been "
                                f"created.")
                except Exception as e:
                    logger.exception(f"Unable to create comment in RT for issue {rt_issue_id}. Message: {e}.")

    def pull_comments_from_rt_to_waldur(self):
        rt_issues_ids = [issue.get('id') for issue in self.rt_client.get_all_issues()]

        for waldur_issue in self.get_waldur_issues():
            rt_issue_id = waldur_issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '')

            if rt_issue_id not in rt_issues_ids:
                logger.info(f"Unable to pull issue comments from RT to Waldur. Issue {rt_issue_id} does not exist.")
                continue

            waldur_comments = self.waldur_client.list_support_comments(
                filters={
                    'is_public': True,
                    'issue_uuid': waldur_issue['uuid'],
                    'remote_id_is_set': True,
                }
            )

            rt_comments = self.rt_client.get_comments(rt_issue_id)

            for rt_comment in rt_comments:
                if WALDUR_COMMENT_MARKER in rt_comment.content:
                    # This comment has been created by Waldur
                    continue

                try:
                    if rt_comment.id in [c['remote_id'] for c in waldur_comments]:
                        # This comment has been pushed to Waldur
                        continue

                    message = f"Description: {rt_comment.content}\n\n" \
                              f"Author_name: {rt_comment.creator}\n\n" \
                              f"Created: {rt_comment.created}\n\n"

                    created_comment = self.waldur_client.create_support_comments(
                        waldur_issue['uuid'],
                        message,
                        rt_comment.id
                    )
                except Exception as e:
                    logger.exception(f"Unable to create comment in Waldur for issue {rt_issue_id}. Message: {e}.")
                else:
                    logger.info(f"A comment {created_comment['uuid']} in Waldur for issue {rt_issue_id} has been "
                                f"created.")
