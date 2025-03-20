mkdir out
cp scripts/*.html out/
uuid=$(python -c 'import uuid; print(str(uuid.uuid4()))')
version=$(tail -c 8 scripts/update.bin)
cp scripts/update.bin out/dudu_update_${uuid}.bin 
sed -i -e "s/UUID/${uuid}/g" -e "s/DATE/${version}/g" out/index.html
python scripts/arena.py
