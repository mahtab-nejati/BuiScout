#!/bin/sh

commit_dir=$1
file_name=$2
output_dir=$3

# gumtree textdiff -g cmake-treesitter ${commit_dir}/before/${file_name} ${commit_dir}/after/${file_name} > ${output_dir}/${file_name}_textdiff.txt
gumtree dotdiff -g cmake-treesitter ${commit_dir}/before/${file_name} ${commit_dir}/after/${file_name} > ${output_dir}/${file_name}_dotdiff.dot
dot -Tsvg ${output_dir}/${file_name}_dotdiff.dot >  ${output_dir}/${file_name}_dotdiff.svg