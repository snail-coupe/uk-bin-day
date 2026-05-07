''' Tewkesbury Bin Collection Module '''

import json
import datetime
import urllib.parse
import urllib.request
import logging

from ukbinday import BinLookup, BinDays, BinDayException

logger = logging.getLogger(__name__)


class TewksburyLookup(BinLookup):
    ''' BinLookup class for tewkesbury '''
    authority: str = "tewkesbury"

    def lookup(self, housenumber: str |None, postcode: str |None) -> BinDays:
        if not housenumber:
            raise TypeError("Missing parameter housenumber")
        if not postcode:
            raise TypeError("Missing parameter postcode")
        normalised_postcode = urllib.parse.quote(postcode.lower())
        round_lookup = urllib.request.urlopen(
            f"https://api-2.tewkesbury.gov.uk/incab/properties/{normalised_postcode}/lookup"
        )
        rounddata = json.loads(round_lookup.read())
        if rounddata['status'] != "OK":
            raise BinDayException(f"Error: {rounddata['status']}")

        if housenumber:
            if housenumber.isdigit():
                logger.debug("Looking for house number %s", housenumber)
                candidates = [x["uprn"] for x in rounddata['body'] if x["propertyNumber"] == int(housenumber)]
            else:
                logger.debug("Looking for %s", housenumber)
                candidates = [x["uprn"] for x in rounddata['body'] if x["fullAddress"].startswith(housenumber)]
        else:
            logger.debug("Checking whole postcode")
            candidates = [x["uprn"] for x in rounddata["body"]]

        if not candidates:
            logger.error("No candiates found")
            raise BinDayException("Error: need more specific house number")
                  
        logger.debug("Potential Addresses: %d", len(candidates))

        if len(candidates) != 1:
            raise BinDayException("Error: need more specific house number")

        uprn_lookup = urllib.request.urlopen(
            f"https://api-2.tewkesbury.gov.uk/incab/rounds/{candidates[0]}/next-collection"
        )
        uprndata: dict[str, dict[str,str]] = json.loads(uprn_lookup.read())

        ret = BinDays()

        rd: list[tuple[str, datetime.date]] = []
        for key, value in uprndata.items():
            rd.append((key, datetime.date.fromisoformat(value['nextCollectionDate'].split('T')[0])))

        for ctype in sorted(rd, key=lambda x: x[1]):
            ret.add(ctype[0].capitalize(), ctype[1])
        return ret
