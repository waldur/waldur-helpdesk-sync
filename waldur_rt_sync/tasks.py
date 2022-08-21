import logging
import os
import sys

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
ISSUE_TYPE = os.environ["ISSUE_TYPE"]
ISSUE_ID_PREFIX = os.environ.get("ISSUE_ID_PREFIX", "RT_ID")
ISSUE_URL_TEMPLATE = os.environ["ISSUE_URL_TEMPLATE"]

REQUEST_TRACKER_IMPORTED_STATUS = os.environ.get("REQUEST_TRACKER_IMPORTED_STATUS", 'open')

client = WaldurClient(WALDUR_API_URL, WALDUR_API_TOKEN)


def pull_issues():
    backend = Backend()
    issues = backend.get_issues()
    waldur_issues = client.list_support_issues(filters={'remote_id': ISSUE_ID_PREFIX})
    waldur_ids = [issue['remote_id'].replace(ISSUE_ID_PREFIX + ':', '') for issue in waldur_issues]

    for issue in issues:
        issue_id = issue.get('id')

        if issue_id in waldur_ids:
            continue

        try:
            comments = backend.get_comments(issue_id)
            description = '<br>'.join(
                [
                    'creator: %s; created: %s; content: %s;' % (comment.creator, comment.created, comment.content)
                    for comment in comments
                ]
            )
            response = client.create_support_issue(
                issue.get('Subject'),
                ISSUE_TYPE,
                ISSUE_USER_URL,
                '%s:%s' % (ISSUE_ID_PREFIX, issue_id),
                description=description
            )

            backend.add_comment(
                issue_id,
                'Task have been created. URL: ' + ISSUE_URL_TEMPLATE.format(uuid=response.get('uuid'))
            )
            backend.edit_issue(issue_id, Status=REQUEST_TRACKER_IMPORTED_STATUS)
        except Exception as e:
            logger.exception(f"Unable to create issue {issue_id}. Message: {e}.")
        else:
            logger.info(f"An issue {issue_id} has been created.")
