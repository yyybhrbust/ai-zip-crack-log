# -*- coding: utf-8 -*-
"""Minimal AutoDL API client used by the benchmark scripts.

The JWT is read from the environment variable AUTODL_TOKEN (never hard-coded):

    Windows:  $env:AUTODL_TOKEN = "eyJ..."
    Linux:    export AUTODL_TOKEN="eyJ..."

How to obtain it: log in at https://autodl.com, open DevTools -> Network,
copy the `authorization` header of any /api/v1 request. It expires after
about 90 days.
"""
import json
import os

import paramiko
import requests

TOKEN = os.environ.get("AUTODL_TOKEN", "").strip()
if not TOKEN:
    raise SystemExit("set AUTODL_TOKEN first (see module docstring)")

S = requests.Session()
S.headers.update({
    "accept": "*/*",
    "appversion": "v6.51.1",
    "authorization": TOKEN,
    "content-type": "application/json;charset=UTF-8",
    "origin": "https://autodl.com",
    "referer": "https://autodl.com/market/list",
    "user-agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/155.0.0.0 Safari/537.36"),
})


def list_instances():
    r = S.post("https://autodl.com/api/v1/instance",
               json={"page_index": 1, "page_size": 50, "status": "", "charge_type": "payg"},
               timeout=40)
    return ((r.json().get("data") or {}).get("list") or [])


def create(machine, image, req_gpu=1):
    body = {"instance_info": {
        "machine_id": machine, "charge_type": "payg", "req_gpu_amount": req_gpu,
        "base_image_uuid": image.get("base_image_uuid", ""),
        "private_image_uuid": image.get("private_image_uuid", ""),
        "reproduction_uuid": image.get("reproduction_uuid", ""),
        "cg_application_uuid": "", "cg_application_info": {},
        "expand_data_disk": 0, "instance_name": "",
    }, "price_info": {"coupon_id_list": [], "machine_id": machine,
                      "charge_type": "payg", "duration": 1, "num": 1,
                      "expand_data_disk": 0}}
    return S.post("https://autodl.com/api/v1/order/instance/create/payg",
                  json=body, timeout=40)


def power_off(uuid):
    return S.post("https://autodl.com/api/v1/instance/power_off",
                  json={"instance_uuid": uuid}, timeout=40)


def power_on(uuid):
    return S.post("https://autodl.com/api/v1/instance/power_on",
                  json={"instance_uuid": uuid}, timeout=40)


def release(uuid):
    return S.post("https://autodl.com/api/v1/instance/release",
                  json={"instance_uuid": uuid}, timeout=40)


def run(client, cmd, timeout=120):
    """Run a shell command over SSH, return (stdout, stderr) as text."""
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    return out, err
