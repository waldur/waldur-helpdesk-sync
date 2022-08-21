import os
from collections import namedtuple

import rt.rest2

from clean_html import clean_html

REQUEST_TRACKER_URL = os.environ["REQUEST_TRACKER_URL"]
REQUEST_TRACKER_TOKEN = os.environ["REQUEST_TRACKER_TOKEN"]
REQUEST_TRACKER_QUEUE = os.environ["REQUEST_TRACKER_QUEUE"]
REQUEST_TRACKER_IMPORT_STATUS = os.environ.get("REQUEST_TRACKER_IMPORT_STATUS", 'new')

Comment = namedtuple('Comment', 'creator created content')


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

    def add_comment(self, ticket_id, content):
        return self.manager.comment(ticket_id, content)

    def edit_issue(self, ticket_id, **kwargs):
        return self.manager.edit_ticket(ticket_id, **kwargs)

    def get_comments(self, ticket_id):
        comments = []

        response = self.manager.session.request(
                'get',
                f'{self.manager.url}ticket/{ticket_id}/attachments',
                params={'fields': 'Filename,ContentType,Content,Created,Creator'}
        ).json()

        for item in response['items']:
            content = item.get('Content', '')
            created = item.get('Created')
            creator = item.get('Creator', {}).get('id')

            if item.get('Filename') or not content:
                continue

            if not creator or creator == 'RT_System':
                continue

            comment = Comment(
                creator,
                created,
                clean_html(content)
            )

            comments.append(comment)

        return comments
