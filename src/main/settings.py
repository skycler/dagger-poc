import dagger
from pydantic import BaseModel, Field
from yaml import safe_load


class Octant(BaseModel):
	version: str = Field(default = "0.25.1", description="The octant version to use")
	port: int = Field(default = 9000, description="The port to expose")

class Chart(BaseModel):
	name: str = Field(description="The name of the helm chart")
	version: str = Field(description="The version of the helm chart")
	repo: str = Field(description="The repository URL of the helm chart")
	values: dict[str, str] = Field(default = {}, description="The values to pass to the helm chart")

class Settings(BaseModel):
	octant: Octant = Field(default = Octant(), description="The octant settings")
	charts: list[Chart] = Field(default = [], description="The charts to deploy")

	@staticmethod
	async def from_file(file: dagger.File | None) -> "Settings":
		if file is None:
			return Settings()
		else:
			yaml = await file.contents()
			return Settings(**safe_load(yaml))