# Import necessary modules
from types import MethodType

# Splash
print(" █████╗ ██╗  ██╗███████╗██████╗ ██╗   ██╗███╗   ██╗ ██████╗ ████████╗███████╗██╗")
print("██╔══██╗██║ ██╔╝██╔════╝██╔══██╗██║   ██║████╗  ██║██╔═══██╗╚══██╔══╝██╔════╝██║")
print("███████║█████╔╝ █████╗  ██████╔╝██║   ██║██╔██╗ ██║██║   ██║   ██║   █████╗  ██║")
print("██╔══██║██╔═██╗ ██╔══╝  ██╔══██╗██║   ██║██║╚██╗██║██║   ██║   ██║   ██╔══╝  ╚═╝")
print("██║  ██║██║  ██╗███████╗██║  ██║╚██████╔╝██║ ╚████║╚██████╔╝   ██║   ███████╗██╗")
print("╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝")


# Settings for AkeruNote server
print("Setting Port...", end=' ')
useWSGI = False  # Untested
port = 9090  # Use port 9090
print("Done!")

# Import
print("Setting up modules...", end=' ')
from twisted.web import server  # filehost
from twisted.internet import reactor
if useWSGI: 
    from twisted.application import internet, service

import sys, time, os, atexit
print("Done!")

# Set the working directory
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

# Logging setup
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
    # Logging methods
    def write(self, String, Silent=False):
        if not Silent:
            print(time.strftime("[%H:%M:%S]"), String)
        self.Activityhandle.write(time.strftime("[%H:%M:%S] ") + String + "")
    Print = write

Log = Log()

# Initialize database
print("Initializing HatenaDB...", end=' ')
import DB
print("Done!")

# Setup Hatena site
print("Setting up Hatena site...", end=' ')
import hatena
hatena.ServerLog = Log
site = server.Site(hatena.Setup())
print("Done!")

# Allow server to accept proxy connections
print("Configuring Hatena -> AkeruNote passthrough proxy...", end=' ')
silent = True
old_buildProtocol = site.buildProtocol
def buildProtocol(self, addr):
    protocol = old_buildProtocol(addr)

    protocol.new_recv_buffer = []

    old_dataReceived = protocol.dataReceived
    def dataReceived(self, data):
        # Assuming the GET request doesn't get fragmented, which should be safe with an MTU at 1500, a crash doesn't matter really anyway. Too much work for a simple twisted upgrade on a dropped project
        for check, repl in (("GET http://flipnote.hatena.com", "GET "), ("POST http://flipnote.hatena.com", "POST ")):
            if check in data:
                data = data.replace(check, repl)
        old_dataReceived(data)
    funcType = type(protocol.dataReceived)
    protocol.dataReceived = funcType(dataReceived, protocol, protocol.__class__)
    return protocol

funcType = type(site.buildProtocol)
site.buildProtocol = MethodType(buildProtocol, site)
print("Done!")

# Run the server
print("Server started successfully!")
if useWSGI:
    # Probably doesn't work
    application = service.Application('web')
    sc = service.IServiceCollection(application)
    internet.TCPServer(port, site).setServiceParent(sc)

    atexit.register(Log.write, String="Server shutdown", Silent=True)
else:
    reactor.listenTCP(port, site)  # Hey listen!~
    reactor.run()

    # Done
    Log.write("Server shutdown", True)
