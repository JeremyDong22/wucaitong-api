# Zeabur 构建系统（可以访问 DockerHub）拉取 postgres:16
# 再推入 Zeabur 内部镜像仓库，绕过运行时 DockerHub 封锁
FROM postgres:16
ENV POSTGRES_DB=zeabur
EXPOSE 5432
