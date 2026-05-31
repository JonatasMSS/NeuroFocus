from pydantic import BaseModel, Field


class BandExtractorConfig(BaseModel):

    sample_rate_hz: float = Field(..., description="Taxa de amostragem em Hz")

    notch_freq: float = Field(
        default=60.0,
        description="Frequência do filtro notch (Hz) pro BR",
    )

    bandpass_low: float = Field(
        default=1.0,
        description="Limite inferior do filtro passa-banda (Hz).",
    )

    bandpass_high: float = Field(
        default=50.0,
        description="Limite superior do filtro passa-banda (Hz).",
    )

    butterworth_order: int = Field(
        default=4,
        description="Ordem do filtro Butterworth.",
    )

    window_seconds: float = Field(
        default=2.0,
        description="Tamanho da janela de Welch em segundos.",
    )

    window_overlap: float = Field(
        default=0.5,
        description="Sobreposição entre janelas (0–1).",
    )

    baseline_seconds: float | None = Field(
        default=None,
        description="Duração do baseline (s) para cálculo de ERD/ERS. None desativa o cálculo.",
    )
