import platform
import time

import pyotp
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

from amazon_client.amazon_client import AmazonClient

ORDERS_PAGE = "https://www.amazon.com/gp/css/summary/print.html/ref=ppx_yo_dt_b_invoice_o00?ie=UTF8&orderID={}"


class AmazonSeleniumClient(AmazonClient):
    def __init__(self, userEmail, userPassword, otpSecret):
        self.userEmail = userEmail
        self.userPassword = userPassword
        self.otpSecret = otpSecret
        platformMachine = platform.machine()
        if platformMachine == "armv7l":
            # TODO: Raspberry Pi: Support this somehow. Webdriver installation needs to be bespoke
            err = "Platform {} not yet supported".format(platformMachine)
            print(err)
            exit(0)
        else:
            print(
                f"Attempting to initialize Chrome Selenium Webdriver on platform {platformMachine}..."
            )
            options = ChromeOptions()
            options.add_argument("--headless")
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=options,
            )
            print("Successfully initialized Chrome Selenium Webdriver")

        self.signIn()

    def getAllOrderIDs(self, pages=1):
        orderPage = "https://www.amazon.com/gp/your-account/order-history/ref=ppx_yo_dt_b_pagination_1_2?ie=UTF8&orderFilter=months-6&search=&startIndex={}"
        orderIDs = []
        for pageNumber in range(pages):
            self.driver.get(orderPage.format(pageNumber * 10))
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            orderIDs.extend([i.getText() for i in soup.find_all("bdi")])
        return orderIDs

    def doSignIn(self):
        # TODO: Wait for page load instead of sleeping so much
        totp = pyotp.TOTP(self.otpSecret)

        self.driver.get("https://amazon.com")
        time.sleep(1)
        accountNav = self.driver.find_element(By.XPATH, "//a[@data-nav-role ='signin']")
        accountNav.click()
        time.sleep(1)

        emailEntry = self.driver.find_element(By.ID, "ap_email")
        emailEntry.clear()
        emailEntry.send_keys(self.userEmail)
        self.driver.find_element(By.ID, "continue").click()

        time.sleep(1)

        passwordEntry = self.driver.find_element(By.ID, "ap_password")
        passwordEntry.clear()
        passwordEntry.send_keys(self.userPassword)
        self.driver.find_element(By.NAME, "rememberMe").click()
        self.driver.find_element(By.ID, "signInSubmit").click()

        time.sleep(1)

        totpSelect = self.driver.find_element(
            By.XPATH, "//input[contains(@value,'TOTP')]"
        )
        totpSelect.click()

        sendCode = self.driver.find_element(By.XPATH, "//input[@id = 'auth-send-code']")
        sendCode.click()

        time.sleep(1)

        otpEntry = self.driver.find_element(By.ID, "auth-mfa-otpcode")
        otpEntry.clear()
        otpEntry.send_keys(totp.now())
        self.driver.find_element(By.ID, "auth-mfa-remember-device").click()
        self.driver.find_element(By.ID, "auth-signin-button").click()
        time.sleep(1)

    def signIn(self):
        try:
            self.doSignIn()
        except:
            print("Amazon sign-in failed. Dumping page source to pagedump.txt")
            with open("pagedump.txt", "w") as f:
                f.write(self.driver.page_source)
            self.interpretDriverErrorPage()
            exit(1)

    def interpretDriverErrorPage(self):
        try:
            failElem = self.driver.find_element(
                By.XPATH, "//*[contains(text(),'not a robot')]"
            )
            print(
                "Blocked by Amazon anti-robot. Circumnavigating this is unsupported. Please try again later."
            )
        except:
            pass

    def getInvoicePage(self, orderID):
        myOrderPage = ORDERS_PAGE.format(orderID)
        self.driver.get(myOrderPage)
        return self.driver.page_source
