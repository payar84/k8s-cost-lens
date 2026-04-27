"""Collects CPU and memory resource requests/limits from Kubernetes namespaces."""

from dataclasses import dataclass, field
from typing import Dict, List

from kubernetes import client, config
from kubernetes.client.exceptions import ApiException


@dataclass
class NamespaceMetrics:
    namespace: str
    cpu_requests_cores: float = 0.0
    cpu_limits_cores: float = 0.0
    memory_requests_bytes: float = 0.0
    memory_limits_bytes: float = 0.0
    pod_count: int = 0
    containers: List[str] = field(default_factory=list)


def _parse_cpu(value: str) -> float:
    """Convert CPU string (e.g. '500m', '1') to fractional cores."""
    if value.endswith("m"):
        return float(value[:-1]) / 1000.0
    return float(value)


def _parse_memory(value: str) -> float:
    """Convert memory string (e.g. '128Mi', '1Gi') to bytes."""
    units = {"Ki": 1024, "Mi": 1024**2, "Gi": 1024**3, "Ti": 1024**4,
             "K": 1000, "M": 1000**2, "G": 1000**3}
    for suffix, multiplier in units.items():
        if value.endswith(suffix):
            return float(value[:-len(suffix)]) * multiplier
    return float(value)


class MetricsCollector:
    def __init__(self, in_cluster: bool = False):
        if in_cluster:
            config.load_incluster_config()
        else:
            config.load_kube_config()
        self._core = client.CoreV1Api()

    def collect(self, namespaces: List[str] = None) -> Dict[str, NamespaceMetrics]:
        """Return per-namespace resource metrics from pod specs."""
        results: Dict[str, NamespaceMetrics] = {}
        try:
            pods = self._core.list_pod_for_all_namespaces(watch=False)
        except ApiException as exc:
            raise RuntimeError(f"Failed to list pods: {exc}") from exc

        for pod in pods.items:
            ns = pod.metadata.namespace
            if namespaces and ns not in namespaces:
                continue
            if pod.status.phase not in ("Running", "Pending"):
                continue
            if ns not in results:
                results[ns] = NamespaceMetrics(namespace=ns)
            metrics = results[ns]
            metrics.pod_count += 1
            for container in pod.spec.containers:
                metrics.containers.append(container.name)
                res = container.resources
                if res and res.requests:
                    metrics.cpu_requests_cores += _parse_cpu(res.requests.get("cpu", "0"))
                    metrics.memory_requests_bytes += _parse_memory(res.requests.get("memory", "0"))
                if res and res.limits:
                    metrics.cpu_limits_cores += _parse_cpu(res.limits.get("cpu", "0"))
                    metrics.memory_limits_bytes += _parse_memory(res.limits.get("memory", "0"))
        return results
