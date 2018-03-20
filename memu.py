from __future__ import print_function

import json
import os
import re
import sys
    
# Don't change anything in this file unless you know what you're doing.
# ==================================================================================================================

file = None
button_points = {}
button_rects = {}
resolution = (1280,720)
time = 0

def do_input():
    return input()

def wait(amount):
    global time
    time = time + amount

def error(message):
    print(message)
    do_input()
    sys.exit(1)

def repeat_generator_for(fn, seconds):
    global time
    initial = time
    milliseconds = seconds * 1000

    while time - initial < milliseconds:
        fn()

def click_loc(loc, time):
    global file
    global resolution
    # global time

    def scale(xy):
        global resolution
        return (int(xy[0]*resolution[0]/1280), 
                int(xy[1]*resolution[1]/720))

    # button click
    x, y = scale(loc)
    file.write("{}--VINPUT--MULTI:1:0:{}:{}\n".format(time, x, y))
    # file.write("0ScRiPtSePaRaToR{0}|{1}|MULTI:1:0:{2}:{3}ScRiPtSePaRaToR{4}\n".format(
    #     resolution[0], resolution[1], x, y, time))

    # This is the delay between pressing the button and releasing the button.  If you set it to be too fast,
    # the device won't register a click properly.  In my experience 100ms is about as fast as you can get
    # to have all clicks properly registered.
    # wait(1000)

    # button release
    file.write("{}--VINPUT--MULTI:1:1:-1:0\n".format(time + 500000))
    # file.write("0ScRiPtSePaRaToR{0}|{1}|MULTI:0:6ScRiPtSePaRaToR{2}\n".format(resolution[0], resolution[1], time))
    # file.write("0ScRiPtSePaRaToR{0}|{1}|MULTI:0:6ScRiPtSePaRaToR{2}\n".format(resolution[0], resolution[1], time))
    # file.write("0ScRiPtSePaRaToR{0}|{1}|MULTI:0:1ScRiPtSePaRaToR{2}\n".format(resolution[0], resolution[1], time))
    # file.write("0ScRiPtSePaRaToR{0}|{1}|MSBRL:-1158647:599478ScRiPtSePaRaToR{2}\n".format(resolution[0], resolution[1], time))

    # This is the delay between finishing one click and beginning the next click.  This needs to account
    # for how fast the game can transition from one screen to the next.  For example, if you're repeatedly
    # clicking a buy button with the game not really doing anything between each click, this can be very
    # low.  On the other hand, if a click causes the game to transition from one screen to another (e.g.
    # using a portal and the game having to load into Orvel and load an entirely new area) then it should
    # be fairly high.
    # wait(wait_milliseconds)

def click_button(button, wait_milliseconds):
    global button_points
    loc = button_points[button]
    return click_loc(loc, wait_milliseconds)

def click_rect(rect, wait_milliseconds, dont_click = None):
    '''Click a single rectangle, optionally *not* clicking in any one of a list of rectangles'''

    global button_rects
    coords = button_rects[rect]
    centerx = int((coords[0][0] + coords[1][0]) / 2)
    centery = int((coords[0][1] + coords[1][1]) / 2)
    return click_loc((centerx, centery), wait_milliseconds)

def click_rects(rect_list, wait_milliseconds, dont_click = None):
    '''Click a list of rectangles, one after the other with a specified delay between each click.
       By passing a list for the `dont_click` argument, the algorithm will guarantee *not* to click
       any point in the specified list of rectangles.'''
    for r in rect_list:
        click_rect(r, wait_milliseconds, dont_click=dont_click)

def prompt_user_for_int(message, default=None, min=None, max=None):
    result = None
    while True:
        print(message, end='')
        result = do_input()

        if default is not None and len(result) == 0:
            result = default
            break

        if not is_integer(result):
            print('Value is not an integer.')
            continue

        result = int(result)
        if min is not None and result < min:
            print('Invalid value.  Must be at least {0}'.format(min))
            continue

        if max is not None and result > max:
            print('Invalid value.  Must be no larger than {0}'.format(max))
            continue

        break
    return int(result)

def prompt_choices(message, choices, default=None):
    result = default
    choice_str = '/'.join(choices)
    default_str = ' (default={0})'.format(default) if default else ''

    lower_choices = [x.lower() for x in choices]

    message = '{0} ({1}){2}: '.format(message, choice_str, default_str)
    while True:
        print(message, end='')
        input = do_input()
        if len(input) == 0:
            if default is not None:
                return default
            continue

        input = input.lower()
        if input in lower_choices:
            return input

    return None

def prompt_user_yes_no(message, default=False):
    result = default
    message = "{0} (Y/N) (default={1}): ".format(message, "Y" if default else "N")
    while True:
        print(message, end='')
        input = do_input()
        if len(input) == 0:
            result = default
            break
        input = input.lower()
        if input == 'n':
            result = False
            break
        if input == 'y':
            result = True
            break
    return result

def find_memu_install():
    prog_files = None
    if sys.platform == 'win32':
        prog_files = os.environ["ProgramFiles"]

    if not prog_files:
        error('Could not get program files folder.  Exiting...')

    microvirt_folder = os.path.join(prog_files, 'Microvirt')
    if not os.path.exists(microvirt_folder):
        error('Could not find Microvirt folder.  Exiting...')

    memu_folder = os.path.join(microvirt_folder, 'MEmu')

    memu_scripts_folder = os.path.join(memu_folder, 'scripts')
    memu_info_file = os.path.join(memu_scripts_folder, 'info.ini')
    if not os.path.exists(memu_info_file):
        error('Missing or invalid MEmu macro folder.  Record an empty macro via the MEmu UI then run this script again.')

    return memu_scripts_folder

def is_integer(s):
    try:
        n = int(s)
        return True
    except:
        pass
 
    return False

def select_macro_interactive(file):
    index = 0
    file_names = [0] * 50
    macro_names = [0] * 50

    for line in file:
        if line[0] == '[':
            file_names[index] = re.sub("\D", "", line.replace('%20', '').replace('%3A', ''))
        if line[:4] == 'name':
            macro_names[index] = line[5:].strip()
            print("{}) {}".format(index + 1, line[5:].strip()))
            index = index + 1

    value = prompt_user_for_int('Enter the macro you wish to overwrite: ', min=1, max=index+1)
    file_name = file_names[value - 1]
    macro_name = macro_names[value - 1]

    return (file_name, macro_name)

def select_resolution_interactive():
    global resolution
    while True:
        print('Enter your emulator resolution (or press Enter for 1280x720): ', end = '')
        res = do_input().strip()
        if len(res) == 0:
            resolution = (1280, 720)
            return
        else:
            match = re.fullmatch(r'(\d+)x(\d+)', res)
            if match is not None and is_integer(match[1]) and is_integer(match[2]):
                resolution = (int(match[1]), int(match[2]))
                return

def get_memu_macro_interactive():
    memu_folder = find_memu_install()
    info_file = os.path.join(memu_folder, 'info.ini')
    fp = open(info_file, 'r')
    # json_obj = json.load(fp)
    (macro_key, name) = select_macro_interactive(fp)
    macro_key = "{}.{}".format(macro_key, "mir")
    macro_file = os.path.join(memu_folder, macro_key)

    fp.close()
    return (name, macro_file)

def initialize(points, rects):
    global button_points
    global button_rects
    select_resolution_interactive()

    button_points = points
    button_rects = rects

def load_macro_file():
    global file
    name = None
    file_path = None
    # get_memu_macro_interactive()
    (name, file_path) = get_memu_macro_interactive()

    file = open(file_path, 'w')
    return (name, file_path)

def close():
    global file
    file.close()