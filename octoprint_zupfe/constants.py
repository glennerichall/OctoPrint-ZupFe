URL_API_KEY = "URL_API_KEY"
URL_API_KEYS = "URL_API_KEYS"
URL_AVATAR = "URL_AVATAR"
URL_CONFIRM_EMAIL = "URL_CONFIRM_EMAIL"
URL_FILE = "URL_FILE"
URL_FILES = "URL_FILES"
URL_FILE_SIGNED_URL = "URL_FILE_SIGNED_URL"
URL_FLASH_ERROR = "URL_FLASH_ERROR"
URL_FLASH_WARNING = "URL_FLASH_WARNING"
URL_GCODE_BUCKETNAMES = "URL_GCODE_BUCKETNAMES"
URL_INVOKE_PRINTER_PROC = "URL_INVOKE_PRINTER_PROC"
URL_LOGIN = "URL_LOGIN"
URL_LOGIN_FAILURE = "URL_LOGIN_FAILURE"
URL_LOGIN_SUCCESS = "URL_LOGIN_SUCCESS"
URL_LOGOUT = "URL_LOGOUT"
URL_MESSAGE = "URL_MESSAGE"
URL_PASSPORT_CALLBACK = "URL_PASSPORT_CALLBACK"
URL_PREFERENCE = "URL_PREFERENCE"
URL_PRINTER = "URL_PRINTER"
URL_PRINTERS = "URL_PRINTERS"
URL_PRINTER_EVENT = "URL_PRINTER_EVENT"
URL_PRINTER_ID_PENDING = "URL_PRINTER_ID_PENDING"
URL_PRINTER_LINK = "URL_PRINTER_LINK"
URL_PRINTER_READ_STREAM = "URL_PRINTER_READ_STREAM"
URL_PRINTER_SNAPSHOT = "URL_PRINTER_SNAPSHOT"
URL_PRINTER_STATUS = "URL_PRINTER_STATUS"
URL_PRINTER_TITLE = "URL_PRINTER_TITLE"
URL_PRINTER_WRITE_STREAM = "URL_PRINTER_WRITE_STREAM"
URL_PROFILE = "URL_PROFILE"
URL_PUBLISH_EVENT = "URL_PUBLISH_EVENT"
URL_PUBLISH_MESSAGE = "URL_PUBLISH_MESSAGE"
URL_RTC_OFFER_PRINTER = "URL_RTC_OFFER_PRINTER"
URL_SEND_FILE = "URL_SEND_FILE"
URL_SESSION = "URL_SESSION"
URL_SESSION_VALIDATE = "URL_SESSION_VALIDATE"
URL_SLICER_PLUGIN = "URL_SLICER_PLUGIN"
URL_SYSTEM_SESSION_COUNT = "URL_SYSTEM_SESSION_COUNT"
URL_SYSTEM_STATUS = "URL_SYSTEM_STATUS"
URL_ZIP_FILES = "URL_ZIP_FILES"
EVENT_APIKEY_CREATED = 4
EVENT_APIKEY_DELETED = 5
EVENT_DISCONNECTED = 0
EVENT_FETCH_DONE = 28
EVENT_FILES_PURGED = 34
EVENT_FILE_PROCESSED = 30
EVENT_FILE_REMOVED = 33
EVENT_FILE_UPLOADED = 29
EVENT_LOGGED_IN = 1
EVENT_LOGGED_OUT = 2
EVENT_MESSAGE = 35
EVENT_MESSAGE_FAILURE = 49
EVENT_MESSAGE_RESPONSE = 50
EVENT_MJPEG_FRAME = 54
EVENT_NEW_FILE_CREATED = 31
EVENT_NOTIFICATION_ERROR = 60
EVENT_NOTIFICATION_INFO = 59
EVENT_NOTIFICATION_SUCCESS = 61
EVENT_NOTIFICATION_WARNING = 58
EVENT_OCTOPRINT_APIKEY_RECEIVED = 26
EVENT_OCTOPRINT_BACKEND_CONNECTED = 24
EVENT_OCTOPRINT_BACKEND_DISCONNECTED = 25
EVENT_OCTOPRINT_BACKEND_INITIALIZED = 23
EVENT_OCTOPRINT_SHOW_WIZARD = 22
EVENT_PENDING_FILE_ABORTED = 32
EVENT_PREFERENCES_CHANGED = 27
EVENT_PRINTER_CANCELED = 17
EVENT_PRINTER_CONNECTED = 63
EVENT_PRINTER_CONNECTING = 10
EVENT_PRINTER_DISCONNECTED = 64
EVENT_PRINTER_FILES_UPDATED = 12
EVENT_PRINTER_FILE_SELECTED = 13
EVENT_PRINTER_LINKED = 6
EVENT_PRINTER_OFFLINE = 9
EVENT_PRINTER_ONLINE = 8
EVENT_PRINTER_OPERATIONAL = 18
EVENT_PRINTER_PAUSED = 16
EVENT_PRINTER_POWER_DOWN = 19
EVENT_PRINTER_POWER_UP = 20
EVENT_PRINTER_PRINTING = 14
EVENT_PRINTER_PRINT_DONE = 15
EVENT_PRINTER_PROGRESS = 21
EVENT_PRINTER_TEMPERATURE = 62
EVENT_PRINTER_TITLE_CHANGED = 11
EVENT_PRINTER_UNLINKED = 7
EVENT_REQUIRE_LOGIN = 3
EVENT_STREAM_INFO = 53
EVENT_SYSTEM_STATUS_CHANGED = 36
MESSAGE_BINARY = 5
MESSAGE_COMMAND = 4
MESSAGE_EMPTY = 7
MESSAGE_EVENT = 13
MESSAGE_JSON = 2
MESSAGE_MJPEG = 3
MESSAGE_REJECT = 9
MESSAGE_REPLY = 8
MESSAGE_STREAM = 1
MESSAGE_STREAM_CONTENT = 11
MESSAGE_STREAM_END = 10
MESSAGE_STREAM_FILE = 12
MESSAGE_STRING = 6
MESSAGE_UNDEFINED = 0
RPC_REQUEST_ABORT_PRINT = 40
RPC_REQUEST_CONNECTION = 48
RPC_REQUEST_DOWNLOAD_FILE = 42
RPC_REQUEST_GET_FILE_LIST = 37
RPC_REQUEST_GET_SOCKET_ID = 43
RPC_REQUEST_GET_STATE = 38
RPC_REQUEST_POWER_OFF = 47
RPC_REQUEST_POWER_ON = 46
RPC_REQUEST_PRINT_ACTIVE_FILE = 39
RPC_REQUEST_PROGRESS = 45
RPC_REQUEST_SET_ACTIVE_FILE = 41
RPC_REQUEST_STREAM = 44
RPC_REQUEST_TEMPERATURE_HISTORY = 57
RPC_REQUEST_TOGGLE_POWER = 56
RPC_REQUEST_WEBRTC = 55


