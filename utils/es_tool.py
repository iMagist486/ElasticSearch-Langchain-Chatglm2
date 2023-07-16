from configs.params import ESParams
from elasticsearch import Elasticsearch

es_params = ESParams()
index_name = es_params.index_name

# %% 初始化ES对象
client = Elasticsearch(['{}:{}'.format(es_params.url, es_params.port)],
                       basic_auth=(es_params.username, es_params.passwd),
                       verify_certs=False)

# %% 连通测试
client.ping()

# %% 检查索引是否存在
index_exists = client.indices.exists(index=index_name)

# %% 新建索引
response = client.indices.create(index=index_name, body=mapping)

# %% 插入数据
response = client.index(index=index_name, id=document_id, document=data)

# %% 更新
rp = client.update(index=index_name, id=document_id, body={"doc": data})

# %% 检查文档是否存在
document_exists = client.exists(index=index_name, id=document_id)

# %% 根据ID删除文档
response = client.delete(index=index_name, id=document_id)
