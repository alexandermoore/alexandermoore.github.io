# kill existing jekyll
ps aux |grep jekyll |awk '{print $2}' | xargs kill -9
# Build prod site
jekyll build