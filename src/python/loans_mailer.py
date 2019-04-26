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

import sys
import os
import logging

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib


class LoansMailer:
  def __init__(self, config_mgr, data_mgr, lib_api, formatter):
    # Dictionary for displaying the days of the week (todo: use Python's date libraries)
    self.Weekdays = {'Mon': 'lundi', 'Tue': 'mardi', 'Wed': 'mercredi', 'Thu': 'jeudi', 'Fri': 'vendredi', 'Sat': 'samedi', 'Sun': 'dimanche'}

    self.config = config_mgr

    self.library_api = lib_api
    self.data_manager = data_mgr
    self.formatter = formatter
    self.loans = list()

    # Set the locale to a universal value and back to french — Needs more testing!
    #self.locale_system = locale.getlocale( locale.LC_TIME )
    #self.locale.setlocale(locale.LC_TIME, str('en_GB'))
    self.config.registerCondition( 'weekday', dt.datetime.now().strftime( "%a" ))

    #self.locale.setlocale(locale.LC_TIME, str('fr_FR'))

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    pass


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
        loan_set = self.formatter.new_value( content_root, '/loan-data/loan-set' )

        self.formatter.set_value( loan_set, './days-left', entry['left_days'].days )
        self.formatter.set_value( loan_set, './return-date', entry['return_date'].strftime( "%A %d %B %Y" ))

      loan = self.formatter.new_value( loan_set, './loan' )

      self.formatter.set_value( loan, './@owner', entry['owner'] )
      self.formatter.set_value( loan, './title', entry['title'] )
      self.formatter.set_value( loan, './author', entry['author'] )

      # NPH TODO: Next instruction is mandatory, find out why
      content_root = self.formatter.getroot(loan)

    content_root = self.formatter.getroot(loan)

    """ Generating general statistics """
    stats = self.formatter.set_value( content_root, './stats' )

    self.formatter.set_value( stats, './total', len(self.loans) )

    for owner in list(set([x['owner'] for x in self.loans])):
      user = self.formatter.new_value( stats, './user', str(len([x for x in self.loans if x['owner'] == owner])))
      self.formatter.set_value( user, './@name', owner )

    content_root = self.formatter.getroot(user)

    for days in list(set([x['left_days'].days for x in self.loans])):
      days_left = self.formatter.new_value( stats, './days-left', str(len([x for x in self.loans if x['left_days'].days == days])))
      self.formatter.set_value( days_left, './@days', str(days) )


    content_root = self.formatter.getroot(days_left)
    return content_root

  """ Generating user rules reminder.
      It's too complicated yet. How can this be simplified?
  """
  def generate_user_rules(self, recipient, xml_document):
    ct_rules = self.formatter.set_value( xml_document, './sending-rules' )

    for name, rule in [x['sending-rules'] for x in self.config.users if x['mail'] == recipient[0]][0].items():
      if name == 'list-change' and rule == True:
        ct_rule_change = self.formatter.new_value( ct_rules, './list-change', None )
        if self.config.rule_match(name, rule):
          self.formatter.set_value( ct_rule_change, './@value', 'true' )

      elif name == 'due-date':
        if type( rule ) is not list:
          rule = [rule]
        for subrule in rule:
          ct_rule_days = self.formatter.new_value( ct_rules, './days-left', subrule[1] )
          if subrule[0] == '<':
            self.formatter.set_value( ct_rule_days, './@type', 'inf')
          else:
            self.formatter.set_value( ct_rule_days, './@type', 'eq')

          matched_rule = self.config.rule_match(name, subrule)
          if matched_rule:
            self.formatter.set_value( ct_rule_days, './@value', str(matched_rule.pop()[1]) )


      elif name == 'weekday':
        if type( rule ) is not list:
          rule = [rule]
        for subrule in rule:
          ct_rule_wday = self.formatter.new_value( ct_rules, './weekday', self.Weekdays[subrule] )
          if self.config.rule_match(name, subrule):
            self.formatter.set_value( ct_rule_wday, './@value', subrule )

      else:
        continue

    xml_document = self.formatter.getroot(ct_rules)
    return xml_document


  def send_message(self, recipient, xml_document):

    # Write the generated XML message for futher debugging (if required)
    xml_data = open( 'var/generated_content.xml', 'w' )
    xml_data.write( etree.tostring( xml_document, method='xml', pretty_print=True, encoding='unicode' ))
    xml_data.close()

    # Write the generated XML message for futher debugging (if required)
    xml_data = open( 'var/generated_content.html', 'w' )
    xml_data.write( etree.tostring( self.formatter.transform( xml_document, 'src/formatting/to_html.xsl' ), pretty_print=True, encoding='unicode' ))
    xml_data.close()

    """ Convert the XML message to HTML and PlainText and send it to the recipient """
    msg = MIMEMultipart('alternative')
    msg['Subject'] = self.config.get( "configuration.subject" )
    msg['From'] = self.config.get( "configuration.sender" )
    msg['To'] = recipient[0]
    msg.attach( MIMEText( etree.tostring( self.formatter.transform( xml_document, 'src/formatting/to_html.xsl' ), pretty_print=True, encoding='unicode' ), 'html' ))
    msg.attach( MIMEText( str( self.formatter.transform( xml_document, 'src/formatting/to_plaintext.xsl' )), 'text' ))

    try:
      server = smtplib.SMTP_SSL( "{}:465".format( self.config.get( "configuration.smtp-server" )))
      server.login(self.config.get( "configuration.smtp-login" ), self.config.get( "configuration.smtp-password" ))
      server.sendmail(msg['From'], msg['To'], msg.as_string())
      server.quit()
      logging.info( "Mail sent to {}".format( recipient[0] ))
      print( "Mail sent to {}".format( recipient[0] ))
    except Exception as e:
      logging.info( "An exception occurred while sending mail to {}\nException: ({}, {}, {})".format( recipient[0], e.args, e.errno, e.strerror ))

  def run(self):
    try:
      for user_account in self.config.accounts:
        self.library_api.load_page(user_account)
        for loan in self.library_api.get_loans():
          has_changed = self.data_manager.add_loan(loan)
          self.config.registerCondition('list-change', has_changed)
          self.loans.append(loan)

      print( "Conditions: {}".format( self.config.session_conditions))

      # Sort by days left in order to have the entries appear in that order
      # before return then generated the data-based XML document
      self.loans = sorted( self.loans, key=itemgetter('left_days') )
      xml_document = self.generate_loans_list()

      for recipient in self.config.getRecipients():
        self.generate_user_rules(recipient, xml_document)
        self.send_message(recipient, xml_document)

    except Exception as e:
      # Build the message according to the exception
      xml_message = None
      error = self.formatter.new_value( xml_message, '/error' )
      self.formatter.set_value( error, './description', "{}".format(e) )
      xml_message = self.formatter.getroot(error)

      # Add the current content of the data structure built from the library web page
      print( "Current loans list content:\n{}".format( self.data_manager.new_list ))

      # Send the message to users who have the role 'admin'
      for admin_recipient in self.config.getAdmins():
        self.send_message( admin_recipient, xml_message )
