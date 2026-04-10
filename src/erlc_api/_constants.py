BASE_URL = "https://api.policeroleplay.community"
DEFAULT_TIMEOUT_S = 20.0

DEFAULT_MAX_RETRIES = 4
DEFAULT_BACKOFF_BASE_S = 0.6
DEFAULT_BACKOFF_CAP_S = 8.0
DEFAULT_BACKOFF_JITTER_S = 0.2

DEFAULT_RETRY_429 = True
DEFAULT_RETRY_5XX = True
DEFAULT_RETRY_NETWORK = True

DEFAULT_ENABLE_REQUEST_COALESCING = True

DEFAULT_ENABLE_CIRCUIT_BREAKER = True
DEFAULT_CIRCUIT_FAILURE_THRESHOLD = 5
DEFAULT_CIRCUIT_OPEN_S = 15.0

DEFAULT_ENABLE_CACHE = True
DEFAULT_CACHE_TTL_BY_PATH = {
    "/v1/server": 5.0,
    "/v1/server/players": 10.0,
    "/v1/server/staff": 30.0,
    "/v1/server/joinlogs": 20.0,
    "/v1/server/killlogs": 20.0,
    "/v1/server/commandlogs": 20.0,
    "/v1/server/queue": 10.0,
    "/v2/server": 5.0,
}

DEFAULT_REQUEST_REPLAY_SIZE = 200
