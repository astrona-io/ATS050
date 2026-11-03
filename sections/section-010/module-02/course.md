---
draft: true
exam_objectives:
- Client Libraries
---
# Metric Types And The Text Exposition Format

Prometheus defines four core metric types and one plain-text format for exposing them. This module explains what each type means, how a histogram and a summary store a distribution, and how to read every line of an endpoint response.

## Learning Goals

- Choose between a counter, a gauge, a histogram and a summary for a given quantity.
- Explain cumulative buckets, the `le` label, `_sum`, `_count` and the `+Inf` bucket.
- Explain why summary quantiles cannot be aggregated across instances.
- Read and write the Prometheus text exposition format, including `# HELP` and `# TYPE` lines.
- Describe how OpenMetrics differs from the classic text format and how a scraper and a target agree on a format.

## Before You Start

You need to know that a client library holds metrics in memory and that Prometheus scrapes them over HTTP. The hands-on page reads the endpoint of a probe application and checks it against Prometheus.

## Reading Order

The first part compares the four types. The second part explains histograms and summaries in detail. The third part covers the exposition format and format negotiation. A guided practice page and a summary follow.

<!-- astrona:playground -->
