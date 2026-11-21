# hash.txt 说明

本目录**不包含** `hash.txt`：它是 287,248,884 字节的单行 `$zip2$…$/zip2$` 记录，
超过 GitHub 单文件 100 MB 的硬上限，无法 push。

可核对的元数据：

- 大小：287,248,884 字节
- 结构：`$zip2$*0*3*0*<salt 32 hex>*<verify 4 hex>*<compress_length>*<data>*<auth 20 hex>*$/zip2$`
- salt：`d5104ed18ea266a70c36285b7e76ea09`
- verify：`7b75`
- compress_length：`88f88ce`（143,621,326）
- data：143,624,398 字节密文的十六进制，即 287,248,796 个字符
- auth：`5e643f339fa77b9b62e3`
- 开头样本：`$zip2$*0*3*0*d5104ed18ea266a70c36285b7e76ea09*7b75*88f88ce*...`

如果你有自己的 zip2john 输出，可以直接用 `scripts/inspect_hh.py` 按同样的方式定位与切片。
