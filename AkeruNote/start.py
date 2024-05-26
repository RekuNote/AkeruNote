from types import MethodType
from twisted.web import server, resource, static
from twisted.internet import reactor
from twisted.python import log
import sys, time, os, atexit

# Splash
print(" █████╗ ██╗  ██╗███████╗██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ████████╗███████╗██╗")
print("██╔══██╗██║ ██╔╝██╔════╝██╔══██╗██║   ██║████╗  ██║██╔═══██╗╚══██╔══╝██╔════╝██║")
print("███████║█████╔╝ █████╗  ██████╔╝██║   ██║██╔██╗ ██║██║   ██║   ██║   █████╗  ██║")
print("██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗██║   ██║██║╚██╗██║██║   ██║   ██║   ██╔══╝  ╚═╝")
print("██║  ██║██║  ██╗███████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝   ██║   ███████╗██╗")
print("╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝  
      
# Settings:
useWSGI = False  # Not fully tested and WILL NOT support multiple instances/workers with the plaintext database
port = 8080  # Use port 8080

# Import:
print("Importing modules...", end=' ')
from twisted.web import server  # filehost
from twisted.internet import reactor
if useWSGI:
    from twisted.application import internet, service

import sys, time, os, atexit
print("Done!")

# Enable logging to the console
log.startLogging(sys.stdout)

# Set working directory
if os.path.dirname(__file__):
    os.chdir(os.path.dirname(__file__))
else:
    for i in sys.path:
        path = os.path.split(i)[0]
        if not os.path.exists(os.path.join(path, "start.py")): continue
        if not os.path.exists(os.path.join(path, "hatena.py")): continue
        if not os.path.exists(os.path.join(path, "DB.py")): continue
        os.chdir(path)
        break
    else:
        print("Can't force working directory, may fail crash!")

# Logging
class Log:
    class filesplit:  # A file object writing to two outputs
        def __init__(self):
            self.files = []
        def write(self, data):
            for i in self.files:
                i.write(data)
        def flush(self):  # IPython needs this
            pass
    def __init__(self):
        minutes, seconds = list(map(int, time.strftime("%M %S").split(" ")))
        minutes = 59 - minutes
        seconds = 59 - seconds
        reactor.callLater(60 * minutes + seconds + 5, self.HandleUpdate)
        reactor.callLater(60 * 5, self.AutoFlush)

        # Create year folder
        if not os.path.exists("logs/" + time.strftime("%Y")):
            os.mkdir("logs/" + time.strftime("%Y"))

        # Create month folder
        if not os.path.exists("logs/" + time.strftime("%Y/%B")):
            os.mkdir("logs/" + time.strftime("%Y/%B"))

        self.Activityhandle = open(time.strftime("logs/%Y/%B/%d %B activity.log"), "a")
        self.Errorhandle = open(time.strftime("logs/%Y/%B/%d %B error.log"), "a")

        self.stderr = sys.stderr
        sys.stderr = self.filesplit()
        sys.stderr.files.append(self.stderr)
        sys.stderr.files.append(self.Errorhandle)

        self.write("Server startup...", True)
    def HandleUpdate(self):
        pass
    def AutoFlush(self):
        pass
    def close(self):
        self.Activityhandle.close()
        self.Errorhandle.close()
    def write(self, String, Silent=False):
        if not Silent:
            print(time.strftime("[%H:%M:%S]"), String)
        self.Activityhandle.write(time.strftime("[%H:%M:%S] ") + String + "\n")
    Print = write

Log = Log()

# Initialize database:
print("Initializing flipnote database...", end=' ')
import DB
print("Done!")

# Setup AkeruNote server:
print("Setting up AkeruNote site...", end=' ')
import hatena
hatena.ServerLog = Log
site = server.Site(hatena.Setup())
print("Done!")

# Detailed request logging
class DetailedLoggingResource(resource.Resource):
    isLeaf = True

    def __init__(self, wrapped_resource):
        self.wrapped_resource = wrapped_resource

    def render(self, request):
        log.msg(f"Received request: {request.method.decode()} {request.uri.decode()}")
        for header, values in request.requestHeaders.getAllRawHeaders():
            log.msg(f"Header: {header.decode()} = {', '.join([value.decode() for value in values])}")
        log.msg(f"Client: {request.getClientIP()}")

        response = self.wrapped_resource.render(request)
        log.msg(f"Response code: {request.code}")
        return response

# Custom resource to handle requests and serve local files instead of proxying
class ProxyResource(resource.Resource):
    isLeaf = True

    def render_GET(self, request):
        # Log the original request URI
        log.msg(f"Original request URI: {request.uri.decode()}")

        # Translate the request path to a local file path
        uri = request.uri.decode()
        if uri.startswith("http://flipnote.hatena.com/ds/v2-us/"):
            local_path = uri.replace("http://flipnote.hatena.com/ds/v2-us/", "Akeru/AkeruRoot/ds/v2-xx/")
        else:
            local_path = uri.replace("/ds/v2-us/", "Akeru/AkeruRoot/ds/v2-xx/")
        
        local_file_path = os.path.join(os.getcwd(), local_path.lstrip('/'))

        log.msg(f"Translated local file path: {local_file_path}")

        if os.path.exists(local_file_path):
            log.msg(f"Serving local file: {local_file_path}")
            return static.File(local_file_path).render_GET(request)
        else:
            log.msg(f"File not found: {local_file_path}")
            request.setResponseCode(404)
            return b"404 Not Found"

# Make the AkeruNote server accept proxy connections:
print("Setting up proxy hack...", end=' ')
silent = True
old_buildProtocol = site.buildProtocol

def buildProtocol(self, addr):
    protocol = old_buildProtocol(addr)
    protocol.new_recv_buffer = []

    old_dataReceived = protocol.dataReceived
    def dataReceived(self, data):
        log.msg(f"Data received: {data}")

        for check, repl in (b"GET http://flipnote.hatena.com", b"GET "), (b"POST http://flipnote.hatena.com", b"POST "):
            if check in data:
                log.msg(f"Replacing {check} with {repl}")
                data = data.replace(check, repl)
        old_dataReceived(data)
    protocol.dataReceived = MethodType(dataReceived, protocol)
    return protocol

site.buildProtocol = MethodType(buildProtocol, site)
print("Done!")

# Wrap the site with the DetailedLoggingResource to log all requests
root_resource = DetailedLoggingResource(ProxyResource())
site = server.Site(root_resource)

# Run the server
print("Server start!")
if useWSGI:
    application = service.Application('web')
    sc = service.IServiceCollection(application)
    internet.TCPServer(port, site).setServiceParent(sc)
    atexit.register(Log.write, String="Server shutdown", Silent=True)
else:
    reactor.listenTCP(port, site)
    reactor.run()
    Log.write("Server shutdown", True)
