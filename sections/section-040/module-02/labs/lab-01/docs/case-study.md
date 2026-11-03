---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Starting Environment

A Python application named `legacy` runs in the namespace `starfleet` as the Deployment `legacy`. Its code is in the ConfigMap `legacy-code` under the key `app.py`, and the Deployment mounts it at `/code`. Prometheus scrapes `legacy:8080` as the job `legacy` every two seconds. The application exposes three metrics that break the rules: `shopOrdersCount` with a `user_id` label whose value is new on every scrape, `shop_checkout_latency_ms` and `shop_cache_size`. The `shuttle` pod has Python and can reach the application and Prometheus.
