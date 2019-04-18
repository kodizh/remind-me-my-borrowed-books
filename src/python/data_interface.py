import abc

class DataInterface(object, metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def write_book(self, book_data):
        pass

    @abc.abstractmethod
    def write_loan(self, loan_data):
        pass

    @abc.abstractmethod
    def lookup_book(self, isbn):
        pass

    @abc.abstractmethod
    def lookup_loans_by_dates(self, date_range):
        pass
