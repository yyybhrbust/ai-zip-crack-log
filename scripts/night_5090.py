# -*- coding: utf-8 -*-
"""凌晨自动抢 RTX 5090 -> 实测 ZIP-opencl 速度 -> 关机 -> 写入 Word。

用法:
    python night_5090.py            # 正常跑（默认 04:30 前一直抢，抢到即测）
    python night_5090.py --dry      # 只看盘面，不创建
    python night_5090.py --deadline 04:30
"""
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, r"D:\crack-log\src")
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import paramiko

from autodl_client import S, list_instances, run

BASE = r"D:\crack-log"
SRC = os.path.join(BASE, "src")
LOG = os.path.join(SRC, "night_5090.log")
TAR = r"D:\john-src.tar.gz"
GEN_SH = (
    "{ printf '$zip2$*0*3*0*'; printf '11%.0s' $(seq 16); "
    "printf '*7b75*88f88ce*'; head -c 143624398 /dev/urandom | "
    "od -An -v -tx1 | tr -d ' \\n'; "
    "printf '*5e643f339fa77b9b62e3*$/zip2$'; } > /root/bench.txt"
)
IMAGES = [
    {"base_image_uuid": "", "private_image_uuid": "image-e0b0bb8f9d", "reproduction_uuid": ""},
    {"base_image_uuid": "", "private_image_uuid": "", "reproduction_uuid": "RVC-Boss/GPT-SoVITS/GPT-SoVITS:v9.0"},
]
GPU = "RTX 5090"
PRICE = 3.14


def log(m):
    line = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(line, flush=True)
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def market():
    body = {"page_index": 1, "page_size": 200, "gpu_type_name": [GPU],
            "gpu_idle_num": 0, "region_sign_list": [], "charge_type": "payg"}
    r = S.post("https://autodl.com/api/v1/user/machine/list", json=body, timeout=40)
    return ((r.json().get("data") or {}).get("list") or [])


def create(machine, img, req_gpu=1):
    body = {"instance_info": {
        "machine_id": machine, "charge_type": "payg", "req_gpu_amount": req_gpu,
        "base_image_uuid": img["base_image_uuid"],
        "private_image_uuid": img["private_image_uuid"],
        "reproduction_uuid": img["reproduction_uuid"],
        "cg_application_uuid": "",
        "cg_application_info": {"image_name": "", "current_version_id": 0,
                                "current_version": "", "image_id": 0},
        "instance_name": "", "expand_data_disk": 0, "reproduction_id": 0},
        "price_info": {"coupon_id_list": [], "machine_id": machine,
                       "charge_type": "payg", "duration": 1, "num": 1,
                       "expand_data_disk": 0}}
    r = S.post("https://autodl.com/api/v1/order/instance/create/payg", json=body, timeout=40)
    return r


def uuid_of(resp_json):
    d = (resp_json or {}).get("data")
    if isinstance(d, dict):
        return d.get("instance_uuid") or d.get("uuid")
    if isinstance(d, str):
        return d
    return None


def power_off(uuid):
    try:
        r = S.post("https://autodl.com/api/v1/instance/power_off",
                   json={"instance_uuid": uuid}, timeout=40)
        log("power_off %s -> %s" % (uuid, r.text[:80]))
    except Exception as ex:
        log("power_off err %r" % (ex,))


def release(uuid):
    try:
        r = S.post("https://autodl.com/api/v1/instance/release",
                   json={"instance_uuid": uuid}, timeout=40)
        log("release %s -> %s" % (uuid, r.text[:80]))
    except Exception as ex:
        log("release err %r" % (ex,))


def wait_running(uuid, timeout=900):
    t0 = time.time()
    last = None
    while time.time() - t0 < timeout:
        it = next((i for i in list_instances() if i.get("uuid") == uuid), None)
        if it:
            st = it.get("status")
            if st != last:
                log("  state=%s pull=%s" % (st, it.get("pull_image_progress")))
                last = st
            if st == "running" and it.get("ssh_port"):
                return it
            if st == "shutdown_by_starting_error":
                return None
        time.sleep(12)
    return None


