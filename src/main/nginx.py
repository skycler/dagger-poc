import dagger
from dagger import dag


class Nginx:
    container: dagger.Container

    def __init__(self, port: int):
        config = f"""
server {{
    listen {port};
    location / {{
        add_header Content-Type text/html;
        return 200 "<html><body><h1>Hello, World!</h1></body></html>";
    }}
}}"""
        self.container = (
            dag.container()
            .from_("nginx:1.21.3")
            .with_exposed_port(port)
            .with_exec(args=["sh", "-c", f"cat > /etc/nginx/conf.d/root.conf <<EOL\n{config}\nEOL"])
            .with_exec(args=["sh", "-c", """cat >> /etc/nginx/nginx.conf <<EOL
stream {
    include /etc/nginx/server-conf.d/server-*.conf;
}"""])
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
    
    def run(self) -> dagger.Service:
        return (
            self.container
            .with_exec(args=["nginx", "-g", "daemon off;"])
            .as_service()
        )