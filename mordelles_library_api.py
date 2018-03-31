#!/usr/bin/env python3
# coding: utf8

import urllib.request
import urllib.parse
import re
from lxml import etree
import datetime as dt
import logging
import os

class MordellesLibraryAPI:
  def __init__(self, config):
    self.configuration = config
    self.cookie = None
    
    Install_Directory = os.path.dirname(os.path.abspath(__file__))
    logging.basicConfig( filename = Install_Directory +'/'+ self.configuration.get("configuration.log-file"), level = logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s' )


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

  """
  Login into the website of the library, provided his credentials. Then stores the cookie in order
  to fetch further pages.
  \param the configuration related to the user. A library account is a dictionary with the following fields:
         { 'name': the name of the user,
           'username': the username (login id) of the user,
           'password': the user's password }
  """
  def login(self, user_account):
    # First, get once the home page to initialise the session
    response = self.get_page( self.configuration.resources['uri-home'] )

    # Then log in
    auth_data = dict(user_account)
    del auth_data['name']
    auth_data.update({'send': 'Valider', 'referer': 'https://mediatheque.ville-mordelles.fr/'})
    data = urllib.parse.urlencode(auth_data).encode('ascii')
    response = self.get_page( self.configuration.resources['uri-authform'], data )


  """
  Collects and returns all current loans of a given user. The user must match the last login that
  was performed. If not, the name and the list of loans will not match.
  \param user_account the configuration related to the user. A library account is a dictionary, see the login
         method for detailed description
  \return a list of all this user's loans. A loan is a dictionary with the following entries:
          { 'owner': the name of the user that owns the loan,
            'title': the title of the book,
            'author': the author of the book,
            'library': the library name,
            'return_date': the return date as a Python date format,
            'information': additional information on the book,
            'left_days': remaining time until the book must be returned (in milliseconds) }
  """
  def analyse_loans_page(self):
    response = self.get_page( self.configuration.resources['uri-bookslist'] )
    the_page = response.read()

    # encoding is fetch roughly
    encoding = re.findall(r'<meta.*?charset=["\']*(.+?)["\'>]', str(the_page), flags=re.I)[0]
    tree = etree.HTML( the_page.decode(encoding) )
    
    """ NPH WIP LOG """
    main_page = open( "main_page.html", 'w' )
    main_page.write( the_page.decode(encoding) )
    main_page.close()

    # 1. Fetch the loans for each user
#    raw_loans_list = tree.xpath( './/div[@class="group-loans-content"]/*' )
    raw_loans_list = tree.xpath(".//div[@class='group-loans-content']/div | .//div[@class='group-loans-content']/p[@class='lead']")
    self.user_loans = list()
    current_user = None

    for raw_loan in raw_loans_list:
      if len( raw_loan.xpath( './/i[@class="fa fa-user"]' )) > 0:
        current_user = raw_loan.xpath( './/text()' )[1].strip().split(' ')[1]
        continue

      title = "Not set"
      try:
        title = " ".join(raw_loan.xpath('.//div[@class="loan-img hidden-xs hidden-sm"]/@data-title'))
      except:
        title = "Error"

      author = "Not set"
      try:
        author = " ".join(raw_loan.xpath('.//div[@class="loan-img hidden-xs hidden-sm"]/@data-author'))
      except:
        author = "Error"

      library = "Not set"
      try:
        library = " ".join(raw_loan.xpath('.//div[@class="loan-info"]/p[1]/b/text()'))
      except:
        library = "Error"

      return_date = "Not set"
      try:
        return_date = dt.datetime.strptime(" ".join(raw_loan.xpath('.//div[@class="loan-info"]/p[2]/text()')), 'Retour prévu le %d-%m-%Y') + dt.timedelta(hours=20)
      except:
        return_date = "Error"

      entry = dict({
        'owner' : current_user,
        'title' : title,
        'author' : author,
        'library' : library,
        'return_date' : return_date,
      })

      if return_date != "Error":
        entry['left_days'] = entry['return_date'] - dt.datetime.now()
      else:
        entry['left_days'] = dt.datetime.now() - dt.datetime.now()
      self.configuration.registerCondition( 'due-date', entry['left_days'].days )

      self.user_loans.append(entry)

    return self.user_loans
