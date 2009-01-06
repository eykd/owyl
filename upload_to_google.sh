CONFIG=~/.subversion/auth
SUMMARY=`pwd|sed -E sN/.+/NN`
PROJECT=Owyl
LABELS=`pwd|sed -E sN/.+/NN`
FILES=`ls dist/*`

./googlecode_upload.py --summary=$SUMMARY --project=$PROJECT --labels=$LABELS $FILES