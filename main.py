from ctypes import FormatError
import sys
from addressnet.predict import predict
import psycopg2
from pathlib import Path
import pandas as pd

SELECT_STMT = "SELECT gnaf_pid, address, postcode, state, latitude, longitude FROM gnaf_202111.addresses WHERE number_first = %(number_first)s AND street_name = %(street_name)s AND locality_name=%(locality_name)s AND postcode=%(postcode)s AND state=%(state)s LIMIT 1"
STATES = {
    "AUSTRALIAN CAPITAL TERRITORY": "ACT",
    "NEW SOUTH WALES": "NSW",
    "NORTHERN TERRITORY": "NT",
    "QUEENSLAND": "QLD",
    "SOUTH AUSTRALIA": "SA",
    "TASMANIA": "TAS",
    "VICTORIA": "VIC",
    "WESTERN AUSTRALIA": "WA",
}

sep = ", "
def get_query(d): 
    return (''
        + d["FLAT_TYPE_CODE"] + sep
        + d["FLAT_NUMBER"] + sep
        + d["BUILDING_NAME"] + sep
        + d["LEVEL_NUMBER"] + sep
        + d["LEVEL_TYPE_CODE"] + sep
        + d["NUMBER_FIRST"] + sep
        + d["NUMBER_LAST"] + sep
        + d["LOT_NUMBER"] + sep
        + d["STREET_NAME"] + sep
        + d["STREET_TYPE_CODE"] + sep
        + d["LOCALITY"] + sep
        + d["STATE_ABBREVIATION"] + sep
        + d["POSTCODE"]
    )


def format_blob_addresses(filename):
    with open(filename) as f:
        a = []
        for line in f:
            a.append(line)

        completed = 0
        addrs = []
        for addr in predict(a):
            if addr["state"]:
                addr["state"] = STATES[addr["state"]]
            addrs.append(addr)
            completed += 1
            print(f"Formatted: {completed}/{len(a)} addresses")
    return addrs

def format_structured_address(filename):
    ext = Path(filename).suffix 
    if ext == "csv":
        data = pd.read_csv(filename)
    else:
        raise FormatError(f"Address format not supported: {ext}")

    data["destructured_query"] = get_query(data)
    print(data)
    exit()

    

def main(filename="test.txt"):

    addrs = (format_blob_addresses(filename) if Path(filename).suffix == "txt" 
        else format_structured_address(filename))

    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="password"
    )

    good_addrs = []
    bad_addrs = []
    for addr in addrs:
        cursor = conn.cursor()
        try:
            cursor.execute(SELECT_STMT, addr)

            data = cursor.fetchone()

            if data:
                formatted_data = {
                    "id": data[0],
                    "address": data[1],
                    "postcode": data[2],
                    "state": data[3],
                    "coords": {
                        "lat": data[4],
                        "long": data[5]
                    }
                }
                good_addrs.append(formatted_data)
                print(formatted_data)
            else:
                bad_addrs.append(addr)
                print("Bad address")

        except:
            bad_addrs.append(addr)
        cursor.close()

    print("Bad addresses: ", bad_addrs)


if __name__ == "__main__":
    if(len(sys.argv) < 2):
        print("     -Usage : poetry run python main.py <filename.txt/.csv>")
        exit()

    filename = sys.argv[1]
    main(filename)