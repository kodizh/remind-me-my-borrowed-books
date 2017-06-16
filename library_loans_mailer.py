#!/usr/bin/env python3
# coding: utf8

"""
Feature wishlist :
d – Organiser et formatter les informations
d   – Par nombre de jours restant (date)
d   – Titre, auteur. \t Carte [groupe par carte]
d   – Add distinctives colours for each loan, depending on the user account
d – Add information on the recipient account (conditions, etc.)
  – Add global information and statistics:
d   – total number of current loans,
d   – number of current loans per user, 
    – number of loan per due date
d – Defining sending conditions:
d   – On defined weekdays
d   – When a threshhold is passed, e.g. number of days before return < 7
d   – When the list has changed (either absolute return date or number of items
d – Specify in the mail why it was sent, i.e. valid above reasons
d – Store the configuration and preferences in an external configuration file
d   – Link the conditions to a user and apply them to him
p – Better organise the source code
p   – Define classes, e.g FetchBooks, ManageBooks, SendBooks
p   – Find a way to better address the email content generation
  – Add internationalisation ^^

d is "done", p is "in progress"
"""


import re
import urllib.request
import urllib.parse
from lxml import etree
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from subprocess import Popen, PIPE
import datetime as dt
import locale
from operator import itemgetter, attrgetter, methodcaller
from collections import OrderedDict
import pickle

import sys
import os
import logging

from configuration_manager import ConfigurationManager
from mordelles_library_api import MordellesLibraryAPI
from xtemplate import Xtemplate

Install_Directory = os.path.dirname(os.path.abspath(__file__))
Backup_List_File = Install_Directory +'/library_list.bak'
Logging_File = Install_Directory +'/library_loans_mailer.log'

# Dictionary for displaying the days of the week (todo: use Python's date libraries)
Weekdays = {'Mon': 'lundi', 'Tue': 'mardi', 'Wed': 'mercredi', 'Thu': 'jeudi', 'Fri': 'vendredi', 'Sat': 'samedi', 'Sun': 'dimanche'}

