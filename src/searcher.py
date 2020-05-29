import os
import sys
import random
import socket
import webbrowser
import urllib.request
from urllib.error import HTTPError

import praw
from prawcore.exceptions import NotFound, ResponseException, Forbidden


from src.reddit import Reddit
from src.utils import GLOBAL, createLogFile, printToFile
from src.jsonHelper import JsonFile
from src.errors import (NoMatchingSubmissionFound, NoPrawSupport,
                        NoRedditSupport, MultiredditNotFound,
                        InvalidSortingType, RedditLoginFailed,
                        InsufficientPermission, DirectLinkNotFound)

print = printToFile

def getPosts(args):
    """Call PRAW regarding to arguments and pass it to extractDetails.
    Return what extractDetails has returned.
    """

    reddit = Reddit(GLOBAL.config).begin()

    if args["sort"] == "best":
        raise NoPrawSupport("PRAW does not support that")

    if "subreddit" in args:
        if "search" in args:
            if args["subreddit"] == "frontpage":
                args["subreddit"] = "all"

    if "user" in args:
        if args["user"] == "me":
            args["user"] = str(reddit.user.me())

    if not "search" in args:
        if args["sort"] == "top" or args["sort"] == "controversial":
            keyword_params = {
                "time_filter":args["time"],
                "limit":args["limit"]
            }
        # OTHER SORT TYPES DON'T TAKE TIME_FILTER
        else:
            keyword_params = {
                "limit":args["limit"]
            }
    else:
        keyword_params = {
                "time_filter":args["time"],
                "limit":args["limit"]
            }

    if "search" in args:
        if GLOBAL.arguments.sort in ["hot","rising","controversial"]:
            raise InvalidSortingType("Invalid sorting type has given")

        if "subreddit" in args:
            print (
                "search for \"{search}\" in\n" \
                "subreddit: {subreddit}\nsort: {sort}\n" \
                "time: {time}\nlimit: {limit}\n".format(
                    search=args["search"],
                    limit=args["limit"],
                    sort=args["sort"],
                    subreddit=args["subreddit"],
                    time=args["time"]
                ).upper(),noPrint=True
            )            
            return extractDetails(
                reddit.subreddit(args["subreddit"]).search(
                    args["search"],
                    limit=args["limit"],
                    sort=args["sort"],
                    time_filter=args["time"]
                )
            )

        elif "multireddit" in args:
            raise NoPrawSupport("PRAW does not support that")
        
        elif "user" in args:
            raise NoPrawSupport("PRAW does not support that")

        elif "saved" in args:
            raise ("Reddit does not support that")
    
    if args["sort"] == "relevance":
        raise InvalidSortingType("Invalid sorting type has given")

    if "saved" in args:
        print(
            "saved posts\nuser:{username}\nlimit={limit}\n".format(
                username=reddit.user.me(),
                limit=args["limit"]
            ).upper(),noPrint=True
        )
        return extractDetails(reddit.user.me().saved(limit=args["limit"]))

    if "subreddit" in args:

        if args["subreddit"] == "frontpage":

            print (
                "subreddit: {subreddit}\nsort: {sort}\n" \
                "time: {time}\nlimit: {limit}\n".format(
                    limit=args["limit"],
                    sort=args["sort"],
                    subreddit=args["subreddit"],
                    time=args["time"]
                ).upper(),noPrint=True
            )
            return extractDetails(
                getattr(reddit.front,args["sort"]) (**keyword_params)
            )

        else:  
            print (
                "subreddit: {subreddit}\nsort: {sort}\n" \
                "time: {time}\nlimit: {limit}\n".format(
                    limit=args["limit"],
                    sort=args["sort"],
                    subreddit=args["subreddit"],
                    time=args["time"]
                ).upper(),noPrint=True
            )
            return extractDetails(
                getattr(
                    reddit.subreddit(args["subreddit"]),args["sort"]
                ) (**keyword_params)
            )

    elif "multireddit" in args:
        print (
            "user: {user}\n" \
            "multireddit: {multireddit}\nsort: {sort}\n" \
            "time: {time}\nlimit: {limit}\n".format(
                user=args["user"],
                limit=args["limit"],
                sort=args["sort"],
                multireddit=args["multireddit"],
                time=args["time"]
            ).upper(),noPrint=True
        )
        try:
            return extractDetails(
                getattr(
                    reddit.multireddit(
                        args["user"], args["multireddit"]
                    ),args["sort"]
                ) (**keyword_params)
            )
        except NotFound:
            raise MultiredditNotFound("Multireddit not found")

    elif "submitted" in args:
        print (
            "submitted posts of {user}\nsort: {sort}\n" \
            "time: {time}\nlimit: {limit}\n".format(
                limit=args["limit"],
                sort=args["sort"],
                user=args["user"],
                time=args["time"]
            ).upper(),noPrint=True
        )
        return extractDetails(
            getattr(
                reddit.redditor(args["user"]).submissions,args["sort"]
            ) (**keyword_params)
        )

    elif "upvoted" in args:
        print (
            "upvoted posts of {user}\nlimit: {limit}\n".format(
                user=args["user"],
                limit=args["limit"]
            ).upper(),noPrint=True
        )
        try:
            return extractDetails(
                reddit.redditor(args["user"]).upvoted(limit=args["limit"])
            )
        except Forbidden:
            raise InsufficientPermission("You do not have permission to do that")

    elif "post" in args:
        print("post: {post}\n".format(post=args["post"]).upper(),noPrint=True)
        return extractDetails(
            reddit.submission(url=args["post"]),SINGLE_POST=True
        )

