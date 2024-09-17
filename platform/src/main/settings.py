from pydantic import BaseModel, Field
from yaml import safe_load


class Octant(BaseModel):
	version: str
	port: int

class Chart(BaseModel):
	name: str
	version: str
	repo: str

class Settings(BaseModel):
	octant: Octant = Field(default = Octant(version="0.25.1", port=9000), description="The octant settings")
	charts: list[Chart] = Field(default = [], description="The charts to deploy")
	
	@staticmethod
	def from_yaml(yaml: str) -> "Settings":
		return Settings(**safe_load(yaml))