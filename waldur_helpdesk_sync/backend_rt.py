import rt.rest2

from backend_base import *

from clean_html import clean_html


REQUEST_TRACKER_QUEUE = os.environ.get('REQUEST_TRACKER_QUEUE')


class Backend:
    def __init__(self):
        if not BACKEND_API_URL.endswith('/'):
            url = f'{BACKEND_API_URL}/REST/2.0/'
        else:
            url = f'{BACKEND_API_URL}REST/2.0/'

        self.manager = rt.rest2.Rt(
            url, token=BACKEND_API_TOKEN
        )
        self.queue = REQUEST_TRACKER_QUEUE

    def get_issues(self):
        response = self.manager.search(Queue=self.queue, Status=BACKEND_IMPORT_STATUS)
        return [Issue(k['id'], k['Subject']) for k in response]

    def get_all_issues(self):
        return list(self.manager.search(Queue=self.queue))

    def add_comment(self, ticket_id, content):
        return self.manager.comment(ticket_id, content)

    def edit_issue(self, ticket_id, **kwargs):
        return self.manager.edit_ticket(ticket_id, **kwargs)

    def resolve_issue(self, ticket_id):
        return self.edit_issue(ticket_id, Status=BACKEND_RESOLVED_STATUS)

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
