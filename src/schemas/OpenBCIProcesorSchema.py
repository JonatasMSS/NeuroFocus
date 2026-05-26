
from pathlib import Path

from pydantic import BaseModel, Field, field_validator


class OpenBCIProcessorConfig(BaseModel):
    input_path: str = Field(..., description="Caminho do arquivo OpenBCI original")
    output_path: str = Field(..., description="Caminho onde o CSV limpo será salvo")

    @field_validator("input_path")
    @classmethod
    def validate_input_path(cls, value: str) -> str:
        path = Path(value)

        if not path.exists():
            raise ValueError(f"Arquivo de entrada não encontrado: {value}")

        if not path.is_file():
            raise ValueError(f"O caminho informado não é um arquivo: {value}")

        return value