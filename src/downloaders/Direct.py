import os

from src.downloaders.downloaderUtils import getFile, getExtension

from src.errors import FileNameTooLong
from src.utils import GLOBAL
from src.utils import printToFile as print

class Direct:
    def __init__(self,directory,POST):
        POST['EXTENSION'] = getExtension(POST['CONTENTURL'])
        if not os.path.exists(directory): os.makedirs(directory)

        filename = GLOBAL.config['filename'].format(**POST)

        print(filename+POST["EXTENSION"])

        fileDir = directory / (
            filename+POST['EXTENSION']
        )
        tempDir = directory / (
            GLOBAL.config["filename"].format(**POST)+".tmp"
        )

        try:
            getFile(fileDir,tempDir,POST['CONTENTURL'])
        except FileNameTooLong:
            fileDir = directory / (POST['POSTID']+POST['EXTENSION'])
            tempDir = directory / (POST['POSTID']+".tmp")

            getFile(fileDir,tempDir,POST['CONTENTURL'])