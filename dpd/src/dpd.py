import json
import os
from datetime import datetime
from base64 import b64decode
from enum import Enum
from typing import Optional
from dataclasses import asdict, dataclass
import requests
from cryptography.fernet import Fernet
from src.mssql import Transaction
from src.pdf_merger import merge_labels
import fitz

# generated by Fernet.generate_key()
SECRET_KEY = b'BW9WgrjqWMoc_zjHmOTqtbpKQY5QuDeuTQwlDYp_DXI='


@dataclass
class Credentials:
    """
    DPD login data
    """
    # If True, use prod URL. Otherwise, use pre-prod URL.
    prod: bool
    # API login
    login: str
    # API Password
    password: str
    # Client ID. Sometimes called "masterfid".
    fid: str
    # Business unit code. In practice, its DPD country code. 021 for Poland.
    bucode: str = "021"

    @property
    def login_url(self):
        return ("https://api.dpdgroup.com/shipping/v1/login" if self.prod else
                "https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/login")

    @property
    def label_url(self):
        return ("https://api.dpdgroup.com/shipping/v1/shipment?LabelPrintFormat=PDF" if self.prod else
                "https://api-preprod.dpsin.dpdgroup.com:8443/shipping/v1/shipment?"
                "LabelPrintFormat=PDF")

    def to_file(self, filename: str):
        "Write credentials to the json file"
        creds = {}
        creds["login"] = Fernet(SECRET_KEY).encrypt(self.login.encode()).decode()
        creds["password"] = Fernet(SECRET_KEY).encrypt(self.password.encode()).decode()
        creds["fid"] = Fernet(SECRET_KEY).encrypt(self.fid.encode()).decode()
        creds["bucode"] = Fernet(SECRET_KEY).encrypt(self.bucode.encode()).decode()
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(creds, f)

    @staticmethod
    def from_file(filename: str, prod: bool):
        "Read secrets file. Decrypt it, and create Credentials instance"
        try:
            with open(filename, 'r', encoding="utf-8") as f:
                data = json.load(f)
            login = Fernet(SECRET_KEY).decrypt(data["login"].encode()).decode()
            password = Fernet(SECRET_KEY).decrypt(data["password"].encode()).decode()
            fid = Fernet(SECRET_KEY).decrypt(data["fid"].encode()).decode()
            bucode = Fernet(SECRET_KEY).decrypt(data["bucode"].encode()).decode()
            return Credentials(prod, login, password, fid, bucode)
        # TODO: better exception
        except Exception:
            return Credentials(prod, "", "", "")


@dataclass
class Address:
    """
    Sender/Receiver data. Class members names matches keys from DHL shipment dict.
    """
    companyName: str
    zipCode: str
    city: str
    street: str
    tel: str
    email: str
    country: str = "PL"
    name1: Optional[str] = None

    # TODO: move this arguments to members
    def to_dpd_json(self, fid: Optional[str], with_business_type: bool) -> dict:
        "Deserialize to json. bu_id stands for Business unit id."
        address = asdict(self)
        del address["tel"]
        dpd_json = {
            "address": address,
            "contact": {"phone1": self.tel, "email": self.email},
        }
        if not dpd_json["address"]["name1"]:
            del dpd_json["address"]["name1"]
        if fid:
            dpd_json["customerInfos"] = {
                "customerAccountNumber": fid, "customerID": fid}
        if with_business_type:
            dpd_json["legalEntity"] = {"businessType": "B"}

        return dpd_json


SENDER = Address(companyName="PCM Barossa", name1="Bartłomiej Sakowicz", city="Hipolitów",
                 street="Hipolitowska 102", zipCode="05-074", tel="227830175",
                 email="barossa@metaloplastyka.pl")


class ProductCode(Enum):
    """
    DPD product codes mapping.
    """
    NORMAL = "101"
    COD = "109"
    NEXTDAY = "155"
    NEXTDAY_COD = "161"


