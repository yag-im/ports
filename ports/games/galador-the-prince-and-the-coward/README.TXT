1CD

SRC[0]\DATA -> E:\DATA

E:\DATA\CODE.EXE
"""

"""
CODE.EXE (original PL VERSION) crack

Wait till CODE and DATA segments are fully unpacked in the `start` function
Dump CODE and DATA segments in Ollydbg

Patch original exe with the unpacked CODE segment:
dd if=code_00401000.bin of=CODE.EXE bs=1 seek=1536 count=51712 conv=notrunc

Patch original exe with the unpacked DATA segment:
dd if=code_0040E000.bin of=CODE.EXE bs=1 seek=53248 count=49152 conv=notrunc

NOP jb (carry flag=1 check) after llseek at 0x40510D

Some interesting research of why it works in certain builds of Wine:
https://www.winehq.org/mailman3/hyperkitty/list/wine-devel@winehq.org/thread/SD7T2WEEEJZATVFJMGOK6HALW6H5HDMP/
