import logging
import psutil
from pathlib import Path
import os
import re


class SDCardInfo:
    def __init__(self, device, mountpoint):
        self.device = device
        self.mountpoint = mountpoint

class DCIMSDCardLoader:
    def __init__(self):
        pass
    def find_sd_cards(self):
        sd_cards = []
        for disk in psutil.disk_partitions():
            logging.debug(f"Checking {disk.device}")
            mountpoint_path = Path(disk.mountpoint)
            dcim_path = mountpoint_path / 'DCIM'
            if dcim_path.exists():
                logging.debug(f"Found DCIM Card: {disk.device}")
                sd_cards.append(SDCardInfo(disk.device, mountpoint_path))
        return sd_cards


class DevNameSDCardLoader:
    def __init__(self):
        pass
    def is_devname_match(self, device_string):
        '''Check if a mounted storage device is an SD card'''
        sd_card_device_string = os.getenv("SD_CARD_MATCH_STRING")
        if sd_card_device_string is None:
            sd_card_device_string = "/dev/sd[b-z]"
        match = re.match(rf'{sd_card_device_string}', device_string)
        # match = re.match(r'/dev/sd[b-z]', device_string)
        return match is not None

    def find_sd_cards(self):
        sd_cards = []
        for disk in psutil.disk_partitions():
            logging.debug(f"Checking {disk.device}")
            if self.is_devname_match(disk.device):
                logging.debug(f"Found SD Card by device name: {disk.device}")
                sd_cards.append(SDCardInfo(disk.device, Path(disk.mountpoint)))
        return sd_cards


class ComboLoader:
    def __init__(self):
        self.sd_card_loaders = [DCIMSDCardLoader(), DevNameSDCardLoader()]

    def find_sd_cards(self):
        '''Returns a list of SDCardInfo objects'''
        sd_cards_dictionary = {}
        for loader in self.sd_card_loaders:
            for sd_card in loader.find_sd_cards():
                sd_cards_dictionary[sd_card.device] = sd_card
        return list(sd_cards_dictionary.values())




if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    dcim_cards = DCIMSDCardLoader().find_sd_cards()
    dev_cards = DevNameSDCardLoader().find_sd_cards()
    combo_cards = ComboLoader().find_sd_cards()

    if not dcim_cards:
        print("No DCIM Cards Found")
    else:
        for dcim_card in dcim_cards:
            print(f"Device: {dcim_card.device}, Path: {dcim_card.mountpoint}")

    if not dev_cards:
        print("No SD Cards Found")
    else:
        for dev_card in dev_cards:
            print(f"Device: {dev_card.device}, Path: {dev_card.mountpoint}")

    if not combo_cards:
        print("No Combo Cards Found")
    else:
        for combo_card in combo_cards:
            print(f"Device: {combo_card.device}, Path: {combo_card.mountpoint}")
