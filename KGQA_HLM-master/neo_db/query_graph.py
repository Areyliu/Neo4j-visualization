from neo_db.config import graph, CA_LIST, similar_words
from spider.show_profile import get_profile
import codecs
import os
import json
import base64

last_node = False
last_name = None

def query_node(name):
    last_name = name
    last_node = True

    data = graph.run(
        "MATCH (p)-[r]->(n {name: '%s'}) RETURN p.name, type(r) AS link_type, n.name \
        UNION ALL \
        MATCH (p {name: '%s'})-[r]->(n) RETURN p.name, type(r) AS link_type, n.name" % (name, name)
    )
    data = list(data)
    return get_json_data(data)


def query_link(link_type):

    last_query = link_type
    last_node = False

    data = graph.run(
        "MATCH (p)-[r:%s]->(n) RETURN p.name, type(r) AS link_type, n.name" % (link_type)
    )
    data = list(data)
    return get_json_data(data)


def delete_node(name):
    graph.run(
        "MATCH (p {name: '%s'}) DETACH DELETE p" % (name)
    )
    if last_node and last_name != None:
        return query_node(name)
    return {'data':[],"links":[]}


def delete_link(link_type):
    graph.run(
        "MATCH (p)-[r:%s]->(n) DELETE r" % (link_type)
    )
    
    if not last_node and last_name is not None:
        return query_link(link_type)
    
    return {'data': [], "links": []}


def add_node(name, kwarg: dict):
    data = graph.run(
        f"CREATE (n:NodeLabel {{name: '{name}'}}) " +
        "SET " +
        (', '.join([f"n.{k} = '{v}'" for k, v in kwarg.items()])) +
        " RETURN n"
    )
    data = list(data)
    return get_json_data(data)


def add_link(start_name, end_name, link_type, kwarg: dict):
    # 查询并创建起始节点
    graph.run(
        f"MERGE (start:NodeLabel {{name: '{start_name}'}})"
    )
    
    # 查询并创建结束节点
    graph.run(
        f"MERGE (end:NodeLabel {{name: '{end_name}'}})"
    )
    
    # 创建边，使用传入的 link_type
    data = graph.run(
        f"MATCH (start:NodeLabel {{name: '{start_name}'}}), (end:NodeLabel {{name: '{end_name}'}}) "
        f"CREATE (start)-[r:{link_type}]->(end) "  # 使用传入的 link_type
        "SET " +
        (', '.join([f"r.{k} = '{v}'" for k, v in kwarg.items()])) +
        " RETURN start.name, r.name, end.name"
    )
    
    data = list(data)
    return get_json_data(data)
  


def modify_node(name, kwarg: dict):
    data = graph.run(
        f"MATCH (n {{name: '{name}'}}) " +
        "SET " +
        (', '.join([f"n.{k} = '{v}'" for k, v in kwarg.items()])) +
        " RETURN n"
    )
    data = list(data)
    return get_json_data(data)


def modify_link(start_name, end_name, link_type, kwarg: dict):
    # 查询并创建起始节点
    graph.run(
        f"MERGE (start:NodeLabel {{name: '{start_name}'}})"
    )
    
    # 查询并创建结束节点
    graph.run(
        f"MERGE (end:NodeLabel {{name: '{end_name}'}})"
    )
    
    # 创建或更新边，使用传入的 link_type
    data = graph.run(
        f"MATCH (start:NodeLabel {{name: '{start_name}'}})-[r:{link_type}]->(end:NodeLabel {{name: '{end_name}'}}) " 
        "MERGE (start)-[r:{link_type}]->(end) "
        "SET " +
        (', '.join([f"r.{k} = '{v}'" for k, v in kwarg.items()])) +
        " RETURN start, r, end"
    )
    
    data = list(data)
    return get_json_data(data)
    

def get_json_data(data):
    json_data = {'data': [], 'links': []}
    d = []
    
    for i in data:
        # 使用新的属性名进行处理
        d.append(i['p.chname'] + "_" + i['p.enname'] + "_" + i['p.tag'] + "_" + i['p.desc'])
        d.append(i['n.chname'] + "_" + i['n.enname'] + "_" + i['n.tag'] + "_" + i['n.desc'])
    
    d = list(set(d))

    name_dict = {}
    count = 0
    for j in d:
        j_array = j.split("_")
        
        data_item = {}
        name_dict[j_array[0]] = count
        count += 1

        data_item['chname'] = j_array[0]
        data_item['enname'] = j_array[1]
        data_item['tag'] = j_array[2]
        data_item['desc'] = j_array[3]

        json_data['data'].append(data_item)

    for i in data:
        link_item = {}
        
        # source和target都是数字索引
        link_item['source'] = name_dict[i['p.chname']]
        link_item['target'] = name_dict[i['n.chname']]
        link_item['value'] = i['r.relation']  # 假设关系仍然适用

        json_data['links'].append(link_item)

    return json_data


# f = codecs.open('./static/test_data.json','w','utf-8')
# f.write(json.dumps(json_data,  ensure_ascii=False))
def get_KGQA_answer(array):
    data_array=[]
    for i in range(len(array)-2):
        if i==0:
            name=array[0]
        else:
            name=data_array[-1]['p.Name']
           
        data = graph.run(
            "match(p)-[r:%s{relation: '%s'}]->(n:Person{Name:'%s'}) return  p.Name,n.Name,r.relation,p.cate,n.cate" % (
                similar_words[array[i+1]], similar_words[array[i+1]], name)
        )
       
        data = list(data)
        print(data)
        data_array.extend(data)
        
        print("==="*36)
    with open("./spider/images/"+"%s.jpg" % (str(data_array[-1]['p.Name'])), "rb") as image:
            base64_data = base64.b64encode(image.read())
            b=str(base64_data)
          
    return [get_json_data(data_array), get_profile(str(data_array[-1]['p.Name'])), b.split("'")[1]]

def get_answer_profile(name):
    with open("./spider/images/"+"%s.jpg" % (str(name)), "rb") as image:
        base64_data = base64.b64encode(image.read())
        b = str(base64_data)
    return [get_profile(str(name)), b.split("'")[1]]
        



