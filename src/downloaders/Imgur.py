import os

import imgurpython

from src.downloaders.downloaderUtils import getExtension, getFile
from src.errors import (AlbumNotDownloadedCompletely, FileAlreadyExistsError,
                        FileNameTooLong)
from src.utils import GLOBAL, nameCorrector
from src.utils import printToFile as print


class Imgur:
    def __init__(self,directory,post):
        self.imgurClient = self.initImgur()

        imgurID = self.getId(post['CONTENTURL'])
        content = self.getLink(imgurID)

        if not os.path.exists(directory): os.makedirs(directory)

        if content['type'] == 'image':

            try:
                post['MEDIAURL'] = content['object'].mp4
            except AttributeError:
                post['MEDIAURL'] = content['object'].link

            post['EXTENSION'] = getExtension(post['MEDIAURL'])

            filename = GLOBAL.config['filename'].format(**post)

            print(filename+post["EXTENSION"])

            fileDir = directory / (
                filename+post['EXTENSION']
            )
            tempDir = directory / (
                GLOBAL.config["filename"].format(**post)+".tmp"
            )

            try:
                getFile(fileDir,tempDir,post['MEDIAURL'])
            except FileNameTooLong:
                fileDir = directory / post['POSTID'] + post['EXTENSION']
                tempDir = directory / post['POSTID'] + '.tmp'
                getFile(fileDir,tempDir,post['MEDIAURL'])

        elif content['type'] == 'album':
            images = content['object'].images
            imagesLenght = len(images)
            howManyDownloaded = imagesLenght
            duplicates = 0

            title = nameCorrector(post['TITLE'])
            print(post["REDDITOR"]+"_"+title+"_"+post['POSTID'],end="\n\n")

            folderDir = directory / (
                post["REDDITOR"] + "_" + title + "_" + post['POSTID']
            )

            filename = GLOBAL.config['filename'].format(**post)

            folderDir = directory / filename

            try:
                if not os.path.exists(folderDir):
                    os.makedirs(folderDir)
            except FileNotFoundError:
                folderDir = directory / post['POSTID']
                os.makedirs(folderDir)

            for i in range(imagesLenght):
                try:
                    imageURL = images[i]['mp4']
                except KeyError:
                    imageURL = images[i]['link']

                images[i]['Ext'] = getExtension(imageURL)

                fileName = (str(i+1)
                            + "_"
                            + nameCorrector(str(images[i]['title']))
                            + "_"
                            + images[i]['id'])

                """Filenames are declared here"""

                fileDir = folderDir / (fileName + images[i]['Ext'])
                tempDir = folderDir / (fileName + ".tmp")

                print("  ({}/{})".format(i+1,imagesLenght))
                print("  {}".format(fileName+images[i]['Ext']))

                try:
                    getFile(fileDir,tempDir,imageURL,indent=2)
                    print()
                except FileAlreadyExistsError:
                    print("  The file already exists" + " "*10,end="\n\n")
                    duplicates += 1
                    howManyDownloaded -= 1

                # IF FILE NAME IS TOO LONG, IT WONT REGISTER
                except FileNameTooLong:
                    fileName = (str(i+1) + "_" + images[i]['id'])
                    fileDir = folderDir / (fileName + images[i]['Ext'])
                    tempDir = folderDir / (fileName + ".tmp")
                    try:
                        getFile(fileDir,tempDir,imageURL,indent=2)
                    # IF STILL TOO LONG
                    except FileNameTooLong:
                        fileName = str(i+1)
                        fileDir = folderDir / (fileName + images[i]['Ext'])
                        tempDir = folderDir / (fileName + ".tmp")
                        getFile(fileDir,tempDir,imageURL,indent=2)

                except Exception as exception:
                    print("\n  Could not get the file")
                    print(
                        "  "
                        + "{class_name}: {info}".format(
                            class_name=exception.__class__.__name__,
                            info=str(exception)
                        )
                        + "\n"
                    )
                    howManyDownloaded -= 1

            if duplicates == imagesLenght:
                raise FileAlreadyExistsError
            elif howManyDownloaded + duplicates < imagesLenght:
                raise AlbumNotDownloadedCompletely(
                    "Album Not Downloaded Completely"
                )
    
    @staticmethod
    def initImgur():
        """Initialize imgur api"""

        config = GLOBAL.config
        return imgurpython.ImgurClient(
            config['imgur_client_id'],
            config['imgur_client_secret']
        )
    def getId(self,submissionURL):
        """Extract imgur post id
        and determine if its a single image or album
        """

        if submissionURL[-1] == "/":
            submissionURL = submissionURL[:-1]

        if "a/" in submissionURL or "gallery/" in submissionURL:
            albumId = submissionURL.split("/")[-1]
            return {'id':albumId, 'type':'album'}

        else:
            url = submissionURL.replace('.','/').split('/')
            imageId = url[url.index('com')+1]
            return {'id':imageId, 'type':'image'}

    def getLink(self,identity):
        """Request imgur object from imgur api
        """

        if identity['type'] == 'image':
            return {'object':self.imgurClient.get_image(identity['id']),
                    'type':'image'}
        elif identity['type'] == 'album':
            return {'object':self.imgurClient.get_album(identity['id']),
                    'type':'album'}
    @staticmethod
    def get_credits():
        return Imgur.initImgur().get_credits()
