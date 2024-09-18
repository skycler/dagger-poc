import platform

import dagger
from dagger import dag


class Octant:

    def build(self, version: str) -> dagger.Container:
        """
        Build the octant image
        
        :param version: The octant version
        :param push: Push the image to the registry
        """
        install_tmp_file = "/tmp/octant.deb"
        match platform.machine():
            case "arm64" | "aarch64":
                arch = "ARM64"
            case "x86_64" | "AMD64":
                arch = "64bit"
            case "arm" | "arm32":
                arch = "ARM"
            case _:
                raise ValueError(f"Unsupported architecture: {platform.machine()}")
        return (
            dag.container()
            .from_("debian:buster-slim")
            .with_exec(args=[
                "sh", "-c", f"""\
apt-get update -qq \
&& apt-get install -yqq curl \
&& curl -L -o {install_tmp_file} https://github.com/vmware/octant/releases/download/v{version}/octant_{version}_Linux-{arch}.deb \
&& dpkg -i {install_tmp_file} \
&& rm -f {install_tmp_file} \
&& apt-get autoremove -y \
&& apt-get autoclean \
&& rm -rf /var/lib/apt/lists/*"""
                ]
            )
        )

    def run(self, config: dagger.File, version: str, port: int) -> dagger.Service:
        """
        Start the octant dashboard

        :param config: The kubeconfig file
        :param version: The octant version
        """
        kube_config_file = "/.kube/config"
        return (
            self.build(version)
            .with_file(kube_config_file, config)
            .with_env_variable("KUBECONFIG", kube_config_file)
            .with_env_variable("OCTANT_DISABLE_OPEN_BROWSER", "true")
            .with_env_variable("OCTANT_LISTENER_ADDR", f"0.0.0.0:{port}")
            .with_exec(args=["/usr/local/bin/octant"])
            .with_exposed_port(port)
            .as_service()
        )