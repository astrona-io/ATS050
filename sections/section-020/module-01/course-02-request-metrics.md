---
draft: true
exam_objectives:
- Instrumentation
---
# Request Metrics: Rate, Errors And Duration

Most incidents are noticed by the same three symptoms: fewer requests than usual, more failures than usual, or slower answers than usual. The RED method turns these symptoms into three metrics for every service that handles requests. RED stands for rate, errors and duration. This chapter shows how to define each one precisely, how to write the queries and where the usual mistakes come from.

## Rate

The request rate is the number of requests per second that the service handles. Record it with a counter that increments once for each completed request. The counter name ends with `_total`, for example `shop_http_requests_total`.

You never read the counter directly. The query `sum(rate(shop_http_requests_total[5m]))` returns the average rate of requests per second over five minutes for the whole service. Adding `by (route)` splits the rate by route.

Decide the moment of counting. Counting at completion includes the outcome, which the error metric needs. Counting at arrival shows load even when requests never finish, for instance because the process is stuck. The in-progress gauge, described below, covers that second case.

## Errors

An error is a request that did not give the caller what it needed. Add a label with a small set of outcomes to the request counter, for example `status_class` with the values `2xx`, `4xx` and `5xx`, or a boolean-like `outcome` label with `success` and `error`. Keep the set small, because the values multiply the series count.

The error ratio is the failures divided by all requests: `sum(rate(shop_http_requests_total{status_class="5xx"}[5m])) / sum(rate(shop_http_requests_total[5m]))`. A ratio is better than a raw error count for alerts, because the same number of errors means something different at 10 requests per second than at 10,000.

Some errors never produce a response, such as a request that times out in a load balancer. Count what your service can see, and know what it cannot see. A client-side or edge metric covers the rest.

## Duration

Duration is the time from the start to the end of handling a request. Record it with a histogram, in seconds, for example `shop_http_request_duration_seconds`. The histogram supports percentiles and fractions that meet a target, and it can be added across instances.

Start the timer as early as possible, before routing and middleware that you want to include, and stop it after the response has been written. Measure in a place that runs on every path, including errors.

Record the duration of failed requests as well, but consider a label that separates them. A failure that returns quickly, such as a rejected input, lowers the average and can hide slow successful requests. The `outcome` label lets a query look at successful requests only.

## In-Progress Requests

A gauge that counts requests in progress shows concurrency. Increment it when a request starts and decrement it when the request ends, on every path. The value rises when requests are slow or blocked, often before errors appear.

A gauge that never returns to zero after traffic stops signals a leak: a path that increments and does not decrement. Test this on error paths and on cancelled requests.

## Choosing Labels

Use labels that you will group or filter by in queries and that have a bounded set of values. Good labels for requests are the method, a route template and a status class. The route template is the pattern, such as `/orders/{id}`, and not the real path.

Avoid the status code as a label unless you need it. Each distinct code is a separate value, and rare codes create series that appear and disappear. A status class is usually enough for alerts, and logs hold the exact code.

## Worked Example: Reading The Three Metrics

A service shows a request rate that is half of the normal value, an error ratio near zero and a normal median duration. The in-progress gauge is high. This combination points to requests that start and do not finish. The cause could be a blocked dependency, so the next step is to look at the dependency metrics.

Another service shows a normal rate and a rising error ratio with short durations. The failures are fast, which suggests a rejection such as a bad configuration or an open circuit breaker. The same ratio with long durations suggests timeouts. The three metrics together narrow the cause, and no single one would.

## Instrument Once, In One Place

Place request metrics in a middleware, an interceptor or a wrapper around the handler, so that every route is measured the same way. When each handler writes its own metrics, the names, labels and units drift apart, and a new route often ships without any measurement.

Most web frameworks have a Prometheus integration that does this. Check its defaults: the bucket bounds, the way it names routes and whether it records the path or the route template. A framework that records raw paths creates unbounded labels.

## Queries For Each Signal

The rate query uses a window of at least four scrape intervals, so that one missed scrape does not leave a gap. With a scrape interval of 15 seconds, a window of one minute or more is safe.

For the 95th percentile of duration, use `histogram_quantile(0.95, sum by (le) (rate(shop_http_request_duration_seconds_bucket[5m])))`. The `sum by (le)` step adds the buckets of all instances before the quantile is estimated. Averaging per-instance percentiles gives a wrong result, because a percentile cannot be averaged.

For the fraction of requests faster than a target, divide the rate of the bucket whose `le` equals the target by the rate of the `_count` series. This works only when the target is one of the bucket bounds, so choose bounds that include your service level targets.

## Handling Client Errors

A response with a 4xx status means the caller sent a bad request. It is usually not a fault of the service. Counting all 4xx responses as errors can trigger alerts for a client that sends invalid input. Many teams count only 5xx responses as service errors and keep 4xx visible as a separate class.

There are exceptions. A 429 response means the service rejected work because of load, and that is relevant to the service owner. A 404 for a route that should exist can signal a broken deployment. Decide per status class and write the decision down next to the metric definition.

## Retries And Double Counting

When a client retries a failed request, the service sees two requests. The rate rises while the failures are still present. During an incident, retries can double the load. The request counter reports what the service received, so a rise in rate together with a rise in errors often indicates retries and not new demand.

If the service itself calls another service and retries, count the outgoing attempts with their own metric. One counter for incoming requests and one for outgoing calls keeps the two populations apart.

## Instrumenting Batch Of Work Inside A Request

Some requests carry many items, for example a bulk import with 500 records. The request counter counts one request. If the question is how many records were processed, add a separate counter for records. Do not add the item count to the request counter, because that mixes two units under one name.

The same rule applies to duration. The request histogram measures the whole request. A separate histogram for per-item time shows whether slowness comes from a few items or from all of them.

## What You Know Now

You can define rate, errors and duration for a service, write the matching counter, histogram and gauge, and write queries for the ratio and for percentiles. You know that labels must stay bounded. The systems behind a request, such as queues and dependencies, need their own metrics.

## Common pitfalls

> [!WARNING]
> An error ratio can hide a problem when requests never finish, so keep the in-progress gauge next to it. Raw paths as labels create unbounded series. Durations of fast failures can lower the average and hide slow successes.
