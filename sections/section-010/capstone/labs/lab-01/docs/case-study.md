---
draft: true
exam_objectives:
- Client Libraries
---
# Starting Environment

One instrumented probe serves metrics in the Prometheus text format. A traffic generator sends one request every 0.25 seconds, and every tenth request fails with status 500. A Prometheus server scrapes the probe every two seconds. The `shuttle` pod has Python and can reach the probe and Prometheus. No report exists yet.
