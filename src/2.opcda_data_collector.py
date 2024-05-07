from datetime import datetime
from pytz import timezone  
import time
import schedule
import json
import pymongo
import os
from dateutil.parser import *
import configparser
import logging
import threading

import OpenOPC
import pywintypes

lst_subscription = []


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

def convert_saved_tag_name(name, len):
    try:
        new_name = ''
        is_open = False
        for c in name:
            if c == '.' and not is_open:
                c = '\n'
            elif c in ('"', "'"):
                is_open = not is_open
            new_name += c

        return ".".join((new_name.split('\n'))[((-1)*int(len)):])        

    except Exception as e:
        return name
        

def collect():
    
    log_file = f"{datetime.now().strftime('%Y-%m-%d')}-Log.log"        
    log_file_handler = logging.FileHandler(log_file)
    log_file_handler.setFormatter(log_formatter)    
    logger.addHandler(log_file_handler)

    
    
    for s in lst_subscription:
        server = s["server"]
        alltags = s["items"]

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Start Collection - {server}")
        logger.info(f"Start Collection - {server}")
        
        pywintypes.datetime = pywintypes.TimeType    
        opc = OpenOPC.client()   
        print(f"Connect to opc client {opc.opc_class}")
        ret = opc.connect(server)
        if (ret != True):
            print(f"Cannot connect to OPC server {server}")
            logger.error(f"Cannot connect to OPC server {server}")
            continue

        cnt_per_group = 100
        groups = [alltags[cnt_per_group*i:cnt_per_group*(i+1)] for i in range(int(len(alltags)/cnt_per_group + 1))]
        cur = 1
        for tags in groups:
            if (len(tags) < 1) : continue
            lst_result = []
            try:
                lst_result = opc.read(tags)
            except Exception as e:
                print(e)

            if (len(lst_result) < 1):
                print("Can not read values")
                print(tags)
                logger.warning(f"Can not read values from {server} - {tags}")                
                continue   

            ###############################
            # Check if values are valid

            strnow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for info in lst_result:            
                if (len(info) != 4):
                    continue            
                print(f"[{strnow}] {len(lst_result)} values fetched from {server} - (ex){str(info[0])} : {str(info[1])} ")
                logger.info(f"{len(lst_result)} values fetched from {server} - (ex){str(info[0])} : {str(info[1])}")
                break
            #################################



            save_to_db(lst_result, logger)
            strnow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"[{strnow}] Collection complete({cur}/{len(groups)})")
            logger.info(f"Collection complete({cur}/{len(groups)})")
            cur = cur+1
        
            #############################################
            # for test - save to file
            # Serializing json

            # lst_dic_test = []
            # for info in lst_result:            
            #     if (len(info) != 4):
            #         continue
            #     lst_dic_test.append({"Name" : str(info[0]), "Value" : str(info[1]), "Quality" : str(info[2]), "timestamp" : str(info[3])})

            # json_object = json.dumps(lst_dic_test, indent=4)
            
            # # Writing to sample.json
            # file_name = f"Result - {server}.json"
            # with open(file_name, "w") as f:
            #     f.write(json_object)
            #     f.close()

            # strnow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # print(f"[{strnow}] Save to {file_name}")
            #############################################
            
        opc.close()
    
    log_file_handler.close()
    logger.handlers.pop() 