locale_system = locale.getlocale( locale.LC_TIME )
logging.basicConfig( filename = Logging_File, level = logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s' )

config = ConfigurationManager()
library = MordellesLibraryAPI(config)
generator = Xtemplate()
loans = list()

#locale.setlocale(locale.LC_TIME, str('en_GB'))
config.registerCondition( 'weekday', dt.datetime.now().strftime( "%a" ))

#locale.setlocale(locale.LC_TIME, str('fr_FR'))

""" for library user card, connect to the library's website, fetch the loans and add
    them to the general list
"""
for card in config.cards:
    library.login(card)
    user_loans = library.fetch_loans(card)
    loans.extend( user_loans )

# sort the list by ascending remaining days
loans = sorted( loans, key=itemgetter('left_days') )


""" The loans list is saved for backup. Then, at the next run, the backup list is compared with the fresh
    one in order to find out if the loans list has changed (i.e. new books were borrowed or books were
    brought back. The whole backup is compare as is, with no specific matches.
"""

# The 'left_days' field is removed from the backup because it changes every day, and the lists would never match.
bakloans = [dict(x) for x in loans]
for loan in bakloans:
  del loan['left_days']

# Compare the backup list and the fresh list
try:
  fbackup = open( Backup_List_File, 'rb')
except IOError as ioe:
  logging.warning( "Error loading list backup. Considering the list has changed.\n\t{}".format(ioe) )
  config.registerCondition( 'list-change', True )
else:
  content = pickle.load(fbackup)
  if bakloans != content:
    config.registerCondition( 'list-change', True )
  fbackup.close()

# Write the fresh list as the new backup list
try:
  fbackup = open( Backup_List_File, 'wb' )
except IOError as ioe:
  logging.warning( "Unable to write the new backup list\n\t{}".format(ioe) )
else:
  pickle.dump(bakloans, fbackup, pickle.HIGHEST_PROTOCOL)
  fbackup.close()


""" For each user (message recipient), we write a specific email. The message is created in pure XML
    using the Xtemplate library, and then transformed into GMail compatible HTML and into PlainText
    using XSL stylesheets.
    Then the messages is sent to the recipient.
"""

content_root = None

for recipient in config.getRecipients():

  days_left = None
  for entry in loans:
    # For each change of 'remaining days', a new loan-set is created
    if days_left == None or days_left != entry['left_days'].days:
      days_left = entry['left_days'].days
      loan_set = generator.new_value( content_root, '/loan-data/loan-set' )

      generator.set_value( loan_set, './days-left', entry['left_days'].days )
      generator.set_value( loan_set, './return-date', entry['return_date'].strftime( "%A %d %B %Y" ))

    loan = generator.new_value( loan_set, './loan' )

    generator.set_value( loan, './@owner', entry['owner'] )
    generator.set_value( loan, './title', entry['title'] )
    generator.set_value( loan, './author', entry['author'] )
    
    # NPH TODO: Next instruction is mandatory, find out why
    content_root = generator.getroot(loan)

  content_root = generator.getroot(loan)

  """ Generating general statistics """
  stats = generator.set_value( content_root, './stats' )

  generator.set_value( stats, './total', len(loans) )

  for owner in list(set([x['owner'] for x in loans])):
    user = generator.new_value( stats, './user', str(len([x for x in loans if x['owner'] == owner])))
    generator.set_value( user, './@name', owner )

  content_root = generator.getroot(user)

  for days in list(set([x['left_days'].days for x in loans])):
    days_left = generator.new_value( stats, './days-left', str(len([x for x in loans if x['left_days'].days == days])))
    generator.set_value( days_left, './@days', str(days) )


  content_root = generator.getroot(days_left)

  """ Generating user rules reminder.
      It's too complicated yet. How can this be simplified?
  """
  ct_rules = generator.set_value( content_root, './sending-rules' )

  for name, rule in [x['sending-rules'] for x in config.users if x['mail'] == recipient[0]][0].items():
    if name == 'list-change' and rule == True:
      ct_rule_change = generator.new_value( ct_rules, './list-change', None )
      if config.rule_match(name, rule):
        generator.set_value( ct_rule_change, './@value', 'true' )

    elif name == 'due-date':
      if type( rule ) is not list:
        rule = [rule]
      for subrule in rule:
        ct_rule_days = generator.new_value( ct_rules, './days-left', subrule[1] )
        if subrule[0] == '<':
          generator.set_value( ct_rule_days, './@type', 'inf')
        else:
          generator.set_value( ct_rule_days, './@type', 'eq')

        matched_rule = config.rule_match(name, subrule)
        if matched_rule:
          generator.set_value( ct_rule_days, './@value', str(matched_rule.pop()[1]) )


    elif name == 'weekday':
      if type( rule ) is not list:
        rule = [rule]
      for subrule in rule:
        ct_rule_wday = generator.new_value( ct_rules, './weekday', Weekdays[subrule] )
        if config.rule_match(name, subrule):
          generator.set_value( ct_rule_wday, './@value', subrule )

    else:
      continue
  
  content_root = generator.getroot(ct_rules)

  # Write the generated XML message for futher debugging (if required)
  xml_data = open( 'generated_content.xml', 'w' )
  xml_data.write( etree.tostring( content_root, method='xml', pretty_print=True, encoding='unicode' ))
  xml_data.close()

  """ Convert the XML message to HTML and PlainText and send it to the recipient """
  msg = MIMEMultipart('alternative')
  msg.attach( MIMEText( etree.tostring( generator.transform( content_root, 'to_html.xsl' ), pretty_print=True, encoding='unicode' ), 'html' ))
  msg.attach( MIMEText( str( generator.transform( content_root, 'to_plaintext.xsl' )), 'text' ))
  msg["From"] = "[ENTER SENDER EMAIL HERE]"
  msg["To"] = recipient[0]
  msg["Subject"] = u"[Bibliothèque][X] Emprunts à la bibliothèque de Mordelles"
  p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE, universal_newlines=True)
  p.communicate(msg.as_string())
  logging.info( "Mail sent to {}".format( recipient[0] ))

#locale.setlocale( locale.LC_TIME, locale_system )
