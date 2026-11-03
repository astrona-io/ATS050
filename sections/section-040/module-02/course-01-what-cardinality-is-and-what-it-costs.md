---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# What Cardinality Is And What It Costs

Prometheus stores one time series for each unique combination of a metric name and a set of label pairs. Cardinality is the count of those series. A metric with no labels has a cardinality of one. Adding labels multiplies the count. This chapter shows how to calculate it and why it matters for the cost of a Prometheus server.

## Series Identity

A time series is identified by its metric name and all of its label pairs. The name is stored internally as the label `__name__`, so a series is simply a full set of labels. Two samples with the same set of labels belong to one series. If one label value differs, they belong to two series.

Prometheus also adds labels at scrape time. The label `job` and the label `instance` come from the scrape configuration. Each target therefore has its own series for the same metric. The series count of a metric is multiplied by the number of targets that expose it.

## Multiplication

For one metric, the maximum number of series is the product of the number of values of each label, if all combinations occur. A request counter with the labels `method` with 4 values, `route` with 20 values and `status` with 5 values can have up to 4 times 20 times 5, which is 400 series, for one target.

The product is a maximum. Many combinations never happen, because a route might accept only one method. The real count is the number of combinations that appear in the data. You can count them in a running system.

With 50 instances of the application, the same metric has up to 20000 series in Prometheus. This is why a small label set on one instance can still produce a large load.

## Histograms Multiply Again

A classic histogram exposes one `_bucket` series for each bucket boundary, including the final `+Inf` bucket, plus one `_sum` series and one `_count` series. A histogram with 10 boundaries has 11 bucket series, plus 2, which is 13 series, for each combination of the other labels.

If that histogram has the labels `route` with 20 values and `method` with 4 values, the count is 13 times 20 times 4, which is 1040 series per instance. Adding one more label with 5 values makes it 5200. A histogram is the most expensive common metric type, so each label on it needs a clear reason.

A summary exposes one series for each quantile plus `_sum` and `_count`. It does not multiply by buckets, but its quantiles cannot be combined across instances.

## Unbounded Labels

A bounded label has a fixed set of values, such as a method. An unbounded label takes values from a set that grows, such as a user identifier, a session token, a request identifier, an email address, a raw URL or a timestamp.

A metric with an unbounded label creates a new series for each new value. The series count grows with the number of users or requests, and it does not stop growing as long as the application runs. This is the most common cause of Prometheus servers that run out of memory.

The cost does not stop when the label values stop appearing. A series that no longer receives samples remains in the in-memory head block until the block is compacted to disk, which happens on a schedule of about two hours. It also takes disk space until the retention period ends. A burst of unique values therefore costs memory for hours and disk for the whole retention.

## Where The Cost Appears

Each active series in the head block holds its labels, an index entry and the most recent chunk of samples in memory. A rough planning figure used in the community is a few kilobytes of memory per active series. Treat this as an order of magnitude and measure your own server, because the true figure depends on label sizes and scrape interval.

Series also cost in other places. The index grows, and queries that select a metric by name must look at every series with that name. Queries over high cardinality metrics can load many series and become slow or run out of memory. Compaction takes longer. Remote write sends every sample of every series.

## Churn

Churn is the rate at which series appear and disappear. A series that exists for a short time still costs index entries and compaction work. Common sources are labels that hold pod names or container identifiers when deployments restart often, and labels that hold request identifiers.

High churn and high cardinality are related but different. A server can have a constant number of active series and still suffer from churn if the identity of the series changes all the time. The metric `scrape_series_added` helps to see churn per target.

## What Is Safe

A label is safe when its set of values is small, known and stable. The method, the status class, the route template, the name of a dependency and the name of a deployment environment are safe. As a guide, a label with more than a hundred values deserves a second look, and a label with thousands of values needs a strong reason.

Information that needs unbounded values still has a home. Logs and traces store one record for each event and are designed for high cardinality. A metric answers how often and how long. A log answers which user and which request.

## Calculating Before You Ship

Before releasing new instrumentation, write the calculation: the number of values for each label, the number of buckets, the number of instances. Compare the result with the capacity of the server. This takes a few minutes and avoids an incident.

Do the calculation again when the system grows, because the number of instances and routes grows too.

## A Worked Calculation

An online shop exposes a histogram `shop_request_duration_seconds` with 8 bucket boundaries, so 9 bucket series with `+Inf`, plus `_sum` and `_count`, which is 11 series for each label combination. The labels are `route` with 30 values and `method` with 3 values, but only 40 combinations actually occur.

The series count for one instance is 11 times 40, which is 440. The service runs 25 instances, so Prometheus holds 11000 series for this one histogram.

A developer proposes adding a `customer` label with 2000 values. If each customer calls 5 routes, the combinations grow from 40 to 10000, and the series grow to 11 times 10000 times 25, which is 2750000. One label turned a small metric into a threat for the whole server.

The correct alternative answers the business question differently: log the customer on each request, and keep the metric without the label.

## Stale Series And The Scrape

When a target stops returning a series, Prometheus writes a stale marker at the next scrape. A query then no longer returns that series, even though it is still stored. This is why a query that counts current series can show a small number while the head still holds many series from the last hours.

For this reason, the count that matters for memory is `prometheus_tsdb_head_series`, not the count that a query for one job returns at one moment.

## Counting Instances Correctly

The instance multiplier counts every target that exposes the metric, not only the replicas of one deployment. If two environments are scraped by the same server, both count. If a deployment runs with autoscaling, count the largest number of replicas, because each replica that existed during the retention period left series behind.

Series from replicas that were removed stay in the database until retention ends. A service that scales up and down many times a day therefore leaves many short-lived series, which is churn.

## What You Know Now

You know that each unique label combination is one series, that the count multiplies across labels and instances, and that a histogram multiplies it by the number of buckets plus two. You know that unbounded label values cause growth that does not stop, and that the cost persists in memory and on disk after the values stop appearing.

## Common pitfalls

> [!WARNING]
> Do not add a label to a histogram without calculating the product. Do not use identifiers of users, requests or sessions as label values. The cost of a burst of unique values stays in memory for hours and on disk until retention ends.
