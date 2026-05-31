from core.BandExtractor import BandExtractor
from core.OpenBCIProcessor import OpenBCIProcessor
from core.Processor import Processor
from schemas.BandExtractorSchema import BandExtractorConfig
from schemas.OpenBCIProcesorSchema import OpenBCIProcessorConfig


if __name__ == "__main__":

    bci_converter_config = OpenBCIProcessorConfig(
        input_path="Test.txt",
        output_path="Test_clean.csv",
    )
    bci_converter = OpenBCIProcessor(config=bci_converter_config)
    clean_df = bci_converter.process(bci_converter_config)

    sample_rate = bci_converter.metadata.get("sample_rate_hz") or 250.0

    band_extractor = BandExtractor(
        config=BandExtractorConfig(
            sample_rate_hz=sample_rate,
            notch_freq=60.0,
        )
    )

    pipeline = [
        band_extractor,
    ]

    processor = Processor(pipeline=pipeline)
    features_df = processor.process(clean_df)

    print("\n=== DataFrame de Atributos Espectrais ===")
    print(features_df.to_string())