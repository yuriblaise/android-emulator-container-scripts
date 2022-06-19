# %%
#imports
from cmath import e
from multiprocessing.connection import wait
import subprocess
import re
import os
import time
import json
import sys
import re
import argparse
from tracemalloc import start
import pandas as pd
from datetime import timedelta, datetime, timezone
import traceback

# %%
#Arguments and defaults
adb = "adb" #Adb Path
benchmark_json = "benchmark.json" # default benchmark config file
verbose = True
output_path = "/sdcard" 
serial = None
apk_folder = "apks"
device_address = 'localhost:5555'
adb_device = None # which adb device to choose if multiple are available
skip_connect = False
culebra = None
# Global Benchmark Settings
timeout = 15
poll_rate = 5
num_output_files = 1 
silent = False # configure whether scripts move on after failure
retries = 2 # number of attempts before moving on to next script or exiting
python_path = "python" # path to python executable
screenshot = True # takes a screenshot on failure
results_path = "/benchmarks/results"
#command line arguments
parser = argparse.ArgumentParser(description='Install and Run Benchmark APKs')
parser.add_argument('-q','--quiet',default=verbose,dest='verbose',action='store_const', const=not(verbose),
                    help='Supress logging and status')
parser.add_argument('-adb','--adb_path',default=adb, dest='adb',
                    help='Set the path for adb the script should use')
parser.add_argument('-s','--serial',default=serial, dest='serial',
                    help="Set the device serial of the connected adb devices you'd like to use")
parser.add_argument('-o','--output_path',default=output_path, dest='output_path',
                    help='adb device folder path to search for benchmark output files in.\
                        Pass comma seperated values to search multiple directories')
parser.add_argument('-c','--config',default=benchmark_json, dest='benchmark_json',
                    help='json config file to run benchmarks')
parser.add_argument('-apks','--apk_folder',default=apk_folder, dest='apk_folder',
                    help='Path to folder of apks to install')
parser.add_argument('-addr','--adb_address',default=device_address, dest='device_address',
                    help='Ip address and port # of the selected adb device defaults to localhost:5555')
parser.add_argument('--skip_connect',default=skip_connect, dest='skip_connect',
                    action='store_const', const=not(skip_connect),
                    help='skip connecting adb to the device, useful if adb is already connected')
parser.add_argument('-t','--timeout',default=timeout, dest='timeout',
                    help="Set the global timeout in minutes for benchmarks, defaults to 20")
parser.add_argument('-num_files','--num_output_files',default=num_output_files, dest='num_output_files',
                    help="Set the number of output files to find before moving on to the next benchmark, defaults to 1")
parser.add_argument('-p','--poll_rate',default=poll_rate, dest='poll_rate',
                    help="How often to check the disk for benchmark output files in seconds, defaults to 5")
parser.add_argument('-culebra','--culebra_config',default=culebra, dest='culebra',
                    help='Location of the culebra json config file to be used, supports custom scripts as well')
parser.add_argument('-d','--adb_device',default=adb_device, dest='adb_device',
                    help='The index of the adb device to connect to if there is more than one device; if no value is set the user will be prompted ')
parser.add_argument('-silent','--silent_fail',default=silent, dest='silent', action='store_const', const=not(silent),
                    help='Script will move on to the next app if the benchmark or install fails, false by default.')
parser.add_argument('-python','--python_path',default=python_path, dest='python_path',
                    help='PATH for python')
parser.add_argument('-r','--retries',default=retries, dest='retries',
                    help="How often to check the disk for benchmark output files in seconds, defaults to 5")
parser.add_argument('-results','--results_path',default=results_path, dest='results_path',
                    help='Absolute path to the folder where benchmark result files will be placed')

# %%
# parses arguments and updates constants if necessary
# prints an output of all the settings when done
args, unknown = parser.parse_known_args(sys.argv[1:])
args_dict = vars(args)
locals().update(args_dict)
if verbose:
    print("Settings".upper())
    print(">"*30)
    for arg in args_dict.keys():
        print(arg.capitalize() + ": \t" + str(args_dict[arg]), flush=True)
    print("<"*30,flush=True)

# %%
#Helper functions the script uses to interface with the terminal and the device via adb

#checks subprocess for error and returns false if none
def err_check(process, msg, stderr = None):
    if process.returncode != 0:
        stderr = "" if None else "\"" + stderr + "\""
        raise Exception(msg + stderr)
    return False

#handles process
def handleProcess(process, err_msg, raw_output=False):
    (stdout, stderr) = process.communicate()
    if raw_output: return stdout
    if not err_check(process,err_msg, stderr): 
        if verbose:
            print(stdout, flush=True)
        return stdout.strip().split("\n")

