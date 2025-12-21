from prometheus_client import Counter

REQUEST_COUNTER = Counter(
    "app_requests_total", "Total number of requests to the app", ["endpoint"]
)
