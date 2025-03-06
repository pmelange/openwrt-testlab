import attr
from time import sleep
from urllib.parse import urlsplit
import shutil

from labgrid.factory import target_factory
from labgrid.util import gen_marker
from labgrid.util.proxy import proxymanager
from labgrid.util.ssh import sshmanager
from labgrid.step import step
from labgrid.driver import Driver
from labgrid.resource import NetworkSerialPort

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select

@target_factory.reg_driver
@attr.s(eq=False)
class OpenwrtLuCIDriver(Driver):
    """
    OpenwrtLuCIDriver is meant as a driver to change settings via the
    web interface.
    """
    bindings = {
            "serial": NetworkSerialPort,
            }
    find_element_retries = attr.ib(default=2, validator=attr.validators.instance_of(int))

    def __attrs_post_init__(self):
        super().__attrs_post_init__()
        self._url = None
        self._forwarder = None

    def on_activate(self):
        self._remotehost = self.serial.host

        self._service = Service(executable_path='/usr/bin/chromedriver')

        self._options = Options()
        self._options.add_argument("--headless=new")
        self._options.accept_insecure_certs = True
        location = shutil.which("chromium-browser")
        if location is None:
            location = shutil.which("chromium")
        self._options.binary_location = location

        self._browser = webdriver.Chrome(service=self._service, 
                                         options=self._options)
        self._browser.implicitly_wait(5)

    def on_deactivate(self):
 #       self._remove_forward()
        self._browser.close()
        self._browser.quit()
        self._browser = None

    @step(args=['form_element', 'optional', 'by'])
    def _get_elements(self, form_element, optional, by=By.NAME):
        elements = None
        retries = self.find_element_retries
        while elements is None:
            try:
                retries -= 1
                elements = self._browser.find_elements(by=by,
                                                       value=form_element)
            except Exception as e:
                if retries == 0:
                    if optional:
                        pass
                    else:
                        raise e
                    break
                else:
                    sleep(2) 
        return elements

    @step(args=['form_element', 'optional', 'by'])
    def _get_element(self, form_element, optional, by=By.NAME):
        return self._get_elements(form_element, optional, by)[0]

    @step(args=['href', 'optional'])
    def _get_link(self, href, optional):
        element = None
        retries = self.find_element_retries
        while element is None:
            try:
                retries -= 1
                element = self._browser.find_element(by=By.XPATH,
                                                     value=f"""//a[contains(@href,'{href}')]""")
            except Exception as e:
                if retries == 0:
                    if optional:
                        pass
                    else:
                        raise e
                    break
                else:
                    pass
        return element

    @Driver.check_active
    @step(args=['url'])
    def get(self, url):
        if self._forwarder is not None:
            sshmanager.remove_forward(
                self._remotehost,
                self._urlparts.hostname,
                self._port
                )
            self._forwarder = None

        self._url = url
        self._urlparts = urlsplit(self._url)
        self._port = 443 if self._urlparts.scheme == "https" else 80
        proxy_port = sshmanager.request_forward(
                self._remotehost,
                self._urlparts.hostname,
                self._port
                )
        self._forwarder=f"""{self._urlparts.scheme}://localhost:{proxy_port}"""
        self._browser.get(self._forwarder)

    @Driver.check_active
    @step(args=['submit_element'])
    def submit_form(self, submit_element="cbi-button.cbi-button-save"):
        # click on the submit button
        self._get_element(submit_element, False, By.CLASS_NAME).click()

    @Driver.check_active
    @step(args=['cancel_element'])
    def cancel_form(self, cancel_element="cbi-button.cbi-button-cancel"):
        # click on the cancel button
        self._get_element(cancel_element, False, By.CLASS_NAME).click()

    @Driver.check_active
    @step(args=['form_element', 'value', 'optional'])
    def set_field(self, form_element, value, optional=False):
        # Set a field to a value on the form
        element = self._get_element(form_element, optional)
        if element is not None:
            element.clear()
            element.send_keys(value)

    @Driver.check_active
    @step(args=['form_element', 'value', 'optional'])
    def select_pulldown(self, form_element, value, optional=False):
        # Select one option from a pulldown list
        element = self._get_element(form_element, optional, By.ID)
        if element is not None:
            select = Select(element)
            select.select_by_visible_text(value)

    @Driver.check_active
    @step(args=['form_element', 'value', 'optional'])
    def select_radiobutton(self, form_element, value, optional=False):
        # Select a radio button on the form
        buttons = self._get_elements(form_element, optional, By.ID)
        if buttons is not None:
            # find the value and click it
            for idx in range(len(buttons)):
                if buttons[idx].get_attribute("value") == value:
                    if buttons[idx].is_selected() != True:
                        buttons[idx].click()
                        break

    @Driver.check_active
    @step(args=['form_element', 'value', 'optional'])
    def set_checkbox(self, form_element, value: bool, optional=False):
        # Check or uncheck a checkbox on the form
        element = self._get_element(form_element, optional)
        if element is not None:
            selected = element.is_selected()
            if selected != value:
                element.click()

    @Driver.check_active
    @step(args=['href', 'optional'])
    def click_link(self, href, optional=False):
        # Click on the first link with href in the link
        element = self._get_link(href, optional)
        if element is not None:
            element.click()
