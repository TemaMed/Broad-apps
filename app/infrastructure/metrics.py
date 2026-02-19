from prometheus_client import Counter

api_requests_total = Counter("api_requests_total", "Total API requests", ["path", "method", "status"])
generation_total = Counter("generation_total", "Total generations", ["kind", "status"])
generation_cost_total = Counter("generation_cost_total_tokens", "Total generation cost in tokens", ["kind"])
provider_errors_total = Counter("provider_errors_total", "Provider errors", ["provider"])
webhook_delivery_total = Counter("webhook_delivery_total", "Outgoing webhook deliveries", ["status"])
