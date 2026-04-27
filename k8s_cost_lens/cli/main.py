"""CLI entry point for k8s-cost-lens."""

import argparse
import sys
from pathlib import Path

from k8s_cost_lens.metrics.collector import MetricsCollector
from k8s_cost_lens.metrics.cost_estimator import CostEstimator
from k8s_cost_lens.report.exporter import CostReportExporter


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="k8s-cost-lens",
        description="Estimate per-namespace Kubernetes cloud spend from live metrics.",
    )
    parser.add_argument(
        "--kubeconfig",
        default=None,
        metavar="PATH",
        help="Path to kubeconfig file (defaults to in-cluster config).",
    )
    parser.add_argument(
        "--cpu-price",
        type=float,
        default=0.048,
        metavar="USD",
        help="Hourly price per vCPU core (default: $0.048).",
    )
    parser.add_argument(
        "--mem-price",
        type=float,
        default=0.006,
        metavar="USD",
        help="Hourly price per GiB of memory (default: $0.006).",
    )
    output_group = parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--csv",
        metavar="FILE",
        help="Write results to a CSV file.",
    )
    output_group.add_argument(
        "--json",
        metavar="FILE",
        help="Write results to a JSON file.",
    )
    return parser


def _validate_prices(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """Validate that price arguments are positive values."""
    if args.cpu_price <= 0:
        parser.error("--cpu-price must be a positive value.")
    if args.mem_price <= 0:
        parser.error("--mem-price must be a positive value.")


def run(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _validate_prices(args, parser)

    collector = MetricsCollector(kubeconfig=args.kubeconfig)
    try:
        namespace_metrics = collector.collect()
    except Exception as exc:  # pragma: no cover
        print(f"[error] Failed to collect metrics: {exc}", file=sys.stderr)
        return 1

    estimator = CostEstimator(
        cpu_price_per_core_hour=args.cpu_price,
        memory_price_per_gib_hour=args.mem_price,
    )
    costs = [estimator.estimate(m) for m in namespace_metrics]

    exporter = CostReportExporter(costs)

    if args.csv:
        exporter.to_file_csv(Path(args.csv))
        print(f"CSV report written to {args.csv}")
    elif args.json:
        exporter.to_file_json(Path(args.json))
        print(f"JSON report written to {args.json}")
    else:
        exporter.to_stdout_table()

    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run())


if __name__ == "__main__":  # pragma: no cover
    main()
