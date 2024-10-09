import argparse
import json
import os
import subprocess
import tempfile
from contextlib import ExitStack, contextmanager
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scanner import ScannerError

yaml = YAML(typ="safe", pure=True)


@contextmanager
def auth(
    key_path,
    cluster="openorganelle",
    location="us-west2-a",
    project="segmentation-challenge",
):
    orig_file = os.environ.get("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE")
    orig_kubeconfig = os.environ.get("KUBECONFIG")
    try:
        with (
            tempfile.NamedTemporaryFile() as kubeconfig,
            get_decrypted_file(key_path) as decrypted_file,
        ):
            os.environ["KUBECONFIG"] = kubeconfig.name
            os.environ["CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE"] = (
                decrypted_file
            )

            subprocess.check_call(
                [
                    "gcloud",
                    "container",
                    "clusters",
                    f"--zone={location}",
                    f"--project={project}",
                    "get-credentials",
                    cluster,
                ]
            )

            yield
    finally:
        # restore modified environment variables to its previous state
        if orig_kubeconfig is not None:
            os.environ["KUBECONFIG"] = orig_kubeconfig
        else:
            os.environ.pop("KUBECONFIG")
        if orig_file is not None:
            os.environ["CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE"] = orig_file
        else:
            os.environ.pop("CLOUDSDK_AUTH_CREDENTIAL_FILE_OVERRIDE")


@contextmanager
def get_decrypted_file(original_filepath):
    """
    Copied from 2i2c/infrastructure
    """
    if not os.path.isfile(original_filepath):
        raise FileNotFoundError(
            f"""
            File Not Found at following location! Have you checked it's the
            correct path? {original_filepath}
        """
        )
    filename = os.path.basename(original_filepath)
    _, ext = os.path.splitext(filename)

    if "secret" in filename:
        with open(original_filepath) as f:
            if ext.endswith("json"):
                loader_func = json.load
            else:
                loader_func = yaml.load
            try:
                content = loader_func(f)
            except ScannerError:
                raise ScannerError(
                    "We expect encrypted files to be valid JSON or YAML files."
                )

        if "sops" not in content:
            raise KeyError(
                """
                Expecting to find the `sops` key in this encrypted file - but
                it wasn't found! Please regenerate the secret in case it has
                been checked into version control and leaked!
                """
            )

        # If file has a `sops` key, we assume it's sops encrypted
        with tempfile.NamedTemporaryFile() as f:
            subprocess.check_call(
                ["sops", "--output", f.name, "--decrypt", original_filepath]
            )
            yield f.name

    else:
        # The file does not have "secret" in its name, therefore does not need
        # to be decrypted. Yield the original filepath unchanged.
        yield original_filepath


@contextmanager
def get_decrypted_files(files):
    """
    Copied from 2i2c/infrastructure
    """
    with ExitStack() as stack:
        yield [stack.enter_context(get_decrypted_file(f)) for f in files]


def deploy(type, namespace, values_files, debug, dry_run):
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
        helm_chart,
    ]
    if dry_run:
        cmd.append("--dry-run")
    if debug:
        cmd.append("--debug")

    if values_files:
        with get_decrypted_files(values_files) as val_files:
            val_files_str = [str(file) for file in val_files]
            for val_file in val_files_str:
                cmd.append(f"--values={val_file}")

            print(f"Running {' '.join([str(c) for c in cmd])}")
            subprocess.check_call(cmd)
    else:
        print(f"Running {' '.join([str(c) for c in cmd])}")
        subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Deploy script")
    parser.add_argument(
        "type", type=str, help="Type of deployment. Choose from support/app!"
    )
    parser.add_argument(
        "--namespace",
        type=str,
        help="Namespace to deploy to. Choose from support/staging/prod",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Perform a dry run"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug mode"
    )

    args = parser.parse_args()
    key_path = Path(__file__).parent.joinpath(
        "helm-charts/enc-deploy-credentials.secret.json"
    )
    if args.type == "support":
        helm_chart = Path(__file__).parent.joinpath("helm-charts/support")
        values_files = [
            helm_chart.joinpath(f"{args.namespace}.values.yaml"),
        ]
    elif args.type == "app":
        helm_chart = Path(__file__).parent.joinpath("helm-charts/app")
        values_files = [
            helm_chart.joinpath("common.values.yaml"),
            helm_chart.joinpath(
                f"{args.namespace}/{args.namespace}.values.yaml"
            ),
            helm_chart.joinpath(
                f"{args.namespace}/enc-{args.namespace}.secret.values.yaml"
            ),
        ]
    else:
        raise ValueError(f"Unknown type: {args.type}")

    with auth(key_path):
        deploy(
            args.type,
            args.namespace,
            values_files,
            args.debug,
            args.dry_run,
        )


if __name__ == "__main__":
    main()
