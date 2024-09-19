from uuid import uuid4
import dagger
from dagger import dag


def make_service() -> dagger.Service:
    port = 8080
    msg = f"""
<html><body>
<h1>Hello, World!</h1>
<h2>{str(uuid4())[:8]}</h2>
</body></html>
"""
    return (
        dag.container()
        .from_("python")
        .with_workdir("/srv")
        .with_new_file("index.html", msg)
        .with_exec(["python", "-m", "http.server", str(port)])
        .with_exposed_port(port)
        .as_service()
    )