import urllib.parse, requests, logging
from time import sleep, time
import os, sys, re, argparse, json
from bs4 import BeautifulSoup
from datetime import datetime
from math import floor, log
from pathlib import Path
from colorama import Back, Fore, Style
from dateutil import parser as dateutil_parser

import platform

if platform.system()=='Windows':
    from colorama import just_fix_windows_console
    just_fix_windows_console()



# Crawler Function
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

# File Saving Function
def saveFile(url, path, chunk_size=3 * 1024 * 100, remain=[], char1="█", char2=' ', div=4): #
    global is_conn_problem, skip, EXCEPTION_OCCURED, ONLY_ONCE, MAX_TRIES, INC_DWD_FILES
    FALSE_COND = False, '', 0

    req, mode = getRequest(url, 1, verbose=ONLY_ONCE)
    if req == -1:
        is_conn_problem = True
        return FALSE_COND

    ONLY_ONCE = False
    total_length = getFileSize(req)
    fn = FileName(url, only_name=True)
    path = CURRENT_WD + os.path.sep + fn if path in ['', None] else path
    if total_length > 1e7 and chunk_size < chunk_size * 10:
        chunk_size *= 10

    # formatted filename
    fn = formatFileName(url)
    tmp_size = 0

    go = True
    try:
        while go:
            try:
                with open(path, mode=mode) as f:
                    for chunk in req.iter_content(chunk_size=chunk_size):
                        f.write(chunk)
                        tmp_size += len(chunk)
                        # Progress bar
                        style_ = progressBarStyle(
                            fn, tmp_size, total_length, char1=char1, char2=char2, div=div,
                            remain=remain, moreFiles=remain)
                        print(style_, end='')
                    break

            except KeyboardInterrupt:
                keyboardIntruption(req, path, fn)
                skip = True
                sleep(1.5)
                return FALSE_COND

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.HTTPError) as e:
                req, mode = getRequest(url, MAX_TRIES, True, tmp_size)

                if req == -1:
                    INC_DWD_FILES.append((url, path, tmp_size))
                    os.remove(path)
                    return FALSE_COND
            except Exception as e:
                logging.exception(e)

    except Exception as EXEC:
        log_exeception(EXEC, True)
        sys.exit()
    return True, path, total_length

def keyboardIntruption(req, path, fn):
    backspace(5)
    req.close()
    if os.path.exists(path):
        os.remove(path)
    print(f"\r  * Skipping {fn} File....", end='')

def log_exeception(exception, verbose=False):
    logger.warning(f"EXCEPTION OCCURED:: {exception}")
    if verbose:
        print(f"EXCEPTION OCCURED:: {exception}")

# Network/Connection functions
def getRequest(url, max_tries=8, verbose=True, start_index=0):
    headers = {'Range': f'bytes={start_index}-'}
    encoded_url = urllib.parse.quote(url, safe=':/%=+-')
    _maxtries = 1
    while max_tries!=-1:
        try:
            if verbose:
                backspace(30)
                print('\r *Requesting Access...', end='')
            r = requests.get(encoded_url, stream=True, headers=headers, timeout=5)
            return r, 'wb' if start_index==0 else 'ab'
        
        except KeyboardInterrupt:
            backspace()
            print("\r  ~ KeyBoard Interruption Occured ")
            sys.exit()
        except Exception as e:
            if max_tries!=0:
                connectionErrorLoop("in Getting Request", _maxtries)
                _maxtries+=1
            max_tries-=1    

    logger.warning("Failed to Establised connection with Host Network")

    backspace(20)
    print(" \r  [!]  Connection with Host Network Failed.", end='')
    sleep(1.5)
    return -1, -1
    
def getLastModifiedTimeFile(path):
    return os.path.getmtime(path)

def getLastModifedTimeURL(url):
    r, _ = getRequest(url, verbose=False)
    t = dateutil_parser.parse(r.headers['last-modified']).timestamp() if r.status_code!= 404 else None
    return t

def isModifiedFile(link, filepath):
    urlTS = getLastModifedTimeURL(link)
    return urlTS > getLastModifiedTimeFile(filepath) if urlTS is not None else None

