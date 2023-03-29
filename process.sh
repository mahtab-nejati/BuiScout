#!/bin/sh

language=$1
commit_dir=$2
file_name=$3
output_dir=$4

# gumtree textdiff -g cmake-treesitter ${commit_dir}/before/${file_name} ${commit_dir}/after/${file_name} > ${output_dir}/${file_name}_textdiff.txt
gumtree dotdiff -g ${language}-treesitter ${commit_dir}/before/${file_name} ${commit_dir}/after/${file_name} > ${output_dir}/${file_name}_dotdiff.dot
dot -Tsvg ${output_dir}/${file_name}_dotdiff.dot >  ${output_dir}/${file_name}_dotdiff.svg