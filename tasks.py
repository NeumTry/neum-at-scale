from celery import Celery
from neumai.Pipelines.Pipeline import Pipeline
from neumai.Pipelines.TriggerSyncTypeEnum import TriggerSyncTypeEnum
from neumai.Shared.CloudFile import CloudFile
from neumai.Shared.NeumDocument import NeumDocument
from neumai.Sources.SourceConnector import SourceConnector
from datetime import datetime
from typing import List

app = Celery('tasks', broker="redis://localhost:6379/0")

# Data Extraction Task
@app.task
def data_extraction(pipeline_model:dict, extract_type:TriggerSyncTypeEnum, last_extraction:datetime = None):
    """
    Extract data with 
    pipeline.source.list_files_full
    pipeline.source.list_files_delta
	"""
    pipeline = Pipeline(**pipeline_model)
	
    for source in pipeline.sources:
        if extract_type == TriggerSyncTypeEnum.full:
            for file in source.list_files_full():
                print(f"Sending file: {file.id} to data_processing")
                data_processing.apply_async(
                    kwargs={"pipeline_model":pipeline_model, "source_model": source.as_json(), "cloudFile_model": file.toJson()}, 
                    queue="data_processing"
                )
        elif extract_type == TriggerSyncTypeEnum.delta:
            for file in source.list_files_delta(last_run = last_extraction):
                print(f"Sending file: {file.id} to data_processing")
                data_processing.apply_async(
                    kwargs={"pipeline_model":pipeline_model, "source_model": source.as_json(), "cloudFile_model": file.toJson()}, 
                    queue="data_processing"
                )

# Data Processing Task
@app.task
def data_processing(pipeline_model:dict, source_model: dict, cloudFile_model:dict):
	"""
    Process data with 
    pipeline.source.download_files, 
    pipeline.source.load_data,
    pipeline.source.chunk_data
	"""
	source = SourceConnector(**source_model)
	cloudFile = CloudFile.as_file(cloudFile_model)

	batch_number = 0
	batched_chunks:List[NeumDocument] = []
	for localFile in source.download_files(cloudFile=cloudFile):
		for document in source.load_data(file=localFile):
			for chunks in source.chunk_data(document=document):
				batched_chunks.extend(chunks)
				# If we have enough chunks, send to embed and ingest
				if len(batched_chunks) > 200:
					print(f"Sending batch # {batch_number} for file: {localFile.id} to data_embed_ingest")
					data_embed_ingest.apply_async(
			            kwargs={"pipeline_model":pipeline_model, "chunks":[chunk.toJson() for chunk in batched_chunks]}, 
						queue="data_embed_ingest"
					)
					batched_chunks = []
					batch_number += 1
	# If anything left, then send over
	if len(batched_chunks) > 0:
		print(f"Sending batch # {batch_number} for file: {localFile.id} to data_embed_ingest")
		data_embed_ingest.apply_async(
			kwargs={"pipeline_model":pipeline_model, "chunks":[chunk.toJson() for chunk in batched_chunks]}, 
			queue="data_embed_ingest"
		)

# Data Embed and Ingest Task
@app.task
def data_embed_ingest(pipeline_model:dict, chunks:List[dict]):
	"""
    Embed and Ingest data with 
    pipeline.embed.embed 
    pipeline.sink.store
	"""
	from neumai.Shared.NeumVector import NeumVector
	pipeline = Pipeline(**pipeline_model)
	documents: List[NeumDocument] = [NeumDocument.as_file(chunk) for chunk in chunks]

	vector_embeddings, embeddings_info = pipeline.embed.embed(documents=documents)
	vectors_to_store = [NeumVector(id=documents[i].id, vector=vector_embeddings[i], metadata=documents[i].metadata) for i in range(0,len(vector_embeddings))]
	vectors_written = pipeline.sink.store(
						            vectors_to_store = vectors_to_store,
						            pipeline_id=pipeline.id, 
						        )
	print(f"Finished embedding and storing {vectors_written} vectors")