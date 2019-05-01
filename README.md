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

# Mini-roadmap

This section presents the next features that may be added soon.

## 1. ~~HTML parsing failures~~ (Done)

~~Detect when parsing the libraries CMS webpages fails. Then:~~
 - ~~add a retry mechanism,~~
 - ~~log every page that failed for later analysis~~

## 2. ~~Include `external_variables.xml` content in `preferences.yaml`~~ (Partial)

 - ~~Generate the `external_variables.xml` file at startup from the `preferences.yaml` configuration file, in order to keep all configuration in one location.~~

 - Add users that are listed in the library page but not in the preference file to the preference file; assign them with a random colour (the user can change the colour afterwards if she or he wants to).

Note: *the `external_variables.xml` file is the configuration file used by the XSL parser, while the `preferences.yaml` file is the configuration file used by the Python program.*

## 3. LevelDB

Make the DataManager based on LevelDB functional.

While the Pickle based DataManager entailed to only keep the current loans, and no history, a DataManager relying on a Database will allow some longer term management of the data. The following example are considered:
 - managing and searching the loans history,
 - showing useful statistics as well as funny ones,
 - easing to open the software to broader cases like manual loans registering.

## 4. Manual loans registering using a barcode scanner

 Add a new module that can interact with a barcode scanner for both libraries that don't have an online management system, and possibly for personal loans.

 For this implementation, the actual scanning relies on the [Barcode & QR code Keyboard](https://play.google.com/store/apps/details?id=com.nikosoft.nikokeyboard) Android application, by Nikola Antonov. The application has the advantage of embedding the barcode scanner into an Android soft keyboard, and to be able to provide barcode decoding into any input text field.

 The development consists in adding an interface between the current program and a web server on the one hand, and to develop a small webapp. The goal of the webapp is to add interaction with the user and reliability concerning the data while adding and removing loans (the reliability part is based on WebStorage/localStorage).

## 5. Add other fields to the message

 - Read the available reservations in the library page
 - Add the data in custom fields in the xml
 - Render the custom fields with the XSL for displaying in the email

## 6. Automate loans prolongation when possible

 - Automate the prolongation to avoid forgetting it
 - Define rules to define when a loan can be updated to optimise the prolongation period

## 7. Improve the rules mechanism to allow more complex rules

 - Mainly concerns the sending rules to allow an `AND` operator
 - Find out if any Python library does the job
