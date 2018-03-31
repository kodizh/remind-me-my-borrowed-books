#!/usr/bin/env python3
# coding: utf8


import re
import urllib.request
import urllib.parse
from lxml import etree

from subprocess import Popen, PIPE
import datetime as dt
import locale
from operator import itemgetter, attrgetter, methodcaller
from collections import OrderedDict
import pickle

import sys
import os
import logging

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib

from configuration_manager import ConfigurationManager
from mordelles_library_api import MordellesLibraryAPI
from xtemplate import Xtemplate


class library_loans_mailer:
  def __init__(self):
    self.Install_Directory = os.path.dirname(os.path.abspath(__file__))

    # Dictionary for displaying the days of the week (todo: use Python's date libraries)
    self.Weekdays = {'Mon': 'lundi', 'Tue': 'mardi', 'Wed': 'mercredi', 'Thu': 'jeudi', 'Fri': 'vendredi', 'Sat': 'samedi', 'Sun': 'dimanche'}

    self.config = ConfigurationManager()

    logging.basicConfig( filename = self.Install_Directory +'/'+ self.config.get("configuration.log-file"), level = logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s' )

    self.library = MordellesLibraryAPI(self.config)
    self.generator = Xtemplate()
    self.loans = list()

    # Set the locale to a universal value and back to french — Needs more testing!
    #self.locale_system = locale.getlocale( locale.LC_TIME )
    #self.locale.setlocale(locale.LC_TIME, str('en_GB'))
    self.config.registerCondition( 'weekday', dt.datetime.now().strftime( "%a" ))

    #self.locale.setlocale(locale.LC_TIME, str('fr_FR'))

  """ for each library user account, connect to the library's website, fetch the loans and add
      them to the general list
  """
  def fetch_loans_list(self):
    for user_account in self.config.accounts:
        self.library.login(user_account)
        user_loans = self.library.analyse_loans_page()
        self.loans.extend( user_loans )

    # sort the list by ascending remaining days
    self.loans = sorted( self.loans, key=itemgetter('left_days') )


  """ The loans list is saved for backup. Then, at the next run, the backup list is compared with the fresh
      one in order to find out if the loans list has changed (i.e. new books were borrowed or books were
      brought back. The whole backup is compare as is, with no specific matches.
  """
  def backup_loans_list(self):
    # The 'left_days' field is removed from the backup because it changes every day, and the lists would never match.
    bakloans = [dict(x) for x in self.loans]
    for loan in bakloans:
      del loan['left_days']

    # Compare the backup list and the fresh list
    try:
      fbackup = open( self.Install_Directory +'/'+ self.config.get('configuration.list-backup-file'), 'rb')
    except IOError as ioe:
      logging.warning( "Error loading list backup. Considering the list has changed.\n\t{}".format(ioe) )
      self.config.registerCondition( 'list-change', True )
    else:
      content = pickle.load(fbackup)
      if bakloans != content:
        self.config.registerCondition( 'list-change', True )
      fbackup.close()

    # Write the fresh list as the new backup list
    try:
      fbackup = open( self.Install_Directory +'/'+ self.config.get('configuration.list-backup-file'), 'wb' )
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
  def generate_loans_list(self):
    content_root = None

    days_left = None
    
    if len(self.loans) == 0:
      logging.error( "No loans in list. Quitting" )
      raise Exception
    
    for entry in self.loans:
      # For each change of 'remaining days', a new loan-set is created
      if days_left == None or days_left != entry['left_days'].days:
        days_left = entry['left_days'].days
        loan_set = self.generator.new_value( content_root, '/loan-data/loan-set' )

        self.generator.set_value( loan_set, './days-left', entry['left_days'].days )
        self.generator.set_value( loan_set, './return-date', entry['return_date'].strftime( "%A %d %B %Y" ))

      loan = self.generator.new_value( loan_set, './loan' )

      self.generator.set_value( loan, './@owner', entry['owner'] )
      self.generator.set_value( loan, './title', entry['title'] )
      self.generator.set_value( loan, './author', entry['author'] )
      
      # NPH TODO: Next instruction is mandatory, find out why
      content_root = self.generator.getroot(loan)

    content_root = self.generator.getroot(loan)

    """ Generating general statistics """
    stats = self.generator.set_value( content_root, './stats' )

    self.generator.set_value( stats, './total', len(self.loans) )

    for owner in list(set([x['owner'] for x in self.loans])):
      user = self.generator.new_value( stats, './user', str(len([x for x in self.loans if x['owner'] == owner])))
      self.generator.set_value( user, './@name', owner )

    content_root = self.generator.getroot(user)

    for days in list(set([x['left_days'].days for x in self.loans])):
      days_left = self.generator.new_value( stats, './days-left', str(len([x for x in self.loans if x['left_days'].days == days])))
      self.generator.set_value( days_left, './@days', str(days) )


    content_root = self.generator.getroot(days_left)
    return content_root

  """ Generating user rules reminder.
      It's too complicated yet. How can this be simplified?
  """
  def generate_user_rules(self, recipient, xml_document):
    ct_rules = self.generator.set_value( xml_document, './sending-rules' )

    for name, rule in [x['sending-rules'] for x in self.config.users if x['mail'] == recipient[0]][0].items():
      if name == 'list-change' and rule == True:
        ct_rule_change = self.generator.new_value( ct_rules, './list-change', None )
        if self.config.rule_match(name, rule):
          self.generator.set_value( ct_rule_change, './@value', 'true' )

      elif name == 'due-date':
        if type( rule ) is not list:
          rule = [rule]
        for subrule in rule:
          ct_rule_days = self.generator.new_value( ct_rules, './days-left', subrule[1] )
          if subrule[0] == '<':
            self.generator.set_value( ct_rule_days, './@type', 'inf')
          else:
            self.generator.set_value( ct_rule_days, './@type', 'eq')

          matched_rule = self.config.rule_match(name, subrule)
          if matched_rule:
            self.generator.set_value( ct_rule_days, './@value', str(matched_rule.pop()[1]) )


      elif name == 'weekday':
        if type( rule ) is not list:
          rule = [rule]
        for subrule in rule:
          ct_rule_wday = self.generator.new_value( ct_rules, './weekday', self.Weekdays[subrule] )
          if self.config.rule_match(name, subrule):
            self.generator.set_value( ct_rule_wday, './@value', subrule )

      else:
        continue

    xml_document = self.generator.getroot(ct_rules)
    return xml_document


  def send_message(self, recipient, xml_document):

    # Write the generated XML message for futher debugging (if required)
    xml_data = open( self.Install_Directory +'/generated_content.xml', 'w' )
    xml_data.write( etree.tostring( xml_document, method='xml', pretty_print=True, encoding='unicode' ))
    xml_data.close()
    
    # Write the generated XML message for futher debugging (if required)
    xml_data = open( self.Install_Directory +'/generated_content.html', 'w' )
    xml_data.write( etree.tostring( self.generator.transform( xml_document, self.Install_Directory +'/to_html.xsl' ), pretty_print=True, encoding='unicode' ))
    xml_data.close()

    """ Convert the XML message to HTML and PlainText and send it to the recipient """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = self.config.get( "configuration.subject" )
    msg['From'] = "Biblio Rasta <{}>".format( recipient[0] )
    msg['To'] = recipient[0]
    msg.attach( MIMEText( etree.tostring( self.generator.transform( xml_document, self.Install_Directory +'/to_html.xsl' ), pretty_print=True, encoding='unicode' ), 'html' ))
    msg.attach( MIMEText( str( self.generator.transform( xml_document, self.Install_Directory +'/to_plaintext.xsl' )), 'text' ))

    try:
      server = smtplib.SMTP_SSL( "{}:465".format( self.config.get( "configuration.smtp-server" )))
      server.login(self.config.get( "configuration.smtp-login" ), self.config.get( "configuration.smtp-password" ))
      server.sendmail(msg['From'], msg['To'], msg.as_string())
      server.quit()
      logging.info( "Mail sent to {}".format( recipient[0] ))
    except Exception as e:
      logging.info( "An exception occurred while sending mail to {}\nException: ({}, {}, {})".format( recipient[0], e.args, e.errno, e.strerror ))

#self.locale.setlocale( locale.LC_TIME, locale_system )

  def run(self):
    try:
      self.fetch_loans_list()
      self.backup_loans_list()
      xml_document = self.generate_loans_list()

      for recipient in self.config.getRecipients():
        self.generate_user_rules(recipient, xml_document)
        self.send_message(recipient, xml_document)

    except Exception as e:
      # Build the message according to the exception
      xml_message = None
      error = self.generator.new_value( xml_message, '/error' )
      self.generator.set_value( error, './description', "{}".format(e) )
      xml_message = self.generator.getroot(error)

      # Add the current content of the data structure built from the library web page
      print( "Current loans list content:\n{}".format( self.library.user_loans ))
      
      # Send the message to users who have the role 'admin'
      for admin_recipient in self.config.getAdmins():
        self.send_message( admin_recipient, xml_message )

if __name__ == "__main__":
  mailer = library_loans_mailer()
  mailer.run()
