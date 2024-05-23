
import os
from twisted.web import resource, static
from importlib.machinery import SourceFileLoader as load_source

class UGOXMLResource(resource.Resource):
    # Placeholder class for UGOXMLResource
    isLeaf = True

class FileResource(static.File):
    # Placeholder class for FileResource
    isLeaf = True

class FolderResource(resource.Resource):
    # Placeholder class for FolderResource
    isLeaf = False

def LoadHatenadirStructure(Resource, path=os.path.join("Akeru/HatenaDB", "ds", "v2-xx")):
    for root, dirs, files in os.walk(path):
        if root != path:
            continue  # use recursion instead
        
        for filename in files:
            filetype = filename.split(".")[-1].lower()
            os.path.join(path, filename)
            
            if filetype == "ugoxml":
                Resource.putChild(filename[:-3].encode('utf-8'), UGOXMLResource(os.path.join(path, filename)))
            elif filetype == "py":
                try:
                    pyfile = load_source("pyfile", os.path.abspath(os.path.join(path, filename)))
                except ImportError as err:
                    pyfile = None
                    print("Error!")
                    print(f"Failed to import the python file \"{os.path.join(path, filename)}\"")
                    print(err)

                if pyfile:
                    Resource.putChild(filename[:-3].encode('utf-8'), pyfile.PyResource())
            elif filetype == "pyc":
                pass  # ignore
            else:
                Resource.putChild(filename.encode('utf-8'), FileResource(os.path.join(path, filename)))
        
        for foldername in dirs:
            if foldername[:2] != "__":
                folder = FolderResource()
                LoadHatenadirStructure(folder, os.path.join(path, foldername))
                Resource.putChild(foldername.encode('utf-8'), folder)

class ds(resource.Resource):
    # Placeholder class for ds
    isLeaf = False

class UgoRoot(resource.Resource):
    # Placeholder class for UgoRoot
    isLeaf = False

class Root(resource.Resource):
    isLeaf = False
    def __init__(self):
        resource.Resource.__init__(self)
        self.dsResource = ds()
        self.cssResource = static.File("Akeru/HatenaDB/css/")
        self.imagesResource = static.File("Akeru/HatenaDB/images/")

def Setup():
    root = Root()
    return root
