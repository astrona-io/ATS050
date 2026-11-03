---
draft: true
exam_objectives:
- Client Libraries
---
# Summary

Prometheus has four core metric types. A counter only increases and is read through `rate()` or `increase()`. A gauge can rise and fall and is read directly. A histogram counts observations in cumulative buckets and also keeps a sum and a count. A summary calculates quantiles inside one process. The question that the metric answers decides the type.

A histogram exposes one `_bucket` series for each bound, with the label `le`, plus `_sum` and `_count`. The last bucket has the bound `+Inf` and equals the count. All of these series are counters, so bucket rates can be added across instances and turned into a percentile with `histogram_quantile`. The percentile is an estimate, and its accuracy depends on the bucket bounds. A summary quantile is exact for one process but cannot be combined across instances.

The text exposition format lists families with `# HELP` and `# TYPE` lines followed by sample lines made of a name, labels and a value. Prometheus rejects a scrape when a line is invalid. OpenMetrics adds the `# EOF` terminator, the `_total` suffix rule for counters, `_created` samples, units and exemplars. The target chooses the format from the `Accept` header of the scrape request, and Prometheus parses the body by its `Content-Type`.

Key facts:

- Buckets are cumulative, and the `+Inf` bucket equals `_count`.
- Average duration is the rate of `_sum` divided by the rate of `_count`.
- Use a histogram when you need percentiles across several instances.
- One invalid line fails the whole scrape.
- Colons in metric names are reserved for recording rules.

<!-- astrona:playground:destroy -->
