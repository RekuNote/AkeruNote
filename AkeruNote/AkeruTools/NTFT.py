#NTFT.py by pbsds for python 2.7, modified by RekuNote for python 3.12.2
#AGPL3 licensed
#
#PIL is required to read and write images to disk
#
#Credits:
#
#	-The guys behind TiledGGD. This sped up my work a lit.
#	-Jsafive for supplying .ugo files
#
import sys, os, numpy as np
try:
	import Image
	hasPIL = True
except ImportError:
	hasPIL = False


#helpers
def AscDec(ascii, LittleEndian=False):#Converts a ascii string into a decimal
	ret = 0
	l = list(map(ord, ascii))
	if LittleEndian: l.reverse()
	for i in l:
		ret = (ret<<8) | i
	return ret
def DecAsc(dec, length=None, LittleEndian=False):#Converts a decimal into an ascii string of chosen length
	out = []
	while dec != 0:
		out.insert(0, dec&0xFF)
		dec >>= 8
	#"".join(map(chr, out))
	
	if length:
		if len(out) > length:
			#return "".join(map(chr, out[-length:]))
			out = out[-length:]
		if len(out) < length:
			#return "".join(map(chr, [0]*(length-len(out)) + out))
			out = [0]*(length-len(out)) + out
			
	if LittleEndian: out.reverse()
	return "".join(map(chr, out))
def clamp(value, min, max):
	if value > max: return max
	if value < min: return min
	return  value

#Class NTFT:
#
#	The NTFT image format stores RGB values as 5 bits each: a value between 0 and 31.
#	It has 1 bit of transparancy, which means its either vidssible or invisible. No gradients.
#	
#	How to use:
#		
#		Converting to NTFT file:
#			
#			image = ReadImage(input_path)
#			NTFT().SetImage(image).WriteFile(output_path)
#			
#		Reading NTFT file:
#			
#			ntft = NTFT().ReadFile(input_path, (width, height))
#			WriteImage(ntft.Image, output_path)
#		
class NTFT:
	def __init__(self):
		self.Loaded = False
	def ReadFile(self, path, size):
		f = open(path, "rb")
		ret = self.Read(f.read(), size)
		f.close()
		return ret
	def Read(self, data, xxx_todo_changeme2):
		#the actual stored data is a image with the sizes padded to the nearest power of 2. The image is then clipped out from it.
		(w, h) = xxx_todo_changeme2
		psize = []
		for i in (w, h):
			p = 1
			while 1<<p < i:
				p += 1
			psize.append(1<<p)
		pw, ph = psize
		
		#check if it fits the file:
		if pw*ph*2 != len(data):
			print("Invalid sizes")
			return False
		
		#JUST DO IT!
		#self.Image = [[None for _ in xrange(h)] for _ in xrange(w)]
		self.Image = np.zeros((w, h), dtype=">u4")
		for y in range(h):
			for x in range(w):
				pos = (x + y*pw)*2
				byte = AscDec(data[pos:pos+2], True)
				
				#ARGB1555 -> RGBA8:
				a = (byte >> 15       ) * 0xFF
				b = (byte >> 10 & 0x1F) * 0xFF / 0x1F
				g = (byte >> 5  & 0x1F) * 0xFF / 0x1F
				r = (byte       & 0x1F) * 0xFF / 0x1F
				
				#self.Image[x][y] = (r<<24) | (g<<16) | (b<<8) | a#RGBA8
				self.Image[x, y] = (r<<24) | (g<<16) | (b<<8) | a#RGBA8
		
		self.Loaded = True
		return self
	def WriteFile(self, path):
		if self.Loaded:
			f = open(path, "wb")
			f.write(self.Pack())
			f.close()
			return True
		else:
			return False
	def Pack(self):
		if not self.Loaded:
			return False
		
		#h = len(self.Image[0])
		#w = len(self.Image)
		w, h = self.Image.shape
		
		#the actual stored data is a image with the sizes padded to the nearest power of 2
		psize = []
		for i in (w, h):
			p = 1
			while 1<<p < i:
				p += 1
			psize.append(1<<p)
		
		out = []
		for y in range(psize[1]):
			for x in range(psize[0]):
				#read
				#c = self.Image[clamp(x, 0, w-1)][clamp(y, 0, h-1)]
				c = self.Image[clamp(x, 0, w-1), clamp(y, 0, h-1)]
				r =  c >> 24
				g = (c >> 16) & 0xFF
				b = (c >> 8 ) & 0xFF
				a =  c        & 0xFF
				
				#convert
				a = 1 if a >= 0x80 else 0
				r = r * 0x1F / 0xFF
				g = g * 0x1F / 0xFF
				b = b * 0x1F / 0xFF
				
				#store
				out.append(DecAsc((a<<15) | (b<<10) | (g<<5) | r, 2, True))
		
		return "".join(out)
	def SetImage(self, Image):
		self.Image = Image
		self.Loaded = True
		return self

