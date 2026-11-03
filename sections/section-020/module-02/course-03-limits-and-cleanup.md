---
draft: true
exam_objectives:
- Instrumentation
- Exporters
---
# Operating Limits And Cleanup

The Pushgateway is simple, and its simplicity brings limits that you must plan for. It never expires data, it has no view of whether a job is alive and it is one more component that can fail. This chapter lists the limits and the practices that keep the gateway correct.

## Metrics Never Expire

The Pushgateway keeps the last pushed value of every metric until the group is replaced or deleted. It does not drop a value because it is old. A job that was removed a year ago still has its metrics in the gateway, and Prometheus still scrapes them as if they were fresh.

The scraped samples get a new timestamp at every scrape. The value looks current, but the real age is only visible in the metrics that the job pushed: its own timestamp gauge, and the gateway's `push_time_seconds`.

Two practices follow. Always push a timestamp of the last success, and always alert on its age and not on its presence.

## Deleting Groups

Remove a group when its job is retired. Send DELETE to the same path that the job used:

```sh
curl -X DELETE http://pushgateway:9091/metrics/job/old_cleanup/instance/x
```

The command removes every metric of that group. A DELETE for a path without extra labels deletes only the group with exactly that key, and not all groups of the job. To remove several groups, delete each one. The Pushgateway also has an administrative API for wiping everything, which is disabled unless it is started with the admin API option.

Add the cleanup step to the process that retires a job. If it is left out, stale groups collect, and alerts that read the old values keep firing or stay silent for the wrong reason.

## Deleting One Metric

DELETE works on a whole group. To remove one metric of a group, push the group again with PUT and a body that leaves that metric out. With POST, the metric stays, because POST only replaces metrics that are in the body. This difference matters when you retire a single metric name from a job.

## No Aggregation

The gateway does not add values. If five jobs each push `batch_rows_total 100` to one group, the group contains one value, 100, not 500. A counter that should count across runs cannot be built in the gateway by pushing. If you need the total across runs, push the value of the run as a gauge and let a query add up the groups, or use a service that stays alive and holds the counter.

## Single Point Of Failure

All jobs depend on one gateway. When it is down, pushes fail, and Prometheus cannot scrape it. The job should treat a failed push as an error worth logging. Running several gateways does not help, because they do not share data, and a scrape of two gateways would show two different views.

A gateway that restarts loses its data unless persistence is enabled. Persistence writes the state to a file at intervals and loads it at startup. Enable it when losing the last values of all groups would cause false alerts. The state of the gateway after a restart is then at most one interval old.

## Scraping Behavior

Each scrape of the gateway returns all groups. With many groups, the response is large, and the load grows with the number of series, not with the number of jobs. Keep the number of groups small, and avoid labels that create a group for every item.

The staleness handling of Prometheus does not apply to the metrics inside the gateway. As long as the gateway returns a series, Prometheus treats it as present. When you delete a group, the series disappears from the next scrape, and Prometheus marks it stale.

## Using `push_time_seconds`

Alert on the age of the push, as well as on the job's own timestamp. A query such as `time() - push_time_seconds{job="nightly_backup"}` returns the seconds since the last push of that group. If it exceeds the schedule plus a margin, the job did not report.

Compare the two timestamps. If the push is recent and the job's last success is old, the job runs but fails. If both are old, the job does not run or cannot reach the gateway. This distinction tells operators where to look.

## Security

The Pushgateway has no built-in authentication in its basic form. Anyone who can reach it can push, replace or delete any group. Limit network access to the jobs that need it, and put it behind a proxy or use the supported TLS and authentication options if it must be reachable from outside a trusted network.

A wrong or malicious push can overwrite the status of an important job. Treat write access to the gateway as write access to the monitoring data of every job.

## Labels On Pushed Data

Prometheus attaches no extra `instance` label to pushed data when `honor_labels: true` is set, and the data has no `instance` label of its own. Add the `instance` label in the push path if your queries expect it. Use meaningful values, such as the name of the database that is backed up, and not the address of the machine that ran the job.

## A Complete Lifecycle

A well-run batch job reports like this. At the end of a successful run, it sends PUT with its duration, its work done and its success timestamp. At the end of a failed run, it sends POST with a failure timestamp, which leaves the last success untouched. The alert rules compare the ages of the two timestamps with the schedule. When the job is retired, an operator sends DELETE for each of its groups.

Each of these steps is small, and skipping any of them leaves a stale or misleading value in the gateway.

## Failure Handling In The Job

A push is a network call, so it can fail or time out. Give the push a short timeout so that a gateway outage does not make the job hang. Decide whether the failure of the push changes the exit code of the job. A common choice is to log the failure and keep the exit code of the real work, because the work itself succeeded.

Because a missed push shows up as an old timestamp, the alert on the age of `push_time_seconds` covers this case without extra code in the job.

## Naming The Job And The Group

Use one `job` value for one kind of work, such as `nightly_backup`. Do not reuse the name of a scraped service as a job name in the gateway. When the gateway job name equals the name of a scrape job, queries that select by `job` mix the two sources, and alerts on one can fire for the other.

## What You Know Now

You know that the Pushgateway keeps data until it is deleted, that it does not aggregate, that it depends on a single process and that it has no access control by itself. You can remove a group, remove one metric from a group and alert on the age of a push.

## Common pitfalls

> [!WARNING]
> Stale groups of retired jobs keep reporting old values, so delete them when the job is retired. DELETE removes a whole group and cannot remove a single metric. Anyone who can reach the gateway can overwrite any group, so restrict network access.
