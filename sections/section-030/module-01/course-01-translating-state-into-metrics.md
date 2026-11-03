---
draft: true
exam_objectives:
- Exporters
---
# Translating State Into Metrics

Many systems do not expose Prometheus metrics. A database has a status command, a hardware device has a management interface and an old application writes statistics to a file. An exporter bridges the gap. It is a small program that queries the system in the way the system supports, converts the answer to the Prometheus text format and serves it over HTTP for Prometheus to scrape.

## Exporter Or Direct Instrumentation

If you control the source code of an application, add a client library to it. The application then exposes metrics that describe its own behavior, and no extra process exists. Use an exporter when you cannot change the code, or when the metrics come from a different place than the process: the operating system, a hardware sensor, a cloud service or a database server.

Some metrics need both. The exporter of a database shows the state of the database server. The application that uses the database shows how many queries it sent and how long they took. These are two views of the same system, and neither replaces the other.

## The Translation Contract

An exporter has one job: on each scrape, produce a correct list of samples. The Prometheus documentation for writing exporters describes the rules. This chapter keeps to the central ones.

Collect when scraped. The exporter reads the system when the scrape request arrives, and not on a timer of its own. The value that Prometheus stores is then as fresh as the scrape time, and the exporter holds no state that can go stale.

Keep the meaning of the source. A value that the system reports as a count of events is a counter, and a value that reports a current level is a gauge. Do not turn a total into a rate inside the exporter, because Prometheus does that with `rate()`.

Use base units. Convert milliseconds to seconds and kilobytes to bytes. Put the unit in the name, for example `_seconds` or `_bytes`.

Use labels for dimensions of the same quantity. Table sizes of different tables belong to one metric with a `table` label, and not to one metric per table.

Use the name of the system as a prefix, for example `mysql_` for a MySQL exporter, so that names do not collide.

## A Worked Translation

A backup tool prints this line when asked for its status:

```text
last_backup=2024-05-01T02:00:07Z size_mb=700 state=ok
```

The exporter parses the line and returns samples of this shape. The values are an example of the format.

```text
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds 1714528807
# TYPE backup_size_bytes gauge
backup_size_bytes 734003200
```

The time became a Unix timestamp in seconds. The size became bytes. The field `state=ok` could become a gauge with value 1, but a better design keeps only the timestamp of the last success, because it supports an alert on age.

## What To Do With Text Values

Prometheus stores numbers. A status that is a word, such as `ok` or `degraded`, cannot be a sample value. The usual approach is one series for each possible state with the value 1 for the current state and 0 for the others, with the state in a label. Another approach is a metric with the constant value 1 and the text in a label, which is used for build or version information.

Keep the number of possible text values small, because each value is a series.

## The Exporter Own Health Metric

Most exporters expose a gauge that says whether the last collection from the system worked, for example `mysql_up` for a MySQL exporter. The value is 1 when the exporter could read the system and 0 when it could not. This is different from the `up` metric that Prometheus adds for every scrape.

The distinction matters. When the backend is down, the exporter itself can still answer the scrape. `up` is 1 because the exporter responded, and the exporter-specific gauge is 0 because the backend did not.

## Partial Failures

A collection can fail in part. The exporter may read most statistics and fail on one. There are two ways to respond. One is to return an error status for the whole scrape, which makes `up` 0 and loses all metrics of that scrape. The other is to return the metrics that worked and mark the failed part.

The second is usually better. Prometheus keeps the good data, and a metric such as `exporter_collector_success{collector="name"}` shows which part failed. Return an HTTP error only when nothing useful can be returned.

## Cost Of Collection

Every scrape triggers a collection. A scrape every 15 seconds across several Prometheus servers can send many requests to the backend. If a collection is expensive, for example a query that scans a large table, the exporter should cache the result for a defined time and say so in its documentation.

An exporter that takes longer than the scrape timeout produces a failed scrape. Keep collection times well below the timeout, and measure the collection time in a metric of its own.

## Where To Run An Exporter

Run the exporter close to the system that it reads: on the same machine, or in the same network. The scrape across the network is then the only long link, and the exporter can use local, low-privilege access.

An exporter that serves the metrics of one machine, such as the Node Exporter for operating system metrics, runs on every machine. An exporter for a database usually runs next to the database or on a nearby host.

## Common Exporters

The Node Exporter exposes metrics about Linux machines: CPU, memory, disks and network. The Blackbox Exporter probes endpoints from the outside over HTTP, TCP, DNS and ICMP, and reports whether the probe succeeded and how long it took. Many database, message queue and cloud exporters exist.

When no exporter exists, writing one is practical. A client library supports custom collectors that read the system when scraped.

## What You Know Now

You know when to use an exporter, and that it must collect at scrape time, keep the meaning and units of the source and use a bounded set of labels. You know that its own health gauge differs from `up`, that partial failures should return the working part and that collection cost must stay below the scrape timeout.

## Common pitfalls

> [!WARNING]
> Do not convert a total to a rate inside the exporter. Do not use milliseconds or kilobytes. A single failing statistic should not fail the whole scrape. A collection that takes longer than the scrape timeout turns every scrape into a failure.