#handle a command taken as a string
def handleCommand(command, err_msg="", raw_output=False, force=False):
    process = subprocess.Popen(
        command.split(" "), stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, text=True
        )
    if force: process.returncode = 0
    return handleProcess(process, err_msg, raw_output)

# Get the serial of the device adb will be sending commands to
# if more than one device is connected the user will be prompted to select a device
def getDevice():
    result = handleCommand(f"{adb} devices", "ADB Failed to connect with error: \n")
    devices = [re.split('\s+', d)[0] for d in result[1:]] # cleaning devices string
    device_cnt = len(devices)
    if device_cnt > 1:
        print("More than one device connected")
        for x,d in enumerate(devices):
            print("(",x+1,")", d)
        idx = adb_device if adb_device else input("Select which device to connect to")
        return devices[int(idx) - 1]
    elif device_cnt > 0:
       return devices[0]
    else:
        raise Exception("No device found ensure that adb is connected to a device before running")

#Tries to install apks if it fails will print exception 
def installApks(folder_path, serial):
    for file in os.listdir(folder_path):
        if file.endswith(".apk"):
            try:
                if verbose: print(f'installing {file}')
                if " " in file:
                    raise NameError ("Apk filenames can't contain whitespace, please rename the file and try again")               
                handleCommand(f'{adb} -s {serial} install -g {apk_folder}/{file}')
            except Exception as e:
                print(f'installation of {file} failed with error: \"{e}\"')
                if not silent:
                    exit()
    return True

#Function takes in a single or list of x,y coords and virtually taps them on the device    
def runBenchmarks(coords, delay=3):
    if type(coords) == tuple:
        (x,y) = coords
        handleCommand(f'{adb} -s {serial} shell input tap {x} {y}')
    if type(coords) == list:
        for coord in coords:
            (x,y) = coord
            handleCommand(f'{adb} -s {serial} shell input tap {x} {y}')
            time.sleep(delay)

# return a json file as an dict
def loadJson(filename):
    with open(filename, 'r') as f:
        return json.load(f)

#Function takes in a tuple (x,y) coords and virtually taps them on the device
#if a tuple has a len of > 2 the first two entries will be taken as coords 
# and the third will be used as the delay in seconds
def tapInput(coords, delay=3):
    if type(coords) == tuple:
        (x,y) = coords
        handleCommand(f'{adb} -s {serial} shell input tap {x} {y}')
    if type(coords) == list:
        for coord in coords:
            #handling (x,y,delay) scenario
            (x,y) = coords if len(coord) == 2 else coord[:2]
            delay = delay if len(coord) == 2 else coord[2]

            handleCommand(f'{adb} -s {serial} shell input tap {x} {y}')
            time.sleep(delay)
def openPackage(package_name, serial):
    handleCommand(f'{adb} -s {serial} shell monkey -p {package_name} 1')

#checks to see if the output of the benchmark is available
#default path is sdcard/benchmarks
def outputCheck(start_time, output_path=output_path, filetype = '.csv',serial=serial):
    try:
        # Parse the file creation dates and names in output_path from adb shell 
        filepaths = []
        for path in output_path.split(","):    
            try:
                cmd = f"{adb} -s {serial} shell find {path}/ -type f -exec stat -c '%y %n' {{}} \;"
                filepaths += handleCommand(cmd)
            except Exception as e:
                print(f"Failed to search folder {path}", e)
        raw_df = pd.DataFrame(filepaths, columns=["raw_data"])
        df = raw_df["raw_data"].str.split(" /", expand=True)
        df.columns = ['created_date', 'filepath']
        df.created_date = df.created_date.astype('datetime64[ns]')
        #get files created after the start_time
        df = df[df.created_date.values > pd.Series(start_time).values[0]]
    
    
        # get files from filepaths
        files_msk = df.filepath.apply(lambda x: x[-4:]).str.contains("\.")
        filenames = df.filepath[files_msk]
        filenames = list(filenames[filenames.str.contains(filetype)].values)
        if verbose:
            print(">"*50,"\n",\
                f"start time: {start_time}\n", f"current time:{datetime.now()}")        
        return filenames
    except Exception as e:
        print("Ran into an error when checking for files, will try again...",e)
        print(">"*50,"\n",\
            f"start time: {start_time}\n", f"current time:{datetime.now()}")
        return []

