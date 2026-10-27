import sys, struct, zlib, os, lzma
def read(path, out=None, pattern=None, listonly=False):
    f=open(path,'rb'); h=f.read(32)
    magic,ver,comp,toclen,tes,ne,bs,flags=struct.unpack('>4sI4sIIIII',h)
    assert magic==b'PSAR',magic
    toc=f.read(toclen-32)
    ents=[]
    for i in range(ne):
        e=toc[i*tes:(i+1)*tes]
        bi=struct.unpack('>I',e[16:20])[0]; us=int.from_bytes(e[20:25],'big'); off=int.from_bytes(e[25:30],'big')
        ents.append((bi,us,off))
    zb={65536:2,16777216:3}.get(bs,4)
    bl=toc[ne*tes:]; nb=len(bl)//zb
    bsz=[int.from_bytes(bl[i*zb:(i+1)*zb],'big') for i in range(nb)]
    def get(bi,us,off):
        f.seek(off); data=bytearray(); i=bi
        while len(data)<us:
            sz=bsz[i] or bs; chunk=f.read(sz)
            if sz==min(bs,us-len(data)) and not (chunk[:1]==b'\x78' or chunk[:3]==b'\x5d\x00\x00'):
                data+=chunk
            else:
                try: data+=zlib.decompress(chunk)
                except Exception:
                    try: data+=lzma.decompress(chunk)
                    except Exception: data+=chunk
            i+=1
        return bytes(data[:us])
    names=get(*ents[0]).decode('utf8','replace').split('\n')
    flags_abs = flags & 2
    for n,e in zip(names,ents[1:]):
        if pattern and pattern not in n.lower(): continue
        if listonly: print(e[1], n); continue
        d=get(*e); p=os.path.join(out,n.lstrip('/')); os.makedirs(os.path.dirname(p),exist_ok=True); open(p,'wb').write(d)
if __name__=='__main__':
    path,mode=sys.argv[1],sys.argv[2]
    if mode=='list': read(path,pattern=(sys.argv[3].lower() if len(sys.argv)>3 else None),listonly=True)
    else: read(path,out=sys.argv[3],pattern=(sys.argv[4].lower() if len(sys.argv)>4 else None))
