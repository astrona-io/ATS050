---
draft: true
exam_objectives:
- Exporters
---
# Starting Environment

A Node Exporter runs at `node-exporter:9100` in the `starfleet` namespace with the flag `--collector.textfile.directory=/textfile`. The directory is a volume from the ConfigMap `textfile`, which holds only a README file. Prometheus scrapes the exporter as the job `node` every two seconds. The `shuttle` pod has Python and can reach the exporter and Prometheus. A change to the ConfigMap reaches the exporter after the kubelet has synced the volume, which can take up to two minutes.
