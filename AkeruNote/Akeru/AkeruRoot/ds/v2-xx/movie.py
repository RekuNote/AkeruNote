from twisted.web import resource
import os

from Akeru.hatena import Log, ServerLog, Silent, NotFound
from Akeru.HatenaDB import Database
from AkeruTools import TMB

#The movie folder:
class PyResource(resource.Resource):
	isLeaf = False
	def __init__(self):
		resource.Resource.__init__(self)
		
		self.CreatorID = CreatorIDResource()
	def getChild(self, name, request):
		if Database.CreatorExists(name):
			return self.CreatorID
		elif name == "":
			return self
		else:
			return NotFound
	def render(self, request):
		request.setResponseCode(403)
		return "403 - Denied access"

#The creator ID folder:
class CreatorIDResource(resource.Resource):
	isLeaf = False
	def __init__(self):
		resource.Resource.__init__(self)
		
		self.CreatorIDFile = CreatorIDFileResource()
	def getChild(self, name, request):
		CreatorID = request.path.split("/")[-2]
		filename = ".".join(name.split(".")[:-1])
		
		if Database.FlipnoteExists(CreatorID, filename):#html, ppm and info
			return self.CreatorIDFile
		elif name == "":
			return self
		else:
			return NotFound
	def render(self, request):
		request.setResponseCode(403)
		return "403 - Denied access"

#Any public file inside creator ID folder:
class CreatorIDFileResource(resource.Resource):
	isLeaf = True
	def __init__(self):
		resource.Resource.__init__(self)
	def render(self, request):
		creator, file = request.path.split("/")[-2:]
		filetype = file.split(".")[-1].lower()
		
		if filetype in "ppm":
			#log it:
			path = "/".join(request.path.split("/")[3:])
			Log(request, path)
			
			#add a view:
			Database.AddView(creator, file[:-4])
			
			#read ppm file:
			data = Database.GetFlipnotePPM(creator, file[:-4])
			
			#send file to the client:
			request.responseHeaders.setRawHeaders('content-type', ['text/plain'])
			return data
		elif filetype == "info":
			path = "/".join(request.path.split("/")[3:])
			Log(request, path, True)
			request.responseHeaders.setRawHeaders('content-type', ['text/plain'])
			return "0\n0\n"#undocumented what it means
		elif filetype == "htm":
			#maybe cache the details page of Database.Newest?
			
			if "mode" in request.args:
				if request.args["mode"][0] == "commentshalfsize":
					pass
			
			return self.GenerateDetailsPage(creator, ".".join(file.split(".")[:-1])).encode("UTF-8")
		elif filetype == "star":
			path = "/".join(request.path.split("/")[3:])
			color = request.args.get('starcolor', ["yellow"])[0] # colour of star, can be green, red, blue, or purple. Yellow otherwise.
			headers = request.getAllHeaders()

			#bad formatting
			if "x-hatena-star-count" not in headers:
				ServerLog.write("%s got 403 when requesting %s without a X-Hatena-Star-Count header" % (request.getClientIP(), path), Silent)
				request.setResponseCode(403)
				return "403 - Denied access\nRequest lacks a X-Hatena-Star-Count http header"
			
			#add the stars:
			amount = int(headers["x-hatena-star-count"])
			if (amount < 1) or (amount > 65535):
				ServerLog.write("%s got 403 when requesting %s with an invalid X-Hatena-Star-Count header" % (request.getClientIP(), path), Silent)
				request.setResponseCode(403)
				return "403 - Denied access\nRequest has an invalid X-Hatena-Star-Count http header"
			
			if not Database.AddStar(creator, file[:-5], amount, color):
				#error
				ServerLog.write("%s got 500 when requesting %s" % (request.getClientIP(), path), Silent)
				request.setResponseCode(500)
				return "500 - Internal server error\nAdding the stars seem to have failed."
			
			#report success
			ServerLog.write("%s added %i %s stars to %s/%s.ppm" % (request.getClientIP(), amount, color, creator, file[:-5]), Silent)
			return "Success"
		elif filetype == "dl":
			path = "/".join(request.path.split("/")[3:])
			Log(request, path, True)
			#this is POSTed to when it've been stored to memory.
			
			Database.AddDownload(creator, file[:-3])
			
			return "Noted ;)"
		else:
			path = "/".join(request.path.split("/")[3:])
			ServerLog.write("%s got 403 when requesting %s" % (request.getClientIP(), path), Silent)
			
			request.setResponseCode(403)
			return "403 - Denied access"
	#details page
	def GenerateDetailsPage(self, CreatorID, filename):#filename without ext
		flipnote = Database.GetFlipnote(CreatorID, filename)#flipnote = [filename, views, stars, green stars, red stars, blue stars, purple stars, Channel], all probably strings
		if not flipnote:
			return "This flipnote doesn't exist!"
		tmb = TMB().Read(Database.GetFlipnoteTMB(CreatorID, filename))
		if not tmb:
			return "This flipnote is corrupt!"
		
		#Is it a spinoff?
		Spinnoff = ""
		if tmb.OriginalAuthorID != tmb.EditorAuthorID or tmb.OriginalFilename != tmb.CurrentFilename:
			if Database.FlipnoteExists(tmb.OriginalAuthorID, tmb.OriginalFilename[:-4]):
				Spinnoff = SpinoffTemplate1.replace("%%CreatorID%%", tmb.OriginalAuthorID).replace("%%Filename%%", tmb.OriginalFilename[:-4])
			elif tmb.OriginalAuthorID != tmb.EditorAuthorID:
				Spinnoff = SpinoffTemplate2
		
		#make each entry:
		Entries = []
		
		#Creator username:
		name = "Creator"
		#content = "<a href=\"http://flipnote.hatena.com/ds/ds/v2-xx/%s/profile.htm?t=260&pm=80\">%s</a>" % (CreatorID, tmb.EditorAuthorName)
		content = '<a href="http://flipnote.hatena.com/ds/v2-xx/%s/profile.htm?t=260&pm=80\">%s</a>' % (CreatorID, tmb.Username)
		Entries.append(PageEntryTemplate.replace("%%Name%%", name).replace("%%Content%%", content))
		
		#Stars:
		name = "Stars"
		content = '<a href="http://flipnote.hatena.com/ds/v2-xx/movie/%s/%s.htm?mode=stardetail"><span class="star0c">\u2605</span> <span class="star0">%s</span></a>' % (CreatorID, filename, flipnote[2])#yellow stars
		content += '<br/><a href="http://flipnote.hatena.com/ds/v2-xx/movie/%s/%s.htm?mode=stardetail"><span class="star1c">\u2605</span> <span class="star1">%s</span></a>' % (CreatorID, filename, flipnote[3])#green stars
		content += '<br/><a href="http://flipnote.hatena.com/ds/v2-xx/movie/%s/%s.htm?mode=stardetail"><span class="star2c">\u2605</span> <span class="star2">%s</span></a>' % (CreatorID, filename, flipnote[4])#red stars
		content += '<br/><a href="http://flipnote.hatena.com/ds/v2-xx/movie/%s/%s.htm?mode=stardetail"><span class="star3c">\u2605</span> <span class="star3">%s</span></a>' % (CreatorID, filename, flipnote[5])#blue stars
		content += '<br/><a href="http://flipnote.hatena.com/ds/v2-xx/movie/%s/%s.htm?mode=stardetail"><span class="star4c">\u2605</span> <span class="star4">%s</span></a>' % (CreatorID, filename, flipnote[6])#purple stars
		Entries.append(PageEntryTemplate.replace("%%Name%%", name).replace("%%Content%%", content))
		
		#Views:
		name = "Views"
		content = str(flipnote[1])
		Entries.append(PageEntryTemplate.replace("%%Name%%", name).replace("%%Content%%", content))
		
		# Downloads:
		name = "Downloads"
		content = str(flipnote[8])
		Entries.append(PageEntryTemplate.replace("%%Name%%", name).replace("%%Content%%", content))

		#Channel:
		if flipnote[7]:#todo: make channels work at all
			name = "Channel"
			content = 'a href="http://flipnote.hatena.com/ds/v2-xx/ch/%s.uls">%s</a>' % (flipnote[7], flipnote[7])
			Entries.append(PageEntryTemplate.replace("%%Name%%", name).replace("%%Content%%", content))
		
		#Comments:
		Comments = "0"
		
		#doto: add original author info too
		
		#add the entries to page:
		return DetailsPageTemplate.replace("%%CreatorID%%", CreatorID).replace("%%Filename%%", filename).replace("%%CommentCount%%", Comments).replace("%%Spinoff%%", Spinnoff).replace("%%PageEntries%%", PageEntrySeparator.join(Entries))

