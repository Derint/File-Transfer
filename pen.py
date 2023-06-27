import urllib.parse, requests
from time import sleep, time
import os, sys, re, argparse, json
from bs4 import BeautifulSoup
from datetime import datetime
from dateutil import parser
from math import floor, log


# Crawler function
def crawler(url):
    global links, folders, l, n
    animate();l+=1
    
    req, _ = getRequest(url, verbose=False)
    soup = BeautifulSoup(req.content, features='html.parser')

    for href in soup.find_all('a'):
        if href.text == '..':continue
            
        # Href problem (i.e href='abs-path' or href='full-path')
        link = index_link 
        if len([_ for _ in href.get('href').replace('%2F', '/').split('/') if _])==1:
            link +=  url.replace(index_link, '')
        link +=  href.get('href')
            
        if href.text.endswith('/'):
            crawler(link)
        else:
            links.append(link)


# Saving File
def saveFile(url, path, fold_name, chunk_size=16 * 10240, remain=[], char1="█", char2=' ', div=4):
    global is_conn_problem
    req, mode = getRequest(url, 1, verbose=False)
    if req==-1:is_conn_problem=True; return False, '', 0

    total_length = getFileSize(req)
    fn = FileName(url, directory, fold_name, only_name=True)
    path = os.getcwd() + slash + fn if path in ['', None] else path
    if total_length > 1e7 and chunk_size<chunk_size*10: chunk_size *= 10

    # formated filename
    fn = formatFileName(url)
    tmp_size=0
    
    go=True
    try:
        while go:
            try:
                with open(path, mode=mode) as f:
                    for chunk in req.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        tmp_size += len(chunk)

                        # Progress bar
                        style_ = progressBarStyle(fn, tmp_size, total_length, char1=char1, char2=char2, 
                                                    div=div, remain=remain, moreFiles = remain )
                        print(style_ , end='')

                    if tmp_size>=total_length:break
                    
            except Exception as e:
                with open('Exception.txt', 'a') as f:
                    f.write(f"Time:{now}\nURL: {url}\nException: {e}\n")
                connectionErrorLoop('')
                req, mode = getRequest(url, 3, verbose=True, start_index=tmp_size)

                if req==-1:
                    if os.path.exists(path):
                        os.remove(path);
                        is_conn_problem=True;go=False

    except (ConnectionResetError):
        connectionErrorLoop("Save file")
        
    except KeyboardInterrupt:
        if os.path.exists(path):os.remove(path)
        return False, '', 0

    except Exception as e:
        print("EXCEPTION OCCURED: ", e)
        sys.exit()
    else:
        return True, path, total_length

# Network/Connection functions
def getRequest(url, max_tries=8, verbose=True, start_index=0):
    headers = {'Range': f'bytes={start_index}-'}
    encoded_url = urllib.parse.quote(url, safe=':/%.=+-')
    while max_tries!=-1:
        try:
            if verbose:
                backspace(30)
                print('\r *Requesting Access...', end='')
            return requests.get(encoded_url, stream=True, headers=headers, timeout=5), 'wb' if start_index==0 else 'ab'
        except KeyboardInterrupt:
            sys.exit()
        except:
            if max_tries!=0:
                connectionErrorLoop("in Getting Request")
            max_tries-=1

    backspace(40)
    print(" \r  [!]  Connection with Host Network Failed.", end='')
    sleep(1.5)
    return -1, -1
    
def getLastModifiedTimeFile(path):
    return os.path.getmtime(path)

def getLastModifedTimeURL(url):
    r, _ = getRequest(url, verbose=False)
    return parser.parse(r.headers['last-modified']).timestamp() if r.status_code!= 404 else None

def isModifiedFile(link, filepath):
    urlTS = getLastModifedTimeURL(link)
    return urlTS > getLastModifiedTimeFile(filepath) if urlTS is not None else None

def check_url(url):
    print("\r  [*]  Checking url ... ", end='\r')
    msg = "\r  [-]  Invalid URL or Server not active\n"

    r, _ = getRequest(url, 1)
    if r!= -1 and r.status_code in [200, 406]:
        return r
    
    backspace(20)
    print(msg); 
    exit()

def getFileSize(request):
    return int(request.headers.get('content-length'))

    
# String Formating
def backspace(n=0):
    print(f"\r {' '*(os.get_terminal_size()[0]-n)}", end='\r')

def getSplit(link): 
    return  '%2F' if '%2F' in link else '/'

def getPlainText(text):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(current_dir+slash+"ASCII-Encoding.json") as f:
        switch_elts = json.load(f)

    for i in switch_elts.keys():
        if i in text:
            text = text.replace(i, switch_elts[i])
    return text

