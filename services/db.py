import re

from bson import ObjectId
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
import sys
import pprint
from configurations import mongo_server


class DB:
    def __init__(self):
        try:
            self.client = MongoClient(
                mongo_server, serverSelectionTimeoutMS=200)
            self.client.server_info()
            self.db = self.client.pcap
            self.pcap_coll = self.db.pcap
            self.file_coll = self.db.filesImported

        except ServerSelectionTimeoutError as err:
            sys.stderr.write("Mongodb server not active on %s: %s" % mongo_server,err)
            sys.exit(1)

    def getFlowList(self, filters):
        #print("parametri iniziali: ")
        #pprint.pprint(filters)
        f = {}
        if "flow.data" in filters:
            f["flow.data"] = re.compile(filters["flow.data"], re.IGNORECASE)
        if "dst_ip" in filters:
            f["dst_ip"] = filters["dst_ip"]
        if "dst_port" in filters:
            f["dst_port"] = int(filters["dst_port"])
        if "from_time" in filters and "to_time" in filters:
            f["time"] = {"$gte": int(filters["from_time"]),
                         "$lt": int(filters["to_time"])}
        if "starred" in filters:
            f["starred"] =  filters["starred"]

        print("query:")
        pprint.pprint(f)

        return self.pcap_coll.find(f, {"flow": 0}).sort("time", -1).limit(2000)

    def getFlowDetail(self, id):
        return self.pcap_coll.find_one({"_id": ObjectId(id)})

    def setStar(self, flow_id, star):
        self.pcap_coll.find_one_and_update({"_id": ObjectId(flow_id)}, {"$set": {"starred":  1 if star == '1' else 0}})

    def isFileAlreadyImported(self, file_name):
        return self.file_coll.find({"file_name": file_name}).count() != 0

    def setFileImported(self, file_name):
        return self.file_coll.insert({"file_name": file_name})

    def insertFlows(self, filename, flows):
        if self.isFileAlreadyImported(filename):
            print("file already present! not importing it!")
            return
        result = self.pcap_coll.insert_many(flows)
        print("result: ", result)
        #IMPORTANT! create index for each field in the table if not present before
        # col.create_index([("time", ASCENDING)])
        # col.create_index([('flow.data', 'text')])
        return result

    def delete_all_pcaps(self, filename):
        return self.pcap_coll.remove({})
