---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Finding High Cardinality

When a Prometheus server uses too much memory or queries become slow, the first task is to find which metrics and labels have the most series. Prometheus gives you several tools for this: its own metrics about the database, the automatic metrics for each scrape, the TSDB status API and queries that count series.

## Total Series In The Head

The metric `prometheus_tsdb_head_series` is a gauge exposed by Prometheus about itself. It holds the number of series currently in the head block, which is the in-memory part of the time series database, abbreviated TSDB. A steady value means a stable system. A line that climbs without leveling off is a warning.

The counter `prometheus_tsdb_head_series_created_total` counts every series ever created in the head. Applying `rate()` to it shows the creation rate, which is a measure of churn. A high rate with a flat `prometheus_tsdb_head_series` means series are created and removed at the same speed.

These metrics describe the whole server. They do not say which application causes the growth.

## Automatic Metrics Per Target

Each scrape produces automatic series with the labels of the target. Three of them help with cardinality.

`scrape_samples_scraped` is the number of samples that the target returned. `scrape_samples_post_metric_relabeling` is the number that remain after `metric_relabel_configs` ran. `scrape_series_added` is an approximate count of series that are new in the latest scrape.

Compare the targets with a query such as `topk(5, scrape_samples_scraped)`. The target with the highest number is the first suspect. A target where `scrape_series_added` stays above zero scrape after scrape is creating new series continuously, which means an unbounded label.

## Counting Series By Metric Name

The query `count by (__name__) ({job="legacy"})` returns one result for each metric name of a job with the number of series that currently exist. Replace the job with any selector.

To rank all metric names on the server, use `topk(10, count by (__name__) ({__name__=~".+"}))`. This query selects every series, so it is expensive on a large server. Run it with care, and prefer the status API below when the server is already under strain.

## The TSDB Status API

The endpoint `/api/v1/status/tsdb` returns a summary of the head block. The response has lists named `seriesCountByMetricName`, `labelValueCountByLabelName`, `memoryInBytesByLabelName` and `seriesCountByLabelValuePair`. Each list shows the top entries with a count or a size.

These lists answer directly: which metric names have the most series, which label names have the most distinct values, which label names use the most memory, and which label value pairs are attached to the most series. A label name that has thousands of distinct values and a high memory figure is the likely culprit.

The Prometheus web interface shows the same data on the TSDB status page. The API form is useful in scripts and in this course, because the environment has no browser.

## Finding The Offending Label

After you know the metric name, find the label. Use `count(count by (user_id) (shopOrdersCount))` style queries: the inner query groups by one label, and the outer query counts the groups. This returns the number of distinct values of that label in the metric. Run it once for each label of the metric. The label with a value close to the series count is the one that multiplies.

Another approach is to print a few raw series, for example with `topk(5, shopOrdersCount)`, and read the labels by eye. Identifiers are easy to recognize.

## Reading Growth Over Time

A single count says how large the problem is now. The trend says whether it is growing. Graph `prometheus_tsdb_head_series` or `count({job="legacy"})` over a day. Linear growth with traffic points to an unbounded label. Growth in steps at each deployment points to labels that hold version or pod identifiers.

Also compare `scrape_series_added` before and after a release. A release that raises it has introduced new series.

## Finding The Source In Code

The status API points to a metric and a label. The code that sets the label is in the application repository. Search for the metric name in code, find where its labels are filled, and check whether the value comes from a request, a user record or a user-supplied string.

Many cases come from a framework that records the raw request path. The correct fix is to record the route template that the framework matched, not the path of the request.

## Alerting On Growth

Do not wait for an outage. Alert on `prometheus_tsdb_head_series` above a threshold that you chose from capacity planning, and on a high rate of `prometheus_tsdb_head_series_created_total`. For each application, alert when `scrape_samples_scraped` exceeds a number that is well above its normal size.

These alerts tell the owning team quickly, while the cost is still small.

## A Short Diagnosis Path

Follow the same steps each time, so the diagnosis is quick and complete.

1. Read `prometheus_tsdb_head_series` and its creation rate to confirm that growth exists.
2. Rank the targets by `scrape_samples_scraped` and by `scrape_series_added` to find the application.
3. Read the TSDB status API to find the metric name and the label name with the most values.
4. Count the distinct values of that label to confirm it.
5. Read the code that fills the label and decide on the fix.

Write down the numbers you find before and after the fix, so that you can show that the fix worked.

## Limits Of These Tools

The status API describes the head block only. Series that already moved to disk blocks do not appear in it. For a historical view, rely on the graphs of the head series count.

The query counts use the lookback window of 5 minutes by default and the stale markers, so they describe what is currently visible. They are best for comparing metrics with each other, not for exact accounting.

## Reading The Target List

The targets API at `/api/v1/targets` lists each target with its labels, its last scrape duration and its last error. A target that returns thousands of samples also tends to have a long scrape duration. Sort by `lastScrapeDuration` to find targets that are costly to scrape, and then check their sample counts.

## What You Know Now

You can read the head series count and the creation rate, compare targets with the automatic scrape metrics, count series by metric name, and use the TSDB status API to find the metric names and label names with the most series. You can find the label that multiplies by counting its distinct values.

## Common pitfalls

> [!WARNING]
> A query that selects every series on a large server is itself expensive. Use the status API first. A flat series count does not prove that there is no problem, because churn can be high while the count stays constant.
