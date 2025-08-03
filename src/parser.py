import re
from bs4 import BeautifulSoup


def parseInvoicePage(page_source, txn_page):
    pageSoup = BeautifulSoup(page_source, "html.parser")
    txnSoup = BeautifulSoup(txn_page, "html.parser")

    itemSections = pageSoup.find_all(attrs={"data-component": "purchasedItems"})
    items = []

    for item in itemSections:
        try:
            itemName = item.find(attrs={"data-component": "itemTitle"}).text

            itemValue = float(
                item.find(attrs={"data-component": "unitPrice"})
                .span.contents[0]
                .text.strip()[1:]
            )

            qty = item.find(class_="od-item-view-qty")
            if qty:
                numItems = int(qty.text)
            else:
                numItems = 1

            items.append((itemName, itemValue * numItems))
        except Exception as e:
            print(f"Something went wrong processing item {item}: {e}")
            input("hit enter to bail...\n")
            exit(1)

    beforeTax = float(
        pageSoup.find(text=re.compile(r"Total before tax"))
        .find_parent(class_="a-row")
        .find(class_="od-line-item-row-content")
        .text.strip()[1:]
    )

    tax = float(
        pageSoup.find(text=re.compile(r"Estimated tax to be collected"))
        .find_parent(class_="a-row")
        .find(class_="od-line-item-row-content")
        .text.strip()[1:]
    )

    if beforeTax <= 0:
        print(f"Before tax value is less than or equal to 0, was {items} free?")
        return None, None
    taxPercent = tax / beforeTax
    afterTaxItems = [
        (i[0], int(100 * round(i[1] * (1 + taxPercent), 2))) for i in items
    ]

    # Then get "Credit Card Transactions"
    transactions = None
    ccTransactions = txnSoup.find("form", method="post")
    if ccTransactions == None:
        print(
            f"No Credit Card Transactions line item found, maybe {afterTaxItems} haven't been paid for yet"
        )
        return None, None

    transactions = ccTransactions.find_all(text=re.compile(r"\$\d+"))
    transactions = [int(float(t.strip()[2:]) * 100) for t in transactions]

    # while True:
    #     x = input("paused, soup it:\n")
    #     if x == "":
    #         break
    #     else:
    #         print(eval(x))

    return afterTaxItems, transactions

