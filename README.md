# AI.zip 密码破解尝试记录

一个**自己的**加密 PDF 压缩包（WinZip AES-256）忘记了解压密码，用 john the Ripper 在本机和租用的 GPU 上做了离线穷举，把全过程、数据与结论留档在这里。

> 所有计算都是离线的：压缩包不上传、不联网、不涉及任何在线破解服务。
> 仓库里**不包含**压缩包本体、原 PDF、283 MB 的哈希文件和任何字典文件，原因见 [为什么没有 hash.txt](#为什么没有-hashtxt-和-aizip)。

## 一句话结论

- **3–6 位（62 字符集：大小写字母 + 数字）已 100% 穷举**，未命中；
- 7 位只覆盖"纯大写 + 数字"和"纯小写 + 数字"两套（各 36⁷），约 4.45%，未命中；
- 8 位只覆盖 4 大写 + 4 数字的 4 种排列、8 位纯数字、手机号等零散切片，覆盖不到 0.01%，未命中；
- 合计约 **2,531 亿候选**、GPU 约 **11 小时**、累计花费约 **¥21.5**（含两次试错）。
- 判断：这不像"随手设的弱密码"，更像随机生成或带特殊符号。继续穷举性价比很低，已停手。

## 目标与哈希参数

| 项目 | 值 |
|---|---|
| 压缩包 | 143,624,640 字节，单文件（一个 PDF，解压后 158,193,187 字节） |
| 加密 | WinZip AES-256（AE-1，压缩方法 99，deflate） |
| 哈希格式 | `$zip2$`（hashcat 13600 / john `ZIP` 与 `ZIP-opencl`） |
| mode / salt | 3（AES-256）/ `d5104ed18ea266a70c36285b7e76ea09` |
| verify / auth | `7b75` / `5e643f339fa77b9b62e3` |
| 压缩后长度 | 143,624,398 字节（`88f88ce`） |
| hash.txt | 287,248,884 字节（`$zip2$…$/zip2$` 一整条） |

这条哈希的 `compress_length` 是 7 位十六进制、`data` 约 2.87 亿字符，两项都超过 **hashcat 13600** 的解析上限（1–6 位 / 16,777,216 字符），所以 hashcat 根本吃不下，只能走 **john**。

## 实测速度（同一 143.6 MB 哈希，john `ZIP-opencl`）

| GPU | 显存 | 速度（候选/秒） | 价格（元/小时） | 每元吞吐（万/元） |
|---|---|---|---|---|
| RTX PRO 6000 | 96 GB | 11,104,000 | 8.80 | 126 |
| RTX 5090 | 32 GB | 10,869,000 | 2.98 | 365 |
| RTX PRO 6000 Max-Q | 96 GB | 10,838,000 | 6.79 | 160 |
| RTX 5090 D | 32 GB | 10,032,000 | 3.14 | 319 |
| RTX 4090 | 24 GB | 8,955,000 | 2.08 | 431 |
| RTX 6000D | 84 GB | 8,500,000 | 6.46 | 132 |
| RTX 4090D | 24 GB | 6,270,000 | 1.98 | 317 |
| H800 | 80 GB | 2,915,000 | 9.98 | 29 |

几个反直觉的点：

- **最贵的卡不是最快的**：H800 只有 4090D 的 0.46 倍、每元吞吐是 4090 的 1/15。这个任务跑的是 PBKDF2-HMAC-SHA1（1000 轮），吃单卡整数吞吐与时钟，高带宽 / FP64 完全用不上。
- **性价比最好的是 RTX 4090**（¥1.77–2.08/h），4090D 次之；5090 更快但更贵，每元吞吐只有 4090 的 85%。
- 本机核显（Ryzen 7 5700U 的 Vega 8）虽然能跑 `ZIP-opencl`，但真实 143.6 MB 哈希只有 **2,000–3,000 /秒**，比 CPU 的 10–13 万/秒还慢 30 多倍——`--test` 的内置小样例会骗人。
- 本机 CPU（16 线程，john `ZIP` 的 AVX2 8x）稳定在 11–13 万/秒，是零成本兜底。

## 已尝试的覆盖范围

| 设备 | 内容 | 候选数 | 结果 |
|---|---|---|---|
| 笔记本 CPU | rockyou、?d×6/?d×7、生日、`?d?u` 与 `?d?l` 的 3–6 位、4 大写 + 4 数字 4 排列 | 约 95 亿 | 0 命中 |
| RTX 4090D | `?u×4?d×3`、`?u×3?d×4`、`?u×5?d×2`、`?d×4?u×3`、rockyou(+best64)、Top204k(+best64/OneRule/dive)、手机号 70 亿、8 位纯数字、7 位两套 | 约 1,960 亿 | 0 命中 |
| RTX 4090 | 62³–62⁶ 全字符集（3–6 位混合） | 约 532 亿 | 0 命中 |

完整的逐条清单、耗时与费用在 [docs/AI.zip破解尝试汇总.docx](docs/AI.zip破解尝试汇总.docx)（11 章、20 张表）。

## 复现

### 1. 准备 john（Linux GPU 机）

```bash
apt-get install -y build-essential ocl-icd-opencl-dev opencl-headers clinfo
mkdir -p /etc/OpenCL/vendors && echo libnvidia-opencl.so.1 > /etc/OpenCL/vendors/nvidia.icd
curl -L -o john.tar.gz https://codeload.github.com/openwall/john/tar.gz/refs/heads/bleeding-jumbo
mkdir -p /root/john-src && tar xzf john.tar.gz -C /root/john-src --strip-components=1
cd /root/john-src && ./configure && make -j$(nproc)
./run/john --list=formats | grep -i zip    # 应看到 ZIP-opencl
```

### 2. 生成等价结构的合成哈希（不要上传真实文件）

```bash
{ printf '$zip2$*0*3*0*'; printf '11%.0s' $(seq 16); printf '*7b75*88f88ce*';
  head -c 143624398 /dev/urandom | od -An -v -tx1 | tr -d ' \n';
  printf '*5e643f339fa77b9b62e3*$/zip2$'; } > /root/bench.txt
```

### 3. 跑一个空间

```bash
cd /root/john-src/run
./john --format=ZIP-opencl -1='?l?u?d' --mask='?1?1?1?1?1?1?1' \
       --session=mix7 --pot=/root/pat.pot /root/hash.txt
./john --status=mix7          # 看进度
./john --restore=mix7         # 断点续跑（必须同目录）
./john --show --format=ZIP-opencl --pot=/root/pat.pot /root/hash.txt
```

**注意**：`.rec` 文件里写死了启动时的 `--format`，CPU 的 `mix7` 进度不能用 `--restore=mix7 --format=ZIP-opencl` 换到 GPU 上续跑。

### 4. 本机 Windows（CPU 兜底）

```powershell
cd D:\john\john-1.9.0-jumbo-1-win64\run
.\john.exe --format=zip -1="?l?u?d" --mask="?1?1?1?1?1?1?1" `
           --session=mix7 --pot=D:\hashb\zip\pat7.pot D:\hashb\zip\hash.txt
```

## 脚本

| 文件 | 作用 |
|---|---|
| `scripts/night_5090.py` | 抢占空闲 RTX 5090 → 装机 → 编译 john → 跑 240 秒 → 关机 → 写 JSON + 重建 Word |
| `scripts/autodl_client.py` | AutoDL 接口封装（从环境变量 `AUTODL_TOKEN` 读 JWT，不硬编码凭据） |
| `scripts/build_cracklog.py` | 用 python-docx 生成 `docs/AI.zip破解尝试汇总.docx`（数据驱动，表格按实测速度排序） |
| `scripts/zip2_crack.py` | 纯 Python 的 `$zip2$` 校验器（PBKDF2 + verify 快筛 + HMAC 终审） |
| `scripts/inspect_hh.py` | 解析 zip2john 的输出，定位 `$zip2$…$/zip2$` 与字段长度 |
| `scripts/check_any_doc.py` | 校验 .docx 的 OOXML 子元素顺序、表格列宽与图片数量 |

脚本里的路径是按作者机器写的（`D:\hashb\zip\...`、`/root/...`），换机器需要改常量。

## 为什么没有 hash.txt 和 AI.zip

- **hash.txt 287,248,884 字节**，超过 GitHub 单文件 100 MB 硬上限，push 会被直接拒绝；Git LFS 免费额度 1 GB 也会被这一个文件吃穿。
- **AI.zip 143,624,640 字节**，超限，而且它是受版权保护的电子书——公开分发不合适。
- 字典（rockyou 139,921,497 字节、CrackStation 等）同样超限，且都有公开下载源。
- 这里只保留**元数据**：上面那张参数表 + 开头 120 字符的样本（`$zip2$*0*3*0*d5104ed18ea266a70c36285b7e76ea09*7b75*88f88ce*...`）。

## 合规与隐私

- 目标文件是作者自己购买的 PDF 压缩包，密码丢失，属于"找回自己的文件"；没有破解任何他人的账号或设备。
- 代码里不含任何账号凭据、SSH 密码、云厂商 Token；AutoDL 的 JWT 从环境变量读取，仓库里只有占位符。
- 不提供、也不接受"绕过付费墙 / 破解他人资源"的请求；`xbp.pub`、`8tupian.net` 这类第三方发卡/网盘站点与本项目无关。
- 如果这个仓库帮到了你，请只把它用在**你自己的文件**上。

## License

代码 MIT；文档（`docs/*.docx`、`README.md`）CC BY-NC 4.0。
