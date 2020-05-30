import os
import socket
import webbrowser
import random

from src.reddit import Reddit
from src.jsonHelper import JsonFile

class Config():

    def __init__(self,filename):
        self.filename = filename
        self.file = JsonFile(self.filename)

    def generate(self):
        self._validateCredentials()
        self._readCustomFileName()
        self._readCustomFolderPath()
        return self.file.read()

    def setCustomFileName(self):
        print("""
IMPORTANT: Do not change the filename structure frequently.
           If you did, the program could not find duplicates and
           would download the already downloaded files again.
           This would not create any duplicates in the directory but
           the program would not be as snappy as it should be.

Type a template file name for each post.

You can use SUBREDDIT, REDDITOR, POSTID, TITLE, UPVOTES, FLAIR in curly braces
The text in curly braces will be replaced with the corresponding property of an each post

For example: {FLAIR}_{SUBREDDIT}_{REDDITOR}

Existing filename template:""", None if "filename" not in self.file.read() else self.file.read()["filename"])

        filename = input(">> ")
        self.file.add({
            "filename": filename
        })

    def _readCustomFileName(self):
        content = self.file.read()

        if not "filename" in content:
            self.file.add({
                "filename": "{REDDITOR}_{TITLE}_{POSTID}"
            })
        elif not "{POSTID}" in content["filename"]:
            self.file.add({
                "filename": content["filename"] + "_{POSTID}"
            })

    def setCustomFolderPath(self):
        print("""
Type a folder structure (generic folder path)

Use slash or DOUBLE backslash to separate folders

You can use SUBREDDIT, REDDITOR, POSTID, TITLE, UPVOTES, FLAIR in curly braces
The text in curly braces will be replaced with the corresponding property of an each post

For example: {REDDITOR}/{SUBREDDIT}/{FLAIR}

Existing folder structure""", None if "folderpath" not in self.file.read() else self.file.read()["folderpath"])

        folderpath = input(">> ").strip("\\").strip("/")

        self.file.add({
            "folderpath": folderpath
        })

    def _readCustomFolderPath(self,path=None):
        content = self.file.read()
        if not "folderpath" in content:
            self.file.add({
                "folderpath": "{SUBREDDIT}"
            })

    def _validateCredentials(self):
        """Read credentials from config.json file"""

        keys = ['imgur_client_id',
                'imgur_client_secret']
        try:
            content = self.file.read()["credentials"]
        except:
            self.file.add({
                "credentials":{}
            })
            content = self.file.read()["credentials"]
            
        if "reddit" in content and len(content["reddit"]) != 0:
            pass
        else:
            Reddit().begin()

        if not all(content.get(key,False) for key in keys):
            print(
                "---Setting up the Imgur API---\n\n" \
                "Go to this URL and fill the form:\n" \
                "https://api.imgur.com/oauth2/addclient\n" \
                "Then, enter the client id and client secret here\n" \
                "Press Enter to open the link in the browser"
            )
            input()
            webbrowser.open("https://api.imgur.com/oauth2/addclient",new=2)

        for key in keys:
            try:
                if content[key] == "":
                    raise KeyError
            except KeyError:
                self.file.add({key:input("\t"+key+": ")},
                              "credentials")
        print()