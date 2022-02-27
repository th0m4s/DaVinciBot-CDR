import dvbcdr
import serial
import serial.tools.list_ports
import getopt
import sys
import yaml
import threading
import time
import json

config = {}
opened_ports = dvbcdr.utils.thread_safe.ThreadSafeList()
retries = dvbcdr.utils.thread_safe.ThreadSafeDict()


def check_ports():
    ports = [x.device for x in serial.tools.list_ports.comports()]
    with opened_ports, retries:
        for port_path in ports:
            if(port_path not in opened_ports):
                if port_path not in retries:
                    retries[port_path] = 0

                if retries[port_path] < 3:
                    retries[port_path] += 1
                    threading.Thread(target=handle_port, args=(port_path, retries[port_path]), daemon=True).start()

        already_tried_ports = list(retries.keys())
        for old_port in already_tried_ports:
            if old_port not in ports:
                del retries[old_port]


def __get_data_type(data):
    if isinstance(data, int):
        return (0, int)
    elif isinstance(data, str):
        return (1, str)
    elif isinstance(data, float):
        return (2, float)

    return (-1, None)


def __get_data_received(crc_subject, port_serial):
    return lambda r: __data_received(port_serial, crc_subject, r)


def __data_received(port_serial, crc_subject, data):
    data_type, _ = __get_data_type(data)
    length = -1
    if data_type == 1:
        data = "\"" + data.replace("\"", "\\\"") + "\""
        data_type = 1
    elif data_type == -1:
        if isinstance(data, tuple):
            data = list(data)

        if isinstance(data, list):
            length = len(data)
            data_type, type_ctor = __get_data_type(data[0])

            if data_type != -1:
                data = "[" + ",".join([("\"" + x.replace("\"", "\\\"") + "\"" if data_type == 1 else str(x)) for x in data if type(x) == type_ctor]) + "]"

    if data_type in [0, 1, 2]:
        port_serial.write(bytes("{\"c\":2,\"t\":" + str(data_type) + (",\"l\":" + str(length) if length >= 0 else "") + ",\"s\":" + str(crc_subject) + ",\"v\":" + str(data) + "}\n", "utf-8"))


def __event_received(port_serial, event):
    port_serial.write(bytes("{\"c\":3,\"e\":\"" + event + "\"}\n", "utf-8"))


def handle_port(port_path, retry_count):
    with opened_ports:
        opened_ports.append(port_path)

    print("Opening", port_path, "(" + str(retry_count) + "/3)...")
    opening_time = time.time()
    device_id = None

    try:
        baudrate = config.get("baudrate", 115200)
        port_serial = serial.Serial(port_path, baudrate=baudrate, timeout=0)
        port_serial.write(b"{\"c\":0}")

        # creating an Intercom instance
        intercom = dvbcdr.intercom.Intercom()
        intercom.on_events(lambda event: __event_received(port_serial, event))
        intercom.wait_in_new_thread()

        while True:
            if device_id is None and time.time() - opening_time > (2 + retry_count):
                print(port_path, "-> connection timeout!")
                port_serial.close()
                time.sleep(retry_count * 2)
                break

            raw_data = port_serial.readline()
            if len(raw_data) == 0:
                continue

            try:
                data = json.loads(raw_data)
            except json.decoder.JSONDecodeError:
                print("Invalid JSON on", port_path, raw_data.decode("utf-8"))
                continue

            if "c" in data:
                command = data["c"]

                # TODO: maybe we can use python 3.10 match in the future
                if command == 0:
                    if device_id is None:
                        device_id = "unknown"
                        if "v" in data:
                            device_id = data["v"]

                        print(port_path, "->", device_id, "connected!")
                        port_serial.write(b"{\"c\":1}")
                elif command == 1:
                    port_serial.write(b"{\"c\":1}")
                elif command == 2:
                    if "t" in data and "s" in data:
                        data_type = data["t"]
                        crc_subject = data["s"]

                        if "v" in data:
                            data = data["v"]

                        if data_type in [0, 1, 2]:
                            intercom.publish_raw(crc_subject, data)
                        elif data_type == 255:
                            intercom.subscribe_raw(crc_subject, __get_data_received(crc_subject, port_serial))
                            port_serial.write(b"{\"c\":1}")
                elif command == 3:
                    intercom.publish_event(data["e"])
    except Exception as exception:
        print("Error on serial port:", port_path, exception)

    # TODO: intercom.close()
    # intercom.close()
    with opened_ports:
        opened_ports.remove(port_path)


def main():
    config_file = "./config.yaml"

    try:
        opts, args = getopt.getopt(sys.argv[1:], "c:", "config=")
    except getopt.GetoptError:
        print("Usage:", sys.argv[0], "-c <config_file>")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-c", "--config"):
            config_file = arg

    try:
        config = yaml.safe_load(open(config_file))
    except FileNotFoundError:
        print("Config file not found:", config_file)
        sys.exit(2)
    except yaml.YAMLError:
        print("Invalid YAML configuration:", config_file)
        sys.exit(2)

    ports_polling_interval = config.get("ports_polling_interval", 0.1)
    ports_polling_timer = dvbcdr.utils.time.RepeatedTimer(ports_polling_interval, check_ports)


if __name__ == "__main__":
    main()
