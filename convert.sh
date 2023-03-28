#!/bin/sh

dir=$1

for file in ${dir}/*.dot; do
    dot -Tsvg $file >  ${file%.dot}.svg
done