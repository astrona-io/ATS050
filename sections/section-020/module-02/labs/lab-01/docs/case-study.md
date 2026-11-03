---
draft: true
exam_objectives:
- Instrumentation
---
# Starting Environment

A Pushgateway runs at `pushgateway:9091` in the `starfleet` namespace. A Prometheus server scrapes it every two seconds with `honor_labels: true`, and also scrapes the `probe` application. The `shuttle` pod has Python and can reach the Pushgateway and Prometheus. The nightly backup job has never reported: the gateway holds no group for it.
