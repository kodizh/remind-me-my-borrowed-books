#!/usr/bin/env python3
# coding: utf8

import urllib.request
import urllib.parse
import re
from lxml import etree
import datetime as dt

class MordellesLibraryAPI:
  def __init__(self, config):
    self.configuration = config

  """
  Login into the website of the library, provided his credentials. Then stores the cookie in order
  to fetch further pages.
  \param the configuration related to the user. A library card is a dictionary with the following fields:
         { 'name': the name of the user,
           'username': the username (login id) of the user,
           'password': the user's password }
  """
  def login(self, user_card):
    auth_data = dict(user_card)
    del auth_data['name']
    data = urllib.parse.urlencode(auth_data)
    req = urllib.request.Request( self.configuration.resources['uri-authform'], data.encode('ascii') )
    response = urllib.request.urlopen(req)
    self.cookie = response.headers.get('Set-Cookie')
  
  """
  Collects and returns all current loans of a given user. The user must match the last login that
  was performed. If not, the name and the list of loans will not match.
  \param user_card the configuration related to the user. A library card is a dictionary, see the login
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
  def fetch_loans(self, user_card):
    req = urllib.request.Request(self.configuration.resources['uri-bookslist'])
    req.add_header('cookie', self.cookie)
    response = urllib.request.urlopen(req)
    the_page = response.read()

    # encoding is fetch roughly
    encoding = re.findall(r'<meta.*?charset=["\']*(.+?)["\'>]', str(the_page), flags=re.I)[0]

    tree = etree.HTML( the_page.decode(encoding) )
    entries = tree.xpath( '//table[@class=\'tablesorter loans\']/tbody/tr' )

    user_loans = list()

    for element in entries:
      entry = dict({
        'owner' : user_card['name'],
        'title' : " ".join(element.xpath("./td[3]/a/text()")),
        'author' : " ".join(element.xpath("./td[4]/a/text()")),
        'library' : " ".join(element.xpath("./td[5]/text()")),
        'return_date' : dt.datetime.strptime(" ".join(element.xpath("./td[6]/text()")), '%d/%m/%Y ') + dt.timedelta(hours=20),
        'informations' : " ".join(element.xpath("./td[7]/text()"))
        })
      entry['left_days'] = entry['return_date'] - dt.datetime.now()

      user_loans.append(entry)
      self.configuration.registerCondition( 'due-date', entry['left_days'].days )

    return user_loans
