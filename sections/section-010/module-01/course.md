---
draft: true
exam_objectives:
- Client Libraries
---
# Client Libraries, Registries And Metric Lifecycle

A client library is code that you add to an application so the application can keep metrics in memory and expose them over HTTP in a format that Prometheus can scrape. This module explains what the library does for you, what it leaves to you, and how metrics behave over the life of a process.

## Learning Goals

- Explain what a client library does and what the application must still decide.
- Choose the counter, gauge or histogram API from the meaning of the quantity.
- Explain registries, collectors, metric families and the effect of duplicate registration.
- Bound label children and explain the difference between a missing series and a zero.
- Describe how restarts, short-lived processes, multiple workers and concurrent scrapes change the values that Prometheus sees.

## Before You Start

You need a general idea of what an HTTP endpoint is and what a time series is. Every other term is defined where it first appears. The hands-on page uses a small Python probe application running in a private kind cluster together with a Prometheus server. You start the environment with `astrona run`.

## Reading Order

The first part defines the measurement and the metric type that fits it. The second part explains registries, metric families and label children. The third part covers restarts, multiple processes and safe collection. The guided practice page inspects a live endpoint, and the summary closes the module.

<!-- astrona:playground -->
