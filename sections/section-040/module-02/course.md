---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Labels And Cardinality

Every distinct combination of a metric name and label values is one time series, and Prometheus pays memory, disk and query time for every series. Cardinality is the number of series. This module explains how labels multiply series, how to find the metrics that cost the most, and how to keep the number under control at the source and at the server.

## Learning Goals

- Calculate the number of series that a metric produces from its labels and its type.
- Explain why unbounded label values cause growth that never stops.
- Find the metrics and labels with the most series using Prometheus' own metrics and the TSDB status API.
- Reduce cardinality in the application, with relabeling at scrape time, and with recording rules.
- Use `sample_limit` and `label_limit` to protect a Prometheus server, and describe what happens when a limit is exceeded.

## Before You Start

You need to know what a label is, how a counter and a histogram are exposed, and how a scrape job is configured. The hands-on page uses a `legacy` application whose metrics break several rules, together with a Prometheus server in a private kind cluster.

## Reading Order

The first part explains what cardinality is and what it costs. The second part shows how to find the source of high cardinality. The third part covers the controls: fixing the source, relabeling, limits and recording rules. A guided practice page and a summary close the module.

<!-- astrona:playground -->
