from neo_db.config import graph, CA_LIST, similar_words
from spider.show_profile import get_profile
import codecs
import os
import json
import base64

def query(name):
    data = graph.run(
    "MATCH (p)-[r]->(n:NodeLabel {chname: '%s'}) RETURN p.chname, p.enname, p.tag, p.desc, r.relation, n.chname, n.enname, n.tag, n.desc \
     UNION ALL \
     MATCH (p:NodeLabel {chname: '%s'})-[r]->(n) RETURN p.chname, p.enname, p.tag, p.desc, r.relation, n.chname, n.enname, n.tag, n.desc" % (name, name)
    )
    data = list(data)
    return get_json_data(data)

def delete(name):
    graph.run(
        "MATCH (p:NodeLabel {chname: '%s'}) DETACH DELETE p" % (name)
    )
    return {'data':[],"links":[]}

def modify(name, kwarg: dict):
    data = graph.run(
        f"MATCH (n {{chname: '{name}'}}) " +
        "SET " +
        (', '.join([f"n.{k} = '{v}'" for k, v in kwarg.items()])) +
        " RETURN n"
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
        



