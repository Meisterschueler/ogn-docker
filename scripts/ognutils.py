import requests
import csv
from io import StringIO

DDB_URL = "http://ddb.glidernet.org/download"


def getDDB():
    r = requests.get(DDB_URL)
    
    # Remove comments
    rows = '\n'.join(i for i in r.text.splitlines() if i[0]!='#')

    data = csv.reader(StringIO(rows),quotechar="'",quoting=csv.QUOTE_ALL)
    ddb = []
    for row in data:
            ddb.append({'device_type':row[0],
                        'device_id':row[1],
                        'aircraft_model':row[2],
                        'registration':row[3],
                        'cn':row[4],
                        'tracked': row[5] == 'Y',
                        'indentified': row[6] == 'Y'})
    return ddb


# NOTE: Missing prefix generation for device types O and I!
def listTrackable(ddb):
   l = []
   for i in ddb:
       if i['tracked']:
           if i['device_type'] == 'F':
               l.append('FLR'+i['device_id'])
           elif i['device_type'] == 'O':
               l.append(i['device_id'])
           elif i['device_type'] == 'I':
               pass
               l.append(i['device_id'])
   return l
