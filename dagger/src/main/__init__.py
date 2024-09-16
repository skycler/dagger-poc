import dagger
from dagger import dag, function


@function
def deployer(config: dagger.File) -> dagger.Container:
	return (
		dag.container()
		.from_("alpine/helm")
		.with_exec(args=["apk", "add", "kubectl"])
		.with_env_variable("KUBECONFIG", "/.kube/config")
		.with_file("/.kube/config", config)
	)

@function
def helm_install(config: dagger.File, chart: str, version: str, repo: str) -> dagger.Container:
	return (
		deployer(config)
		.with_exec(args=["helm", "pull", f"{repo}/{chart}", "--version", version, "--untar", "--plain-http"])
		.with_exec(args=["helm", "install", "--wait", "--debug", chart, chart])
	)

@function
async def monet_platform() -> dagger.Container:
	k3s = dag.k3_s("monet")
	await k3s.server().start()
	kubce_config = k3s.config()
	#await helm_install(kube_config, "mp-model-platform-test", "0.0.0", "oci://host.docker.internal:5001/helm")
	await helm_install(kubce_config, "nginx", "18.1.14", "oci://registry-1.docker.io/bitnamicharts")
	await helm_install(kubce_config, "rabbitmq", "14.7.0", "oci://registry-1.docker.io/bitnamicharts")
	return deployer(kubce_config)