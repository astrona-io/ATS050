---
draft: true
exam_objectives:
- Client Libraries
---
# Histograms And Summaries In Detail

A histogram looks like a single metric in code, but it produces many series in the endpoint output. A reader who does not know the structure cannot interpret the output, write a correct percentile query or choose useful buckets. This chapter explains the structure line by line, shows how a percentile is estimated, and explains why the estimate has limits.

## The Series Of One Histogram

A histogram named `http_request_duration_seconds` with three bucket bounds exposes these series:

```text
# TYPE http_request_duration_seconds histogram
http_request_duration_seconds_bucket{le="0.1"} 240
http_request_duration_seconds_bucket{le="0.5"} 390
http_request_duration_seconds_bucket{le="1"} 398
http_request_duration_seconds_bucket{le="+Inf"} 400
http_request_duration_seconds_sum 71.2
http_request_duration_seconds_count 400
```

The numbers here are chosen for illustration. Each `_bucket` series has the label `le`, short for less than or equal. The series with `le="0.5"` counts all observations that were 0.5 seconds or less. The value 390 therefore includes the 240 observations that were 0.1 seconds or less.

## Buckets Are Cumulative

Buckets are cumulative: each bucket contains every observation of the smaller buckets. The values never decrease from one bucket to the next. The last bucket has the bound `+Inf`, and it counts all observations. Its value always equals `_count`.

To find how many observations fell between 0.1 and 0.5 seconds, subtract: 390 minus 240 is 150. The number of observations above one second is `_count` minus the value of the `le="1"` bucket, which is 400 minus 398, or 2.

The `_sum` series holds the sum of all observed values, here 71.2 seconds. The average duration over the life of the process is `_sum` divided by `_count`, which is 0.178 seconds. Over a time window, divide the rate of `_sum` by the rate of `_count`.

## All Histogram Series Are Counters

Every histogram series only increases. The buckets, the sum and the count are counters, so `rate()` applies to each of them and handles resets. This is the property that makes a histogram aggregatable. If ten instances expose the same bucket bounds, you can add their bucket rates with `sum by (le)` and get the buckets of the whole service.

The bounds must be identical on every instance that you aggregate. Different bounds on different instances produce a result that cannot be merged correctly. Define the bounds in one shared place in the code.

## Estimating A Percentile

A histogram does not store individual observations, so a percentile is an estimate. The function `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` finds the bucket where the 95th percentile falls. Then it assumes that the observations inside that bucket are spread evenly, and it interpolates linearly between the lower and upper bound.

The accuracy depends on the bucket width. If the 95th percentile falls in a bucket from 0.5 to 1 seconds, the answer is somewhere in that range, and the function can only guess where. An estimate that lies at the edge of a wide bucket can be far from the true value.

Place the bounds so that important thresholds sit on a bucket edge. If your target is that 95 percent of requests finish within 300 milliseconds, include a bucket with `le="0.3"`. Then the fraction of requests within the target is exact: the rate of that bucket divided by the rate of the count.

## Choosing Bucket Bounds

The default buckets of most libraries cover a range from a few milliseconds to ten seconds, and they suit typical web requests. They do not suit every case. A batch job that takes minutes needs bounds in minutes. A cache lookup that takes microseconds needs much smaller bounds.

Choose bounds from the range that you expect, with denser bounds around the service level objective. Do not add dozens of buckets. Every bucket is one series per label combination, so ten buckets and ten label combinations already create one hundred series.

## Summaries And Their Limits

A summary exposes quantiles that the application computed over a sliding window, for example the last ten minutes:

```text
# TYPE rpc_duration_seconds summary
rpc_duration_seconds{quantile="0.5"} 0.012
rpc_duration_seconds{quantile="0.99"} 0.098
rpc_duration_seconds_sum 8120.5
rpc_duration_seconds_count 560000
```

The numbers here are illustrative. A reader gets the quantile directly with no estimation error from bucket width. The cost is that the quantiles are fixed in the code, that they cover one process, and that they cannot be added or averaged correctly across processes. Queries cannot choose a different quantile or a different time window after the fact.

The `_sum` and `_count` series of a summary are counters, and the average duration works the same way as for a histogram.

## Worked Example: A Fleet Percentile

A service runs on five instances. Each instance exposes a histogram with the same bounds. The query `histogram_quantile(0.99, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))` first adds the bucket rates of all five instances, per bound, and then estimates the 99th percentile from the combined buckets. The result describes all requests of the service.

If the same service used a summary, each instance would report its own 99th percentile, and no query could combine the five numbers into the service percentile. That is the practical reason to prefer histograms for services with more than one instance.

## Fraction Of Requests Within A Target

Often the question is not the percentile but the share of requests that met a target. With a bucket at `le="0.3"`, the query `sum(rate(http_request_duration_seconds_bucket{le="0.3"}[5m])) / sum(rate(http_request_duration_seconds_count[5m]))` returns that share as a number between 0 and 1.

This calculation is exact, because it only divides two counter rates. It does not interpolate. That is why a bucket at every threshold that matters is worth more than many evenly spaced buckets.

## What You Know Now

You can read the series of a histogram, calculate a count between two bounds and an average, and explain why a percentile from a histogram is an estimate. You know why summaries do not aggregate. The next question is how all of these series are written as text, and how a scraper and a target agree on the format.

The average from `_sum` and `_count` is exact for the window, and the percentile is an estimate.

## Common pitfalls

> [!WARNING]
> A percentile calculated from wide buckets can be far from the true value. Different bucket bounds on different instances cannot be merged. Averaging per-instance summary quantiles does not give a service-wide quantile.
