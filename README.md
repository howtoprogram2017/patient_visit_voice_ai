## Simple Implementation of LiveKit Voice Agent

### Environment and Code Dependencies
python version: 3.10.1

install dependencies:
```aiignore
python -m pip install --upgrade pip
pip install -r requiment.txt 
```

### Instructions
to test voice agent without phone call:
```
python app/main console
```

to connecting inbound phone call from self-host phone number, neet to setup configuration with LiveKit Server.
1. authorize access to LiveKit Server
```
lk cloud auth
```
2. setup inbound trunk
```
lk inbound create inbound-trunk.json
```
3. set up dispatch rule
```aiignore
lk dispatch create dispatch-rule.json
```

make sure you have setup phone number and inbound trunk before running the code.
then execute:
```aiignore
python app/main dev
```

### API KEY
All API needed are:
1. DEEPGRAM_API_KEY
2. CARTESIA_API_KEY
3. OPENAI_API_KEY
4. LIVEKIT_API_KEY
5. LIVEKIT_API_SECRET
6. LIVEKIT_URL
7. GOOGLE_MAP_API_KEY
8. LARK_TOKEN
Ask me for access: bl2684@nyu.edu



