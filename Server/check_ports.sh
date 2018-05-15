CHECK="do while"

while [[ ! -z $CHECK ]]; do
    PORT=$(( ( RANDOM % 60000 )  + 1025 ))
        CHECK=$(netstat -lat | grep $PORT)
    done

echo $PORT
