import os
from collections import namedtuple

import rt.rest2

from clean_html import clean_html

REQUEST_TRACKER_URL = os.environ["REQUEST_TRACKER_URL"]
REQUEST_TRACKER_TOKEN = os.environ["REQUEST_TRACKER_TOKEN"]
REQUEST_TRACKER_QUEUE = os.environ["REQUEST_TRACKER_QUEUE"]
REQUEST_TRACKER_IMPORT_STATUS = os.environ.get("REQUEST_TRACKER_IMPORT_STATUS", 'new')

Comment = namedtuple('Comment', 'id creator created content')


class Backend:
    def __init__(self):
        if not REQUEST_TRACKER_URL.endswith('/'):
            url = f'{REQUEST_TRACKER_URL}/REST/2.0/'
        else:
            url = f'{REQUEST_TRACKER_URL}REST/2.0/'

        self.manager = rt.rest2.Rt(
            url, token=REQUEST_TRACKER_TOKEN
        )
        self.queue = REQUEST_TRACKER_QUEUE

    def get_issues(self):
        return list(self.manager.search(Queue=self.queue, Status=REQUEST_TRACKER_IMPORT_STATUS))

    def get_all_issues(self):
        return list(self.manager.search(Queue=self.queue))

    def add_comment(self, ticket_id, content):
        return self.manager.comment(ticket_id, content)

    def edit_issue(self, ticket_id, **kwargs):
        return self.manager.edit_ticket(ticket_id, **kwargs)

    def get_comments(self, ticket_id):
        comments = []

        response = self.manager._Rt__paged_request(
            f'{self.manager.url}ticket/{ticket_id}/attachments',
            per_page=100,
            params={'fields': 'Filename,ContentType,Content,Created,Creator'}
        )

        for item in response:
            comment_id = item.get('id', '')
            content = item.get('Content', '')
            created = item.get('Created')
            creator = item.get('Creator', {}).get('id')

            if item.get('Filename') or not content:
                continue

            if not creator or creator == 'RT_System':
                continue

            comment = Comment(
                comment_id,
                creator,
                created,
                clean_html(content)
            )

            comments.append(comment)

        return comments
