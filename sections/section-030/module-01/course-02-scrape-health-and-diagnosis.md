---
draft: true
exam_objectives:
- Exporters
---
# Scrape Health, Backend Health And Diagnosis

When a dashboard shows no data, the cause can lie in several places: the backend, the exporter, the network, the Prometheus configuration or the query. This chapter explains what the automatic scrape metrics say, what they do not say and a fixed order for finding the failing stage.

## The `up` Metric

Prometheus creates the series `up` for every target at every scrape. The value is 1 if the scrape succeeded and 0 if it failed. A scrape succeeds when Prometheus received an HTTP 200 response with a body that it could parse before the scrape timeout.

The metric describes the scrape and nothing else. It says that Prometheus reached the target and read valid text. It does not say that the numbers are right, that the application is healthy or that the backend of an exporter works.

## Other Automatic Metrics

Prometheus adds more series for every scrape:

- `scrape_duration_seconds` is the time that the scrape took.
- `scrape_samples_scraped` is the number of samples that the target returned.
- `scrape_samples_post_metric_relabeling` is the number of samples that remained after metric relabeling.
- `scrape_series_added` is the number of new series in this scrape.

A sudden fall in `scrape_samples_scraped` while `up` stays 1 shows that the target returns less data than before, for example because a collector failed. A scrape duration that approaches the timeout is a warning before scrapes begin to fail.

## Application Errors Are Not Scrape Failures

A service that answers every request with an error can still serve its `/metrics` endpoint. In that case `up` is 1, and the error counter shows the failures. The reverse holds as well: `up` can be 0 while the application works, if the metrics endpoint is blocked or slow.

Because of this, alert on both. An alert on `up == 0` finds missing observation. An alert on the error ratio finds failing work. Neither replaces the other.

## Exporter Health Versus Backend Health

An exporter that reads a backend can fail in two separate ways. If the exporter process is down or unreachable, the scrape fails and `up` is 0. If the exporter runs but the backend is down, the scrape succeeds and `up` is 1, while the exporter reports the backend failure in its own metric, such as `backend_up 0`.

Read both signals together:

- `up` is 0: Prometheus cannot reach the exporter. Check the network, the address and the exporter process.
- `up` is 1 and the backend gauge is 0: the exporter works, and the backend is unreachable or refuses the exporter.
- `up` is 1 and the backend gauge is 1: collection works. If a metric is still missing, check the name, labels and the query.

## The Targets Page And API

Prometheus lists every target with its state. The web interface shows this under the targets page, and the HTTP API serves it at `/api/v1/targets`. Each entry shows the labels, the scrape URL, the health (`up`, `down` or `unknown`), the time of the last scrape, the duration and the last error.

The `lastError` text is the most direct evidence. Typical values include a refused connection, a timeout and a status code other than 200. Read it before changing anything.

## A Fixed Diagnostic Order

Check the stages in the direction of the data flow, and stop at the first one that fails.

1. The backend. Can the exporter host reach it with the same address and credentials that the exporter uses?
2. The exporter process. Does it run, and does it log errors?
3. The exporter endpoint. Does a request to `/metrics` from a host that can reach it return the expected text?
4. The scrape. Is the target listed, is its health `up` and what does `lastError` say?
5. The stored series. Does a query for `up` and for the metric name return data, and with which labels?
6. The query. Does the expression use the right name, labels and range?

Skipping ahead causes wasted effort. A query that returns nothing says little until you know whether the series exist.

## Staleness

When a target disappears or a series is no longer returned, Prometheus marks the series stale at the next scrape. A stale series is not returned by instant queries, even though samples exist in the past. After a failed scrape, all series of that target become stale at once. This explains why dashboards show gaps and not the last known value.

## Timeouts

Each scrape job has a scrape timeout, which cannot be longer than the interval. An exporter that needs 20 seconds fails every scrape of a job with a 10-second timeout, and `up` is 0 with a `lastError` that mentions the context deadline. Raise the timeout and interval together, or make the exporter faster.

## What Prometheus Sends

Prometheus sends a header with the scrape timeout, `X-Prometheus-Scrape-Timeout-Seconds`. Exporters can read it to stop long work early. Many exporters ignore it, so the safe approach is to keep collection time well below the timeout.

## Worked Example: A Silent Database

A dashboard for a database exporter shows no query data. The targets API lists the exporter with health `up`. The exporter-specific gauge `backend_up` is 0. The reading: the exporter works, and the backend does not answer it. The next step is stage one: test the connection from the exporter host with the credentials that it uses. An expired password is a common cause, and it would also appear in the exporter log.

If the targets API had listed health `down`, the work would start at stage two or three.

## Alerting On Missing Targets

The expression `up == 0` fires only for targets that exist and fail. A target that was removed from the configuration has no `up` series at all, so the alert stays silent. To detect a disappeared target, use `absent(up{job="name"})`, which returns a value of 1 when no series matches the selector.

## What You Know Now

You know that `up` says only whether the scrape worked, that the other automatic metrics show scrape cost and size and that an exporter has its own gauge for the backend. You can diagnose a missing metric by checking the backend, the exporter, the endpoint, the scrape, the stored series and the query in that order.

## Common pitfalls

> [!WARNING]
> `up` equal to 1 does not mean that the application or backend works. A scrape that exceeds its timeout fails completely. Query for `up` before querying for the missing metric, because an empty result for the metric means little until you know the scrape works.
