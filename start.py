#!/usr/bin/env python3
# coding: utf8

# Python system imports
import os
import sys

import logging
import logging.handlers

# Broadening the base path in order to import remind-me's libraries
Install_Directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(Install_Directory)
sys.path.append(Install_Directory +'/src/python')

# remind-me's libraries imports
from configuration_manager import ConfigurationManager
from data_manager_plyvel import DataManagerPlyvel
from data_manager_pickle import DataManagerPickle
from mordelles_library_api import MordellesLibraryAPI
from xtemplate import Xtemplate
from loans_mailer import LoansMailer


if __name__ == "__main__":

    with ConfigurationManager(Install_Directory + '/preferences.yaml') as cm, \
        DataManagerPickle(cm) as dm,                                          \
        MordellesLibraryAPI(cm) as lib_api,                                   \
        Xtemplate() as formatter,                                             \
        LoansMailer(cm, dm, lib_api, formatter) as mailer:

        # Configure logging facility
        app_logger = logging.getLogger()
        app_logger.setLevel(0)
        # Defines logger file and max size
        handler = logging.handlers.RotatingFileHandler( cm.get('configuration.log-directory') +'/'+ cm.get("configuration.log-file"), maxBytes=1000000 )
        # Define logger format
        formatter = logging.Formatter("%(asctime)s [%(filename)25s:%(lineno)5s - %(funcName)20s()] [%(levelname)-5.5s]  %(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(0)
        # add loggerhandler to applications
        app_logger.addHandler(handler)

        logging.info( "logger started" )

        mailer.run()

#    mailer = library_loans_mailer(
#        preferences = Install_Directory + '/preferences.yaml',
#        working_directory = Install_Directory,
#        logging_directory = Install_Directory + '/log/')