def check_url(url):
    print("\r  [*]  Checking url ... ", end='\r')
    msg = "\r  [-]  Invalid URL or Server not active\n"
    if url.startswith('http'):
        r, _ = getRequest(url, 0)
        if r!= -1 and r.status_code in [200, 406, 206]:
            return r
    backspace(20)
    print(msg); 
    logger.warning("Invalid URL or Server not active")
    exit()

def getFileSize(request):
    return int(request.headers.get('content-length'))


# String Formating
def backspace(n=0):
    print(f"\r {' '*(os.get_terminal_size()[0]-n)}", end='\r')

def getSplit(link): 
    return  '%2F' if '%2F' in link else '/'

def getPlainText(text):
    global switch_elts
    for i in switch_elts.keys():
        if i in text:
            text = text.replace(i, switch_elts[i])
    return text

def getFolderName(link):
    "It Return the Main folder Name + the directory of files"
    tmpDir = link.replace(index_link, '')
    tmpDir = os.path.dirname(tmpDir.replace("%2F", '/'))
    tmp_fold_name = fold_name if not ndf else ''
    if fold_name.startswith("UKN-FIL"):
        return directory+tmp_fold_name+slash+getPlainText(tmpDir)
    
    dirSplit = tmpDir.split('/')
        
    idx = dirSplit.index(fold_name)
    idx = idx+ 1 if ndf else idx
    tmpDir = "/".join(dirSplit[idx:])
    tmpDir = tmpDir.replace('/', slash)# For windows
    return getPlainText(directory + tmpDir)

def FileName(link, only_name=False):
    link = link.replace('%2F', '/')
    file_name = getPlainText(os.path.basename(link))
    if only_name:
        return file_name
    return getFolderName(link) + slash + file_name

def getList(list_):
    return list(filter(lambda x: x!='', list_))

def getDirName(url):
    if url.replace(index_link, '')=='':
        return UNKNOWN_FILE_NAME
    url_ = url[:-1]
    tmp_fold = url_.replace(index_link, '')
    tmp_fold = tmp_fold.replace(getSplit(url_), slash)
    if (len(getList(tmp_fold.split(slash)))) > 1:
        return getList(tmp_fold.split(slash))[-1]
    tmp_fold = tmp_fold[:-1] if tmp_fold.endswith('/') else tmp_fold
    return tmp_fold

def getFolders(links):
    folders = set()
    for folder in links:
        tmpFn = getFolderName(folder)
        folders.add(tmpFn+slash)
    return list(folders)

def get_links_2_be_dwd(links):
    links_2_be_downloaded = []
    for idx, link in enumerate(links):
        fn = FileName(link)
        if fn.endswith(slash):continue
        print(f'\r   *Checking for Previous/Modified File ({round(idx/len(links)*100)}%)... ', end='')
        if not os.path.isfile(fn)  or isModifiedFile(link, fn):
            links_2_be_downloaded.append((link, fn))
    return links_2_be_downloaded


# System Functions
def createFolders(folders):
    for folder in folders:
        if not os.path.isdir(folder):
            os.makedirs(folder)
            
def check_empty_dir(directory):
    emptyDir = [path_ for path_, *_ in os.walk(directory) if not(os.listdir(path_))]
    if emptyDir:
        try:    
            uc = input(f"  [>]  Found {len(emptyDir)} empty directories. Do you want to delete {'it' if len(emptyDir)==1 else 'them'} (y/n)? ")
            if 'y' in uc:
                list(map(lambda x: os.removedirs(x), emptyDir))
                print("  [+]  Empty Directories Purged...")
        except:
            pass
        
        print()

# Animations
def animate():
    global l, n
    print(f"\r {' '*5}Getting all the links " + '.' * l, end='\r')
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
    s = f'{convert_size(tmp_size).center(10)}/ {convert_size(total_length)}' 
    prog_bar = f"{char1 * (int(cal / div))}{char2 * int(100 / div - int(cal / div))}"
    style_ = f'\r  [{fn} | {prog_bar} |  {s.ljust(len(s))} ]'
                
    # for one file
    if not moreFiles: return style_
    
    tmp_cal2 = f"{remain[0]} of {remain[1]} file(s) "
    per_str = f"({str(cal).center(6)} %)"

   
    if style==1:
        style_ = f' {style_}  {tmp_cal2} '
    elif style==2:
        style_ = f'\r  [ {prog_bar} ]   {tmp_cal2} '
    else:
        style_ = f"\r  {per_str} {tmp_cal2} " 

    return style_

