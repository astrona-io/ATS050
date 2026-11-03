---
draft: true
exam_objectives:
- Instrumentation
---
# Instrumenting Requests, Work Queues And Dependencies

Instrumentation is the work of adding code to a program so that it records what it does. This module explains how to decide what to measure, which metrics describe requests, queues and calls to other systems, and how to keep the measurements honest.

## Learning Goals

- Tell online-serving, offline-processing and batch systems apart and name the key metrics of each.
- Instrument a request path with the rate, errors and duration (RED) method.
- Instrument queues, workers and resources with the utilization, saturation and errors (USE) method.
- Instrument a call to a dependency so that its failures and delays are visible separately.
- Use timestamps and in-progress gauges to detect stuck work.

## Before You Start

You need to know what a counter, a gauge and a histogram are, and that Prometheus scrapes metrics over HTTP. The hands-on page uses a probe application and a Prometheus server in a private kind cluster.

## Reading Order

The first part explains what to instrument in each kind of system. The second part covers request metrics. The third part covers queues, workers and dependencies. A guided practice page and a summary close the module.

<!-- astrona:playground -->
