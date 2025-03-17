class CustomObject:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)
