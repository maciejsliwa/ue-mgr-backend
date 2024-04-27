from datetime import datetime
from azure.cosmos import CosmosClient, PartitionKey
import src.config as config
from src.classes.StreamingHistory import StreamingHistory

HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']


class DatabaseContext:
    def __init__(self):
        self.client = CosmosClient(HOST, {'masterKey': MASTER_KEY},
                                   user_agent="CosmosDBPythonQuickstart",
                                   user_agent_overwrite=True)
        self.database = self.client.create_database_if_not_exists(id=DATABASE_ID)
        self.container = self.database.create_container_if_not_exists(
            id=CONTAINER_ID,
            partition_key=PartitionKey(path="/username"),
            offer_throughput=1000
        )

    def save_streaming_history(self, sh: StreamingHistory):
        for month in sh.get_months():
            new_id = f"{sh.file_name}_{month[0]}_{month[1]}"
            min_date, max_date = sh.get_date_range_for_month(*month)
            body = dict(id=new_id, username=sh.username, min_date=min_date, max_date=max_date,
                        tracks=sh.get_items_by_month(*month))
            self.container.create_item(body=body)

    def get_data_time_range(self, username: str) -> (datetime, datetime):
        min = list(self.container.query_items(
            query=f"""SELECT VALUE MIN(c.min_date)
                  FROM c
                  WHERE c.username = '{username}'
                  """
        ))
        max = list(self.container.query_items(
            query=f"""SELECT VALUE MAX(c.max_date)
                  FROM c
                  WHERE c.username = '{username}'
                  """
        ))
        return datetime.fromisoformat(min[0]), datetime.fromisoformat(max[0])

    def get_last_played_track(self, username: str) -> str:
        items = list(self.container.query_items(
            query=f"""SELECT TOP 1 c.tracks
                  FROM c
                  WHERE c.username = '{username}'
                  ORDER BY c.max_date DESC
                  """
        ))
        return items[0]['tracks'][-1]['master_metadata_track_name']
