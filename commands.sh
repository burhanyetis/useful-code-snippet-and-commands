##############################COMMANDS#############################
1. hadoop fs -ls hdfs://ma2-gbip-lnn11.corp.itt.com:8020/user/hive/gbi/edw/itunes/idaa/idaa_pipeline/paf_dqmstats_re_detail/ |sed 's/ */ /g'|sed -n '1!p'|awk -F "" '{print $8}'|awk -F "/" '{print $12}'|sort -r

2. part1 = "hdfs://TEST2/user/hive/dir1/dir2/"
   part2 = "hdfs://TEST3/user/hive/dir1/dir2/"
   hadoop distcp -Dmapred.job.queue.name = <queue_name> -skipcrccheck -pb -delete -update -m 20 part1 part2
   

