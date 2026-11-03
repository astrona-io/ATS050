---
draft: true
exam_objectives:
- Exporters
- Instrumentation
---
# Writing And Publishing Metric Files

The textfile collector accepts only valid text format, and it reads a file whenever a scrape arrives. Two things follow. The content must be correct, and the file must never be visible in a half-written state. This chapter covers the rules for the content and a safe way to publish a file.

## The Format Rules

A file is a list of lines. A line is a comment, a blank line or a sample.

A sample has a metric name, optional labels in braces and a value:

```text
metric_name{label_one="value",label_two="value"} 42
```

Metric names use letters, digits, underscores and colons, and cannot start with a digit. Label names use letters, digits and underscores. Label values are in double quotes, and a quote, a backslash or a line break inside a value must be escaped.

The value is a number in decimal or exponent notation, or one of the special values `NaN`, `+Inf` and `-Inf`. A word such as `twelve` is not a number, and a file that holds it fails to parse.

Comment lines that start with `# HELP` give a description of a metric, and lines that start with `# TYPE` give its type. Write both for every metric, with the type as one of `counter`, `gauge`, `histogram`, `summary` or `untyped`.

## One Declaration For Each Metric

Each metric name must have one type and one help text in the combined output of all files. If two files declare the same metric name with a different type or a different help text, the combined output is inconsistent, and the collector reports an error. Give each script its own metric name prefix, so that two scripts never define the same name.

Within one file, all samples of a metric name belong together, below one `# TYPE` line. Do not repeat a sample with the same name and the same label set, since the second one is a duplicate.

## Timestamps

A sample may carry a timestamp after the value, but do not use this feature in textfile files. A sample with an explicit timestamp does not follow the scrape time, which confuses staleness handling. Use the file modification time, which the collector exposes, to judge freshness.

## Gauges And Counters

A script that runs once and exits cannot keep a counter between runs, because the process memory is gone. The file persists, but the script would have to read its old value and increase it. For most batch results, write gauges: the size of the last run, its duration and the time of the last success. If a script must keep a running total, it needs to read the previous value from storage and write the new total, and it must handle a missing or damaged file.

## Writing A File Atomically

The collector may read the file at any moment. If a script writes the final file directly, a scrape can read a half-written file. It then sees a truncated line, a missing newline or a missing metric.

The safe method has two steps. First, write the complete content to a temporary file in the same directory, using a name that does not end in `.prom`, for example `backup.prom.tmp`. Second, rename it to the final name. A rename within one file system is atomic: a reader sees either the old file or the new file, never a mixture.

```sh
cat > /var/lib/node_exporter/textfile/backup.prom.$$ <<'METRICS'
# HELP backup_size_bytes Size of the last backup in bytes.
# TYPE backup_size_bytes gauge
backup_size_bytes{database="orders"} 734003200
METRICS
mv /var/lib/node_exporter/textfile/backup.prom.$$ /var/lib/node_exporter/textfile/backup.prom
```

The temporary name must be in the same directory, because a rename between file systems copies the content and loses the atomic property. The suffix keeps the temporary file from being read as a metric file, because the name does not end in `.prom`.

## When A Run Fails

Decide what the file says after a failed run. A common choice is to leave the old file untouched, so the age of `backup_last_success_timestamp_seconds` grows. A script can also write a gauge such as `backup_last_run_success` with the value 0 or 1. Do not delete the file on failure, because a missing file means missing metrics and not a visible failure.

## Detecting Problems

Three checks cover the usual failures.

A malformed file sets `node_textfile_scrape_error` to 1. Alert on `node_textfile_scrape_error == 1`.

A stale file is one whose script stopped. Alert on `time() - node_textfile_mtime_seconds > 3600`, with a limit above the schedule of the script. The label `file` identifies the file.

A missing file gives no series. Use `absent(backup_last_success_timestamp_seconds)` to alert on the absence of a metric that must exist.

## Testing A File

Before you rely on a file, check it. Read the combined output of the exporter at its `/metrics` endpoint, and find your metric and its type. Check that `node_textfile_scrape_error` is 0 and that `node_textfile_mtime_seconds` lists your file. Then check that Prometheus has the series with the expected labels.

## Label Choices In Files

Use a label when one script reports the same quantity for several things, for example `database="orders"` and `database="users"` for the size of each backup. Write all of them below one `# TYPE` line.

Do not add the name of the machine as a label. Prometheus attaches the `instance` label of the scrape, and a second label with the machine name only adds a duplicate dimension that can disagree with it.

## Escaping Example

A label value that contains a quote must escape it with a backslash, and a value with a line break must use `\n`. For example, the label value `say "hi"` is written as `"say \"hi\""`. A raw quote ends the value early and breaks the line.

## What You Know Now

You know the rules for lines, names, labels and values, and you can write a file that the collector accepts. You can publish it with a temporary file and a rename, so that a scrape never reads a partial file. You know which three alert conditions cover a malformed, a stale and a missing file.

## Common pitfalls

> [!WARNING]
> Writing the final file directly lets a scrape read a partial file. A temporary file in another directory or file system loses the atomic rename. Two files that declare the same metric with different types make the output inconsistent. A value that is not a number makes the whole file fail to parse.
