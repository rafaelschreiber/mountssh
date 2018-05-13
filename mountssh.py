import os
import subprocess
import json


def getCommandOutput(command):
    """Returns the output of the given unix command"""
    output = subprocess.run(command, stdout=subprocess.PIPE)
    output = output.stdout.decode("utf-8")
    return output[:-1]


# set working variables for the programm
HOME = os.getenv("HOME")
PWD = os.getenv("PWD")
CONFIGFOLDER = HOME + "/.mountssh"
USER = os.getenv("USER")
EDITOR = os.getenv("VISUAL")
if EDITOR is None:
    EDITOR = False
OS = getCommandOutput(["uname"])
HIDEOUTPUT = " > /dev/null 2>&1"
try:
    BOOKMARKS = os.listdir(CONFIGFOLDER)
except FileNotFoundError:
    BOOKMARKS = [ ]


def pathCleaner(path):
    """Returns the full path of the given path"""
    if path[0] == '~':
        return HOME + path[1:]
    elif path[0] == '/':
        return path
    else:
        return PWD + '/' + path


def isCommandAvaiable(command):
    """Checks if command is avaible and/or installed"""
    if os.system("which " + command + HIDEOUTPUT) != 0:
        return False
    else:
        return True


def checkDependencies():
    """Checks if all dependencies are installed"""
    if not isCommandAvaiable("sshfs"):
        print("sshfs isn't installed please install it to use mountssh")
        exit(1)


def isReachable(host):
    """Checks if host is reachable"""
    if os.system("ping -c 1 " + host + HIDEOUTPUT) != 0:
        return False
    else:
        return True


def isEmptyString(string):
    """Checks if string consist just of empty characters"""
    for char in string:
        if char != " ":
            return False
    return True


def init():
    """Initializes the programm and prepares everything for work"""
    checkDependencies()
    if not os.path.exists(HOME + "/.mountssh"):
        os.mkdir(HOME + "/.mountssh")

    # checks if configfolder is writeable
    if os.system("touch " + CONFIGFOLDER + "/.test" + HIDEOUTPUT) != 0:
        print("Configfolder is not writeable")
        exit(1)
    else:
        os.system("rm " + CONFIGFOLDER + "/.test" + HIDEOUTPUT)


class Bookmark:
    hostname = None
    user = None
    port = None
    remotemount = None
    localmount = None
    displayname = None
    bookmarkname = None


    def __init__(self, hostname=None, user=None, port=None, remotemount=None, localmount=None, displayname=None, bookmarkname=None):
        self.hostname = hostname
        self.user = user
        self.port = port
        self.remotemount = remotemount
        self.localmount = localmount
        self.displayname = displayname
        self.bookmarkname = bookmarkname


    def getDictionary(self):
        dictionary = {"hostname":self.hostname,
                      "user":self.user,
                      "port":self.port,
                      "remotemount":self.remotemount,
                      "localmount":self.localmount,
                      "displayname":self.displayname,
                      "bookmarkname":self.bookmarkname
                      }
        return dictionary


    def putDictionary(self, data):
        self.hostname = data["hostname"]
        self.user = data["user"]
        self.port = data["port"]
        self.remotemount = data["remotemount"]
        self.localmount = data["localmount"]
        self.displayname = data["displayname"]
        self.bookmarkname = data["bookmarkname"]


    def getHostname(self):
        return self.hostname

    def getUser(self):
        return self.user


    def getPort(self):
        return self.port


    def getRemotemount(self):
        return self.remotemount


    def getLocalmount(self):
        return self.localmount


    def getDisplayname(self):
        return self.displayname


    def getBookmarkname(self):
        return self.bookmarkname


def newBookmark(bookmark):
    if bookmark.getBookmarkname() in BOOKMARKS:
        print("The bookmark named " + bookmark.getBookmarkname() + " already exist")
        exit(1)
    with open(CONFIGFOLDER + '/' + bookmark.getBookmarkname(), 'w') as jsonFile:
        jsonFile.write(json.dumps(bookmark.getDictionary(), indent=4))
        jsonFile.close()


def loadBookmark(bookmarkname):
    if bookmarkname not in BOOKMARKS:
        print("The bookmark named " + bookmarkname + " doesn't exist")
        exit(1)
    with open(CONFIGFOLDER + '/' + bookmarkname, 'r') as jsonFile:
           bookmarkDict = json.load(jsonFile)
           jsonFile.close()
    bookmark = Bookmark()
    bookmark.putDictionary(bookmarkDict)
    return bookmark


