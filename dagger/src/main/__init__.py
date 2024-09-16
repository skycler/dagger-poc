import asyncio
import dagger
from dagger import dag, function


@function
async def platform() -> dagger.Container:
	# Start a k3s server and get the kubeconfig
	k3s = dag.k3_s("monet")
	await k3s.server().start()
	kubce_config = k3s.config()
	# Deploy some services using helm
	tasks = [
		helm_install(kubce_config, "nginx", "18.1.14", "oci://registry-1.docker.io/bitnamicharts"),
		helm_install(kubce_config, "rabbitmq", "14.7.0", "oci://registry-1.docker.io/bitnamicharts"),
		helm_install(kubce_config, "postgresql", "15.5.31", "oci://registry-1.docker.io/bitnamicharts")
		#helm_install(kube_config, "mp-model-platform-test", "0.0.0", "oci://host.docker.internal:5001/helm")
	]
	await asyncio.gather(*tasks)
	# Return a container ready to interact with the cluster
	return deployer(kubce_config)

@function
def helm_install(config: dagger.File, chart: str, version: str, repo: str) -> dagger.Container:
	return (
		deployer(config)
		.with_exec(args=["helm", "pull", f"{repo}/{chart}", "--version", version, "--untar", "--plain-http"])
		.with_exec(args=["helm", "install", "--wait", "--debug", chart, chart])
	)

@function
def deployer(config: dagger.File) -> dagger.Container:
	return (
		dag.container()
		.from_("alpine/helm")
		.with_exec(args=["apk", "add", "kubectl"])
		.with_env_variable("KUBECONFIG", "/.kube/config")
		.with_file("/.kube/config", config)
	)