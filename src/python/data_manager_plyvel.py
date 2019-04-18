from data_interface import DataInterface
import plyvel
import json

class DataManagerPlyvel(DataInterface):
    def __init__(self, config_mgr):
        self.configuration_manager = config_mgr

    def __enter__(self):
        # NPH WIP # Add Configration Manager Query
        self.db = plyvel.DB(self.configuration_manager.get('configuration.leveldb-database'), create_if_missing=True)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()

    def write_book(self, book_data):
        db.put(book_data['book_id'], json.dumps(book_data))

    def write_loan(self, loan_data):
        db.put(loan_data['loan_id'], json.dumps(loan_data))
        # NPH WIP # Do we need extra indexes for facilitating querying the base?

    def lookup_book(self, book_id):
        pass

    def lookup_loans_by_dates(self, date_range):
        pass

    def run_tests(self, python_object):
        print( "Python object: {}".format(python_object) )

        # Command for serializing
        json_object = json.dumps(python_object)
        print( "Json object  : {}".format(json_object) )

        # Command for deserializing
        python_object = json.loads(json_object)
        print( "Python object: {}".format(python_object) )

        key="test-558900"
        self.db.put(key.encode('utf-8'), json_object.encode('utf-8'))
        print( "Put new entry with key={}".format(key) )

        json_object = self.db.get(key.encode('utf-8')).decode('utf-8')
        print( "Get entry with key={}\nvalue: {}".format(key, json_object) )

        self.db.delete(key.encode('utf-8'))
        print( "Removed entry with key={}".format(key) )

if __name__ == "__main__":
    with DataManagerPlyvel() as test:
        test.test_json([{"ding": 3, "dong": 7}, "foo", "bar"])
