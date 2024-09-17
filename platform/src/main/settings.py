from pydantic import BaseModel, Field
from yaml import safe_load


class Chart(BaseModel):
	name: str
	version: str
	repo: str

class Settings(BaseModel):
	charts: list[Chart] = Field(default = [], description="The charts to deploy")
	
	@staticmethod
	def from_yaml(yaml: str) -> "Settings":
		return Settings(**safe_load(yaml))