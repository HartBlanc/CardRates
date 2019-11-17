#!/bin/bash

source activate python3

N=$1

python pre.py $N

scrapyd-deploy -p CardRatesUpdater

END=$(($N - 1))

for i in $(seq 0 $END);

do
	cURL http://localhost:6800/schedule.json -d project=CardRatesUpdater -d spider=VisaSpider -d number=$i -d setting=FEED_URI="output/$i.csv" -d setting=CONCURRENT_REQUESTS="$2" -d setting=CONCURRENT_REQUESTS_PER_DOMAIN="$2" -d setting=CONCURRENT_ITEMS="$2"
done

sleep 10

while true; do
foo="$(cURL -s 'http://localhost:6800/listjobs.json?project=CardRatesUpdater' | \
    python -c "import sys, json; print(len(json.load(sys.stdin)['running']))")"
if [ "0" == $foo ]; then
    break
else
    sleep 10
fi
done
python post.py
