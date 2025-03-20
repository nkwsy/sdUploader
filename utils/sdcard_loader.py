import logging
import psutil
from pathlib import Path
import os
import re
from utils.sdcard import SDCardAnalyzer


class DCIMSDCardLoader:
    def __init__(self, analyzer):
        self.analyzer = analyzer
    def find_sd_cards(self):
        sd_cards = []
        for disk in psutil.disk_partitions():
            logging.debug(f"Checking {disk.device}")
            mountpoint_path = Path(disk.mountpoint)
            dcim_path = mountpoint_path / 'DCIM'
            if dcim_path.exists():
                logging.debug(f"Found DCIM Card: {disk.device}")
                sd_card = self.analyzer.analyze_sd_card(disk.device, mountpoint_path)
                sd_cards.append(sd_card)
        return sd_cards


class DevNameSDCardLoader:
    def __init__(self, analyzer):
        self.analyzer = analyzer

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
                sd_card = self.analyzer.analyze_sd_card(disk.device, Path(disk.mountpoint))
                sd_cards.append(sd_card)
        return sd_cards


class ComboLoader:
    def __init__(self):
        self.sd_card_loaders = [DCIMSDCardLoader(SDCardAnalyzer()), DevNameSDCardLoader(SDCardAnalyzer())]

    def find_sd_cards(self):
        '''Returns a list of SDCardInfo objects'''
        sd_cards_dictionary = {}
        for loader in self.sd_card_loaders:
            for sd_card in loader.find_sd_cards():
                sd_cards_dictionary[sd_card.device] = sd_card
        return list(sd_cards_dictionary.values())