def FileName(link, directory, fold_name, only_name=False):
    rp = getSplit(link)
    file_name = getPlainText(os.path.basename(link.replace(rp, '/')))
    if only_name:
        return file_name

    file_dir = getFolderName(link, fold_name) + slash
    return directory + file_dir + file_name

def getList(list_):
    """Removes blank spaces from the lists"""
    return list(filter(lambda x: x!='', list_))

def getDirName(url):
    """It returns the Main Folder name where all files/directories will be saved"""
    tmp_fold = url.replace(index_link, '')
    tmp_fold = tmp_fold.replace(getSplit(url), slash).replace('/', '')
    if tmp_fold=='':
        fold_name = UNKNOWN_FILE_NAME
    else:
        if len(getList(tmp_fold.split(slash))) > 1:
            fold_name =  getList(tmp_fold.split(slash))[-1]  
        else:
            fold_name=tmp_fold[:-1]
    
    return fold_name.replace(slash, '')

def getFolderName(link, fold_name):
    "It Return the Main folder Name + the directory of files"
    rp = getSplit(link) 
    tmpDir = os.path.dirname(link.replace(rp, slash).replace(index_link, ''))

    if not fold_name.startswith('UKN-FIL-'):
        dir_split = tmpDir.split(slash)
        idx = dir_split.index(fold_name)
        x = 0 if ndf else 1
        tmpDir = "/".join(dir_split[idx+x:])

    tmpDir2 = getPlainText(tmpDir.replace('/', slash))
    if tmpDir2==url[:-1].replace('/', slash): return ''

    if ndf and not fold_name.startswith('UKN-FIL-'):
        split_dir = tmpDir2.split(slash)
        return f"{slash}".join(split_dir[1:])if len(split_dir)>1 else ''
    return tmpDir2

def getFolders(links, fold_name):
    folders = set()
    for folder in links:
        tmpFn = getFolderName(folder, fold_name)
        folders.add(tmpFn+slash)
    return list(folders)


# System Functions
def createFolders(folders, location):
    for folder in folders:
        loc = location + slash + folder
        if not os.path.isdir(loc):
            os.makedirs(loc)
            

# Animations
def animate():
    global l, n
    print(f"\r\tGetting all the links " + '.' * l, end='\r')
    if l > n: backspace(n=50);l=1

def getStyle():
    termianl_s = os.get_terminal_size()[0]
    if termianl_s<=49:style=3
    elif 49< termianl_s < 110:style=2
    else:style=1
    return style

def progressBarStyle(fn, tmp_size, total_length, char1, char2, div, remain, moreFiles=True):
    style = getStyle()
    cal = round(tmp_size / total_length * 100, 2)
    s = f'{convert_size(tmp_size)} / {convert_size(total_length)}' 
    prog_bar = f"{char1 * (int(cal / div))}{char2 * int(100 / div - int(cal / div))}"
    style_ = f'\r  [{fn} | {prog_bar} |  {s.ljust(20)} ]'
                
    # for one file
    if not moreFiles: return style_
    
    cal2 = round(remain[0]/remain[1] * 100, 2)
    tmp_cal2 = f"{remain[0]} of {remain[1]} file(s) "
    per_str = f"({str(cal).center(6)} %)"
   
    if style==1:
        style_ = f' {style_}  {tmp_cal2} '
    elif style==2:
        style_ = f'\r  [ {prog_bar} ]   {tmp_cal2} '
    else:
        style_ = f"\r  {per_str} {tmp_cal2} " 
        
    if style==1:backspace(10)
    return style_

def formatFileName(link, tl=25):
    fn, ext = os.path.splitext(FileName(link, directory, fold_name, only_name=True))
    fnL, extL = int(tl*0.80), int(tl * 0.20)
    
    if len(fn)>fnL: fn = fn[:fnL]
    if len(ext)>extL:
        ext = '.'+ext[1:][-extL+1:]
    return str(fn+ext).strip().center(tl)

def connectionErrorLoop(funcName, n=8):
    backspace(n=5)
    for i in range(n, 0, -1):
        print(f"\r  Connection Problem {funcName}: Reconnecting in {i} secs..", end="")
        sleep(1);


# Calculation Functions
def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(floor(log(size_bytes, 1024)))
   p = pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
    m, s = 'm', 's'
    if minutes:
        m = f':{minutes}m' if minutes>9 else f':0{minutes}m'
    if seconds:
        s = f':{seconds}s' if seconds>9 else f':0{seconds}s'
    return "%d%s%s" % (hour, m, s)

def noOfFolders(path):
    return sum([len(j) for _, j,_ in os.walk(path)])


