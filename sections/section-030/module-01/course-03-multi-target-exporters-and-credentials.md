---
draft: true
exam_objectives:
- Exporters
---
# Multi-Target Exporters, Credentials And Cost

Some exporters do not belong to one system. The Blackbox Exporter probes any address that it is asked to probe, and exporters for SNMP devices or cloud accounts work in the same way. One exporter instance serves many targets, and the target is a parameter of each request. This chapter explains how Prometheus is configured for this pattern and how to handle credentials and cost.

## The Multi-Target Pattern

An ordinary exporter is scraped at its own address, and it reads one system. A multi-target exporter is scraped at a path such as `/probe` with a query parameter that names the real target. For the Blackbox Exporter the request looks like this:

```text
http://blackbox-exporter:9115/probe?target=http://probe:8080/&module=http_2xx
```

The parameter `target` names what to probe. The parameter `module` selects a probe definition from the exporter configuration, for example `http_2xx`, which sends an HTTP request and expects a status code in the 2xx range.

The response holds metrics about this one probe. Among them are `probe_success`, which is 1 if the probe passed, `probe_duration_seconds` and, for HTTP probes, `probe_http_status_code`.

## The Scrape Configuration

Prometheus must scrape the exporter address, but it must remember which target each result belongs to. Relabeling achieves this. The documented configuration for the Blackbox Exporter looks like this:

```yaml
scrape_configs:
  - job_name: blackbox
    metrics_path: /probe
    params:
      module: [http_2xx]
    static_configs:
      - targets:
          - http://probe:8080/
          - http://probe:8080/work?status=500
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: blackbox-exporter:9115
```

The list under `targets` holds the addresses to probe, and not the address of the exporter.

## What Each Relabeling Rule Does

Relabeling runs before the scrape and rewrites the labels of each target. Labels that start with `__` are internal and are removed after relabeling.

The first rule copies the original address, which is the probe target, into the internal label `__param_target`. Labels with the prefix `__param_` become URL query parameters, so the scrape URL gets `target=<address>`.

The second rule copies the same value into the `instance` label. The results are then labeled with the probed address, and not with the exporter address.

The third rule sets `__address__` to the exporter address. This is where Prometheus sends the scrape request.

Because the `params` block sets `module`, the request carries `module=http_2xx` as well. The result is one scrape for each target in the list, each with its own `instance` label.

## Reading The Result

Select the results for one target with its `instance` label. The query `probe_success{job="blackbox", instance="http://probe:8080/"}` returns 1 if that probe passed. A target that answers with a status outside 2xx gives `probe_success` of 0, and the `up` series of that scrape stays at 1, because the exporter itself answered.

This again separates scrape health from target health. A failing probe is a normal, valid answer of the exporter.

## When A Probe Fails

The exporter returns metrics for a failed probe with `probe_success 0`. It does not return an HTTP error. For a failed DNS lookup or refused connection, the result also holds fewer metrics, because the later stages of the probe never ran. Alerts should therefore use `probe_success == 0`, and not the absence of other probe metrics.

## Credentials

An exporter often needs credentials to read its backend. Apply these rules.

Create a dedicated account for the exporter with the least privilege that it needs, usually read-only access to statistics.

Keep credentials out of command lines, because process lists show them. Use a file with restricted permissions, an environment variable from a secret store or a mounted secret.

Keep credentials out of metric labels, scrape URLs and logs. In a multi-target setup, never put a secret in a target address, because the address becomes the `instance` label and is stored and displayed.

Protect the exporter endpoint itself. A multi-target exporter that accepts any `target` can be used to make requests from the exporter host to any address that it can reach. Restrict who can call it, and limit it to the modules and networks that it must serve.

## Cost

Each target in a multi-target job is a separate scrape. A list of 500 targets creates 500 scrapes per interval, and each one makes the exporter contact the real target. Choose an interval that the targets can bear, and a timeout that is smaller than the interval.

Probes that run from one place show only the view from that place. A probe that passes from inside the cluster says nothing about the path that users take. Run probes from where the clients are, if the question is about their experience.

## Targets From Discovery

Instead of a static list, the target list can come from service discovery, a file or an API. The same relabeling rules apply to all of them. Only the source of `__address__` changes.

## What You Know Now

You can configure the multi-target pattern with the three relabeling rules and explain what each does. You know that a failed probe is a valid answer, so `up` stays 1 and `probe_success` is 0. You can apply the rules for credentials: least privilege, no secrets in addresses or labels and a protected endpoint.

## Common pitfalls

> [!WARNING]
> Without the relabeling rules, Prometheus would scrape the targets directly and not the exporter. Putting credentials in a target address exposes them in the `instance` label. An open multi-target exporter can be abused to send requests to internal addresses, so restrict access.
