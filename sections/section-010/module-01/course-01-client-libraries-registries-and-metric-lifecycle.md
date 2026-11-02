---
draft: true
exam_objectives:
- Client Libraries
---
# Client Libraries, Registries And Metric Lifecycle

A Prometheus client library gives application code a supported way to maintain metrics and expose them for collection. It normally provides counters, gauges, distributions, registries and an exposition handler. The library handles important format and concurrency details, but it cannot decide what a business operation means or where its successful completion occurs.

## Define The Measurement Before The API Call

A completed-request counter should be incremented at the point where the application considers the request complete. Incrementing only successful requests and naming the metric as all requests would misstate its population. A separate status dimension can distinguish outcomes when the values are bounded and consistently defined.

A gauge can track current in-progress work or queue depth. A histogram can observe request duration using a documented unit. Choose the metric API according to the quantity's semantics rather than the visual shape desired in a dashboard. The raw counter value is cumulative; query functions later derive its activity rate.

## Registration Creates A Family Contract

A registry organizes collectors and metric families for exposition. Metric names, help text, types and label keys must be compatible. Registering conflicting definitions of the same family can fail or create invalid collection behavior. Construct metrics through the application's intended lifecycle rather than registering a new family for every request.

Libraries can support separate registries for tests or components. That makes ownership explicit and avoids accidental global collisions. However, the exposition endpoint must use the registry containing the intended metrics. Updating one registry while exposing another produces a healthy-looking endpoint with missing instrumentation.

## Labels Create Stateful Children

A labeled metric can maintain separate children for each label combination. Calling the metric with an unbounded user or request identifier can therefore create continuously growing producer state as well as collector cardinality. The fact that the application finishes a request does not universally remove that metric child.

Use bounded dimensions such as normalized route and outcome class where they serve a defined question. Initialize known series when a meaningful zero should be available, while distinguishing that from a producer or collector failure. A missing child and a zero-valued child can produce different query results.

## Process Lifecycle Affects Values

Counters typically reset when their owning process restarts. The query must account for visible resets rather than require the application to persist every operational counter. A short-lived process may exit before its final values are scraped, so its collection model needs deliberate consideration. A library's counter alone does not guarantee complete transaction accounting.

Multi-process applications require a supported model for combining worker metrics. Exposing only one worker's registry can omit the others, while blindly combining incompatible gauges can misrepresent current state. Review the particular library's multi-process support and the intended aggregation semantics rather than assume all libraries share one implementation.

## Keep Collection Safe And Bounded

The metrics handler can run while application threads update state. Use the library's supported concurrent operations and avoid expensive blocking work in custom collectors. A scrape that triggers slow dependency calls can increase latency or cause the endpoint to time out. Exposition should provide a bounded observation path with understandable failure behavior.

Instrumentation must also avoid sensitive label values and heavy per-request processing. Validate the emitted family structure and the application's update points. A parseable endpoint establishes format compatibility, while correct measurement requires evidence that the code updates the intended quantity under normal, error and restart behavior.

## Common pitfalls

> [!WARNING]
> Registration, update and exposition must use the intended registry. Client libraries do not define business semantics, expire every label child automatically or provide universal multi-process aggregation.
