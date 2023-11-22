from neumai.Pipelines import Pipeline
from neumai.DataConnectors import WebsiteConnector
from neumai.Shared import Selector
from neumai.Loaders.HTMLLoader import HTMLLoader
from neumai.Chunkers.RecursiveChunker import RecursiveChunker
from neumai.Sources import SourceConnector
from neumai.EmbedConnectors import OpenAIEmbed
from neumai.SinkConnectors import WeaviateSink
import json

website_connector =  WebsiteConnector(
    url = "https://www.neum.ai/post/retrieval-augmented-generation-at-scale",
    selector = Selector(
        to_metadata=['url']
    )
)

source = SourceConnector(
  data_connector=website_connector,
  loader=HTMLLoader(),
  chunker=RecursiveChunker()
)

openai_embed = OpenAIEmbed(
    api_key = "<Open AI Key>",
)

weaviate_sink = WeaviateSink(
  url = "Weaviate Cloud URL",
  api_key = "Weaviate Cloud API Key",
  class_name = "Test",
)

pipeline = Pipeline(
  sources=[source],
  embed=openai_embed,
  sink=weaviate_sink
)

from tasks import data_extraction
from neumai.Pipelines.TriggerSyncTypeEnum import TriggerSyncTypeEnum

data_extraction.apply_async(
	kwargs={"pipeline_model":pipeline.as_pipeline_model(), "extract_type":TriggerSyncTypeEnum.full},
	queue="data_extraction"
)
#You can update the kwargs to do a delta trigger