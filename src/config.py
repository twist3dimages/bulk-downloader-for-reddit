import os
import socket
import webbrowser
import random

from src.reddit import Reddit
from src.utils import GLOBAL
from src.jsonHelper import JsonFile

def getConfig(configFileName):
    """Read credentials from config.json file"""

    keys = ['imgur_client_id',
            'imgur_client_secret']

    if os.path.exists(configFileName):
        FILE = JsonFile(configFileName)
        content = FILE.read()
        if "reddit_refresh_token" in content and len(content["reddit_refresh_token"]) != 0:
            pass
        else:
            Reddit(GLOBAL.config).begin()

        if not all(False if content.get(key,"") == "" else True for key in keys):
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
                FILE.add({key:input("\t"+key+": ")})
        print()
        return JsonFile(configFileName).read()

    else:
        FILE = JsonFile(configFileName)
        configDictionary = {}
        print(
            "Go to this URL and fill the form: " \
            "https://api.imgur.com/oauth2/addclient\n" \
            "Enter the client id and client secret here:"
            )
        webbrowser.open("https://api.imgur.com/oauth2/addclient",new=2)
        for key in keys:
            configDictionary[key] = input("  "+key+": ")
        FILE.add(configDictionary)
        return FILE.read()