from typing import Dict, List
from collections import defaultdict
from fastapi import WebSocket

game_rooms: Dict[int, List[WebSocket]] = defaultdict(list)
game_user_map: Dict[int, List[int]] = {}
ready_status: Dict[int, Dict[int, bool]] = defaultdict(dict)