@dataclass
class ShipmentDetails:
    weight: str = "1.0"  # in kgs
    cod: bool = False
    next_day: bool = False
    receiver_second_name: str = ""

    def product_code(self):
        "Map cod and nextday booleans to ProductCode used by DPD"
        if self.cod and self.next_day:
            return ProductCode.NEXTDAY_COD
        if self.cod and not self.next_day:
            return ProductCode.COD
        if not self.cod and self.next_day:
            return ProductCode.NEXTDAY
        return ProductCode.NORMAL


@dataclass
class Shipment:
    receiver: Address
    sender: Address
    weight: float  # in kgs
    parcel_content: str
    product_code: ProductCode
    price: Optional[float] = None

    # TODO: move this arguments to members
    def to_dpd_json(self, fid: str) -> dict:
        """
        Tranform Shipment instance to a valid DPD json.
        """
        entry = {
            "shipmentInfos": {
                "productCode": self.product_code.value
            },
            "numberOfParcels": "1",
            "sender": self.sender.to_dpd_json(fid=fid, with_business_type=True),
            "receiver": self.receiver.to_dpd_json(fid=None, with_business_type=False),
            "parcel": [{
                "parcelInfos": {
                    "weight": str(int(self.weight * 1000))
                },
                "parcelContent": self.parcel_content
            }],
        }
        if self.product_code in (ProductCode.COD, ProductCode.NEXTDAY_COD):
            entry["parcel"][0]["cod"] = {"amount": {"amount": self.price, "currency": "PLN"}}

        return entry

    @staticmethod
    def from_transaction(trans: Transaction, details: ShipmentDetails):
        """
        Create Shipment instance from a transaction and shipment details.
        """
        # TODO: validate data, and raise if an exception occurs
        company_name = trans.client_name[:35]
        receiver = Address(companyName=company_name,
                           zipCode=trans.zip_code,
                           city=trans.city,
                           street=trans.address,
                           tel=trans.tel,
                           email=trans.email,
                           name1=details.receiver_second_name)
        return Shipment(receiver=receiver,
                        sender=SENDER,
                        weight=float(details.weight.replace(",", ".")),
                        parcel_content=trans.name,
                        product_code=details.product_code(),
                        price=trans.value)


def generate_labels(shipments: list[dict], credentials: Credentials) -> tuple[bytes, str]:
    """
    Login to DPD API. Make a label creation request using login token.
    Save generated label in PDF file. Return preview of one label and path to PDF file.
    """
    login_body = {
        "X-DPD-LOGIN":   	credentials.login,
        "X-DPD-PASSWORD": 	credentials.password,
        "X-DPD-BUCODE":   	credentials.bucode
    }

    ret = requests.post(credentials.login_url, headers=login_body)
    if ret.status_code != 200:
        # TODO: Some custom exception
        raise Exception(ret.text)
    token = ret.headers['X-DPD-TOKEN']
    headers = {
        'Authorization': f'Bearer {token}',
    }

    b64_labels = []
    # After the last DPD update (version 1.34.11) DPD removed support of multi-shipment requests.
    # But at the same time, they still require list of shipments in the API,
    # which has to be one-elemented :clown-face:
    for shipment in shipments:
        ret = requests.post(credentials.label_url, headers=headers, json=[shipment])
        if ret.status_code != 200:
            # TODO: Some custom exception
            raise Exception(ret.text)
        b64_labels.append(ret.json()["label"]["base64Data"])
    windows_friendly_date = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filepath = os.path.abspath(os.path.join("labels", f"{windows_friendly_date}.pdf"))
    merge_labels(b64_labels, filepath)

    # TODO: this preview should be done better, with paging or sth
    doc = fitz.open(filepath)
    pixmap = doc.load_page(0).get_pixmap()
    one_label = fitz.Pixmap(pixmap, pixmap.width, pixmap.height,
                            fitz.IRect(0,  0, int(pixmap.width / 2), int(pixmap.height / 2)))
    png_data = one_label.tobytes("png")
    return png_data, filepath
