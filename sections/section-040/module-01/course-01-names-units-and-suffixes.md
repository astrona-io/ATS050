---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Names, Units And Suffixes

A metric name says what is measured. Prometheus stores the name as the label `__name__`, and every query starts from it. The conventions in this chapter come from the Prometheus documentation on metric and label naming. They are conventions, not rules that the server enforces, but tools, dashboards and people rely on them.

## What The Server Accepts

A metric name may contain ASCII letters, digits, underscores and colons, and it must not start with a digit. The colon is reserved for names that users define in recording rules, so instrumentation code must not use it. Newer versions of Prometheus also accept other characters in quoted names, but exporters and client libraries keep to the classic form.

A label name may contain ASCII letters, digits and underscores, and must not start with a digit. Label names that begin with two underscores are reserved for internal use by Prometheus.

## The Naming Pattern

The common pattern is `<prefix>_<what is measured>_<unit>`, with a suffix that matches the type when needed. For example, `http_request_duration_seconds` tells the reader the area (HTTP requests), the quantity (duration) and the unit (seconds).

Use lowercase letters with underscores between words. This style is called snake case. Names such as `shopOrdersCount` or `Http_Requests` break the convention, and queries become harder to remember and type.

## The Prefix

Start the name with a prefix that names the application or the library, as a single word. For example, `prometheus_notifications_total` belongs to Prometheus itself, and `process_cpu_seconds_total` belongs to the process collector in a client library.

The prefix keeps names from different programs apart, and it lets a reader find all metrics of one program by the start of the name. Do not use the prefix of another project for your own metrics.

## Base Units

Use base units, without prefixes such as milli or kilo. The common base units are seconds for time, bytes for data, meters for length and volts for voltage. Use ratios from 0 to 1 and not percentages.

The reason is arithmetic. A query that mixes values with different units gives wrong results without an error. If every metric uses seconds, a duration from one program can be compared with a duration from another. Conversion for display belongs in the dashboard, where the unit can be shown next to the axis.

Write the unit as the last word of the name before any type suffix: `_seconds`, `_bytes`, `_meters`, `_ratio`. A name with `_ms`, `_mb` or `MB` shows a non-base unit and should be changed in the code.

## One Unit Per Metric

A metric has one unit for all its series. Do not use a label to switch units, such as a label `unit="bytes"` and `unit="kilobytes"` on the same metric. Such a metric cannot be summed.

## Type Suffixes

A counter has the suffix `_total`. The name `http_requests_total` tells the reader that it is a cumulative count and that it needs `rate()`. When a counter has a unit, put the unit before the suffix: `process_cpu_seconds_total`.

A histogram creates three series with the suffixes `_bucket`, `_sum` and `_count`. A summary creates `_sum` and `_count`, and series with a `quantile` label. These suffixes belong to the histogram and the summary. Do not use `_sum`, `_count` or `_bucket` for names of other metrics, because queries could mistake them for histogram parts.

A gauge has no type suffix. Do not add `_total` to a gauge: the suffix claims a counter, and a reader would apply `rate()` to a value that goes up and down.

## Special Suffixes

A metric that holds a Unix time uses the suffix `_timestamp_seconds`, for example `batch_last_success_timestamp_seconds`. The suffix `_info` marks an info metric. The suffix `_ratio` is for values from 0 to 1.

Do not use `_created` for new metrics, because OpenMetrics uses it for the creation time of a counter.

## Names Describe The Quantity

A name must describe what the metric measures and must not describe where it came from or how it is labeled. A metric called `requests_by_status_total` repeats information that a `status` label holds. A name that includes a label value, such as `requests_status_500_total`, creates one metric per value and breaks aggregation.

A useful test is that the sum or the average over all label values of the metric should be meaningful. The sum of `http_requests_total` over all routes and methods is the number of requests. The sum of a metric that mixes requests and errors is not meaningful, and it should be split.

## Names Are Not Computed At Runtime

Do not build metric names from input at runtime, for example a name with a customer or a route in it. Each name is a separate metric family, and queries cannot select them with one selector. Use a label for the varying part, with bounded values.

## Examples

The table below contrasts weak names with better ones.

| Weak name | Problem | Better name |
|---|---|---|
| `shopOrdersCount` | Capital letters, no `_total` | `shop_orders_total` |
| `checkout_latency_ms` | Milliseconds | `checkout_duration_seconds` |
| `memoryMB` | Capitals, non-base unit | `memory_bytes` |
| `queue_depth_total` | `_total` on a gauge | `queue_depth` |
| `errors_500_total` | Value in the name | `errors_total{status="500"}` |

## Durations, Sizes And Counts

A duration is measured in seconds, even when the operation takes only microseconds. The value 0.00025 is correct, and a dashboard can show it as 250 microseconds.

A size of data is measured in bytes. For a count of items, such as the entries of a cache, use the plural noun without a unit: `cache_entries`. A count of events that accumulate is a counter with `_total`, for example `cache_evictions_total`.

## Following Existing Conventions

When a library or exporter already names a quantity, use the same name. If your program exposes CPU time of a process, the client library's `process_cpu_seconds_total` is the name that dashboards expect. Inventing a second name makes every shared dashboard fail for your program.

## What You Know Now

You can write a metric name from a prefix, a quantity and a base unit, and add the suffix that fits the type. You know which characters are valid, which names to avoid and why values must never appear inside a name.

## Common pitfalls

> [!WARNING]
> A unit in the name must match the real unit of the value, because nothing in Prometheus checks it. Adding `_total` to a gauge makes readers apply `rate()` to it. Building a name from runtime input creates a separate metric family for every value.
