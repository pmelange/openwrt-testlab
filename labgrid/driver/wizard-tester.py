#!/usr/bin/env python3

# mypy: disable-error-code="attr-defined"

import argparse
import json
import logging

from argparse import RawTextHelpFormatter
from time import sleep

from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
#from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
#from selenium.webdriver.firefox.options import Options
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select

luci_webaddress = "https://192.168.0.124"
luci_timeout = 2

##############################
#    Play around with LuCI   #
##############################


def click_next(browser):
    button = browser.find_element(by=By.CLASS_NAME, value="cbi-button.cbi-button-save")
    button.click()


display = Display(visible=0, size=(1280, 720))
display.start()

logger = logging.getLogger('selenium')
logger.setLevel(logging.DEBUG)

service = Service(executable_path='/usr/bin/chromedriver')

options = Options()
#options.add_argument('ignore-certificate-errors')
options.add_argument("--headless=new")
options.accept_insecure_certs = True
options.binary_location = "/usr/bin/chromium-browser"

browser = webdriver.Chrome(service=service, options=options)
browser.implicitly_wait(5)

# call LuCI-interface and wait unti its loaded
browser.get(luci_webaddress)
# figure out success via checking pagetitle fo "LuCI"
error_count = 0
while "LuCI" not in browser.title:
    sleep(2)
    error_count += 1
    if error_count > 12:
        print("connecting to " + luci_webaddress + " failed!")
        print("exiting...")
        exit(1)

sleep(2)
pw_0 = browser.find_element(by=By.NAME, value="cbid.ffwizward.1.pw1")
pw_1 = browser.find_element(by=By.NAME, value="cbid.ffwizward.1.pw2")
while not pw_0:
    try:
        sleep(luci_timeout)
        pw_0 = browser.find_element(by=By.NAME, value="cbid.ffwizward.1.pw1")
        pw_1 = browser.find_element(by=By.NAME, value="cbid.ffwizward.1.pw2")
    except Exception:
        continue


pw_0.send_keys("passwd")
pw_1.send_keys("passwd")
click_next(browser)

sleep(2)

# select community
hostname = browser.find_element(by=By.NAME, value="cbid.ffwizward.1.hostname")
hostname.clear()
hostname.send_keys("hostname")
click_next(browser)

browser.find_element(
            by=By.LINK_TEXT, value="Participate in the Freifunk-Network and share Internet"
        ).click()

# configure bandwidth of sharenet
bw_down = browser.find_element(
       by=By.NAME, value="cbid.ffuplink.1.usersBandwidthDown"
    )
bw_up = browser.find_element(by=By.NAME, value="cbid.ffuplink.1.usersBandwidthUp")

bw_down.send_keys("60")
bw_up.send_keys("40")

click_next(browser)

# monitoring yes/no
elem = browser.find_element(by=By.NAME, value="cbid.ffwizard.1.stats")
elem.click()

click_next(browser)

# set ip-adresses
sleep(2)
radio0 = browser.find_element(by=By.NAME, value="cbid.ffwizard.1.meship_radio0")
radio0.send_keys("10.0.0.1")
radio1 = browser.find_element(by=By.NAME, value="cbid.ffwizard.1.meship_radio1")
radio1.send_keys("10.0.0.2")

dhcp = browser.find_element(by=By.NAME, value="cbid.ffwizard.1.dhcpmesh")
dhcp.send_keys("10.2.0.0/24")

click_next(browser)

print("Configuration of your test-node seems to be successfully done.")
browser.close()

browser.quit()
display.stop()

exit()
