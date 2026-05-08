import httpx, json, sys

docs = [
    ("electricity_jan.txt", b"BESCOM Bill\nDue Date: 15 Jan 2026\nAmount Due: Rs. 2450\nBilling Period: January 2026"),
    ("rent_feb.txt",        b"Rent Receipt\nMonthly Rent: Rs 8000\nFor the month of: February 2026\nPayment Date: 01 Feb 2026"),
    ("upi_mar.txt",         b"Google Pay\nPayment Successful\nAmount: Rs 3500 received\nDate: 20 Mar 2026"),
]

files = [("files", (name, content, "text/plain")) for name, content in docs]
meta  = [
    {"id": f"f{i}", "filename": name, "mimeType": "text/plain",
     "tag": ["Utility Bill", "Receipt", "UPI Screenshot"][i]}
    for i, (name, _) in enumerate(docs)
]

data = {"metadata": json.dumps(meta), "whatsappText": ""}

try:
    r = httpx.post("http://127.0.0.1:8000/parse", files=files, data=data, timeout=20)
except Exception as e:
    print("Connection error:", e)
    sys.exit(1)

print("HTTP Status:", r.status_code)

if r.status_code != 200:
    print("Error body:", r.text[:1000])
    sys.exit(1)

resp = r.json()
print("consistencyScore:     ", resp.get("consistencyScore"))
print("averageMonthlyIncome: ", resp.get("averageMonthlyIncome"))
print("totalIncome:          ", resp.get("totalIncome"))
print("months:               ", resp.get("months"))
print("transactions count:   ", len(resp.get("transactions", [])))
print("flags:                ", resp.get("flags"))
print()
for t in resp.get("transactions", []):
    print(f"  {t.get('source'):12} | {t.get('date')} | Rs.{t.get('amount')} | {t.get('transaction_type')}")
