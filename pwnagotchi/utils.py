import glob
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from enum import Enum

import toml
import yaml

import pwnagotchi
from pwnagotchi.fs import ensure_write


# https://stackoverflow.com/questions/823196/yaml-merge-in-python
def merge_config(user, default):
    if isinstance(user, dict) and isinstance(default, dict):
        for k, v in default.items():
            if k not in user:
                user[k] = v
            else:
                user[k] = merge_config(user[k], v)
    return user


def keys_to_str(data):
    if isinstance(data, list):
        converted_list = list()
        for item in data:
            if isinstance(item, list) or isinstance(item, dict):
                converted_list.append(keys_to_str(item))
            else:
                converted_list.append(item)
        return converted_list

    converted_dict = dict()
    for key, value in data.items():
        if isinstance(value, list) or isinstance(value, dict):
            converted_dict[str(key)] = keys_to_str(value)
        else:
            converted_dict[str(key)] = value

    return converted_dict


def load_config(args):
    default_config_path = os.path.dirname(args.config)
    if not os.path.exists(default_config_path):
        os.makedirs(default_config_path)

    ref_defaults_file = os.path.join(os.path.dirname(pwnagotchi.__file__),
                                     "defaults.toml")
    ref_defaults_data = None

    # check for a config.yml file on /boot/
    for boot_conf in ["/boot/config.yml", "/boot/config.toml"]:
        if os.path.exists(boot_conf):
            # logging not configured here yet
            print("installing %s to %s ...", boot_conf, args.user_config)
            # https://stackoverflow.com/questions/42392600/oserror-errno-18-invalid-cross-device-link
            shutil.move(boot_conf, args.user_config)
            break

    # check for an entire pwnagotchi folder on /boot/
    if os.path.isdir("/boot/pwnagotchi"):
        print("installing /boot/pwnagotchi to /etc/pwnagotchi ...")
        shutil.rmtree("/etc/pwnagotchi", ignore_errors=True)
        shutil.move("/boot/pwnagotchi", "/etc/")

    # if not config is found, copy the defaults
    if not os.path.exists(args.config):
        print("copying %s to %s ..." % (ref_defaults_file, args.config))
        shutil.copy(ref_defaults_file, args.config)
    else:
        # check if the user messed with the defaults

        with open(ref_defaults_file) as fp:
            ref_defaults_data = fp.read()

        with open(args.config) as fp:
            defaults_data = fp.read()

        if ref_defaults_data != defaults_data:
            print(
                "!!! file in %s is different than release defaults, overwriting !!!"
                % args.config)
            shutil.copy(ref_defaults_file, args.config)

    # load the defaults
    with open(args.config) as fp:
        config = toml.load(fp)

    # load the user config
    try:
        user_config = None
        # migrate
        yaml_name = args.user_config.replace(".toml", ".yml")
        if not os.path.exists(args.user_config) and os.path.exists(yaml_name):
            # no toml found; convert yaml
            logging.info("Old yaml-config found. Converting to toml...")
            with open(args.user_config,
                      "w") as toml_file, open(yaml_name) as yaml_file:
                user_config = yaml.safe_load(yaml_file)
                # convert int/float keys to str
                user_config = keys_to_str(user_config)
                # convert to toml but use loaded yaml
                toml.dump(user_config, toml_file)
        elif os.path.exists(args.user_config):
            with open(args.user_config) as toml_file:
                user_config = toml.load(toml_file)

        if user_config:
            config = merge_config(user_config, config)
    except Exception as ex:
        logging.error(
            "There was an error processing the configuration file:\n%s ", ex)
        sys.exit(1)

    # the very first step is to normalize the display name so we don't need dozens of if/elif around
    if config["ui"]["display"]["type"] in ("inky", "inkyphat"):
        config["ui"]["display"]["type"] = "inky"

    elif config["ui"]["display"]["type"] in ("papirus", "papi"):
        config["ui"]["display"]["type"] = "papirus"

    elif config["ui"]["display"]["type"] in ("oledhat", ):
        config["ui"]["display"]["type"] = "oledhat"

    elif config["ui"]["display"]["type"] in (
            "ws_1",
            "ws1",
            "waveshare_1",
            "waveshare1",
    ):
        config["ui"]["display"]["type"] = "waveshare_1"

    elif config["ui"]["display"]["type"] in (
            "ws_2",
            "ws2",
            "waveshare_2",
            "waveshare2",
    ):
        config["ui"]["display"]["type"] = "waveshare_2"

    elif config["ui"]["display"]["type"] in (
            "ws_27inch",
            "ws27inch",
            "waveshare_27inch",
            "waveshare27inch",
    ):
        config["ui"]["display"]["type"] = "waveshare27inch"

    elif config["ui"]["display"]["type"] in (
            "ws_29inch",
            "ws29inch",
            "waveshare_29inch",
            "waveshare29inch",
    ):
        config["ui"]["display"]["type"] = "waveshare29inch"

    elif config["ui"]["display"]["type"] in ("lcdhat", ):
        config["ui"]["display"]["type"] = "lcdhat"

    elif config["ui"]["display"]["type"] in ("dfrobot", "df"):
        config["ui"]["display"]["type"] = "dfrobot"

    elif config["ui"]["display"]["type"] in (
            "ws_154inch",
            "ws154inch",
            "waveshare_154inch",
            "waveshare154inch",
    ):
        config["ui"]["display"]["type"] = "waveshare154inch"

    elif config["ui"]["display"]["type"] in (
            "waveshare144lcd",
            "ws_144inch",
            "ws144inch",
            "waveshare_144inch",
            "waveshare144inch",
    ):
        config["ui"]["display"]["type"] = "waveshare144lcd"

    elif config["ui"]["display"]["type"] in (
            "ws_213d",
            "ws213d",
            "waveshare_213d",
            "waveshare213d",
    ):
        config["ui"]["display"]["type"] = "waveshare213d"

    elif config["ui"]["display"]["type"] in (
            "ws_213bc",
            "ws213bc",
            "waveshare_213bc",
            "waveshare213bc",
    ):
        config["ui"]["display"]["type"] = "waveshare213bc"

    elif config["ui"]["display"]["type"] in ("spotpear24inch"):
        config["ui"]["display"]["type"] = "spotpear24inch"

    else:
        print("unsupported display type %s" % config["ui"]["display"]["type"])
        sys.exit(1)

    return config


