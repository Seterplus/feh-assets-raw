mkdir out
cp scripts/*.html out/
uuid=$(uuidgen)
version=$(tail -c 8 scripts/dudu_update.bin)
cp scripts/dudu_update.bin out/dudu_update_${uuid}.bin 
sed -i -e "s/UUID/${uuid}/g" -e "s/DATE/${version}/g" out/index.html
python scripts/arena.py
