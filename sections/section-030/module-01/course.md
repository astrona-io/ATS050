---
draft: true
exam_objectives:
- Exporters
---
# Exporters, Target Failure And Multi-Target Probes

An exporter is a program that reads the state of a system that Prometheus cannot scrape directly and presents it as metrics at an HTTP endpoint. This module explains what an exporter must do, what the `up` metric does and does not say, and how one exporter can probe many targets.

## Learning Goals

- Explain how an exporter translates the state of an external system into metrics.
- Distinguish the health of a scrape from the health of the backend system.
- Describe the multi-target exporter pattern and the relabeling that it needs.
- Control collection cost, credentials and partial failures.
- Diagnose a missing metric by checking each stage from the backend to the query.

## Before You Start

You need to know what a scrape is, what a scrape job is and how the Prometheus text format looks. The hands-on page uses the `probe` application and a Prometheus server in a private kind cluster.

## Reading Order

The first part explains how an exporter translates state into metrics. The second part separates scrape health from backend health and shows how to diagnose a missing metric. The third part covers the multi-target pattern, credentials and cost. A guided practice page and a summary close the module.

<!-- astrona:playground -->
