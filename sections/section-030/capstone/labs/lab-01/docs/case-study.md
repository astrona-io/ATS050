---
draft: true
exam_objectives:
- Exporters
---
# Starting Environment

A Node Exporter runs at `node-exporter:9100` and reads the ConfigMap `textfile`. Its file `inventory.prom` holds a value that is not a number, so the textfile collector reports an error. A Blackbox Exporter runs at `blackbox-exporter:9115` and offers the module `http_2xx`, but Prometheus has no job that uses it. Prometheus reads its configuration from the ConfigMap `prometheus-config` (key `prometheus.yaml`) and was started with `--web.enable-lifecycle`, so a POST to `/-/reload` makes it read the configuration again. The `probe` application answers at `http://probe:8080/` with status 200 and at `http://probe:8080/work?status=500` with status 500. The `shuttle` pod has Python and can reach all of them.
