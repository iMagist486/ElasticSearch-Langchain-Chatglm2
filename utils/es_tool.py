# 检查索引是否存在
index_exists = self.es.indices.exists(index=index_name)
# 新建索引

response = self.es.indices.create(index=index_name, body=mapping)

# 插入数据
response = self.es.index(index=index_name, id=document_id, document=data)

# 更新
rp = self.es.update(index=index_name, id=document_id, body={"doc": data})

# 检查文档是否存在
document_exists = self.es.exists(index=index_name, id=document_id)

response = self.es.delete(index=index_name, id=document_id)
