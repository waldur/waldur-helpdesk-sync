from zammad_py import ZammadAPI

from clean_html import clean_html

from backend_base import *


ZAMMAD_IMPORT_STATUS = os.environ.get("ZAMMAD__IMPORT_STATUS", 'open')


class Backend:
    def __init__(self):
        if not BACKEND_API_URL.endswith('/'):
            url = f'{BACKEND_API_URL}/api/v1/'
        else:
            url = f'{BACKEND_API_URL}api/v1/'

        self.manager = ZammadAPI(url, http_token=BACKEND_API_TOKEN)

    def get_issues(self):
        response = self.manager.ticket.search({'query': 'state.name:' + ZAMMAD_IMPORT_STATUS})
        return [Issue(v['id'], v['title']) for k, v in response['assets']['Ticket'].items()]

    def get_all_issues(self):
        return list(self.manager.ticket.all())

    def add_comment(self, ticket_id, content):
        return self.manager.ticket_article.create({
            'ticket_id': ticket_id,
            'body': content,
        })

    def edit_issue(self, ticket_id, **kwargs):
        return self.manager.ticket.update(ticket_id, kwargs)

    def resolve_issue(self, ticket_id):
        return self.edit_issue(ticket_id, state=BACKEND_RESOLVED_STATUS)

    def get_comments(self, ticket_id):
        comments = []

        for zammad_comment in self.manager.ticket.articles(ticket_id):
            comment_id = zammad_comment.get('id', '')
            content = zammad_comment.get('body', '')
            created = zammad_comment.get('created_at')
            creator = zammad_comment.get('created_by')

            comment = Comment(
                comment_id,
                creator,
                created,
                clean_html(content)
            )

            comments.append(comment)

        return comments
