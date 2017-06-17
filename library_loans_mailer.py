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
  – Better organise the source code
    – Define classes, e.g FetchBooks, ManageBooks, SendBooks
    – Find a way to better address the email content generation
  – Add internationalisation ^^
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
#import xtemplate

Install_Directory = os.path.dirname(os.path.abspath(__file__))
Backup_List_File = Install_Directory +'/library_list.bak'
Logging_File = Install_Directory +'/library_loans_mailer.log'
Weekdays = {'Mon': 'lundi', 'Tue': 'mardi', 'Wed': 'mercredi', 'Thu': 'jeudi', 'Fri': 'vendredi', 'Sat': 'samedi', 'Sun': 'dimanche'}

locale_system = locale.getlocale( locale.LC_TIME )
logging.basicConfig( filename = Logging_File, level = logging.DEBUG, format='%(asctime)s [%(levelname)s] %(message)s' )

config = ConfigurationManager()
loans = list()

#locale.setlocale(locale.LC_TIME, str('en_GB'))
config.registerCondition( 'weekday', dt.datetime.now().strftime( "%a" ))

#locale.setlocale(locale.LC_TIME, str('fr_FR'))

for card in config.cards:
  auth_data = dict(card)
  del auth_data['name']
  data = urllib.parse.urlencode(auth_data)
  req = urllib.request.Request(config.resources['uri-authform'], data.encode('ascii'))
  response = urllib.request.urlopen(req)
  cookie = response.headers.get('Set-Cookie')

  req = urllib.request.Request(config.resources['uri-bookslist'])
  req.add_header('cookie', cookie)
  response = urllib.request.urlopen(req)
  the_page = response.read()

  # je récupère l'encoding à la rache
  encoding = re.findall(r'<meta.*?charset=["\']*(.+?)["\'>]', str(the_page), flags=re.I)[0]

  tree = etree.HTML( the_page.decode(encoding) )
  entries = tree.xpath( '//table[@class=\'tablesorter loans\']/tbody/tr' )

  for element in entries:
    """
    entry = OrderedDict()
    entry['owner']        = card['name']
    entry['title']        = " ".join(element.xpath("./td[2]/a/text()"))
    entry['author']       = " ".join(element.xpath("./td[3]/text()"))
    entry['library']      = " ".join(element.xpath("./td[4]/text()"))
    entry['return_date']  = dt.datetime.strptime(" ".join(element.xpath("./td[5]/text()")), '%d/%m/%Y ') + dt.timedelta(hours=20)
    entry['informations'] = " ".join(element.xpath("./td[6]/text()"))
    """

    entry = dict({
      'owner' : card['name'],
      'title' : " ".join(element.xpath("./td[3]/a/text()")),
      'author' : " ".join(element.xpath("./td[4]/text()")),
      'library' : " ".join(element.xpath("./td[5]/text()")),
      'return_date' : dt.datetime.strptime(" ".join(element.xpath("./td[6]/text()")), '%d/%m/%Y ') + dt.timedelta(hours=20),
      'informations' : " ".join(element.xpath("./td[7]/text()"))
    })
    entry['left_days'] = entry['return_date'] - dt.datetime.now()
    loans.append( entry )
    config.registerCondition( 'due-date', entry['left_days'].days )

loans = sorted( loans, key=itemgetter('left_days') )

# Copy the list and remove the left_days that are changing every seconds
bakloans = [dict(x) for x in loans]
for loan in bakloans:
  del loan['left_days']

# Compare the backup and the new list
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

# Write the new list as backup
try:
  fbackup = open( Backup_List_File, 'wb' )
except IOError as ioe:
  logging.warning( "Unable to write the new backup list\n\t{}".format(ioe) )
else:
  pickle.dump(bakloans, fbackup, pickle.HIGHEST_PROTOCOL)
  fbackup.close()

