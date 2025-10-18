from firecrawl import Firecrawl
from pydantic import BaseModel
import pandas as pd
import os
import numpy as np
import requests
import json
import re
from pprint import pprint

firecrawl = Firecrawl(api_key="fc-fc67856032f3451bbf59bfb07d00f85e")

docs = firecrawl.crawl(url="https://www.amazon.com/", limit=1)
# print(dir(docs))
payload = {
    "success": docs.status == "completed",
    "status": docs.status,
    "total": docs.total,
    "completed": docs.completed,
    "credits_used": docs.credits_used,
    "data": [doc.model_dump(exclude_none=True) for doc in docs.data],
}
print(json.dumps(payload, ensure_ascii=False, indent=2))