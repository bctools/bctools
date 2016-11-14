#BCTOOLS README

##Image integrity
There are two CRC values in a BCFS image, at 0x10, 4 hex chars each.
The first is a checksum of all the headers, starting at _CP_CZK and ending at 0x4000 (start of strings table)
The second starts at 0x4000 and finishes at the end of the image.

###HMAC:
The HMAC-SHA1 values appear in ~6.5 and are calculated over the same data as the checksums. The HMAC key is present in the calculate-checksum-sig.py script.
The first HMAC starts at 0x18 and is 20 bytes long
The second starts at 0x58, same length.
HMACs are calculated over the same data as the CRC checksums.

##Extracting binaries and config files
Run `extract.py <system1|starter.si>` 
This will make a dump directory and write the extracted files in there.
Check them out with a quick `file dump/*`, if you dont see a lot of ELFs somethings gone wrong.
The extract.py code seems to work for 6.4.X, 6.5.X, and 6.6.X. Hasnt  been testing on any other versions.

##Altering images
Make the alterations in a hex editor, don't change the length of the file. Run `calculate-checksum-sig.py -p <filename>`, which will recalculate the CRC and HMAC values and patch them in automatically. Omit the -p flag to see the calculated hashes without altering the files.
