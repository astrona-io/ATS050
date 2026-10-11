---
draft: true
exam_objectives:
- Instrumentation
---
# Instrumenting Requests, Work Queues And Dependencies

Instrumentation should answer a question about service behavior, not merely produce many metrics. Define the measured quantity, event population, lifecycle boundary and useful dimensions before choosing a client API. A small set of well-defined observations often provides better evidence than a large collection of ambiguous counters.

## Measure Service Outcomes And Load

Request rate describes incoming or completed work according to the defined boundary. Error rate describes a subset of that work whose outcome meets an explicit failure definition. Duration distributions describe how long relevant operations take. Saturation measurements describe constrained resources or queued work that can explain pressure before user outcomes deteriorate.

These observations complement one another. High traffic can be healthy when errors and latency remain acceptable. Low traffic can coincide with a serious outage if clients cannot reach the service. A current queue depth does not reveal how many jobs were completed, and a request counter does not reveal the slow tail of their durations.

## Choose A Consistent Boundary

For an HTTP handler, decide whether duration begins at acceptance, after queueing or at another meaningful point. Include the relevant completion paths so errors and cancellations are not silently excluded. If only successful requests are timed, the duration metric cannot describe all user experiences. State whether streaming operations and background work fit the same contract.

The numerator of an error ratio must belong to the denominator's population. A dependency-error counter divided by frontend requests may be useful only if the relationship is explicitly intended. Multiple dependency calls and retries can make that ratio exceed one without indicating an arithmetic bug. Naming and documentation should make the population clear.

## Bound And Normalize Dimensions

Useful dimensions can include service, normalized route, method and outcome class. A raw URL containing customer IDs or query strings can generate unbounded values and expose confidential information. Normalize routes to templates where appropriate and use logs or traces for individual-request context.

Status dimensions should follow the operational question. A finite response-code label may be useful, while arbitrary error-message text is usually too variable. Ensure that every label combination is semantically meaningful rather than mixing different units or unrelated operations under one metric family.

## Account For Asynchronous Work

A queue-based service has producer acceptance, queued waiting and consumer completion boundaries. A successful enqueue does not establish successful processing. Measure the relevant stages separately, including queue depth, age, processing outcomes and duration where useful. A last-success timestamp can support freshness checks for periodic work without pretending that queue admission equals business completion.

Nested instrumentation can double-count when an aggregate combines both outer requests and internal attempts as though they were the same events. Retries are especially important: they may improve final success while increasing dependency load. Distinguish logical operations from attempts so dashboards and alerts use the intended denominator.

## Keep The Observer Lightweight

Instrumentation executes on application paths and can add overhead or contention. Use supported library operations, avoid expensive label construction and limit synchronous collection dependencies. Validate success, failure, restart and cancellation behavior rather than only a happy-path example. The objective is dependable evidence with a clear meaning, not an impressive metric count.

## Common pitfalls

> [!WARNING]
> Define populations and boundaries before ratios. Raw URLs and error messages can create unbounded labels, while retries and nested calls can make apparently similar counters describe different work.
