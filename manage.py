#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mrwf.settings")

    from django.core.management import execute_from_command_line
    sys.path.append(os.path.split(os.getcwd())[0])
    import settings

    execute_from_command_line(sys.argv)
