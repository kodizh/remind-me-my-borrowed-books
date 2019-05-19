from data_interface import DataInterface
import pickle
import logging

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
    self.list_has_changed = False


  def __enter__(self):
    logging.info( "Opening Pickle file {}".format(self.backup_file))
    try:
      with open(self.backup_file , 'rb') as fbackup:
        self.existing_list = pickle.load(fbackup)
    except FileNotFoundError:
      logging.warning("Pickle file does not exists. Using empty list.")
      self.existing_list = list()
    return self


  def __exit__(self, exc_type, exc_value, traceback):
    # the list is not saved if it is empty
    if not self.new_list:
        return

    with open(self.backup_file , 'wb+') as fbackup:
      pickle.dump(self.new_list, fbackup, pickle.HIGHEST_PROTOCOL)


  def get_loan_key(self, item):
      return str( item['loan_date'].timestamp() ) + item['isbn']


  def add_loan(self, loan_data ):
    self.new_list.append(loan_data)

    if len(self.new_list) != len(self.existing_list):
      self.list_has_changed = True
      return

    # Sorting the loans is required when dealing with a static pickle
    # object to compare changes with the previous sync
    self.new_list = sorted( self.new_list, key=self.get_loan_key )

    for i in range(0, len(self.new_list)):
      el_new = self.new_list[i]
      el_exist = self.existing_list[i]

      if el_new['isbn'] != el_exist['isbn'] or el_new['loan_date'] != el_exist['loan_date']:
        print( "False comparison\n\t{}\n\t\t** vs. **n\t{}".format(el_new, el_exist) )
        self.list_has_changed = True

    self.list_has_changed = False


  def has_changed(self):
      return self.list_has_changed


  def get_current_loans(self):
      return self.new_list
