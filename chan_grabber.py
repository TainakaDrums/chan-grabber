import lxml.html as html
import sys
import threading
import os.path
import os
import argparse
from itertools import chain

if sys.version_info.major == 2:
    from urlparse import urlparse
    from urllib import quote
    import urllib2
    from urllib2 import HTTPError
    import Queue as queue
else:
    from urllib.parse import urlparse
    from urllib.parse import quote
    import urllib.request as urllib2
    from urllib.error  import HTTPError as HTTPError
    import queue


class Download_pics(threading.Thread):

    def __init__ (self):
        threading.Thread.__init__(self)

    def run(self):

        while True:
            page=None
            link=q.get()
            link_on_pic=quote(link, ":/")
            file_name=link.split("/")[-1]

            if link_on_pic.startswith("//"):
                link_on_pic=parsed_link.scheme+":"+link_on_pic
            elif not link_on_pic.startswith("http"):
                link_on_pic=parsed_link.scheme+"://"+parsed_link.hostname+link_on_pic

            link_on_pic=urllib2.Request( link_on_pic, headers=headers)

            while not page:
                try:
                    page=urllib2.urlopen(link_on_pic)                    
                except HTTPError as e:
                    if e.getcode() == 503:
                        time.sleep(2)
                    else:
                        print(e.getcode(), e.url)
                        break


            if page and page.getcode() == 200 :
                data=page.read()

                if data:
                    with open( os.path.join(dir_name, file_name) , "wb") as file:
                            file.write(data)

            q.task_done()
            

def create_dir_name(parsed_link):
    thread=parsed_link.path.split("/")[-1].split(".")[0]
    section=parsed_link.path.split("/")[1]
    host=parsed_link.hostname.split(".")[-2]

    dir_name="_".join( (host, section, thread) )
    
    if os.path.split(os.getcwd())[-1] == dir_name:
        dir_name=os.getcwd()
        
    return dir_name

    

types={"all": (".jpeg", ".jpg", ".png", ".bmp", ".gif", ".webm"),
           "pic": (".jpeg", ".jpg", ".png", ".bmp"),
           "gif":  (".gif", ),
           "webm": (".webm",)
}


parser = argparse.ArgumentParser(description="Download content from imageboard thread")

parser.add_argument(
    "-l",
    "-u",
    "--url",
    "--link",
    action='store',
    dest='thread_link',
    type=str,
    required=True,
    help='Link to thread'
)

parser.add_argument(
    "-t",
    "--type",
    action='store',
    dest='types',
    type=str,
    choices=list(types.keys()),
    nargs="*",
    default= ("all",),
    required=False,
    help='Type of content'
)

parser.add_argument(
    "-n",
    "-d",
    "-o",
    "--name",
    action='store',
    dest='dir_name',
    type=str,
    required=False,
    help='Directory name'
)


if __name__ == '__main__':
    
    args = parser.parse_args()
    
    headers={"User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64; rv:21.0) Gecko/20100101 Firefox/21.0"}
    link=urllib2.Request(args.thread_link, headers=headers)
    parsed_link=urlparse(args.thread_link.strip().rstrip("/"))
    preferred_type= tuple( chain.from_iterable( (types[type]  for type in args.types) ) )


    if args.dir_name:
        dir_name=args.dir_name
    else:
        dir_name=create_dir_name(parsed_link)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

    try:
        page=urllib2.urlopen(link)
    except HTTPError as e:
        print("Can't open url. Code %d" % e.getcode() )
        exit()

    doc=html.document_fromstring(page.read())
    res=doc.findall(".//a[@target='_blank']")
    links={i.attrib['href'].split(":")[-1]    for i in res  if  i.attrib['href'].endswith(preferred_type) }

    q=queue.Queue()
    
    for link in links:
        if  not os.path.exists( os.path.join( dir_name, link.split("/")[-1])  ):
            q.put(link)


    for _ in range(10):
        thread=Download_pics()
        thread.daemon = True
        thread.start()

    q.join()
