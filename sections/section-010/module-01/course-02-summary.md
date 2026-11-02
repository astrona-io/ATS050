---
draft: true
exam_objectives:
- Client Libraries
---
# Summary

Client libraries provide metric types, label handling, registration and exposition. The application still defines what is measured and updates the appropriate metric at the correct lifecycle point.

Registries must avoid conflicting families and unbounded label children. Concurrency, process restart and multi-process deployments need explicit library support; successful endpoint exposure does not establish that the instrumentation measures useful business outcomes.
