"""
Lexbot lambda handler
"""

import requests
import json


def getAuth():
    client_id = r'l7xx37d79b1fc1524123a34c51e361cb3a0e'
    client_secret = r'15880948e2bb41d79cfd563ba5012ab4'
    redirect_uri = 'https://your.callback/uri'
    scope = "CITYGUIDES DCIOFFERS DCIOFFERS_POST DCILOUNGES DCILOUNGES_POST DCILOUNGES_PROVIDER_LG DCILOUNGES_PROVIDER_DCIPL DCI_ATM DCI_CURRENCYCONVERSION DCI_CUSTOMERSERVICE DCI_TIP"

    url = "https://apis.discover.com/auth/oauth/v2/token"

    payload = 'grant_type=client_credentials&scope=CITYGUIDES%20DCIOFFERS%20DCIOFFERS_POST%20DCILOUNGES%20DCILOUNGES_POST%20DCILOUNGES_PROVIDER_LG%20DCILOUNGES_PROVIDER_DCIPL%20DCI_ATM%20DCI_CURRENCYCONVERSION%20DCI_CUSTOMERSERVICE%20DCI_TIP'

    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic bDd4eDM3ZDc5YjFmYzE1MjQxMjNhMzRjNTFlMzYxY2IzYTBlOjE1ODgwOTQ4ZTJiYjQxZDc5Y2ZkNTYzYmE1MDEyYWI0'
    }

    response = requests.request("POST", url, data=payload, headers=headers)

    json_dict = json.loads(response.text)
    print(json_dict)
    print(response.text)

    return json_dict


def lambda_handler(event, context):
    auth_dict = getAuth()

    location = event['currentIntent']['slots']['Location']
    offers_url = 'https://api.discover.com/dci-offers/v2/offers'

    auth_payload = "destination={0}&radius=20&lang=en&x-dfs-api-plan=DCIOFFERS_SANDBOX&undefined=".format(location)
    auth_headers = {
        'Accept': "application/json",
        'x-dfs-api-plan': "DCIOFFERS_SANDBOX",
        'Authorization': "Bearer {0}".format(auth_dict['access_token']),
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
        'cache-control': "no-cache",
        'Postman-Token': "68cf694d-4629-4bad-ac66-daf94c10b6f7"
    }

    auth_response = requests.request("GET", offers_url, data=auth_payload, headers=auth_headers)

    print(auth_response.text)
    return auth_response.text