def formatFileName(link, tl=25):
    fn, ext = os.path.splitext(FileName(link, only_name=True))
    fnL, extL = int(tl*0.80), int(tl * 0.20)
    
    if len(fn)>fnL: fn = fn[:fnL]
    if len(ext)>extL:
        ext = '.'+ext[1:][-extL+1:]
    return str(fn+ext).strip().center(tl)

def connectionErrorLoop(funcName, tryNo, n=8):
    backspace(n=5)
    for i in range(n, 0, -1):
        print(f"\r [{tryNo}/{MAX_TRIES}] Connection Problem {funcName}: Reconnecting in {i} secs..", end="")
        sleep(1);
    backspace(10)

def logAnimation():
    print("\r Debugging Started", end='')
    sleep(1)
    print("\r Program Activity Will be Recorded....", end='')
    sleep(1.5)
    backspace()


# Calculation Functions
def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB")
   i = int(floor(log(size_bytes, 1024)))
   p = pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def convert(seconds):
    hour = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60

    m, s= '0m:', ''
    h = f'{hour}h:' if hour else ''
    if minutes:
        m = f"0{minutes}m:" if minutes<9 else f"{minutes}m:"
    if seconds:
        s = f"{seconds}s" if seconds<9 else f"{seconds}s"
    return h+m+s

def noOfFolders(path):
    return sum([len(j) for _, j,_ in os.walk(path)])


# Reading Terminal Arguments
def getArguments():
    argParser = argparse.ArgumentParser()
    argParser.add_argument('--url', '-u',  dest='url', help='URL of File to be downloaded.')
    argParser.add_argument('--Fold_name', '-Fn', dest='folder_name', help="Folder Name In which you want to save all the downloaded files.", default="Downloaded-Files")
    argParser.add_argument('--todirectory', '-dir', dest='dir', help="Directory Path to save all the file(s) ", default=os.getcwd())
    argParser.add_argument('-ndf', action='store_true', help="Directly Just Download the File i.e No Default Directory ")
    argParser.add_argument('--addLogs', action='store_true', dest='addLogs', help="Add Log(s)")
    argParser.add_argument('--maxRetries', '-xtries', dest='max_retries', help="Maximum No of Retries to Fetch the File..", default=3, type=int)
    argParser.add_argument('--extensions', '-ext', dest='allowed_exts', help='Download only the Specified Extensions', nargs='+', default=())
    argParser.add_argument('--ignoreExt', '-IgnExt', dest='ignore_ext', help='Ignore the Specified File Extensions', nargs='+', default=())
    return argParser, argParser.parse_args()


argParser, args = getArguments()
url = args.url
m_fold_name = args.folder_name
directory = args.dir
ndf = args.ndf
addLogs = args.addLogs
MAX_TRIES = args.max_retries
ALLOWED_EXTS = tuple(args.allowed_exts)
IGNORE_EXTS = tuple(args.ignore_ext)

if ALLOWED_EXTS and IGNORE_EXTS:
    error_message = "Error: Only one of --extensions/-ext or --ignoreExt/IgnExt is allowed, not both."
    print(f"  {Fore.RED}{Style.BRIGHT}{error_message}{Style.RESET_ALL}")
    sys.exit()

l, n, size, c = 1, 8, 0, 0
links, INC_DWD_FILES = [], []
slash = os.path.sep
is_conn_problem = False
EXCEPTION_OCCURED = False
ONLY_ONCE = True
CURRENT_WD = os.getcwd()

EXCEPTION_PATH = directory + slash + "app.log"
UNKNOWN_FILE_NAME = 'UKN-FIL-' + str(datetime.now().strftime("%d-%m-%y-%H"))

m_fold_name += slash

if ndf: m_fold_name = ''
    
if directory[:2] in ['.\\', './']:
    directory = CURRENT_WD + slash + directory[2:]
    
