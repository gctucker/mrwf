What is the MRWF-CAMS?
======================

The **C**\ omputer **A**\ ided **M**\ anagement **S**\ ystem is a
database-driven web-based tool to help manage events, the first of which being
the *Mill Road Winter Fair* in Cambridge, UK (**MRWF**, here simply referred to
as the **Fair**).

Its first purpose is to allow a set of **organizers** to share contact details
of all the fair's participants in an **address book**, i.e. organisations,
volunteers, members of the committee etc.  Each organizers has a user name and
a password and is granted a set of rights to work on some parts of the
database.

People can also apply via **public online forms** to take part in the fair, for
example if they want to have a stall or publish an advert in the fair's
programme.  In this case, no user account is required but people have to enter
their names and e-mail addresses.  Organizers can then review the applications,
edit the programme and generate invoices.

There is also an API to extract the public programme information (HTTP/XML
interface) so websites and smartphone applications can produce it in any
electronic format; see the `Mill Road Winter Fair website`_ for example.

This is powered by `Django`_, which is basically an awesome software framework
to create database-driven websites written in `Python`_.

.. _Mill Road Winter Fair website: http://www.millroadwinterfair.org/events/
.. _Django: https://www.djangoproject.com/
.. _Python: http://python.org/


Prerequisites
=============

These instructions are to set-up a self-contained Django development
environment, which is slightly different from hosting it on a web server.  The
main difference being that SQLite is easier to use for development, but is less
performent than MySQL or PostgreSQL which are preferred on the public web
version.  The Django framework provides an abstraction layer so the code
remains the same regardless of the SQL database flavour in use.  Also, static
files are handeled with the Django development server here whereas Apache would
typically be used on the production web server.

It is also worth mentioning that a separate set of fictional data is used for
development purposes, so no privacy issues get in the way.  It helps making a
clear difference when switching between the development and production
versions.  The development data can be initialised via `Django fixtures`_.

.. _Django fixtures: https://docs.djangoproject.com/en/dev/howto/initial-data/

.. note::

   It is recommended to use a **Linux** system for many practical reasons.  If
   you haven't got Linux installed on your computer, an easy alternative is to
   run it in a **virtual machine**.  For example, you can download and install
   `Virtual Box`_ and `Ubuntu`_.

   .. _Virtual Box: https://www.virtualbox.org/wiki/Downloads
   .. _Ubuntu: http://www.ubuntu.com/download/desktop

You will need these things installed on your Linux system:

* `Python v2.7`_ recommended, v2.6 should also work.  Run ``python -V`` to
  check what you have already installed.
* `pysqlite`_, a Python interface to SQLite 3.  If you can run ``python -c
  "import pysqlite2"`` without an error message then you already have it.
* `Django v1.4`_, the latest v1.5 should also work.

.. _Python v2.7: http://python.org/download/releases/2.7.3/
.. _pysqlite: https://pypi.python.org/pypi/pysqlite
.. _Django v1.4: https://www.djangoproject.com/download/1.4.5/tarball/

.. warning::

   You **must read** the `Getting Started`_ page and especially the `Quick
   install guide`_ and `database setup`_ pages on the Django documentation
   website.

.. _Getting started: https://docs.djangoproject.com/en/dev/intro/
.. _Quick install guide: https://docs.djangoproject.com/en/dev/intro/install/
.. _database setup: https://docs.djangoproject.com/en/dev/intro/tutorial01/#database-setup


Initial Django set-up
=====================

Clone the `cams`_ and `mrwf`_ repositories, then create a file with your local
settings based on the boilerplate::

   cp local_settings_sample.py local_settings.py

.. _cams: https://github.com/gctucker/cams.git
.. _mrwf: https://github.com/gctucker/mrwf.git

.. note::

   This ``mrwf`` repository repends on the ``cams`` repository.  The principle
   is to keep things specific to the MRWF in ``mrwf`` and out of ``cams`` which
   can be reused for other events.  It also makes the design much neater.  In
   fact the ``mrwf`` now has many features that could be migrated into ``cams``
   with some little extra effort.

In your ``local_settings.py`` which is imported by the main ``settings.py``,
edit the ``BASE_DIR`` with the path to where you cloned the repositories.  Now
run this command to initialise the database::

    python manage.py syncdb

Answer 'yes' to create a ``superuser`` account, with the name and password of
your choice as well as your e-mail address.

You should now all be set to run the development server::

    python manage.py runserver

Then in your favourite browser, open this URL: `http://localhost:8000
<http://localhost:8000>`_.  Enter your user name and password, this should
work!
