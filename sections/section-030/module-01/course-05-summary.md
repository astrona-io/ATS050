---
draft: true
exam_objectives:
- Exporters
---
# Summary

An exporter translates the state of a system that Prometheus cannot scrape into the text format. It collects when scraped, keeps the meaning and base units of the source, uses a small set of labels and prefixes names with the name of the system. Text values become labels, and partial failures return the working data together with a marker for the failed part.

The automatic `up` series says only that a scrape succeeded. It does not say that an application or a backend is healthy. An exporter exposes its own gauge for the state of the backend, so a dead backend leaves `up` at 1 while the gauge is 0. The scrape duration and sample count show the cost and size of each scrape.

A missing metric is diagnosed in order: the backend, the exporter process, the exporter endpoint, the scrape, the stored series and the query. The targets API shows health and the last error of each target. A removed target has no `up` series, so `absent()` is needed to detect it.

A multi-target exporter receives the real target as a parameter. Three relabeling rules copy the address into `__param_target` and `instance` and send the scrape to the exporter. A failed probe is a valid answer with `probe_success` of 0. Exporter credentials need least privilege and must stay out of addresses, labels and logs.

Key facts:

- `up` describes the scrape, not the system behind it.
- Alert on both a missing scrape and failing work.
- A scrape that exceeds its timeout fails completely.
- Cache expensive collections and keep them below the scrape timeout.
- Restrict access to a multi-target exporter.

<!-- astrona:playground:destroy -->
