#/bin/bash

BUILDDIR="build"
CONFIGS="params.conf categories.json dictionary.json"



# Bash find do this much faster and more easy.
# But shell emulator which i use on windows don't have find function :[.
# And this help to solve issue.
function find {
    local dir=$1
    local out=""

    for file in $(ls -lA $dir | grep -v "^d" | awk '{print $9}'); do
        out+=$dir"/"$file"\n"
    done

    for dirr in $(ls -l $dir | grep "^d" | awk '{print $9}'); do
        rez=$(find $dir"/"$dirr)
        
        if [ "$rez" != "" ]; then
            out+=$rez"\n"
        fi
    done

    echo -ne "$out"
}


echo -e "\e[36mPreparing '"$BUILDDIR" directory.\e[0m"

# Set up build dir.
if [ -d "$DIRECTORY" ]; then
    mkdir ./$BUILDDIR
else
    rm -rf ./$BUILDDIR
    mkdir ./$BUILDDIR
fi

echo -e "\e[36mCopying utils.\e[0m"

# Copy data from ./util subdirectories exclude python cache and .gitignore
cp --parents $(find ./util | grep -v __pycache__ | grep -v .gitignore) "./"$BUILDDIR"/"

echo -e "\e[36mCopying config files.\e[0m"

# Copy all kind of configuration files.
for file in $CONFIGS; do
    if [ -f $file ]; then
        cp $file ./$BUILDDIR"/"
    else
        cp  $(echo $file | sed "s|\(.*\)\.\(.*\)|\1.sample.\2|") ./$BUILDDIR"/"$file
    fi
done

echo -e "\e[36mCopying main source files.\e[0m"

# Copy main python files.
cp ./*.py ./$BUILDDIR"/"


echo -e "\e[36mCompiling.\e[0m"

# Compile and remove source files.
cd ./$BUILDDIR
python -m compileall -b ./

echo -e "\e[36mRemoving sources.\e[0m"
rm $(find ./ | grep ".py$")

echo -e "\e[36mCreating archive.\e[0m"
bandizip c -r -l:9 -y Scrapper.zip ./*