---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Summary

A metric name describes one quantity. It starts with the name of the application or subsystem, uses a base unit such as seconds or bytes as the last word before the type suffix, and ends in `_total` for counters and `_info` for info metrics. A name must match what the code counts.

Labels describe dimensions of the same quantity. A label is correct when its values come from a bounded, listable set and when the sum over the label is meaningful. Different units or different quantities need separate metrics. Label names keep one meaning in every metric, and `job` and `instance` are reserved for the scrape target. Descriptive facts such as a version go into an info metric with the value 1.

A rename, a label change or a unit change ends the old series and starts a new one, and no consumer receives an error. A change runs in steps: expose the new metric beside the old one, find and migrate every consumer, then remove the old one. Recording rules are named by their labels, source metric and operation.

Key facts:

- Use base units and never mix units under one name.
- Never put identifiers of users, requests or sessions in labels.
- Initialize series for known label values at start-up.
- A series produced by `rate()` is not a counter.
- Review the real endpoint output, not only the code.

<!-- astrona:playground:destroy -->
