import dagger
from dagger import dag


class Nginx:
    port: int

    def __init__(self, port: int):
        self.port = port

    async def run_nginx(self, name: str, service: dagger.Service, port: int) -> dagger.Service:
        """
        Start the nginx server

        :param config: The nginx configuration file
        :param port: The port to expose
        """
        svc_port = await (await service.ports())[0].port()
        config = f"""
server {{
    listen {self.port};
    location / {{
        proxy_pass http://{name}:{svc_port};
    }}
}}"""
        return (
            dag.container()
            .from_("nginx:1.21.3")
            .with_exposed_port(self.port)
            .with_exec(args=["sh", "-c", """cat >> /etc/nginx/nginx.conf <<EOL
stream {
    include /etc/nginx/server-conf.d/server-*.conf;
}"""])
            .with_service_binding(name, service)
            .with_exec(args=["sh", "-c", f"cat > /etc/nginx/conf.d/{name}.conf <<EOL\n{config}\nEOL"])
            .with_exec(args=["nginx", "-g", "daemon off;"])
            #.with_exposed_port(port, experimental_skip_healthcheck=True)
            .as_service()
        )