# Descrição

Usaremos a arquitetura Chain of Responsabilities. Basicamente, no projeto, faremos etapas de tratamento antes de entregar o resultado final.

```python

if __name__ == "__main__":
    
    pipeline = [] ### Aqui ficará cada etapa do processo

    results = Processor()

```


# Organização de pastas

Em **Core** teremos as classes que farão cada etapa do processamento dos dados. Sempre que criar uma etapa de processamento, crie um arquivo com o nome do processamento e dentro deste sua classe para realizar o tratamento. 

# Organização das Classes

Cada classe terá que ter a seguinte estrutura

```python

class NomeClasse():
    def __init__(self):
        pass #dados de recebimento
    def process(self): # Aqui onde ocorrerá o processamento. Deverá retornar o resultado do processamento.
        pass

```

