#!/bin/sh
export PYTHONPATH=.:$PYTHONPATH
django-admin.py test tests --settings=syndication.tests.settings