def bench(it):
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    for _ in range(8):
        try:
            c.connect(it["proxy_host"], port=it["ssh_port"], username="root",
                      password=it["root_password"], timeout=30,
                      banner_timeout=120, auth_timeout=120)
            break
        except Exception as ex:
            log("ssh retry %r" % (ex,))
            time.sleep(15)
    log("ssh ok")
    o, e = run(c, "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq >/tmp/a1 2>&1; "
                    "apt-get install -y -qq ocl-icd-opencl-dev opencl-headers build-essential "
                    ">/tmp/a2 2>&1; echo rc=$?; ls /usr/include/CL/cl.h 2>&1", 1200)
    log("apt: " + (o + e).strip().replace("\n", " | ")[:160])
    run(c, "mkdir -p /etc/OpenCL/vendors; [ -e /etc/OpenCL/vendors/nvidia.icd ] || "
             "echo libnvidia-opencl.so.1 > /etc/OpenCL/vendors/nvidia.icd", 60)
    need_build = True
    o, _ = run(c, "test -x /root/john-src/run/john && "
                    "cd /root/john-src/run && ./john --list=formats 2>/dev/null | grep -ci opencl || true", 120)
    log("existing opencl formats: %s" % (o or "").strip())
    if (o or "").strip().isdigit() and int((o or "0").strip()) > 0:
        need_build = False
    if need_build:
        t0 = time.time()
        sftp = c.open_sftp()
        sftp.put(TAR, "/root/john.tar.gz")
        sftp.close()
        log("uploaded john src %.0f MB in %.0fs" % (os.path.getsize(TAR) / 1e6, time.time() - t0))
        o, e = run(c, "mkdir -p /root/john-src && tar xzf /root/john.tar.gz -C /root/john-src "
                        "--strip-components=1 && cd /root/john-src/src && ./configure >/tmp/cfg 2>&1; "
                        "echo cfg=$?; make -j$(nproc) >/tmp/mk 2>&1; echo make=$?; "
                        "ls -l /root/john-src/run/john", 2400)
        log("build: " + (o + e).strip().replace("\n", " | ")[-200:])
    o, e = run(c, "cd /root/john-src/run && ./john --list=formats | tr ',' '\\n' | grep -i zip | head -5", 120)
    log("zip formats: " + " ".join((o + e).split())[:160])
    t0 = time.time()
    o, e = run(c, "time " + GEN_SH + "; ls -l /root/bench.txt", 1800)
    log("gen %.0fs: %s" % (time.time() - t0, (o + e).strip().splitlines()[-1][:100]))
    t0 = time.time()
    o, e = run(c, "cd /root/john-src/run && timeout 240 ./john --format=ZIP-opencl "
                    "--mask='?l?l?l?l?l?l?l' --progress-every=15 --session=bench "
                    "--pot=/root/bench.pot /root/bench.txt 2>&1 | tail -12", 420)
    log("run %.0fs" % (time.time() - t0))
    for line in (o + e).strip().splitlines()[-4:]:
        log("  J " + line[:140])
    speeds = re.findall(r"([\d.]+)([KMG]?)p/s", o)
    ps = 0.0
    if speeds:
        mult = {"": 1, "K": 1e3, "M": 1e6, "G": 1e9}
        ps = float(speeds[-1][0]) * mult[speeds[-1][1]]
    c.close()
    return ps


