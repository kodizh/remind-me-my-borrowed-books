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

  def login(self, user_card):
    auth_data = dict(user_card)
    del auth_data['name']
    data = urllib.parse.urlencode(auth_data)
    req = urllib.request.Request( self.configuration.resources['uri-authform'], data.encode('ascii') )
    response = urllib.request.urlopen(req)
    self.cookie = response.headers.get('Set-Cookie')
  
  def fetch_loans(self, user_card):
    req = urllib.request.Request(self.configuration.resources['uri-bookslist'])
    req.add_header('cookie', self.cookie)
    response = urllib.request.urlopen(req)
    the_page = response.read()

    # je récupère l'encoding à la rache
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
