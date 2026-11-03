---
draft: true
exam_objectives:
- Exporters
---
# The Node Exporter And The Textfile Collector

The Node Exporter is a program that runs on a machine and exposes metrics about it at an HTTP endpoint, by default on port 9100 at the path `/metrics`. It reads the information from the operating system, for example from the `/proc` and `/sys` file systems on Linux. One instance serves one machine, so it runs on every machine that Prometheus monitors.

## Collectors

The exporter is built from collectors. Each collector reads one area and returns metrics for it. Examples are `cpu`, `meminfo`, `diskstats`, `filesystem` and `netdev`. A set of collectors is enabled by default, and others must be enabled by a flag. A collector can be turned off with a flag that has the form `--no-collector.<name>`, and a disabled-by-default collector is turned on with `--collector.<name>`.

Switching off collectors that you do not use reduces the number of series and the work per scrape.

## Metrics About The Collectors

The exporter reports on its own collection. The metric `node_scrape_collector_success` has a label `collector` and is 1 when that collector worked in the last scrape, and 0 when it failed. The metric `node_scrape_collector_duration_seconds` shows how long each collector took.

These are the first metrics to check when a machine metric is missing. A collector that failed shows 0 here, while `up` for the scrape stays at 1.

## Why A Textfile Collector

Not everything on a machine is in `/proc`. A backup script knows when it last succeeded. A hardware tool prints the state of a disk controller. A scheduled job counts the rows that it processed. These programs run for a short time, and they cannot serve an endpoint of their own.

The textfile collector reads the results from files. A script writes a file in the Prometheus text format to a directory, and the Node Exporter includes the samples of that file in its own output at every scrape. The values stay as long as the file exists, so a short-lived script can publish a result that outlives its process.

## Enabling The Collector

The collector reads a directory that you name with a flag:

```text
--collector.textfile.directory=/var/lib/node_exporter/textfile
```

Without this flag the collector reads nothing. The collector reads only files whose names end in `.prom`. Other files in the directory are ignored. The exporter reads the directory at each scrape, so a new file appears in the next scrape, and a removed file disappears.

## What The Collector Reports

For each file, the collector exposes the samples in it, and in addition it exposes:

- `node_textfile_mtime_seconds`, a gauge with the file path in the label `file` and the modification time of the file as a Unix time.
- `node_textfile_scrape_error`, a gauge that is 1 if the collector had an error opening the directory or reading or parsing a file, and 0 otherwise.

The modification time lets an alert detect a script that stopped updating its file. The error gauge lets an alert detect a malformed file.

## A Worked Example

A backup script writes the file `backup.prom` to the textfile directory after a successful run. The content, shown as an illustration of the format, is:

```text
# HELP backup_size_bytes Size of the last backup in bytes.
# TYPE backup_size_bytes gauge
backup_size_bytes{database="orders"} 734003200
# HELP backup_last_success_timestamp_seconds Unix time of the last successful backup.
# TYPE backup_last_success_timestamp_seconds gauge
backup_last_success_timestamp_seconds{database="orders"} 1714528807
```

At the next scrape of the Node Exporter, these samples appear in its output together with the machine metrics. Prometheus stores them with the labels of the scrape job, such as `job` and `instance`, plus the labels in the file.

The `instance` label is the machine. This is the main advantage over the Pushgateway: the batch metrics belong to the same machine as the rest of its metrics.

## What Does Not Work

The collector does not run scripts. It only reads files. A script that is not scheduled does not update anything.

The collector does not delete old files. If a script stops writing and its file stays, the old values stay as well, and look current. The modification time metric is the defense.

The collector cannot read a file that another process is still writing. A partial file may produce a parse error or wrong values. Files must therefore be written so that the collector never sees a partial file.

## Labels And Series

The labels that you put in a file become labels of the series, so the same cardinality rules apply as for any other metric. Keep the label values bounded, and do not use identifiers that grow with every run.

## Default Port And Access

The Node Exporter listens on all interfaces on port 9100 unless told otherwise. The endpoint shows details of the machine, such as mount points and network interface names. Restrict who can reach it, and use the supported TLS and authentication options when it must be reachable across an untrusted network.

## Directory Ownership

The directory must be readable by the user of the exporter and writable by the scripts that produce files. Use a dedicated directory for it, and give the scripts write access to that directory only. A script with write access can publish any metric through the exporter, so treat the directory like part of the monitoring system.

## Many Writers

Several scripts can write their own files in the same directory, for example `backup.prom` and `inventory.prom`. Give each script its own file, so that one script never overwrites the output of another. The collector combines all files into one output.

## What You Know Now

You know that the Node Exporter runs on each machine and is built from collectors, and that its scrape metrics show whether a collector worked. You know what the textfile collector reads, when files are picked up and what the two extra metrics mean.

## Common pitfalls

> [!WARNING]
> The collector reads only files that end in `.prom`, and reads nothing unless the directory flag is set. An old file keeps reporting old values, so monitor its modification time. A collector can fail while `up` stays 1, so check `node_scrape_collector_success`.
