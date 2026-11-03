---
draft: true
exam_objectives:
- Instrumentation
- Exporters
---
# Groups, HTTP Methods And Scraping The Pushgateway

The Pushgateway stores metrics in groups. A group is identified by a set of labels called the grouping key, which is part of the URL of every push. The HTTP method that you use decides what the push does to the group. This chapter explains both and shows how Prometheus must be configured to read the result correctly.

## The URL Path

A push goes to a path of this shape:

```text
/metrics/job/<JOB_NAME>/<LABEL_NAME>/<LABEL_VALUE>
```

The segment `job` and its value are required. Further pairs of label name and label value are optional, and each pair adds one label to the grouping key. For example, the path `/metrics/job/nightly_backup/instance/db1` addresses the group with the labels `job="nightly_backup"` and `instance="db1"`.

The Pushgateway adds the grouping labels to every metric in the group. A metric in the request body that already carries one of these labels with a different value is rejected, so keep the grouping labels only in the path.

## The Request Body

The body is the Prometheus text format: one sample per line, optionally preceded by `# HELP` and `# TYPE` lines. The body must end with a newline character. A body without a final newline is rejected as malformed.

An illustrative body for a backup job:

```text
# TYPE batch_duration_seconds gauge
batch_duration_seconds 42
# TYPE batch_last_success_timestamp_seconds gauge
batch_last_success_timestamp_seconds 1700000000
```

The numbers are an example of the format. Pushed samples must not carry explicit timestamps. The Pushgateway rejects them, because the stored values are meant to describe the last push.

## POST, PUT And DELETE

Three HTTP methods change a group.

PUT replaces the whole group. All metrics that were in the group before are removed, and the metrics in the request body become the group.

POST replaces only the metrics of the group that have the same names as the metrics in the request body. Other metrics of the group stay. A POST with a new metric name adds it to the group.

DELETE removes the whole group. The request has no body.

The consequence is important. Two jobs that share a group and use PUT will delete each other's metrics. Use POST when several writers add different metrics to one group, and use PUT when one writer owns the group and wants the stored state to match its last push exactly.

## Choosing The Grouping Key

The grouping key decides which pushes replace which. A job that runs for different databases should push with an `instance` label, for example the database name, so that each database has its own group. Without it, the pushes for different databases replace each other, and only the last one remains.

Keep the key small and stable. A grouping label that changes on every run, such as a run identifier, creates a new group on every push, and the old groups remain until someone deletes them.

## Extra Metrics From The Gateway

The Pushgateway creates two metrics for every group by itself. The gauge `push_time_seconds` holds the time of the last successful push. The gauge `push_failure_time_seconds` holds the time of the last failed push. These values come from the gateway, not from the job, and they have the grouping labels.

`push_time_seconds` is useful for alerts. The age of the last push shows whether the job reports at all, even if the job does not set its own timestamp.

## Scraping The Gateway

Prometheus scrapes the Pushgateway at its `/metrics` endpoint like any other target. The scrape job needs one setting that most targets do not:

```yaml
scrape_configs:
  - job_name: pushgateway
    honor_labels: true
    static_configs:
      - targets: ["pushgateway:9091"]
```

The setting `honor_labels: true` tells Prometheus to keep the `job` and `instance` labels that come with the scraped samples. Without it, Prometheus sees a conflict between the label `job="nightly_backup"` in the data and its own `job="pushgateway"` target label. It then keeps its own value and renames the scraped one to `exported_job`. Queries that select `job="nightly_backup"` then return nothing, and the data hides under `exported_job`.

## The Meaning Of `up`

For the scrape job above, `up` is 1 when the Pushgateway answered the scrape. It says nothing about the batch jobs, because the jobs are not scraped. A dead batch job and a healthy batch job both leave `up` at 1, as long as the gateway runs. Use the timestamp metrics to judge the jobs.

## Pushing From Code

Client libraries offer functions for the three operations. The Python library has `push_to_gateway`, which uses PUT, `pushadd_to_gateway`, which uses POST, and `delete_from_gateway`, which uses DELETE. The Go library has a pusher object whose `Push` method uses PUT and whose `Add` method uses POST. A grouping label is passed as an argument, and the library builds the path.

Check the documentation of your language for the exact signature, since names and defaults differ.

## Pushing From A Shell

A shell script can push with an HTTP client. With `curl`, a push to a group looks like this, where the body comes from standard input:

```sh
cat <<'METRICS' | curl --data-binary @- http://pushgateway:9091/metrics/job/nightly_backup/instance/db1
# TYPE batch_duration_seconds gauge
batch_duration_seconds 42
METRICS
```

The command uses POST because `curl` posts data by default. The option `-X PUT` selects PUT. The `--data-binary` option keeps the final newline of the body.

## Reading Back What Is Stored

Open `/metrics` on the gateway, or query Prometheus after a scrape. In the gateway output, find the lines with the group labels, and look at `push_time_seconds`. In Prometheus, select `batch_duration_seconds{job="nightly_backup"}` and compare the labels with your path.

## What You Know Now

You can build the path of a group, push a body with the correct method, and predict what a second push does to the first one. You know why `honor_labels: true` belongs in the scrape job of the Pushgateway and that `up` describes only the gateway.

## Common pitfalls

> [!WARNING]
> A body without a final newline is rejected. PUT removes every metric of the group that is not in the new body. Without `honor_labels: true`, the job and instance labels are renamed to `exported_job` and `exported_instance`. A grouping label with a changing value creates a new group on every push.