# function checks for a file every x seconds and will timeout in y minutes
# a list can be passed to filter out filenames if more than one file is generated
# num_files can be used
def fileWait(start_time, poll_rate=5, timeout_min=timeout, filetype = '.csv', filter=[], num_files=1, serial=serial):
    timeout = timeout_min*60 #convert timeout from min to seconds
    while timeout > 0:
        try:
            results = outputCheck(start_time, output_path, filetype=filetype,serial=serial)
            results = list(set(results).difference(filter))
            t = time.localtime()
            ts = time.strftime("%m/%d/%Y, %H:%M:%S", t)
            if len(results) > 0:
                if len(results) >= num_files:
                    return results
            elif verbose:
                print(f"Searched for {filetype} files in {output_path} at {ts} nothing found...",flush=True)
        except Exception as e:
            print("Error Occured while waiting for file, trying again", e)
        timeout = timeout - int(poll_rate)
        time.sleep(poll_rate)
    return False

# Hacky way to confirm emulator is on from SO question/3634041
def powerOnWait(serial):
    result = []
    while len(result) < 1:
        try:
            if verbose: print("Waiting for phone to turn on please ensure usb debugging is enabled",flush=True)
            result = handleCommand(f"{adb} -s {serial} shell dumpsys connectivity | sed -e '/[0-9] NetworkAgentInfo.*CONNECTED/p' -n")
        except Exception as e:
            print("script crashed while waiting for device to power on", e,flush=True)
            print("Restarting the adb server and trying again",flush=True)
            if not skip_connect: handleCommand(f"{adb} connect {device_address}")
        if verbose: print("Waiting for device to  turn on....")
        time.sleep(3)
    print("Device is now on",flush=True)
    return True

def handleStream(command):
    process = subprocess.Popen(
        command.split(" "), stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, text=True
        )
    return process

# Waits for Activity Manager to show a package is open in logcat
def waitForOpen(package_name, serial):
    logcat_str = f"Displayed {package_name}"
    proc = handleStream(f"{adb} -s {serial} logcat")
    start = datetime.now()
    for line in proc.stdout:
        # listens to logcat for up to 20s to find logcat_str
        # Will print a message and give the app additional
        # time to load to account for any render lag
        # waits for half the activity load time  
        if logcat_str in line:
            proc.stdout.close()
            loadtime = re.findall(r"\d+s\d+ms", line)[-1]
            loadtime_float = float(loadtime.replace("ms","").replace("s","."))
            additional_time = round(loadtime_float * 0.5,2)
            print(f"{package_name} loaded in {loadtime} \n\
                Giving Activity additional {additional_time}s\
                    to load...")
            time.sleep(additional_time)            
            return True
        if datetime.now() - start > timedelta(seconds=30):
            print(f"Couldn't find logcat output for {package_name} starting benchmark anyway")
            return False


def setWritePermissions(package_name, serial):
    handleCommand(f"{adb} -s {serial} shell pm grant {package_name}\
         android.permission.WRITE_EXTERNAL_STORAGE")
# %%
# Press the back button and home button three times to
# reset to home screen to retry benchmark.
def reset():
    if verbose: print("Attempting to reset phone after failed attempt")
    for _ in range(3):
        handleCommand(f"{adb} -s {serial} shell input KEYCODE_BACK")
        time.sleep(2)
    for _ in range(3):    
        handleCommand(f"{adb} -s {serial} shell input KEYCODE_HOME")
        time.sleep(2)
# %%
def loadBenchmarks(benchmark_json,retries,screenshot):
    inputs = loadJson(benchmark_json)
    benchmarks = inputs
    tryagain = True # try again if the script fails to account for irregularities when opening a package
    # incase there is only one benchmark being configured
    benchmarks = benchmarks if type(benchmarks) == list else [benchmarks]
    index = []
    for b in benchmarks:
        for _ in range(retries):        
            try:
                #open package
                t = datetime.now(timezone.utc).astimezone()
                setWritePermissions(b['package_name'], serial)
                openPackage(b['package_name'], serial)
                waitForOpen(b['package_name'], serial)
                tapInput(b['Coords'], .3)
                
                # set benchmark specific settings
                b_timeout = b['timeout'] if 'timeout' in b.keys() else timeout
                b_poll_rate = b['poll_rate'] if 'poll_rate' in b.keys() else poll_rate
                b_poll_rate = int(b_poll_rate)
                b_num_files = b['num_output_files'] if 'num_output_files' in b.keys() else num_output_files
                b_filetype = b['filetype'] if 'filetype' in b.keys() else '.csv'
                # will check device storage for output
                r = fileWait(t, filetype=b_filetype, filter=index, timeout_min=b_timeout,
                    poll_rate=b_poll_rate, num_files=b_num_files,serial=serial)
                
                if not r:
                    raise TimeoutError(f'Timeout: No files found after {b_timeout} minutes')
                index = index + r
                print("Benchmark complete, output files \n", index,flush=True)
                break
            except Exception as e:
                print(f"Benchmark for {b['package_name']} failed.",e,flush=True)
                print(">"*50,"\n",f"Trying again...",flush=True)
                reset()
                print("Reset Complete. Benchmark restarting...")
        else:
            if silent: print(f"Silent_fail is on, moving on to next benchmark after {retries} failed attempts.")
            if screenshot:
                print("Saving Screenshot....")
                dir_path = os.path.dirname(os.path.realpath(__file__))
                try:
                    screenshot = f"{adb} -s {serial} shell screencap -p > {dir_path}/screenshot_{t}.png"
                    subprocess.Popen(
                    screenshot, stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE, text=True, shell=True
                    ).communicate()
                except Exception as e:
                    print("Failed to save screenshot_{t}.png",e)
            if not silent: exit()
    # Transfer files to results_path and exit
    if verbose: print("Pulling Files")
    for filepath in index:
        result_filename = os.path.basename(filepath)
        pull_files = f"{adb} -s {serial} pull {filepath} {results_path}/{result_filename}"
        subprocess.Popen(
        pull_files, stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, text=True, shell=True
        ).communicate()
        if verbose: print(f"Pushed {filepath} to {results_path}/")
    print("Benchmarks Complete, output files exported")