def get_constant_name(value):
    if value == URL_API_KEY: return "URL_API_KEY"
    if value == URL_API_KEYS: return "URL_API_KEYS"
    if value == URL_AVATAR: return "URL_AVATAR"
    if value == URL_CONFIRM_EMAIL: return "URL_CONFIRM_EMAIL"
    if value == URL_FILE: return "URL_FILE"
    if value == URL_FILES: return "URL_FILES"
    if value == URL_FILE_SIGNED_URL: return "URL_FILE_SIGNED_URL"
    if value == URL_FLASH_ERROR: return "URL_FLASH_ERROR"
    if value == URL_FLASH_WARNING: return "URL_FLASH_WARNING"
    if value == URL_GCODE_BUCKETNAMES: return "URL_GCODE_BUCKETNAMES"
    if value == URL_INVOKE_PRINTER_PROC: return "URL_INVOKE_PRINTER_PROC"
    if value == URL_LOGIN: return "URL_LOGIN"
    if value == URL_LOGIN_FAILURE: return "URL_LOGIN_FAILURE"
    if value == URL_LOGIN_SUCCESS: return "URL_LOGIN_SUCCESS"
    if value == URL_LOGOUT: return "URL_LOGOUT"
    if value == URL_MESSAGE: return "URL_MESSAGE"
    if value == URL_PASSPORT_CALLBACK: return "URL_PASSPORT_CALLBACK"
    if value == URL_PREFERENCE: return "URL_PREFERENCE"
    if value == URL_PRINTER: return "URL_PRINTER"
    if value == URL_PRINTERS: return "URL_PRINTERS"
    if value == URL_PRINTER_EVENT: return "URL_PRINTER_EVENT"
    if value == URL_PRINTER_ID_PENDING: return "URL_PRINTER_ID_PENDING"
    if value == URL_PRINTER_LINK: return "URL_PRINTER_LINK"
    if value == URL_PRINTER_READ_STREAM: return "URL_PRINTER_READ_STREAM"
    if value == URL_PRINTER_SNAPSHOT: return "URL_PRINTER_SNAPSHOT"
    if value == URL_PRINTER_STATUS: return "URL_PRINTER_STATUS"
    if value == URL_PRINTER_TITLE: return "URL_PRINTER_TITLE"
    if value == URL_PRINTER_WRITE_STREAM: return "URL_PRINTER_WRITE_STREAM"
    if value == URL_PROFILE: return "URL_PROFILE"
    if value == URL_PUBLISH_EVENT: return "URL_PUBLISH_EVENT"
    if value == URL_PUBLISH_MESSAGE: return "URL_PUBLISH_MESSAGE"
    if value == URL_RTC_OFFER_PRINTER: return "URL_RTC_OFFER_PRINTER"
    if value == URL_SEND_FILE: return "URL_SEND_FILE"
    if value == URL_SESSION: return "URL_SESSION"
    if value == URL_SESSION_VALIDATE: return "URL_SESSION_VALIDATE"
    if value == URL_SLICER_PLUGIN: return "URL_SLICER_PLUGIN"
    if value == URL_SYSTEM_SESSION_COUNT: return "URL_SYSTEM_SESSION_COUNT"
    if value == URL_SYSTEM_STATUS: return "URL_SYSTEM_STATUS"
    if value == URL_ZIP_FILES: return "URL_ZIP_FILES"
    if value == EVENT_APIKEY_CREATED: return "EVENT_APIKEY_CREATED"
    if value == EVENT_APIKEY_DELETED: return "EVENT_APIKEY_DELETED"
    if value == EVENT_DISCONNECTED: return "EVENT_DISCONNECTED"
    if value == EVENT_FETCH_DONE: return "EVENT_FETCH_DONE"
    if value == EVENT_FILES_PURGED: return "EVENT_FILES_PURGED"
    if value == EVENT_FILE_PROCESSED: return "EVENT_FILE_PROCESSED"
    if value == EVENT_FILE_REMOVED: return "EVENT_FILE_REMOVED"
    if value == EVENT_FILE_UPLOADED: return "EVENT_FILE_UPLOADED"
    if value == EVENT_LOGGED_IN: return "EVENT_LOGGED_IN"
    if value == EVENT_LOGGED_OUT: return "EVENT_LOGGED_OUT"
    if value == EVENT_MESSAGE: return "EVENT_MESSAGE"
    if value == EVENT_MESSAGE_FAILURE: return "EVENT_MESSAGE_FAILURE"
    if value == EVENT_MESSAGE_RESPONSE: return "EVENT_MESSAGE_RESPONSE"
    if value == EVENT_MJPEG_FRAME: return "EVENT_MJPEG_FRAME"
    if value == EVENT_NEW_FILE_CREATED: return "EVENT_NEW_FILE_CREATED"
    if value == EVENT_NOTIFICATION_ERROR: return "EVENT_NOTIFICATION_ERROR"
    if value == EVENT_NOTIFICATION_INFO: return "EVENT_NOTIFICATION_INFO"
    if value == EVENT_NOTIFICATION_SUCCESS: return "EVENT_NOTIFICATION_SUCCESS"
    if value == EVENT_NOTIFICATION_WARNING: return "EVENT_NOTIFICATION_WARNING"
    if value == EVENT_OCTOPRINT_APIKEY_RECEIVED: return "EVENT_OCTOPRINT_APIKEY_RECEIVED"
    if value == EVENT_OCTOPRINT_BACKEND_CONNECTED: return "EVENT_OCTOPRINT_BACKEND_CONNECTED"
    if value == EVENT_OCTOPRINT_BACKEND_DISCONNECTED: return "EVENT_OCTOPRINT_BACKEND_DISCONNECTED"
    if value == EVENT_OCTOPRINT_BACKEND_INITIALIZED: return "EVENT_OCTOPRINT_BACKEND_INITIALIZED"
    if value == EVENT_OCTOPRINT_SHOW_WIZARD: return "EVENT_OCTOPRINT_SHOW_WIZARD"
    if value == EVENT_PENDING_FILE_ABORTED: return "EVENT_PENDING_FILE_ABORTED"
    if value == EVENT_PREFERENCES_CHANGED: return "EVENT_PREFERENCES_CHANGED"
    if value == EVENT_PRINTER_CANCELED: return "EVENT_PRINTER_CANCELED"
    if value == EVENT_PRINTER_CONNECTED: return "EVENT_PRINTER_CONNECTED"
    if value == EVENT_PRINTER_CONNECTING: return "EVENT_PRINTER_CONNECTING"
    if value == EVENT_PRINTER_DISCONNECTED: return "EVENT_PRINTER_DISCONNECTED"
    if value == EVENT_PRINTER_FILES_UPDATED: return "EVENT_PRINTER_FILES_UPDATED"
    if value == EVENT_PRINTER_FILE_SELECTED: return "EVENT_PRINTER_FILE_SELECTED"
    if value == EVENT_PRINTER_LINKED: return "EVENT_PRINTER_LINKED"
    if value == EVENT_PRINTER_OFFLINE: return "EVENT_PRINTER_OFFLINE"
    if value == EVENT_PRINTER_ONLINE: return "EVENT_PRINTER_ONLINE"
    if value == EVENT_PRINTER_OPERATIONAL: return "EVENT_PRINTER_OPERATIONAL"
    if value == EVENT_PRINTER_PAUSED: return "EVENT_PRINTER_PAUSED"
    if value == EVENT_PRINTER_POWER_DOWN: return "EVENT_PRINTER_POWER_DOWN"
    if value == EVENT_PRINTER_POWER_UP: return "EVENT_PRINTER_POWER_UP"
    if value == EVENT_PRINTER_PRINTING: return "EVENT_PRINTER_PRINTING"
    if value == EVENT_PRINTER_PRINT_DONE: return "EVENT_PRINTER_PRINT_DONE"
    if value == EVENT_PRINTER_PROGRESS: return "EVENT_PRINTER_PROGRESS"
    if value == EVENT_PRINTER_TEMPERATURE: return "EVENT_PRINTER_TEMPERATURE"
    if value == EVENT_PRINTER_TITLE_CHANGED: return "EVENT_PRINTER_TITLE_CHANGED"
    if value == EVENT_PRINTER_UNLINKED: return "EVENT_PRINTER_UNLINKED"
    if value == EVENT_REQUIRE_LOGIN: return "EVENT_REQUIRE_LOGIN"
    if value == EVENT_STREAM_INFO: return "EVENT_STREAM_INFO"
    if value == EVENT_SYSTEM_STATUS_CHANGED: return "EVENT_SYSTEM_STATUS_CHANGED"
    if value == MESSAGE_BINARY: return "MESSAGE_BINARY"
    if value == MESSAGE_COMMAND: return "MESSAGE_COMMAND"
    if value == MESSAGE_EMPTY: return "MESSAGE_EMPTY"
    if value == MESSAGE_EVENT: return "MESSAGE_EVENT"
    if value == MESSAGE_JSON: return "MESSAGE_JSON"
    if value == MESSAGE_MJPEG: return "MESSAGE_MJPEG"
    if value == MESSAGE_REJECT: return "MESSAGE_REJECT"
    if value == MESSAGE_REPLY: return "MESSAGE_REPLY"
    if value == MESSAGE_STREAM: return "MESSAGE_STREAM"
    if value == MESSAGE_STREAM_CONTENT: return "MESSAGE_STREAM_CONTENT"
    if value == MESSAGE_STREAM_END: return "MESSAGE_STREAM_END"
    if value == MESSAGE_STREAM_FILE: return "MESSAGE_STREAM_FILE"
    if value == MESSAGE_STRING: return "MESSAGE_STRING"
    if value == MESSAGE_UNDEFINED: return "MESSAGE_UNDEFINED"
    if value == RPC_REQUEST_ABORT_PRINT: return "RPC_REQUEST_ABORT_PRINT"
    if value == RPC_REQUEST_CONNECTION: return "RPC_REQUEST_CONNECTION"
    if value == RPC_REQUEST_DOWNLOAD_FILE: return "RPC_REQUEST_DOWNLOAD_FILE"
    if value == RPC_REQUEST_GET_FILE_LIST: return "RPC_REQUEST_GET_FILE_LIST"
    if value == RPC_REQUEST_GET_SOCKET_ID: return "RPC_REQUEST_GET_SOCKET_ID"
    if value == RPC_REQUEST_GET_STATE: return "RPC_REQUEST_GET_STATE"
    if value == RPC_REQUEST_POWER_OFF: return "RPC_REQUEST_POWER_OFF"
    if value == RPC_REQUEST_POWER_ON: return "RPC_REQUEST_POWER_ON"
    if value == RPC_REQUEST_PRINT_ACTIVE_FILE: return "RPC_REQUEST_PRINT_ACTIVE_FILE"
    if value == RPC_REQUEST_PROGRESS: return "RPC_REQUEST_PROGRESS"
    if value == RPC_REQUEST_SET_ACTIVE_FILE: return "RPC_REQUEST_SET_ACTIVE_FILE"
    if value == RPC_REQUEST_STREAM: return "RPC_REQUEST_STREAM"
    if value == RPC_REQUEST_TEMPERATURE_HISTORY: return "RPC_REQUEST_TEMPERATURE_HISTORY"
    if value == RPC_REQUEST_TOGGLE_POWER: return "RPC_REQUEST_TOGGLE_POWER"
    if value == RPC_REQUEST_WEBRTC: return "RPC_REQUEST_WEBRTC"
    return "UNKNOWN_VALUE"
