# waldur-helpdesk-sync

Sync script for integrating a helpdesk with Waldur

Please set the following environment variables in order to make this script work:

BACKEND - a helpdesk software: 'rt' or 'zammad'.  
BACKEND_API_URL - URL of a helpdesk.  
BACKEND_API_TOKEN - token for access.  
REQUEST_TRACKER_QUEUE - queue for sync to waldur (only tickets with status BACKEND_IMPORT_STATUS will be syncronisated).  
BACKEND_IMPORT_STATUS - issue status to import from a helpdesk to Waldur. Default: 'new'.  
BACKEND_RESOLVED_STATUS - resolved issue status. Default: 'resolved'.  

WALDUR_API_URL - URL of Waldur.  
WALDUR_API_TOKEN - token for access. see http://your_waldur.domen/profile/manage/.

ISSUE_USER_URL - user to be used to create an issue.  
ISSUE_TYPE -  issue type to be used to create an issue.  
ISSUE_ID_PREFIX - prefix for ticket id what will be saved in Waldur. It can be needed if you use several helpdesk instances. Default: 'RT_ID'.  
