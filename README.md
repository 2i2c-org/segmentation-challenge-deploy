# segmentation-challenge-deploy

This repository contains the code to deploy the [2i2c FRX Challenges](https://2i2c.org/frx-challenges) [helm chart](https://2i2c.org/frx-challenges-helm-chart) for the segmentation challenge.

## Installation

You can install the chart by running the `deployer` script like:

1. Install the support chart:

```bash
python3 deployer.py support --namespace=support
```

2. Install the app chart:

- For staging:

  ```bash
  python3 deployer.py app --namespace=staging
  ```

- For production:
  ```bash
  python3 deployer.py app --namespace=prod
  ```

### Debugging

1. You can also use the `--dry-run` flag to see the generated manifests without applying them.
2. You can use the `--debug` flag to see the helm command being run.
