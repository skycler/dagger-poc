import dagger
from dagger import dag


class Nginx:
    port: int

    def __init__(self, port: int):
        self.port = port

    async def run_nginx(self, name: str, service: dagger.Service, port: int) -> dagger.Container:
        """
        Start the nginx server

        :param config: The nginx configuration file
        :param port: The port to expose
        """
        config = f"""
server {{
    listen {self.port};
    location / {{
        proxy_pass http://{name}:{port};
        proxy_set_header Upgrade "websocket";
        proxy_set_header Connection "keep-alive, Upgrade";
        proxy_http_version 1.1;
        proxy_redirect off;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Server \$host;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }}
}}"""
        return (
            dag.container()
            .from_("nginx:1.21.3")
            .with_service_binding(name, service)
            .with_exec(args=["sh", "-c", f"cat > /etc/nginx/conf.d/test.conf <<EOL\n{config}\nEOL"])
            .with_exec(args=["nginx", "-g", "daemon off;"])
            .with_exposed_port(self.port)
        )