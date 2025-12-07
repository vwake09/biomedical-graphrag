# Neo4j Dockerfile for Railway
FROM neo4j:5-community

# Set environment variables
ENV NEO4J_PLUGINS=["apoc"]
ENV NEO4J_dbms_security_procedures_unrestricted=apoc.*
ENV NEO4J_dbms_memory_heap_initial__size=256m
ENV NEO4J_dbms_memory_heap_max__size=512m
ENV NEO4J_dbms_memory_pagecache_size=256m

# Expose ports
EXPOSE 7474 7687

