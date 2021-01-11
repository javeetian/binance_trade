i=0
while [ $i -le 2 ]
do
	find . -mtime +5 -name "*.log" -exec rm -rf {} \;
	date
	sleep 10d
done
