---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Summary

Each unique combination of a metric name and label values is one time series. The number of series multiplies across labels, across instances and, for a classic histogram, by the number of buckets plus two. Labels with unbounded values, such as identifiers of users or requests and raw paths, create new series without end. The cost stays in memory until the head block is compacted and on disk until retention ends.

High cardinality is found with the gauge `prometheus_tsdb_head_series`, the creation rate of series, the automatic scrape metrics `scrape_samples_scraped` and `scrape_series_added`, and the TSDB status API, which lists the metric names and label names with the most series. Counting the distinct values of a label confirms the cause.

The lasting fix is in the application: record bounded values such as route templates, and move identifiers to logs. At scrape time, `metric_relabel_configs` can drop metrics and labels, but dropping a label that was a real dimension makes series collide. The limits `sample_limit`, `label_limit` and `target_limit` fail the whole scrape and set `up` to 0, so they need a margin above the normal size. Recording rules make queries cheap but do not reduce what is stored.

Key facts:

- Calculate the series count before shipping new labels.
- A histogram multiplies series by its bucket count plus two.
- A scrape that exceeds a limit stores nothing.
- Check `up` after setting any limit.
- A fix at the source is the only change that removes the cost.

<!-- astrona:playground:destroy -->
