---
draft: true
exam_objectives:
- Client Libraries
---
# Summary

A client library lets an application keep metrics in memory and expose them as text over HTTP. It supplies the metric types, thread-safe updates, a registry and an exposition handler. The application decides what each metric means and where in the code it changes. A name that promises more than the code counts gives wrong answers, and the library cannot detect that.

The registry holds the metric families of a process. Each family has one name, one type and one set of label keys, and registration enforces that contract. Create each metric once at start-up, and serve the same registry that the code updates. Every label combination is a child that stays in memory, so label values must come from a small, known set. A missing series and a series with the value zero mean different things, so create the known children early.

Metric values live in process memory. A counter returns to zero after a restart, and `rate()` and `increase()` handle that reset. A short-lived process can exit before it is scraped. A server with several worker processes needs a supported way to combine their values. Collection runs inside the scrape request, so it must stay cheap, and the endpoint must not expose secrets.

Key facts:

- Counters only grow while the process runs, and gauges can rise and fall.
- Always apply `rate()` or `increase()` to a counter.
- The exposition handler must serve the registry that holds the metrics.
- Label children are not removed automatically.
- A valid endpoint does not prove that the instrumentation is correct.

<!-- astrona:playground:destroy -->
