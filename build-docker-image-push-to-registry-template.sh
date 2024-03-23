# $1 = version number
# $2 = "skip_run" if you want the container to not run before building
procedures=(
  baton_demo_procedure
)
if [ "$2" == "skip_run" ]; then 
  procedures=()
fi
config="configs/releases/nych-release-$1.yaml"
tag="batoncontainerregistry.azurecr.io/baton:$1"
secret_file="" # TODO: Insert service principal secret file 

echo "Procedures to test run after build:"
for i in ${procedures[*]}; do echo ${i}; done

echo "Building docker image $tag"
docker build --secret id=sp_password,src=$secret_file -t $tag . --progress=plain
# If build result equals 0 (it succeeded), then run docker image
if [ "$?" == 0 ]; then 
  if [ ${#procedures[@]} -gt 0 ]; then
    for p in "${procedures[@]}"; do
      procedure=procedures/$p.py
      echo "Running docker image $tag with procedure $procedure and config $config"
      docker run -e PROCEDURE_NAME=$procedure -e CONFIG_FILE=$config $tag
    done
  fi
fi
echo "Pushing docker image $tag"
docker push $tag