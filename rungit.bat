
@REM echo "Enter the message for git commit : "

set /p cm=Please put the message :

git add .

git commit -m %cm%

git push

