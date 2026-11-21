import os

p = r"C:\Users\Lenovo\.dsh\attachments\v1\files\d9\d91d25aeebd2d77d958f9805329f679a2b63e180fd573f27a752882388a15d15\hh.txt"
size = os.path.getsize(p)
print("size:", size)

with open(p, "rb") as f:
    head = f.read(400)
print("head repr:", repr(head[:200]))
print("head hex:", head[:16].hex())

markers = [b"$zip2$", b"$/zip2$", b"$pkzip2$", b"PK\x03\x04", b"PK\x05\x06"]
found = {m: [] for m in markers}
nl_first = None
nl_count = 0
chunk_size = 8 * 1024 * 1024
pos = 0
with open(p, "rb") as f:
    while True:
        b = f.read(chunk_size)
        if not b:
            break
        for m in markers:
            start = 0
            while True:
                i = b.find(m, start)
                if i < 0:
                    break
                off = pos + i
                if len(found[m]) < 5:
                    found[m].append(off)
                else:
                    found[m].append(-1)
                    break
                start = i + 1
        if nl_first is None:
            j = b.find(b"\n")
            if j >= 0:
                nl_first = pos + j
        nl_count += b.count(b"\n")
        pos += len(b)

print("first newline offset:", nl_first, "total newlines:", nl_count)
for m in markers:
    print(m, "->", found[m])

# print context around the first occurrence of each interesting marker
with open(p, "rb") as f:
    for m in (b"$zip2$", b"$/zip2$"):
        offs = [o for o in found[m] if o >= 0]
        if offs:
            o = offs[0]
            f.seek(max(0, o - 150))
            ctx = f.read(400)
            print("\ncontext around", m, "at", o, ":")
            print(repr(ctx))
