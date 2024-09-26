import dagger
from dagger import dag


class Cluster:
    @classmethod
    async def create(cls, name: str) -> "Cluster":
        self = cls()
        self.k3s = dag.k3_s(name)
        await self.k3s.server().start()
        return self

    @property
    def config(self) -> dagger.File:
        return self.k3s.config()


def helm_install(config: dagger.File, chart: str, version: str, repo: str, values: dict[str, str]) -> dagger.Container:
    """
    Install a helm chart from a repository
    
    :param config: The kubeconfig file
    :param chart: The chart name
    :param version: The chart version
    :param repo: The repository URL
    :param values: The values to pass to the chart
    """
    # TODO: define namespace for the chart
    install_args = [
        "helm", "upgrade", "--install",
        "--create-namespace", "--wait", "--debug",
        "--version", version, chart, chart
    ]
    for key, value in values.items():
        install_args.extend(["--set", f"{key}={value}"])
    return (
        deployer(config)
        .with_exec(args=["helm", "pull", f"oci://{repo}/{chart}", "--version", version, "--untar", "--plain-http"])
        .with_exec(args=install_args)
    )

def deployer(config: dagger.File) -> dagger.Container:
    """
    Deployer container to interact with the cluster

    :param config: The kubeconfig file
    """
    return (
        dag.container()
        .from_("alpine/helm")
        .with_exec(args=["apk", "add", "kubectl"])
        .with_env_variable("KUBECONFIG", "/.kube/config")
        .with_file("/.kube/config", config)
    )