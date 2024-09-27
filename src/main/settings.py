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
	namespace: str = Field(default = "default", description="The namespace to deploy the chart")
	values: dict[str, str] = Field(default = {}, description="The values to pass to the chart")

class Settings(BaseModel):
	local_registry_acronym: str | None = Field(default = None, description="The acronym for the local registry")
	octant: Octant = Field(default = Octant(), description="The octant settings")
	charts: list[Chart] = Field(default = [], description="The charts to deploy")

	@staticmethod
	async def from_file(file: dagger.File | None, with_registry: str | None) -> "Settings":
		"""
		Load the settings from a file
		
		:param file: The file to load the settings from
		"""
		settings = Settings()
		if file is not None:
			yaml = await file.contents()
			settings = Settings(**safe_load(yaml))
		if with_registry is not None and settings.local_registry_acronym is not None:
			# Replace the local registry acronym with the dagger-internal registry URL
			for chart in settings.charts:
				# for chart registries
				if chart.registry == settings.local_registry_acronym:
					chart.registry = with_registry
				# for values
				for key, value in chart.values.items():
					if value == settings.local_registry_acronym:
						chart.values[key] = with_registry
		return settings