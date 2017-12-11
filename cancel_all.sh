for row in $(cURl 'http://localhost:6800/listjobs.json?project=CardRatesUpdater' | jq -c '.running[] | {id: .id}'); do
   cURl 'http://localhost:6800/cancel.json?project=CardRatesUpdater' -d job=${row:7:32}
done
