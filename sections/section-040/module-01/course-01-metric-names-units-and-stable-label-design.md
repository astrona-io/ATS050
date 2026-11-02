---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Metric Names, Units And Stable Label Design

Metric naming is part of the measurement contract. A reader should be able to identify the quantity, unit and intended dimensions before choosing an aggregation or alert. Clear naming also reduces the chance that different services expose similarly named metrics with incompatible meanings.

## Name A Coherent Quantity

A metric family should describe one quantity whose observations can be interpreted consistently. A request-duration metric measured in seconds should not also contain memory usage under a type label. The numerical values need a shared unit and semantic meaning. Labels can distinguish routes or outcomes within that quantity rather than switch it into an unrelated measurement.

Names commonly use a subsystem prefix and a base-unit suffix. Duration in seconds and size in bytes make conversions explicit. Counter names conventionally end in total to indicate accumulation. A timestamp-valued gauge can use a timestamp_seconds suffix to distinguish event time from elapsed duration. Naming conventions help, but the documented producer behavior remains authoritative.

## Labels Are Useful Dimensions

A bounded method or status class can support request analysis. A normalized route can identify a handler without creating a series for every customer-specific URL. Label keys should have stable meaning across producers and consumers. If environment means a deployment environment in one service and a process variable name in another, broad queries can combine incompatible populations.

Avoid putting every possible detail into labels. A user ID, request ID or arbitrary exception text can create unbounded combinations. Their cost includes client state, collector memory, ingestion and queries. Logs and traces are often better suited to individual-event context, subject to confidentiality and retention requirements.

## Think About The Combinations

Cardinality is determined by combinations, not merely the number of label keys. Ten routes, five outcomes and twenty instances can yield many series for one family. Additional dimensions multiply the possible space. The observed population may be smaller, but planning should account for its realistic growth and churn.

A fixed label value that duplicates information already encoded elsewhere may add little query value. Conversely, an ownership label can be essential for alert routing. Choose dimensions based on the operational questions and downstream decisions they enable rather than maximize either detail or minimality indiscriminately.

## Preserve Consistent Arithmetic

A quantity should make sense when the intended series are aggregated. Summing counts across non-overlapping populations can produce a total. Summing percentages or unrelated units may not. If a metric uses a ratio, document its denominator and whether aggregation needs weighting. A misleading name cannot be corrected by a visually attractive dashboard.

A gauge's ordinary decrease is not a counter reset. A name ending in total does not justify using rate if the producer actually overwrites an arbitrary current value. Validate the implementation and update boundary as well as the naming convention.

## Change Contracts Deliberately

Renaming a metric or changing its labels creates different series and can break selectors, recording rules, alert matching and dashboards. Historical samples keep their original identity. A transition may need a documented compatibility period and updated consumers rather than silently assign a new meaning to the same name.

Review whether old and new metrics are collected simultaneously and whether broad queries double-count during migration. Retire obsolete families deliberately and explain missing series separately from zero activity. The aim is a stable, understandable measurement interface that can evolve without concealing changes in population or meaning.

## Common pitfalls

> [!WARNING]
> Names and labels define a measurement interface. Base units, bounded dimensions and consistent populations matter, while a counter-looking name cannot repair gauge behavior or automatically migrate historical series.
