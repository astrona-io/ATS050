---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Controlling Cardinality

Once you know which metric and label cause the growth, there are four places to act: the application, the scrape configuration, the limits of the scrape job and the queries that consume the data. They differ in effect, in cost and in who owns them. This chapter explains each and when to use it.

## Fix It At The Source

The best fix removes the unbounded label in the application. After the fix, the series are never created. Nothing downstream has to compensate, and the application owner learns the rule.

Typical fixes are to record a route template instead of a raw path, to record a class of error instead of an error message, to remove an identifier of a user or request from the labels, and to put the detail in a log line instead. If a business question needs per-customer numbers, answer it from logs or from a separate analytics system.

A source fix needs a release of the application. When that is not possible quickly, use the scrape-side controls below as protection until it ships.

## Drop At Scrape Time With metric_relabel_configs

The scrape job option `metric_relabel_configs` runs rules on every scraped sample after the scrape and before storage. Each rule has an `action`. The actions that matter for cardinality are `drop`, `keep`, `labeldrop` and `labelkeep`.

The action `drop` removes samples whose source labels match a regular expression. The special label `__name__` holds the metric name, so a rule can drop a whole metric:

```yaml
metric_relabel_configs:
- source_labels: [__name__]
  regex: shop_debug_.*
  action: drop
```

The action `labeldrop` removes labels whose names match a regular expression. It does not look at values. The rule below removes the label `user_id` from every sample of the job:

```yaml
metric_relabel_configs:
- regex: user_id
  action: labeldrop
```

Relabeling saves storage and memory, but the application still produces and sends the data, so the scrape cost on the network and on the application side stays.

## The Collision Problem

Dropping a label can make several series identical. If the series `a{user_id="1"}`, `a{user_id="2"}` and `a{user_id="3"}` lose the label `user_id`, all three become `a{}` in one scrape. Prometheus cannot store three different values for one series at the same timestamp. It keeps one and rejects the rest, and the stored value is not a sum.

This means `labeldrop` is correct only when the remaining labels still identify each sample uniquely. When the dropped label was a real dimension, the result is wrong data, not smaller data. Check the labels of the remaining series first.

## Limits On The Scrape Job

A scrape job can protect the server with limits. They are fields of the job, and the default value of each is zero, which means no limit.

`sample_limit` is the maximum number of samples that one scrape may contribute after `metric_relabel_configs` ran. If a target returns more samples, Prometheus treats the whole scrape as failed. It stores none of the samples of that scrape, and the series `up` for the target becomes 0.

`label_limit` is the maximum number of labels that one sample may have. `label_name_length_limit` and `label_value_length_limit` cap the length in characters. A sample that breaks them fails the whole scrape in the same way.

`target_limit` is the maximum number of targets that one job may have after service discovery and relabeling. Exceeding it makes all targets of the job fail their scrapes.

## What A Limit Does And Does Not Do

A limit is a circuit breaker, not a filter. It does not keep the first part of the samples. It rejects all of them. A target that exceeds the limit disappears from your graphs completely, and an alert on `up == 0` fires.

This is intended. A target that suddenly returns far more samples than before is a likely problem, and rejecting it protects every other target on the server. Set the limit with a margin above the normal size, for example 20 percent above the largest value of `scrape_samples_post_metric_relabeling` that you observe over a typical week.

Do not set the limit equal to the current size, because normal changes in traffic would then trigger failures.

## Check A Limit Is Working

After you add a limit, compare `scrape_samples_post_metric_relabeling` with the limit. The targets API shows the last error of a failed scrape, and the message says that the sample limit was exceeded. In the Prometheus configuration API at `/api/v1/status/config`, the limit appears in the running configuration of the job, which confirms that a reload took effect.

## Recording Rules To Reduce Query Cost

A recording rule evaluates an expression on a schedule and stores the result as a new series. A rule that aggregates away a label creates a series set that is much smaller than the source. Dashboards and alerts then read the small set.

This does not reduce what Prometheus stores of the source metric. It reduces the cost of queries and the load of dashboards. To also reduce storage, combine it with a drop of the source series, but only when nothing needs the detailed data.

An example is a rule that sums the request rate by route and discards the instance:

```yaml
groups:
- name: routes
  rules:
  - record: route:lab_requests:rate5m
    expr: sum by (route) (rate(lab_requests_total[5m]))
```

The example shows the format. The metric in the rule must have a `route` label for the rule to produce results.

## Choose The Right Control

Use the source fix when you own the application and can release. Use `labeldrop` or `drop` when you do not own the code or need a quick reduction, and when the remaining labels stay unique. Use limits on every job as a safety net. Use recording rules to make queries cheap.

The controls combine. A common design is a source fix as the lasting solution, limits as the safety net, and recording rules for the dashboards.

## Reloading The Configuration

Changes to scrape configuration take effect after Prometheus reloads. Prometheus reloads when it receives the signal SIGHUP, or when an HTTP POST arrives at `/-/reload`, if the server runs with the flag `--web.enable-lifecycle`. After a reload, check that it succeeded: a configuration with a syntax error is rejected and the old configuration stays active.

Validate the file before the reload with `promtool check config`. It reports errors in the file.

## What You Know Now

You know the four places to control cardinality and when to use each. You know that `metric_relabel_configs` can drop metrics and labels at scrape time, and that dropping a label is safe only when the remaining labels stay unique. You know that `sample_limit` and `label_limit` fail the whole scrape and set `up` to 0, and that a limit is a safety net with a margin.

## Common pitfalls

> [!WARNING]
> Do not drop a label that was a real dimension, because several series then collide and Prometheus keeps one of them. Do not set `sample_limit` to the current size. A scrape that exceeds the limit stores nothing at all, so the target disappears from your graphs.
