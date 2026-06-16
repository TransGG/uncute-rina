class CustomObject:
    def __init__(self, **kwargs) -> None:
        for k, v in kwargs.items():
            self.__setattr__(k, v)
