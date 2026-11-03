---
draft: true
exam_objectives:
- Structuring and naming metrics
---
# Prerequisites

Use astrona, kubectl, kind, Python 3, Podman and a shell.

Use a host shell with the private kubeconfig for this independent kind environment. A kubeconfig identifies the cluster and credentials used by kubectl, the Kubernetes command-line tool.

```sh
export KUBECONFIG="$(astrona kubeconfig ats-050-lab-040-02-01)"
test "$(kubectl config current-context)" = "kind-astro-ats-050-lab-040-02-01" || exit 1
```

Keep this connection selected. Every command in this lab targets only this environment.
