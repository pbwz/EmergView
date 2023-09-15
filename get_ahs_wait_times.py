'''
AHS Wait Time Grabber
    - v1.0

Connects to AHS Emergency Room Wait Time API and collects
data at a set interval. Data is then saved for future use
and trend analysis.

Author: Paul Belland
'''

import time
import requests
from datetime import date,datetime

BASE_URL = 'https://www.albertahealthservices.ca/Webapps/WaitTimes/api/waittimes/'

# REGION INFO - FILES
CALGARY_E_STORE = 'calgary_e.txt'  # Emergency care
CALGARY_U_STORE = 'calgary_u.txt'  # Urgent care
EDMONTON_STORE = 'edmonton.txt'
GP_STORE = 'grandprairie.txt'
LETH_STORE = 'lethbridge.txt'
MED_STORE = 'medicinehat.txt'
RED_STORE = 'reddeer.txt'
ALL_FILES = [CALGARY_E_STORE,CALGARY_U_STORE,EDMONTON_STORE,GP_STORE,LETH_STORE,MED_STORE,RED_STORE]

# REGION INFO - HEADERS
CALGARY_E_HEADER = 'DATE,TIME,ACH,FMC,PLC,RGH,SHC'
CALGARY_U_HEADER = 'DATE,TIME,ACHC,SMCC,CCHC,OHWC,SCHC'
EDMONTON_HEADER = 'DATE,TIME,DGH,FSCH,GNCH,LCH,MCH,NCHC,RAH,STOCH,STRCH,STUCH,UAH,WVHC'
GP_HEADER = 'DATE,TIME,GPRH'
LETH_HEADER = 'DATE,TIME,CRH'
MED_HEADER = 'DATE,TIME,MCRH'
RED_HEADER = 'DATE,TIME,RDRH,IHC,LHCC'
ALL_HEADERS = [CALGARY_E_HEADER,CALGARY_U_HEADER,EDMONTON_HEADER,GP_HEADER,LETH_HEADER,MED_HEADER,RED_HEADER]

# REGION INFO - FORMAT PACKAGES - STORAGE,CITY,TYPE,# OF HOSPITALS
CALGARY_E_PACKAGE = [CALGARY_E_STORE,'Calgary','Emergency',5]
CALGARY_U_PACKAGE = [CALGARY_U_STORE,'Calgary','Urgent',5]
EDMONTON_PACKAGE = [EDMONTON_STORE,'Edmonton','Emergency',12]
GP_PACKAGE = [GP_STORE,'GrandePrairie','Emergency',1]
LETH_PACKAGE = [LETH_STORE,'Lethbridge','Emergency',1]
MED_PACKAGE = [MED_STORE,'MedicineHat','Emergency',1]
RED_PACKAGE = [RED_STORE,'RedDeer','Emergency',3]
ALL_PACKAGES = [CALGARY_E_PACKAGE,CALGARY_U_PACKAGE,EDMONTON_PACKAGE,GP_PACKAGE,LETH_PACKAGE,MED_PACKAGE,RED_PACKAGE]

# DATA COLLECTION SETTINGS
WAIT_TIME = 300   # 5 minute wait time

class Watcher:
    def __init__(self) -> None:
        self.response = None
        self.write_headers()
        
    def write_headers(self):
        '''Writes all headers to their respective files'''
        for i in range(len(ALL_FILES)):
            with open(ALL_FILES[i], 'w') as w_file:
                w_file.write(ALL_HEADERS[i]+'\n')
        
    def connect(self):
        '''
        Connects to API, saves instance of response to self.response
        Returns API connection status code
        '''
        self.response = requests.get(BASE_URL)
        self.start_time = time.time()

        return self.response.status_code
        
    def run(self):
        '''
        When called, creates a new entry into the data storage file with
        the current data and time. If status code is not 200, terminates.
        '''
        if self.response.status_code == 200:
            raw_data = self.get_raw_data()
            self.format_data(raw_data)  # formats and writes to file

    def get_raw_data(self):
        '''
        Gets raw data in form of JSON from the API in preparation for
        formatting
        '''
        raw_data = self.response.json()
        return raw_data
        
    def format_data(self, raw_data):
        '''
        Formats the raw JSON data into usable data. Should return nested
        lists of hospitals and wait times.
        '''
        c_date = self.get_date()
        c_time = self.get_time()
        
        # iterate through packages
        for package in ALL_PACKAGES:
            package_data = [c_date,c_time]
            
            file_name = package[0]
            city = package[1]
            ue_type = package[2]  # urgent/emergency type
            hosp_count = package[3]
            
            # iterate through every hospital
            for i in range(0,hosp_count):
                wait_time = raw_data[city][ue_type][i]['WaitTime']  # retrieve from dicts
                fmtd_wait_time = self.format_wait_time(wait_time)   # format
                package_data.append(fmtd_wait_time)
            
            # join and write
            fmtd_string = ','.join(package_data)
            self.write_data(file_name, fmtd_string)

        # finished executing
            self.end_time = time.time()
        
    def format_wait_time(self, wait_time):
        '''
        Formats wait time info correct form for storage
        '''
        if wait_time == 'Wait times unavailable':
            return 'Unavailable'
        else:   # form is 'hr:min'
            stripped_wait = wait_time.strip(' min')
            split_wait = stripped_wait.split(' hr ')
            fmtd_wait_time = f'{split_wait[0]}:{split_wait[1]}'
            return fmtd_wait_time
        
    def write_data(self, a_file, data):
        '''
        Writes the given data to a file
        '''
        with open(a_file, 'a') as w_file:
            w_file.write(data + '\n')
        
    def get_date(self):
        '''
        Returns the current date
        '''
        today = date.today()
        date_str = today.strftime("%m/%d/%y")
        return date_str
        
    def get_time(self):
        '''
        Returns the current time in 24 hours
        '''
        now = datetime.now()
        c_time = now.strftime("%H:%M")
        return c_time

    def get_execution_time(self):
        '''
        Returns the amount of time Watcher took
        to execute the last full cycle
        '''
        return self.end_time - self.start_time
    
def main():
    watcher = Watcher()
    response = 200
    
    while True and response == 200:
        response = watcher.connect()
        watcher.run()
        
        # ensures next call happens exactly 5 mins later
        time_elapsed = watcher.get_execution_time()
        time.sleep(WAIT_TIME - time_elapsed)
    
if __name__ == '__main__':
    main()
