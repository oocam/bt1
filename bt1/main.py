import os
import asyncio
import websockets
import json
from threading import Timer
import logging 
from bt1.ble import DeviceManager, Device
from bt1.utils import create_request_payload, parse_charge_controller_info, parse_set_load_response, Bytes2Int

logging.basicConfig(level=logging.INFO)

SERVER_URI = os.environ.get("SERVER_URI", "wss://api.fishcam.openoceancam.com/ws")

DEVICE_ID = 255
POLL_INTERVAL = 30 # seconds

NOTIFY_CHAR_UUID = "0000fff1-0000-1000-8000-00805f9b34fb"
WRITE_CHAR_UUID  = "0000ffd1-0000-1000-8000-00805f9b34fb"

READ_PARAMS = {
    'FUNCTION': 3,
    'REGISTER': 256,
    'WORDS': 34
}

WRITE_PARAMS_LOAD = {
    'FUNCTION': 6,
    'REGISTER': 266
}

class BT1:
    def __init__(self, adapter_name, mac_address, alias=None, on_connected=None, on_data_received=None, interval = POLL_INTERVAL):
        self.adapter_name = adapter_name
        self.connected_callback = on_connected
        self.data_received_callback = on_data_received
        self.manager = DeviceManager(adapter_name=adapter_name)
        self.device = Device(mac_address=mac_address, alias=alias, manager=self.manager, on_resolved=self.__on_resolved, on_data=self.__on_data_received, notify_uuid=NOTIFY_CHAR_UUID, write_uuid=WRITE_CHAR_UUID)
        self.timer = None
        self.interval = interval
        self.data = {}

    def connect(self):
        self.device.connect()

    def __on_resolved(self):
        logging.info("resolved services")
        if self.connected_callback is not None:
            self.connected_callback(self)

    def __on_data_received(self, value):
        operation = Bytes2Int(value, 1, 1)

        if operation == 3:
            logging.debug("on_data_received: response for read operation")
            self.data = parse_charge_controller_info(value)
            if self.data_received_callback is not None:
                self.data_received_callback(self, self.data)
        elif operation == 6:
            self.data = parse_set_load_response(value)
            logging.debug("on_data_received: response for write operation")
            if self.data_received_callback is not None:
                self.data_received_callback(self, self.data)
        else:
            logging.warn("on_data_received: unknown operation={}.format(operation)")

    def poll_params(self):
        self.__read_params()
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.timer = Timer(self.interval, self.poll_params)
        self.timer.start()

    def __read_params(self):
        logging.debug("reading params")
        request = create_request_payload(DEVICE_ID, READ_PARAMS["FUNCTION"], READ_PARAMS["REGISTER"], READ_PARAMS["WORDS"])
        self.device.characteristic_write_value(request)

    def set_load(self, value = 0):
        logging.debug("setting load {}".format(value))
        request = create_request_payload(DEVICE_ID, WRITE_PARAMS_LOAD["FUNCTION"], WRITE_PARAMS_LOAD["REGISTER"], value)
        self.device.characteristic_write_value(request)

    def disconnect(self):
        if self.timer is not None and self.timer.is_alive():
            self.timer.cancel()
        self.device.disconnect()

async def send_data(data):
    async with websockets.connect(SERVER_URI) as websocket:
        await websocket.send(json.dumps(data))

def on_connected(app: BT1):
    app.poll_params() # OR app.set_load(1)

def on_data_received(app: BT1, data):
    logging.info("{} => {}".format(app.device.alias(), data))
    loop = asyncio.get_event_loop()
    loop.run_until_complete(send_data(data=data))

def main():
    ADAPTER = "hci0"
    MAC_ADDR = "DC:0D:30:9C:64:14"
    DEVICE_ALIAS = "BT-TH-309C6414"
    POLL_INTERVAL = 1 # read data interval (seconds)
    
    logging.info("Using server:".format(SERVER_URI))

    bt1 = BT1(ADAPTER, MAC_ADDR, DEVICE_ALIAS, on_connected, on_data_received, POLL_INTERVAL)
    bt1.connect()


if __name__ == "__main__":
    main()