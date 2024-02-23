from dataclasses import dataclass
from typing import Optional
import pymssql


@dataclass(slots=True)
class Transaction:
    "Class representing transaction from SubiektGT/GestorGT CRM"
    # Tech fields
    id: int
    addr_type: int

    # User fields
    client_symbol: str
    name: str
    value: float
    client_name: str
    email: str
    tel: str
    address: str
    zip_code: str
    city: str

    def validate(self) -> bool:
        return bool(self.name and self.client_name and self.email
                    and self.tel and self.address and self.zip_code and self.city)


def refresh_transaction(old_trans: Transaction) -> Transaction:
    """
    Get a new version of an old transaction from the database.
    """
    conn = pymssql.connect(server="127.0.0.1:50845", user="sa", password="",
                           database="DATABASE_NAME", charset="CP1250")
    cursor = conn.cursor(as_dict=True)
    transactions_query = """
    select tr_Id, tr_Nazwa, kh_Symbol, kh_EMail, dok_WartBrutto, adr_Nazwa, adr_Telefon, adr_Adres, adr_Kod, adr_Miejscowosc, adr_TypAdresu
    from tr__Transakcja
    inner join dok__Dokument on tr__Transakcja.tr_Oferta=dok__Dokument.dok_Id
    inner join kh__Kontrahent on dok__Dokument.dok_OdbiorcaId=kh__Kontrahent.kh_Id
    inner join adr__Ewid on kh__Kontrahent.kh_Id=adr__Ewid.adr_IdObiektu
    where tr_Id = %d and adr_TypAdresu = %d
    """
    cursor.execute(transactions_query, (old_trans.id, old_trans.addr_type))
    results = cursor.fetchall()
    assert len(results) == 1
    new_trans = results[0]
    return Transaction(id=new_trans["tr_Id"],
                       addr_type=new_trans["adr_TypAdresu"],
                       name=new_trans["tr_Nazwa"].strip(),
                       value=float(new_trans["dok_WartBrutto"]),
                       client_symbol=new_trans["kh_Symbol"].strip(),
                       client_name=new_trans["adr_Nazwa"].strip(),
                       email=new_trans["kh_EMail"].strip(),
                       tel=new_trans["adr_Telefon"].strip()[:30],
                       address=new_trans["adr_Adres"].strip(),
                       zip_code=new_trans["adr_Kod"].strip(),
                       city=new_trans["adr_Miejscowosc"].strip()
                       )


def get_active_transactions() -> list[Transaction]:
    """
    Get transactions from SQL database that are not finished yet. It uses database schema used by
    Insert programs like SubiektGT or GestorGT. This function selects only those fields that might
    be useful for DPD shipping API. It prefers delivery address over normal address.
    """
    # TODO: make these credentials configurable. These are example ones
    conn = pymssql.connect(server="127.0.0.1:50845", user="sa", password="",
                           database="DATABASE_NAME", charset="CP1250")
    cursor = conn.cursor(as_dict=True)
    transactions_query = """
    select tr_Id, tr_Nazwa, kh_Symbol, kh_EMail, dok_WartBrutto, adr_Nazwa, adr_Telefon, adr_Adres, adr_Kod, adr_Miejscowosc, adr_TypAdresu
    from tr__Transakcja
    inner join dok__Dokument on tr__Transakcja.tr_Oferta=dok__Dokument.dok_Id
    inner join kh__Kontrahent on dok__Dokument.dok_OdbiorcaId=kh__Kontrahent.kh_Id
    inner join adr__Ewid on kh__Kontrahent.kh_Id=adr__Ewid.adr_IdObiektu
    where tr_Status = 0 and (adr_TypAdresu = 1 or adr_TypAdresu = 11)
    """
    cursor.execute(transactions_query)
    results = cursor.fetchall()
    transactions = []
    for trans in results:
        # Prefer address of type 11 (delivery address) over default address.
        # But ignore it if its empty.
        if trans["adr_TypAdresu"] == 1:
            twin_trans = [t for t in results if t["adr_TypAdresu"] == 11 and
                          t["tr_Id"] == trans["tr_Id"]]
            if twin_trans and twin_trans[0]["adr_Nazwa"] and twin_trans[0]["adr_Kod"]:
                continue
        if trans["adr_TypAdresu"] == 11 and not trans["adr_Nazwa"] and ["adr_Kod"]:
            continue
        elif trans["adr_TypAdresu"] == 11 and trans["adr_Nazwa"] and ["adr_Kod"]:
            trans["adr_Telefon"] = [t for t in results if t["adr_TypAdresu"] == 1 and
                                    t["tr_Nazwa"] == trans["tr_Nazwa"]][0]["adr_Telefon"]
        transactions.append(
            Transaction(id=trans["tr_Id"],
                        addr_type=trans["adr_TypAdresu"],
                        name=trans["tr_Nazwa"].strip(),
                        value=float(trans["dok_WartBrutto"]),
                        client_symbol=trans["kh_Symbol"].strip(),
                        client_name=trans["adr_Nazwa"].strip(),
                        email=trans["kh_EMail"].strip(),
                        tel=trans["adr_Telefon"].strip()[:30],
                        address=trans["adr_Adres"].strip(),
                        zip_code=trans["adr_Kod"].strip(),
                        city=trans["adr_Miejscowosc"].strip()
                        )
        )

    return transactions
