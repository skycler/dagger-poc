import asyncio
from typing import Annotated

import dagger
from dagger import function, object_type
from typing_extensions import Doc

from .cluster import Cluster, helm_install
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
        # Return a container ready to interact with the cluster
        return Octant().run(kube_config, settings.octant.version, settings.octant.port)
