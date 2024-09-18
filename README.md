# dagger-poc
minimal setup to deploy helm charts to k3s cluster using dagger.io

## How-to-Use
Since everything in dagger runs in containers, the only prerequisites are docker and dagger itself.
1. install dagger (v0.13.0): `cd /usr/local && curl -fsSL https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.13.0 sudo -E sh && cd -`
2. run `dagger call platform --config config.yaml up`
3. once the platform is up: open `localhost:9000`

## How-to-Develop
In order to develop locally, python 3.12 together with appropriate virtual environment must be setup.
1. install dagger CLI (see above step1)
2. make sure to have appropriate python version installed (see platform/pyproject.toml), including development libraries
3. install `uv`: `curl -LsSf https://astral.sh/uv/install.sh | sh`
4. re-generate sdk code: run `dagger develop -m platform`
5. create virtual environment: `cd platform && uv sync && cd -`