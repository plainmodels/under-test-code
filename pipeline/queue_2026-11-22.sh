#!/usr/bin/env bash
# Fixed-order build queue after the 22 Nov reboot. Each step takes the render lock on its own, so short
# agent jobs can run between steps. Progress lines go to logs/queue.log ("DONE <step>" / "FAIL <step>").
cd .; py=.venv/bin/python; P=youtube/pipeline; L=logs/queue.log
step() { name="$1"; shift; echo "$(date +%H:%M) START $name" >> $L
  if flock .render.lock "$@"; then echo "$(date +%H:%M) DONE $name" >> $L; else echo "$(date +%H:%M) FAIL $name" >> $L; fi; }
step me02-assemble bash -c "$py $P/assemble.py moneyentirely/me02 >> moneyentirely/me02/build/build.log 2>&1 && $py $P/script_md.py moneyentirely/me02 $P/../scripts/me02-script.md >> moneyentirely/me02/build/build.log 2>&1"
step ep13-shorts bash -c "cd $P && $py shorts.py ../ep13 && $py short_thumbs.py ../ep13" 
step wf02-shorts bash -c "$py $P/shorts.py wherefell/wf02 && $py $P/short_thumbs.py wherefell/wf02"
step me02-shorts bash -c "$py $P/shorts.py moneyentirely/me02 && $py $P/short_thumbs.py moneyentirely/me02"
step el02-build bash -c "bash $P/build.sh everylayer/el02 3 > everylayer/el02/build/build.log 2>&1"
step el02-shorts bash -c "$py $P/shorts.py everylayer/el02 && $py $P/short_thumbs.py everylayer/el02"
step cn11-build bash -c "bash $P/build.sh contour/cn11 3 > contour/cn11/build/build.log 2>&1"
step cn11-shorts bash -c "$py $P/shorts.py contour/cn11 && $py $P/short_thumbs.py contour/cn11"
step ec11-build bash -c "bash $P/build.sh earth/ec11 3 > earth/ec11/build/build.log 2>&1"
step ec11-shorts bash -c "$py $P/shorts.py earth/ec11 && $py $P/short_thumbs.py earth/ec11"
echo "$(date +%H:%M) QUEUE FINISHED" >> $L
