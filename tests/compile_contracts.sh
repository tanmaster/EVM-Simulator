BASEDIR=$(dirname "$0")
solc --version
output="$BASEDIR"/test_contracts/output/
for entry in "$BASEDIR"/test_contracts/*.sol
do

  solc --bin --abi --pretty-json --optimize --overwrite -o "$output" "$entry"

done
