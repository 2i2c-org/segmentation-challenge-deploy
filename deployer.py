import argparse
from pathlib import Path

import subprocess

HELM_CHARTS_DIR = Path(__file__).parent.joinpath("helm-chart")
print(HELM_CHARTS_DIR)

def deploy(namespace, values_file, debug, dry_run):
  cmd = [
      "helm",
      "upgrade",
      "--install",
      "--create-namespace",
      "--wait",
      f"--values={values_file}",
      f"--namespace={namespace}",
      namespace,
      HELM_CHARTS_DIR
  ]

  if dry_run:
      cmd.append("--dry-run")

  if debug:
      cmd.append("--debug")

  print(f"Running {' '.join([str(c) for c in cmd])}")
  subprocess.check_call(cmd)

def main():
  parser = argparse.ArgumentParser(description='Deploy script')
  parser.add_argument('namespace', type=str, help='Namespace to deploy to')
  parser.add_argument('values_file', type=str, help='Name of the values file')
  parser.add_argument('--dry-run', action='store_true', help='Perform a dry run')
  parser.add_argument('--debug', action='store_true', help='Enable debug mode')

  args = parser.parse_args()

  print(args)

  values_file = HELM_CHARTS_DIR.joinpath(args.values_file)
  deploy(args.namespace, values_file, args.dry_run, args.debug)

if __name__ == "__main__":
    main()