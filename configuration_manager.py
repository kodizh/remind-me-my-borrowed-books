from yaml import load
import os
import sys
import logging

Install_Directory = os.path.dirname(os.path.abspath(__file__))
Preferences_File = Install_Directory +'/preferences.yaml'

class ConfigurationManager:
  def __init__(self):
    preferences = load( open( Preferences_File ).read() )
    # The users are those with an Active state
    self.users = [x for x in preferences['users'] if x['active']]
    self.cards = preferences['library-cards']
    self.resources = preferences['resources']
    self.session_conditions = set()

    # Load users
    for user in self.users:
      user['condition_set'] = set()
      self.processRules( user, user['sending-rules'].items() )


  def processRules( self, user, rules ):
    for name, rule in rules:
      new_rules = self.rule_modeling( name, rule )
      user['condition_set'] |= new_rules
      print( "Added rules: {}".format( new_rules ))
    print( "Full rules set: {}".format( user['condition_set'] ))


  def registerCondition(self, key, value ):
    self.session_conditions.add( (key, value) )


  def rule_modeling(self, name, rule):
    print( "Processing rule: ({}, {})".format(name, rule) )
    rules = set()

    if type( rule ) is list:
      subrules = set()
      for subrule in rule:
        rules |= self.rule_modeling(name, subrule)

    elif name == 'due-date':
      print( "  Found due-date for ({}, {})".format(name, rule))
      if rule[0] == '=':
        print( "  Found rule: ({},{})".format(name, int(rule[1])))
        rules.add( (name, int(rule[1])))
      elif rule[0] == '<':
        for i in range( 0, int(rule[1]) ):
          print( "  Found rule: ({},{})".format(name, i))
          rules.add((name, i))
      else:
        logging.error( "Rule ({}, {}) not supported".format( name, rule ))

    else:
      print( "  Found rule: ({}, {})".format(name, rule) )
      rules.add((name, rule))
    
    print( "  Returning: {}".format(rules))
    return rules


  def rule_match(self, name, rule):
    return set(self.rule_modeling(name, rule)) & self.session_conditions


  def getRecipients(self):
    recipients_list = list()
    for user in self.users:
      intersection = user['condition_set'] & self.session_conditions
      if intersection:
        recipients_list.append( (user['mail'], intersection) )
        logging.info( "Added recipient: {} <{}>".format( user['name'], user['mail'] ))
      else:
        logging.info( "Skipped recipient: {} <{}>".format( user['name'], user['mail'] ))
    return recipients_list
