---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Starting Environment

A Python application named `legacy` runs as the Deployment `legacy` in the namespace `starfleet`. Its code is in the ConfigMap `legacy-code` under the key `app.py`. Prometheus scrapes it as the job `legacy` every two seconds. The configuration is in the ConfigMap `prometheus-config` under the key `prometheus.yaml`, and Prometheus runs with `--web.enable-lifecycle`, so a POST to `/-/reload` makes it read the configuration again. The application exposes `Http_Requests` with the labels `path` and `method` where each path holds a new order number, a gauge `memoryMB` with the value 512, a gauge `build_version` that holds the version in a label and a number in the value, and a gauge `queue_depth_total`. The `shuttle` pod has Python and can reach both services.