def deleteBookmark(bookmarkname = True):
    if len(BOOKMARKS) == 0:
        print("There are no bookmarks to delete")
        exit(1)
    if bookmarkname is True:
        os.system("rm " + CONFIGFOLDER + "/*" + HIDEOUTPUT)
    else:
        if bookmarkname not in BOOKMARKS:
            print("The bookmark named " + str(bookmarkname) + " doesn't exist")
            exit(1)
        else:
            os.system("rm " + CONFIGFOLDER + "/" + bookmarkname + HIDEOUTPUT)


def getBookmarkInformation(bookmarkname):
    bookmark = loadBookmark(bookmarkname).getDictionary()
    for key in bookmark:
        print(key + " = " + str(bookmark[key]))


def editBookmark(bookmarkname):
    if bookmarkname not in BOOKMARKS:
        print("The bookmark named " + bookmarkname + " doesn't exist")
        exit(1)
    if not EDITOR:
        print("With which editor do you want to use?")
        while True:
            editor = str(input(">>> "))
            if isCommandAvaiable(editor):
              break
            else:
                print("The editor called " + editor + "isn't installed\n")
    else:
        editor = EDITOR
    os.system(editor + " " + CONFIGFOLDER + "/" + bookmarkname)


def renameBookmark(oldName, newName):
    if oldName not in BOOKMARKS:
        print("The bookmark named " + oldName + " doesn't exist")
        exit(1)
    if newName in BOOKMARKS:
        print("The bookmark named " + newName + " already exist")
        exit(1)
    bookmark = loadBookmark(oldName)
    bookmark.bookmarkname = newName
    deleteBookmark(oldName)
    newBookmark(bookmark)


def connect(bookmark):
    if not isReachable(bookmark.getHostname()):
        print(bookmark.getHostname() + " is not reachable. Cannot connect")
        exit(1)
    bookmark.localmount = pathCleaner(bookmark.getLocalmount())
    if os.path.exists(bookmark.getLocalmount()):
        if os.path.isfile(bookmark.getLocalmount()):
            print(bookmark.getLocalmount() + " is not a directory")
            exit(1)
    else:
        os.mkdir(bookmark.getLocalmount())
    if OS == "Darwin":
        command = "sshfs " + bookmark.getUser() + "@" + bookmark.getHostname() + ":" + bookmark.getRemotemount() + \
                  " " + bookmark.getLocalmount() + " " + "-ovolname=" + bookmark.getDisplayname()
    else:
        command = "sshfs " + bookmark.getUser() + "@" + bookmark.getHostname() + ":" + bookmark.getRemotemount() + \
                  " " + bookmark.getLocalmount()
    os.system(command)


def getUserInput(isBookmark = False):
    # get hostname
    print("Please type in the Hostname")
    while True:
        hostname = str(input(">>> "))
        if isReachable(hostname):
            break
        else:
            if isBookmark:
                print("\nThe host is currently unavailable. Do you want to add this host anyway? (y/n)")
                while True:
                    answer = str(input(">>> "))
                    if answer == 'y' or answer == 'n':
                        break
                    else:
                        print("Please type in y or n\n")
                if answer == 'y':
                    break
                else:
                    print("\nPlease type in the Hostname")
                    continue
            else:
                print("Please type in a reachable hostname\n")
    # get username
    print("\nPlease type in the username default = " + USER)
    username = str(input(">>> "))
    if isEmptyString(username):
        username = USER
    # get port
    print("\nPlease type in the port default = 22")
    while True:
        try:
            port = str(input(">>> "))
            if isEmptyString(port):
                port = 22
                break
            else:
                print("here")
                port = int(port)
                break
        except ValueError:
            print("Please type in a number\n")
    # get remote mount
    print("\nPlease type in the remote mountpoint default = ~/")
    remotemount = str(input(">>> "))
    if isEmptyString(remotemount):
        remotemount = ""
    # get local mount
    print("\nPlease type in the local mountpoint")
    localmount = str(input(">>> "))
    # get display name only on macOS
    if OS == "Darwin":
        print("\nPlease type in the display name")
        displayname = str(input(">>> "))
    else:
        displayname = ""
    # get bookmarkname only when creating a bookmark
    if isBookmark:
        print("\nPlease type in the bookmark name")
        while True:
            bookmarkname = str(input(">>> "))
            if bookmarkname in BOOKMARKS:
                print("This bookmark name already exist\n")
                continue
            else:
                break
        if isEmptyString(displayname):
            displayname = bookmarkname
    else:
        bookmarkname = None
    # building object
    bookmark = Bookmark(hostname, username, port, remotemount, localmount, displayname, bookmarkname)
    return bookmark


def main():
    init()
    connectInformation = getUserInput()
    connect(connectInformation)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("")
        exit(1)
    except EOFError:
        print("")
        exit(1)
