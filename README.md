# Loans mailer

Automate sending email reminders for public libraries. The app has been developed for use with the library of Mordelles, France, and has not been tested with any other library yet.

The loans mailer app allows the user to :

  - Authenticate,
  - Parse the library webpage to fetch the loans list,
  - Send a reminder based on user-defined preferences.

The app is written in Python. The principle is to refresh the list of loans each time the app is started. Then the sending filters are evaluted for each user to find out if the message should be sent. And eventually the program finishes and stop.

The philosophy is to separate the reminder's recepients from the library accounts. for one configuration file, the program collects the loans from **all the library accounts** and sends the list to **all configured recipients**. Therefore, one can group the reminders for the whole family.

# Installation

To install the program just drop the files anywhere in the filesystem, and configure the app using the `preference.yaml` file.

Then invoke `library_loans_mailer.py` using either the command line, or configure any manager like `cron` to invoke the program frequently.

# Configuration

The configuration file is named `preferences.yaml`, and currently allows to configure both the users and the library-related settings. The configuration is written using the [YAML] format.

The configuration file is organised into 4 sections:

  - The `users` section defines any configuration related to the users **who want to receive the reminders**. For each user, the configuration includes the user name, his email address, and the filters for finding out when a message should be sent for him.
  - The `library-cards` section configures the library accounts credentials to allow the program to fetch the list of loans. Several cards can be configured for grouping several accounts' loans into one reminder.
  - the `resources` section allows to configures the resources related to the library, that is the required URI for authenticating and querying the list of loans.
  - The `configuration` section provides additional configuration for the program itself.


[yaml]: <http://yaml.org/>

