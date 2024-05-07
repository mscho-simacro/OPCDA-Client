
import OpenOPC
import pywintypes
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

log_file = f"{ datetime.now().strftime('%Y-%m-%d')}-Log.log"        
log_file_handler = logging.FileHandler(log_file)
log_file_handler.setFormatter(log_formatter)    
logger.addHandler(log_file_handler)





try:
    pywintypes.datetime = pywintypes.TimeType
    opc = OpenOPC.client() 
    print(f"Connect to opc client {opc.opc_class}")
    servers = opc.servers()
except Exception as e:
    print(e)
    logger.error(e)


try:
    for s in servers: 
        ret = opc.connect(s)
        if (ret != True): continue
        items = []
        try:        
            items = opc.list(flat=True)
        except Exception as e:
            print(f"{s} : Exception for opc.list(flat=True)")
            logger.error(f"{s} : Exception for opc.list(flat=True)")

        if (len(items) > 0):
            f = open(f"Subscription-{s}.txt", "w")
            for item in items:
                f.write(f"{item}\n")
            f.close()   
            print(f"Saved {len(items)} tag names for {s}")
            logger.info(f"Saved {len(items)} tag names for {s}")

        opc.close()
        

except Exception as e:
    print(e)
    logger.error(e)

log_file_handler.close()
logger.handlers.pop() 


print("Completed! Press any key")
input()

