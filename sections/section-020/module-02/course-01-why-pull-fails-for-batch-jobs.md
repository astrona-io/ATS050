---
draft: true
exam_objectives:
- Instrumentation
---
# Why Pull Fails For Batch Jobs

Prometheus works by pulling. At a fixed interval it sends an HTTP request to each target and stores the answer. This design has a useful property: Prometheus itself decides when and how often to look, and a target that does not answer is visible at once through the `up` metric. The design assumes that the target lives longer than the scrape interval.

A batch job breaks that assumption. It starts, does its work and exits. This chapter explains what goes wrong and what the options are.

## The Timing Problem

Suppose Prometheus scrapes every 15 seconds and a backup job runs for 4 seconds once per night. The probability that a scrape lands inside the 4-second window is about one in four, and even then the process may exit before the response is complete. The job can run correctly for months without Prometheus ever seeing a single sample.

Shortening the scrape interval does not solve this. A 1-second interval would raise the load on every target and every series, and the job could still finish in less than a second.

## Where The Job Runs

A second problem is discovery. Prometheus has to know where to scrape. A job that runs in a container scheduler or on a temporary machine has an address that exists only while it runs. Service discovery lists live targets, so a short-lived job appears and disappears before the next discovery refresh.

## What A Batch Job Needs To Report

A batch job has few things to tell. Did the last run succeed? When did it finish? How long did it take? How much work did it do? These values describe a run, and they remain true after the process exits. The question after the run is whether the last run was fine, and the answer needs a value that survives the process.

## Option One: Push To A Gateway

The Pushgateway is a service that lives long. The job sends its metrics to it with an HTTP request at the end of the run, and then exits. Prometheus scrapes the Pushgateway like any other target. The metrics seen by Prometheus are those of the last push of each group, and they stay until someone replaces or deletes them.

The Pushgateway is a metric cache. It does not aggregate, and it does not compute anything.

## Option Two: The Textfile Collector

If the job runs on a machine that already runs the Node Exporter, the job can write a file in the Prometheus text format to a directory that the Node Exporter reads. The Node Exporter then exposes the values for as long as the file exists. This has an advantage: the metrics have the same `instance` label as the other metrics of the machine, and they disappear when the machine is removed.

Choose this option for jobs tied to one machine. Choose the Pushgateway for jobs that are not tied to a machine, such as a job in a cluster that can run on any node.

## Option Three: Keep The Process Alive

Some jobs can be restructured as a long-running service with an internal schedule. That service exposes metrics at its own endpoint like any other. This is the cleanest design when the job allows it, because the normal rules apply: `up` shows whether the service runs, and counters keep their history.

## When The Pushgateway Is The Right Choice

The Pushgateway is meant for service-level batch jobs: jobs that are not bound to one machine and that produce a result for the service as a whole. The result of a nightly backup of a database is a good example.

It is not a way to turn Prometheus into a push system. Using it for metrics of long-running services removes the benefits of pull: `up` no longer reports whether the service is alive, and the gateway keeps the last value of every instance forever, even for instances that no longer exist.

## What To Push

For a batch job, push these values:

- The time of the last success, as a Unix timestamp in a gauge, for example `batch_last_success_timestamp_seconds`.
- The duration of the last run, in seconds, in a gauge such as `batch_duration_seconds`.
- A measure of the work done, for example the number of processed rows, in a gauge.

Prefer gauges, because a push replaces the value. A counter pushed from a job that restarts from zero on every run would show a value that jumps back to a small number, and `rate()` and `increase()` would read each run as a counter reset.

## A Fixed Convention For Failures

Decide what a failed run reports. One design pushes the success timestamp only on success. When the run fails, nothing is updated, and the age of the timestamp grows. A second design pushes a separate `batch_last_failure_timestamp_seconds` on failure. This shows when the failure happened, and a query can compare the two timestamps. Both designs work, and the important point is to choose one and apply it to every job.

## Alerting On Batch Jobs

An alert on a batch job compares the age of the last success with the schedule. For a job that runs every hour, the expression `time() - batch_last_success_timestamp_seconds{job="nightly_backup"} > 7200` fires when two runs were missed. Setting the limit slightly above the schedule avoids alerts for a run that is a little late.

Because the Pushgateway keeps the last value, this alert also fires correctly when the job was never started again: the value stays and its age grows.

## Jobs That Run Often

A job that runs every few seconds, for example a short task started by a queue, is a different case. Pushing at the end of each run creates a stream of updates that overwrite each other. The gateway keeps only the last one. For such work, count events in a service that stays alive, such as the queue consumer itself, and avoid pushing from every run.

Pushing at the end of a run is right when the number of runs is small and each run is a meaningful event.

## Where The Push Call Goes

Place the push at the end of the job, in code that runs on both success and failure. If the push call is inside the success branch only, a failed run reports nothing, and the alert on the age of the success timestamp is the only signal. If the push fails because the gateway is down, the job should log that failure and not hide it, because a missing push is itself a monitoring failure.

Most client libraries provide a function for pushing a whole registry. The job builds a registry, sets the gauges, calls the push function once and exits.

## The Registry Of A Batch Job

A batch job should use its own registry that contains only the batch metrics. The default registry of a client library includes process metrics and runtime metrics. Pushing those to a gateway gives values that describe a process that no longer exists, and that adds noise.

## What You Know Now

You know why a scrape can miss a short-lived job and why more frequent scrapes do not fix it. You can name the three ways of reporting a job result and choose between them. You know which metrics a batch job should report and why gauges fit them.

## Common pitfalls

> [!WARNING]
> Do not use the Pushgateway for metrics of long-running services, because it hides their failures. A counter pushed from a job that restarts from zero looks like a counter reset on every run, so use gauges for results of runs. A shorter scrape interval does not fix a missed job.
