# Instrumentation and Exporters (ATS050)

Prometheus Certified Associate (PCA): Instrumentation and Exporters, worth 16% of the official curriculum. This course belongs to ATP010.

Developed reading explains mechanisms, responsible components, examples and limits. Every section has an introduction and every module closes with a summary. Reusable YAML checks contain 5–15 questions per bank. Technical content remains draft. Private playgrounds and draft graded labs are included.

## Course Outline

| Section / module | Module |
| --- | --- |
| 010 / 01 | Client Libraries, Registries And Metric Lifecycle |
| 010 / 02 | Metric Types And The Text Exposition Format |
| 020 / 01 | Instrumenting Requests, Work Queues And Dependencies |
| 020 / 02 | Batch Jobs And The Pushgateway |
| 030 / 01 | Exporters, Target Failure And Multi-Target Probes |
| 030 / 02 | Node Exporter And The Textfile Collector |
| 040 / 01 | Metric Names, Units And Stable Label Design |
| 040 / 02 | Labels And Cardinality |

Each module has a landing page, three reading parts, a guided practice page and a summary. Each section ends with a capstone lab and a knowledge check, and the course ends with a final knowledge check.

## Author Review

See [curriculum coverage](CURRICULUM.md), [primary sources](SOURCES.md), [question-bank documentation](ASSESSMENTS.md) and [contribution instructions](CONTRIBUTING.md). No runtime execution is claimed.

## Hands-On Coverage

This course has 8 ungraded playgrounds and 12 independent graded labs: 8 module labs and 4 capstones. Every lab is UNTESTED: it was checked statically with `astrona validate`, `bash -n` and YAML parsing, but no lab or playground was ever run. Tasks, launch entries and solutions follow their teaching reading. Guided practice precedes the summary.

| Module | Labs in reading order |
| --- | --- |
| 010/01 | Inspect A Registry Exposed By A Process |
| 010/02 | Read The Types And Buckets Of A Live Endpoint |
| 010/capstone | Client Libraries Capstone |
| 020/01 | Instrument Completion And Duration Together |
| 020/02 | Report A Batch Job Through The Pushgateway |
| 020/capstone | Pushgateway Capstone |
| 030/01 | Distinguish Target Health From Application Errors |
| 030/02 | Publish Backup Metrics Through The Textfile Collector |
| 030/capstone | Exporters Capstone |
| 040/01 | Check Units And Bounded Labels |
| 040/02 | Remove An Unbounded Label And Fix Metric Names |
| 040/capstone | Metric Design And Cardinality Capstone |
