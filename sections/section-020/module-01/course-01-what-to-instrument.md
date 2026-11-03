---
draft: true
exam_objectives:
- Instrumentation
---
# What To Instrument In Each Kind Of System

A program can expose thousands of numbers, and most of them answer no question. Good instrumentation starts from the people who run the service and the decisions they must make: is the service up, is it slow, is it failing, is it about to run out of capacity. This chapter explains how to choose the measurements by looking at what kind of system you run.

## Three Kinds Of Systems

Online-serving systems answer a request while a person or another program waits. Examples are web servers, databases and API gateways. The important questions are how many requests arrive, how many fail and how long they take.

Offline-processing systems take work from a queue and process it without anyone waiting. Examples are message consumers and pipelines. The important questions are how much work waits, how much is in progress and how fast the system catches up.

Batch jobs run on a schedule or on demand, do a piece of work and exit. Examples are nightly backups and report exports. The important questions are whether the last run succeeded, when it ran and how long it took.

A single service can be all three. A web application serves requests, consumes a queue in the background and runs a nightly cleanup. Instrument each part according to its kind.

## Online-Serving Metrics

For an online-serving system, record on the server side: the number of requests received or completed, the number of failed requests and the time that each request took. Also record the number of requests in progress, because a growing in-progress count shows a backlog before failures appear.

The same metrics apply to every kind of outgoing call: calls to a database, a cache or another service. These client-side metrics show whether a slow response is caused by your code or by a dependency.

## Offline-Processing Metrics

For each stage of a pipeline, record the amount of work that enters, the amount that is waiting, the amount in progress, the amount that finished and the amount that failed. Add the time of the last item processed, as a Unix timestamp in seconds, because a stuck stage stops updating while all counters keep their old values.

The queue length and the rate of processing together tell you the time to drain the queue. A queue that grows for ten minutes while the processing rate stays flat is a capacity problem that you can detect early.

## Batch Job Metrics

A batch job exits, so Prometheus often cannot scrape it. The job pushes a small set of results to a place that Prometheus can read. Whatever the transport, the useful values are the same: the Unix time when the job last succeeded, how long it ran, and how much work it handled.

A job that has not succeeded for longer than its schedule allows is the alert condition. The query for it needs the time of the last success, not a count of runs.

## Libraries And Frameworks

A library has no view of the service that uses it. Library authors add metrics for the resources the library manages, for example a connection pool, a cache or a thread pool. They record the number of items in use, the number waiting and the number of errors.

Keep library metrics free of service-specific names, and let the application decide labels such as the service name. Good library instrumentation is cheap when no one scrapes it, and it never changes behavior.

## Decide By Question, Then By Metric

A practical method is to write the questions first. For example: how many orders per second, what share fails, how long a checkout takes, how many orders wait for packing, and when the last export finished. Each question maps to one or two metrics, and the types follow from the question.

A metric that answers no question is a cost. It uses memory in the application and storage in Prometheus, and it adds noise for the next person who reads the endpoint. A metric that is missing when an incident starts is a different cost, and it is paid at the worst moment. Aim for few metrics with clear definitions.

## Add Metrics At The Boundaries

The most valuable places to instrument are boundaries: where requests enter the service, where work leaves for a dependency and where a queue takes or releases an item. Measurements at a boundary describe what the service delivers or consumes, and they stay correct when the code behind the boundary changes.

Instrumenting deep inside the logic is harder to keep accurate. Tie each metric to a clear event, and do it in one place, such as a middleware or a wrapper.

## Worked Example

A team runs an order service. Its online-serving part exposes `shop_http_requests_total` with the labels `route` and `status_class`, and `shop_http_request_duration_seconds` as a histogram. Its background consumer exposes `shop_orders_waiting`, a gauge of queued orders, and `shop_orders_processed_total`. The nightly export job reports `shop_export_last_success_timestamp_seconds` and `shop_export_duration_seconds`.

During an incident the on-call engineer asks three questions in order. Are requests failing? The request counter answers. Are orders piling up? The queue gauge answers. Did the export run last night? The timestamp answers. Each question has exactly one metric to read.

## Count Failures Separately

Failures deserve their own measurement, even when a status label already marks them. Two reasons apply. Errors are the signal that most alerts use, so the query for them must be simple and fast. And the definition of an error is a decision that you make once, in code, instead of a regular expression that every dashboard writes again.

Decide what counts as a failure for each operation. An HTTP 404 for a missing page is usually a correct answer, while a 500 is a failure. A timeout in a dependency is a failure of the call even if your service then returns a cached answer. Write these rules down in the metric help text.

## The Cost Of A Metric

Each metric has a cost in three places. The application keeps the value in memory and spends a little CPU on every update. The `/metrics` response grows, so each scrape moves more bytes. Prometheus stores one series for each label combination and keeps it for the retention period.

A single counter without labels costs almost nothing. A histogram with ten buckets and three label dimensions with ten values each creates ten thousand series. Estimate the number of series before you add a label, and review the estimate when the label set changes.

## Metrics, Logs And Traces

Metrics are numbers that Prometheus aggregates over time. They answer how much and how often, and they are cheap to store. They do not say which request failed or why. Logs record individual events, and traces follow one request across services. A good setup uses metrics to detect a problem and logs or traces to find its cause.

For that reason, keep identifiers such as request numbers out of metric labels. Put them in logs, where one line per event is the right shape.

## Instrument Early

Adding instrumentation after an incident means that the first occurrence has no data. Add the standard request, queue and dependency metrics when you write the service, and treat them as part of the feature. The cost is small, and the history that builds up from day one is the evidence that makes later debugging possible.

## What You Know Now

You can classify a system and name the metrics that matter for it. You know to start from questions and to instrument at boundaries.

## Common pitfalls

> [!WARNING]
> Counting only successful events under a name that suggests all events misleads every query. Instrumenting every function creates cost and noise. A stuck consumer keeps its old counters, so add a timestamp of the last processed item.
