''' Dorstt Bin Collection Module '''

import datetime
import logging
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from typing import Dict

from ukbinday import BinDayException, BinDays, BinLookup

logger = logging.getLogger(__name__)


class _AddressCB(HTMLParser):  # pylint: disable=abstract-method

    search_for: str = None
    result: str = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            trib_dict: Dict[str, str] = {}
            for (trib, value) in attrs:
                trib_dict[trib] = value
            if "href" in trib_dict and \
                    trib_dict["href"].startswith("/mylocal/viewresults") and \
                    "title" in trib_dict and \
                    trib_dict["title"].startswith("Link to nearest information about the address "):
                location_id = trib_dict['href'][21:]
                house_id = trib_dict['title'][46:]
                # logger.debug(f"{location_id}:{house_id}")
                if self.search_for and house_id.startswith(self.search_for):
                    if house_id[len(self.search_for)] in " ,":
                        self.result = location_id


class _CollectionCB(HTMLParser):  # pylint: disable=abstract-method

    collection_days: Dict[str, datetime.date] = {}
    intag = False
    data: str = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'li':
            trib_dict: Dict[str, str] = {}
            for (trib, value) in attrs:
                trib_dict[trib] = value
            if "class" in trib_dict and trib_dict["class"] == "resultListItem":
                self.intag = True
                self.data = ""

    def handle_endtag(self, tag):
        if tag == 'li':
            self.intag = False
            self.data = self.data.strip()
            if self.data.startswith("Your recycling collection"):
                day = " ".join(self.data.split()[-4:])
                self.collection_days["recycling"] = datetime.datetime.strptime(day, "%A %d %B %Y")
                logger.debug("recycling %s", day)
            elif self.data.startswith("Your rubbish collection"):
                day = " ".join(self.data.split()[-4:])
                self.collection_days["rubbish"] = datetime.datetime.strptime(day, "%A %d %B %Y")
                logger.debug("rubbish %s", day)
            elif self.data.startswith("Your food waste collection"):
                day = " ".join(self.data.split()[-4:])
                self.collection_days["food waste"] = datetime.datetime.strptime(day, "%A %d %B %Y")
                logger.debug("food %s", day)

            # logger.info(self.data)

    def handle_data(self, data: str) -> None:
        if self.intag:
            self.data += " " + data


class DorsetLookup(BinLookup):
    ''' BinLookup class for dorset '''
    authority: str = "dorset"

    def lookup(self, housenumber: str = None, postcode: str = None) -> BinDays:
        if not postcode:
            raise BinDayException("Missing parameter postcode")
        if not housenumber:
            raise BinDayException("Missing parameter housenumber")

        normalised_postcode = urllib.parse.quote(postcode.lower())
        address_lookup = urllib.request.urlopen(
            f"https://mapping.dorsetcouncil.gov.uk/mylocal/selectaddress?"
            f"myLocalSearch_text={normalised_postcode}"
        )
        dom = address_lookup.read()

        addr_parser = _AddressCB()
        addr_parser.search_for = housenumber
        addr_parser.feed(dom.decode("utf-8"))
        logger.debug(addr_parser.result)
        if not addr_parser.result:
            raise BinDayException(f"Failed to look up {housenumber} {postcode}")

        collection_lookup = urllib.request.urlopen(
            f"https://mapping.dorsetcouncil.gov.uk/mylocal/viewresults/{addr_parser.result}"
        )
        dom = collection_lookup.read()
        day_parser = _CollectionCB()
        day_parser.feed(dom.decode('utf-8'))

        ret = BinDays()
        for (ctype, day) in day_parser.collection_days.items():
            ret.add(ctype, day)
        return ret