def extractDetails(posts,SINGLE_POST=False):
    """Check posts and decide if it can be downloaded.
    If so, create a dictionary with post details and append them to a list.
    Write all of posts to file. Return the list
    """

    postList = []
    postCount = 0

    allPosts = {}

    print("\nGETTING POSTS")
    postsFile = createLogFile("POSTS")

    if SINGLE_POST:
        submission = posts
        postCount += 1 
        try:
            details = {'postId':submission.id,
                       'postTitle':submission.title,
                       'postSubmitter':str(submission.author),
                       'postType':None,
                       'postURL':submission.url,
                       'postSubreddit':submission.subreddit.display_name}
        except AttributeError:
            pass

        result = matchWithDownloader(submission)

        if result is not None:
            details = result
            postList.append(details)

        postsFile.add({postCount:details})

    else:
        try:
            for submission in posts:
                postCount += 1

                if postCount % 100 == 0:
                    sys.stdout.write("• ")
                    sys.stdout.flush()

                if postCount % 1000 == 0:
                    sys.stdout.write("\n"+" "*14)
                    sys.stdout.flush()

                try:
                    details = {'postId':submission.id,
                            'postTitle':submission.title,
                            'postSubmitter':str(submission.author),
                            'postType':None,
                            'postURL':submission.url,
                            'postSubreddit':submission.subreddit.display_name}
                except AttributeError:
                    continue

                result = matchWithDownloader(submission)

                if result is not None:
                    details = {**details, **result}
                    postList.append(details)

                allPosts[postCount] = details
        except KeyboardInterrupt:
            print("\nKeyboardInterrupt",noPrint=True)
        
        postsFile.add(allPosts)

    if not len(postList) == 0:
        print()
        return postList
    else:
        raise NoMatchingSubmissionFound("No matching submission was found")

def matchWithDownloader(submission):

    if 'gfycat' in submission.domain:
        return {'postType': 'gfycat'}

    elif 'imgur' in submission.domain:
        return {'postType': 'imgur'}

    elif 'erome' in submission.domain:
        return {'postType': 'erome'}

    elif 'redgifs' in submission.domain:
        return {'postType': 'redgifs'}

    elif 'gifdeliverynetwork' in submission.domain:
        return {'postType': 'gifdeliverynetwork'}

    elif submission.is_self:
        return {'postType': 'self',
                'postContent': submission.selftext}

    try:
        return {'postType': 'direct',
                'postURL': extractDirectLink(submission.url)}
    except DirectLinkNotFound:
        return None        

def extractDirectLink(URL):
    """Check if link is a direct image link.
    If so, return URL,
    if not, return False
    """

    imageTypes = ['.jpg','.png','.mp4','.webm','.gif']
    if URL[-1] == "/":
        URL = URL[:-1]

    if "i.reddituploads.com" in URL:
        return URL

    elif "v.redd.it" in URL:
        bitrates = ["DASH_1080","DASH_720","DASH_600", \
                    "DASH_480","DASH_360","DASH_240"]
                    
        for bitrate in bitrates:
            videoURL = URL+"/"+bitrate

            try:
                responseCode = urllib.request.urlopen(videoURL).getcode()
            except urllib.error.HTTPError:
                responseCode = 0

            if responseCode == 200:
                return videoURL

        else:
            raise DirectLinkNotFound

    for extension in imageTypes:
        if extension in URL.split("/")[-1]:
            return URL
    else:
        raise DirectLinkNotFound
