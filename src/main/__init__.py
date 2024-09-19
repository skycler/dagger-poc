import asyncio
from typing import Annotated

import dagger
from dagger import dag, function, object_type
from typing_extensions import Doc

from .cluster import Cluster, helm_install
from .hello_world import make_service
from .nginx import Nginx
from .octant import Octant
from .settings import Settings


@object_type
class DaggerPoc:

    @function
    async def platform(self,
        config: Annotated[dagger.File | None, Doc("The configuration yaml file for the platform.")] = None
    ) -> dagger.Service:
        """
        Create a k3s cluster and deploy some services using helm.
        Outside of the cluster run octant to interact with the cluster.
        """
        # Load the settings
        settings = Settings() if config is None else Settings.from_yaml(await config.contents())
        # Start a k3s server and get the kubeconfig
        cluster = await Cluster.create("my-cluster")
        kube_config = cluster.config
        # Deploy some services using helm
        tasks = [helm_install(kube_config, chart.name, chart.version, chart.repo) for chart in settings.charts]
        await asyncio.gather(*tasks)
        # Run octant dashboard for monitoring the cluster
        #octant = Octant().run(kube_config, settings.octant.version, settings.octant.port)
        # Run a web service (postgres DB)
        # db = (
        #     dag.container()
        #     .from_("postgres:15.7")
        #     .with_exposed_port(5432)
        #     .with_env_variable("POSTGRES_USER", "postgres")
        #     .with_env_variable("POSTGRES_PASSWORD", "postgrespw")
        #     .as_service()
        # )
        # Run nginx to expose the services
        nginx = Nginx(settings.nginx.port)
        await nginx.add_server("hello-world-1", make_service(), 9001)
        await nginx.add_server("hello-world-2", make_service(), 9002)
        await nginx.add_server("hello-world-3", make_service(), 9003)
        return nginx.run()
