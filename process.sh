#!/bin/sh

language=$1
code_dir=$2
file_name=$3
output_dir=$4

# gumtree textdiff -g cmake-treesitter ${code_dir}/before/${file_name} ${code_dir}/after/${file_name} > ${output_dir}/${file_name}_textdiff.txt
gumtree dotdiff -g ${language}-treesitter ${code_dir}/before/${file_name} ${code_dir}/after/${file_name} > ${output_dir}/${file_name}_dotdiff.dot
# dot -Tsvg ${output_dir}/${file_name}_dotdiff.dot >  ${output_dir}/${file_name}_dotdiff.svg