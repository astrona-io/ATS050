---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Metric Names, Units And Stable Label Design

A metric name and its labels are the interface between the code that produces a metric and every query, dashboard and alert that uses it. A name that follows the conventions is easy to find, easy to combine and hard to misread. This module explains the naming rules, the choice between labels and separate metrics, and how to change names without breaking users.

## Learning Goals

- Name metrics by the quantity that they measure, with a base unit and the correct suffix for their type.
- Decide when a distinction belongs in a label and when it needs a separate metric.
- Keep label meanings consistent and label values bounded.
- Use info metrics for descriptive data such as versions.
- Change an instrumentation contract in a way that does not silently break dashboards and alerts.

## Before You Start

You need to know the four metric types and the Prometheus text format. The hands-on page uses the `probe` application and a Prometheus server in a private kind cluster.

## Reading Order

The first part explains metric names, units and suffixes. The second part covers label design and info metrics. The third part describes how to change names and labels safely and how to review instrumentation. A guided practice page and a summary close the module.

<!-- astrona:playground -->
