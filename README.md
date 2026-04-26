# k8s-cost-lens

> Lightweight Kubernetes resource analyzer that estimates per-namespace cloud spend from live cluster metrics.

---

## Installation

```bash
pip install k8s-cost-lens
```

> Requires `kubectl` configured with access to your target cluster.

---

## Usage

Analyze resource usage and estimated costs across all namespaces:

```bash
k8s-cost-lens analyze
```

Target a specific namespace:

```bash
k8s-cost-lens analyze --namespace production
```

Export results as JSON:

```bash
k8s-cost-lens analyze --output json > report.json
```

**Example output:**

```
NAMESPACE        CPU (cores)   MEMORY (GiB)   EST. MONTHLY COST
production       4.20          8.50           $112.40
staging          1.10          2.30           $29.80
default          0.30          0.60           $7.90
```

Cost estimates are based on configurable on-demand pricing for AWS, GCP, and Azure.
Set your cloud provider with `--provider aws` (default).

---

## Configuration

Override default pricing via environment variables:

```bash
export K8S_COST_LENS_CPU_PRICE=0.048      # price per vCPU-hour
export K8S_COST_LENS_MEMORY_PRICE=0.006   # price per GiB-hour
```

---

## Requirements

- Python 3.8+
- `kubectl` with valid kubeconfig
- Metrics Server installed in your cluster

---

## License

This project is licensed under the [MIT License](LICENSE).