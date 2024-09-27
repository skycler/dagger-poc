import asyncio
from typing import Annotated

import dagger
from dagger import function, object_type
from typing_extensions import Doc

from .cluster import Cluster
from .hello_world import make_service
from .nginx import Nginx
from .octant import Octant
from .settings import Settings


@object_type
class DaggerPoc:

    @function
    async def platform(self,
        registry: Annotated[dagger.Service, Doc("The local registry endpoint (<host>:<port>) to pull the images and charts from.")],
        config: Annotated[dagger.File | None, Doc("The configuration yaml file for the platform.")] = None,
        is_dev: Annotated[bool, Doc("Whether to run the platform in development mode.")] = False
    ) -> dagger.Container:
        """
        Create a k3s cluster and deploy some services using helm.
        Outside of the cluster run octant to interact with the cluster.
        """
        repo = await registry.endpoint()
        # Start a k3s server and get the kubeconfig
        cluster = await Cluster.create("my-cluster", repo)
        # Load the settings
        settings = await Settings.from_file(config, with_registry=repo)
        # Deploy some services using helm
        tasks = [cluster.install_chart(chart) for chart in settings.charts]
        await asyncio.gather(*tasks)
        # return the container to interact with the cluster
        if is_dev:
            # Run the container with kubectl and helm to interact with the cluster
            return (
                cluster.deployer()
                .with_env_variable("REGISTRY", repo)
            )
        else:
            # Run octant dashboard for monitoring the cluster
            return Octant().run(cluster.k3s.config(), settings.octant.version, settings.octant.port)

    @function
    async def nginx(self,
        port: Annotated[int, Doc("The port to expose")] = 8008,
        n_services: Annotated[int, Doc("The number of services to deploy")] = 1,
    ) -> dagger.Service:
        """
        Create an nginx server with three hello-world services.
        """
        # Run nginx to expose the services
        nginx = Nginx(port)
        for i in range(n_services):
            await nginx.add_server(f"hello-world-{i}", make_service(), 9001 + i)
        return nginx.run()