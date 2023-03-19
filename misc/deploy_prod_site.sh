SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
bash $SCRIPT_DIR/build_prod_site.sh &&
bash $SCRIPT_DIR/git_add_all.sh
git commit -am "pre-deployment commit" &&
git checkout master &&
git pull &&
git checkout dev &&
git merge master --no-edit &&
git commit -am "merge master" &&
git checkout master &&
git merge dev --no-edit &&
git push origin master &&
git checkout dev