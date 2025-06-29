 #!/bin/bash

     
 
languages="go gcc python rust"
 
for lang in $languages; do
  echo "[piston-entry] Installing $lang via API..."
  curl -s -X POST http://localhost:2000/api/v2/packages \
       -H "Content-Type: application/json" \
       -d "{\"language\": \"$lang\", \"version\": \"*\"}"
done


curl http://localhost:2000/api/v2/runtimes 