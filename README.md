
- Enter the container
`docker exec -i horace-horace-1 /bin/bash`
- install the corpora, e.g.
`averell download adso100`

- start the process
`python horace/main.py -i corpora/ -o out/`