# Reading Terminal Arguments
def getArguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', '-u', dest='url', help='URL of File to be downloaded.')
    parser.add_argument('--Fold_name', '-Fn', dest='folder_name', help="Folder Name In which you want to save all the downloaded files.")
    parser.add_argument('--todirectory', '-dir', dest='dir', help="Directory Path to save all the file(s) ")
    parser.add_argument('-ndf', action='store_true',  help="Directly Just Download the File i.e No Default Directory ")
    return parser.parse_args()


args = getArguments()
url =  args.url
m_fold_name = args.folder_name
directory = args.dir
ndf = args.ndf

l, n, size, c = 1, 8, 0, 0
links = []
slash = '\\' if os.name in ['nt', 'dos'] else '/'
is_conn_problem = False

now = datetime.now()
UNKNOWN_FILE_NAME = 'UKN-FIL-' + str(now.strftime("%d-%m-%y-%H"))


if not m_fold_name: m_fold_name = "Downloaded-Files"
m_fold_name += slash

if ndf: m_fold_name = ''
    
if not directory: directory = os.getcwd()
    
if not os.path.isdir(directory):
    print("\r  [!]  Invalid Directory Path ... ");exit()

if directory.startswith('.' +slash):
    directory = os.getcwd() + directory.replace('.', '')

directory += slash + m_fold_name

if not os.path.isdir(directory): os.mkdir(directory)

if url is None:
    url = input("\n  [>]  Enter URL: ").strip()
    if not url:
        print('\r  [!]  Invalid Url '); exit()

if not url.endswith('/'): url += '/'

# Getting index link
try:
    index_link = re.search(r'http[s]{,1}://.*?/', url).group(0)
except Exception as e:
    print(e)
    print('\r  [!]  Invalid Url '); exit()

#Checking if the url is working
check_url(url)
s_time = time()
sub_time = 0
fold_name = getDirName(url)

# For Single File
print(f"\r Checking if its a File ...", end='')
sleep(2)
if getRequest(url)[0].headers.get('last-modified'):
    fname = directory+slash+ FileName(url, directory, fold_name, True)
    if not os.path.isfile(fname):
        if saveFile(url, fname, fold_name)[0]:
            backspace(n=20)
            print("\r  [+]  Download Complete")
    else:
        backspace(n=20)
        print("\r  [o]  File Already Downloaded ")
    exit()


# For Multiple files
directory +=  getPlainText(fold_name) + slash if not ndf else ''
crawler(url)
backspace()

if not links:
    print("\r  [!]  No Files were found !!!"); 
    exit()

# Creating Directories
print('\r  *Creating Directories ....', end='')
folders = getFolders(links, fold_name)
createFolders(folders, directory)
backspace(30)

# Checking if the file is already present in folder
links_2_be_downloaded = []
for idx, link in enumerate(links):
    fn = FileName(link, directory, fold_name)
    print(f'\r   *Checking for Previous/Modified File ({round(idx/len(links)*100)}%)... ', end='')
    if not os.path.isfile(fn)  or isModifiedFile(link, fn) :
        links_2_be_downloaded.append((link, fn))
backspace(n=20)

if not links_2_be_downloaded:
    print(f"\r  [+]  All files Already Downloaded : {directory}")
    exit()

# Downloading the File(s)
try:
    for idx, (link, path) in enumerate(links_2_be_downloaded):
        ok, _, tsize = saveFile(link, path, fold_name,remain=[idx+1, len(links_2_be_downloaded)])
        if ok:size+=tsize; c+=1
except KeyboardInterrupt:
    backspace(30)
    print("KeyBoard Interruption Occured"); ok=False

e_time = time()
backspace(5)

emptyDir = [path_ for path_, _, _ in os.walk(directory) if not(os.listdir(path_))]
if emptyDir:
    uc = input(f"  [>]  Found {len(emptyDir)} empty directories. Do you want to delete {'it' if len(emptyDir)==1 else 'them'} (y/n)? ")
    if 'y' in uc:
        map(lambda x: os.removedirs(x), emptyDir)
        print("  [+]  Empty Directories Purged...\n")

af_num = noOfFolders(directory)
print(f"  [INFO]  Files saved @{directory}")
print(f'\r  [INFO]  Downloaded {c} File(s), {len(folders)} Folder(s), size : {convert_size(size)} ')
print("\r  [INFO]  Download Time : ", convert(round(e_time - s_time -sub_time)))
if is_conn_problem:
    print("  [!]  Some Files were not able to be Downloaded. Pls Re-run the program to download them.")
else:
    if ok:print("\r  [+]\t  Download Complete")