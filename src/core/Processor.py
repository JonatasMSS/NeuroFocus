

class Processor:

    def __init__(self, pipeline: list = None) -> None:
        self.pipeline = pipeline or []

    def process(self, data):
        current = data
        for step in self.pipeline:
            current = step.process(current)
        return current