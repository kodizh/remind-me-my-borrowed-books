#!/usr/bin/env python3
# coding: utf8

import urllib.request
import urllib.parse
import re
from lxml import etree
import datetime as dt
import logging
import os
from pathlib import Path
import time

class MordellesLibraryAPI:
  def __init__(self, config):
    self.configuration = config
    self.cookie = None

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    pass

  """
  """
  def get_page(self, uri, auth_data = None):
    logging.info( "Connecting to {}".format(uri) )
    request = urllib.request.Request( uri, auth_data )

    if self.cookie:
      logging.info( "Using cookie: {}".format(self.cookie) )
      request.add_header( 'Cookie', self.cookie )
    else:
      logging.info( "Not using cookie" )

    response = urllib.request.urlopen(request)

    if not self.cookie:
      self.cookie = response.headers.get('Set-Cookie')
      logging.info( "Cookie stored: {}".format(self.cookie) )

    return response


  def get_field(self, loan_as_html, field_data):
    field_name = field_data[0]
    xpath_expr = field_data[1]
    try:
      value = " ".join(loan_as_html.xpath(xpath_expr))
      if len(field_data) == 3:
        value = field_data[2](value)
      return { field_name : value }
    except:
      self.dbg_error.append(field_name)
      return { field_name : "Error" }


  def dump_page(self, plaintext_page, filename, reset=False):
    dump_dir = self.configuration.get('configuration.log-directory')
    if reset:
      for file in Path(dump_dir).glob(filename +"*.html"):
        file.unlink()
      self.dump_order = 1

    if plaintext_page:
      file = dump_dir +'/'+ filename +'_'+ str(self.dump_order) +".html"
      with open( file, "w+" ) as dump_file:
        dump_file.write( plaintext_page )
        dump_file.close()
      logging.info( "Dumped page to {}".format(file) )
      self.dump_order = self.dump_order + 1


  """
  Login into the website of the library, provided his credentials. Then stores the cookie in order
  to fetch further pages.
  \param the configuration related to the user. A library account is a dictionary with the following fields:
         { 'name': the name of the user,
           'username': the username (login id) of the user,
           'password': the user's password }
  """
  def load_page(self, user_account):
    if self.configuration.get('debug.set-library-offline'):
      with open( "var/main_page.html", 'r' ) as main_page:
        plaintext_page = main_page.read()
        self.page_tree = etree.HTML( plaintext_page )
      return

    self.dump_page(None, 'main_page', True)

    while True:
      # First, get once the home page to initialise the session
      response = self.get_page( self.configuration.get('resources-mordelles.uri-home') )
      # encoding is fetch roughly
      encoding = re.findall(r'<meta.*?charset=["\']*(.+?)["\'>]', str(response.read()), flags=re.I)[0]

      self.dump_page(response.read().decode(encoding), 'main_page')

      time.sleep(1)

      # Then log in
      auth_data = dict(user_account)
      del auth_data['name']
      auth_data.update({'send': 'Valider', 'referer': 'https://mediatheque.ville-mordelles.fr/'})
      data = urllib.parse.urlencode(auth_data).encode('ascii')
      response = self.get_page( self.configuration.get('resources-mordelles.uri-authform'), data )
      self.dump_page(response.read().decode(encoding), 'main_page')

      time.sleep(1)

      response = self.get_page( self.configuration.get('resources-mordelles.uri-bookslist') )
      plaintext_page = response.read().decode(encoding)
      self.dump_page(plaintext_page, 'main_page')

      self.page_tree = etree.HTML( plaintext_page )

      # test if the page contains a loans list
      is_loan_page = self.page_tree.xpath( ".//div[contains(@class, 'catalog-page')]" )
      if not is_loan_page:
        logging.error("The loaded page is not a catalog page. Retrying...")
        time.sleep(1)
        continue
      else:
        break


  def format_date(self, date_string):
    date_string = re.search('[0-9]+-[0-9]+-[0-9]+', date_string).group(0)
    return dt.datetime.strptime(date_string, '%d-%m-%Y') + dt.timedelta(hours=20)


  def format_book_id(self,book_url):
    return book_url.split('=')[1]


  """
  Collects and returns all current loans of a given user. The user must match the last login that
  was performed. If not, the name and the list of loans will not match.
  \param user_account the configuration related to the user. A library account is a dictionary, see the login
         method for detailed description
  \return a list of all this user's loans. A loan is a dictionary with the following entries:
          { 'owner': the name of the user that owns the loan,
            'id': the unique ID identifying the book in the library,
            'isbn': the ISBN identifier of the book,
            'title': the title of the book,
            'author': the author of the book,
            'library': the library name,
            'return_date': the return date as a Python date format,
            'information': additional information on the book,
            'left_days': remaining time until the book must be returned (in milliseconds) }
  """
  def get_loans(self):
    raw_loans_list = self.page_tree.xpath(".//div[@class='group-loans-content']/*")
    logging.debug( 'RAW loans list size: {}'.format(len(raw_loans_list)))

    current_user = None

    for raw_loan in raw_loans_list:
      self.dbg_error = list()

      if len( raw_loan.xpath( './/i[@class="fa fa-user"]' )) > 0:
        current_user = raw_loan.xpath( './/text()' )[1].strip().split(' ')[1]
        logging.debug( 'Process loans for user {}'.format(current_user) )
        continue

      fields_list= [
        [ 'id', './/div[@class="loan-book"]//a/@href', self.format_book_id ],
        [ 'isbn', './/div[@class="loan-img hidden-xs hidden-sm"]/@data-ean' ],
        [ 'title', './/div[@class="loan-img hidden-xs hidden-sm"]/@data-title' ],
        [ 'author', './/div[@class="loan-img hidden-xs hidden-sm"]/@data-author' ],
        [ 'library', './/div[@class="loan-info"]/p[1]/b/text()' ],
        [ 'loan_date', './/div[@class="loan-info"]/p[1]/text()', self.format_date ],
        [ 'return_date', './/div[@class="loan-info"]/p[2]/text()', self.format_date ]
      ]

      entry = dict()
      for field in fields_list:
        entry.update( self.get_field( raw_loan, field ))
      entry.update({ 'owner' : current_user })

      if len(self.dbg_error) > 0 :
        logging.debug( 'An error was raised while analysing fields: {}\nwhile processing loans {}'.format(self.dbg_error, entry) )

      if entry['return_date'] != "Error":
        entry['left_days'] = entry['return_date'] - dt.datetime.now()
      else:
        entry['left_days'] = dt.datetime.now() - dt.datetime.now()
      self.configuration.registerCondition( 'due-date', entry['left_days'].days )

      yield entry
