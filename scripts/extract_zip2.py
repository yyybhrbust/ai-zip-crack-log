import os

SRC = r"C:\Users\Lenovo\.dsh\attachments\v1\files\d9\d91d25aeebd2d77d958f9805329f679a2b63e180fd573f27a752882388a15d15\hh.txt"
WANT_DIR = r"C:\Users\Lenovo\Desktop\hashb\zip"
OUT = os.path.join(WANT_DIR, "hash.txt")
FALLBACK_DIR = r"D:\hashb\zip"

with open(SRC, "rb") as f:
    raw = f.read()

i = raw.find(b"$zip2$")
j = raw.find(b"$/zip2$")
end = j + len(b"$/zip2$")
h = raw[i:end]

target = OUT
try:
    os.makedirs(WANT_DIR, exist_ok=True)
    with open(target, "wb") as f:
        f.write(h)
except OSError as e:
    print("write to Desktop failed:", e)
    os.makedirs(FALLBACK_DIR, exist_ok=True)
    target = os.path.join(FALLBACK_DIR, "hash.txt")
    with open(target, "wb") as f:
        f.write(h)

print("src bytes :", len(raw))
print("zip2 start:", i, " end marker end:", end)
print("hash bytes:", len(h))
print("head:", h[:90].decode("ascii"))
print("tail:", h[-40:].decode("ascii"))
print("newline inside:", b"\n" in h or b"\r" in h)
print("written:", target)
