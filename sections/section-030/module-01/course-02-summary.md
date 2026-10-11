---
draft: true
exam_objectives:
- Exporters
---
# Summary

Exporters translate another system's observations into Prometheus metrics. A successful scrape can establish exporter availability while the monitored backend is failing, so explicit backend health and collection evidence are necessary.

Multi-target exporters separate the scraped endpoint from the target being probed. Relabeling, credentials and collection limits must preserve that identity, and partial failures must not be hidden as ordinary zero values.
