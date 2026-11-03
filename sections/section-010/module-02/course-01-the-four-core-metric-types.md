---
draft: true
exam_objectives:
- Client Libraries
---
# The Four Core Metric Types

Prometheus stores every sample as a number. The type of a metric tells you how to read that number and which functions are valid on it. A type is not stored inside the time series database in the same way. It is metadata that the client library writes into the exposition output, and that humans and tools use to choose the right query. Choosing the wrong type makes later queries wrong or impossible, so the choice deserves care.

## Counter

A counter is a cumulative value that only increases, or resets to zero when the process restarts. It counts events: requests served, errors returned, bytes sent, tasks completed.

The value of a counter alone has little meaning, because it depends on how long the process has run. The useful quantity is how fast the counter grows. The function `rate(counter[5m])` returns the average per-second increase over the last five minutes. The function `increase(counter[1h])` returns the total growth over an hour. Both handle resets.

Never use a counter for a value that can go down. A counter that is decremented breaks reset detection, because Prometheus reads every decrease as a restart.

## Gauge

A gauge is a value that can rise and fall. It reports a current state: memory in use, the number of items in a queue, the number of requests in progress, a temperature, or the time of the last successful run as a Unix timestamp.

You read a gauge directly, or you aggregate it with `avg`, `max`, `min` or `sum`. For a gauge that changes quickly, the functions `avg_over_time` and `max_over_time` show the behavior inside a window. Do not apply `rate()` to a gauge. The function assumes growth that only increases, and its result for a gauge has no meaning.

A gauge samples a state at scrape time. If the value spikes and returns between two scrapes, the spike is invisible. When the peaks matter, use a counter or a histogram that records every event.

## Histogram

A histogram records observations of a value, usually a duration or a size, and counts them in buckets. Each bucket has an upper bound, and it counts the observations that are less than or equal to that bound. The library also keeps the sum of all observed values and the count of observations.

A histogram answers questions that a gauge cannot. Examples are how many requests took longer than 300 milliseconds, what the 95th percentile of request duration is, and what the average duration is. The histogram stores the data needed for these answers, and the buckets can be added across instances, so the answers hold for a whole fleet.

## Summary

A summary also records observations. Instead of buckets, it calculates quantiles inside the application, over a sliding time window, and exposes them directly. A summary with quantiles 0.5 and 0.99 exposes series with the label `quantile` set to `0.5` and `0.99`, plus `_sum` and `_count`.

The quantiles are exact for that one process. They cannot be combined across instances. The average of the 99th percentiles of ten servers is not the 99th percentile of the whole service. For this reason a histogram is the usual choice when you run more than one instance and need service-wide percentiles. A summary suits a single process, or a case where you need an accurate quantile that you can define in the code.

## Compare The Types

The table lists the main differences.

| Type | Can go down | Key query function | Aggregation across instances |
| --- | --- | --- | --- |
| Counter | No, except a reset | `rate`, `increase` | Sum the rates |
| Gauge | Yes | Read directly, `avg_over_time` | Sum, average, min or max |
| Histogram | No (buckets are counters) | `histogram_quantile` over `rate` of buckets | Sum the bucket rates |
| Summary | No (`_sum` and `_count`) | Read the quantile series | Not valid for quantiles |

## Pick The Type From The Question

Start with the question that the metric must answer. If the answer is how many or how often, use a counter. If the answer is how much right now, use a gauge. If the answer is how long or how big, with a percentile or a threshold, use a histogram. Use a summary only when you cannot use a histogram and you accept that quantiles stay per instance.

A single quantity sometimes needs two metrics. Request duration is a histogram. The number of failed requests is a counter with a status label. Do not try to encode both in one metric.

## Worked Example

A team measures a job queue. The number of jobs waiting is a gauge, because it rises and falls. The number of jobs finished is a counter, because it only grows. The time a job spends in the queue is a histogram, because the team wants the 95th percentile. The time of the last finished job is a gauge that holds a Unix timestamp.

Four questions led to four metrics with three different types. Each query then uses the matching function: `rate()` on the counter, a direct read on the gauges, and `histogram_quantile()` on the histogram buckets.

## Unit And Name Match The Type

The type affects the name. By convention, counters end with `_total`, durations carry the unit `_seconds`, and sizes carry `_bytes`. The Python client library adds the suffix `_total` to a counter name for you in the exposition output, while the Go client expects you to write it in the name. Check how your library behaves so that you do not publish `requests_total_total`.

## Common Wrong Choices

Four mistakes appear often in real code. Each one can be spotted in the exposition output or in a query.

A gauge that holds a running total of events looks fine on a graph. After a restart it drops to zero, and `rate()` is not valid on it, so the application loses the reset handling that a counter provides. Use a counter for event totals.

A counter that holds a current level, such as the number of connected clients, needs decrements. Prometheus reads the decrease as a restart and reports a large false increase. Use a gauge for levels.

An average duration stored in a gauge hides the distribution. Two services with an average of 200 milliseconds can differ greatly: one answers every request in 200 milliseconds, and the other answers most requests in 20 milliseconds and a few in several seconds. Store durations in a histogram and calculate the average or a percentile at query time.

A summary used on ten instances gives ten separate 99th percentiles. A dashboard that averages them shows a number that no user experienced. Use a histogram so that the buckets can be added first and the percentile is calculated after that.

## Metadata Lines Describe The Type

In the exposition output, a `# TYPE` line names the type of each family, and a `# HELP` line gives a short description. For example, `# TYPE queue_jobs_waiting gauge` tells a reader that the family is a gauge. Prometheus uses this metadata when it stores and returns data, and tools such as dashboards use it to suggest functions.

Write a meaningful help text. It is the only documentation that travels with the metric, and the person who finds an unknown series at night reads it first.

## What You Know Now

You can map a question to a type and name the query function that fits it. You know that a counter and a gauge hold one number, while a histogram and a summary hold a distribution. What remains is the structure of the distribution metrics, because a histogram has several series and a summary has a different structure.

## Common pitfalls

> [!WARNING]
> A decreasing value does not belong in a counter. Applying `rate()` to a gauge gives meaningless results. Averaging summary quantiles from several instances produces a number that is not a quantile of the whole service.
