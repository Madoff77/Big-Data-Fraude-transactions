FROM python:3.10-slim

# Install system dependencies for Hadoop and PostgreSQL
RUN apt-get update && apt-get install -y \
    openjdk-21-jre-headless \
    wget \
    bash \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Hadoop client (for streaming jobs)
ENV HADOOP_VERSION=3.3.6
ENV HADOOP_HOME=/opt/hadoop
ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
ENV PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$JAVA_HOME/bin

RUN wget -q https://archive.apache.org/dist/hadoop/common/hadoop-${HADOOP_VERSION}/hadoop-${HADOOP_VERSION}.tar.gz \
    && tar -xzf hadoop-${HADOOP_VERSION}.tar.gz \
    && mv hadoop-${HADOOP_VERSION} ${HADOOP_HOME} \
    && rm hadoop-${HADOOP_VERSION}.tar.gz

# Configure Hadoop to connect to namenode
RUN mkdir -p ${HADOOP_HOME}/etc/hadoop && \
    echo '<?xml version="1.0" encoding="UTF-8"?>' > ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '<configuration>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '  <property>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '    <name>fs.defaultFS</name>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '    <value>hdfs://namenode:9000</value>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '  </property>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml && \
    echo '</configuration>' >> ${HADOOP_HOME}/etc/hadoop/core-site.xml

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install loader dependencies (psycopg2 and hdfs for pipeline execution)
RUN pip install --no-cache-dir psycopg2-binary==2.9.9 hdfs==2.7.0

# Copy application
COPY main.py .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
