import asyncio
import dagger
from dagger import dag, function, object_type

from .settings import Settings

@object_type
class DaggerPoc:
	k3s = dag.k3_s("monet")

	@function
	async def platform(self, config: dagger.File | None = None) -> dagger.Service:
		"""
		Deploy a k3s cluster and deploy some services using helm
		"""
		# Load the settings
		settings = Settings() if config is None else Settings.from_yaml(await config.contents())
		# Start a k3s server and get the kubeconfig
		await self.k3s.server().start()
		kube_config = self.k3s.config()
		# Deploy some services using helm
		tasks = [self.helm_install(kube_config, chart.name, chart.version, chart.repo) for chart in settings.charts]
		await asyncio.gather(*tasks)
		# Return a container ready to interact with the cluster
		return self.octant(kube_config)

	@function
	def helm_install(self, config: dagger.File, chart: str, version: str, repo: str) -> dagger.Container:
		"""
		Install a helm chart from a repository
		
		:param config: The kubeconfig file
		:param chart: The chart name
		:param version: The chart version
		:param repo: The repository URL
		"""
		return (
			self.deployer(config)
			.with_exec(args=["helm", "pull", f"{repo}/{chart}", "--version", version, "--untar", "--plain-http"])
			.with_exec(args=["helm", "install", "--wait", "--debug", chart, chart])
		)

	@function
	def deployer(self, config: dagger.File) -> dagger.Container:
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
	
	@function
	def octant(self, config: dagger.File, version: str = "0.25.1") -> dagger.Service:
		"""
		Start the octant dashboard

		:param config: The kubeconfig file
		:param version: The octant version
		"""
		return (
			dag.container()
			.from_("debian:buster-slim")
			.with_file("/.kube/config", config)
			.with_env_variable("KUBECONFIG", "/.kube/config")
			.with_env_variable("OCTANT_DISABLE_OPEN_BROWSER", "true")
			.with_env_variable("OCTANT_LISTENER_ADDR", "0.0.0.0:9000")
			.with_exec(args=[
				"sh", "-c", f"""\
apt-get update -qq \
&& apt-get install -yqq curl\
&& curl -L -o /tmp/octant.deb https://github.com/vmware/octant/releases/download/v{version}/octant_{version}_Linux-ARM64.deb \
&& dpkg -i /tmp/octant.deb \
&& rm -f /tmp/octant.deb \
&& apt-get autoremove -y \
&& apt-get autoclean \
&& rm -rf /var/lib/apt/lists/*"""
				]
			)
			.with_exec(args=["/usr/local/bin/octant"])
			.with_exposed_port(9000)
			.as_service()
		)