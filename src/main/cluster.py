from datetime import datetime as dt
import dagger
from dagger import dag
from dagger.client.gen import K3S

from .settings import Chart


class Cluster():
    k3s: K3S

    def __init__(self, name: str):
        self.k3s = dag.k3_s(name)

    @classmethod
    async def create(cls, name: str, registry_endpoint: str) -> "Cluster":
        cluster = Cluster(name)
        # Start a k3s server with a mirror to the local registry, enforcing to use http instead of https
        await cluster.k3s.with_(
            lambda k: k.with_container(
                k.container()
                .with_env_variable("BUST", dt.now().isoformat())
                .with_exec(["sh", "-c", f"""
cat <<EOF > /etc/rancher/k3s/registries.yaml
mirrors:
  "{registry_endpoint}":
      endpoint:
        - "http://{registry_endpoint}"
EOF
"""])
            )).server().start()
        return cluster
    
    def install_chart(self, chart: Chart) -> None:
        """
        Install a helm chart from a repository
        
        :param chart: The chart name
        :param version: The chart version
        :param repo: The repository URL
        :param values: The values to pass to the chart
        """
        install_args = [
            "helm", "upgrade", "--install", "--namespace", chart.namespace,
            "--create-namespace", "--wait", "--debug", "--atomic",
            "--version", chart.version, chart.name, chart.name
        ]
        for key, value in chart.values.items():
            install_args.extend(["--set", f"{key}={value}"])
        return (
            self.deployer()
            .with_exec(args=["helm", "pull", f"oci://{chart.registry}/{chart.path}/{chart.name}", "--version", chart.version, "--untar", "--plain-http"])
            .with_exec(args=install_args)
        )

    def deployer(self) -> dagger.Container:
        """
        Deployer container to interact with the cluster

        :param config: The kubeconfig file
        """
        return (
            dag.container()
            .from_("alpine/helm")
            .with_exec(args=["apk", "add", "kubectl"])
            .with_env_variable("KUBECONFIG", "/.kube/config")
            .with_file("/.kube/config", self.k3s.config())
        )