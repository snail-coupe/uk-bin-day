''' Moduke to look up bin collection dates in the UK '''

from __future__ import annotations
from datetime import datetime

import urllib.request
import glob
import os
import importlib
import logging

from typing import Dict, List

logger = logging.getLogger(__name__)


class BinDayException(BaseException):
    ''' Exceptions for this module '''


class BinDays():
    ''' Return class for BinLookup '''
    def __init__(self) -> None:
        self.days: Dict[str, datetime.date] = {}

    def add(self, label: str, collection: datetime.date):
        ''' add a collection event '''
        self.days[label] = collection

    def __str__(self):
        ret: List[str] = []
        for binday in sorted(self.days.items(), key=lambda x: (x[1], x[0])):
            ret.append(f"{binday[0]}: {binday[1]:%a %d %b}")
        return "\n".join(ret)


class BinLookup():
    ''' This base class specifies an Interface for commands '''

    lookups: Dict[str, BinLookup] = {}  # class leve lookup

    authority: str = "Unknown"

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.lookups[cls.authority] = cls

    def lookup(self, housenumber: str = None, postcode: str = None) -> BinDays:
        ''' overload with a function returning a string with the binday info '''
        raise NotImplementedError(
            f"Cannot lookup for {self.authority}"
        )


class BinDayGetter():
    ''' A UK level binday checker '''

    def __init__(self, postcode: str = None, housenumber: str = None) -> None:
        self.post_code = postcode
        self.house_number = housenumber

        council_lookup = urllib.request.urlopen(
            "https://www.gov.uk/rubbish-collection-day",
            urllib.parse.urlencode({"postcode": postcode}).encode("ascii")
        )

        self.council = council_lookup.geturl().rsplit(
            sep='/', maxsplit=2
        )[2]
        if self.council not in BinLookup.lookups:
            raise BinDayException(f"Unknown Authority '{self.council}'")

        self.checker = BinLookup.lookups[self.council]()

    def bin_day(self) -> BinDays:
        ''' returns a string summary '''
        return self.checker.lookup(
            housenumber=self.house_number,
            postcode=self.post_code
        )

    def __str__(self):
        return str(self.bin_day())


for f in glob.glob(os.path.join(
    os.path.dirname(__file__),
    "*.py"
)):
    m = os.path.basename(f)
    if m.startswith("_"):
        continue
    try:
        logger.debug("Loading Cmd: %s", m)
        importlib.import_module("." + os.path.splitext(m)[0], __package__)
    except ImportWarning as e:
        logger.warning("%s: %s", m.rsplit(".", 1)[0], str(e))
    except ImportError as e:
        logger.error("Failed to import command '%s': %s", m.rsplit(".", 1)[0], e.msg)
