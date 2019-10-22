BASEDIR=$(dirname "$0")
solc --version
output="$BASEDIR"/solidity_contracts/output/
for entry in "$BASEDIR"/solidity_contracts/*.sol
do

  solc --bin --abi --pretty-json --optimize --overwrite -o "$output" "$entry"

done
