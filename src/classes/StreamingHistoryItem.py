from datetime import datetime
from typing import Optional


class StreamingHistoryItem:
    def __init__(self, data):
        self.ts: datetime = datetime.fromisoformat(data['ts'])
        self.username: str = data.get('username', '')
        self.platform: str = data.get('platform', '')
        self.ms_played: int = self.safe_cast(data.get('ms_played', 0), int)
        self.conn_country: str = data.get('conn_country', '')
        self.ip_addr_decrypted: str = data.get('ip_addr_decrypted', '')
        self.user_agent_decrypted: str = data.get('user_agent_decrypted', '')
        self.master_metadata_track_name: str = data.get('master_metadata_track_name', '')
        self.master_metadata_album_artist_name: str = data.get('master_metadata_album_artist_name', '')
        self.master_metadata_album_album_name: str = data.get('master_metadata_album_album_name', '')
        self.spotify_track_uri: str = data.get('spotify_track_uri', '')
        self.episode_name: Optional[str] = data.get('episode_name', None)
        self.episode_show_name: Optional[str] = data.get('episode_show_name', None)
        self.spotify_episode_uri: Optional[str] = data.get('spotify_episode_uri', None)
        self.reason_start: str = data.get('reason_start', '')
        self.reason_end: str = data.get('reason_end', '')
        self.shuffle: bool = data.get('shuffle', False)
        self.skipped: bool = data.get('skipped', False)
        self.offline: bool = data.get('offline', False)
        self.offline_timestamp: int = self.safe_cast(data.get('offline_timestamp', 0), int)
        self.incognito_mode: bool = data.get('incognito_mode', False)

    def safe_cast(self, value, cast_type, default=None):
        try:
            return cast_type(value)
        except (ValueError, TypeError):
            return default