def save_to_db(lst_result, logger):
    try:
        strnow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        config = configparser.ConfigParser()
        files = config.read('config.txt')
        if (len(files) == 0):
            print(f"[{strnow}] Threse's no config file")
            logger.error(f"Threse's no config file")
            return
        
        strnow = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        time_zone = config['DB']['TIME_ZONE']
        strnow_tz = datetime.now(timezone(time_zone)).strftime('%Y-%m-%d %H:%M:%S.%f%z')

       
        if (config['DB']['DB_SAVE'] == '0'):
            print(f"[{strnow}] DB_SAVE option is 0. If you want to save data to db, set DB_SAVE to 1 in config.txt")
            logger.info(f"DB_SAVE option is 0. If you want to save data to db, set DB_SAVE to 1 in config.txt")
            return


        db_conn = config['DB']['DB_CONNECTION']
        
        # Check if db server is working
        
        try:        
            mongo_client = pymongo.MongoClient(db_conn, serverSelectionTimeoutMS=100)
            mongo_client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as err:            
            print(f"[{strnow}] MongoDB is NOT working")
            logger.error(err)
            return

   
        # Get db information from config file
        db_name = config['DB']['DB_NAME']
        collection_data_name = config['DB']['DB_COLLECTION_DATA']
        collection_list_name = config['DB']['DB_COLLECTION_LIST']
        tag_name_length = config['DB']['TAG_NAME_LENGTH']
        


        db = mongo_client[db_name]

        # Check if collections exists
        cur_cols = db.list_collection_names()
        if ((collection_list_name in cur_cols) == False):
            db.create_collection(collection_list_name)
        if ((collection_data_name in cur_cols) == False):
            db.create_collection(collection_data_name, timeseries={ 'timeField': 'timestamp' })



        # Make inserted data as dictionary
        lst_dic_for_hierarchy = []
        lst_dic_for_data = []
        try:            
            for info in lst_result:            
                if (len(info) != 4):
                    continue    

                new_name = convert_saved_tag_name(str(info[0]), tag_name_length) 
                feature = f"{config['DB']['ROOT_NAME']}, {new_name}"                

                # info[3]  에 있는 time 값은 최종 업데이트 된 시간을 의미하는 것으로 보임...
                # DB 에 저장할때는 현재 시간으로 저장함!!!

                #lst_dic_for_data.append({"timestamp" : parse(str(info[3])),  "value" : str(info[1]), "feature" : feature })
                lst_dic_for_data.append({"timestamp" : parse(strnow_tz),  "value" : str(info[1]), "feature" : feature })
                lst_dic_for_hierarchy.append({"feature" : feature, "name" : new_name })

                #lst_dic.append({"Name" : str(info[0]), "Value" : str(info[1]), "Quality" : str(info[2]), "timestamp" : datetime.strptime(str(info[3]), '%Y-%m-%d %H:%M:%S.%f%z')})
        except Exception as e:
            print(e)
            logger.error(e)
            return

  
        # Check if hierarchy information exists            
        for item in lst_dic_for_hierarchy:            
            hierarchy_info = list(db[collection_list_name].find({'feature' : item['feature']}))
            if (len(hierarchy_info) == 0):
                db[collection_list_name].insert_one({'feature' : item['feature'], 'name' :  item['name']})
                

        # Insert item value     
        try:          
            collection_data = db[collection_data_name]
            if (len(lst_dic_for_data) > 0):
                collection_data.insert_many(lst_dic_for_data)    
        except Exception as e:
            print(e)
            logger.error(e)
            return   


        # print result
        print(f"[{strnow}] Save data to DB") 
        logger.info("Save data to DB")

    except Exception as e:
        print(e)


def run_threaded(job_func):
    job_thread = threading.Thread(target=job_func)
    job_thread.start()

def run():
    try:
        collect()
        
        config = configparser.ConfigParser()
        config.read('config.txt')

        schedule.clear()

        interval = config['Collection']['COLLECTION_INTERVAL_SECOND']
        schedule.every(int(interval)).seconds.do(run_threaded, collect)

        while True:
            schedule.run_pending()
            time.sleep(1)
    except Exception as e:
        print(e)

def get_subscription_info():
    try:
        for filename in os.listdir():
            if ("Subscription" not in filename): continue
            
            server = filename.split("-")[1][0:-4]
            with open(filename, 'r') as f:
                items = f.read().splitlines()
            f.close()

            lst_subscription.append({"server" : server, "items" : items})
        return True
    except Exception as e:
        print("Threre's a problem to read subscription info")
        return False

try:
    if (get_subscription_info()):
        run()
    input()
        
except Exception as e:
        print(e)
        