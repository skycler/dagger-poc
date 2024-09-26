import dagger
from pydantic import BaseModel, Field
from yaml import safe_load


class Octant(BaseModel):
	version: str = Field(default = "0.25.1", description="The octant version to use")
	port: int = Field(default = 9000, description="The port to expose")

class Chart(BaseModel):
	name: str = Field(..., description="The chart name")
	version: str = Field(..., description="The chart version")
	registry: str = Field(..., description="The registry URL")
	path: str = Field(default = "", description="The path to the chart")
	values: dict[str, str] = Field(default = {}, description="The values to pass to the chart")

class Settings(BaseModel):
	local_registry_acronym: str = Field(..., description="The acronym for the local registry")
	octant: Octant = Field(default = Octant(), description="The octant settings")
	charts: list[Chart] = Field(default = [], description="The charts to deploy")

	@staticmethod
	async def from_file(file: dagger.File | None) -> "Settings":
		"""
		Load the settings from a file
		
		:param file: The file to load the settings from
		"""
		if file is None:
			return Settings()
		else:
			yaml = await file.contents()
			return Settings(**safe_load(yaml))
	
	def resolve_local_registry(self, local_registry: str) -> None:
		"""
		Replace the local registry acronym with the local registry URL

		:param local_registry: The local registry URL
		"""
		for chart in self.charts:
			# for chart registries
			if chart.registry == self.local_registry_acronym:
				chart.registry = local_registry
			# for values
			for key, value in chart.values.items():
				if value == self.local_registry_acronym:
					chart.values[key] = local_registry
			