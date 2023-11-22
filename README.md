# Neum AI - Sample Distributed Architecture

This repo contains a sample of a distributed architecture solution using Neum AI with Celery and Redis Queues. By design Neum AI as a framework provides constructs to parallelize workloads in order to process larger data sets. 

![DALL·E 2023-11-21 19 03 39 - A vibrant and colorful logo design without any letters, creating a playful and abstract aesthetic  The design should feature a mix of bright, eye-catc](https://github.com/ddematheu/neum-at-scale/assets/10717976/42206fac-fdc9-4d12-9a30-a7ca673e4a83)

## Getting started

To leverage this repo, you will need to install dependencies:

```
pip install -r requirements.txt
```

- Install the  the [redis CLI](https://redis.io/docs/install/install-redis/install-redis-on-linux/) to run it locally.
- Open AI embeddings model for which you will need an Open AI API Key. To get an API Key visit **[OpenAI](https://platform.openai.com/signup)**. Make sure you have configured billing for the account.
- Weaviate vector database for which you will need a Weaviate Cloud Service URL and API Key. To get a URL and API Key visit [Weaviate Cloud Service](notion://www.notion.so/neumai/Neum-AI-101-v2-f1f1d442990d46e7872d62553706c06b).

## Configure connectors

In the `main.py` file, you need to configure the Open AI and Weaviate connectors. 

Alternatively, you can re-configure your pipeline by using [Neum AI connectors](https://docs.neum.ai/components/pipeline).

## Run it locally

To get everything ready to run our solution, we first need to get our `redis` queues running. To do this, we will use the `redis` CLI:

```python
sudo service redis-server start
```

Once we have the `redis` queues running, we can now start our `Celery` based workers. We will have each running on its own command line.

**data_extraction worker**

```python
celery -A tasks worker --concurrency 1 -Q data_extraction
```

**data_processing worker**

```python
celery -A tasks worker --concurrency 1 -Q data_processing
```

**data_embed_ingest worker**

```python
celery -A tasks worker --concurrency 1 -Q data_embed_ingest
```

Once everything is running, we can now trigger out pipeline. This will distribute the tasks from it into the different queues as it processes the data.

```python
python main.py
```