#Function WriteImage:
#
#	Writes a 2D array of uint32 RGBA values as a image file.
#	Designed to work with NTFT.Image
#
#	This function requires the PIl imaging module
def WriteImage(image, outputPath):
	if not hasPIL:
		print("Error: PIL not found!")
		return False
	#if not image: return False
	
	out = image.tostring("F")
	
	# out = []
	# for y in xrange(len(image[0])):
		# for x in xrange(len(image)):
			# out.append(DecAsc(image[x][y], 4))
	
	out = Image.fromstring("RGBA", (len(image), len(image[0])), out)
	
	filetype = outputPath[outputPath.rfind(".")+1:]
	out.save(outputPath, filetype)
	
	return True

#Function ReadImage:
#
#	Returns a 2D list of uint32 RGBA values of the image file.
#	This can be passed into NTFT().SetImage()
#
#	This function requires the PIl imaging module
def ReadImage(path):#TODO: make it support numpy
	if not hasPIL: return False
	
	image = Image.open(path)
	pixeldata = image.getdata()
	w, h = image.size
	
	if len(pixeldata[0]) < 4:
		def Combine(xxx_todo_changeme):
			(r, g, b) = xxx_todo_changeme
			return (r << 24) | (g << 16) | (b << 8) | 0xFF
	else:
		def Combine(xxx_todo_changeme1):
			(r, g, b, a) = xxx_todo_changeme1
			return (r << 24) | (g << 16) | (b << 8) | a
	
	#ret = []
	ret = np.zeros((w, h), dtype=">u4")
	for x in range(w):
		#line = []
		for y in range(h):
			ret[x, y] = Combine(pixeldata[y*w + x])#maybe make a more numpy efficient way?
			#line.append(Combine(pixeldata[y*w + x]))
		#ret.append(line)
	
	return ret



#testing:
# i = NTFT().ReadFile("NTFTtests/kaeru.ntft", (36, 30))
# WriteImage(i.Image, "NTFTtests/kaeru.png")

# i = NTFT().ReadFile("NTFTtests/News.ntft", (32, 32))
# WriteImage(i.Image, "NTFTtests/News.png")

# i = NTFT().ReadFile("NTFTtests/Special Room.ntft", (32, 32))
# WriteImage(i.Image, "NTFTtests/Special Room.png")

#i = NTFT()
#i.Loaded = True
#i.Image = ReadImage("NTFTtests/geh.png")
#i.WriteFile("NTFTtests/geh.ntft")

if __name__ == "__main__":
	print("              ==      NTFT.py     ==")
	print("             ==      by pbsds      ==")
	print("              ==       v0.95      ==")
	print()
	
	if not hasPIL:
		print("PIL not found! Exiting...")
		sys.exit()
	
	if len(sys.argv) < 2:
		print("Usage:")
		print("      NTFT.py <input> [<output> [<width> <height>]]")
		print("")
		print("Can convert a NTFT to PNG or the other way around.")
		print("if <output> isn't specified it will be set to <input> with an another extension")
		print("")
		print("The NTFT file contain only the colordata, so it's up to the user to find or")
		print("store the resolution of the image. <width> and <height> is required")
		print("to convert a NTFT file to a image.")
		print("32x32 is the normal resolution for button icons in UGO files.")
		sys.exit()
	
	input = sys.argv[1]
	
	if input[-4:].lower() == "ntft" or len(sys.argv) >= 5:
		print("Mode: NTFT -> image")
		Encode = False
	else:
		print("Mode: image -> NTFT")
		Encode = True#if false it'll decode
	
	if len(sys.argv) >= 3:
		output = sys.argv[2]
		
		width, height = None, None
		if len(sys.argv) >= 5:
			if (not sys.argv[3].isdigit()) or (not sys.argv[4].isdigit()):
				print("Invalid size input!")
				sys.exit()
			width = int(sys.argv[3])
			height = int(sys.argv[4])
		
		if not (width and height) and not Encode:
			print("Image size not provided!")
			sys.exit()
		
	else:
		output = ".".join(input.split(".")[:-1]) + (".ntft" if Encode else ".png")
	
	print("Converting...")
	if Encode:
		try:
			image = ReadImage(input)
		except IOError as err:
			print(err)
			sys.exit()
		
		i = NTFT()
		i.Loaded = True
		i.Image = image
		i.WriteFile(output)
	else:
		try:
			ntft = NTFT().ReadFile(input, (width, height))
		except IOError as err:
			print(err)
			sys.exit()
		
		if not ntft:#eeror message already printed
			sys.exit()
		
		WriteImage(ntft.Image, output)
	print("Done!")