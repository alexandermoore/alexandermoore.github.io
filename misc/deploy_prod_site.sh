SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
bash $SCRIPT_DIR/build_prod_site.sh &&
bash $SCRIPT_DIR/git_add_all.sh
git commit -am "pre-deployment commit" &&
git merge master &&
git commit -am "merge master" &&
git checkout master &&
git merge dev &&
git commit -am "merge dev" &&
git push origin master &&
git checkout dev