import argparse
from pathlib import Path

import subprocess

def deploy(type, namespace, values_file, debug, dry_run):
  print(values_file)
  if type == "support":
    helm_chart = Path(__file__).parent.joinpath("helm-charts/support")
  elif type == "app":
    helm_chart = Path(__file__).parent.joinpath("helm-charts/app")
  else:
    raise ValueError(f"Unknown type: {type}")

  cmd = [
    "helm",
    "upgrade",
    "--install",
    "--create-namespace",
    "--wait",
    f"--namespace={namespace}",
    namespace,
    helm_chart
  ]

  if values_file:
    values_file = helm_chart.joinpath(values_file)
    cmd.append(f"--values={values_file}")

  if dry_run:
    cmd.append("--dry-run")

  if debug:
    cmd.append("--debug")

  print(f"Running {' '.join([str(c) for c in cmd])}")
  subprocess.check_call(cmd)

def main():
  parser = argparse.ArgumentParser(description='Deploy script')
  parser.add_argument('type', type=str, help='Type of deployment. Choose from support/app!')
  parser.add_argument('--namespace', type=str, help='Namespace to deploy to')
  parser.add_argument('--values_file', type=str, help='Name of the values file', default=None)
  parser.add_argument('--dry-run', action='store_true', help='Perform a dry run')
  parser.add_argument('--debug', action='store_true', help='Enable debug mode')

  args = parser.parse_args()

  deploy(args.type, args.namespace, args.values_file, args.debug, args.dry_run)

if __name__ == "__main__":
    main()