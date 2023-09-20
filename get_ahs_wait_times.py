'''
AHS Wait Time Grabber
    - v1.1 (Database update)

Connects to AHS Emergency Room Wait Time API and collects
data at a set interval. Data is then saved for future use
and trend analysis.

Author: Paul Belland
'''

import time
import requests
from datetime import date,datetime
from db import Database

BASE_URL = 'https://www.albertahealthservices.ca/Webapps/WaitTimes/api/waittimes/'

# DB TABLES
T_CALE = ('Calgary_E', 
            ['DATE','TIME','ACH','FMC','PLC','RGH','SHC'])
T_CALU = ('Calgary_U', 
            ['DATE','TIME','ACHC','SMCC','CCHC','OHWC','SCHC'])
T_EDMN = ('Edmonton', 
            ['DATE','TIME','DGH','FSCH','GNCH','LCH','MCH','NCHC','RAH','STOCH','STRCH','STUCH','UAH','WVHC'])
T_GRPR = ('Grande_Prairie',
            ['DATE','TIME','GPRH'])
T_LETH = ('Lethbridge',
            ['DATE','TIME','CRH'])
T_MEDH = ('Medicine_Hat',
            ['DATE','TIME','MCRH'])
T_REDR = ('Red_Deer',
            ['DATE','TIME','RDRH','IHC','LHCC'])
ALL_TABLES = [T_CALE,T_CALU,T_EDMN,T_GRPR,T_LETH,T_MEDH,T_REDR]

# FORMAT PACKAGES - TABLE_NAME,CITY,TYPE,# OF HOSPITALS
CALE_PACKAGE = [T_CALE[0],'Calgary','Emergency',5]
CALU_PACKAGE = [T_CALU[0],'Calgary','Urgent',5]
EDMN_PACKAGE = [T_EDMN[0],'Edmonton','Emergency',12]
GRPR_PACKAGE = [T_GRPR[0],'GrandePrairie','Emergency',1]
LETH_PACKAGE = [T_LETH[0],'Lethbridge','Emergency',1]
MEDH_PACKAGE = [T_MEDH[0],'MedicineHat','Emergency',1]
REDR_PACKAGE = [T_REDR[0],'RedDeer','Emergency',3]
ALL_PACKAGES = [CALE_PACKAGE,CALU_PACKAGE,EDMN_PACKAGE,GRPR_PACKAGE,LETH_PACKAGE,MEDH_PACKAGE,REDR_PACKAGE]

# DATA COLLECTION SETTINGS
DB_NAME = 'wait_times.db'
WAIT_TIME = 300   # wait time
SPEC_START = False  # start at HH:MM%START_FACTOR=0:SS
SPEC_START_EXACT = False  # start at HH:MM:00
START_FACTOR = 5

class Watcher:
    '''API Watcher'''
    def __init__(self) -> None:
        self._loop = False
        self._database = Database(DB_NAME)
    
    def setup(self) -> None:
        '''Called to initially set up database.
        
        Input: None
        Return: None'''
        # creates database tables
        for table in ALL_TABLES:
            name = table[0]
            col_vals = table[1]
            self._database.create_table(name, col_vals)
        
    def start(self) -> None:
        '''Call to start API data collection loop.
        Cannot run unless database setup has been called.
        
        Input: None
        Return: None'''
        if not self._loop:
            self._loop = True
            time.sleep(self._get_start_time())  # spec start
            
            # enter loop
            while self._loop:
                start_time = time.time()
                
                # loop actions
                self._write_snapshot()
                
                # time correction
                end_time = time.time()
                time_elapsed = end_time - start_time
                time.sleep(WAIT_TIME - time_elapsed)
                
        else:
            raise Exception('Already started!')
        
    def stop(self) -> None:
        '''Stops API data collection loop
        
        Input: None
        Return: None'''
        self._loop = False
        
    def get_status(self) -> str:
        '''Returns a message regarding status of Watcher
        
        Input: None
        Return: str - status msg'''
        res = requests.get(BASE_URL)
        status = res.status_code
        
        # all possibilities
        if self._loop and status == 200:
            return 'API Healthy, Loop Active'
        elif status == 200:
            return 'API Healthy, Loop Inactive'
        elif self._loop:
            return 'API Bad Status, Loop Active'
        else:
            return 'API Bad Status, Loop Inactive'
        
    def _get_start_time(self) -> int:
        '''Returns the amount of seconds before the next
        valid time is divisble by start_factor
        
        Input: None
        Return: int'''
        exact_time = str(datetime.now()).split(':')
        c_mins = int(exact_time[1])
        c_secs = float(exact_time[-1])
        o_mins = c_mins % START_FACTOR  # over mins
        
        # start now
        if o_mins == 0 and c_secs < 10 or not SPEC_START:
            if not SPEC_START_EXACT:
                return 0
        
        # calculate start time
        w_mins = START_FACTOR - o_mins  # wait mins
        w_secs = w_mins * 60 - c_secs  # calc wait secs
        return w_secs
        
    def _write_snapshot(self) -> None:
        '''Connects to API, writes current snapshot
        of data to DB.
        
        Input: None
        Returns: None'''
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            data = response.json()
            
            # format all for writing
            for package in ALL_PACKAGES:
                table_name = package[0]
                fmtd_data = self._format_data(data, package)
                self._write_to_db(table_name, fmtd_data)
                
    def _write_to_db(self, table_name:str, wait_times:list) -> None:
        '''Writes the given formatted data to it's respective
        table inside of the database
        
        Input: str - table name, list - region wait times
        Return: None'''
        self._database.insert(table_name,wait_times)
        
    def _format_data(self, raw_data:dict, package:list) -> list[str]:
        '''
        Formats the raw JSON data into usable data. Should return nested
        lists of hospitals and wait times.
        
        Input: dict - api data, list - info for formatting
        Return: list - region wait times'''
        c_date = self._get_date()
        c_time = self._get_time()
        
        # read package, get info
        package_data = [c_date,c_time]
        
        city = package[1]
        ue_type = package[2]  # urgent/emergency type
        hosp_count = package[3]
        
        # iterate through every hospital
        for i in range(0,hosp_count):
            wait_time = raw_data[city][ue_type][i]['WaitTime']  # retrieve from dicts
            fmtd_wait_time = self._format_wait_time(wait_time)   # format
            package_data.append(fmtd_wait_time)
        
        return package_data
        
    def _format_wait_time(self, wait_time:str) -> str:
        '''Formats wait time info correct form for storage
        
        Input: None
        Return: str - wait time'''
        if wait_time == 'Wait times unavailable':
            return 'Unavailable'
        else:   # form is 'hr:min'
            stripped_wait = wait_time.strip(' min')
            split_wait = stripped_wait.split(' hr ')
            
            # add missing 0 to min
            if len(split_wait[1]) == 1:
                split_wait[1] = '0' + split_wait[1]
            
            fmtd_wait_time = f'{split_wait[0]}:{split_wait[1]}'
            return fmtd_wait_time
        
    def _get_date(self) -> str:
        '''Gets the current date in writeable format
        
        Input: None
        Return: str - date'''
        today = date.today()
        date_str = today.strftime("%m/%d/%y")
        return date_str
        
    def _get_time(self) -> str:
        '''Gets the current time in writeable format
        
        Input: None
        Return: str - time'''
        now = datetime.now()
        c_time = now.strftime("%H:%M")
        
        # remove leading 0
        if c_time[0] == '0':
            c_time = c_time[1:]
            
        return c_time
        

def main():
    watcher = Watcher()
    watcher.start()
    
if __name__ == '__main__':
    main()
