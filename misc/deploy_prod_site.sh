SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
# kill nb2md_cli if running since branch switches may mess it up
ps aux |grep nb2md_cli |awk '{print $2}' | xargs kill -9
bash $SCRIPT_DIR/build_prod_site.sh &&
bash $SCRIPT_DIR/git_add_all.sh
git commit -am "pre-deployment commit" &&
git checkout master &&
git pull &&
git checkout dev &&
git merge master --no-edit &&
git checkout master &&
git merge dev --no-edit &&
git push origin master &&
git checkout dev