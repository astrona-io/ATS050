---
draft: true
exam_objectives:
- Exporters
- Instrumentation
---
# Node Exporter And The Textfile Collector

The Node Exporter is the standard exporter for machine metrics: CPU, memory, disks and network. It also has a collector that reads metrics from files, which lets scripts and batch jobs on a machine publish their own values through the same endpoint. This module explains how that collector works, how to write correct files and how to operate the exporter.

## Learning Goals

- Explain what the Node Exporter exposes and how collectors are enabled and disabled.
- Configure and use the textfile collector for metrics written by scripts and jobs.
- Write metric files that the collector accepts, and publish them without partial reads.
- Detect failed reads, stale files and duplicate metrics with the metrics that the exporter provides.
- Choose between the textfile collector and the Pushgateway for a batch job.

## Before You Start

You need to know the Prometheus text format and what a scrape job is. The hands-on page uses a Node Exporter, a Prometheus server and a ConfigMap that holds the metric files, in a private kind cluster.

## Reading Order

The first part explains the Node Exporter and the textfile mechanism. The second part describes how to write and publish files correctly. The third part covers operating the exporter and choosing the right tool for batch metrics. A guided practice page and a summary close the module.

<!-- astrona:playground -->
