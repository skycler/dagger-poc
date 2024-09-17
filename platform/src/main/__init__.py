import asyncio
import dagger
from dagger import dag, function, object_type
from pydantic import BaseModel

# NOTE: it's recommended to move your code into other files in this package
# and keep __init__.py for imports only, according to Python's convention.
# The only requirement is that Dagger needs to be able to import a package
# called "main", so as long as the files are imported here, they should be
# available to Dagger.

class Chart(BaseModel):
	name: str
	version: str
	repo: str

# List of charts to deploy
CHARTS = [
	Chart(name="nginx", version="18.1.14", repo="oci://registry-1.docker.io/bitnamicharts"),
	Chart(name="rabbitmq", version="14.7.0", repo="oci://registry-1.docker.io/bitnamicharts"),
	Chart(name="postgresql", version="15.5.31", repo="oci://registry-1.docker.io/bitnamicharts"),
	#Chart(name="mp-model-platform-test", version="0.0.0", repo="oci://host.docker.internal:5001/helm")
]

@object_type
class DaggerPoc:
	k3s = dag.k3_s("monet")

	@function
	async def platform(self) -> dagger.Container:
		"""
		Deploy a k3s cluster and deploy some services using helm
		"""
		# Start a k3s server and get the kubeconfig
		await self.k3s.server().start()
		kube_config = self.k3s.config()
		# Deploy some services using helm
		tasks = [self.helm_install(kube_config, chart.name, chart.version, chart.repo) for chart in CHARTS]
		await asyncio.gather(*tasks)
		# Return a container ready to interact with the cluster
		return self.deployer(kube_config)

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