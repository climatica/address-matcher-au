
import math
import sys
from addressnet.predict import predict
from numpy import SHIFT_UNDERFLOW
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

def entry(data, suffix: str = '', prefix:str = ''):
    # Nans are empty
    copy = data.copy()
    nans = copy == 'nan'
    copy = prefix + copy.astype(str) + suffix
    copy[nans] = ''
    return copy

def get_query(d): 
    return (''
        + entry(d["LOT_NUMBER"],prefix='LOT ',suffix=', ')
        + entry(d["FLAT_TYPE_CODE"]," ") + entry(d["FLAT_NUMBER"],", ")
        + entry(d["LEVEL_NUMBER"]) + entry(d["LEVEL_TYPE_CODE"],", ")
        + entry(d["BUILDING_NAME"],", ")
        + entry(d["NUMBER_FIRST"])
        + entry(d["NUMBER_LAST"],prefix="-")
        + entry(d["STREET_NAME"],prefix=' ',suffix=' ')
        + entry(d["STREET_TYPE_CODE"],suffix=', ')
        + entry(d["LOCALITY"],suffix=', ')
        + entry(d["STATE_ABBREVIATION"],suffix=', ')
        + entry(d["POSTCODE"])
        # We only handle australia for now, so omit AU
        # + entry(d["COUNTRY"],prefix=', ')
    )

def format_addr_list(blobs):
    addrs = []
    completed = 0
    for addr in predict(blobs):
        if addr["state"]:
            addr["state"] = STATES[addr["state"]]
        print(f"Formatted: {completed}/{len(blobs)} addresses")
        print(f"     - {blobs[completed]}")
        print(f"        => {addr}")
        addrs.append(addr)
        completed += 1
    return addrs

def format_blob_addresses(filename):
    with open(filename) as f:
        a = []
        for line in f:
            a.append(line)

        addrs = format_addr_list(a)
    return addrs

def format_structured_address(filename):
    ext = Path(filename).suffix 
    if ext == ".csv":
        data = pd.read_csv(filename).astype(str)
    else:
        raise RuntimeError(f"Address format not supported: {ext}")

    data["destructured_query"] = get_query(data)
    queries = data["destructured_query"].to_list()

    return format_addr_list(queries)


def main(filename="test.txt"):

    addrs = (format_blob_addresses(filename) if Path(filename).suffix == ".txt" 
        else format_structured_address(filename))
    
    conn = psycopg2.connect(
        host="localhost",
        port=5433,
        user="postgres",
        password="password"
    )

    print("Geocoding formatted addresses...")
    good_addrs = []
    bad_addrs = []
    completed = 0
    last_report = 0
    report_thres_percent = 5
    report_thres = math.floor(report_thres_percent * len(addrs) / 100)
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
                # print(formatted_data)
            else:
                bad_addrs.append(addr)
                # print("Bad address")

        except:
            bad_addrs.append(addr)
        cursor.close()
        completed += 1
        if(completed - last_report > report_thres):
            print(f"Completed {math.floor(100 * completed / float(len(addrs)))}% - (success + fail = total : {len(good_addrs)} + {len(bad_addrs)} = {completed})")
            last_report = completed

    print("Geocoding finished!")
    print(f"Total success rate: {100 * len(good_addrs) / float(len(addrs))}%")

    
    print(f"Saved failed addresses to ")


if __name__ == "__main__":
    if(len(sys.argv) < 2):
        print("     -Usage : poetry run python main.py <filename.txt/.csv>")
        exit()

    filename = sys.argv[1]
    main(filename)