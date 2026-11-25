"""Beget Passenger entry point; paths follow the repository location."""

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / 'sphere'))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.production'

from config.wsgi import application  # noqa: E402, F401
