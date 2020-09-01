# You'll need to install PyJWT via pip 'pip install PyJWT' or your project packages file

import jwt

METABASE_SITE_URL = "http://coral.eskilltrading.com:3000"
METABASE_SECRET_KEY = "30ddebd653ba14e30c762eb0ddbf6dc44fae25f1c11889e47999c677668b971c"

payload = {
  "resource": {"dashboard": 3},
  "params": {
    
  }
}
token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token.decode("utf8") + "#theme=night&bordered=false&titled=false"