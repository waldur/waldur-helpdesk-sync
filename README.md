# waldur-rt-sync

Sync script for integrating RT with Waldur

Please set the following environment variables in order to make this script work:

REQUEST_TRACKER_URL - URL of request tracker
REQUEST_TRACKER_TOKEN - token for access. see http://your_rt.domen/Prefs/AuthTokens.html
REQUEST_TRACKER_QUEUE - queue for sync to waldur (only tickets with status REQUEST_TRACKER_IMPORT_STATUS will be syncronisated)
REQUEST_TRACKER_IMPORT_STATUS - issue status to import from RT to Waldur. Default: 'new'
REQUEST_TRACKER_RESOLVED_STATUS - resolved issue status. Default: 'resolved'

WALDUR_API_URL - URL of Waldur
WALDUR_API_TOKEN - token for access. see http://your_waldur.domen/profile/manage/

ISSUE_USER_URL - user to be used to create an issue
ISSUE_TYPE -  issue type to be used to create an issue
ISSUE_ID_PREFIX - prefix for ticket id what will be saved in Waldur. It can be needed if you use several waldur_rt_sync instances. Default: 'RT_ID'
