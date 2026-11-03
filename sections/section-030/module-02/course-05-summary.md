---
draft: true
exam_objectives:
- Exporters
- Instrumentation
---
# Summary

The Node Exporter exposes machine metrics from the operating system. It is built from collectors, and `node_scrape_collector_success` shows which ones worked in the last scrape. A collector can fail while `up` stays at 1.

The textfile collector reads files that end in `.prom` from the directory named by `--collector.textfile.directory`, and reads nothing without that flag. Scripts and batch jobs write metrics in the text format, and the exporter includes them in its output. The series carry the `instance` label of the machine. The collector exposes `node_textfile_mtime_seconds` for the age of each file and `node_textfile_scrape_error`, which is 1 if a file could not be read or parsed.

A file must contain valid lines, numeric values and one consistent declaration for each metric name. Publish it by writing a complete temporary file in the same directory and renaming it, so that a scrape never reads a partial file. Do not use explicit timestamps. Prefer gauges for the results of runs.

Alert on a malformed file with the error gauge, on a stale file with the age from the modification time and on a missing metric with `absent()`. Choose the textfile collector for jobs that belong to a machine and the Pushgateway for jobs that do not. Restrict who can write into the directory, because it feeds the exporter endpoint.

Key facts:

- Only files that end in `.prom` are read.
- A removed file removes its series at the next scrape, and an old file keeps them.
- A rename within one directory is atomic.
- A mounted ConfigMap updates with a delay.
- Do not use `honor_labels: true` for the Node Exporter job.

<!-- astrona:playground:destroy -->
