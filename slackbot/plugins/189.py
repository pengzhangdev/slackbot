#! /usr/bin/env python
#
# 189.py ---
#
# Filename: 189.py
# Description:
# Author: Werther Zhang
# Maintainer:
# Created: Tue Oct 11 17:27:24 2016 (+0800)
#

# Change Log:
#
#


# -*- coding: utf-8 -*-

import time
import requests
import json
from slackbot.bot import tick_task

next_time = 0
cached_number = list()

request_url = "http://www.189.cn/sales/basedata/combonumber.do?systemType=1&salesProdId=00000000275F29724FBD182EE053AA1410AC7DA8&shopId=10036&comboDetailsId=&channelId=&pageindex=%d&pagesize=32&areacode=8330300&minpay=&prettypattern=&contnumber=&cacheId=&maxPage=78&numbertype=0&phoneNumMinExpense=&subPhoneNumMinExpense=&phoneNumPrestoreExpense=&mall_price=0.00&fourFlag=1&minExpenseCloud=&inflag=0&lastFlag=0&headNumber=%d&sortby=1&type=&numberLevel=&innumber=&maxpay=&_=1476067368536"


def send_request(url):
    some_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/52.0.2743.116 Safari/537.36'
    response = requests.get(url, headers={'User-Agent': some_agent}, timeout=10)
    results = response.json()
    data_obj = results.get('dataObject', {})
    querystatus = data_obj.get('querystatus', 0)
    listphones = data_obj.get('listphones', [])

    return (querystatus, listphones)

def parse_number(phonelist):
    global cached_number

    phone_number = list()
    for phone in phonelist:
        number = phone.get('phoneNumber', 0)
        if number in cached_number:
            continue
        cached_number.append(number)
        phone_number.append(number)

    return phone_number

def get_phone_number():
    numbers = list()

    querystatus, listphones = send_request(request_url % (1, 189))
    if querystatus != 0:
        numbers += parse_number(listphones)

    querystatus, listphones = send_request(request_url % (1, 181))
    if querystatus != 0:
        numbers += parse_number(listphones)

    querystatus, listphones = send_request(request_url % (1, 180))
    if querystatus != 0:
        numbers += parse_number(listphones)

    return numbers

@tick_task
def work(message):
    global next_time
    now = time.time()
    if now < next_time:
        return
    next_time = now + 30*60

    numbers = get_phone_number()
    if len(numbers) == 0:
        return
    message.send_to('werther0331', '189 phone numbers: {}'.format(' '.join(numbers)))
