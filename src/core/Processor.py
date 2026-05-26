

class Processor():
    def __init__(self, pipeline:list[any] = None):
        self.pipeline = pipeline or []

    def process(self, data):
        output = None
        for step in self.pipeline:
            output = step.process(data)
        return output
    