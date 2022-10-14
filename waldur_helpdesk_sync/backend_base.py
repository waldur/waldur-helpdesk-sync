import os
from collections import namedtuple

BACKEND_API_URL = os.environ['BACKEND_API_URL']
BACKEND_API_TOKEN = os.environ['BACKEND_API_TOKEN']
BACKEND_IMPORT_STATUS = os.environ.get('BACKEND_IMPORT_STATUS', 'new')
BACKEND_RESOLVED_STATUS = os.environ.get("BACKEND_RESOLVED_STATUS", "resolved")

Comment = namedtuple('Comment', 'id creator created content')
Issue = namedtuple('Issue', 'id summary')