#templates:
DetailsPageTemplate = """<html>
	<head>
		<title>Flipnote by %%Username%%</title>
		<meta name="upperlink" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.ppm">
		<meta name="starbutton" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star">
    		<meta name="starbutton1" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=green,9001">
    		<meta name="starbutton2" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=red,9001">
    		<meta name="starbutton3" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=blue,9001">
    		<meta name="starbutton4" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.star?starcolor=purple,9001">
		<meta name="savebutton" content="http://flipnote.hatena.com/ds/v2-xx/movie/%%CreatorID%%/%%Filename%%.ppm">
		<meta name="playcontrolbutton" content="">
		<link rel="stylesheet" href="http://flipnote.hatena.com/css/ds/basic.css">
	</head>
	<body>
		<table width="240" border="0" cellspacing="0" cellpadding="0" class="tab">
			<tr>
				<td class="border" width="5" align="center">
					<div class="border"></div>
				</td>
				<td class="border" width="70" align="center">
					<div class="border"></div>
				</td>
				<td class="border" width="95" align="center">
					<div class="border"></div>
				</td>
			</tr>
			<tr>
				<td class="space"> </td>
				<td class="tabon" align="center">
					<div class="on" align="center">Description</div>
				</td>
				<td class="taboff" align="center">
					<a class="taboff" href="http://flipnote.hatena.com/ds/v2-eu/movie/%%CreatorID%%/%%Filename%%.htm?mode=commentshalfsize">Comments(%%CommentCount%%)</a>
				</td>
			</tr>
		</table>
		<div class="pad5b"></div>%%Spinoff%%
		<table width="226" border="0" cellspacing="0" cellpadding="0" class="detail">%%PageEntries%%
		</table>
	</body>
</html>"""
SpinoffTemplate1 = """
		<div class="notice2" align="center">
			This Flipnote is a spin-off.<br>
			<a href="http://flipnote.hatena.com/ds/v2-eu/movie/%%CreatorID%%/%%Filename%%.htm">Original Flipnote</a>
		</div>"""
SpinoffTemplate2 = """
		<div class="notice2" align="center">
			This Flipnote is a spin-off.
		</div>"""
PageEntryTemplate = """
			<tr>
				<th width="90">
					<div class="item-term" align="left">%%Name%%</div>
				</th>
				<td width="136">
					<div class="item-value" align="right">
						%%Content%%
					</div>
				</td>
			</tr>"""
PageEntrySeparator="""
			<tr> </tr>
			<tr>
				<td colspan="2">
					<div class="hr"></div>
				</td>
			</tr>"""
