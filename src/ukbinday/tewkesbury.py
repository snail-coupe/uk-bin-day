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

    def lookup(self, housenumber: str = None, postcode: str = None) -> BinDays:
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
            raise BinDayException(f"Error: {data['status']}")

        if housenumber:
            if housenumber.isdigit():
                logger.info("Looking for house number %s", housenumber)
                candidates = [x["uprn"] for x in rounddata['body'] if x["propertyNumber"] == int(housenumber)]
            else:
                logger.info("Looking for %s", housenumber)
                candidates = [x["uprn"] for x in rounddata['body'] if x["fullAddress"].startswith(housenumber)]
        else:
            logger.info("Checking whole postcode")
            candidates = [x["uprn"] for x in rounddata["body"]]

        if not candidates:
            logger.error("No candiates found")
            raise BinDayException(f"Error: need more specific house number")
                  
        logger.info("Potential Addresses: %d", len(candidates))

        if len(candidates) != 1:
            raise BinDayException(f"Error: need more specific house number")

        allrns = {}
        for uprn in candidates:
            uprn_lookup = urllib.request.urlopen(
                f"https://api-2.tewkesbury.gov.uk/incab/rounds/{uprn}/next-collection"
            )
            uprndata = json.loads(uprn_lookup.read())
            if uprndata['status'] != "OK":
                next
            uprnday = uprndata["body"][0]["roundInfo"]
            allrns[uprnday] = uprndata["body"]

        if len(allrns) != 1:
            raise BinDayException(f"Error: need more specific house number")

        ret = BinDays()

        data = allrns[uprnday]

        for cday in sorted(data, key=lambda x: x['NextCollection']):
            ret.add(cday['collectionType'], datetime.date.fromisoformat(cday['NextCollection']))

        return ret
