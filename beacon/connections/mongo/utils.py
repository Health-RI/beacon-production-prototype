from pymongo.cursor import Cursor
from beacon.connections.mongo.__init__ import client
from pymongo.collection import Collection

def get_documents(collection: Collection, query: dict, skip: int, limit: int) -> Cursor:
    return collection.find(query).skip(skip).limit(limit).max_time_ms(100 * 1000)

def get_count(collection: Collection, query: dict) -> int:
    if not query:
        return collection.estimated_document_count()
    else:
        counts=client.beacon.counts.find({"id": str(query), "collection": str(collection)})
        try:
            counts=list(counts)
            if counts == []:
                match_dict={}
                match_dict['$match']=query
                count_dict={}
                aggregated_query=[]
                count_dict["$count"]='Total'
                aggregated_query.append(match_dict)
                aggregated_query.append(count_dict)
                total=list(collection.aggregate(aggregated_query))
                insert_dict={}
                insert_dict['id']=str(query)
                total_counts=total[0]['Total']
                insert_dict['num_results']=total_counts
                insert_dict['collection']=str(collection)
                insert_total=client.beacon.counts.insert_one(insert_dict)
            else:
                total_counts=counts[0]["num_results"]
        except Exception:
            try:
                total_counts=client.beacon.counts.count_documents(query)
                insert_dict={}
                insert_dict['id']=str(query)
                insert_dict['num_results']=total_counts
                insert_dict['collection']=str(collection)
                insert_total=client.beacon.counts.insert_one(insert_dict)
            except Exception:
                total_counts=15
        return total_counts

def get_docs_by_response_type(include: str, query: dict, datasets_dict: dict, dataset: str, limit: int, skip: int, mongo_collection, idq: str):
    if include == 'NONE':
        count = get_count(mongo_collection, query)
        dataset_count=0
        docs = get_documents(
        mongo_collection,
        query,
        skip*limit,
        limit
        )
    elif include == 'ALL':
        count=0
        query_count=query
        i=1
        query_count["$or"]=[]
        for k, v in datasets_dict.items():
            if k == dataset:
                for id in v:
                    if i < len(v):
                        queryid={}
                        queryid[idq]=id
                        query_count["$or"].append(queryid)
                        i+=1
                    else:
                        queryid={}
                        queryid[idq]=id
                        query_count["$or"].append(queryid)
                        i=1
                if query_count["$or"]!=[]:
                    dataset_count = get_count(mongo_collection, query_count)
                    docs = get_documents(
                        mongo_collection,
                        query_count,
                        skip*limit,
                        limit
                    )
                else:
                    dataset_count=0
    return count, dataset_count, docs