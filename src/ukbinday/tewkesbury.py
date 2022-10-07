''' Tewkesbury Bin Collection Module '''

import json
import datetime
import urllib.parse
import urllib.request

from ukbinday import BinLookup, BinDays, BinDayException


class TewksburyLookup(BinLookup):
    ''' BinLookup class for tewkesbury '''
    authority: str = "tewkesbury"

    def lookup(self, housenumber: str = None, postcode: str = None) -> BinDays:
        if not postcode:
            raise TypeError("Missing parameter postCode")
        normalised_postcode = urllib.parse.quote(postcode.lower())
        round_lookup = urllib.request.urlopen(
            f"https://api-2.tewkesbury.gov.uk/general/rounds/{normalised_postcode}/nextCollection"
        )
        data = json.loads(round_lookup.read())
        if data['status'] != "OK":
            raise BinDayException(f"Error: {data['status']}")

        ret = BinDays()

        for cday in sorted(data['body'], key=lambda x: x['NextCollection']):
            ret.add(cday['collectionType'], datetime.date.fromisoformat(cday['NextCollection']))

        return ret
