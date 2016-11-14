#!/usr/bin/python
'''
Calculates the CRCs and SHA1 HMACs for a BCFS image
Also supports patching system1 and starter.si files with the updated checksums
Certificate signing of images  began around 6.6, which defeats this patching

#Usage
First you'll want to check this works on an unmodified image.
Run the tool without the -p (patch) flag, and ensure that both the extracted and calculated CRC and HMAC values are consistent.
If they are the same, make the necessary patches to the image, then re-run the tool with the -p flag.
This will patch the new calculated CRC and HMAC values into the image and ensure that it passes validation.
'''

import binascii,sys
from Crypto.Hash import SHA, HMAC

#BC HMAC key
KEY="7b552f020a67ca128f4a810f3d40b92fcae88dc33c5da5eaca0a80dc372a17c6bb087c332cbbb8d2f4b9e5acab4bfa40bc67f3fb6628b610598006b8c4e67fbe"
HEX_KEY=binascii.unhexlify(KEY)

def do_patch(fh,crc1,crc2,hmac1,hmac2):
    '''Patches the supplied file with the calculated crc/hmacs'''

    try:
        fh.seek(0x10)
        fh.write(binascii.unhexlify(crc1))
        fh.write(binascii.unhexlify(crc2))
        fh.write(binascii.unhexlify(hmac1))
        fh.seek(0x2C,1)
        fh.write(binascii.unhexlify(hmac2))

        print "File patched, new values are:"
        get_current_values(fh)

    except:
        print "Failed to write updated values"
        return False

    return True

def get_current_values(fh):
    fh.seek(0x10)
    crc1 = fh.read(0x4)
    crc2 = fh.read(0x4)
    hmac1 = fh.read(0x14)
    fh.seek(0x2C,1)
    hmac2 = fh.read(0x14)

    print "CRCs = %s, %s" %(binascii.hexlify(crc1),binascii.hexlify(crc2))
    print "HMACs = %s, %s" %(binascii.hexlify(hmac1),binascii.hexlify(hmac2))
    return True

def hmac(data):
    '''Returns the sha1-hmac of the provided data signed with the BC key'''
    return HMAC.new(HEX_KEY, data, SHA).hexdigest()

def crc32(file_obj):
    '''Returns a hex representation of the CRC32 of provided data'''
    z = binascii.crc32(file_obj) & 0xffffffff
    return "%08x" % (z)

def endian_rev(in_str):
    '''Reverse the endianness of a hex array'''
    return "".join(map(str.__add__, in_str[-2::-2] , in_str[-1::-2]))

def do_calculate(input_fh, patch):
    '''Main function'''
    f = input_fh

    print "[+] Current (extracted from image) checksum values:" 
    get_current_values(f)

    print "\n[+] Calculated values:"

    f.seek(0)

    offset_czk = 0xc00 #Start of the _CP__CZK__ section
    offset_strings = 0x4000  # Start of the strings table

    #Calculate first checksum
    f.seek(offset_czk)
    czk_bit = f.read(offset_strings - offset_czk)
    initial_czk = crc32(czk_bit)

    crc1 = endian_rev(initial_czk)
    hmac1 = hmac(czk_bit)


    #Calculate the other bit
    f.seek(offset_strings)
    data_bit = f.read()
    initial_data = crc32(data_bit)

    crc2 = endian_rev(initial_data)
    hmac2 = hmac(data_bit)


    print "CRC values: %s, %s" %(crc1,crc2)
    print "HMAC values: %s, %s"%(hmac1,hmac2)

    if patch:
        print "[+] Patching..."
        do_patch(fh,crc1,crc2,hmac1,hmac2)

    return True

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: python calc-checksum.py [-p] <file>")

    if sys.argv[1] == "-p":
        print "[+] Patching mode enabled"
        inputf = sys.argv[2]
        fh = open(inputf,'r+')
        patch = True
    else:
        inputf = sys.argv[1]
        fh = open(inputf,'r')
        patch = False

    if fh.read(0x4) != binascii.unhexlify("5f43505f"):
        print "Image doesn't start normally, are you sure this is a BC system1 or starter.si file?"
    else:
        do_calculate(fh, patch)