def secs_to_hhmmss(secs):
    mins, secs = divmod(secs, 60)
    hours, mins = divmod(mins, 60)
    return "%02d:%02d:%02d" % (hours, mins, secs)


def total_unique_handshakes(path):
    expr = os.path.join(path, "*.pcap")
    return len(glob.glob(expr))


def iface_channels(ifname):
    channels = []
    output = subprocess.getoutput("/sbin/iwlist %s freq" % ifname)
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("Channel "):
            channels.append(int(line.split()[1]))
    return channels


def led(on=True):
    with open("/sys/class/leds/led0/brightness", "w+t") as fp:
        fp.write("%d" % (0 if on is True else 1))


def blink(times=1, delay=0.3):
    for t in range(0, times):
        led(True)
        time.sleep(delay)
        led(False)
        time.sleep(delay)
    led(True)


class WifiInfo(Enum):
    """
    Fields you can extract from a pcap file
    """

    BSSID = 0
    ESSID = 1
    ENCRYPTION = 2
    CHANNEL = 3
    RSSI = 4


class FieldNotFoundError(Exception):
    pass


def extract_from_pcap(path, fields):
    """
    Search in pcap-file for specified information

    path: Path to pcap file
    fields: Array of fields that should be extracted

    If a field is not found, FieldNotFoundError is raised
    """
    results = dict()
    for field in fields:
        if not isinstance(field, WifiInfo):
            raise TypeError("Invalid field")

        subtypes = set()

        if field == WifiInfo.BSSID:
            from scapy.all import (
                Dot11Beacon,
                Dot11ProbeResp,
                Dot11AssoReq,
                Dot11ReassoReq,
                Dot11,
                sniff,
            )

            subtypes.add("beacon")
            bpf_filter = " or ".join(
                [f"wlan type mgt subtype {subtype}" for subtype in subtypes])
            packets = sniff(offline=path, filter=bpf_filter)
            try:
                for packet in packets:
                    if packet.haslayer(Dot11Beacon):
                        if hasattr(packet[Dot11], "addr3"):
                            results[field] = packet[Dot11].addr3
                            break
                else:  # magic
                    raise FieldNotFoundError("Could not find field [BSSID]")
            except Exception:
                raise FieldNotFoundError("Could not find field [BSSID]")
        elif field == WifiInfo.ESSID:
            from scapy.all import (
                Dot11Beacon,
                Dot11ReassoReq,
                Dot11AssoReq,
                Dot11,
                sniff,
                Dot11Elt,
            )

            subtypes.add("beacon")
            subtypes.add("assoc-req")
            subtypes.add("reassoc-req")
            bpf_filter = " or ".join(
                [f"wlan type mgt subtype {subtype}" for subtype in subtypes])
            packets = sniff(offline=path, filter=bpf_filter)
            try:
                for packet in packets:
                    if packet.haslayer(Dot11Elt) and hasattr(
                            packet[Dot11Elt], "info"):
                        results[field] = packet[Dot11Elt].info.decode("utf-8")
                        break
                else:  # magic
                    raise FieldNotFoundError("Could not find field [ESSID]")
            except Exception:
                raise FieldNotFoundError("Could not find field [ESSID]")
        elif field == WifiInfo.ENCRYPTION:
            from scapy.all import Dot11Beacon, sniff

            subtypes.add("beacon")
            bpf_filter = " or ".join(
                [f"wlan type mgt subtype {subtype}" for subtype in subtypes])
            packets = sniff(offline=path, filter=bpf_filter)
            try:
                for packet in packets:
                    if packet.haslayer(Dot11Beacon) and hasattr(
                            packet[Dot11Beacon], "network_stats"):
                        stats = packet[Dot11Beacon].network_stats()
                        if "crypto" in stats:
                            # set with encryption types
                            results[field] = stats["crypto"]
                            break
                else:  # magic
                    raise FieldNotFoundError(
                        "Could not find field [ENCRYPTION]")
            except Exception:
                raise FieldNotFoundError("Could not find field [ENCRYPTION]")
        elif field == WifiInfo.CHANNEL:
            from scapy.all import sniff, RadioTap
            from pwnagotchi.mesh.wifi import freq_to_channel

            packets = sniff(offline=path, count=1)
            try:
                results[field] = freq_to_channel(
                    packets[0][RadioTap].ChannelFrequency)
            except Exception:
                raise FieldNotFoundError("Could not find field [CHANNEL]")
        elif field == WifiInfo.RSSI:
            from scapy.all import sniff, RadioTap
            from pwnagotchi.mesh.wifi import freq_to_channel

            packets = sniff(offline=path, count=1)
            try:
                results[field] = packets[0][RadioTap].dBm_AntSignal
            except Exception:
                raise FieldNotFoundError("Could not find field [RSSI]")

    return results


class StatusFile(object):
    def __init__(self, path, data_format="raw"):
        self._path = path
        self._updated = None
        self._format = data_format
        self.data = None

        if os.path.exists(path):
            self._updated = datetime.fromtimestamp(os.path.getmtime(path))
            with open(path) as fp:
                if data_format == "json":
                    self.data = json.load(fp)
                else:
                    self.data = fp.read()

    def data_field_or(self, name, default=""):
        if self.data is not None and name in self.data:
            return self.data[name]
        return default

    def newer_then_minutes(self, minutes):
        return (self._updated is not None
                and ((datetime.now() - self._updated).seconds / 60) < minutes)

    def newer_then_hours(self, hours):
        return (self._updated is not None and
                ((datetime.now() - self._updated).seconds / (60 * 60)) < hours)

    def newer_then_days(self, days):
        return (self._updated is not None
                and (datetime.now() - self._updated).days < days)

    def update(self, data=None):
        self._updated = datetime.now()
        self.data = data
        with ensure_write(self._path, "w") as fp:
            if data is None:
                fp.write(str(self._updated))

            elif self._format == "json":
                json.dump(self.data, fp)

            else:
                fp.write(data)
