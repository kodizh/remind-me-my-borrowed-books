import abc

class DataInterface(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_loan(self, loans_data):
        pass
