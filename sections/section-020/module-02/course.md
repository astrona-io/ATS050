---
draft: true
exam_objectives:
- Instrumentation
- Exporters
---
# Batch Jobs And The Pushgateway

Prometheus collects metrics by pulling them from targets. A batch job that runs for a few seconds and then exits is not a good target, because it may be gone before the next scrape. The Pushgateway is a small server that accepts metrics pushed by such jobs and holds them so that Prometheus can scrape them later. This module explains when to use it, how its grouping works and what its limits are.

## Learning Goals

- Explain why a pull model fails for short-lived jobs and name the cases where the Pushgateway is the right answer.
- Push metrics to a group with the correct HTTP method and path.
- Tell apart the behavior of POST, PUT and DELETE on a group.
- Configure the scrape job for the Pushgateway with `honor_labels: true` and explain what happens without it.
- Describe the operating limits: no expiry, no timestamps, the meaning of `up` and the need for cleanup.

## Before You Start

You need to know what a counter and a gauge are, what a scrape is and how a scrape job is configured. The hands-on page uses a Pushgateway and a Prometheus server in a private kind cluster.

## Reading Order

The first part explains why pull fails for short-lived jobs. The second part describes how the Pushgateway groups and replaces metrics. The third part covers the operating limits and cleanup. A guided practice page and a summary close the module.

<!-- astrona:playground -->
