# stringimage #

Converting email addresses to images since 2008.

Based off some stuff [Facebook](http://www.facebook.com) was doing at the time.

## Requirements ##

I used an old, slightly modified version of [pngcanvas.py](http://the.taoofmac.com/space/projects/PNGCanvas).  Due to license restrictions (CC Attribution-NonCommercial-NoDerivs 2.0) I'm uncertain if I can include it here.  My patch against [version 0.8](http://the.taoofmac.com/media/projects/PNGCanvas/pngcanvas-0.8.py.txt) is below:

    --- pngcanvas-0.8.py	2012-07-06 15:42:04.000000000 -0600
    +++ pngcanvas.py	2012-07-06 14:02:44.000000000 -0600
    @@ -1,11 +1,3 @@
    -#!/usr/bin/env python
    -
    -"""Simple PNG Canvas for Python"""
    -__version__ = "0.8"
    -__author__ = "Rui Carmo (http://the.taoofmac.com)"
    -__copyright__ = "CC Attribution-NonCommercial-NoDerivs 2.0 Rui Carmo"
    -__contributors__ = ["http://collaboa.weed.rbse.com/repository/file/branches/pgsql/lib/spark_pr.rb"], ["Eli Bendersky"]
    -
     import zlib, struct
 
     signature = struct.pack("8B", 137, 80, 78, 71, 13, 10, 26, 10)
    @@ -72,6 +64,7 @@
         x0, y0, x1, y1 = self._rectHelper(x0,y0,x1,y1)
         for x in range(x0, x1+1):
           for y in range(y0, y1+1):
    +        color = self.canvas[y][x]
             destination.canvas[dy+y-y0][dx+x-x0] = self.canvas[y][x]
 
       def blendRect(self,x0,y0,x1,y1,dx,dy,destination,alpha=0xff):
    @@ -156,12 +149,12 @@
         return signature + \
           self.pack_chunk('IHDR', struct.pack("!2I5B",self.width,self.height,8,2,0,0,0)) + \
           self.pack_chunk('tRNS', struct.pack("!6B",0xFF,0xFF,0xFF,0xFF,0xFF,0xFF)) + \
    -      self.pack_chunk('IDAT', zlib.compress(raw_data,9)) + \
    +      self.pack_chunk('IDAT', zlib.compress(raw_data,1)) + \
           self.pack_chunk('IEND', '')
 
       def pack_chunk(self,tag,data):
         to_check = tag + data
    -    return struct.pack("!I",len(data)) + to_check + struct.pack("!I", zlib.crc32(to_check) & 0xFFFFFFFF)
    +    return struct.pack("!I",len(data)) + to_check + struct.pack("!i",zlib.crc32(to_check))
 
       def load(self,f):
         assert f.read(8) == signature
    @@ -249,8 +242,11 @@
             crc = struct.unpack("!i",f.read(4))[0]
           except:
             return
    -      if zlib.crc32(tag + data) != crc:
    -        raise IOError
    +#      tcrc = zlib.crc32(tag + data)
    +#      if (tag == 'IHDR'):
    +#        raise IOError("%s[%i]: %s (%s) != %s (%s) :: %r" % (tag, length, tcrc, type(tcrc), crc, type(crc), data))
    +#      if tcrc != crc:
    +#        raise IOError("%s: %s != %s" % (tag, tcrc, crc))
           yield [tag,data]
 
     if __name__ == '__main__':
     
No idea if any of these modifications are still required.  I just wanted to put this here to have it somewhere :)

## Acknowledgements ##

* [ProFont](http://www.tobias-jung.de/seekingprofont/)
* [PNGCanvas](http://the.taoofmac.com/space/projects/PNGCanvas)