from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from scipy import signal

from schemas.BandExtractorSchema import BandExtractorConfig

# Definição das bandas de frequência
BANDS: dict[str, tuple[float, float]] = {
    "delta": (0.5, 3.5),
    "theta": (4.0, 7.5),
    "alpha": (8.0, 13.0),
    "beta":  (14.0, 30.0),
    "gamma": (30.0, 50.0),
}


class BandExtractor:

    def __init__(self, config: BandExtractorConfig) -> None:
        self.config = config

    def process(self, data: pd.DataFrame) -> pd.DataFrame:

        exg_cols = [col for col in data.columns if col.startswith("exg_")]

        if not exg_cols:
            raise ValueError()

        fs = self.config.sample_rate_hz
        signals: dict[str, np.ndarray] = {
            col: data[col].dropna().to_numpy(dtype=float) for col in exg_cols
        }

        filtered = {col: self._prefilter(sig, fs) for col, sig in signals.items()}

        psds: dict[str, tuple[np.ndarray, np.ndarray]] = {
            col: self._compute_psd(sig, fs) for col, sig in filtered.items()
        }

        rows: list[dict] = []
        for col in exg_cols:
            freqs, psd = psds[col]
            row = {"channel": col}

            abs_powers: dict[str, float] = {}
            for band, (lo, hi) in BANDS.items():
                abs_powers[band] = self._band_power(freqs, psd, lo, hi)
                row[f"power_{band}"]    = abs_powers[band]

            total = self._band_power(
                freqs, psd,
                self.config.bandpass_low,
                self.config.bandpass_high,
            )

            for band in BANDS:
                row[f"relpower_{band}"] = (
                    abs_powers[band] / total if total > 0 else 0.0
                )

            row["tbr"] = (
                abs_powers["theta"] / abs_powers["beta"]
                if abs_powers["beta"] > 0 else np.nan
            )
            row["bar"] = (
                abs_powers["beta"] / abs_powers["alpha"]
                if abs_powers["alpha"] > 0 else np.nan
            )

            if self.config.baseline_seconds is not None:
                erd_ers = self._compute_erd_ers(
                    filtered[col], fs, freqs, psd
                )
                for band, value in erd_ers.items():
                    row[f"erd_ers_{band}"] = value

            rows.append(row)

        features_df = pd.DataFrame(rows).set_index("channel")

        for band in BANDS:
            features_df.loc["mean", f"power_{band}"] = (
                features_df[f"power_{band}"].mean()
            )
            features_df.loc["mean", f"relpower_{band}"] = (
                features_df[f"relpower_{band}"].mean()
            )

        features_df.loc["mean", "tbr"] = features_df["tbr"].mean()
        features_df.loc["mean", "bar"] = features_df["bar"].mean()

        self._print_summary(features_df)
        return features_df

    def _prefilter(self, sig: np.ndarray, fs: float) -> np.ndarray:
        b_notch, a_notch = signal.iirnotch(
            w0=self.config.notch_freq,
            Q=30.0,
            fs=fs,
        )
        sig = signal.filtfilt(b_notch, a_notch, sig)

        nyq = fs / 2.0
        low  = self.config.bandpass_low  / nyq
        high = self.config.bandpass_high / nyq
        b_bp, a_bp = signal.butter(
            self.config.butterworth_order,
            [low, high],
            btype="band",
        )
        sig = signal.filtfilt(b_bp, a_bp, sig)

        return sig

    def _compute_psd(
        self,
        sig: np.ndarray,
        fs: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        nperseg = int(self.config.window_seconds * fs)
        noverlap = int(nperseg * self.config.window_overlap)

        freqs, psd = signal.welch(
            sig,
            fs=fs,
            nperseg=nperseg,
            noverlap=noverlap,
            window="hann",
        )
        return freqs, psd

    @staticmethod
    def _band_power(
        freqs: np.ndarray,
        psd: np.ndarray,
        low_hz: float,
        high_hz: float,
    ) -> float:
        mask = (freqs >= low_hz) & (freqs <= high_hz)
        if not mask.any():
            return 0.0
        return float(np.trapezoid(psd[mask], freqs[mask]))

    def _compute_erd_ers(
        self,
        sig: np.ndarray,
        fs: float,
        freqs: np.ndarray,
        psd_full: np.ndarray,
    ) -> dict[str, float]:

        baseline_samples = int(self.config.baseline_seconds * fs)
        baseline_sig = sig[:baseline_samples]

        if len(baseline_sig) < 2:
            return {band: np.nan for band in BANDS}

        freqs_b, psd_b = self._compute_psd(baseline_sig, fs)

        result: dict[str, float] = {}
        for band, (lo, hi) in BANDS.items():
            r = self._band_power(freqs_b, psd_b, lo, hi)
            a = self._band_power(freqs, psd_full, lo, hi)
            result[band] = ((a - r) / r * 100) if r > 0 else np.nan

        return result

    def _print_summary(self, df: pd.DataFrame) -> None:
        """Imprime um resumo dos atributos extraídos."""
        print("\n=== BandExtractor — Atributos Espectrais ===")
        print(f"Taxa de amostragem : {self.config.sample_rate_hz} Hz")
        print(f"Canais analisados  : {[i for i in df.index if i != 'mean']}")
        print("\nPotência Relativa Média por Banda:")
        for band in BANDS:
            col = f"relpower_{band}"
            if col in df.columns:
                val = df.loc["mean", col]
                print(f"  {band.capitalize():6s}: {val:.4f}")

        tbr = df.loc["mean", "tbr"] if "tbr" in df.columns else None
        bar = df.loc["mean", "bar"] if "bar" in df.columns else None
        if tbr is not None:
            print(f"\nRazão Theta/Beta (TBR) : {tbr:.4f}  ← quanto maior, menor a concentração")
        if bar is not None:
            print(f"Razão Beta/Alfa  (BAR) : {bar:.4f}  ← quanto maior, maior o engajamento")