if not os.path.isdir(directory):
    os.makedirs(directory)

if directory.startswith('.' +slash):
    directory = CURRENT_WD + directory.replace('.', '')

directory += slash + m_fold_name

if not os.path.isdir(directory):
    os.mkdir(directory)

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(EXCEPTION_PATH)]
)
logger = logging.getLogger(__name__)
if addLogs:
    logAnimation()
else:
    logging.getLogger().setLevel(logging.CRITICAL + 1)
    logging.disable(logging.NOTSET)
    logging.shutdown()
    os.remove(EXCEPTION_PATH)

logger.info("Program Started")

if url is None:
    url = input("\n  [>]  Enter URL: ").strip()
    if not url:
        print('\r  [!]  Invalid Url '); exit()

#Checking if the url is working
check_url(url)

# Reading ASCII File
current_dir = os.path.dirname(os.path.abspath(__file__))
with open(current_dir+slash+"ASCII-Encoding.json") as f:
    switch_elts = json.load(f)

# Stopwatch starts now...
s_time = time()

# For Single File
print(f"\r  *Checking if its a File ...", end='')
if getRequest(url, 3)[0].headers.get('last-modified'):
    fname = directory+slash+ FileName(url, True)
    if not os.path.isfile(fname):
        if saveFile(url, fname)[0]:
            backspace(n=10)
            print("\r  [+]  Download Complete")
    else:
        backspace(n=20)
        print("\r  [o]  File Already Downloaded ")
    exit()

# For Multiple files
if not url.endswith('/'): 
    url += '/'

# Getting index link
try:
    index_link = re.search(r'http[s]{,1}://.*?/', url).group(0)
except Exception as e:
    print('\r  [!]  Invalid Url '); exit()

fold_name = getDirName(url)
skip=False
_dir_ = getFolderName(url).rstrip(slash)

crawler(url)
backspace()

if not links:
    print("\r  [!]  No Files were found !!!"); 
    exit()

if ALLOWED_EXTS:
    backspace(20)
    print("\r  *Filtering Links Based on Passed Extension....", end='')
    links = tuple(filter(
        lambda link: Path(link).suffix[1:] in ALLOWED_EXTS,
        links
    ))

if IGNORE_EXTS:
    backspace(20)
    print("\r  *Filtering Links Based on Passed Extension....", end='')
    links = tuple(filter(
        lambda link: Path(link).suffix[1:] not in IGNORE_EXTS,
        links
    ))

backspace(30)

# Creating Directories
print('\r  *Creating Directories ....', end='')
pre_num = noOfFolders(_dir_)
folders = getFolders(links)
createFolders(folders)
backspace(30)

# Checking if the file is already present in folder
backspace(n=20)
links_2_be_downloaded = get_links_2_be_dwd(links)

if not links_2_be_downloaded:
    print(f"\r  [+]  All files Already Downloaded : @{_dir_}")
    check_empty_dir(_dir_)
    exit()

# Downloading the File(s)
try:
    for idx, (link, path) in enumerate(links_2_be_downloaded):
        ok, _, tsize = saveFile(link, path, remain=[idx+1, len(links_2_be_downloaded)])
        if ok:size+=tsize; c+=1
except KeyboardInterrupt:
    backspace(30)
    ok=False
e_time = time()
backspace(5)
check_empty_dir(_dir_)

if size==0:
    print('\r  [NOTE]  No Files were Downloaded...')
    sys.exit()

af_num = noOfFolders(_dir_)
print(f"  [INFO]  Files saved @{_dir_}")
print(f'\r  [INFO]  Downloaded {c} File(s), {af_num-pre_num} Folder(s), size : {convert_size(size)} ')
print("\r  [INFO]  Download Time : ", convert(round(e_time - s_time)))
if EXCEPTION_OCCURED:
    print(f"\r  [!]  Path Not found. (See Logs @{EXCEPTION_PATH})")   

if is_conn_problem and skip:
    print("  [!]  Some Files were not able to be Downloaded. Pls Re-run the program to download them.")
else:
    if ok:print("\r   [+]\t  Download Complete")

logger.info("Program Terminated Successfully....")