def record(ps, price, uuid, machine):
    res = {"gpu": GPU, "uuid": uuid, "machine": machine, "price": price,
           "zip_opencl_real_ps": round(ps), "ratio_vs_4090d": round(ps / 6.27e6, 2),
           "at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(SRC, "gpu_bench_rtx5090.json"), "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    log("RESULT " + json.dumps(res, ensure_ascii=False))

    path = os.path.join(SRC, "gpu_results.json")
    data = {"rows": []}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    rows = [r for r in data.get("rows", []) if r.get("name") != GPU]
    wan = ps / 1e4
    yuan = ps / price / 1e4
    note = ("%s 实测 %s 万/秒（4090D 的 %.2f 倍、4090 的 %.2f 倍）；¥%.2f/h 对应每元吞吐 %s 万，"
            "是 4090 的 %d%%、4090D 的 %d%%。"
            % (GPU, "{:,.0f}".format(wan), ps / 6.27e6, ps / 8.955e6, price,
               "{:,.0f}".format(yuan), 100 * yuan / (8.955e6 / 2.08 / 1e4),
               100 * yuan / (6.27e6 / 1.98 / 1e4)))
    rows.append({"name": GPU, "mem": "32 GB", "speed_ps": round(ps), "price": price,
                 "note": note, "at": time.strftime("%Y-%m-%d")})
    data["rows"] = sorted(rows, key=lambda r: -r.get("speed_ps", 0))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    log("gpu_results.json updated")

    build = os.path.join(SRC, "build_cracklog.py")
    doc = os.path.join(BASE, "AI.zip破解尝试汇总.docx")
    p = subprocess.run([sys.executable, build], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    if p.returncode != 0:
        staging = os.path.join(SRC, "_night_staging.docx")
        log("rebuild failed (%s), retry to staging" % ((p.stderr or "").strip()[-120:],))
        p = subprocess.run([sys.executable, build, staging], capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if p.returncode == 0:
            doc = staging
    log("rebuild: %s %s" % (p.returncode, (p.stdout or "").strip()[:120]))
    chk = os.path.join(SRC, "check_any_doc.py")
    p = subprocess.run([sys.executable, chk, doc],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    log("check: " + (p.stdout or "").strip().replace("\n", " | ")[:200])


def restore_power():
    """Put the AC standby timeout back to 180 min (the original value)."""
    try:
        subprocess.run(["powercfg", "/change", "standby-timeout-ac", "180"],
                       capture_output=True, timeout=30)
        log("power: standby-timeout-ac restored to 180")
    except Exception as ex:
        log("power restore failed %r" % (ex,))


def main():
    try:
        _main()
    finally:
        restore_power()


def _main():
    dry = "--dry" in sys.argv
    deadline = "08:00"
    if "--deadline" in sys.argv:
        deadline = sys.argv[sys.argv.index("--deadline") + 1]
    hh, mm = [int(x) for x in deadline.split(":")]
    start = time.time()
    now = time.localtime()
    end = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, hh, mm, 0, 0, 0, -1))
    if end <= start:
        # started late (e.g. laptop woke up after the deadline): still give it 90 minutes
        end = start + 90 * 60
    cap = start + 6 * 3600  # never run longer than 6 hours
    hard = time.mktime((now.tm_year, now.tm_mon, now.tm_mday, 11, 30, 0, 0, 0, -1))
    if hard <= start:
        hard = cap  # started after 11:30 today: just cap by duration
    end = min(end, cap, hard)  # nothing may still be running past 11:30
    log("=== night_5090 start, deadline %s (%.0f min) dry=%s" % (deadline, (end - time.time()) / 60, dry))

    black = {}  # machine_id -> unix time before which we skip it
    uuid = None
    it = None
    n = 0
    while time.time() < end and not uuid:
        lst = market()
        now_t = time.time()
        cand = [m for m in lst if (m.get("gpu_idle_num") or 0) > 0
                and black.get(m.get("machine_id"), 0) < now_t]
        cand.sort(key=lambda m: ((m.get("payg_price") or 9999), -(m.get("gpu_idle_num") or 0)))
        near = (end - now_t) < 1800
        take = 4 if near else 2
        log("cycle %d: idle=%d trying=%d left=%.0fmin" %
            (n, len(cand), min(take, len(cand)), (end - now_t) / 60))
        for m in cand[:take]:
            mid = m.get("machine_id")
            for img in IMAGES:
                if dry:
                    log("  [dry] would create on %s price=%s idle=%s" %
                        (mid, (m.get("payg_price") or 0) / 1000, m.get("gpu_idle_num")))
                    continue
                r = create(mid, img)
                txt = r.text[:160].replace("\n", " ")
                log("  create %s %s -> %s %s" % (mid, (img["private_image_uuid"] or "repro"),
                                                 r.status_code, txt))
                if r.status_code == 200 and '"code":"Success"' in r.text:
                    uuid = uuid_of(r.json())
                    if uuid:
                        it = m
                        break
                if ("存储库存已满" in r.text or "已租满" in r.text
                        or "MachineGpuNumUpdateFailed" in r.text):
                    black[mid] = time.time() + 600  # retry this machine in 10 min
                    break
            if uuid:
                break
        n += 1
        if dry:
            break
        if not uuid:
            time.sleep(20 if near else 45)

    if dry:
        log("dry-run done")
        return
    if not uuid:
        log("no 5090 available before deadline, give up")
        return

    log("created %s on %s" % (uuid, (it or {}).get("machine_id")))
    ps = 0
    try:
        info = wait_running(uuid)
        if not info:
            log("instance never became running, releasing")
            power_off(uuid)
            time.sleep(5)
            release(uuid)
            return
        price = (info.get("payg_price") or 0) / 1000 or PRICE
        log("running: %s %s price=%.2f" % (info.get("snapshot_gpu_alias_name"), info.get("proxy_host"), price))
        ps = bench(info)
    except Exception as ex:
        log("bench error %r" % (ex,))
    finally:
        # billing safety: never leave an instance running, whatever happened above
        power_off(uuid)
    if ps and ps > 1e6:
        record(ps, price, uuid, info.get("machine_id"))
    else:
        log("bench failed (ps=%s), nothing written" % ps)


if __name__ == "__main__":
    main()
