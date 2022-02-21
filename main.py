from addressnet.predict import predict
import psycopg2

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


def main():
    with open("test.txt") as f:
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
    main()