# %%
def loadCulebra(culebra_config,retries,screenshot):
    scripts = loadJson(culebra_config)
    tryagain = True # try again if the script fails to account for irregularities when opening a package
    # incase there is only one benchmark being configured
    scripts = scripts if type(scripts) == list else [scripts]
    index = []
    for b in scripts:
        for _ in range(retries):        
            try:
            # set benchmark specific settings
                b_timeout = b['timeout'] if 'timeout' in b.keys() else timeout
                b_poll_rate = b['poll_rate'] if 'poll_rate' in b.keys() else poll_rate
                b_poll_rate = int(b_poll_rate)
                b_num_files = b['num_output_files'] if 'num_output_files' in b.keys() else num_output_files
                b_filetype = b['filetype'] if 'filetype' in b.keys() else '.csv'
                b_shell = b['shell'] if 'shell' in b.keys() else False
                t = datetime.now(timezone.utc).astimezone()
                if b['adbLaunch']:
                    setWritePermissions(b['package_name'], serial)
                    openPackage(b['package_name'], serial)
                    waitForOpen(b['package_name'], serial)
                #handling custom scripts 
                if not b_shell and 'script' in b.keys():
                    handleCommand(f'{python_path} {b["script"]}', f'The culebra script {b["script"]} failed with the error: ')
                if 'script' in b.keys():                
                    handleCommand(f'{b["script"]}', f'The following command failed: "{b["script"]}"')
                    
                # will check device storage for output
                r = fileWait(t, filetype=b_filetype, filter=index, timeout_min=b_timeout,
                    poll_rate=b_poll_rate, num_files=b_num_files, serial=serial)

                if not r:
                    raise TimeoutError(f'Timeout: No files found after {b_timeout} minutes')
                index = index + r
                print("Benchmarks complete, output files \n", index,flush=True)
                break
            except Exception as e:
                print(f"Benchmark for {b['package_name']} failed.",e,flush=True)
                print(traceback.format_exc())
                print(">"*50,"\n",f"Trying again...",flush=True)
                reset()
                print("Reset Complete. Benchmark restarting...")
        else:
            if silent: print(f"Silent_fail is on, moving on to the next benchmark after {retries} failed attempts.")
            if screenshot:
                dir_path = os.path.dirname(os.path.realpath(__file__))
                print("Saving Screenshot....")
                try:
                    #Trying Culebra script as well
                    handleCommand(f'{python_path} {dir_path}/screenshot.py', f'The culebra script {b["package_name"]} failed with the error: ')
                except Exception as e:
                    print(f"Failed to save screenshot_{t}.png",e)
            if not silent: exit()
    # Transfer files to results_path and exit
    if verbose: print("Pulling Files")
    for filepath in index:
        result_filename = os.path.basename(filepath)
        pull_files = f"{adb} -s {serial} pull {filepath} {results_path}/{result_filename}"
        subprocess.Popen(
        pull_files, stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, text=True, shell=True
        ).communicate()
        if verbose: print(f"Pushed {filepath} to {results_path}")
    print("Benchmarks Complete, output files exported")



# %%
# attempt to connect to device address if skip_conenct is false
if not skip_connect: handleCommand(f"{adb} connect {device_address}")
serial = getDevice() if serial == None else serial

# %%
powerOnWait(serial)
installationFinished = installApks(apk_folder, serial)
print("Installation Complete", time.time())

# %%
if culebra:
    loadCulebra(culebra, retries, screenshot)
else:
    loadBenchmarks(benchmark_json,retries, screenshot)




    