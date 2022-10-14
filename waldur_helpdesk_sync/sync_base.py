import logging
import os
import sys
from functools import lru_cache

from waldur_client import WaldurClient

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
WALDUR_COMMENT_UUID_PREFIX = os.environ.get("WALDUR_COMMENT_UUID_PREFIX", "WALDUR_COMMENT_UUID")
WALDUR_COMMENT_MARKER = os.environ.get("WALDUR_COMMENT_MARKER", "THIS IS WALDUR COMMENT.")


class SyncBase:
    @property
    def backend_client(self):
        raise NotImplementedError()

    @property
    def waldur_client(self):
        return WaldurClient(WALDUR_API_URL, WALDUR_API_TOKEN)

    @lru_cache(maxsize=1)
    def get_backend_issues(self):
        return self.backend_client.get_issues()

    @lru_cache(maxsize=1)
    def get_waldur_issues(self):
        return self.waldur_client.list_support_issues(filters={'remote_id': ISSUE_ID_PREFIX})

    def pull_issues(self):
        waldur_remote_ids = [issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '') for issue in self.get_waldur_issues()]

        for issue in self.get_backend_issues():
            if str(issue.id) in waldur_remote_ids:
                continue

            try:
                response = self.waldur_client.create_support_issue(
                    issue.summary,
                    ISSUE_TYPE,
                    ISSUE_USER_URL,
                    '%s:%s' % (ISSUE_ID_PREFIX, issue.id),
                )

                self.backend_client.add_comment(
                    issue.id,
                    f"""{WALDUR_COMMENT_MARKER}
                    Task has been mirrored. ID of the created task is {response.get("key")}."""
                )
            except Exception as e:
                logger.exception(f'Unable to create issue {issue.id}. Message: {e}.')
            else:
                logger.info(f'An issue {issue.id} has been mirror as {response.get("key")}.')

    def sync_resolved(self):
        waldur_resolved_ids = [
            issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '')
            for issue in self.get_waldur_issues()
            if issue['resolved'] == True
        ]

        for issue in self.get_backend_issues():
            if str(issue.id) in waldur_resolved_ids:
                try:
                    self.backend_client.resolve_issue(issue.id)
                except Exception as e:
                    logger.exception(f"Unable to resolve issue {issue.id}. Message: {e}.")
                else:
                    logger.info(f"An issue {issue.id} has been resolved.")

    def is_waldur_comment_synced(self, waldur_comment, backend_comments):
        for backend_comment in backend_comments:
            if WALDUR_COMMENT_MARKER in backend_comment.content and \
                    waldur_comment['uuid'] in backend_comment.content:
                return True
        return False

    def pull_comments_from_waldur_to_backend(self):
        backend_issues_ids = [str(issue.get('id')) for issue in self.backend_client.get_all_issues()]

        for waldur_issue in self.get_waldur_issues():
            backend_issue_id = waldur_issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '')

            if backend_issue_id not in backend_issues_ids:
                logger.info(f"Unable to pull issue comments from Waldur to help desk. Issue {backend_issue_id} does not exist.")
                continue

            waldur_comments = self.waldur_client.list_support_comments(
                filters={
                    'is_public': True,
                    'issue_uuid': waldur_issue['uuid'],
                    'remote_id_is_set': False,
                }
            )

            backend_comments = self.backend_client.get_comments(backend_issue_id)

            for waldur_comment in waldur_comments:
                try:
                    if self.is_waldur_comment_synced(waldur_comment, backend_comments):
                        continue

                    message = '%s / %s\n\n%s wrote on %s:\n%s\n\n' % (
                        WALDUR_COMMENT_MARKER,
                        waldur_comment['uuid'],
                        waldur_comment['author_name'],
                        waldur_comment['created'],
                        clean_html(waldur_comment['description'])
                    )

                    self.backend_client.add_comment(backend_issue_id, message)
                    logger.info(f"A Waldur comment {waldur_comment['uuid']} in help desk for issue {backend_issue_id} has been "
                                f"created.")
                except Exception as e:
                    logger.exception(f"Unable to create comment in help desk for issue {backend_issue_id}. Message: {e}.")

    def pull_comments_from_backend_to_waldur(self):
        backend_issues_ids = [str(issue.get('id')) for issue in self.backend_client.get_all_issues()]

        for waldur_issue in self.get_waldur_issues():
            backend_issue_id = waldur_issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '')

            if backend_issue_id not in backend_issues_ids:
                logger.info(f"Unable to pull issue comments from help desk to Waldur. Issue {backend_issue_id} does not exist.")
                continue

            waldur_comments = self.waldur_client.list_support_comments(
                filters={
                    'is_public': True,
                    'issue_uuid': waldur_issue['uuid'],
                    'remote_id_is_set': True,
                }
            )

            backend_comments = self.backend_client.get_comments(backend_issue_id)

            for backend_comment in backend_comments:
                if WALDUR_COMMENT_MARKER in backend_comment.content:
                    # This comment has been created by Waldur
                    continue

                try:
                    if str(backend_comment.id) in [c['remote_id'] for c in waldur_comments]:
                        # This comment has been pushed to Waldur
                        continue

                    message = f"Description: {backend_comment.content}\n\n" \
                              f"Author_name: {backend_comment.creator}\n\n" \
                              f"Created: {backend_comment.created}\n\n"

                    created_comment = self.waldur_client.create_support_comments(
                        waldur_issue['uuid'],
                        message,
                        backend_comment.id
                    )
                except Exception as e:
                    logger.exception(f"Unable to create comment in Waldur for issue {backend_issue_id}. Message: {e}.")
                else:
                    logger.info(f"A comment {created_comment['uuid']} in Waldur for issue {backend_issue_id} has been "
                                f"created.")
