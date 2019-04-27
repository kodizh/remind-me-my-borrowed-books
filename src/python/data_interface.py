import abc

class DataInterface(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def add_loan(self, loans_data):
        pass

    @abc.abstractmethod
    def has_changed(self):
        pass

    @abc.abstractmethod
    def get_current_loans(self):
        pass
