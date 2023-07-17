# Docker部署Elasticsearch

### 1. 下载Elasticsearch和Kibana镜像

```sh
docker pull elastic/elasticsearch:8.8.2
docker pull elastic/kibana:8.8.2
```

### 2. 设置max_map_count

```sh
cat /proc/sys/vm/max_map_count
sysctl -w vm.max_map_count=262144
```

### 3. 为Elasticsearch和Kibana创建docker网络

```sh
docker network create elastic
```

### 4. 创建映射文件夹并设置最高权限

```sh
mkdir /data/es
chmod 777 -R /data/es/
```

### 4. 启动ES镜像

```sh
docker run --name es01 \
--net elastic -p 9200:9200 \
-v /data/es/data:/usr/share/elasticsearch/data \
-v /data/es/logs:/usr/share/elasticsearch/logs \
-v /data/es/plugins:/usr/share/elasticsearch/plugins \
-it elastic/elasticsearch:8.8.2
```

这时会生成一个elastic账户的密码和一个Kibana的enrollment token

### 5.启动kibana镜像

```sh
docker run --name kib-01 --net elastic -p 5601:5601 elastic/kibana:8.8.2
```



### 其他命令

##### 取出证书

```sh
docker cp es01:/usr/share/elasticsearch/config/certs/http_ca.crt .
```

##### 重置密码 

```sh
docker exec -it es01 /usr/share/elasticsearch/bin/elasticsearch-reset-password -u elastic
```

##### 重置kibana token

```sh
docker exec -it es01 /usr/share/elasticsearch/bin/elasticsearch-create-enrollment-token -s kibana
```