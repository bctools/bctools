#!/usr/bin/python
#Hacky and terrible script to extract binaries and shit from Blue Coat system1 or starter.si BCFS image

import binascii,struct,array,sys,os
STRINGSTABLESTART=0
STRINGSTABLELEN=0
CPIETABLESTART=0

EXTRACT=True #Set to false to disable actually pulling the files. If this is False it will just list filenames / paths

def get_table_offsets(fh):
    global STRINGSTABLESTART, CPIETABLESTART, STRINGSTABLELEN #i dont give a fuck

    #Get string table offset
    fh.seek(0xcd0) #CPCE entry for string table, consistent accross versions
    fh.seek(0x19,1)
    str_tabl_off = fh.read(0x4)
    tabl_arr = array.array('h',str_tabl_off)
    tabl_arr.byteswap()
    print "String table = ", binascii.hexlify(tabl_arr.tostring())
    STRINGSTABLESTART = int(binascii.hexlify(tabl_arr.tostring()),16) / 0x100
    print STRINGSTABLESTART

    fh.seek(0xcf0) #Seems to be where the strings table length is stored
    str_tabl_len = fh.read(0x2)
    stba = array.array('h',str_tabl_len)
    stba.byteswap()
    print "Strings table len = ", binascii.hexlify(stba.tostring())
    STRINGSTABLELEN=int(binascii.hexlify(stba.tostring()),16)
    print STRINGSTABLELEN


    #Get CPVE table offset
    fh.seek(0xD10)
    fh.seek(0x19,1)
    cpve_tabl_off = array.array('h',fh.read(0x4))
    cpve_tabl_off.byteswap()
    print "CPVE table = ", binascii.hexlify(cpve_tabl_off.tostring())

    #Get CPIE table offset
    fh.seek(0xD50)
    fh.seek(0x19,1)
    cpie_table_off = array.array('h',fh.read(0x4))
    cpie_table_off.byteswap()
    print "CPIE table = ", binascii.hexlify(cpie_table_off)
    CPIETABLESTART = int(binascii.hexlify(cpie_table_off),16) / 0x100
    print CPIETABLESTART

def walk_cpie_table_headers(fh,offset):
    #Get str table
    str_table = get_strings()

    fh.seek(offset)
    i = 0
    end = find_cpie_end(offset)
    nfiles = (end - offset) /0x100
    print "Number of files = ",nfiles
    while i <= nfiles:
        fh.seek(0x10,1)
        offset = rev(binascii.hexlify(fh.read(0x8)))
        offset_int = int(offset,16)
        size = rev(binascii.hexlify(fh.read(0x8)))
        size_int = int(size,16)
        #print "Offset = %s, size = %s" %(offset,size)
        bc_name = str("%03d")%(i)  + "-" + get_name(str_table,i)
        print "Filename == %s" %(bc_name)
        if EXTRACT == True:
            read_out_file(offset_int,size_int,bc_name)
        fh.seek(0xe0,1)
        i+=1

def get_name(str_table,i):
    return str_table[i]

def find_cpie_end(offset):
    #Returns the offset of the last CPIE entry
    f2 = open(sys.argv[1],'r')
    f2.seek(offset)
    f2.seek(0x10,1)
    last_offset = rev(binascii.hexlify(f2.read(0x8)))
    last_offset_int = int(last_offset,16)
    print "CPIE -a = ", hex(last_offset_int)
    f2.close()
    print "CPIE -b = ", hex((last_offset_int + offset)-0x100)
    #sys.exit()
    return (last_offset_int + offset)-0x100

def read_out_file(offset,size,name):
    #takes an offset from the start of cpie table, as well as bin length,
    #and reads the binary out of the system1 image, then writes it to the system
    #Uses a seperate fh to not fuck up the seeks
    fh2 = open(sys.argv[1],'r')
    fname = "dump/%s" %(name)
    outf = open(fname,"w")
    location = CPIETABLESTART+offset
    #print "location = %s" %location
    fh2.seek(location)
    fcontents = fh2.read(size)
    outf.write(fcontents)
    outf.close()
    
    return True

def get_strings():
    image=open(sys.argv[1],'r')
    image.seek(STRINGSTABLESTART)
    image.seek(0x8,1)
    tabl_arr = array.array('h',image.read(0x2))
    tabl_arr.byteswap()
    print int(binascii.hexlify(tabl_arr),16)
    
    strings_loc = STRINGSTABLESTART + int(binascii.hexlify(tabl_arr),16)
    print strings_loc
    image.seek(strings_loc)

    tmp=image.read(STRINGSTABLELEN - int(binascii.hexlify(tabl_arr),16))
    strings = tmp.split('\x00')
    str_table = strings_extract(strings)
    print str_table
    print "Length of string table = %d" %(len(str_table))
    image.close()
    if sys.argv[1] == "system1":
        return str_table[2:]
    else: #starter.si has an additional thing in the string table before the filenames start
        return str_table[3:]

def rev(s):
    ''' :( '''
    s = s.strip()
    if " " not in s:
        s = ' '.join(a+b for a,b in zip(s[::2], s[1::2]))
    in_str = s.split(" ")
    if len(in_str) % 2 != 0:
        print "invalid length"
    else:
        last = len(in_str)-1
        out = ""
        i = last
        while i > 0:
            hb = in_str[i] + in_str[i-1]
            out += hb
            i -=2
        return out

def strings_extract(strings):
    s2 = []
    for s in strings:
        if s != "":
            s2.append(s)
    #print s2
    s3=[]
    i = 0
    #print s2

    while i < len(s2):
        if "/" not in s2[i]:
                if s2[i] != "main_cr.cfg": #Something wrong here
                    s3.append(s2[i])

        else:
            print "Path: ", s2[i]
        i+=1

    return s3

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Usage: extract.py <file>")
    image=open(sys.argv[1],'r')
    if not os.path.exists("dump"):
        os.makedirs("dump")
    get_table_offsets(image)
    walk_cpie_table_headers(image,CPIETABLESTART)
    image.close() 
