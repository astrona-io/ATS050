---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Changing Names And Reviewing Instrumentation

A metric name and its labels are a contract with every query, dashboard, alert and recording rule that uses them. Prometheus does not track these users. If you rename a metric, the old series stops, and every consumer that still uses the old name silently gets no data. This chapter explains how to change a contract without breaking it and how to review instrumentation before it ships.

## What Breaks When A Name Changes

A rename creates a new series and ends the old one. Prometheus stores no link between the two. A dashboard panel that queries the old name shows data up to the moment of the change and nothing after it. An alert rule that queries the old name sees an empty result, and an empty result is not true, so the alert never fires.

The same applies to labels. Removing a label, renaming it or changing its meaning changes the identity of every series of the metric. Changing the unit of a metric without changing its name is the worst case, because queries keep returning numbers and the numbers are wrong by a constant factor.

## Prefer Not To Change

The cheapest change is the one you avoid. Before you rename, ask whether the old name is wrong or only unattractive. A name that is accurate and follows the conventions should stay. Rename only for a real defect: a wrong unit, a name that promises something the code does not count, or a label that carries unbounded values.

## Running Both Names During A Transition

When a change is needed, publish the new metric next to the old one for a transition period. The application updates both. Consumers move to the new name one at a time. When no query, dashboard or rule uses the old name any more, remove the old metric from the code.

The same method works for labels: add the new metric with the corrected labels, keep the old one, migrate, then remove the old one.

If the application cannot expose both, a recording rule can create the old name from the new one for the duration of the migration. The rule evaluates an expression and stores the result as a new series under the name that the old consumers expect.

## Finding The Consumers

Before you remove an old name, find where it is used. Search the repository that holds dashboards and rule files for the metric name. Query the Prometheus rules API at `/api/v1/rules` to see which loaded rules mention it. Prometheus also exposes the status of its query load in its own metrics, but a search for the name in the stored definitions is the direct check.

Remember that people also run ad hoc queries and keep bookmarks. A transition period of one or more retention cycles for important metrics gives them time to move.

## Naming Recording Rules

A recording rule evaluates an expression on a schedule and stores the result as a new series. Its name follows a fixed pattern of three parts separated by colons: the labels that the result keeps, the name of the source metric, and the operation that produced it. An example is `route:lab_requests:rate5m`.

This pattern tells a reader what the series contains without reading the rule. The source metric name is kept as it is, including its unit, and the suffix `_total` of a counter is removed once `rate()` is applied, because the result is no longer a cumulative total.

Colons are reserved for recording rule names. Do not use them in names that application code or exporters create.

## Rate Of A Counter Is Not A Counter

A series produced by `rate()` is a gauge that describes a per-second value. Name it for what it now is. A name that keeps `_total` on a rate result misleads the next reader into applying `rate()` a second time.

## A Review Checklist

Use the same short list for every review of new or changed instrumentation.

- The name starts with the name of the application or subsystem and describes one quantity.
- The unit is a base unit and is the last word before the type suffix.
- Counters end in `_total`. Info metrics end in `_info`. Timestamps end in `_timestamp_seconds`.
- Every label has a bounded, listable set of values.
- Label names mean the same thing in every metric.
- The sum over each label is meaningful, or the label is not present.
- No label carries an identifier of a user, a request, a session or a full URL.
- Series for known label values exist from start-up with the value zero.
- The update happens on every code path, including errors and timeouts.
- Help text states what the metric measures and in which unit.

## Reviewing Against Real Output

Review the output of the endpoint, not only the code. Fetch the page, read the names and labels, and look for surprises: a label with many values, two metrics that look like one quantity, a name with a unit in non-base form, or a counter without the suffix.

Count the series. A short check is to count the lines for each metric family. A family with many more lines than the number of label combinations that you expect has a label that you did not expect.

## Tooling

Prometheus provides a command-line tool, `promtool`, with a `check metrics` command that reads metrics in the text format from standard input and reports lint problems, such as a counter without the `_total` suffix. Running it against the endpoint output in a continuous integration job catches naming mistakes before they reach production. Treat its output as advice from a set of rules, and decide each case on its meaning.

## A Worked Rename

Suppose a service exposes `shop_latency_ms`, a gauge that holds the last request duration in milliseconds. The unit is not a base unit, the type hides the distribution, and the name does not say what is measured.

The corrected design is a histogram named `shop_request_duration_seconds`. The code adds it and keeps updating the old gauge for the transition. Dashboards and rules are changed one at a time to use `histogram_quantile` on the new histogram. When a search of the dashboards and of the loaded rules finds no use of `shop_latency_ms`, a later release removes the gauge.

During the transition, both series exist. Queries on the old name keep working and report the old, weaker data. Queries on the new name report the better data. Nothing breaks at any step, because no step removes something that is still in use.

## Changing A Label

The same steps apply when a label changes. If the label `path` holds raw URLs, the fix is a new label `route` that holds the template. Expose both for a period, move the queries to `route`, and then remove `path`.

Removing the unbounded label is also the moment when the number of series falls, because the old series stop receiving samples and leave the head of the database after a short time.

## What You Know Now

You know that a rename or label change breaks every consumer without any error. You can run the old and the new metric together, find the consumers, and remove the old one at the end. You can name a recording rule by its labels, source and operation, and you have a checklist for reviewing instrumentation against real endpoint output.

## Common pitfalls

> [!WARNING]
> Never change the unit of a metric under the same name. Never remove an old name before you have searched the dashboards and rules for it. A missing series produces an empty result, and an alert that gets an empty result does not fire.
