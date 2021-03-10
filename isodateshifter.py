#!/usr/bin/env python3
# -*- coding: utf-8; mode: python; -*-
PROG_VERSION = u"Time-stamp: <2021-03-10 20:01:50 vk>"
PROG_VERSION_DATE = PROG_VERSION[13:23]

import time
INVOCATION_TIME = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
import sys
import os
PROG_NAME = os.path.basename(sys.argv[0])

# TODO:
# - fix parts marked with «FIXXME»
# -

# ===================================================================== ##
#  You might not want to modify anything below this line if you do not  ##
#  know, what you are doing :-)                                         ##
# ===================================================================== ##

import re
import argparse   # for handling command line arguments
import datetime
import logging
import codecs
from datetime import timedelta

# global variable because I can't use any parameter for the
# replacement function of re.sunb()
# https://docs.python.org/3/library/re.html#re.sub
difference_days = 0

DAY_RAW_REGEX = r'(?P<year>\d{4,4})-(?P<month>[01]\d)-(?P<day>[0123]\d)'
DATE_REGEX = re.compile(DAY_RAW_REGEX)
REFERENCEDAY_REGEX = re.compile(r'.*' + DAY_RAW_REGEX + r'=referenceday.*')

DESCRIPTION = """This script shifts ISO dates within a file relative to a reference day.

You need a string like "2021-03-07=referenceday" anywhere within the file, typically as a comment.

When you call this script with the parameter "-r 2021-03-09" and a file name, this file name then
gets processed and all ISO datestamps found will be shifted two days to the future."""

EPILOG = """
:copyright: (c) by Karl Voit <tools@Karl-Voit.at>
:license: GPL v3 or any later version
:URL: https://github.com/novoid/isodateshifter
:bugreports: via github or <tools@Karl-Voit.at>
:version: """ + PROG_VERSION_DATE + "\n·\n"

parser = argparse.ArgumentParser(prog=sys.argv[0],
                                 # keep line breaks in EPILOG and such
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=EPILOG,
                                 description=DESCRIPTION)

parser.add_argument(dest="filename", metavar='FILE', nargs=1, help='the file to modify')

parser.add_argument("-r", "--referenceday",
                    dest="referenceday",
                    nargs=1,
                    type=str,
                    metavar='"ISO-day of reference"',
                    required=True,
                    help="This is the reference day which is compared to the old reference day stored within the file")

parser.add_argument("-v", "--verbose",
                    dest="verbose", action="store_true",
                    help="Enable verbose mode")

parser.add_argument("-q", "--quiet",
                    dest="quiet", action="store_true",
                    help="Enable quiet mode")

parser.add_argument("--version",
                    dest="version", action="store_true",
                    help="Display version and exit")

options = parser.parse_args()

def handle_logging():
    """Log handling and configuration"""

    if options.verbose:
        FORMAT = "%(levelname)-8s %(asctime)-15s %(message)s"
        logging.basicConfig(level=logging.DEBUG, format=FORMAT)
    elif options.quiet:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.ERROR, format=FORMAT)
    else:
        FORMAT = "%(levelname)-8s %(message)s"
        logging.basicConfig(level=logging.INFO, format=FORMAT)

def error_exit(errorcode, text):
    """exits with return value of errorcode and prints to stderr"""

    sys.stdout.flush()
    logging.error(text)
    #input('Press <Enter> to finish with return value %i ...' % errorcode).strip()
    sys.exit(errorcode)

def replace_match(matchobj):
    """
    Used within re.sub() for replacing a matching string with a different.

    @type  matchobj: match object
    @param matchobj: the date-string to replace
    @rtype:   string
    @return:  the changed date-string
    """

    current_reference_datetime = datetime.datetime(
        int(matchobj.group('year')),
        int(matchobj.group('month')),
        int(matchobj.group('day')), 0, 0, 0)

    return (current_reference_datetime +
            datetime.timedelta(days=difference_days)).strftime('%Y-%m-%d')


def main():
    """Main function"""

    if options.version:
        print(os.path.basename(sys.argv[0]) + " version " + PROG_VERSION_DATE)
        sys.exit(0)

    handle_logging()

    filename = options.filename[0]

    if not os.path.isfile(filename):
        error_exit(2, "File is not an existing one.")

    cli_referenceday = re.match(DATE_REGEX, options.referenceday[0])
    logging.debug('cli_referenceday = ' + cli_referenceday.group('year') + '-' + \
                  cli_referenceday.group('month') + '-' + cli_referenceday.group('day'))

    if not cli_referenceday:
        error_exit(3, "The given date is not in the ISO format YYYY-MM-DD.")

    logging.debug('reading file for finding the line with the referenceday ...')
    file_referenceday = None
    with codecs.open(filename, 'r', encoding='utf-8') as input:
        for line in input:
            candidate_match = re.match(REFERENCEDAY_REGEX, line)
            if candidate_match:
                file_referenceday = candidate_match

    if not file_referenceday:
        error_exit(4, "No referenceday found in the file.")
    else:
        logging.debug('file_referenceday = ' + file_referenceday.group('year') + '-' + \
                      file_referenceday.group('month') + '-' + file_referenceday.group('day'))


    file_reference_datetime = datetime.datetime(int(file_referenceday.group('year')),
                                                int(file_referenceday.group('month')),
                                                int(file_referenceday.group('day')), 0, 0, 0)
    cli_reference_datetime = datetime.datetime(int(cli_referenceday.group('year')),
                                               int(cli_referenceday.group('month')),
                                               int(cli_referenceday.group('day')), 0, 0, 0)
    global difference_days
    difference_days = (cli_reference_datetime - file_reference_datetime).days
    logging.debug('difference in days between cli_referenceday and file_referenceday: ' + str(difference_days))

    logging.debug('reading file again for processing date-stamps ...')
    with codecs.open(filename, 'r', encoding='utf-8') as input:
        for line in input:
            print(re.subn(DAY_RAW_REGEX, replace_match, line)[0][:-1])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:

        logging.info("Received KeyboardInterrupt")

# END OF FILE #################################################################
