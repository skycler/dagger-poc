# dagger-poc
minimal setup to deploy helm charts to k3s cluster using dagger.io

## How-to-Use
1. install dagger (v0.13.0): `cd /usr/local && curl -fsSL https://dl.dagger.io/dagger/install.sh | DAGGER_VERSION=0.13.0 sudo -E sh`
2. run `dagger call platform --config config.yaml terminal`
3. once the terminal is ready: `kubectl get services`