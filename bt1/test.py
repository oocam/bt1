from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import time
import os

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:4000/graphql")

def upload_result():
    update_time = datetime.utcnow().isoformat()
    transport = RequestsHTTPTransport(url = BACKEND_URL)
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    query = gql("""
        mutation LogBatteryStatus($data: BatteryStatusArgs!) {
            logBatteryStatus(data: $data) {
                id
            }
        }
    """)
    try:
        params = {
            "data": {
                "batteryStatus":{
                    "battery_percentage": 100,
                    "battery_voltage": 16.4,
                    "battery_current": 0.0,
                    "controller_temperature": 28,
                    "battery_temperature": 25,
                    "load_status": 'on',
                    "load_voltage": 16.4,
                    "load_current": 1.09,
                    "load_power": 17.0,
                    "pv_voltage": 23.1,
                    "pv_current": 0.0,
                    "pv_power": 0,
                    "max_charging_power_today": 141,
                    "max_discharging_power_today": 23,
                    "charging_amp_hours_today": 59,
                    "discharging_amp_hours_today": 12,
                    "power_generation_today": 950,
                    "power_consumption_today": 192,
                    "power_generation_total": 6202,
                    "charging_status": 'mppt',
                    },
                "readingTime": update_time}
                }
        result = client.execute(query, variable_values=params)
        print(result)
    except Exception as error:
        print("upload error")
        print(error)




def main():
    upload_result()


if __name__ == "__main__":
    main()
