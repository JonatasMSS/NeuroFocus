





from core.OpenBCIProcessor import OpenBCIProcessor
from core.Processor import Processor
from schemas.OpenBCIProcesorSchema import OpenBCIProcessorConfig



if __name__ == "__main__":
    
    bci_converter_config = OpenBCIProcessorConfig(
        input_path="C:\\Users\\gears\\Desktop\\NeuroFocus\\Test.txt",
        output_path="C:\\Users\\gears\\Desktop\\NeuroFocus\\Test_clean.csv"
    )
    bci_converter = OpenBCIProcessor(config=bci_converter_config)

    df = bci_converter.process() # Extraindo os dados do arquivo e convertendo para DataFrame

    pipeline = [
        # TODO: Colocar aqui os proximos passos de processamento
    ]

    processor = Processor(pipeline=pipeline)
    processor.process(df) # Processando o DataFrame com os passos definidos na pipeline