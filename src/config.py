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
        self._validateCustomFileName()
        self._validateCustomFolderPath()
        return self.file.read()

    def setCustomFileName(self):
        pass

    def _validateCustomFileName(self,name=None):
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
        pass

    def _validateCustomFolderPath(self,path=None):
        content = self.file.read()
        if not "folderpath" in content:
            self.file.add({
                "folderpath": "\\{SUBREDDIT}\\"
            })

    def _validateCredentials(self):
        """Read credentials from config.json file"""

        keys = ['imgur_client_id',
                'imgur_client_secret']

        content = self.file.read()
        if "reddit_refresh_token" in content and len(content["reddit_refresh_token"]) != 0:
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
                self.file.add({key:input("\t"+key+": ")})
        print()