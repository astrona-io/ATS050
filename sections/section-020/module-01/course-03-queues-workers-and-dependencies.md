---
draft: true
exam_objectives:
- Instrumentation
---
# Queues, Workers And Dependencies

A request is only one part of a system. Behind it sit resources such as queues, thread pools and connections, background workers that process items, and other services that the program calls. These parts fail in ways that request metrics do not show. This chapter explains how to instrument them with the USE method and with timestamps.

## The USE Method

USE stands for utilization, saturation and errors. It applies to a resource: something that has a limited capacity and that work consumes.

Utilization is the share of the capacity that is in use, for example the number of busy workers divided by the number of workers. Saturation is work that waits because the resource is full, for example items in a queue. Errors are failures of the resource itself, for example a connection that could not be opened.

A resource at full utilization is not yet a problem if nothing waits. Saturation is the signal that users feel, because waiting adds time to every request. Errors add failures. Measure all three, because each one points to a different fix.

## Queues

A queue holds items that wait for a worker. Three metrics describe it. A gauge shows the current depth, for example `shop_queue_depth`. A counter of added items and a counter of finished items show the flow in and out. A histogram of the waiting time shows how long an item stayed in the queue before work started.

The depth alone can mislead. A depth of 100 is harmless if workers drain 1,000 items per second and serious if they drain one. The rates of the two counters give the drain speed, and the waiting time shows the effect on the user directly.

Record the waiting time at the moment work starts: subtract the enqueue timestamp, which the item carries, from the current time.

## Workers

A worker pool has a fixed or limited number of workers. A gauge for busy workers and a gauge for the configured size give the utilization. A counter of processed items with an `outcome` label gives throughput and failure rate. A histogram of processing time gives the duration.

Keep the queue metrics and the worker metrics separate. A slow item shows up in the processing time. A full pool shows up in the waiting time and the depth. Mixed into one duration, the two causes cannot be told apart.

## In-Progress Gauges

Increment a gauge when work starts and decrement it when work ends. Place the decrement where every path passes, such as a `finally` block. Most client libraries offer a helper that does this for you, for example a context manager or a decorator that tracks in-progress work.

A value that stays above zero when no work is expected points to a path that never decrements, or to work that is truly stuck.

## Last-Success Timestamps

Some work runs on a schedule and produces no continuous stream of events. A backup runs once per hour. A counter that grows once per hour is hard to alert on, because a flat line looks the same as a normal gap between runs.

Record the Unix time of the last success in a gauge, for example `shop_last_success_timestamp_seconds`. The expression `time() - shop_last_success_timestamp_seconds` returns the age of the last success in seconds. An alert on an age larger than the schedule plus a margin detects a job that has stopped, whatever the reason.

Set the gauge only on success. Write a second gauge for the last failure if you also want to know when the problem started.

The probe in the lab environment exposes `lab_last_success_timestamp_seconds` for exactly this purpose.

## Dependencies

A dependency is another system that your program calls: a database, a cache, a remote API. Calls to it fail and slow down independently of your own code. Instrument each call site with the same three signals as a request, from the point of view of the caller.

Use a counter of calls with an `outcome` label, and a histogram of call duration. Name the dependency in the metric name or in a bounded `dependency` label, for example `shop_database_queries_total`.

With these metrics, a rise in request duration can be traced. If the duration of database calls rises at the same time, the cause is the database. If it stays flat, the cause lies in your own code or in another dependency.

## Timeouts And Cancelled Calls

A call that hits a timeout is an error from the caller's point of view, although no response arrived. Record it with its own `outcome` value, such as `timeout`. A timeout means the caller waited for the full limit, so the duration histogram shows a cluster of values at the timeout limit.

A call that is cancelled because the caller gave up should also be recorded. If it is not recorded, the dependency looks healthier than it is.

## Connection Pools

A pool of connections is a resource, so USE applies. Expose the pool size, the number of connections in use and the number of callers that wait for a connection. A pool that is always full with callers waiting is saturated, and adding more requests only adds more waiting.

Some database drivers expose these values through a standard collector. Check for one before writing your own.

## Worked Example: A Stuck Worker

A service shows normal request metrics, but customers complain that exports never arrive. The queue depth is rising, the finished-items counter is flat, and the busy-worker gauge equals the pool size. The processing time histogram has no new observations.

The reading is clear: every worker is occupied by an item that does not finish, so no item completes and the queue grows. The request metrics looked normal because the request only enqueues the work. Without the queue and worker metrics, the failure would have been invisible until users reported it.

## Choosing The Queue Metrics For Your Case

Not every queue needs every metric. An in-memory queue inside one process can expose depth and waiting time. A queue in a broker such as a message system is often measured by the broker, and your program adds only the processing metrics on the consumer side. Check what the broker already exports before duplicating it.

When items can be dropped because the queue is full, add a counter of dropped items. A dropped item is a loss, and it must not disappear silently. An alert on the drop rate catches overload even when the depth looks capped.

## Retries Inside Workers

A worker that retries a failed item executes it more than once. Count attempts and final outcomes separately. The attempts counter shows the real load on the dependency, and the outcome counter shows how many items ended in success or in permanent failure.

Give the retry count a bounded label or a separate histogram. Do not use the item identifier as a label, because the number of series would grow without limit.

## Graceful Shutdown

When a process stops, workers may hold items that are in progress. The in-progress gauge disappears with the process, and a new process starts at zero. This is normal for a gauge. For work that must not be lost, the queue system, not the metric, has to keep the item until it is acknowledged.

## What You Know Now

You can describe a resource with utilization, saturation and errors, instrument a queue with depth, flow and waiting time, and instrument workers with busy counts and processing time. You can use a last-success timestamp to detect work that stopped, and you can instrument calls to a dependency so that its failures and delays are visible separately from your own.

## Common pitfalls

> [!WARNING]
> A queue depth without the drain rate cannot tell a healthy backlog from a stuck one. A counter that grows once per hour makes a poor alert, so use a last-success timestamp instead. Timeouts and cancelled calls must be recorded as outcomes, or the dependency looks healthier than it is.
