##############################COMMANDS#############################

hadoop fs -ls hdfs://ma2-gbip-lnn11.corp.itt.com:8020/user/hive/gbi/edw/itunes/idaa/idaa_pipeline/paf_dqmstats_re_detail/ |sed 's/ */ /g'|sed -n '1!p'|awk -F "" '{print $8}'|awk -F "/" '{print $12}'|sort -r
