#!/usr/bin/env python3
# coding: utf8

import os
import sys

Install_Directory = os.path.dirname(os.path.abspath(__file__))
os.chdir(Install_Directory)

sys.path.append(Install_Directory +'/src/python')
from library_loans_mailer import library_loans_mailer

if __name__ == "__main__":
    mailer = library_loans_mailer(
        preferences = Install_Directory + '/preferences.yaml',
        working_directory = Install_Directory,
        logging_directory = Install_Directory + '/log/')
    mailer.run()
