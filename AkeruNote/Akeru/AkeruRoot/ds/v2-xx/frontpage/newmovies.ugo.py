from twisted.web import resource
from twisted.internet import reactor
import time

from Akeru.hatena import Log, NotFound
from Akeru.HatenaDB import Database
from AkeruTools import UGO

#makes a flipnote list of the newest flipnotes
class PyResource(resource.Resource):
	isLeaf = True
	def __init__(self):
		resource.Resource.__init__(self)
		
		self.pages = []#10 first pages
		self.newestflip = None
		reactor.callLater(4, self.Update)#or it'll clash with the others in the terminal
	def render(self, request):
		page = int(request.args["page"][0]) if "page" in request.args else 1
		
		if len(self.pages) >= page:
			path = "/".join(request.path.split("/")[3:])
			Log(request, "%s page %i" % (path, page))
			
			request.responseHeaders.setRawHeaders('content-type', ['text/plain'])
			return self.pages[page-1]
		#elif (page-1)*50 < len(Database.Newest):
		#	pass
		else:
			return NotFound.render(request)
	#===
	def Update(self):#called every minute
		reactor.callLater(60, self.Update)
		
		if self.newestflip != Database.Newest[0]:
			self.newestflip = Database.Newest[0]
			reactor.callInThread(self.UpdateThreaded, Database.Newest)
	def UpdateThreaded(self, flipnotes):#run in an another thread
		#create pages:
		pages = []
		pagecount = (len(flipnotes)-1)/50 + 1
		if pagecount > 10: pagecount = 10#temp?
		flipcount = len(flipnotes)
		
		for i in range(min((pagecount, 10))):
			pages.append(self.MakePage(flipnotes[i*50:i*50+50], i+1, i<pagecount-1, flipcount))
		
		if self.pages:#not on startup
			print(time.strftime("[%H:%M:%S] Updated newmovies.ugo"))
		self.pages = pages
	def MakePage(self, flipnotes, page, next, count):
		ugo = UGO()
		ugo.Loaded = True
		ugo.Items = []
		
		#meta
		ugo.Items.append(("layout", (2, 1)))
		ugo.Items.append(("topscreen text", ["New Flipnotes", "Flipnotes", str(count), "", "The newest Flipnotes submitted."], 0))
		
		#categories
		ugo.Items.append(("category", "http://flipnote.hatena.com/ds/v2-xx/frontpage/hotmovies.uls", "Most Popular", False))
		ugo.Items.append(("category", "http://flipnote.hatena.com/ds/v2-xx/frontpage/likedmovies.uls", "Most Liked", False))
		#ugo.Items.append(("category", "http://flipnote.hatena.com/ds/v2-xx/frontpage/recommended.uls", "Recommended", False))
		ugo.Items.append(("category", "http://flipnote.hatena.com/ds/v2-xx/frontpage/newmovies.uls", "New Flipnotes", True))
		#ugo.Items.append(("category", "http://flipnote.hatena.com/ds/v2-xx/frontpage/following.uls", "New Favourites", False))
		
		#the "post flipnote" button
		ugo.Items.append(("unknown", ("3", "http://flipnote.hatena.com/ds/v2-xx/help/post_howto.htm", "UABvAHMAdAAgAEYAbABpAHAAbgBvAHQAZQA=")))
		
		#previous page
		if page > 1:
			ugo.Items.append(("button", 115, "Previous", "http://flipnote.hatena.com/ds/v2-xx/frontpage/newmovies.uls?page=%i" % (page-1), ("", ""), None))
		
		#Flipnotes
		for creatorid, filename in flipnotes:#[i*50 : i*50+50]:
			stars = str(Database.GetFlipnote(creatorid, filename)[2])
			ugo.Items.append(("button", 3, "", "http://flipnote.hatena.com/ds/v2-xx/movie/%s/%s.ppm" % (creatorid, filename), (stars, "765", "573", "0"), (filename+".ppm", Database.GetFlipnoteTMB(creatorid, filename))))
		
		#next page
		if next:
			ugo.Items.append(("button", 115, "Next", "http://flipnote.hatena.com/ds/v2-xx/frontpage/newmovies.uls?page=%i" % (page+1), ("", ""), None))
		
		return ugo.Pack()






