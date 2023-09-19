import time
import rapidjson
EVENTPATH = '../RoboNene/sekai_master/events.json'

def getCurrentEvent(timestamp=None):
    if timestamp == None:
        timestamp = int(time.time() * 1000)
    with open(EVENTPATH, 'r', encoding='utf8') as f:
        eventData = rapidjson.load(f)
        f.close()
    for i, event in enumerate(eventData):
        if event['startAt'] < timestamp and event['closedAt'] > timestamp:
            if timestamp > event['aggregateAt']:
                if i < len(eventData) - 1:
                    return eventData[i + 1]
            return event

    return None