import dagger
from dagger import dag


class Nginx:
    port: int
    container: dagger.Container
    port_mapping: dict[str, int] = {}

    def __init__(self, port: int):
        self.port = port
        self.container = (
            dag.container()
            .from_("nginx:1.21.3")
        )
    
    async def add_server(self, name: str, service: dagger.Service, port: int) -> None:
        """
        Add a server to the nginx configuration

        :param name: The name of the server
        :param service: The service to bind to the server
        :param port: The port to bind the server to
        """
        svc_port = await (await service.ports())[0].port()
        config = f"""
server {{
    listen {port};
    location / {{
        proxy_pass http://{name}:{svc_port};
    }}
}}"""
        self.container = (
            self.container
            .with_service_binding(name, service)
            .with_exec(args=["sh", "-c", f"cat > /etc/nginx/conf.d/{name}.conf <<EOL\n{config}\nEOL"])
            .with_exposed_port(port, experimental_skip_healthcheck=True)
        )
        self.port_mapping[name] = port
    
    def run(self) -> dagger.Service:
        config = f"""
server {{
    listen {self.port};
    location / {{
        add_header Content-Type text/html;
        return 200 "<html><body>
        <h1>List of available ports</h1>
        <ul>
        {"".join(f"<li>{name}: {port}</li>" for name, port in self.port_mapping.items())}
        </ul>
        </body></html>";
    }}
}}"""
        return (
            self.container
            .with_exposed_port(self.port)
            .with_exec(args=["sh", "-c", f"cat > /etc/nginx/conf.d/root.conf <<EOL\n{config}\nEOL"])
            .with_exec(args=["nginx", "-g", "daemon off;"])
            .as_service()
        )