# Writing the emails and sending them to the eligible recipients
for recipient in config.getRecipients():
  htmloutput = "<html><head><meta charset=\"UTF-8\"/></head><body>"
  htmloutput = htmloutput +"<div class=\"loans\">"
  textoutput = ""

  htmloutput = htmloutput +"<div>Pourquoi reçois-je ce message ?</div><ul>"
  textoutput = textoutput +"Pourquoi reçois-je ce message ?"
  for name, rule in recipient[1]:
    if name == 'due-date':
      htmloutput = htmloutput +"<li>Des livres sont à rendre dans {} jour(s)</li>".format(rule)
      textoutput = textoutput +" * Des livres sont à rendre dans {}".format(rule)
    elif name == 'weekday':
      day = Weekdays[rule]
      htmloutput = htmloutput +"<li>Nous sommes {}, et {} est le jour du mémo !</li>".format(day, day)
      textoutput = textoutput +" * Nous sommes {}, et {} est le jour du mémo !".format(day, day)
    elif name == 'list-change':
      htmloutput = htmloutput +"<li>La liste des livres a changé depuis hier</li>"
      textoutput = textoutput +" * La liste des livres a changé depuis hier"
  htmloutput = htmloutput +"</ul><div style=\"display: inline-block;\">"

  current_days_left = -1
  for entry in loans:
    if current_days_left != entry['left_days'].days:
      if current_days_left != -1:
        htmloutput = htmloutput + "</ul></div>"
      current_days_left = entry['left_days'].days

      htmloutput = htmloutput +"<div><b>{} jours restants</b> (retour le {}) <ul>".format( current_days_left, entry['return_date'].strftime( "%A %d %B %Y" ))
      textoutput = textoutput +"{} jours restants (retour le {})\n\n".format( current_days_left, entry['return_date'].strftime( "%A %d %B %Y" ))
      last_name = ""

    htmloutput = htmloutput + '<li class=\"book\" style=\"margin-left: 1em; padding-right: 2px;'
    if entry['owner'] == 'Aziliz':
      htmloutput = htmloutput + ' background: linear-gradient(to right, rgba(255,0,0,0) 99%, #3399ff);'
    elif entry['owner'] == 'Nicolas':
      htmloutput = htmloutput + ' background: linear-gradient(to right, rgba(255,0,0,0) 99%, #00cc66);'
    elif entry['owner'] == 'Alice':
      htmloutput = htmloutput + ' background: linear-gradient(to right, rgba(255,0,0,0) 99%, #ff5050);'
    htmloutput = htmloutput +'\">'
    htmloutput = htmloutput + "<b>{}</b>, <i>{}</i>".format( entry['title'], entry['author'] )
    if entry['owner'] != last_name:
      htmloutput = htmloutput +"<div style=\"float: right; clear: right; margin-left: 2em; color: grey; font-size: small; font-style: italic;\">{}</div>".format( entry['owner'] )
      last_name = entry['owner']
    htmloutput = htmloutput + "</li>"
    textoutput = textoutput + "  — "+ entry['title'] +", "+ entry['author'] +" ("+ entry['owner'] +")\n"
#  if current_days_left != -1:
#    htmloutput = htmloutput +"</ul></div>"
    textoutput = textoutput +"\n"
  htmloutput = htmloutput + "</div>"

  ## Generating some general statistics
  htmloutput = htmloutput +"<div style=\"color: grey; font-size: 75%; border: 1px solid lightgrey; margin-bottom: 1em;\"><div style=\"background: darkgrey; color: white;\">Statistiques</div>"
  htmloutput = htmloutput +"<div style=\"display: inline-block; margin-left: 2em; vertical-align: top;\">Nombre de livres empruntés :<ul>"
  htmloutput = htmloutput +"<li style=\"font-weight: bold\">Total des livres : {}</li>".format( len(loans) )
  for owner in list(set([x['owner'] for x in loans])):
    htmloutput = htmloutput +"<li style=\"font-weight: bold\">Sur la carte d'{} : {}</li>".format(owner, str(len([x for x in loans if x['owner'] == owner])))
  htmloutput = htmloutput +"</ul></div>"
  htmloutput = htmloutput +"<div style=\"display: inline-block; margin-left: 2em; vertical-align: top;\">Nombre de livres à rendre :<ul>"
  for days in list(set([x['left_days'].days for x in loans])):
    htmloutput = htmloutput +"<li>dans {} jours : {}</li>".format(days, str(len([x for x in loans if x['left_days'].days == days])))
  htmloutput = htmloutput +"</ul></div></div>"

  ## Generating user rules reminder
  htmloutput = htmloutput +"<div style=\"color: grey; font-size: 75%; border: 1px solid lightgrey;\"><div style=\"background: darkgrey; color: white;\">Mes conditions d'envoi</div><ul>"
  for name, rule in [x['sending-rules'] for x in config.users if x['mail'] == recipient[0]][0].items():
    if name == 'list-change' and rule == True:
      htmloutput = htmloutput +"<li>la liste des livres a changé depuis le dernier envoi</li>"
    if name == 'due-date':
      htmloutput = htmloutput +"<li>des livres sont à rendre :<ul>"
      if type( rule ) is not list:
        rule = [rule]
      for subrule in rule:
        if subrule[0] == '<':
          htmloutput = htmloutput +"<li>dans moins de {} jours.</li>".format( subrule[1] )
        else:
          htmloutput = htmloutput +"<li>dans exactement {} jours.</li>".format( subrule[1] )
      htmloutput = htmloutput +"</ul></li>"
    if name == 'weekday':
      htmloutput = htmloutput +"<li>Chaque "
      if type( rule ) is not list:
        rule = [rule]
      for subrule in rule:
        htmloutput = htmloutput + Weekdays[subrule]+ ", "
      htmloutput = htmloutput +"</li>"
  htmloutput = htmloutput +"</ul></div>"

  htmloutput = htmloutput + "</body></html>"

  msg = MIMEMultipart('alternative')
  msg.attach( MIMEText( htmloutput, 'html' ))
  msg.attach( MIMEText( textoutput, 'text' ))
  msg["From"] = "[ENTER SENDER EMAIL HERE]"
  msg["To"] = recipient[0]
  msg["Subject"] = u"[Bibliothèque] Emprunts à la bibliothèque de Mordelles"
  p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE, universal_newlines=True)
  p.communicate(msg.as_string())
  logging.info( "Mail sent to {}".format( recipient[0] ))

#locale.setlocale( locale.LC_TIME, locale_system )
