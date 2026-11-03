---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Label Design And Info Metrics

Labels let one metric name describe many related series. They are what makes queries such as "requests per route" possible. They also multiply the number of series, and a poorly chosen label makes a metric hard to use. This chapter explains how to choose labels and where descriptive data belongs.

## What A Label Does

A label is a key and a value attached to a series. Series that share a metric name and differ in labels describe the same quantity for different things: different routes, different instances, different outcomes. A query selects series by label, and aggregation functions group or merge them by label.

The unique combination of the metric name and all label pairs identifies one series. If two samples have the same name and the same labels, they belong to the same series.

## Label Or Separate Metric

Use a label when the values describe a dimension of the same quantity, and when the sum over the dimension is meaningful. Requests by route, by method and by status class fit this rule: the sum over all values is the total number of requests.

Use a separate metric when the quantities differ. The number of items in a queue and the number of bytes in the same queue are two different quantities with different units. A label `kind` with the values `items` and `bytes` would give a metric whose sum is meaningless.

A second test is the unit. If two series need different units, they need different metrics.

## Bounded Values

Every distinct combination of label values is one series, and every series costs memory and storage in Prometheus. Label values must therefore come from a set that is small and known in advance.

Good label values include the HTTP method, a route template such as `/orders/{id}`, a status class and the name of a dependency. Dangerous values include user identifiers, email addresses, session tokens, request identifiers, full URLs and timestamps. These sets grow with use, and they can grow without limit.

The detail of cost and control belongs to the study of cardinality. At the stage of design, the rule is short: if you cannot list the possible values, or if the list grows over time, the value does not belong in a label.

## Normalize Before Labeling

Often the real input is unbounded, but a bounded form of it is useful. A URL path `/orders/1234` has an unbounded set of values. The route template `/orders/{id}` has one value for all orders. Record the template.

Do the same for error messages. The text of an error can contain addresses and identifiers. Record an error class, such as `timeout` or `refused`, and keep the full text in logs.

## Consistent Label Names

The same label name must mean the same thing in all metrics. If `route` is the template of a path in one metric, it must not be a full path in another. A dashboard can then use one variable for all panels.

Prometheus reserves the labels `job` and `instance` for the scrape target. Do not use them for other meanings in your metrics. Use specific names, such as `database` or `dependency`, for the things that your program describes.

Do not use a label name that only repeats the metric name or prefix, and do not use labels that duplicate information that Prometheus already attaches.

## Do Not Mix Meanings

Avoid a generic label such as `type` or `kind` that carries different meanings in different series of one metric. A label that carries two unrelated dimensions, for example a `status` that is sometimes an HTTP code and sometimes a job state, makes aggregation wrong. Use one label per dimension.

## Initial Values

A labeled series appears only after its first update. For a small, known set of values, create the series at start-up with the value 0, so that queries and alerts see zero and not a missing series. This applies to bounded sets only.

## Info Metrics

Some data describes a program and does not change from sample to sample: the version, the build commit and the language runtime. Putting it as a label on every metric would multiply series and clutter results.

Instead, expose one gauge with the suffix `_info`, a constant value of 1 and the descriptive data in labels:

```text
# TYPE shop_build_info gauge
shop_build_info{version="2.4.1",commit="abc123"} 1
```

The text above shows the format. Queries can then join the information to other series when needed. When the version changes, the old series ends and a new one starts, which marks a deployment in the graphs. The value is always 1, because the information is in the labels. Do not store the version number as the value, because a value such as 2.4 loses the detail of 2.4.1 and cannot be compared meaningfully.

## Enumerations

A state that has a fixed set of values, such as `ok`, `degraded` and `failed`, can use one series per state. The series for the current state has the value 1, and the others have the value 0. The state name goes in a label, with the metric name describing the thing, for example `shop_service_state{state="ok"} 1`. Keep the set of states small and fixed.

## Target Labels Versus Instrumentation Labels

Labels that identify where a series came from, such as the cluster, the zone or the team, are added by Prometheus through service discovery and relabeling at scrape time. Instrumentation code should not add them. This keeps the code independent of the deployment, and the same binary can run in any environment.

Labels that describe what was measured, such as the route or the method, belong in the instrumentation code.

## A Review Test For Each Label

Before you add a label to a metric, ask four questions about it.

First, can you list every value the label can take? If not, the set is unbounded.

Second, does the sum over all values of the label give a meaningful number? If not, the values belong in separate metrics.

Third, does the label have the same name and meaning in every other metric of the program? If not, rename it or change the meaning.

Fourth, will anyone filter or group by this label in a query, a dashboard or an alert? A label that nobody uses still multiplies series, so remove it.

Apply the same four questions again when a label is changed later, because a change in meaning is a change in the contract of the metric.

## What You Know Now

You can decide between a label and a separate metric by checking whether the sum is meaningful and whether the units match. You know that label values must be bounded and normalized, that label names keep one meaning, and that versions and similar facts belong in an info metric with the value 1.

## Common pitfalls

> [!WARNING]
> A label that carries a user identifier or a raw path grows without limit. A `type` label that mixes unrelated meanings makes sums wrong. A version stored as a numeric value loses information, so use an info metric with labels.
