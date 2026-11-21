#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WinZip AES ($zip2$) 快速筛选 / 破解脚本

原理（已用 hashcat 官方 13600 示例验证）：
  dk    = PBKDF2-HMAC-SHA1(口令, salt, 1000, 2*keylen+2)
  key1  = dk[0:keylen]        AES 密钥
  key2  = dk[keylen:2*keylen] HMAC 密钥
  ver   = dk[-2:]             WinZip 的 16 位“密码校验值”
  auth  = HMAC-SHA1(key2, 整段密文)[:10]
每个候选只算 PBKDF2（1000 次 SHA1）并比对 ver，命中的概率约 1/65536；
只有这些极少数候选才需要对 143MB 密文算 HMAC 做最终确认。

为什么不能直接用 hashcat：hashcat -m 13600 要求把整段密文写进 hash 行，
data 上限 0x200000*4 字节（8 MiB）、compress_length 上限 0xFFFFFF（6 位十六进制），
本条目 compress_length 是 7 位、data 是 143MB，解析阶段就失败。

用法：
  python zip2_crack.py hash.txt rockyou.txt
  python zip2_crack.py hh.txt rockyou.txt --workers 8 --out hits.txt
  python zip2_crack.py hash.txt rockyou.txt --limit 2000     # 只跑前 2000 行，测速
"""

import argparse
import hashlib
import hmac
import multiprocessing as mp
import os
import sys
import time
from binascii import unhexlify

KEYLEN = {1: 16, 2: 24, 3: 32}
ROUNDS = 1000

SALT = None
VERIFY = None
DKLEN = None


def parse_hash(path):
    with open(path, "rb") as f:
        line = f.readline()
    s = line.find(b"$zip2$")
    e = line.find(b"$/zip2$")
    if s < 0 or e < 0:
        sys.exit("找不到 $zip2$ ... $/zip2$ 标记")
    h = line[s:e + 7].decode("ascii")
    t = h.split("*")
    if len(t) != 10 or t[0] != "$zip2$" or t[-1] != "$/zip2$":
        sys.exit("hash 字段数不对：%d" % len(t))
    mode = int(t[2])
    salt = unhexlify(t[4])
    verify = unhexlify(t[5])
    data = unhexlify(t[7]) if t[7] else b""
    auth = unhexlify(t[8])
    return h, mode, salt, verify, data, auth


def _init(salt, verify, dklen):
    global SALT, VERIFY, DKLEN
    SALT, VERIFY, DKLEN = salt, verify, dklen


def _work(chunk):
    hits = []
    salt, verify, dklen = SALT, VERIFY, DKLEN
    for pw in chunk:
        pw = pw.rstrip(b"\r\n")
        if not pw:
            continue
        dk = hashlib.pbkdf2_hmac("sha1", pw, salt, ROUNDS, dklen)
        if dk[-2:] == verify:
            hits.append(pw)
    return hits


def read_chunks(path, limit, size):
    with open(path, "rb") as f:
        chunk = []
        n = 0
        for line in f:
            chunk.append(line)
            n += 1
            if len(chunk) >= size:
                yield chunk
                chunk = []
            if limit and n >= limit:
                yield chunk
                return
        if chunk:
            yield chunk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("hashfile")
    ap.add_argument("wordlist")
    ap.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 4) - 1))
    ap.add_argument("--out", default="hits.txt")
    ap.add_argument("--limit", type=int, default=0, help="只处理前 N 行（0 = 全部）")
    ap.add_argument("--chunk", type=int, default=500)
    args = ap.parse_args()

    h, mode, salt, verify, data, auth = parse_hash(args.hashfile)
    keylen = KEYLEN.get(mode)
    if keylen is None:
        sys.exit("未知 mode: %r" % mode)
    dklen = 2 * keylen + 2

    print("mode      : %d (AES-%d)" % (mode, keylen * 8))
    print("salt      : %s" % salt.hex())
    print("verify    : %s" % verify.hex())
    print("data bytes: %d" % len(data))
    print("auth      : %s" % auth.hex())
    print("workers   : %d" % args.workers)

    pool = mp.Pool(args.workers, initializer=_init, initargs=(salt, verify, dklen))
    t0 = time.time()
    done = 0
    found = []
    last = t0

    for hits in pool.imap_unordered(_work, read_chunks(args.wordlist, args.limit, args.chunk)):
        done += args.chunk
        for pw in hits:
            ok = False
            if data:
                key2 = hashlib.pbkdf2_hmac("sha1", pw, salt, ROUNDS, dklen)[keylen:2 * keylen]
                ok = hmac.new(key2, data, hashlib.sha1).digest()[:10] == auth
            else:
                ok = True  # 空 data 的 hash 只能信任 16 位校验值
            found.append((pw, ok))
            print("\n[候选] %r  最终确认: %s" % (pw.decode("utf-8", "replace"), "是" if ok else "否(1/65536 误报)"))
            with open(args.out, "ab") as f:
                f.write(pw + (b"\tVERIFIED\n" if ok else b"\tCANDIDATE\n"))
        now = time.time()
        if now - last >= 3:
            rate = done / (now - t0)
            print("已试 %d 个，%.0f 个/秒，用时 %.0f 秒" % (done, rate, now - t0), end="\r")
            last = now

    pool.close()
    pool.join()
    dt = time.time() - t0
    print("\n完成：%d 个候选，用时 %.1f 秒，平均 %.0f 个/秒" % (done, dt, done / max(dt, 1e-9)))
    if not found:
        print("字典内未找到（只代表这批候选的 16 位校验值都不匹配）")
    else:
        print("命中写入：%s" % args.out)


if __name__ == "__main__":
    mp.freeze_support()
    main()
