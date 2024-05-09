from fastapi import FastAPI 

import json
from pydantic import BaseModel, Field
from typing import List

from simacro_opc_client import *

hidden_imports=[
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'app',
]


app = FastAPI( title="Simacro Opc Client", version="1")


class targetInfo(BaseModel):   
    server:str = Field(title = 'server name') 
    item: List[str] = Field(title='item list')



@app.get("/")
async def read_root():
    return "Server working"

@app.post('/get_item_list')
async def getitemlist(info: targetInfo):
    server = info.server
    client = SimacroOpcClient(server)
    ret = client.get_item_list()    
    client.close()
    
    ret_json = json.dumps(ret) 

    return ret_json

@app.post('/get_item_hierarchy')
async def getitemhierarchy(info: targetInfo):
    server = info.server
    client = SimacroOpcClient(server)
    ret = client.get_item_hierarchy()    
    client.close()
    
    ret_json = json.dumps(ret) 

    return ret_json

@app.post('/read_item_values')
async def readitemvalues(info: targetInfo):
    server = info.server
    client = SimacroOpcClient(server)    
    lst_result = client.read_item(info.item)

    lst_dic = []
    for info in lst_result:            
        if (len(info) != 4):
            continue
        lst_dic.append({"Name" : str(info[0]), "Value" : str(info[1]), "Quality" : str(info[2]), "Timestamp" : str(info[3])})

    client.close()    
    ret_json = json.dumps(lst_dic) 
    return ret_json

@app.post('/read_item_properties')
async def readitemproperties(info: targetInfo):
    try:
        server = info.server
        client = SimacroOpcClient(server)
        item_property_col = ["Item ID", "Access Rights", "Scan Rate", "Description"]   
        
        properties = client.get_item_property(info.item)
        lst_dic = []
        property_value = []  

        for item in info.item:  
            item_properties = [p for p in properties if p[0] == item]

            for col in item_property_col:
                found = False
                for p in item_properties :            
                    if (col in p[2]):
                        found = True
                        property_value.append(p[3])                    
                        break
                if (found == False):property_value.append("")    

            
            lst_dic.append({"Name" : str(property_value[0]), "AccessRights" : str(property_value[1]), "ScanRate" : str(property_value[2]), "Description" : str(property_value[3])})
            property_value.clear()

        client.close()
        
        ret_json = json.dumps(lst_dic) 
        return ret_json
    except Exception as e:
        print(e)
        return []

@app.post('/get_opc_servers')
async def getopcservers():
    try :
        opc_manager = SimacroOPCClientManager()
        lst = opc_manager.get_server_list()
        ret_json = json.dumps(lst) 
        return ret_json
    
    except Exception as e:
        print(e)
        return []

