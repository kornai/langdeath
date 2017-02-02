#!/bin/bash -

# Set default value to 'classifier.log'
FILE="${1:-classifier.log}"

if ! [ -r "$FILE" ]; then
  echo "Please pass the classifier log file as the first argument"
  exit 1
fi

cat "$FILE" |\
  tr '\n' ' ' |\
  sed -e 's/\(\],\)/\1\n/g'  |\
  sed 's/.*Index\(.*\)/\1/' |\
  tr -s ' ' |\
  sed "s/u'\([^ ']*\)'/\1\n/g"  |\
  tr -d ', [(]' |\
  sed '/^$/d' |\
  grep -v "dtype='object'" |\
  sort |\
  uniq -c |\
  sort -k 1,1g |\
  tac
