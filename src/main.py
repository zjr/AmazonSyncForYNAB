import argparse
import configparser
import parser
from datetime import date, timedelta

import matcher
from amazon_client.amazon_selenium_client import AmazonSeleniumClient
from ynab_client import YNABClient

ap = argparse.ArgumentParser(
    prog="AmazonSyncToYNAB",
    description="Visits your Amanzon account, finds transactions and adds info to the memo in YNAB.",
)

ap.add_argument("--debug", action="store_true")
args = ap.parse_args()

# TODO: Use encrypted secrets config
config = configparser.ConfigParser()
config.read("secrets/credentials.ini")
myConfig = config["DEFAULT"]
otpSecret = myConfig["otpSecret"]
userEmail = myConfig["userEmail"]
userPassword = myConfig["userPassword"]
ynabToken = myConfig["ynabToken"]


def main(amazonClient):
    orderIDs = amazonClient.getAllOrderIDs(3)
    amazonT = []
    for orderID in orderIDs:
        try:
            iPage = amazonClient.getInvoicePage(orderID)
            afterTaxItems, transactions = parser.parseInvoicePage(iPage)
            if afterTaxItems is None or transactions is None:
                continue
            matched = matcher.matchAmazonTransactions(afterTaxItems, transactions)
            amazonT.append(matched)
        except Exception as e:
            print(f"Something went wrong processing order {orderID}: {e}")
    myYNAB = YNABClient(ynabToken)
    ynabT = myYNAB.list_recent_amazon_transactions(date.today() - timedelta(days=30))
    transactions = matcher.matchAmazonToYNAB(amazonT, ynabT)
    myYNAB.patch_transactions(transactions)


if __name__ == "__main__":
    amazonSeleniumClient = AmazonSeleniumClient(
        userEmail, userPassword, otpSecret, args
    )
    main(amazonSeleniumClient)
