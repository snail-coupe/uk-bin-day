''' implements a basic stand-alone CLI '''
import logging
from argparse import ArgumentParser

from ukbinday import BinDayGetter


def main():
    ''' main '''
    logging.basicConfig(level=logging.DEBUG, force=True)

    parser = ArgumentParser()
    parser.add_argument("number", nargs='?', type=str, default=None)
    parser.add_argument("postcode", nargs=2)
    args = parser.parse_args()
    postcode = (" ".join(args.postcode)).upper()

    logging.info("Lookup from Scratch:")
    logging.info(BinDayGetter(housenumber=args.number, postcode=postcode).bin_day())


if __name__ == "__main__":
    main()
