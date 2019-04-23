from data_interface import DataInterface
import pickle

"""
  With DataManagerPickle, the loans are aggragated into a ordinary Python list,
  and then saved for backup. At the next run, the backup list is compared with
  the fresh one in order to find out if the loans list has changed (i.e. new books
  were borrowed or books were brought back.
  The list is dumped as a Pickle object onto the disk, and loaded at module startup.
  Specific comparisons on objects were lately introduced: two objects are considered
  identical if their ISBN and loan dates are identical.
"""
class DataManagerPickle(DataInterface):
  def __init__(self, config_mgr):
    self.configuration_manager = config_mgr
    self.backup_file = self.configuration_manager.get('configuration.list-backup-file')
    self.new_list = list()


  def __enter__(self):
    print( "Trying to open {}".format(self.backup_file))
    with open(self.backup_file , 'rb') as fbackup:
      self.existing_list = pickle.load(fbackup)
    return self


  def __exit__(self, exc_type, exc_value, traceback):
    with open(self.backup_file , 'wb') as fbackup:
      pickle.dump(self.new_list, fbackup, pickle.HIGHEST_PROTOCOL)


  def get_loan_key(self, item):
      return str( item['loan_date'].timestamp() ) + item['isbn']


  def add_loan(self, loan_data ):
    self.new_list.append(loan_data)

    if len(self.new_list) != len(self.existing_list):
      return True

    # Sorting the loans is required when dealing with a static pickle
    # object to compare changes with the previous sync
    self.new_list = sorted( self.new_list, key=self.get_loan_key )

    for i in range(0, len(self.new_list)):
      enew = self.new_list[i]
      eexist = self.existing_list[i]

      if enew['isbn'] != eexist['isbn'] or enew['loan_date'] != eexist['loan_date']:
        print( "False comparison\n\t{}\n\t\t** vs. **n\t{}".format(enew, eexist) )
        return True

    return False
