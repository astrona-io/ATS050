---
draft: true
exam_objectives:
- Client Libraries
---
# Defining The Measurement Before The API Call

A Prometheus client library is a package for one programming language, such as Go, Python, Java or Ruby, that lets application code create metrics, update them and expose them for collection. It does the parts that are easy to get wrong: thread-safe updates, correct text output and the standard metric types. It does not know what your application is supposed to measure. That decision stays with you, and it must come before the first line of instrumentation code.

## What The Library Provides

A client library gives you four things. It gives you metric types: counter, gauge, histogram and summary. It gives you a registry, which is a container that holds the metrics of one process. It gives you an exposition handler, which is an HTTP handler that writes the registry content in the Prometheus text format. It also usually registers a few default collectors, for example metrics about the process itself such as CPU time and open file descriptors.

Prometheus then scrapes the handler, normally at the path `/metrics`. A scrape is one HTTP GET request that Prometheus sends to a target on a schedule. The response body is a list of samples. Prometheus attaches a timestamp when it stores each sample.

The library keeps only the current value. It does not keep history. History is created by Prometheus, which stores one sample per scrape. This split explains most instrumentation rules: the application holds a small amount of current state, and the server turns that state into time series.

## A Measurement Needs A Definition

Before you create a metric, write down what one unit of the metric means and at which point in the code it changes. A request counter has several possible definitions. It can count requests received, requests that finished, or requests that finished successfully. These three numbers differ whenever a request fails or is still running.

Choose the definition that answers a real operational question. If the question is how many requests the service handled, count at the point where the handler finishes, whatever the result. If the question is how many requests failed, you need the outcome available at that point. A common design is one counter with a bounded `status` label. The total is the sum over all label values, and the failures are the series with an error status.

The mistake to avoid is a name that promises more than the code delivers. A counter called `requests_total` that is incremented only on success silently reports a smaller population than its name states. Every query and dashboard built on it then gives wrong answers.

## Counter, Gauge And Histogram By Meaning

Choose the metric type from the meaning of the quantity, not from the shape you want on a graph.

A counter is a value that only goes up while the process runs. Use it for events that accumulate: requests handled, bytes sent, errors seen. The raw value is rarely useful on its own. Queries apply `rate()` or `increase()` to turn the cumulative value into activity over a time window.

A gauge is a value that can go up and down. Use it for a current state: items in a queue, requests in progress, memory in use, a temperature. You read a gauge directly. You do not apply `rate()` to it.

A histogram records observations, such as durations or sizes, into counting buckets. Use it when you need the distribution of a value, and when you want to calculate percentiles across many instances. The next module explains the structure in detail.

A useful test: if the value can decrease while the process is healthy, it is a gauge. If it can only grow, it is a counter. Using a gauge for an event total is allowed but loses reset handling, and using a counter for a current level cannot be corrected later.

## Choose The Update Point

Where you update the metric matters as much as what you update. Place the update in code that every path goes through. A handler that has an early return for invalid input will skip a counter incremented at the bottom of the function. Many libraries offer a middleware or a wrapper for this reason, so that the update happens once for every request.

For durations, start the timer before the work and observe after it, in a place that runs even when the work fails. In several languages this means a `finally` block or a deferred call. Record the unit in the metric name and use base units: seconds, not milliseconds.

For an in-progress gauge, increment when work starts and decrement when it ends, again on every path. A missed decrement on an error path makes the gauge drift upward, and the metric shows work that no longer exists.

## Worked Example: One Request

Consider an HTTP service with a handler `checkout`. The team asks three questions: how many checkouts happen, how many fail, and how long they take. One design answers all three.

The code defines a counter `shop_checkouts_total` with a label `status` whose values are `success` and `error`, and a histogram `shop_checkout_duration_seconds` without labels. The handler records the start time, runs the work, and in a `finally` block increments the counter with the status and observes the elapsed seconds.

The total checkouts are the sum over both statuses. The failures are the series with `status="error"`. The failure ratio divides one rate by the other. The duration histogram gives the average and the percentiles. Three questions are answered with two metrics, and each metric has a clear definition.

## What The Endpoint Output Shows

When Prometheus scrapes the handler, it receives plain text. For the design above, the output has lines of this shape:

```text
# HELP shop_checkouts_total Completed checkouts.
# TYPE shop_checkouts_total counter
shop_checkouts_total{status="success"} 1027
shop_checkouts_total{status="error"} 13
```

The numbers here are an illustration of the format, not output from a lab. Each line after the comments is one sample: a metric name, a set of labels in braces and a value. The two samples belong to one metric family, because they share a name and a type.

## Initialize Series You Care About

A labeled counter creates a series only after the first update for that label combination. Until the first error happens, the series with `status="error"` does not exist. A query for the failure rate then returns no data instead of zero, and an alert built on it cannot fire or resolve cleanly.

Most libraries let you touch a label combination at start-up so that the series exists with the value zero. Do this for the small, known set of label values, such as the status values. Do not do this for unbounded values.

## Metrics The Library Adds By Default

Most client libraries register default collectors on their default registry. These collectors read values from the runtime or the operating system when Prometheus scrapes. The Go library adds metrics about the Go runtime, such as goroutines and garbage collection, and metrics about the process, such as resident memory and open file descriptors. The Python library adds `process_` metrics and garbage collector statistics.

These default series are useful for finding a leak or a stuck process, and you did not write any code for them. They do not describe your business logic. A process that uses normal memory and CPU can still return an error for every request, so default metrics never replace the instrumentation you define yourself.

## Check The Instrumentation, Not Only The Endpoint

An endpoint that returns valid text proves only that the library works. It does not prove that your code updates the right metric. Test the instrumentation like any other behavior. Send one successful request and one failing request to a test instance, read the endpoint, and confirm that exactly the expected samples changed by exactly the expected amount.

Repeat the check for the paths that are easy to forget: validation errors, timeouts, panics and requests that the client cancels. A metric that is correct on the happy path and silent on the others hides exactly the failures that you want to see.

## Summary Of The Part

You now know that the library holds current values and exposes them, and that the application owns the meaning. You can choose a counter, a gauge or a histogram from the nature of the quantity, and you can place the update where every path passes through it.

## Common pitfalls

> [!WARNING]
> A name must match what the code counts. Updating the metric on only one code path, using milliseconds instead of seconds, or choosing a counter for a value that can fall each produce a metric that looks valid but gives wrong answers. The library cannot detect these mistakes.
